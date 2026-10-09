"""Structural chunker: converts legal hierarchy + pages into provenance-bound PhaseChunk objects.

Primary strategy: one chunk per detected legal unit (Section, Rule, Sub-section, etc.).
Fallback: when a legal unit text exceeds MAX_CHUNK_CHARS, split with sliding overlap,
retaining full hierarchy breadcrumb and overlap metadata.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

from velis_rag.models.enums import LanguageCode
from velis_rag.models.phase2a import (
    ExtractionStatus,
    HierarchyNode,
    HierarchyNodeType,
    PageExtractionResult,
    PhaseChunk,
)
from velis_rag.normalization.invariants import StructuredInvariantEngine

MAX_CHUNK_CHARS = 3000  # ~750 tokens; fallback splitting threshold
OVERLAP_CHARS = 200  # character overlap on fallback splits


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_text(text: str) -> str:
    text = text.lstrip("\ufeff")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in text.split("\n")]
    cleaned: list[str] = []
    blank = 0
    for line in lines:
        if not line:
            blank += 1
            if blank <= 1:
                cleaned.append("")
        else:
            blank = 0
            cleaned.append(line)
    return "\n".join(cleaned).strip()


def _detect_language(text: str) -> LanguageCode:
    """Rough language detection: Devanagari block → Hindi, else English."""
    devanagari = sum(1 for ch in text if "\u0900" <= ch <= "\u097f")
    return LanguageCode.HI if devanagari / max(len(text), 1) > 0.15 else LanguageCode.EN


@dataclass
class DocumentMeta:
    """Metadata injected from the Phase 1 catalog for a single document."""

    document_id: str
    source_id: str
    canonical_url: str
    delivery_url: str
    raw_file_sha256: str
    norm_doc_text_sha256: str
    trust_tier: str
    doc_version: str
    effective_date: str | None
    issuing_authority: str
    local_filename: str
    doc_type: str | None = None


def _text_for_pages(
    page_results: list[PageExtractionResult],
    page_start: int,
    page_end: int,
) -> tuple[str, str]:
    """Concatenate original and normalized text for a page range (inclusive)."""
    orig_parts: list[str] = []
    norm_parts: list[str] = []
    for pr in page_results:
        if page_start <= pr.page_number <= page_end:
            if pr.status not in (ExtractionStatus.QUARANTINED,):
                orig_parts.append(pr.raw_text)
                norm_parts.append(pr.normalized_text)
    return "\n".join(orig_parts), "\n".join(norm_parts)


def _build_citation(meta: DocumentMeta, node: HierarchyNode | None, page_start: int, page_end: int) -> str:
    """Build a human-readable citation locator."""
    doc_short = meta.document_id.replace("_", " ").title()
    if node:
        path_str = " > ".join(node.parent_path + [node.label])
        return f"{doc_short}, {path_str}, p.{page_start}"
    return f"{doc_short}, p.{page_start}"


def _split_fallback(
    text: str,
    max_chars: int = MAX_CHUNK_CHARS,
    overlap: int = OVERLAP_CHARS,
) -> list[str]:
    """Split text into overlapping chunks not exceeding max_chars.

    Attempts to split at sentence/paragraph boundaries.
    """
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # Try to break at a paragraph or sentence boundary
        if end < len(text):
            for sep in ("\n\n", "\n", ". ", "। "):
                pos = text.rfind(sep, start, end)
                if pos != -1 and pos > start + overlap:
                    end = pos + len(sep)
                    break
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def _find_node_line_indices(
    doc_lines: list[tuple[int, str, str]],
    nodes: list[HierarchyNode],
) -> list[tuple[int, HierarchyNode]]:
    """Determine line boundaries for primary hierarchy nodes."""
    has_indices = any(n.line_index > 0 for n in nodes)
    if has_indices:
        results = []
        for n in nodes:
            idx = min(max(0, n.line_index), len(doc_lines) - 1)
            results.append((idx, n))
        results.sort(key=lambda x: x[0])
        deduped: list[tuple[int, HierarchyNode]] = []
        seen_idx: set[int] = set()
        for idx, n in results:
            if idx not in seen_idx:
                seen_idx.add(idx)
                deduped.append((idx, n))
        return deduped

    # Fallback content-matching when line_index is not set (e.g., in mock tests)
    results = []
    curr = 0
    for n in nodes:
        lbl_token = n.label.split()[-1] if " " in n.label else n.label
        found = None
        for i in range(curr, len(doc_lines)):
            pnum, _, nline = doc_lines[i]
            if pnum < n.page_start:
                continue
            if pnum > n.page_start + 1:
                break
            if (
                n.label.lower() in nline.lower()
                or nline.startswith(lbl_token + ".")
                or nline.startswith(lbl_token + " ")
                or nline == lbl_token
            ):
                found = i
                break
        if found is not None:
            results.append((found, n))
            curr = found + 1
    return results


def build_chunks(
    meta: DocumentMeta,
    page_results: list[PageExtractionResult],
    hierarchy: list[HierarchyNode],
) -> list[PhaseChunk]:
    """Convert page extraction results + hierarchy into non-overlapping provenance-bound chunks.

    Strategy:
    1. Flatten non-quarantined document pages into ordered line tuples (page_num, line_raw, line_norm).
    2. If no hierarchy detected, emit 1 chunk per page (split if > MAX_CHUNK_CHARS).
    3. If hierarchy detected, select primary structural units (depth <= 2 or all units).
       Partition line stream into contiguous, non-overlapping slices:
       - Preamble slice (lines before first unit, if any)
       - Per-unit slices (lines belonging to unit k from its start to next unit's start)
    4. Units exceeding MAX_CHUNK_CHARS are split using sliding window with overlap.
    """
    doc_lines: list[tuple[int, str, str]] = []
    for pr in page_results:
        if pr.status == ExtractionStatus.QUARANTINED:
            continue
        norm_lines = [line.strip() for line in pr.normalized_text.splitlines() if line.strip()]
        raw_lines = [line.strip() for line in pr.raw_text.splitlines() if line.strip()]
        for idx, nl_str in enumerate(norm_lines):
            raw_str = raw_lines[idx] if (idx < len(raw_lines) and raw_lines[idx]) else nl_str
            doc_lines.append((pr.page_number, raw_str, nl_str))

    if not doc_lines:
        return []

    chunks: list[PhaseChunk] = []
    doc_short = meta.document_id.replace("_", " ").title()

    # Clean fallback when no hierarchy detected (e.g. process flowcharts / guidelines)
    if not hierarchy:
        for pr in page_results:
            if pr.status == ExtractionStatus.QUARANTINED or not pr.normalized_text.strip():
                continue
            norm_text = pr.normalized_text
            raw_text = pr.raw_text
            sub_texts = _split_fallback(norm_text)
            orig_sub_texts = _split_fallback(raw_text) if len(sub_texts) > 1 else [raw_text]
            lang = _detect_language(norm_text)
            invariants = [inv.model_dump() for inv in StructuredInvariantEngine.extract_invariants(norm_text, lang)]

            base_citation = f"{doc_short}, Page {pr.page_number}"
            for s_idx, stext in enumerate(sub_texts):
                citation = (
                    f"{base_citation} [split {s_idx + 1}/{len(sub_texts)}]" if len(sub_texts) > 1 else base_citation
                )
                sub_orig = (
                    orig_sub_texts[s_idx] if (s_idx < len(orig_sub_texts) and orig_sub_texts[s_idx].strip()) else stext
                )
                chunks.append(
                    PhaseChunk(
                        chunk_id=f"{meta.document_id}__c{len(chunks):04d}",
                        document_id=meta.document_id,
                        chunk_index=len(chunks),
                        source_id=meta.source_id,
                        canonical_url=meta.canonical_url,
                        delivery_url=meta.delivery_url,
                        raw_file_sha256=meta.raw_file_sha256,
                        norm_doc_text_sha256=meta.norm_doc_text_sha256,
                        trust_tier=meta.trust_tier,
                        page_start=pr.page_number,
                        page_end=pr.page_number,
                        hierarchy_path=[f"Page {pr.page_number}"],
                        citation_locator=citation,
                        doc_version=meta.doc_version,
                        effective_date=meta.effective_date,
                        original_text=sub_orig,
                        normalized_text=stext,
                        chunk_text_sha256=_sha256(stext),
                        extraction_status=pr.status,
                        invariants=invariants,
                    )
                )
        return chunks

    # Primary structural boundaries (depth <= 2 or all units if none <= 2)
    primary_nodes = [
        n
        for n in hierarchy
        if n.node_type
        in (
            HierarchyNodeType.PART,
            HierarchyNodeType.CHAPTER,
            HierarchyNodeType.SECTION,
            HierarchyNodeType.RULE,
            HierarchyNodeType.SCHEDULE,
            HierarchyNodeType.ANNEXURE,
        )
    ]
    if not primary_nodes:
        primary_nodes = hierarchy

    node_indices = _find_node_line_indices(doc_lines, primary_nodes)

    slices: list[tuple[HierarchyNode | None, list[tuple[int, str, str]]]] = []
    if node_indices:
        first_idx, first_node = node_indices[0]
        if first_idx > 0:
            slices.append((None, doc_lines[:first_idx]))
        for k in range(len(node_indices)):
            cur_idx, cur_node = node_indices[k]
            next_idx = node_indices[k + 1][0] if k + 1 < len(node_indices) else len(doc_lines)
            slices.append((cur_node, doc_lines[cur_idx:next_idx]))
    else:
        # Fallback to page-by-page if boundary matching yielded nothing
        return build_chunks(meta, page_results, [])

    for node, sec_lines in slices:
        if not sec_lines:
            continue
        p_start = sec_lines[0][0]
        p_end = sec_lines[-1][0]
        orig_text = "\n".join(ln_item[1] for ln_item in sec_lines).strip() or norm_text
        norm_text = "\n".join(ln_item[2] for ln_item in sec_lines).strip()
        if not norm_text:
            continue

        if node is not None:
            path = node.parent_path + [node.label]
            path_str = " > ".join(path)
            base_locator = (
                f"{doc_short}, {path_str}, p.{p_start}"
                if p_start == p_end
                else f"{doc_short}, {path_str}, p.{p_start}-{p_end}"
            )
        else:
            path = ["Preamble"]
            base_locator = (
                f"{doc_short}, Preamble, p.{p_start}"
                if p_start == p_end
                else f"{doc_short}, Preamble, p.{p_start}-{p_end}"
            )

        sub_texts = _split_fallback(norm_text)
        orig_sub_texts = _split_fallback(orig_text) if len(sub_texts) > 1 else [orig_text]
        lang = _detect_language(norm_text)
        invariants = [inv.model_dump() for inv in StructuredInvariantEngine.extract_invariants(norm_text, lang)]

        for s_idx, stext in enumerate(sub_texts):
            citation = f"{base_locator} [split {s_idx + 1}/{len(sub_texts)}]" if len(sub_texts) > 1 else base_locator
            sub_orig = (
                orig_sub_texts[s_idx] if (s_idx < len(orig_sub_texts) and orig_sub_texts[s_idx].strip()) else stext
            )
            chunks.append(
                PhaseChunk(
                    chunk_id=f"{meta.document_id}__c{len(chunks):04d}",
                    document_id=meta.document_id,
                    chunk_index=len(chunks),
                    source_id=meta.source_id,
                    canonical_url=meta.canonical_url,
                    delivery_url=meta.delivery_url,
                    raw_file_sha256=meta.raw_file_sha256,
                    norm_doc_text_sha256=meta.norm_doc_text_sha256,
                    trust_tier=meta.trust_tier,
                    page_start=p_start,
                    page_end=p_end,
                    hierarchy_path=path,
                    citation_locator=citation,
                    doc_version=meta.doc_version,
                    effective_date=meta.effective_date,
                    original_text=sub_orig,
                    normalized_text=stext,
                    chunk_text_sha256=_sha256(stext),
                    extraction_status=ExtractionStatus.OK,
                    invariants=invariants,
                )
            )

    return chunks

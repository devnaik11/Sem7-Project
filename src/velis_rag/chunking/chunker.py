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


def build_chunks(
    meta: DocumentMeta,
    page_results: list[PageExtractionResult],
    hierarchy: list[HierarchyNode],
) -> list[PhaseChunk]:
    """Convert page extraction results + hierarchy into provenance-bound chunks.

    Strategy:
    1. For each hierarchy node, collect the text from its page range.
    2. If text fits in MAX_CHUNK_CHARS → one chunk.
    3. If text exceeds limit → fallback split with overlap, each sub-chunk retains parent path.
    4. Pages with no matching hierarchy node are emitted as PARAGRAPH chunks.
    """
    chunks: list[PhaseChunk] = []
    chunk_idx = 0

    # Track which pages are covered by explicit hierarchy nodes
    covered_pages: set[int] = set()

    for node in hierarchy:
        page_s = node.page_start
        page_e = node.page_end or node.page_start
        orig_text, norm_text = _text_for_pages(page_results, page_s, page_e)

        if not norm_text.strip():
            continue

        # Determine extraction status of pages in range
        page_statuses = [pr.status for pr in page_results if page_s <= pr.page_number <= page_e]
        worst_status = (
            ExtractionStatus.QUARANTINED
            if ExtractionStatus.QUARANTINED in page_statuses
            else (
                ExtractionStatus.LOW_DENSITY if ExtractionStatus.LOW_DENSITY in page_statuses else ExtractionStatus.OK
            )
        )

        hierarchy_path = node.parent_path + [node.label]
        lang = _detect_language(norm_text)

        # Invariants
        invariants = [inv.model_dump() for inv in StructuredInvariantEngine.extract_invariants(norm_text, lang)]

        sub_texts = _split_fallback(norm_text)
        orig_sub_texts = _split_fallback(orig_text) if len(sub_texts) > 1 else [orig_text]

        for sub_i, sub_norm in enumerate(sub_texts):
            sub_orig = orig_sub_texts[sub_i] if sub_i < len(orig_sub_texts) else sub_norm
            chunk_id = f"{meta.document_id}__c{chunk_idx:04d}"
            citation = _build_citation(meta, node, page_s, page_e)
            if len(sub_texts) > 1:
                citation += f" [split {sub_i + 1}/{len(sub_texts)}]"

            chunks.append(
                PhaseChunk(
                    chunk_id=chunk_id,
                    document_id=meta.document_id,
                    chunk_index=chunk_idx,
                    source_id=meta.source_id,
                    canonical_url=meta.canonical_url,
                    delivery_url=meta.delivery_url,
                    raw_file_sha256=meta.raw_file_sha256,
                    norm_doc_text_sha256=meta.norm_doc_text_sha256,
                    trust_tier=meta.trust_tier,
                    page_start=page_s,
                    page_end=page_e,
                    hierarchy_path=hierarchy_path,
                    citation_locator=citation,
                    doc_version=meta.doc_version,
                    effective_date=meta.effective_date,
                    original_text=sub_orig,
                    normalized_text=sub_norm,
                    chunk_text_sha256=_sha256(sub_norm),
                    extraction_status=worst_status,
                    invariants=invariants,
                )
            )
            chunk_idx += 1
            for p in range(page_s, page_e + 1):
                covered_pages.add(p)

    # Emit uncovered non-quarantined pages as paragraph chunks
    for pr in page_results:
        if pr.page_number in covered_pages:
            continue
        if pr.status == ExtractionStatus.QUARANTINED:
            continue
        if not pr.normalized_text.strip():
            continue

        sub_texts = _split_fallback(pr.normalized_text)
        orig_sub_texts = _split_fallback(pr.raw_text) if len(sub_texts) > 1 else [pr.raw_text]

        lang = _detect_language(pr.normalized_text)
        invariants = [
            inv.model_dump() for inv in StructuredInvariantEngine.extract_invariants(pr.normalized_text, lang)
        ]

        for sub_i, sub_norm in enumerate(sub_texts):
            sub_orig = orig_sub_texts[sub_i] if sub_i < len(orig_sub_texts) else sub_norm
            chunk_id = f"{meta.document_id}__c{chunk_idx:04d}"
            citation = f"{meta.document_id.replace('_', ' ').title()}, p.{pr.page_number}"
            if len(sub_texts) > 1:
                citation += f" [split {sub_i + 1}/{len(sub_texts)}]"

            chunks.append(
                PhaseChunk(
                    chunk_id=chunk_id,
                    document_id=meta.document_id,
                    chunk_index=chunk_idx,
                    source_id=meta.source_id,
                    canonical_url=meta.canonical_url,
                    delivery_url=meta.delivery_url,
                    raw_file_sha256=meta.raw_file_sha256,
                    norm_doc_text_sha256=meta.norm_doc_text_sha256,
                    trust_tier=meta.trust_tier,
                    page_start=pr.page_number,
                    page_end=pr.page_number,
                    hierarchy_path=[f"Document/{meta.document_id}", f"Page {pr.page_number}"],
                    citation_locator=citation,
                    doc_version=meta.doc_version,
                    effective_date=meta.effective_date,
                    original_text=sub_orig,
                    normalized_text=sub_norm,
                    chunk_text_sha256=_sha256(sub_norm),
                    extraction_status=pr.status,
                    invariants=invariants,
                )
            )
            chunk_idx += 1

    return chunks

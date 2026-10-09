"""PDF text extraction with per-page quality assessment."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pymupdf

from velis_rag.models.phase2a import ExtractionStatus, PageExtractionResult

# Quality thresholds
MIN_CHARS_PER_PAGE = 80  # below this → LOW_DENSITY or EMPTY
GARBLED_RATIO_THRESHOLD = 0.15  # fraction of replacement chars (U+FFFD) or control chars
REPEATED_HEADER_WINDOW = 3  # check for identical text in N consecutive pages


def _normalize(text: str) -> str:
    """NFC normalize and collapse whitespace; preserve line breaks."""
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


def _garbled_ratio(text: str) -> float:
    """Return fraction of characters that are replacement chars or C0/C1 control chars."""
    if not text:
        return 0.0
    bad = sum(
        1 for ch in text if ch == "\ufffd" or (unicodedata.category(ch) in ("Cc", "Cs") and ch not in ("\n", "\t"))
    )
    return bad / len(text)


def extract_pages(pdf_path: Path, document_id: str) -> list[PageExtractionResult]:
    """Extract text from every page of a PDF with quality assessment.

    Returns a list of PageExtractionResult (one per page, 1-indexed).
    Pages with quality issues are flagged but retained; only QUARANTINED
    pages should be excluded from downstream chunking.
    """
    doc = pymupdf.open(str(pdf_path))
    results: list[PageExtractionResult] = []
    raw_texts: list[str] = []

    for idx in range(len(doc)):
        page = doc[idx]
        raw = page.get_text()
        raw_texts.append(raw)

    # Detect repeated headers/footers across consecutive pages
    # Identify lines that appear in >= 60% of pages → likely header/footer
    line_counter: dict[str, int] = {}
    total_pages = len(raw_texts)
    for raw in raw_texts:
        first_lines = set(raw.strip().splitlines()[:3] + raw.strip().splitlines()[-2:])
        for line in first_lines:
            stripped = line.strip()
            if len(stripped) > 3:
                line_counter[stripped] = line_counter.get(stripped, 0) + 1
    repeated_headers = {line for line, count in line_counter.items() if count >= max(2, int(total_pages * 0.5))}

    for idx, raw in enumerate(raw_texts):
        page_num = idx + 1
        # Strip repeated header/footer lines for quality analysis (not from original_text)
        analysis_lines = [ln for ln in raw.splitlines() if ln.strip() not in repeated_headers]
        analysis_text = "\n".join(analysis_lines)

        normalized = _normalize(raw)
        char_count = len(normalized)
        word_count = len(normalized.split()) if normalized else 0
        garbled = _garbled_ratio(raw)

        if char_count == 0:
            status = ExtractionStatus.EMPTY
            reason: str | None = "Page yielded zero characters after normalization."
        elif char_count < MIN_CHARS_PER_PAGE and len(analysis_text.strip()) < MIN_CHARS_PER_PAGE:
            status = ExtractionStatus.LOW_DENSITY
            reason = f"Extracted text too short ({char_count} chars < {MIN_CHARS_PER_PAGE} threshold)."
        elif garbled > GARBLED_RATIO_THRESHOLD:
            status = ExtractionStatus.GARBLED
            reason = f"High garbled character ratio ({garbled:.2%} > {GARBLED_RATIO_THRESHOLD:.0%})."
        else:
            status = ExtractionStatus.OK
            reason = None

        # Quarantine only if both empty AND garbled (catastrophic extraction failure)
        if status in (ExtractionStatus.EMPTY, ExtractionStatus.GARBLED):
            status = ExtractionStatus.QUARANTINED

        results.append(
            PageExtractionResult(
                document_id=document_id,
                page_number=page_num,
                raw_text=raw,
                normalized_text=normalized,
                char_count=char_count,
                word_count=word_count,
                status=status,
                quarantine_reason=reason,
            )
        )

    doc.close()
    return results

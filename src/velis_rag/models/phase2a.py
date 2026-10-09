"""Phase 2A data models: extraction quality, hierarchy, and full-provenance chunks."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExtractionStatus(StrEnum):
    OK = "ok"
    LOW_DENSITY = "low_density"
    GARBLED = "garbled"
    EMPTY = "empty"
    QUARANTINED = "quarantined"


class HierarchyNodeType(StrEnum):
    DOCUMENT = "document"
    PART = "part"
    CHAPTER = "chapter"
    SECTION = "section"
    SUB_SECTION = "sub_section"
    RULE = "rule"
    SUB_RULE = "sub_rule"
    CLAUSE = "clause"
    PROVISO = "proviso"
    EXPLANATION = "explanation"
    SCHEDULE = "schedule"
    ANNEXURE = "annexure"
    LIST = "list"
    TABLE = "table"
    PARAGRAPH = "paragraph"


class PageExtractionResult(BaseModel):
    """Extraction result for a single PDF page."""

    document_id: str
    page_number: int  # 1-indexed
    raw_text: str
    normalized_text: str
    char_count: int
    word_count: int
    status: ExtractionStatus
    quarantine_reason: str | None = None


class HierarchyNode(BaseModel):
    """A node in the detected legal document hierarchy."""

    node_type: HierarchyNodeType
    label: str  # e.g. "Chapter II", "Section 6", "Rule 3"
    title: str | None  # heading text after the label
    page_start: int
    page_end: int | None = None
    depth: int  # 0 = document root, 1 = chapter/part, 2 = section/rule, etc.
    parent_path: list[str] = Field(default_factory=list)  # breadcrumb of ancestor labels


class PhaseChunk(BaseModel):
    """Full-provenance chunk: every required field for Phase 2A."""

    # Identity
    chunk_id: str
    document_id: str
    chunk_index: int  # sequential within document

    # Source provenance
    source_id: str
    canonical_url: str
    delivery_url: str
    raw_file_sha256: str
    norm_doc_text_sha256: str
    trust_tier: str

    # Location
    page_start: int
    page_end: int
    hierarchy_path: list[str]  # full breadcrumb from root to immediate parent
    citation_locator: str  # human-readable e.g. "RTI Act 2005, Section 6(1), p.5"

    # Document metadata
    doc_version: str
    effective_date: str | None

    # Text
    original_text: str  # as extracted, before normalization
    normalized_text: str  # NFC + whitespace normalized

    # Hashes
    chunk_text_sha256: str  # SHA-256 of normalized_text

    # Quality
    extraction_status: ExtractionStatus

    # Invariants (serialised as list of dicts for DB storage)
    invariants: list[dict[str, Any]] = Field(default_factory=list)

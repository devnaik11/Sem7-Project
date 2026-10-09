"""Data models for retrieval, filtering, and ranked search results."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RetrievalRecord(BaseModel):
    """An indexed passage chunk carrying all verified provenance and metadata attributes."""

    chunk_id: str = Field(..., min_length=3, description="Unique chunk identifier")
    document_id: str = Field(..., min_length=3, description="Parent document identifier")
    chunk_index: int = Field(..., ge=0, description="Sequential index within document")
    source_id: str = Field(..., min_length=2, description="Source registry ID")
    document_title: str = Field(..., min_length=3, description="Official title of document")
    canonical_url: str = Field(..., description="Canonical source URL")
    delivery_url: str = Field(..., description="Resolved direct delivery URL")
    page_start: int = Field(..., ge=1, description="Starting 1-indexed PDF page")
    page_end: int = Field(..., ge=1, description="Ending 1-indexed PDF page")
    citation_locator: str = Field(..., min_length=3, description="Human-readable citation locator")
    hierarchy_path: list[str] = Field(..., description="Hierarchical breadcrumb path")
    trust_tier: str = Field(..., description="Trust tier (must be Tier_A)")
    doc_version: str = Field(..., min_length=1, description="Document version / amendment string")
    effective_date: str | None = Field(default=None, description="Effective date (YYYY-MM-DD)")
    issuing_authority: str = Field(..., min_length=3, description="Issuing Ministry/Authority")
    jurisdiction: str = Field(..., min_length=2, description="Jurisdiction code e.g. IN-CENTRAL")
    doc_type: str = Field(..., min_length=2, description="Official document type")
    original_text: str = Field(..., min_length=1, description="Raw extracted passage text")
    normalized_text: str = Field(..., min_length=1, description="Normalized passage text")
    raw_file_sha256: str = Field(..., description="SHA-256 of raw PDF")
    norm_doc_text_sha256: str = Field(..., description="SHA-256 of normalized document text")
    chunk_text_sha256: str = Field(..., description="SHA-256 of normalized passage text")
    extraction_status: str = Field(default="ok", description="Extraction quality status")
    invariants: list[dict[str, Any]] = Field(default_factory=list, description="Extracted legal invariants")

    @field_validator("trust_tier")
    @classmethod
    def validate_tier_a_only(cls, v: str) -> str:
        if v != "Tier_A":
            raise ValueError(f"Strict governance violation: Only Tier_A chunks eligible for retrieval, found '{v}'")
        return v

    @field_validator("raw_file_sha256", "norm_doc_text_sha256", "chunk_text_sha256")
    @classmethod
    def validate_sha256_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[0-9a-f]{64}$", v):
            raise ValueError(f"Invalid SHA-256 checksum format: '{v}'")
        return v

    @field_validator("page_end")
    @classmethod
    def validate_page_range(cls, v: int, info: Any) -> int:
        if "page_start" in info.data and v < info.data["page_start"]:
            raise ValueError(f"page_end ({v}) cannot be less than page_start ({info.data['page_start']})")
        return v


class RetrievalFilter(BaseModel):
    """Deterministic metadata filter parameters for BM25 and dense retrieval."""

    document_id: str | None = None
    jurisdiction: str | None = None
    trust_tier: str | None = None
    doc_type: str | None = None
    doc_version: str | None = None
    source_id: str | None = None
    effective_date_from: str | None = None
    effective_date_to: str | None = None

    def matches(self, record: RetrievalRecord) -> bool:
        """Evaluate deterministic filter matching against a RetrievalRecord."""
        if self.document_id is not None and record.document_id != self.document_id:
            return False
        if self.jurisdiction is not None and record.jurisdiction != self.jurisdiction:
            return False
        if self.trust_tier is not None and record.trust_tier != self.trust_tier:
            return False
        if self.doc_type is not None and record.doc_type != self.doc_type:
            return False
        if self.doc_version is not None and record.doc_version != self.doc_version:
            return False
        if self.source_id is not None and record.source_id != self.source_id:
            return False
        if self.effective_date_from is not None:
            if not record.effective_date or record.effective_date < self.effective_date_from:
                return False
        if self.effective_date_to is not None:
            if not record.effective_date or record.effective_date > self.effective_date_to:
                return False
        return True


class SearchResult(BaseModel):
    """A scored, ranked retrieval result preserving all constituent fusion metadata."""

    chunk_id: str
    score: float
    rank: int
    bm25_score: float | None = None
    bm25_rank: int | None = None
    dense_score: float | None = None
    dense_rank: int | None = None
    rrf_score: float | None = None
    record: RetrievalRecord

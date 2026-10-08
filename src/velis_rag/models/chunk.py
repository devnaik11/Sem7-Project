"""Passage chunk schema representing an indexed atomic legal segment."""

import re

from pydantic import BaseModel, Field, field_validator

from velis_rag.models.enums import TrustTier


class PassageChunk(BaseModel):
    """An indexed structural segment of a legal or governmental document."""

    chunk_id: str = Field(..., min_length=3, description="Unique chunk identifier")
    document_id: str = Field(..., min_length=3, description="Parent document identifier")
    section_hierarchy: list[str] = Field(
        ..., min_length=1, description="Hierarchical breadcrumb (e.g. Chapter, Section, Sub-section)"
    )
    text_content: str = Field(..., min_length=10, description="Normalized passage text content")
    source_tier: TrustTier = Field(..., description="Trust tier of source document")
    source_url: str = Field(..., description="Canonical source URL")
    issuing_authority: str = Field(..., min_length=3, description="Ministry or Department")
    jurisdiction: str = Field(..., min_length=2, description="Jurisdiction scope")
    effective_date: str | None = Field(default=None, description="Effective date (YYYY-MM-DD)")
    document_version: str = Field(..., description="Document amendment version")
    extracted_text_sha256: str = Field(..., description="SHA-256 of the normalized passage text")

    @field_validator("extracted_text_sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        v = v.strip().lower()
        if "placeholder" in v:
            raise ValueError(f"Placeholder hashes strictly rejected in runtime chunks: '{v}'")
        if not re.match(r"^[0-9a-f]{64}$", v):
            raise ValueError(f"Invalid SHA-256 format (must be 64-char lowercase hex): '{v}'")
        return v

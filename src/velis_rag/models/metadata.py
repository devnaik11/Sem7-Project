"""Legal document metadata schema with dual-hash provenance."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from velis_rag.models.enums import TrustTier


class LegalDocumentMetadata(BaseModel):
    """Authoritative metadata and provenance for an ingested government document."""

    document_id: str = Field(..., min_length=3, description="Canonical document ID")
    title: str = Field(..., min_length=3, description="Official title of Act or Scheme")
    issuing_authority: str = Field(..., min_length=3, description="Ministry or Department name")
    jurisdiction: str = Field(..., min_length=2, description="Jurisdiction (e.g. Union of India, Maharashtra)")
    source_url: str = Field(..., description="Initiating canonical page or portal URL")
    final_file_url: str = Field(..., description="Final resolved file download URL after redirects")
    doc_type: str = Field(..., description="Type of document (e.g. Central Act, Operational Guidelines)")
    source_tier: TrustTier = Field(..., description="Trust classification (Tier_A, Tier_B, Tier_C)")
    publication_date: str | None = Field(default=None, description="Publication date (YYYY-MM-DD)")
    effective_date: str | None = Field(default=None, description="Effective or commencement date (YYYY-MM-DD)")
    document_version: str = Field(..., description="Document amendment or version identifier")
    raw_file_sha256: str = Field(..., description="SHA-256 digest of original downloaded file bytes")
    extracted_text_sha256: str = Field(..., description="SHA-256 digest of normalized extracted text")
    download_timestamp: datetime = Field(..., description="UTC timestamp of file acquisition")
    license_and_reuse_basis: str = Field(
        ..., min_length=10, description="Specific statutory or open data license basis"
    )
    compliance_checkpoint_passed: bool = Field(default=False, description="Compliance review clearance")

    @field_validator("raw_file_sha256", "extracted_text_sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        v = v.strip().lower()
        if "placeholder" in v:
            raise ValueError(f"Placeholder hashes strictly rejected in runtime metadata: '{v}'")
        if not re.match(r"^[0-9a-f]{64}$", v):
            raise ValueError(f"Invalid SHA-256 format (must be 64-char lowercase hex): '{v}'")
        return v

    @field_validator("source_url", "final_file_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"Invalid URL protocol (must start with http:// or https://): '{v}'")
        return v

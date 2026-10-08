"""Source registry entry schema and validation."""

import re

from pydantic import BaseModel, Field, field_validator

from velis_rag.models.enums import TrustTier


class SourceRegistryEntry(BaseModel):
    """Configuration record for an approved official document source."""

    id: str = Field(..., min_length=3, description="Unique source identifier")
    canonical_host: str = Field(..., description="Approved canonical portal host")
    approved_file_delivery_hosts: list[str] = Field(
        ..., min_length=1, description="Approved redirect/file-delivery hosts"
    )
    allowed_document_types: list[str] = Field(..., min_length=1, description="Permitted document types")
    allowed_path_patterns: list[str] = Field(..., min_length=1, description="Regex patterns for allowed URL paths")
    default_trust_tier: TrustTier = Field(default=TrustTier.Tier_A, description="Assigned trust tier")
    licensing_and_reuse_basis: str = Field(
        ..., min_length=10, description="Specific statutory or open data licensing basis"
    )
    status: str = Field(default="active", description="Registry entry status")

    @field_validator("canonical_host")
    @classmethod
    def validate_canonical_host(cls, v: str) -> str:
        v = v.strip().lower()
        if "*" in v or "%" in v or " " in v:
            raise ValueError(f"Wildcards or spaces forbidden in canonical host: {v}")
        if not re.match(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]*[a-z0-9])?)+$", v):
            raise ValueError(f"Invalid canonical host format: {v}")
        return v

    @field_validator("approved_file_delivery_hosts")
    @classmethod
    def validate_file_delivery_hosts(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        for host in v:
            h = host.strip().lower()
            if "*" in h or "%" in h or " " in h:
                raise ValueError(f"Wildcards or spaces forbidden in file delivery host: {h}")
            if not re.match(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]*[a-z0-9])?)+$", h):
                raise ValueError(f"Invalid file delivery host format: {h}")
            cleaned.append(h)
        return cleaned

    @field_validator("allowed_path_patterns")
    @classmethod
    def validate_path_patterns(cls, v: list[str]) -> list[str]:
        for pattern in v:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex path pattern '{pattern}': {e}") from e
        return v

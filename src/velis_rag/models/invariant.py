"""Structured legal invariant schema."""

from pydantic import BaseModel, Field

from velis_rag.models.enums import InvariantType, LanguageCode


class Invariant(BaseModel):
    """A normalized legal invariant (fee, timeline, section reference, or authority)."""

    type: InvariantType = Field(..., description="Category of legal invariant")
    raw_surface_form: str = Field(..., description="Surface string as it appears in the text")
    normalized_value: str = Field(..., description="Canonical structured representation (e.g. INR:10.00)")
    language: LanguageCode = Field(..., description="Source text language")
    source_chunk_id: str | None = Field(default=None, description="Originating Tier A chunk reference")

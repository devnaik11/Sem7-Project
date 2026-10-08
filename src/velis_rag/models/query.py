"""Citizen query schema."""

from pydantic import BaseModel, Field

from velis_rag.models.enums import ClaimType, LanguageCode, QueryComplexity


class CitizenQuery(BaseModel):
    """Citizen query input schema."""

    query_id: str = Field(..., min_length=3, description="Unique query request identifier")
    query_text: str = Field(..., min_length=3, description="User query text")
    language: LanguageCode = Field(default=LanguageCode.EN, description="Query language")
    complexity: QueryComplexity | None = Field(default=None, description="Router complexity assessment")
    jurisdiction_hint: str | None = Field(default=None, description="Target jurisdiction if specified")
    uploaded_doc_ref: str | None = Field(default=None, description="Reference to uploaded document (Tier C subject)")
    target_claim_type: ClaimType = Field(default=ClaimType.OPERATIVE, description="Expected nature of inquiry")

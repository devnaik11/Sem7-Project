"""Citizen brief and bilingual response schemas."""

from pydantic import BaseModel, Field, model_validator

from velis_rag.models.enums import LanguageCode, TrustTier
from velis_rag.models.invariant import Invariant
from velis_rag.models.verification import VerificationResult


class CitizenBriefSection(BaseModel):
    """A thematic section within a simplified citizen brief."""

    title: str = Field(..., min_length=3, description="Section heading")
    content: str = Field(..., min_length=10, description="Simplified explanatory content")
    citations: list[str] = Field(default_factory=list, description="Associated chunk citations")


class CitizenBrief(BaseModel):
    """A structured, simplified legal brief in a single target language."""

    query_id: str = Field(..., min_length=3, description="Associated query identifier")
    language: LanguageCode = Field(..., description="Language of this brief (en / hi)")
    summary: str = Field(..., min_length=10, description="Core direct takeaway")
    sections: list[CitizenBriefSection] = Field(..., min_length=1, description="Structured sections")
    invariants: list[Invariant] = Field(default_factory=list, description="Extracted legal invariants")
    tier_b_warning_present: bool = Field(default=False, description="Whether an explicit Tier B caveat is attached")
    disclaimer_present: bool = Field(
        default=True, description="Whether mandatory non-legal-advice disclaimer is present"
    )
    verification_summary: VerificationResult | None = Field(
        default=None, description="Detailed claim verification audit"
    )

    @model_validator(mode="after")
    def validate_mandatory_disclaimer_and_tier_b_warning(self) -> "CitizenBrief":
        if not self.disclaimer_present:
            raise ValueError("Mandatory non-legal-advice disclaimer cannot be omitted from CitizenBrief.")
        if self.verification_summary:
            all_cited_tiers = [tier for claim in self.verification_summary.claims for tier in claim.cited_tiers]
            if TrustTier.Tier_B in all_cited_tiers and not self.tier_b_warning_present:
                raise ValueError("Tier B evidence cited without required prominent warning banner.")
        return self


class BilingualBrief(BaseModel):
    """A paired bilingual brief covering English and Hindi representations."""

    query_id: str = Field(..., min_length=3, description="Query identifier")
    english_brief: CitizenBrief = Field(..., description="English brief")
    hindi_brief: CitizenBrief = Field(..., description="Hindi brief")
    invariants_match: bool = Field(..., description="Whether all normalized invariants match identically")
    audit_logged: bool = Field(default=False, description="Whether an audit incident record was created")

    @model_validator(mode="after")
    def validate_languages(self) -> "BilingualBrief":
        if self.english_brief.language != LanguageCode.EN:
            raise ValueError(f"english_brief must have language 'en', got '{self.english_brief.language}'")
        if self.hindi_brief.language != LanguageCode.HI:
            raise ValueError(f"hindi_brief must have language 'hi', got '{self.hindi_brief.language}'")
        return self

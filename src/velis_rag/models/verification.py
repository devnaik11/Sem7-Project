"""Verification schemas enforcing source trust tiers and operative claim restrictions."""

from pydantic import BaseModel, Field, model_validator

from velis_rag.models.enums import ClaimType, EntailmentStatus, OperativeCategory, TrustTier


class VerificationClaim(BaseModel):
    """An individual atomic claim extracted from a generated brief."""

    claim_id: str = Field(..., min_length=3, description="Claim identifier")
    claim_text: str = Field(..., min_length=5, description="Proposition text")
    claim_type: ClaimType = Field(..., description="Operative vs contextual classification")
    operative_category: OperativeCategory | None = Field(
        default=None, description="Specific operative category if applicable"
    )
    cited_chunk_ids: list[str] = Field(..., min_length=1, description="Citations supporting the claim")
    cited_tiers: list[TrustTier] = Field(..., min_length=1, description="Trust tiers of the supporting passages")
    status: EntailmentStatus = Field(default=EntailmentStatus.UNVERIFIED, description="Entailment outcome")
    entailment_score: float | None = Field(default=None, ge=0.0, le=1.0, description="NLI confidence score")

    @model_validator(mode="after")
    def validate_operative_claim_tiers(self) -> "VerificationClaim":
        if self.claim_type == ClaimType.OPERATIVE:
            non_tier_a = [t for t in self.cited_tiers if t != TrustTier.Tier_A]
            if non_tier_a:
                raise ValueError(
                    f"Tier B/C violation: Legally operative claim '{self.claim_id}' must be supported "
                    f"exclusively by Tier A evidence. Prohibited tiers found: {non_tier_a}"
                )
        return self


class VerificationResult(BaseModel):
    """Verification outcome evaluating grounding across all claims."""

    is_grounded: bool = Field(..., description="Whether all claims are verified without unsupported extrapolations")
    unsupported_claim_count: int = Field(..., ge=0, description="Count of unentailed claims")
    claims: list[VerificationClaim] = Field(..., description="List of evaluated atomic claims")
    overall_entailment_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate entailment confidence")

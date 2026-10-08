"""Tests enforcing Trust Tier classifications and operative claim restrictions."""

import pytest
from pydantic import ValidationError

from velis_rag.models.brief import CitizenBrief, CitizenBriefSection
from velis_rag.models.enums import (
    ClaimType,
    EntailmentStatus,
    LanguageCode,
    OperativeCategory,
    TrustTier,
)
from velis_rag.models.verification import VerificationClaim, VerificationResult


def test_tier_a_operative_claim_allowed() -> None:
    """Test that Tier A evidence is valid for legally operative claims."""
    claim = VerificationClaim(
        claim_id="CLM-FEE-001",
        claim_text="The statutory fee for filing an RTI application is Rs. 10.",
        claim_type=ClaimType.OPERATIVE,
        operative_category=OperativeCategory.FEE,
        cited_chunk_ids=["RTI-RULES-2012-RULE-3"],
        cited_tiers=[TrustTier.Tier_A],
        status=EntailmentStatus.ENTAILED,
        entailment_score=0.98,
    )
    assert claim.claim_id == "CLM-FEE-001"
    assert claim.claim_type == ClaimType.OPERATIVE


def test_tier_b_prohibited_from_operative_fee_claim() -> None:
    """Test that using Tier B evidence for a statutory fee claim raises a validation error."""
    with pytest.raises(ValidationError, match="Tier B/C violation: Legally operative claim"):
        VerificationClaim(
            claim_id="CLM-FEE-002",
            claim_text="The fee is Rs. 10 according to the ministry circular.",
            claim_type=ClaimType.OPERATIVE,
            operative_category=OperativeCategory.FEE,
            cited_chunk_ids=["DOPT-CIRCULAR-2015-SEC-2"],
            cited_tiers=[TrustTier.Tier_B],  # PROHIBITED FOR OPERATIVE CLAIMS
            status=EntailmentStatus.ENTAILED,
            entailment_score=0.95,
        )


def test_tier_b_prohibited_from_operative_deadline_claim() -> None:
    """Test that using Tier B evidence for a statutory deadline claim is prohibited."""
    with pytest.raises(ValidationError, match="Tier B/C violation: Legally operative claim"):
        VerificationClaim(
            claim_id="CLM-DEADLINE-001",
            claim_text="The Public Information Officer must reply within 30 days.",
            claim_type=ClaimType.OPERATIVE,
            operative_category=OperativeCategory.DEADLINE,
            cited_chunk_ids=["DOPT-FAQ-PAGE-3"],
            cited_tiers=[TrustTier.Tier_B],  # PROHIBITED
            status=EntailmentStatus.ENTAILED,
            entailment_score=0.92,
        )


def test_tier_b_allowed_for_contextual_claim() -> None:
    """Test that Tier B evidence is permitted for contextual/background claims."""
    claim = VerificationClaim(
        claim_id="CLM-CTX-001",
        claim_text="The Department of Personnel and Training issues nodal guidance on RTI implementation.",
        claim_type=ClaimType.CONTEXTUAL,
        cited_chunk_ids=["DOPT-CIRCULAR-2015-OVERVIEW"],
        cited_tiers=[TrustTier.Tier_B],  # ALLOWED FOR CONTEXTUAL
        status=EntailmentStatus.ENTAILED,
        entailment_score=0.94,
    )
    assert claim.claim_type == ClaimType.CONTEXTUAL
    assert claim.cited_tiers == [TrustTier.Tier_B]


def test_tier_c_prohibited_from_all_claims() -> None:
    """Test that Tier C (user/untrusted content) can never support operative claims."""
    with pytest.raises(ValidationError, match="Tier B/C violation: Legally operative claim"):
        VerificationClaim(
            claim_id="CLM-USER-001",
            claim_text="The citizen claims exemption under low income status.",
            claim_type=ClaimType.OPERATIVE,
            operative_category=OperativeCategory.ELIGIBILITY,
            cited_chunk_ids=["USER-UPLOADED-PETITION-CHUNK-1"],
            cited_tiers=[TrustTier.Tier_C],  # PROHIBITED
            status=EntailmentStatus.UNVERIFIED,
        )


def test_citizen_brief_enforces_tier_b_warning() -> None:
    """Test that if Tier B evidence is cited, the CitizenBrief must have tier_b_warning_present=True."""
    contextual_claim = VerificationClaim(
        claim_id="CLM-CTX-002",
        claim_text="Background history of the portal guidelines.",
        claim_type=ClaimType.CONTEXTUAL,
        cited_chunk_ids=["CIRCULAR-01"],
        cited_tiers=[TrustTier.Tier_B],
        status=EntailmentStatus.ENTAILED,
        entailment_score=0.90,
    )
    verification = VerificationResult(
        is_grounded=True,
        unsupported_claim_count=0,
        claims=[contextual_claim],
        overall_entailment_score=0.90,
    )
    section = CitizenBriefSection(
        title="Background",
        content="Background explanation based on advisory circular.",
        citations=["CIRCULAR-01"],
    )

    # Omitting tier_b_warning_present when Tier B is in verification must fail validation
    with pytest.raises(ValidationError, match="Tier B evidence cited without required prominent warning banner"):
        CitizenBrief(
            query_id="Q-CTX-01",
            language=LanguageCode.EN,
            summary="Background summary.",
            sections=[section],
            tier_b_warning_present=False,  # VIOLATION: must be True when Tier B is present
            disclaimer_present=True,
            verification_summary=verification,
        )

    # With warning present, it should validate successfully
    valid_brief = CitizenBrief(
        query_id="Q-CTX-01",
        language=LanguageCode.EN,
        summary="Background summary.",
        sections=[section],
        tier_b_warning_present=True,
        disclaimer_present=True,
        verification_summary=verification,
    )
    assert valid_brief.tier_b_warning_present is True

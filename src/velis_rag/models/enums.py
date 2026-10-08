"""Enumerations for VeLiS-RAG domain, trust tiers, claims, and invariants."""

from enum import StrEnum


class TrustTier(StrEnum):
    """Source trust classification."""

    Tier_A = "Tier_A"  # Authoritative legal ground truth (Acts, Rules, Notified Guidelines)
    Tier_B = "Tier_B"  # Qualified official context (Circulars, Drafts, FAQs) - non-operative
    Tier_C = "Tier_C"  # Untrusted user or external material - never legal evidence


class ClaimType(StrEnum):
    """Classification of claim legal operativeness."""

    OPERATIVE = "operative"  # Fees, deadlines, eligibility, penalties, statutory rights, procedures
    CONTEXTUAL = "contextual"  # Background, historical context, organizational descriptions


class OperativeCategory(StrEnum):
    """Specific categories of legally operative claims."""

    ELIGIBILITY = "eligibility"
    FEE = "fee"
    DEADLINE = "deadline"
    PENALTY = "penalty"
    STATUTORY_RIGHT = "statutory_right"
    MANDATORY_PROCEDURE = "mandatory_procedure"


class InvariantType(StrEnum):
    """Types of normalized legal invariants."""

    CURRENCY = "currency"
    DURATION = "duration"
    DATE = "date"
    PERCENTAGE = "percentage"
    SECTION_ID = "section_id"
    AUTHORITY = "authority"


class EntailmentStatus(StrEnum):
    """NLI entailment status of claims against retrieved passages."""

    ENTAILED = "entailed"
    CONTRADICTED = "contradicted"
    NEUTRAL = "neutral"
    UNVERIFIED = "unverified"


class LanguageCode(StrEnum):
    """Supported languages in VeLiS-RAG Phase 0/1."""

    EN = "en"
    HI = "hi"


class QueryComplexity(StrEnum):
    """Adaptive query retrieval depth classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

"""Property-based and unit tests for the Structured Invariant Extraction & Normalization Engine."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from velis_rag.models.enums import InvariantType, LanguageCode
from velis_rag.models.invariant import Invariant
from velis_rag.normalization.invariants import (
    StructuredInvariantEngine,
    to_ascii_digits,
)


@given(st.integers(min_value=0, max_value=999999))
def test_property_devanagari_digit_conversion(n: int) -> None:
    """Property test: Converting ASCII digits to Devanagari and back must be identity."""
    ascii_str = str(n)
    # Map ASCII to Devanagari
    ascii_to_dev = str.maketrans("0123456789", "०१२३४५६७८९")
    devanagari_str = ascii_str.translate(ascii_to_dev)

    # Convert back via to_ascii_digits
    recovered = to_ascii_digits(devanagari_str)
    assert recovered == ascii_str
    assert int(recovered) == n


@given(st.integers(min_value=1, max_value=10000))
def test_property_currency_normalization(amount: int) -> None:
    """Property test: Diverse surface forms of INR amounts must normalize to identical canonical values."""
    en_surfaces = [
        f"Rs. {amount}",
        f"Rs.{amount}",
        f"INR {amount}",
        f"₹{amount}",
        f"{amount} rupees",
    ]
    expected = f"INR:{Decimal(amount):.2f}"
    for surface in en_surfaces:
        norm = StructuredInvariantEngine.normalize_currency(surface, LanguageCode.EN)
        assert norm == expected, f"Failed for surface form '{surface}'"


def test_hindi_currency_normalization() -> None:
    """Test Hindi currency surface forms in Devanagari numerals and words."""
    assert StructuredInvariantEngine.normalize_currency("10 रुपये", LanguageCode.HI) == "INR:10.00"
    assert StructuredInvariantEngine.normalize_currency("१० रुपये", LanguageCode.HI) == "INR:10.00"
    assert StructuredInvariantEngine.normalize_currency("दस रुपये", LanguageCode.HI) == "INR:10.00"
    assert StructuredInvariantEngine.normalize_currency("₹१०", LanguageCode.HI) == "INR:10.00"


def test_duration_normalization_bilingual() -> None:
    """Test duration normalization across English and Hindi."""
    # Days
    assert StructuredInvariantEngine.normalize_duration("30 days", LanguageCode.EN) == "DURATION:30_DAYS"
    assert StructuredInvariantEngine.normalize_duration("thirty days", LanguageCode.EN) == "DURATION:30_DAYS"
    assert StructuredInvariantEngine.normalize_duration("30 दिन", LanguageCode.HI) == "DURATION:30_DAYS"
    assert StructuredInvariantEngine.normalize_duration("३० दिन", LanguageCode.HI) == "DURATION:30_DAYS"
    assert StructuredInvariantEngine.normalize_duration("तीस दिन", LanguageCode.HI) == "DURATION:30_DAYS"

    # Hours
    assert StructuredInvariantEngine.normalize_duration("48 hours", LanguageCode.EN) == "DURATION:48_HOURS"
    assert StructuredInvariantEngine.normalize_duration("forty eight hours", LanguageCode.EN) == "DURATION:48_HOURS"
    assert StructuredInvariantEngine.normalize_duration("48 घंटे", LanguageCode.HI) == "DURATION:48_HOURS"
    assert StructuredInvariantEngine.normalize_duration("४८ घंटे", LanguageCode.HI) == "DURATION:48_HOURS"
    assert StructuredInvariantEngine.normalize_duration("अड़तालीस घंटे", LanguageCode.HI) == "DURATION:48_HOURS"


def test_section_id_normalization_bilingual() -> None:
    """Test statutory section identifier normalization across English and Hindi."""
    assert StructuredInvariantEngine.normalize_section_id("Section 6(1)") == "SEC_ID:6(1)"
    assert StructuredInvariantEngine.normalize_section_id("Sec. 6(1)") == "SEC_ID:6(1)"
    assert StructuredInvariantEngine.normalize_section_id("धारा 6(1)") == "SEC_ID:6(1)"
    assert StructuredInvariantEngine.normalize_section_id("धारा ६(१)") == "SEC_ID:6(1)"

    assert StructuredInvariantEngine.normalize_section_id("Section 7(1)") == "SEC_ID:7(1)"
    assert StructuredInvariantEngine.normalize_section_id("धारा 7(1)") == "SEC_ID:7(1)"

    assert StructuredInvariantEngine.normalize_section_id("Rule 3") == "RULE_ID:3"
    assert StructuredInvariantEngine.normalize_section_id("नियम 3") == "RULE_ID:3"
    assert StructuredInvariantEngine.normalize_section_id("नियम ३") == "RULE_ID:3"


def test_authority_normalization_bilingual() -> None:
    """Test statutory authority title normalization across English and Hindi."""
    assert StructuredInvariantEngine.normalize_authority("Public Information Officer") == "AUTH_ID:PIO"
    assert StructuredInvariantEngine.normalize_authority("लोक सूचना अधिकारी") == "AUTH_ID:PIO"
    assert StructuredInvariantEngine.normalize_authority("Central Public Information Officer") == "AUTH_ID:CPIO"
    assert StructuredInvariantEngine.normalize_authority("केंद्रीय लोक सूचना अधिकारी") == "AUTH_ID:CPIO"
    assert StructuredInvariantEngine.normalize_authority("First Appellate Authority") == "AUTH_ID:FAA"
    assert StructuredInvariantEngine.normalize_authority("प्रथम अपीलीय प्राधिकारी") == "AUTH_ID:FAA"


def test_bilingual_invariant_matching_and_no_silent_repair() -> None:
    """Test that bilingual comparison detects discrepancies and never silently passes mismatched invariants."""
    en_invariants = [
        Invariant(
            type=InvariantType.CURRENCY,
            raw_surface_form="Rs. 10",
            normalized_value="INR:10.00",
            language=LanguageCode.EN,
        ),
        Invariant(
            type=InvariantType.DURATION,
            raw_surface_form="30 days",
            normalized_value="DURATION:30_DAYS",
            language=LanguageCode.EN,
        ),
    ]

    # Identical normalized values in Hindi
    hi_invariants_matching = [
        Invariant(
            type=InvariantType.CURRENCY,
            raw_surface_form="दस रुपये",
            normalized_value="INR:10.00",
            language=LanguageCode.HI,
        ),
        Invariant(
            type=InvariantType.DURATION,
            raw_surface_form="तीस दिन",
            normalized_value="DURATION:30_DAYS",
            language=LanguageCode.HI,
        ),
    ]

    matched, discrepancies = StructuredInvariantEngine.compare_bilingual_invariants(
        en_invariants, hi_invariants_matching
    )
    assert matched is True
    assert len(discrepancies) == 0

    # Discrepant Hindi invariants (e.g. Hindi draft says 15 days instead of 30 days)
    hi_invariants_discrepant = [
        Invariant(
            type=InvariantType.CURRENCY,
            raw_surface_form="दस रुपये",
            normalized_value="INR:10.00",
            language=LanguageCode.HI,
        ),
        Invariant(
            type=InvariantType.DURATION,
            raw_surface_form="पंद्रह दिन",
            normalized_value="DURATION:15_DAYS",
            language=LanguageCode.HI,
        ),
    ]

    matched, discrepancies = StructuredInvariantEngine.compare_bilingual_invariants(
        en_invariants, hi_invariants_discrepant
    )
    # Must flag mismatch! Under system policy: never silently repair, trigger single regen or abstain
    assert matched is False
    assert len(discrepancies) == 2
    assert any("DURATION:30_DAYS" in d for d in discrepancies)
    assert any("DURATION:15_DAYS" in d for d in discrepancies)

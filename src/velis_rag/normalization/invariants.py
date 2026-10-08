"""Structured legal invariant extraction and normalization engine.

Normalizes currencies, durations, percentages, section IDs, statutory authorities,
and approved bilingual terminology across English and Hindi.
"""

import re
from decimal import Decimal

from velis_rag.models.enums import InvariantType, LanguageCode
from velis_rag.models.invariant import Invariant

# Devanagari to ASCII digit mapping
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# Word-number lookup for numbers frequently occurring in RTI and Scheme rules
HINDI_NUMBER_WORDS: dict[str, int] = {
    "एक": 1,
    "दो": 2,
    "तीन": 3,
    "चार": 4,
    "पांच": 5,
    "पाँच": 5,
    "छह": 6,
    "सात": 7,
    "आठ": 8,
    "नौ": 9,
    "दस": 10,
    "पंद्रह": 15,
    "बीस": 20,
    "तीस": 30,
    "पैंतालीस": 45,
    "अड़तालीस": 48,
    "पचास": 50,
    "साठ": 60,
    "नब्बे": 90,
    "सौ": 100,
}

ENGLISH_NUMBER_WORDS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "forty-five": 45,
    "forty-eight": 48,
    "forty eight": 48,
    "fifty": 50,
    "sixty": 60,
    "ninety": 90,
    "hundred": 100,
}

# Authority Canonical Normalization Table (CSTT bilingual mapping)
AUTHORITY_MAP: dict[str, str] = {
    # Central Public Information Officer
    "central public information officer": "AUTH_ID:CPIO",
    "cpio": "AUTH_ID:CPIO",
    "केंद्रीय लोक सूचना अधिकारी": "AUTH_ID:CPIO",
    "केन्द्रीय लोक सूचना अधिकारी": "AUTH_ID:CPIO",
    # Public Information Officer
    "public information officer": "AUTH_ID:PIO",
    "pio": "AUTH_ID:PIO",
    "लोक सूचना अधिकारी": "AUTH_ID:PIO",
    # First Appellate Authority
    "first appellate authority": "AUTH_ID:FAA",
    "faa": "AUTH_ID:FAA",
    "प्रथम अपीलीय प्राधिकारी": "AUTH_ID:FAA",
    "प्रथम अपील अधिकारी": "AUTH_ID:FAA",
    # Central Information Commission
    "central information commission": "AUTH_ID:CIC",
    "cic": "AUTH_ID:CIC",
    "केंद्रीय सूचना आयोग": "AUTH_ID:CIC",
    "केन्द्रीय सूचना आयोग": "AUTH_ID:CIC",
}


def to_ascii_digits(text: str) -> str:
    """Convert any Devanagari numerals to standard ASCII digits."""
    return text.translate(DEVANAGARI_DIGITS)


class StructuredInvariantEngine:
    """Extracts and normalizes legal invariants across English and Hindi."""

    @classmethod
    def normalize_currency(cls, text: str, lang: LanguageCode) -> str | None:
        """Normalize currency amounts to canonical INR:XX.XX format."""
        s = to_ascii_digits(text.strip().lower())
        # Try numeric matches
        match = re.search(r"(?:rs\.?|inr|₹|रु\.?)\s*([0-9]+(?:\.[0-9]{1,2})?)", s)
        if not match:
            match = re.search(r"([0-9]+(?:\.[0-9]{1,2})?)\s*(?:rupees|रुपये|रुपए)", s)
        if match:
            val = Decimal(match.group(1))
            return f"INR:{val:.2f}"

        # Try word-number matches (longer phrases checked first)
        if lang == LanguageCode.HI:
            for word, num_val in sorted(HINDI_NUMBER_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
                if word in s and any(k in s for k in ["रुपये", "रुपए", "रु"]):
                    return f"INR:{Decimal(num_val):.2f}"
        else:
            for word, num_val in sorted(ENGLISH_NUMBER_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
                if word in s and "rupee" in s:
                    return f"INR:{Decimal(num_val):.2f}"

        return None

    @classmethod
    def normalize_duration(cls, text: str, lang: LanguageCode) -> str | None:
        """Normalize durations to DURATION:N_UNIT (e.g. DURATION:30_DAYS, DURATION:48_HOURS)."""
        s = to_ascii_digits(text.strip().lower())
        # Check days
        match_days = re.search(r"([0-9]+)\s*(?:days?|दिन|दिवस)", s)
        if match_days:
            return f"DURATION:{int(match_days.group(1))}_DAYS"

        # Check hours
        match_hours = re.search(r"([0-9]+)\s*(?:hours?|hrs?|घंटे|घण्टे)", s)
        if match_hours:
            return f"DURATION:{int(match_hours.group(1))}_HOURS"

        # Check word-numbers (longer compound phrases checked first)
        if lang == LanguageCode.HI:
            for word, num in sorted(HINDI_NUMBER_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
                if word in s and any(d in s for d in ["दिन", "दिवस"]):
                    return f"DURATION:{num}_DAYS"
                if word in s and any(h in s for h in ["घंटे", "घण्टे"]):
                    return f"DURATION:{num}_HOURS"
        else:
            for word, num in sorted(ENGLISH_NUMBER_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
                if word in s and "day" in s:
                    return f"DURATION:{num}_DAYS"
                if word in s and "hour" in s:
                    return f"DURATION:{num}_HOURS"

        return None

    @classmethod
    def normalize_percentage(cls, text: str, lang: LanguageCode) -> str | None:
        """Normalize percentages to PERCENT:XX.X format."""
        s = to_ascii_digits(text.strip().lower())
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent|प्रतिशत)", s)
        if match:
            return f"PERCENT:{float(match.group(1)):.1f}"
        if "half" in s or "आधा" in s:
            return "PERCENT:50.0"
        return None

    @classmethod
    def normalize_section_id(cls, text: str) -> str | None:
        """Normalize statutory references (e.g. Section 6(1), धारा 6(1))."""
        s = to_ascii_digits(text.strip().lower())
        # Section patterns
        match_sec = re.search(r"(?:section|sec\.?|धारा)\s*([0-9]+(?:\([0-9a-z]+\))*)", s)
        if match_sec:
            return f"SEC_ID:{match_sec.group(1)}"
        # Rule patterns
        match_rule = re.search(r"(?:rule|नियम)\s*([0-9]+(?:\([0-9a-z]+\))*)", s)
        if match_rule:
            return f"RULE_ID:{match_rule.group(1)}"
        return None

    @classmethod
    def normalize_authority(cls, text: str) -> str | None:
        """Normalize designated statutory authorities."""
        s = to_ascii_digits(text.strip().lower())
        for raw_title, auth_id in AUTHORITY_MAP.items():
            if raw_title in s:
                return auth_id
        return None

    @classmethod
    def extract_invariants(cls, text: str, lang: LanguageCode) -> list[Invariant]:
        """Scan text and extract all recognized normalized legal invariants."""
        invariants: list[Invariant] = []
        # Normalization scans across lines and sentences
        sentences = re.split(r"[.\n।]+", text)
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue

            # Currency
            curr = cls.normalize_currency(sent_clean, lang)
            if curr:
                invariants.append(
                    Invariant(
                        type=InvariantType.CURRENCY,
                        raw_surface_form=sent_clean,
                        normalized_value=curr,
                        language=lang,
                    )
                )

            # Duration
            dur = cls.normalize_duration(sent_clean, lang)
            if dur:
                invariants.append(
                    Invariant(
                        type=InvariantType.DURATION,
                        raw_surface_form=sent_clean,
                        normalized_value=dur,
                        language=lang,
                    )
                )

            # Percentage
            pct = cls.normalize_percentage(sent_clean, lang)
            if pct:
                invariants.append(
                    Invariant(
                        type=InvariantType.PERCENTAGE,
                        raw_surface_form=sent_clean,
                        normalized_value=pct,
                        language=lang,
                    )
                )

            # Section ID
            sec = cls.normalize_section_id(sent_clean)
            if sec:
                invariants.append(
                    Invariant(
                        type=InvariantType.SECTION_ID,
                        raw_surface_form=sent_clean,
                        normalized_value=sec,
                        language=lang,
                    )
                )

            # Authority
            auth = cls.normalize_authority(sent_clean)
            if auth:
                invariants.append(
                    Invariant(
                        type=InvariantType.AUTHORITY,
                        raw_surface_form=sent_clean,
                        normalized_value=auth,
                        language=lang,
                    )
                )

        # Deduplicate by normalized_value
        unique_map: dict[str, Invariant] = {}
        for inv in invariants:
            if inv.normalized_value not in unique_map:
                unique_map[inv.normalized_value] = inv
        return list(unique_map.values())

    @classmethod
    def compare_bilingual_invariants(
        cls, en_invariants: list[Invariant], hi_invariants: list[Invariant]
    ) -> tuple[bool, list[str]]:
        """Compare normalized invariants between English and Hindi briefs.

        Returns (True, []) if sets of normalized values are identical.
        Returns (False, discrepancies) if there is any mismatch.
        """
        en_set = {inv.normalized_value for inv in en_invariants}
        hi_set = {inv.normalized_value for inv in hi_invariants}

        missing_in_hi = en_set - hi_set
        missing_in_en = hi_set - en_set

        discrepancies: list[str] = []
        for item in sorted(missing_in_hi):
            discrepancies.append(f"Invariant '{item}' present in English brief but missing in Hindi brief.")
        for item in sorted(missing_in_en):
            discrepancies.append(f"Invariant '{item}' present in Hindi brief but missing in English brief.")

        return (len(discrepancies) == 0, discrepancies)

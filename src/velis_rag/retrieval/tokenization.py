"""Multilingual tokenizer supporting English and Hindi (Devanagari) without destructive transliteration."""

from __future__ import annotations

from typing import cast

import regex

# Matches consecutive sequences of Unicode Letters (\p{L}), Marks (\p{M}), and Numbers (\p{N}).
# This preserves Devanagari words intact with all vowel signs (matras) and combining characters,
# as well as Latin words and numeric identifiers (e.g. section numbers '6', '12').
_TOKEN_PATTERN = regex.compile(r"[\p{L}\p{M}\p{N}]+", regex.UNICODE)


def tokenize_multilingual(text: str) -> list[str]:
    """Tokenize English and Hindi text into Unicode word tokens.

    Preserves Devanagari vowel signs, virama, anusvara, and numbers.
    Case-folds Latin characters to lowercase.
    """
    if not text:
        return []
    cleaned = text.lower().strip()
    return cast(list[str], _TOKEN_PATTERN.findall(cleaned))


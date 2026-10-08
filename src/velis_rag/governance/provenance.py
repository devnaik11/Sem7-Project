"""Cryptographic dual-hash calculation and text normalization utilities."""

import hashlib
import re
import unicodedata


def is_valid_sha256(hash_str: str) -> bool:
    """Verify whether a string is a valid 64-character lowercase hex SHA-256 digest."""
    if not isinstance(hash_str, str):
        return False
    return bool(re.match(r"^[0-9a-f]{64}$", hash_str.strip().lower()))


def is_placeholder_hash(hash_str: str) -> bool:
    """Check whether a hash string is a placeholder or template string."""
    if not isinstance(hash_str, str):
        return True
    s = hash_str.lower()
    return "placeholder" in s or "dummy" in s or not is_valid_sha256(s)


def normalize_text(text: str) -> str:
    """Normalize extracted text canonically (Unicode NFC, strip BOM, normalize whitespace)."""
    if not text:
        return ""
    # Strip Byte Order Mark (BOM) if present
    text = text.lstrip("\ufeff")
    # Unicode Normalization Form C (canonical decomposition followed by canonical composition)
    text = unicodedata.normalize("NFC", text)
    # Standardize line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple spaces and horizontal whitespace within lines while preserving line breaks
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in text.split("\n")]
    # Strip leading and trailing empty lines, collapse more than 2 consecutive blank lines to 1
    cleaned: list[str] = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)
    return "\n".join(cleaned).strip()


def compute_raw_bytes_sha256(raw_bytes: bytes) -> str:
    """Calculate SHA-256 digest directly from downloaded raw file bytes."""
    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise TypeError(f"Expected bytes or bytearray, got {type(raw_bytes).__name__}")
    hasher = hashlib.sha256()
    hasher.update(raw_bytes)
    return hasher.hexdigest().lower()


def compute_normalized_text_sha256(text: str) -> str:
    """Calculate SHA-256 digest from canonically normalized UTF-8 text."""
    normalized = normalize_text(text)
    hasher = hashlib.sha256()
    hasher.update(normalized.encode("utf-8"))
    return hasher.hexdigest().lower()


def verify_dual_hash(
    raw_bytes: bytes,
    text: str,
    expected_raw_hash: str,
    expected_norm_hash: str,
) -> tuple[bool, str]:
    """Verify both raw-byte hash and normalized-text hash against expected digests."""
    if is_placeholder_hash(expected_raw_hash):
        return False, "Expected raw hash is a placeholder or malformed."
    if is_placeholder_hash(expected_norm_hash):
        return False, "Expected normalized hash is a placeholder or malformed."

    computed_raw = compute_raw_bytes_sha256(raw_bytes)
    if computed_raw != expected_raw_hash.strip().lower():
        return False, f"Raw bytes SHA-256 mismatch: expected {expected_raw_hash}, computed {computed_raw}"

    computed_norm = compute_normalized_text_sha256(text)
    if computed_norm != expected_norm_hash.strip().lower():
        return False, f"Normalized text SHA-256 mismatch: expected {expected_norm_hash}, computed {computed_norm}"

    return True, "Dual-hash verification passed."

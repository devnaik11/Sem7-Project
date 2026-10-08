"""Tests for raw-byte and normalized-text cryptographic SHA-256 provenance."""

import hashlib

import pytest

from velis_rag.governance.provenance import (
    compute_normalized_text_sha256,
    compute_raw_bytes_sha256,
    is_placeholder_hash,
    is_valid_sha256,
    normalize_text,
    verify_dual_hash,
)


def test_raw_bytes_sha256_empty() -> None:
    """Test standard empty byte array SHA-256 test vector."""
    empty_bytes = b""
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert compute_raw_bytes_sha256(empty_bytes) == expected


def test_raw_bytes_sha256_known_vector() -> None:
    """Test raw-byte SHA-256 against standard hashlib reference."""
    payload = b"RTI_ACT_2005_SECTION_6_STATUTORY_TEXT_DATA"
    expected = hashlib.sha256(payload).hexdigest().lower()
    assert compute_raw_bytes_sha256(payload) == expected


def test_raw_bytes_sha256_type_rejection() -> None:
    """Test that passing non-bytes raises TypeError."""
    with pytest.raises(TypeError, match="Expected bytes"):
        compute_raw_bytes_sha256("string_not_bytes")  # type: ignore[arg-type]


def test_normalized_text_sha256_invariance() -> None:
    raw_text_1 = "Section 6(1): An application shall be made in writing.\n\nFee is Rs. 10."
    raw_text_2 = "\ufeff  Section 6(1):   An application shall be made in writing.  \r\n\r\nFee is Rs. 10.  \n"

    # Both must produce identical normalized strings and identical hashes
    norm_1 = normalize_text(raw_text_1)
    norm_2 = normalize_text(raw_text_2)
    assert norm_1 == norm_2

    hash_1 = compute_normalized_text_sha256(raw_text_1)
    hash_2 = compute_normalized_text_sha256(raw_text_2)
    assert hash_1 == hash_2
    assert is_valid_sha256(hash_1)


def test_is_placeholder_hash() -> None:
    """Test identification of placeholder hash strings."""
    assert is_placeholder_hash("PLACEHOLDER_HASH_RAW_BYTES")
    assert is_placeholder_hash("<PLACEHOLDER_HASH>")
    assert is_placeholder_hash("dummy_hash_value")
    assert is_placeholder_hash("12345")  # Too short
    assert not is_placeholder_hash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")


def test_verify_dual_hash_success() -> None:
    """Test successful dual-hash verification."""
    raw_bytes = b"Sample government gazette notification byte stream"
    text = "Sample government gazette notification byte stream"

    raw_hash = compute_raw_bytes_sha256(raw_bytes)
    norm_hash = compute_normalized_text_sha256(text)

    ok, msg = verify_dual_hash(raw_bytes, text, raw_hash, norm_hash)
    assert ok is True
    assert "passed" in msg


def test_verify_dual_hash_rejections() -> None:
    """Test that dual-hash verification fails on mismatched or placeholder hashes."""
    raw_bytes = b"Official bytes"
    text = "Official bytes"
    raw_hash = compute_raw_bytes_sha256(raw_bytes)
    norm_hash = compute_normalized_text_sha256(text)

    # 1. Mismatched raw hash
    bad_raw = "0" * 64
    ok, msg = verify_dual_hash(raw_bytes, text, bad_raw, norm_hash)
    assert ok is False
    assert "Raw bytes SHA-256 mismatch" in msg

    # 2. Mismatched normalized text hash
    bad_norm = "1" * 64
    ok, msg = verify_dual_hash(raw_bytes, text, raw_hash, bad_norm)
    assert ok is False
    assert "Normalized text SHA-256 mismatch" in msg

    # 3. Placeholder hash rejected
    ok, msg = verify_dual_hash(raw_bytes, text, "PLACEHOLDER_HASH", norm_hash)
    assert ok is False
    assert "placeholder" in msg

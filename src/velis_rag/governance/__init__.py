"""Governance and provenance package."""

from velis_rag.governance.provenance import (
    compute_normalized_text_sha256,
    compute_raw_bytes_sha256,
    is_placeholder_hash,
    is_valid_sha256,
    normalize_text,
    verify_dual_hash,
)
from velis_rag.governance.registry import SourceRegistry

__all__ = [
    "SourceRegistry",
    "compute_normalized_text_sha256",
    "compute_raw_bytes_sha256",
    "is_placeholder_hash",
    "is_valid_sha256",
    "normalize_text",
    "verify_dual_hash",
]

# VeLiS-RAG Provenance & Integrity Architecture

Every document and passage chunk ingested into VeLiS-RAG carries cryptographic proof of origin and integrity.

## Dual-Hash Mechanism
1. **`raw_file_sha256`:**
   - Computed immediately upon download from the exact raw file bytes before any parsing or decoding.
   - Preserved alongside the archived original file in `data/raw/`.
   - Protects against file corruption, upstream tampering, and parsing drift.
2. **`extracted_text_sha256`:**
   - Computed on the normalized UTF-8 text representation after structural parsing and canonical whitespace/unicode normalization.
   - Binds the retrieval passage text directly to the database record.

## Runtime Rejection of Placeholder Hashes
- In documentation and schema templates, placeholders like `"PLACEHOLDER_HASH"` are permitted for illustration only.
- In runtime ingestion and verification components, **placeholder hashes are strictly rejected**.
- Runtime validators require a valid 64-character lowercase hexadecimal string (`^[0-9a-f]{64}$`).

## Metadata Provenance Fields
Every passage chunk links back to its parent document through:
- `document_id`: Unique identifier (e.g. `RTI-ACT-2005-CENTRAL`).
- `source_url`: Canonical official source URL.
- `download_timestamp`: ISO 8601 UTC timestamp of acquisition.
- `document_version`: Version or amendment status (e.g. `As amended by Act 24 of 2019`).
- `section_hierarchy`: Breadcrumb array (e.g. `["Chapter II", "Section 6", "Sub-section 1"]`).
- `source_tier`: `Tier_A`, `Tier_B`, or `Tier_C`.
- `license_and_reuse_basis`: Statutory exemption or specific open government license.

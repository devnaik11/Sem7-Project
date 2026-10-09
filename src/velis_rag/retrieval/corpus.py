"""Retrieval corpus loader: extracts and strictly validates Tier-A records from SQLite catalog."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from velis_rag.retrieval.document_registry import OFFICIAL_DOCUMENTS
from velis_rag.retrieval.models import RetrievalRecord

DEFAULT_CATALOG_DB = Path("data/processed/catalog.db")


def load_retrieval_corpus(db_path: Path | None = None) -> list[RetrievalRecord]:
    """Load and validate all eligible Tier-A chunks from the SQLite catalog.

    Enforces strict governance constraints:
      - Only Tier_A chunks are accepted; any non-Tier-A chunk triggers an error.
      - Chunks missing provenance, locators, or cryptographic hashes are rejected.
      - Document metadata (title, issuing authority, jurisdiction) is joined deterministically.
    """
    path = db_path or DEFAULT_CATALOG_DB
    if not path.exists():
        raise FileNotFoundError(f"SQLite catalog database not found at {path}")

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            chunk_id,
            document_id,
            chunk_index,
            source_id,
            canonical_url,
            delivery_url,
            raw_file_sha256,
            norm_doc_text_sha256,
            trust_tier,
            page_start,
            page_end,
            hierarchy_path_json,
            citation_locator,
            doc_version,
            effective_date,
            original_text,
            normalized_text,
            chunk_text_sha256,
            extraction_status,
            invariants_json
        FROM chunks
        ORDER BY document_id, chunk_index
        """
    )
    rows = cursor.fetchall()
    conn.close()

    records: list[RetrievalRecord] = []
    for r in rows:
        doc_id = r["document_id"]
        if doc_id not in OFFICIAL_DOCUMENTS:
            raise ValueError(f"Unregistered document identifier in chunks catalog: '{doc_id}'")

        doc_meta = OFFICIAL_DOCUMENTS[doc_id]

        # Enforce governance tier
        if r["trust_tier"] != "Tier_A":
            raise ValueError(
                f"Governance violation: Chunk '{r['chunk_id']}' has tier '{r['trust_tier']}', "
                "only Tier_A chunks are eligible for retrieval indexing."
            )

        hierarchy_path = json.loads(r["hierarchy_path_json"]) if r["hierarchy_path_json"] else []
        invariants = json.loads(r["invariants_json"]) if r["invariants_json"] else []

        record = RetrievalRecord(
            chunk_id=r["chunk_id"],
            document_id=doc_id,
            chunk_index=r["chunk_index"],
            source_id=r["source_id"],
            document_title=doc_meta.title,
            canonical_url=r["canonical_url"],
            delivery_url=r["delivery_url"],
            page_start=r["page_start"],
            page_end=r["page_end"],
            citation_locator=r["citation_locator"],
            hierarchy_path=hierarchy_path,
            trust_tier=r["trust_tier"],
            doc_version=r["doc_version"],
            effective_date=r["effective_date"],
            issuing_authority=doc_meta.issuing_authority,
            jurisdiction=doc_meta.jurisdiction,
            doc_type=doc_meta.doc_type,
            original_text=r["original_text"],
            normalized_text=r["normalized_text"],
            raw_file_sha256=r["raw_file_sha256"],
            norm_doc_text_sha256=r["norm_doc_text_sha256"],
            chunk_text_sha256=r["chunk_text_sha256"],
            extraction_status=r["extraction_status"],
            invariants=invariants,
        )
        records.append(record)

    return records

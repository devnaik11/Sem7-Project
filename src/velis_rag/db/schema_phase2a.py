"""Phase 2A SQLite schema: document-page, extraction, hierarchy, and chunk tables.

These tables extend the Phase 1 catalog (data/processed/catalog.db).
Run this module as a script to apply migrations.

Usage:
    .venv/Scripts/python.exe -m velis_rag.db.schema_phase2a
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent  # repo root
DEFAULT_DB = ROOT / "data" / "processed" / "catalog.db"

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------
MIGRATIONS: list[str] = [
    # Phase 1 table (idempotent, may already exist)
    """
    CREATE TABLE IF NOT EXISTS ingested_documents (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id           TEXT    NOT NULL,
        doc_type            TEXT    NOT NULL,
        canonical_url       TEXT    NOT NULL,
        delivery_url        TEXT    NOT NULL,
        local_filename      TEXT    NOT NULL,
        trust_tier          TEXT    NOT NULL,
        raw_file_sha256     TEXT    NOT NULL,
        norm_text_sha256    TEXT    NOT NULL,
        page_count          INTEGER NOT NULL,
        byte_size           INTEGER NOT NULL,
        ingested_at         TEXT    NOT NULL
    );
    """,
    # Page-level extraction results
    """
    CREATE TABLE IF NOT EXISTS document_pages (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id         TEXT    NOT NULL,
        page_number         INTEGER NOT NULL,
        raw_text            TEXT    NOT NULL,
        normalized_text     TEXT    NOT NULL,
        char_count          INTEGER NOT NULL,
        word_count          INTEGER NOT NULL,
        extraction_status   TEXT    NOT NULL,
        quarantine_reason   TEXT,
        extracted_at        TEXT    NOT NULL,
        UNIQUE(document_id, page_number)
    );
    """,
    # Hierarchy nodes
    """
    CREATE TABLE IF NOT EXISTS hierarchy_nodes (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id         TEXT    NOT NULL,
        node_type           TEXT    NOT NULL,
        label               TEXT    NOT NULL,
        title               TEXT,
        page_start          INTEGER NOT NULL,
        page_end            INTEGER,
        depth               INTEGER NOT NULL,
        parent_path_json    TEXT    NOT NULL,
        detected_at         TEXT    NOT NULL
    );
    """,
    # Full-provenance chunks
    """
    CREATE TABLE IF NOT EXISTS chunks (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        chunk_id                TEXT    NOT NULL UNIQUE,
        document_id             TEXT    NOT NULL,
        chunk_index             INTEGER NOT NULL,
        source_id               TEXT    NOT NULL,
        canonical_url           TEXT    NOT NULL,
        delivery_url            TEXT    NOT NULL,
        raw_file_sha256         TEXT    NOT NULL,
        norm_doc_text_sha256    TEXT    NOT NULL,
        trust_tier              TEXT    NOT NULL,
        page_start              INTEGER NOT NULL,
        page_end                INTEGER NOT NULL,
        hierarchy_path_json     TEXT    NOT NULL,
        citation_locator        TEXT    NOT NULL,
        doc_version             TEXT    NOT NULL,
        effective_date          TEXT,
        original_text           TEXT    NOT NULL,
        normalized_text         TEXT    NOT NULL,
        chunk_text_sha256       TEXT    NOT NULL,
        extraction_status       TEXT    NOT NULL,
        invariants_json         TEXT    NOT NULL,
        chunked_at              TEXT    NOT NULL
    );
    """,
    # Quarantine log
    """
    CREATE TABLE IF NOT EXISTS quarantine_log (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id         TEXT    NOT NULL,
        page_number         INTEGER,
        reason              TEXT    NOT NULL,
        logged_at           TEXT    NOT NULL
    );
    """,
]

INDEXES: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_trust_tier  ON chunks(trust_tier);",
    "CREATE INDEX IF NOT EXISTS idx_pages_document_id  ON document_pages(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_hierarchy_doc_id   ON hierarchy_nodes(document_id);",
]


def apply_migrations(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    """Create or update the catalog database with Phase 2A tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    for ddl in MIGRATIONS:
        conn.execute(ddl)
    for idx in INDEXES:
        conn.execute(idx)
    conn.commit()
    return conn


if __name__ == "__main__":
    conn = apply_migrations()
    conn.close()
    print(f"Phase 2A schema applied to: {DEFAULT_DB}")

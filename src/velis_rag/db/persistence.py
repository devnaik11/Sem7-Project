"""SQLite persistence helpers for Phase 2A extraction and chunking results."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from velis_rag.models.phase2a import HierarchyNode, PageExtractionResult, PhaseChunk


def _now() -> str:
    return datetime.now(UTC).isoformat()


def insert_pages(conn: sqlite3.Connection, pages: list[PageExtractionResult]) -> None:
    """Upsert page extraction results into document_pages."""
    for pr in pages:
        conn.execute(
            """
            INSERT OR REPLACE INTO document_pages
                (document_id, page_number, raw_text, normalized_text,
                 char_count, word_count, extraction_status, quarantine_reason, extracted_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                pr.document_id,
                pr.page_number,
                pr.raw_text,
                pr.normalized_text,
                pr.char_count,
                pr.word_count,
                pr.status.value,
                pr.quarantine_reason,
                _now(),
            ),
        )
    conn.commit()


def insert_hierarchy(conn: sqlite3.Connection, document_id: str, nodes: list[HierarchyNode]) -> None:
    """Insert hierarchy nodes into hierarchy_nodes table."""
    ts = _now()
    for node in nodes:
        conn.execute(
            """
            INSERT INTO hierarchy_nodes
                (document_id, node_type, label, title, page_start, page_end,
                 depth, parent_path_json, detected_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                document_id,
                node.node_type.value,
                node.label,
                node.title,
                node.page_start,
                node.page_end,
                node.depth,
                json.dumps(node.parent_path),
                ts,
            ),
        )
    conn.commit()


def insert_chunks(conn: sqlite3.Connection, chunks: list[PhaseChunk]) -> None:
    """Insert provenance-bound chunks into chunks table."""
    ts = _now()
    for ch in chunks:
        conn.execute(
            """
            INSERT OR IGNORE INTO chunks
                (chunk_id, document_id, chunk_index, source_id,
                 canonical_url, delivery_url, raw_file_sha256,
                 norm_doc_text_sha256, trust_tier, page_start, page_end,
                 hierarchy_path_json, citation_locator, doc_version,
                 effective_date, original_text, normalized_text,
                 chunk_text_sha256, extraction_status, invariants_json, chunked_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                ch.chunk_id,
                ch.document_id,
                ch.chunk_index,
                ch.source_id,
                ch.canonical_url,
                ch.delivery_url,
                ch.raw_file_sha256,
                ch.norm_doc_text_sha256,
                ch.trust_tier,
                ch.page_start,
                ch.page_end,
                json.dumps(ch.hierarchy_path),
                ch.citation_locator,
                ch.doc_version,
                ch.effective_date,
                ch.original_text,
                ch.normalized_text,
                ch.chunk_text_sha256,
                ch.extraction_status.value,
                json.dumps(ch.invariants),
                ts,
            ),
        )
    conn.commit()


def log_quarantine(conn: sqlite3.Connection, document_id: str, page_number: int | None, reason: str) -> None:
    conn.execute(
        "INSERT INTO quarantine_log (document_id, page_number, reason, logged_at) VALUES (?,?,?,?)",
        (document_id, page_number, reason, _now()),
    )
    conn.commit()

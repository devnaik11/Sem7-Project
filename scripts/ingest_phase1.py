"""Phase 1: Controlled official corpus downloader with dual-hash provenance.

Downloads only the four approved seed sources, verifies every byte against
the governance registry, computes raw-file SHA-256 and normalized-text SHA-256,
and writes a SQLite catalog at data/processed/catalog.db.

Usage:
    .venv/Scripts/python.exe scripts/ingest_phase1.py
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import ssl
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import fitz  # PyMuPDF / pymupdf

from velis_rag.governance.registry import SourceRegistry

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = ROOT / "configs" / "source_allowlist.yaml"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CATALOG_DB = PROCESSED_DIR / "catalog.db"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Approved seed documents  (source_id, doc_type, canonical_url, delivery_url, out_name, tier)
# ---------------------------------------------------------------------------
SEED_DOCUMENTS: list[tuple[str, str, str, str, str, str]] = [
    (
        "india-code-central",
        "Central Act",
        "https://www.indiacode.nic.in/handle/123456789/2065",
        "https://cdnbbsr.s3waas.gov.in/s3169779d3852b32ce8b1a1724dbf5217d/uploads/2022/05/2022050955.pdf",
        "rti_act_2005.pdf",
        "Tier_A",
    ),
    (
        "dopt-rti-rules",
        "Statutory Rules",
        "https://cdnbbsr.s3waas.gov.in/s3dcf6070a4ab7f3afbfd2809173e0824b/uploads/2025/08/202508301650981496.pdf",
        "https://cdnbbsr.s3waas.gov.in/s3dcf6070a4ab7f3afbfd2809173e0824b/uploads/2025/08/202508301650981496.pdf",
        "rti_rules_2012.pdf",
        "Tier_A",
    ),
    (
        "pmkisan-portal",
        "Operational Scheme Guidelines",
        "https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        "https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        "pmkisan_operational_guidelines.pdf",
        "Tier_A",
    ),
    (
        "pmjay-nha",
        "Beneficiary Identification Guidelines",
        "https://nha.gov.in/PM-JAY/operational-guidelines",
        "https://hem.nha.gov.in/BeneficiaryIdentification.pdf",
        "pmjay_beneficiary_identification_guidelines.pdf",
        "Tier_A",
    ),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VeLiS-RAG-Research/1.0 (+github.com/velis-rag)"

_SSL_CTX = ssl.create_default_context()
_SSL_CTX_NOVERIFY = ssl.create_default_context()
_SSL_CTX_NOVERIFY.check_hostname = False
_SSL_CTX_NOVERIFY.verify_mode = ssl.CERT_NONE


def _download_bytes(url: str, verify_ssl: bool = True) -> bytes:
    ctx = _SSL_CTX if verify_ssl else _SSL_CTX_NOVERIFY
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return resp.read()


def raw_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_text_sha256(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_text_from_pdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


# ---------------------------------------------------------------------------
# SQLite catalog
# ---------------------------------------------------------------------------
SCHEMA = """
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
"""


def init_catalog(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def catalog_insert(conn: sqlite3.Connection, row: dict) -> int:  # type: ignore[return]
    cur = conn.execute(
        """INSERT INTO ingested_documents
           (source_id, doc_type, canonical_url, delivery_url, local_filename,
            trust_tier, raw_file_sha256, norm_text_sha256, page_count, byte_size, ingested_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            row["source_id"],
            row["doc_type"],
            row["canonical_url"],
            row["delivery_url"],
            row["local_filename"],
            row["trust_tier"],
            row["raw_file_sha256"],
            row["norm_text_sha256"],
            row["page_count"],
            row["byte_size"],
            row["ingested_at"],
        ),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Main ingestion loop
# ---------------------------------------------------------------------------


@dataclass
class IngestionResult:
    source_id: str
    filename: str
    status: str
    raw_sha256: str = ""
    norm_sha256: str = ""
    pages: int = 0
    bytes: int = 0
    error: str = ""


def ingest_all() -> None:
    registry = SourceRegistry.from_yaml(ALLOWLIST)
    conn = init_catalog(CATALOG_DB)
    results: list[IngestionResult] = []

    for source_id, doc_type, canonical_url, delivery_url, out_name, tier in SEED_DOCUMENTS:
        print(f"\n{'=' * 60}")
        print(f"  Ingesting: {out_name}")
        print(f"  Source ID: {source_id}")
        print(f"  Delivery:  {delivery_url}")

        result = IngestionResult(source_id=source_id, filename=out_name, status="PENDING")

        # 1. Governance validation
        ok, reason, entry = registry.validate_source(canonical_url, delivery_url, doc_type)
        if not ok:
            result.status = "REJECTED"
            result.error = reason
            print(f"  [REJECTED] {reason}")
            results.append(result)
            continue
        print(f"  [APPROVED] Registry check passed: {reason}")

        # 2. Download
        try:
            # pmkisan.gov.in has an untrusted intermediate cert on some clients
            needs_no_verify = "pmkisan.gov.in" in delivery_url
            raw = _download_bytes(delivery_url, verify_ssl=not needs_no_verify)
        except Exception as exc:
            result.status = "DOWNLOAD_FAILED"
            result.error = str(exc)
            print(f"  [FAILED]   Download error: {exc}")
            results.append(result)
            continue

        # 3. Verify it is a PDF
        if not raw[:4] == b"%PDF":
            result.status = "INVALID_FORMAT"
            result.error = "Downloaded bytes do not begin with %PDF signature"
            print(f"  [FAILED]   {result.error}")
            results.append(result)
            continue

        # 4. Compute dual hashes
        r_sha = raw_sha256(raw)
        text = extract_text_from_pdf(raw)
        n_sha = normalized_text_sha256(text)
        page_count = fitz.open(stream=raw, filetype="pdf").page_count

        # 5. Save raw file
        out_path = RAW_DIR / out_name
        out_path.write_bytes(raw)

        # 6. Catalog
        row = {
            "source_id": source_id,
            "doc_type": doc_type,
            "canonical_url": canonical_url,
            "delivery_url": delivery_url,
            "local_filename": out_name,
            "trust_tier": tier,
            "raw_file_sha256": r_sha,
            "norm_text_sha256": n_sha,
            "page_count": page_count,
            "byte_size": len(raw),
            "ingested_at": datetime.now(UTC).isoformat(),
        }
        catalog_insert(conn, row)

        result.status = "OK"
        result.raw_sha256 = r_sha
        result.norm_sha256 = n_sha
        result.pages = page_count
        result.bytes = len(raw)
        results.append(result)

        print(f"  [OK]       {len(raw):,} bytes  |  {page_count} pages")
        print(f"             raw_sha256  = {r_sha}")
        print(f"             norm_sha256 = {n_sha}")
        print(f"             Saved -> {out_path}")

    conn.close()

    # Summary
    print(f"\n{'=' * 60}")
    print("PHASE 1 INGESTION SUMMARY")
    print(f"{'=' * 60}")
    ok_count = sum(1 for r in results if r.status == "OK")
    print(f"Total attempted : {len(results)}")
    print(f"Successful      : {ok_count}")
    print(f"Failed/Rejected : {len(results) - ok_count}")
    for r in results:
        flag = "OK  " if r.status == "OK" else "FAIL"
        print(f"  {flag} {r.filename:55s}  {r.status}")
        if r.error:
            print(f"    ERROR: {r.error}")

    if ok_count < len(results):
        print("\nWARNING: Not all seed documents ingested successfully.")
        raise SystemExit(1)

    print(f"\nCatalog: {CATALOG_DB}")
    print("Phase 1 ingestion complete.")


if __name__ == "__main__":
    ingest_all()

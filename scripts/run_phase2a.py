"""Phase 2A runner: structural extraction, bilingual chunking, and provenance catalog.

Processes all four Tier-A seed PDFs from data/raw/ through the full pipeline:
  extraction → quality check → hierarchy parse → chunking → SQLite persistence

Usage:
    .venv/Scripts/python.exe scripts/run_phase2a.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from velis_rag.chunking.chunker import DocumentMeta, build_chunks
from velis_rag.chunking.legal_parser import parse_hierarchy
from velis_rag.db.persistence import insert_chunks, insert_hierarchy, insert_pages, log_quarantine
from velis_rag.db.schema_phase2a import DEFAULT_DB, apply_migrations
from velis_rag.extraction.pdf_extractor import extract_pages
from velis_rag.models.phase2a import ExtractionStatus

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# Document registry: ties filename → Phase 1 catalog metadata
# ---------------------------------------------------------------------------
DOCUMENTS: list[DocumentMeta] = [
    DocumentMeta(
        document_id="rti_act_2005",
        source_id="india-code-central",
        canonical_url="https://www.indiacode.nic.in/handle/123456789/2065",
        delivery_url="https://cdnbbsr.s3waas.gov.in/s3169779d3852b32ce8b1a1724dbf5217d/uploads/2022/05/2022050955.pdf",
        raw_file_sha256="489cf9bc21c775117503c54f2df7402905b94c83d4a40b72456454157bdb7159",
        norm_doc_text_sha256="df2e7d1a0e7f61953cbc6e2e83314d14ca07c47277a18ac33c76efac97092cf6",
        trust_tier="Tier_A",
        doc_version="Act No. 22 of 2005 (as amended 2019)",
        effective_date="2005-10-12",
        issuing_authority="Ministry of Personnel, Public Grievances and Pensions",
        local_filename="rti_act_2005.pdf",
        doc_type="Central Act",
    ),
    DocumentMeta(
        document_id="rti_rules_2012",
        source_id="dopt-rti-rules",
        canonical_url="https://cdnbbsr.s3waas.gov.in/s3dcf6070a4ab7f3afbfd2809173e0824b/uploads/2025/08/202508301650981496.pdf",
        delivery_url="https://cdnbbsr.s3waas.gov.in/s3dcf6070a4ab7f3afbfd2809173e0824b/uploads/2025/08/202508301650981496.pdf",
        raw_file_sha256="69ff4f337ef8d84dc8e0432d4196c7610649f1c432e71c908ed32da4f4918168",
        norm_doc_text_sha256="81da3586d6a1fcc62b13c648cd926c8881246abab9ee8d25c819ed6ba9a0e4f9",
        trust_tier="Tier_A",
        doc_version="G.S.R. 603(E) dated 31 July 2012",
        effective_date="2012-07-31",
        issuing_authority="Ministry of Personnel, Public Grievances and Pensions",
        local_filename="rti_rules_2012.pdf",
        doc_type="Statutory Rules",
    ),
    DocumentMeta(
        document_id="pmkisan_guidelines",
        source_id="pmkisan-portal",
        canonical_url="https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        delivery_url="https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        raw_file_sha256="ae82cac83f61a5fa5049387a7c13e00c6d55cef0e9163deb5497dc86c86d697f",
        norm_doc_text_sha256="c1005a8a37c8eb8e70e73df5f4eb491ecc9ebee911750b65c7c957cc4f4a7430",
        trust_tier="Tier_A",
        doc_version="Revised Operational Guidelines (March 2020)",
        effective_date="2020-03-01",
        issuing_authority="Ministry of Agriculture and Farmers Welfare",
        local_filename="pmkisan_operational_guidelines.pdf",
        doc_type="Operational Scheme Guidelines",
    ),
    DocumentMeta(
        document_id="pmjay_big",
        source_id="pmjay-nha",
        canonical_url="https://nha.gov.in/PM-JAY/operational-guidelines",
        delivery_url="https://hem.nha.gov.in/BeneficiaryIdentification.pdf",
        raw_file_sha256="5ce0137307176a67e883d063bfe14ab62cd18f081c1aec6ddbb2b323dedd9b62",
        norm_doc_text_sha256="fa74d283079b94d40562c71a412736e403d3c73322c227336fead9670fca3a19",
        trust_tier="Tier_A",
        doc_version="NHA Beneficiary Identification Guidelines",
        effective_date=None,
        issuing_authority="National Health Authority",
        local_filename="pmjay_beneficiary_identification_guidelines.pdf",
        doc_type="Beneficiary Identification Guidelines",
    ),
]


def run_pipeline() -> None:
    print("=" * 65)
    print("VeLiS-RAG Phase 2A: Structural Extraction and Chunking")
    print("=" * 65)

    conn = apply_migrations(DEFAULT_DB)

    summary: list[dict[str, object]] = []

    for meta in DOCUMENTS:
        pdf_path = RAW_DIR / meta.local_filename
        if not pdf_path.exists():
            print(f"\n[SKIP] {meta.document_id}: PDF not found at {pdf_path}")
            continue

        print(f"\n{'-' * 65}")
        print(f"  Document : {meta.document_id}")
        print(f"  File     : {pdf_path.name}")

        # 1. Extract pages
        pages = extract_pages(pdf_path, meta.document_id)
        insert_pages(conn, pages)

        ok_pages = [p for p in pages if p.status == ExtractionStatus.OK]
        low_pages = [p for p in pages if p.status == ExtractionStatus.LOW_DENSITY]
        q_pages = [p for p in pages if p.status == ExtractionStatus.QUARANTINED]

        print(
            f"  Pages    : {len(pages)} total | {len(ok_pages)} OK | {len(low_pages)} low-density | {len(q_pages)} quarantined"
        )

        for qp in q_pages:
            log_quarantine(conn, meta.document_id, qp.page_number, qp.quarantine_reason or "unknown")
            print(f"  [QUARANTINE] Page {qp.page_number}: {qp.quarantine_reason}")

        # 2. Parse hierarchy
        page_tuples = [
            (p.page_number, p.normalized_text) for p in pages if p.status not in (ExtractionStatus.QUARANTINED,)
        ]
        hierarchy = parse_hierarchy(page_tuples, doc_type=meta.doc_type)
        insert_hierarchy(conn, meta.document_id, hierarchy)

        print(f"  Hierarchy: {len(hierarchy)} nodes detected")
        for node in hierarchy[:5]:  # preview first 5
            indent = "  " * node.depth
            print(f"    {indent}[{node.node_type.value}] {node.label} - p.{node.page_start}")

        # 3. Build chunks
        chunks = build_chunks(meta, pages, hierarchy)
        insert_chunks(conn, chunks)

        total_text = sum(len(c.normalized_text) for c in chunks)
        print(f"  Chunks   : {len(chunks)} | total normalized chars: {total_text:,}")

        summary.append(
            {
                "document_id": meta.document_id,
                "pages_total": len(pages),
                "pages_ok": len(ok_pages),
                "pages_quarantined": len(q_pages),
                "hierarchy_nodes": len(hierarchy),
                "chunks_total": len(chunks),
                "text_chars": total_text,
            }
        )

    conn.close()

    # Persist summary JSON for report generation
    summary_path = PROCESSED_DIR / "phase2a_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'=' * 65}")
    print("PHASE 2A PIPELINE COMPLETE")
    print(f"{'=' * 65}")
    print(f"{'Document':<30} {'Pages':>6} {'Nodes':>6} {'Chunks':>7}")
    print("-" * 55)
    for s in summary:
        print(f"  {s['document_id']:<28} {s['pages_total']:>6} {s['hierarchy_nodes']:>6} {s['chunks_total']:>7}")
    print(f"\nCatalog DB : {DEFAULT_DB}")
    print(f"Summary    : {summary_path}")


if __name__ == "__main__":
    run_pipeline()

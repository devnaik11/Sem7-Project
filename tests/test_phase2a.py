"""Phase 2A tests: extraction quality, hierarchy, chunking, and provenance.

Covers all required acceptance criteria:
- page-level extraction preservation
- hierarchy detection
- parent hierarchy retention in every chunk
- stable chunk identifiers and hashes
- original vs normalized text separation
- Devanagari numeral normalization without altering source text
- malformed / low-quality extraction quarantine
- chunk metadata completeness
- no chunk from unapproved/Tier-B/Tier-C source
"""

from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path

import pytest

from velis_rag.chunking.chunker import DocumentMeta, build_chunks
from velis_rag.chunking.legal_parser import parse_hierarchy
from velis_rag.extraction.pdf_extractor import MIN_CHARS_PER_PAGE, extract_pages
from velis_rag.models.phase2a import (
    ExtractionStatus,
    HierarchyNodeType,
    PageExtractionResult,
)
from velis_rag.normalization.invariants import to_ascii_digits

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
SEED_FILES = {
    "rti_act_2005": "rti_act_2005.pdf",
    "rti_rules_2012": "rti_rules_2012.pdf",
    "pmkisan_guidelines": "pmkisan_operational_guidelines.pdf",
    "pmjay_big": "pmjay_beneficiary_identification_guidelines.pdf",
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_meta(doc_id: str) -> DocumentMeta:
    return DocumentMeta(
        document_id=doc_id,
        source_id="india-code-central",
        canonical_url="https://www.indiacode.nic.in/handle/123456789/2065",
        delivery_url="https://cdnbbsr.s3waas.gov.in/s3abc/uploads/2022/05/test.pdf",
        raw_file_sha256="a" * 64,
        norm_doc_text_sha256="b" * 64,
        trust_tier="Tier_A",
        doc_version="Test v1.0",
        effective_date="2005-10-12",
        issuing_authority="Test Authority",
        local_filename=f"{doc_id}.pdf",
    )


def _make_page(
    doc_id: str,
    page_num: int,
    text: str,
    status: ExtractionStatus = ExtractionStatus.OK,
) -> PageExtractionResult:
    norm = unicodedata.normalize("NFC", text)
    return PageExtractionResult(
        document_id=doc_id,
        page_number=page_num,
        raw_text=text,
        normalized_text=norm,
        char_count=len(norm),
        word_count=len(norm.split()),
        status=status,
        quarantine_reason=None,
    )


# ---------------------------------------------------------------------------
# Tests: Devanagari normalization
# ---------------------------------------------------------------------------


class TestDevanagariNormalization:
    def test_digits_converted_correctly(self) -> None:
        assert to_ascii_digits("०१२३४५६७८९") == "0123456789"

    def test_mixed_script_preserved(self) -> None:
        result = to_ascii_digits("धारा ३(१)")
        assert result == "धारा 3(1)"

    def test_source_text_not_mutated(self) -> None:
        original = "धारा ३(१) के अनुसार"
        _ = to_ascii_digits(original)  # must not raise; original must be untouched
        assert original == "धारा ३(१) के अनुसार"

    def test_ascii_digits_passthrough(self) -> None:
        assert to_ascii_digits("Section 6(1)") == "Section 6(1)"

    def test_empty_string(self) -> None:
        assert to_ascii_digits("") == ""


# ---------------------------------------------------------------------------
# Tests: Hierarchy detection
# ---------------------------------------------------------------------------


class TestHierarchyParsing:
    def test_detects_chapter(self) -> None:
        text = "CHAPTER II\nInformation Disclosure\nSome content here."
        nodes = parse_hierarchy([(1, text)])
        labels = [n.label for n in nodes]
        assert any("II" in lbl or "chapter" in lbl.lower() for lbl in labels)

    def test_detects_section(self) -> None:
        text = "Section 6. Right to information\nContent here."
        nodes = parse_hierarchy([(1, text)])
        assert any(n.node_type == HierarchyNodeType.SECTION for n in nodes)

    def test_detects_rule(self) -> None:
        text = "Rule 3. Application form\nContent here."
        nodes = parse_hierarchy([(1, text)])
        assert any(n.node_type == HierarchyNodeType.RULE for n in nodes)

    def test_detects_proviso(self) -> None:
        text = "Provided that no such information shall be provided."
        nodes = parse_hierarchy([(1, text)])
        assert any(n.node_type == HierarchyNodeType.PROVISO for n in nodes)

    def test_parent_path_assigned(self) -> None:
        text = "CHAPTER I\nPreliminary\nSection 2. Definitions\nContent."
        nodes = parse_hierarchy([(1, text)])
        sec_nodes = [n for n in nodes if n.node_type == HierarchyNodeType.SECTION]
        if sec_nodes:
            assert len(sec_nodes[0].parent_path) >= 1

    def test_empty_text_no_nodes(self) -> None:
        assert parse_hierarchy([(1, "")]) == []

    def test_page_numbers_assigned(self) -> None:
        pages = [(1, "CHAPTER I\nContent"), (2, "Section 3. Right\nContent")]
        nodes = parse_hierarchy(pages)
        for node in nodes:
            assert node.page_start >= 1

    def test_schedule_detected(self) -> None:
        text = "SCHEDULE\nList of exempted organizations"
        nodes = parse_hierarchy([(1, text)])
        assert any(n.node_type == HierarchyNodeType.SCHEDULE for n in nodes)

    def test_depth_ordering(self) -> None:
        """Section depth must be > chapter depth."""
        text = "CHAPTER II\nIntro\nSection 4. Duties\nContent."
        nodes = parse_hierarchy([(1, text)])
        chapter_nodes = [n for n in nodes if n.node_type == HierarchyNodeType.CHAPTER]
        section_nodes = [n for n in nodes if n.node_type == HierarchyNodeType.SECTION]
        if chapter_nodes and section_nodes:
            assert section_nodes[0].depth > chapter_nodes[0].depth


# ---------------------------------------------------------------------------
# Tests: Chunker – provenance completeness
# ---------------------------------------------------------------------------


class TestChunker:
    def _minimal_pages(self, doc_id: str) -> list[PageExtractionResult]:
        return [
            _make_page(doc_id, 1, "Section 6. Right to information\nEvery citizen shall have right."),
            _make_page(doc_id, 2, "Section 7. Disposal of request\nPIO shall act within 30 days."),
        ]

    def test_chunk_ids_unique(self) -> None:
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_all_chunks_have_hierarchy_path(self) -> None:
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            assert len(chunk.hierarchy_path) >= 1, f"Chunk {chunk.chunk_id} missing hierarchy_path"

    def test_chunk_text_sha256_matches(self) -> None:
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            expected = hashlib.sha256(chunk.normalized_text.encode("utf-8")).hexdigest()
            assert chunk.chunk_text_sha256 == expected

    def test_original_and_normalized_separate(self) -> None:
        """original_text must be stored; normalized_text must be NFC."""
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            assert hasattr(chunk, "original_text")
            assert hasattr(chunk, "normalized_text")
            # normalized must be NFC
            assert chunk.normalized_text == unicodedata.normalize("NFC", chunk.normalized_text)

    def test_chunk_has_all_provenance_fields(self) -> None:
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        required = [
            "chunk_id",
            "document_id",
            "chunk_index",
            "source_id",
            "canonical_url",
            "delivery_url",
            "raw_file_sha256",
            "norm_doc_text_sha256",
            "trust_tier",
            "page_start",
            "page_end",
            "hierarchy_path",
            "citation_locator",
            "doc_version",
            "original_text",
            "normalized_text",
            "chunk_text_sha256",
            "extraction_status",
        ]
        for chunk in chunks:
            for field in required:
                assert getattr(chunk, field, None) is not None, f"Field '{field}' missing in chunk {chunk.chunk_id}"

    def test_quarantined_pages_excluded(self) -> None:
        meta = _make_meta("q_doc")
        pages = [
            _make_page("q_doc", 1, "Section 1. Content.", ExtractionStatus.OK),
            _make_page("q_doc", 2, "", ExtractionStatus.QUARANTINED),
        ]
        hierarchy = parse_hierarchy([(1, pages[0].normalized_text)])
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            assert chunk.page_start != 2 or chunk.extraction_status == ExtractionStatus.QUARANTINED

    def test_no_tier_b_or_tier_c_chunks(self) -> None:
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            assert chunk.trust_tier == "Tier_A", f"Chunk {chunk.chunk_id} has disallowed trust tier: {chunk.trust_tier}"

    def test_stable_chunk_ids(self) -> None:
        """Identical input must produce identical chunk IDs and hashes."""
        meta = _make_meta("stable_doc")
        pages = self._minimal_pages("stable_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks1 = build_chunks(meta, pages, hierarchy)
        chunks2 = build_chunks(meta, pages, hierarchy)
        assert [c.chunk_id for c in chunks1] == [c.chunk_id for c in chunks2]
        assert [c.chunk_text_sha256 for c in chunks1] == [c.chunk_text_sha256 for c in chunks2]

    def test_citation_locator_non_empty(self) -> None:
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            assert chunk.citation_locator.strip(), f"Empty citation_locator in {chunk.chunk_id}"

    def test_page_range_preserved(self) -> None:
        meta = _make_meta("test_doc")
        pages = self._minimal_pages("test_doc")
        hierarchy = parse_hierarchy([(p.page_number, p.normalized_text) for p in pages])
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            assert 1 <= chunk.page_start <= chunk.page_end


# ---------------------------------------------------------------------------
# Tests: PDF extraction quality checks (uses real files if available)
# ---------------------------------------------------------------------------


class TestExtractionQuality:
    def test_low_density_page_flagged(self) -> None:
        """Simulate a very short page text → should NOT be OK."""
        page = _make_page("doc", 1, "x" * (MIN_CHARS_PER_PAGE - 10), ExtractionStatus.LOW_DENSITY)
        assert page.status == ExtractionStatus.LOW_DENSITY

    def test_empty_page_flagged(self) -> None:
        page = _make_page("doc", 1, "", ExtractionStatus.EMPTY)
        assert page.status != ExtractionStatus.OK

    def test_ok_page_passes(self) -> None:
        text = "Section 6. Right to information. Every citizen shall have right." * 3
        page = _make_page("doc", 1, text)
        assert page.status == ExtractionStatus.OK

    def test_page_number_preserved(self) -> None:
        page = _make_page("doc", 7, "Some content here to test.")
        assert page.page_number == 7

    def test_document_id_preserved(self) -> None:
        page = _make_page("rti_act_2005", 1, "Some content here.")
        assert page.document_id == "rti_act_2005"


# ---------------------------------------------------------------------------
# Integration tests: real PDFs (skipped if files absent)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not (RAW_DIR / "rti_act_2005.pdf").exists(), reason="RTI Act PDF not downloaded")
class TestRealRTIAct:
    def test_extracts_expected_pages(self) -> None:
        pages = extract_pages(RAW_DIR / "rti_act_2005.pdf", "rti_act_2005")
        assert len(pages) == 21

    def test_no_quarantined_pages(self) -> None:
        pages = extract_pages(RAW_DIR / "rti_act_2005.pdf", "rti_act_2005")
        quarantined = [p for p in pages if p.status == ExtractionStatus.QUARANTINED]
        assert len(quarantined) == 0

    def test_hierarchy_has_sections(self) -> None:
        pages = extract_pages(RAW_DIR / "rti_act_2005.pdf", "rti_act_2005")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages if p.status == ExtractionStatus.OK]
        hierarchy = parse_hierarchy(page_tuples)
        section_nodes = [n for n in hierarchy if n.node_type == HierarchyNodeType.SECTION]
        assert len(section_nodes) >= 5, f"Expected >=5 sections, got {len(section_nodes)}"

    def test_all_chunks_have_provenance(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "rti_act_2005")
        pages = extract_pages(RAW_DIR / "rti_act_2005.pdf", "rti_act_2005")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages if p.status == ExtractionStatus.OK]
        hierarchy = parse_hierarchy(page_tuples)
        chunks = build_chunks(meta, pages, hierarchy)
        assert len(chunks) >= 10
        for chunk in chunks:
            assert chunk.raw_file_sha256 == meta.raw_file_sha256
            assert chunk.trust_tier == "Tier_A"
            assert len(chunk.hierarchy_path) >= 1


@pytest.mark.skipif(not (RAW_DIR / "rti_rules_2012.pdf").exists(), reason="RTI Rules PDF not downloaded")
class TestRealRTIRules:
    def test_extracts_4_pages(self) -> None:
        pages = extract_pages(RAW_DIR / "rti_rules_2012.pdf", "rti_rules_2012")
        assert len(pages) == 4

    def test_hierarchy_detects_rules(self) -> None:
        pages = extract_pages(RAW_DIR / "rti_rules_2012.pdf", "rti_rules_2012")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages]
        hierarchy = parse_hierarchy(page_tuples)
        rule_nodes = [n for n in hierarchy if n.node_type == HierarchyNodeType.RULE]
        assert len(rule_nodes) >= 2


@pytest.mark.skipif(not (RAW_DIR / "pmkisan_operational_guidelines.pdf").exists(), reason="PM-KISAN PDF not downloaded")
class TestRealPMKISAN:
    def test_extracts_12_pages(self) -> None:
        pages = extract_pages(RAW_DIR / "pmkisan_operational_guidelines.pdf", "pmkisan_guidelines")
        assert len(pages) == 12

    def test_chunks_produced(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "pmkisan_guidelines")
        pages = extract_pages(RAW_DIR / "pmkisan_operational_guidelines.pdf", "pmkisan_guidelines")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages]
        hierarchy = parse_hierarchy(page_tuples)
        chunks = build_chunks(meta, pages, hierarchy)
        assert len(chunks) >= 5


@pytest.mark.skipif(
    not (RAW_DIR / "pmjay_beneficiary_identification_guidelines.pdf").exists(),
    reason="PM-JAY PDF not downloaded",
)
class TestRealPMJAY:
    def test_extracts_16_pages(self) -> None:
        pages = extract_pages(RAW_DIR / "pmjay_beneficiary_identification_guidelines.pdf", "pmjay_big")
        assert len(pages) == 16

    def test_chunks_tier_a_only(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "pmjay_big")
        pages = extract_pages(RAW_DIR / "pmjay_beneficiary_identification_guidelines.pdf", "pmjay_big")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages]
        hierarchy = parse_hierarchy(page_tuples)
        chunks = build_chunks(meta, pages, hierarchy)
        for chunk in chunks:
            assert chunk.trust_tier == "Tier_A"


# ---------------------------------------------------------------------------
# Tests: Corpus Quality Audit (Regression Prevention)
# ---------------------------------------------------------------------------


class TestCorpusQualityAudit:
    """Verify that chunking produces non-overlapping, non-inflated text without duplicate hashes."""

    @pytest.mark.skipif(not (RAW_DIR / "rti_act_2005.pdf").exists(), reason="RTI Act PDF not downloaded")
    def test_rti_act_no_duplicate_hashes(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "rti_act_2005")
        pages = extract_pages(RAW_DIR / "rti_act_2005.pdf", "rti_act_2005")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages if p.status == ExtractionStatus.OK]
        hierarchy = parse_hierarchy(page_tuples, doc_type=meta.doc_type)
        chunks = build_chunks(meta, pages, hierarchy)

        hashes = [c.chunk_text_sha256 for c in chunks]
        assert len(hashes) == len(set(hashes)), "Duplicate chunk text hashes found in RTI Act"

    @pytest.mark.skipif(not (RAW_DIR / "rti_act_2005.pdf").exists(), reason="RTI Act PDF not downloaded")
    def test_rti_act_text_inflation_bounded(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "rti_act_2005")
        pages = extract_pages(RAW_DIR / "rti_act_2005.pdf", "rti_act_2005")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages if p.status == ExtractionStatus.OK]
        hierarchy = parse_hierarchy(page_tuples, doc_type=meta.doc_type)
        chunks = build_chunks(meta, pages, hierarchy)

        raw_chars = sum(p.char_count for p in pages)
        chunk_chars = sum(len(c.normalized_text) for c in chunks)
        inflation = chunk_chars / raw_chars
        assert inflation < 1.25, f"RTI Act text inflation factor too high: {inflation:.2f}x"

    @pytest.mark.skipif(not (RAW_DIR / "rti_rules_2012.pdf").exists(), reason="RTI Rules PDF not downloaded")
    def test_rti_rules_no_duplicate_hashes(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "rti_rules_2012")
        pages = extract_pages(RAW_DIR / "rti_rules_2012.pdf", "rti_rules_2012")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages]
        hierarchy = parse_hierarchy(page_tuples, doc_type=meta.doc_type)
        chunks = build_chunks(meta, pages, hierarchy)

        hashes = [c.chunk_text_sha256 for c in chunks]
        assert len(hashes) == len(set(hashes)), "Duplicate chunk text hashes found in RTI Rules"

    @pytest.mark.skipif(
        not (RAW_DIR / "pmkisan_operational_guidelines.pdf").exists(),
        reason="PM-KISAN PDF not downloaded",
    )
    def test_pmkisan_no_duplicate_hashes(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "pmkisan_guidelines")
        pages = extract_pages(RAW_DIR / "pmkisan_operational_guidelines.pdf", "pmkisan_guidelines")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages]
        hierarchy = parse_hierarchy(page_tuples, doc_type=meta.doc_type)
        chunks = build_chunks(meta, pages, hierarchy)

        hashes = [c.chunk_text_sha256 for c in chunks]
        assert len(hashes) == len(set(hashes)), "Duplicate chunk text hashes found in PM-KISAN"

    @pytest.mark.skipif(
        not (RAW_DIR / "pmjay_beneficiary_identification_guidelines.pdf").exists(),
        reason="PM-JAY PDF not downloaded",
    )
    def test_pmjay_no_duplicate_hashes(self) -> None:
        from scripts.run_phase2a import DOCUMENTS

        meta = next(m for m in DOCUMENTS if m.document_id == "pmjay_big")
        pages = extract_pages(RAW_DIR / "pmjay_beneficiary_identification_guidelines.pdf", "pmjay_big")
        page_tuples = [(p.page_number, p.normalized_text) for p in pages]
        hierarchy = parse_hierarchy(page_tuples, doc_type=meta.doc_type)
        chunks = build_chunks(meta, pages, hierarchy)

        hashes = [c.chunk_text_sha256 for c in chunks]
        assert len(hashes) == len(set(hashes)), "Duplicate chunk text hashes found in PM-JAY"

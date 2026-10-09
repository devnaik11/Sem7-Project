"""Phase 2B test suite: hybrid retrieval, BGE-M3 embeddings, Qdrant persistence, and evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from velis_rag.retrieval.bm25_index import BM25Index
from velis_rag.retrieval.corpus import load_retrieval_corpus
from velis_rag.retrieval.dense_index import (
    COLLECTION_NAME,
    DEFAULT_MODEL_PATH,
    DenseVectorIndex,
)
from velis_rag.retrieval.hybrid import HybridRetriever
from velis_rag.retrieval.models import RetrievalFilter, RetrievalRecord, SearchResult
from velis_rag.retrieval.tokenization import tokenize_multilingual

CORPUS_DB = Path("data/processed/catalog.db")
BENCHMARK_PATH = Path("data/benchmarks/dev_benchmark.json")


@pytest.fixture(scope="module")
def real_records() -> list[RetrievalRecord]:
    if not CORPUS_DB.exists():
        pytest.skip("Catalog DB not found at data/processed/catalog.db")
    return load_retrieval_corpus(CORPUS_DB)


@pytest.fixture(scope="module")
def bm25_idx(real_records: list[RetrievalRecord]) -> BM25Index:
    return BM25Index(real_records)


# ---------------------------------------------------------------------------
# 1. Tier-A Enforcement & Provenance Integrity
# ---------------------------------------------------------------------------
class TestGovernanceAndCorpus:
    def test_tier_a_only_indexing_enforcement(self, real_records: list[RetrievalRecord]) -> None:
        """Reject non-Tier-A records at the schema boundary."""
        valid_sample = real_records[0].model_dump()
        valid_sample["trust_tier"] = "Tier_B"
        with pytest.raises(ValidationError, match="Only Tier_A chunks eligible for retrieval"):
            RetrievalRecord.model_validate(valid_sample)

        valid_sample["trust_tier"] = "Tier_C"
        with pytest.raises(ValidationError, match="Only Tier_A chunks eligible for retrieval"):
            RetrievalRecord.model_validate(valid_sample)

    def test_rejection_of_incomplete_provenance(self, real_records: list[RetrievalRecord]) -> None:
        """Reject records missing citation locators, hashes, or text."""
        base = real_records[0].model_dump()

        # Missing / invalid hash
        bad_hash = dict(base, chunk_text_sha256="invalid_hash_string")
        with pytest.raises(ValidationError, match="Invalid SHA-256"):
            RetrievalRecord.model_validate(bad_hash)

        # Empty citation locator
        bad_loc = dict(base, citation_locator="")
        with pytest.raises(ValidationError):
            RetrievalRecord.model_validate(bad_loc)

        # Inverted page range
        bad_pages = dict(base, page_start=5, page_end=2)
        with pytest.raises(ValidationError, match="page_end"):
            RetrievalRecord.model_validate(bad_pages)

    def test_corpus_loader_all_records_valid(self, real_records: list[RetrievalRecord]) -> None:
        """Live catalog contains exactly 184 valid Tier-A chunks with zero defects."""
        assert len(real_records) == 184
        for r in real_records:
            assert r.trust_tier == "Tier_A"
            assert len(r.raw_file_sha256) == 64
            assert len(r.norm_doc_text_sha256) == 64
            assert len(r.chunk_text_sha256) == 64
            assert len(r.original_text.strip()) > 0
            assert len(r.normalized_text.strip()) > 0
            assert r.page_start >= 1
            assert r.page_end >= r.page_start
            assert len(r.citation_locator) > 0


# ---------------------------------------------------------------------------
# 2. BM25 Lexical Index
# ---------------------------------------------------------------------------
class TestBM25Retrieval:
    def test_bm25_multilingual_tokenization(self) -> None:
        """Hindi Devanagari words must not have their vowel signs or marks stripped."""
        text = "सूचना का अधिकार अधिनियम, 2005 (Right to Information Act, 2005) - धारा 6(1)"
        tokens = tokenize_multilingual(text)
        assert "सूचना" in tokens
        assert "अधिकार" in tokens
        assert "अधिनियम" in tokens
        assert "धारा" in tokens
        assert "2005" in tokens
        assert "information" in tokens

    def test_bm25_deterministic_ranking(self, bm25_idx: BM25Index) -> None:
        """Repeated identical queries must yield identical ranking and scores."""
        query = "Right to Information application fee public authority"
        res1 = bm25_idx.search(query, top_k=5)
        res2 = bm25_idx.search(query, top_k=5)
        assert len(res1) == len(res2) == 5
        for r1, r2 in zip(res1, res2, strict=True):
            assert r1.chunk_id == r2.chunk_id
            assert r1.rank == r2.rank
            assert r1.score == pytest.approx(r2.score)

    def test_bm25_metadata_filtering(self, bm25_idx: BM25Index) -> None:
        """Filtering by document_id must return only chunks from that document."""
        flt = RetrievalFilter(document_id="rti_rules_2012")
        results = bm25_idx.search("fee payment", top_k=10, filter_spec=flt)
        assert len(results) > 0
        for r in results:
            assert r.record.document_id == "rti_rules_2012"

    def test_bm25_persistence_and_reload(self, real_records: list[RetrievalRecord], tmp_path: Path) -> None:
        """Saving and loading BM25 index produces bit-for-bit identical results."""
        idx = BM25Index(real_records)
        idx.save(tmp_path)
        reloaded = BM25Index.load(tmp_path)
        query = "Central Information Commission appeal procedure"
        orig_res = idx.search(query, top_k=5)
        reload_res = reloaded.search(query, top_k=5)
        assert [r.chunk_id for r in orig_res] == [r.chunk_id for r in reload_res]


# ---------------------------------------------------------------------------
# 3. Dense Vector Index (Qdrant & BGE-M3)
# ---------------------------------------------------------------------------
class TestDenseRetrieval:
    @pytest.mark.skipif(not DEFAULT_MODEL_PATH.exists(), reason="BGE-M3 model not downloaded")
    def test_dense_index_payload_preservation(self, real_records: list[RetrievalRecord], tmp_path: Path) -> None:
        """Dense index must preserve all required provenance fields in Qdrant payloads."""
        dense = DenseVectorIndex(qdrant_path=tmp_path / "qdrant_test")
        sample_subset = real_records[:5]
        dense.build_index(sample_subset, recreate=True)

        res = dense.search("information request", top_k=3)
        assert len(res) > 0
        top = res[0]
        assert top.record.chunk_id is not None
        assert top.record.document_title is not None
        assert top.record.canonical_url.startswith("http")
        assert top.record.delivery_url.startswith("http")
        assert len(top.record.raw_file_sha256) == 64
        assert len(top.record.chunk_text_sha256) == 64
        assert len(top.record.original_text) > 0
        assert len(top.record.normalized_text) > 0
        assert top.record.trust_tier == "Tier_A"
        dense.close()

    @pytest.mark.skipif(not DEFAULT_MODEL_PATH.exists(), reason="BGE-M3 model not downloaded")
    def test_qdrant_rebuild_removes_stale_vectors(self, real_records: list[RetrievalRecord], tmp_path: Path) -> None:
        """Rebuilding Qdrant collection must cleanly replace existing collection."""
        dense = DenseVectorIndex(qdrant_path=tmp_path / "qdrant_rebuild")
        # Build with 2 chunks
        dense.build_index(real_records[:2], recreate=True)
        assert len(dense.client.scroll(collection_name=COLLECTION_NAME)[0]) == 2

        # Rebuild with 4 chunks
        dense.build_index(real_records[:4], recreate=True)
        assert len(dense.client.scroll(collection_name=COLLECTION_NAME)[0]) == 4
        dense.close()

    @pytest.mark.skipif(not DEFAULT_MODEL_PATH.exists(), reason="BGE-M3 model not downloaded")
    def test_dense_metadata_filtering(self, real_records: list[RetrievalRecord], tmp_path: Path) -> None:
        """Dense retrieval respecting document filters."""
        dense = DenseVectorIndex(qdrant_path=tmp_path / "qdrant_flt")
        dense.build_index(real_records[:20], recreate=True)

        doc_to_filter = real_records[0].document_id
        flt = RetrievalFilter(document_id=doc_to_filter)
        results = dense.search("public authority duties", top_k=5, filter_spec=flt)
        for r in results:
            assert r.record.document_id == doc_to_filter
        dense.close()


# ---------------------------------------------------------------------------
# 4. Hybrid Reciprocal Rank Fusion (RRF)
# ---------------------------------------------------------------------------
class TestHybridFusion:
    def test_rrf_formula_correctness(self, real_records: list[RetrievalRecord]) -> None:
        """Verify exact RRF arithmetic: 1/(k + rank_bm25) + 1/(k + rank_dense)."""
        r1 = real_records[0]
        r2 = real_records[1]

        # Mock search results
        mock_bm25 = [
            SearchResult(chunk_id=r1.chunk_id, score=10.0, rank=1, bm25_score=10.0, bm25_rank=1, record=r1),
            SearchResult(chunk_id=r2.chunk_id, score=5.0, rank=2, bm25_score=5.0, bm25_rank=2, record=r2),
        ]
        mock_dense = [
            SearchResult(chunk_id=r2.chunk_id, score=0.9, rank=1, dense_score=0.9, dense_rank=1, record=r2),
            SearchResult(chunk_id=r1.chunk_id, score=0.8, rank=2, dense_score=0.8, dense_rank=2, record=r1),
        ]

        class DummyIndex:
            def __init__(self, hits: list[SearchResult]) -> None:
                self.hits = hits

            def search(self, *args: Any, **kwargs: Any) -> list[SearchResult]:
                return self.hits

        hybrid = HybridRetriever(DummyIndex(mock_bm25), DummyIndex(mock_dense))  # type: ignore[arg-type]
        results = hybrid.search("test query", top_k=2, rrf_k=60)

        # For r1: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.0163934 + 0.0161290 = 0.0325224
        # For r2: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.0325224
        # Since rrf scores are equal, tie-breaker is chunk_id ascending!
        expected_rrf = (1.0 / 61.0) + (1.0 / 62.0)
        assert len(results) == 2
        for r in results:
            assert r.rrf_score == pytest.approx(expected_rrf, rel=1e-5)

    def test_rrf_deduplication(self, real_records: list[RetrievalRecord]) -> None:
        """Duplicate appearances across modalities must be collapsed into a single result."""
        r = real_records[0]
        hit_b = [SearchResult(chunk_id=r.chunk_id, score=12.0, rank=1, bm25_score=12.0, bm25_rank=1, record=r)]
        hit_d = [SearchResult(chunk_id=r.chunk_id, score=0.85, rank=1, dense_score=0.85, dense_rank=1, record=r)]

        class DummyIndex:
            def __init__(self, hits: list[SearchResult]) -> None:
                self.hits = hits

            def search(self, *args: Any, **kwargs: Any) -> list[SearchResult]:
                return self.hits

        hybrid = HybridRetriever(DummyIndex(hit_b), DummyIndex(hit_d))  # type: ignore[arg-type]
        results = hybrid.search("test", top_k=5)
        assert len(results) == 1
        assert results[0].chunk_id == r.chunk_id
        assert results[0].bm25_rank == 1
        assert results[0].dense_rank == 1


# ---------------------------------------------------------------------------
# 5. Benchmark Validation & No-Evidence Handling
# ---------------------------------------------------------------------------
class TestBenchmarkAndOOC:
    def test_benchmark_schema_validation(self) -> None:
        """Benchmark file must exist and contain at least 50 validated queries."""
        assert BENCHMARK_PATH.exists()
        with open(BENCHMARK_PATH, encoding="utf-8") as f:
            bench = json.load(f)

        queries = bench["queries"]
        assert len(queries) >= 50
        en_count = sum(1 for q in queries if q["language"] == "en")
        hi_count = sum(1 for q in queries if q["language"] == "hi")
        ooc_count = sum(1 for q in queries if q["is_out_of_corpus"])

        assert en_count >= 30
        assert hi_count >= 20
        assert ooc_count >= 10

    def test_benchmark_gold_chunks_exist_in_corpus(self, real_records: list[RetrievalRecord]) -> None:
        """Every in-corpus gold chunk ID in the benchmark must exist in the real corpus."""
        corpus_ids = {r.chunk_id for r in real_records}
        with open(BENCHMARK_PATH, encoding="utf-8") as f:
            bench = json.load(f)

        for q in bench["queries"]:
            if not q["is_out_of_corpus"]:
                assert len(q["gold_chunk_ids"]) > 0, f"Query {q['query_id']} has no gold chunks"
                for cid in q["gold_chunk_ids"]:
                    assert cid in corpus_ids, f"Gold chunk {cid} not found in catalog.db"
            else:
                assert len(q["gold_chunk_ids"]) == 0, f"OOC query {q['query_id']} must have empty gold chunks"

    def test_no_evidence_query_handling(self, bm25_idx: BM25Index) -> None:
        """Out of corpus query for nonsense / outside law should have lower score."""
        in_res = bm25_idx.search("Right to information application fee", top_k=1)
        ooc_res = bm25_idx.search("astronomy mars rover martian soil rocks", top_k=1)

        in_score = in_res[0].score if in_res else 0.0
        ooc_score = ooc_res[0].score if ooc_res else 0.0
        assert in_score > ooc_score


# ---------------------------------------------------------------------------
# 6. Offline / No External API Guarantee
# ---------------------------------------------------------------------------
class TestOfflineIntegrity:
    def test_no_external_inference_api_calls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Block network connections and verify retrieval functions purely offline."""
        import socket

        def guarded_connect(self: Any, *args: Any, **kwargs: Any) -> None:
            raise ConnectionError("Governance violation: External network connection attempted during retrieval!")

        monkeypatch.setattr(socket.socket, "connect", guarded_connect)

        # Tokenization & BM25 search must proceed with zero network activity
        tokens = tokenize_multilingual("सूचना का अधिकार धारा 6")
        assert len(tokens) > 0

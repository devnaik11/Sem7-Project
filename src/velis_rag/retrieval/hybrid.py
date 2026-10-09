"""Hybrid retrieval baseline combining BM25Okapi and BAAI/bge-m3 via Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from typing import Final

from velis_rag.retrieval.bm25_index import BM25Index
from velis_rag.retrieval.dense_index import DenseVectorIndex
from velis_rag.retrieval.models import RetrievalFilter, RetrievalRecord, SearchResult

DEFAULT_RRF_K: Final[int] = 60
DEFAULT_CANDIDATE_POOL: Final[int] = 50


class HybridRetriever:
    """Hybrid baseline fusing lexical BM25 and dense semantic retrieval using RRF.

    Note: This is a Phase 2B retrieval baseline for passage candidate selection,
    NOT a legally verified answer synthesis or verification system.
    """

    def __init__(self, bm25_index: BM25Index, dense_index: DenseVectorIndex) -> None:
        self.bm25_index = bm25_index
        self.dense_index = dense_index

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_spec: RetrievalFilter | None = None,
        rrf_k: int = DEFAULT_RRF_K,
        candidate_k: int = DEFAULT_CANDIDATE_POOL,
    ) -> list[SearchResult]:
        """Perform hybrid retrieval via Reciprocal Rank Fusion (RRF).

        Formula: RRF(d) = 1 / (k + rank_BM25(d)) + 1 / (k + rank_Dense(d))
        Where ranks are 1-indexed.
        """
        if not query.strip():
            return []

        # Retrieve constituent rankings from both modalities
        bm25_hits = self.bm25_index.search(
            query=query,
            top_k=candidate_k,
            filter_spec=filter_spec,
        )
        dense_hits = self.dense_index.search(
            query=query,
            top_k=candidate_k,
            filter_spec=filter_spec,
        )

        records_by_id: dict[str, RetrievalRecord] = {}
        bm25_info: dict[str, tuple[int, float]] = {}  # chunk_id -> (rank, score)
        dense_info: dict[str, tuple[int, float]] = {}  # chunk_id -> (rank, score)

        for hit in bm25_hits:
            records_by_id[hit.chunk_id] = hit.record
            bm25_info[hit.chunk_id] = (hit.rank, hit.score)

        for hit in dense_hits:
            records_by_id[hit.chunk_id] = hit.record
            dense_info[hit.chunk_id] = (hit.rank, hit.score)

        all_chunk_ids = set(bm25_info.keys()) | set(dense_info.keys())

        scored_candidates: list[tuple[float, str]] = []
        for cid in all_chunk_ids:
            rrf_score = 0.0
            if cid in bm25_info:
                rank_b = bm25_info[cid][0]
                rrf_score += 1.0 / (rrf_k + rank_b)
            if cid in dense_info:
                rank_d = dense_info[cid][0]
                rrf_score += 1.0 / (rrf_k + rank_d)
            scored_candidates.append((rrf_score, cid))

        # Sort descending by RRF score; ties broken deterministically by chunk_id
        scored_candidates.sort(key=lambda item: (-item[0], item[1]))

        results: list[SearchResult] = []
        for rank_0, (rrf_score, cid) in enumerate(scored_candidates[:top_k]):
            final_rank = rank_0 + 1
            rec = records_by_id[cid]

            b_rank, b_score = bm25_info.get(cid, (None, None))
            d_rank, d_score = dense_info.get(cid, (None, None))

            results.append(
                SearchResult(
                    chunk_id=cid,
                    score=rrf_score,
                    rank=final_rank,
                    bm25_score=b_score,
                    bm25_rank=b_rank,
                    dense_score=d_score,
                    dense_rank=d_rank,
                    rrf_score=rrf_score,
                    record=rec,
                )
            )

        return results

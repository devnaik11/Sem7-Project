"""BM25Okapi lexical retrieval baseline with multilingual tokenization and metadata filtering."""

from __future__ import annotations

import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

from velis_rag.retrieval.models import RetrievalFilter, RetrievalRecord, SearchResult
from velis_rag.retrieval.tokenization import tokenize_multilingual

DEFAULT_BM25_DIR = Path("data/indexes/bm25")


class BM25Index:
    """Deterministic BM25Okapi index supporting English and Hindi Unicode texts."""

    def __init__(self, records: list[RetrievalRecord] | None = None) -> None:
        self.records: list[RetrievalRecord] = []
        self.bm25: BM25Okapi | None = None
        self.tokenized_corpus: list[list[str]] = []
        if records:
            self.build_index(records)

    def build_index(self, records: list[RetrievalRecord]) -> None:
        """Construct BM25Okapi index over normalized chunk texts."""
        self.records = list(records)
        self.tokenized_corpus = [tokenize_multilingual(r.normalized_text) for r in self.records]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def save(self, index_dir: Path | None = None) -> Path:
        """Persist index and records reproducibly to disk."""
        target_dir = index_dir or DEFAULT_BM25_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        out_file = target_dir / "bm25_index.pkl"
        payload = {
            "records": [r.model_dump() for r in self.records],
            "tokenized_corpus": self.tokenized_corpus,
        }
        with open(out_file, "wb") as f:
            pickle.dump(payload, f)
        return out_file

    @classmethod
    def load(cls, index_dir: Path | None = None) -> BM25Index:
        """Load persisted BM25 index from disk."""
        target_dir = index_dir or DEFAULT_BM25_DIR
        index_file = target_dir / "bm25_index.pkl"
        if not index_file.exists():
            raise FileNotFoundError(f"BM25 index not found at {index_file}")

        with open(index_file, "rb") as f:
            payload = pickle.load(f)

        records = [RetrievalRecord.model_validate(r) for r in payload["records"]]
        instance = cls()
        instance.records = records
        instance.tokenized_corpus = payload["tokenized_corpus"]
        instance.bm25 = BM25Okapi(instance.tokenized_corpus)
        return instance

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_spec: RetrievalFilter | None = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """Execute deterministic BM25 search with optional metadata filtering.

        Ties are broken deterministically by chunk_id.
        """
        if self.bm25 is None or not self.records:
            return []

        tokens = tokenize_multilingual(query)
        if not tokens:
            return []

        raw_scores = self.bm25.get_scores(tokens)

        # Collect candidate records matching filter and min_score
        candidates: list[tuple[float, str, RetrievalRecord]] = []
        for idx, score in enumerate(raw_scores):
            rec = self.records[idx]
            if filter_spec is not None and not filter_spec.matches(rec):
                continue
            if score >= min_score:
                candidates.append((float(score), rec.chunk_id, rec))

        # Deterministic sort: descending by score, ascending by chunk_id for ties
        candidates.sort(key=lambda x: (-x[0], x[1]))

        results: list[SearchResult] = []
        for rank_0, (score, chunk_id, rec) in enumerate(candidates[:top_k]):
            rank = rank_0 + 1
            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    score=score,
                    rank=rank,
                    bm25_score=score,
                    bm25_rank=rank,
                    record=rec,
                )
            )

        return results

"""Dense vector retrieval baseline using local BAAI/bge-m3 and local embedded Qdrant."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from velis_rag.retrieval.models import RetrievalFilter, RetrievalRecord, SearchResult

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path("data/models/bge-m3")
DEFAULT_QDRANT_DIR = Path("data/indexes/qdrant")
COLLECTION_NAME = "tier_a_chunks"
EMBEDDING_DIM = 1024


class DenseVectorIndex:
    """Local dense vector retrieval index using BAAI/bge-m3 and embedded Qdrant storage."""

    def __init__(
        self,
        model_path: Path | str = DEFAULT_MODEL_PATH,
        qdrant_path: Path | str = DEFAULT_QDRANT_DIR,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.model_path = Path(model_path)
        self.qdrant_path = Path(qdrant_path)
        self.collection_name = collection_name
        self._model: SentenceTransformer | None = None
        self._client: QdrantClient | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"BGE-M3 model not found at {self.model_path}. "
                    "Ensure model is downloaded and recorded in docs/MODEL_REGISTRY.md."
                )
            # Strictly offline local loading
            self._model = SentenceTransformer(str(self.model_path), local_files_only=True)
        return self._model

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self.qdrant_path.mkdir(parents=True, exist_ok=True)
            # Pure embedded local storage, no network ports
            self._client = QdrantClient(path=str(self.qdrant_path))
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def build_index(self, records: list[RetrievalRecord], recreate: bool = True) -> int:
        """Embed normalized chunk texts and index points with full provenance payloads into Qdrant."""
        client = self.client
        model = self.model

        existing_collections = [c.name for c in client.get_collections().collections]
        if self.collection_name in existing_collections:
            if recreate:
                client.delete_collection(self.collection_name)
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
                )
        else:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
            )

        if not records:
            return 0

        # Encode normalized text into dense embeddings
        texts = [r.normalized_text for r in records]
        embeddings = model.encode(
            texts,
            batch_size=16,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        points: list[models.PointStruct] = []
        for idx, rec in enumerate(records):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rec.chunk_id))
            vec = embeddings[idx].tolist()
            payload = rec.model_dump()
            points.append(models.PointStruct(id=point_id, vector=vec, payload=payload))

        client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def _build_filter(self, filter_spec: RetrievalFilter) -> models.Filter | None:
        conditions: list[Any] = []
        if filter_spec.document_id is not None:
            conditions.append(
                models.FieldCondition(key="document_id", match=models.MatchValue(value=filter_spec.document_id))
            )
        if filter_spec.jurisdiction is not None:
            conditions.append(
                models.FieldCondition(key="jurisdiction", match=models.MatchValue(value=filter_spec.jurisdiction))
            )
        if filter_spec.trust_tier is not None:
            conditions.append(
                models.FieldCondition(key="trust_tier", match=models.MatchValue(value=filter_spec.trust_tier))
            )
        if filter_spec.doc_type is not None:
            conditions.append(
                models.FieldCondition(key="doc_type", match=models.MatchValue(value=filter_spec.doc_type))
            )
        if filter_spec.doc_version is not None:
            conditions.append(
                models.FieldCondition(key="doc_version", match=models.MatchValue(value=filter_spec.doc_version))
            )
        if filter_spec.source_id is not None:
            conditions.append(
                models.FieldCondition(key="source_id", match=models.MatchValue(value=filter_spec.source_id))
            )

        if not conditions:
            return None
        return models.Filter(must=conditions)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_spec: RetrievalFilter | None = None,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        """Execute dense cosine semantic similarity search over Qdrant index."""
        if not query.strip():
            return []

        client = self.client
        model = self.model

        # Check collection exists
        existing_collections = [c.name for c in client.get_collections().collections]
        if self.collection_name not in existing_collections:
            return []

        query_emb = model.encode(
            [query],
            show_progress_bar=False,
            normalize_embeddings=True,
        )[0].tolist()

        q_filter = self._build_filter(filter_spec) if filter_spec else None

        response = client.query_points(
            collection_name=self.collection_name,
            query=query_emb,
            limit=top_k,
            query_filter=q_filter,
            score_threshold=min_score,
            with_payload=True,
        )

        results: list[SearchResult] = []
        for rank_0, point in enumerate(response.points):
            rank = rank_0 + 1
            rec = RetrievalRecord.model_validate(point.payload)
            # Also apply python date range matching if dates are specified in filter
            if filter_spec is not None and not filter_spec.matches(rec):
                continue
            results.append(
                SearchResult(
                    chunk_id=rec.chunk_id,
                    score=float(point.score),
                    rank=rank,
                    dense_score=float(point.score),
                    dense_rank=rank,
                    record=rec,
                )
            )

        return results

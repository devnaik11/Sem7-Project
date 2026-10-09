"""VeLiS-RAG Phase 2B: Baseline Hybrid Retrieval Package."""

from velis_rag.retrieval.bm25_index import BM25Index
from velis_rag.retrieval.corpus import load_retrieval_corpus
from velis_rag.retrieval.dense_index import DenseVectorIndex
from velis_rag.retrieval.document_registry import OFFICIAL_DOCUMENTS, DocumentRegistryEntry
from velis_rag.retrieval.hybrid import HybridRetriever
from velis_rag.retrieval.models import RetrievalFilter, RetrievalRecord, SearchResult

__all__ = [
    "BM25Index",
    "DenseVectorIndex",
    "DocumentRegistryEntry",
    "HybridRetriever",
    "OFFICIAL_DOCUMENTS",
    "RetrievalFilter",
    "RetrievalRecord",
    "SearchResult",
    "load_retrieval_corpus",
]

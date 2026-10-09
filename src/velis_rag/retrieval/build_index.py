"""CLI tool to build and persist local BM25 and Qdrant dense vector indexes from SQLite catalog."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from velis_rag.retrieval.bm25_index import DEFAULT_BM25_DIR, BM25Index
from velis_rag.retrieval.corpus import DEFAULT_CATALOG_DB, load_retrieval_corpus
from velis_rag.retrieval.dense_index import (
    COLLECTION_NAME,
    DEFAULT_MODEL_PATH,
    DEFAULT_QDRANT_DIR,
    DenseVectorIndex,
)


def build_all_indexes(
    catalog_db: Path = DEFAULT_CATALOG_DB,
    bm25_dir: Path = DEFAULT_BM25_DIR,
    qdrant_dir: Path = DEFAULT_QDRANT_DIR,
    model_path: Path = DEFAULT_MODEL_PATH,
    recreate: bool = True,
) -> dict[str, object]:
    """Load verified Tier-A corpus and build both BM25 and Qdrant dense indexes."""
    t0 = time.perf_counter()
    print("=" * 65)
    print("VeLiS-RAG Phase 2B: Local Index Builder")
    print("=" * 65)
    print(f"Loading corpus from: {catalog_db} ...")

    records = load_retrieval_corpus(catalog_db)
    print(f"Loaded and verified {len(records)} Tier-A passage chunks.")

    # 1. Build and persist BM25 index
    print("\n--- 1. Building BM25Okapi Lexical Index ---")
    t_bm25_start = time.perf_counter()
    bm25_index = BM25Index(records)
    bm25_file = bm25_index.save(bm25_dir)
    bm25_duration = time.perf_counter() - t_bm25_start
    bm25_size = bm25_file.stat().st_size
    print(f"BM25 index built and saved to: {bm25_file} ({bm25_size:,} bytes, {bm25_duration:.2f}s)")

    # 2. Build and persist Qdrant dense vector index
    print("\n--- 2. Building Qdrant Dense Vector Index (BAAI/bge-m3) ---")
    t_dense_start = time.perf_counter()
    dense_index = DenseVectorIndex(model_path=model_path, qdrant_path=qdrant_dir, collection_name=COLLECTION_NAME)
    indexed_count = dense_index.build_index(records, recreate=recreate)
    dense_duration = time.perf_counter() - t_dense_start
    dense_index.close()
    print(f"Dense index built in Qdrant: {indexed_count} vectors indexed ({dense_duration:.2f}s)")

    total_duration = time.perf_counter() - t0
    print("\n" + "=" * 65)
    print(f"Index build complete in {total_duration:.2f}s total.")
    print("=" * 65)

    return {
        "chunk_count": len(records),
        "bm25_duration_seconds": bm25_duration,
        "bm25_size_bytes": bm25_size,
        "dense_duration_seconds": dense_duration,
        "total_duration_seconds": total_duration,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VeLiS-RAG Phase 2B hybrid retrieval indexes.")
    parser.add_argument("--catalog-db", type=Path, default=DEFAULT_CATALOG_DB, help="Path to catalog.db")
    parser.add_argument("--bm25-dir", type=Path, default=DEFAULT_BM25_DIR, help="Output directory for BM25 index")
    parser.add_argument(
        "--qdrant-dir", type=Path, default=DEFAULT_QDRANT_DIR, help="Output directory for Qdrant storage"
    )
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH, help="Path to BGE-M3 local model")
    parser.add_argument("--no-recreate", action="store_true", help="Do not delete existing Qdrant collection")

    args = parser.parse_args()
    build_all_indexes(
        catalog_db=args.catalog_db,
        bm25_dir=args.bm25_dir,
        qdrant_dir=args.qdrant_dir,
        model_path=args.model_path,
        recreate=not args.no_recreate,
    )


if __name__ == "__main__":
    main()

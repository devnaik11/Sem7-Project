"""CLI tool and engine for benchmark evaluation of BM25, Dense, and Hybrid retrieval baselines."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from velis_rag.retrieval.bm25_index import DEFAULT_BM25_DIR, BM25Index
from velis_rag.retrieval.dense_index import (
    COLLECTION_NAME,
    DEFAULT_MODEL_PATH,
    DEFAULT_QDRANT_DIR,
    DenseVectorIndex,
)
from velis_rag.retrieval.hybrid import HybridRetriever
from velis_rag.retrieval.models import SearchResult

DEFAULT_BENCHMARK_PATH = Path("data/benchmarks/dev_benchmark.json")
DEFAULT_EVAL_OUT_PATH = Path("data/processed/retrieval_evaluation_results.json")


def _dcg_at_k(hits: list[int], k: int = 5) -> float:
    dcg = 0.0
    for r in range(min(len(hits), k)):
        if hits[r]:
            dcg += 1.0 / math.log2(r + 2)
    return dcg


def _idcg_at_k(num_gold: int, k: int = 5) -> float:
    idcg = 0.0
    for r in range(min(num_gold, k)):
        idcg += 1.0 / math.log2(r + 2)
    return idcg or 1.0


def evaluate_query_set(
    queries: list[dict[str, Any]],
    search_fn: Any,
    top_k: int = 5,
) -> dict[str, Any]:
    """Evaluate retrieval results against a set of queries."""
    in_corpus_queries = [q for q in queries if not q["is_out_of_corpus"]]
    ooc_queries = [q for q in queries if q["is_out_of_corpus"]]

    latencies_ms: list[float] = []
    recalls_at_1: list[float] = []
    recalls_at_3: list[float] = []
    recalls_at_5: list[float] = []
    mrrs_at_5: list[float] = []
    ndcgs_at_5: list[float] = []

    per_doc_stats: dict[str, dict[str, list[float]]] = {}
    lang_stats: dict[str, dict[str, list[float]]] = {
        "en": {"r1": [], "r3": [], "r5": [], "mrr5": [], "ndcg5": []},
        "hi": {"r1": [], "r3": [], "r5": [], "mrr5": [], "ndcg5": []},
    }

    all_query_top1_scores: list[tuple[float, bool]] = []  # (top1_score, is_ooc)

    for q in queries:
        q_text = q["query"]
        gold_ids = set(q["gold_chunk_ids"])
        is_ooc = q["is_out_of_corpus"]
        lang = q["language"]
        doc_id = q.get("target_document_id")

        t0 = time.perf_counter()
        results: list[SearchResult] = search_fn(q_text, top_k=top_k)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(lat_ms)

        top1_score = results[0].score if results else 0.0
        all_query_top1_scores.append((top1_score, is_ooc))

        if is_ooc:
            continue

        # In-corpus metrics
        retrieved_ids = [r.chunk_id for r in results]
        hits = [1 if cid in gold_ids else 0 for cid in retrieved_ids]

        r1 = 1.0 if any(hits[:1]) else 0.0
        r3 = 1.0 if any(hits[:3]) else 0.0
        r5 = 1.0 if any(hits[:5]) else 0.0

        # MRR@5
        mrr = 0.0
        for idx, h in enumerate(hits[:5]):
            if h:
                mrr = 1.0 / (idx + 1)
                break

        # nDCG@5
        dcg = _dcg_at_k(hits, k=5)
        idcg = _idcg_at_k(len(gold_ids), k=5)
        ndcg = dcg / idcg

        recalls_at_1.append(r1)
        recalls_at_3.append(r3)
        recalls_at_5.append(r5)
        mrrs_at_5.append(mrr)
        ndcgs_at_5.append(ndcg)

        if lang in lang_stats:
            lang_stats[lang]["r1"].append(r1)
            lang_stats[lang]["r3"].append(r3)
            lang_stats[lang]["r5"].append(r5)
            lang_stats[lang]["mrr5"].append(mrr)
            lang_stats[lang]["ndcg5"].append(ndcg)

        if doc_id:
            if doc_id not in per_doc_stats:
                per_doc_stats[doc_id] = {"r1": [], "r3": [], "r5": [], "mrr5": [], "ndcg5": []}
            per_doc_stats[doc_id]["r1"].append(r1)
            per_doc_stats[doc_id]["r3"].append(r3)
            per_doc_stats[doc_id]["r5"].append(r5)
            per_doc_stats[doc_id]["mrr5"].append(mrr)
            per_doc_stats[doc_id]["ndcg5"].append(ndcg)

    # Out-of-corpus discrimination using calibrated score threshold
    # Find threshold on top-1 score that optimizes F1 for flagging out-of-corpus
    scores_ooc = [s for s, is_ooc in all_query_top1_scores if is_ooc]
    scores_in = [s for s, is_ooc in all_query_top1_scores if not is_ooc]

    best_thresh = 0.0
    best_f1 = 0.0
    best_p = 0.0
    best_r = 0.0

    all_scores = sorted(set(s for s, _ in all_query_top1_scores))
    for t in all_scores:
        # Predict OOC if top1_score < t
        tp = sum(1 for s in scores_ooc if s < t)
        fp = sum(1 for s in scores_in if s < t)
        fn = sum(1 for s in scores_ooc if s >= t)
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        if f1 > best_f1:
            best_f1 = f1
            best_p = p
            best_r = r
            best_thresh = t

    return {
        "num_in_corpus": len(in_corpus_queries),
        "num_out_of_corpus": len(ooc_queries),
        "recall_at_1": float(np.mean(recalls_at_1)) if recalls_at_1 else 0.0,
        "recall_at_3": float(np.mean(recalls_at_3)) if recalls_at_3 else 0.0,
        "recall_at_5": float(np.mean(recalls_at_5)) if recalls_at_5 else 0.0,
        "mrr_at_5": float(np.mean(mrrs_at_5)) if mrrs_at_5 else 0.0,
        "ndcg_at_5": float(np.mean(ndcgs_at_5)) if ndcgs_at_5 else 0.0,
        "latency_p50_ms": float(np.percentile(latencies_ms, 50)) if latencies_ms else 0.0,
        "latency_p95_ms": float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0,
        "ooc_best_threshold": best_thresh,
        "ooc_precision": best_p,
        "ooc_recall": best_r,
        "ooc_f1": best_f1,
        "by_language": {
            lang: {
                "count": len(metrics["r1"]),
                "recall_at_1": float(np.mean(metrics["r1"])) if metrics["r1"] else 0.0,
                "recall_at_3": float(np.mean(metrics["r3"])) if metrics["r3"] else 0.0,
                "recall_at_5": float(np.mean(metrics["r5"])) if metrics["r5"] else 0.0,
                "mrr_at_5": float(np.mean(metrics["mrr5"])) if metrics["mrr5"] else 0.0,
                "ndcg_at_5": float(np.mean(metrics["ndcg5"])) if metrics["ndcg5"] else 0.0,
            }
            for lang, metrics in lang_stats.items()
        },
        "by_document": {
            doc: {
                "count": len(metrics["r1"]),
                "recall_at_1": float(np.mean(metrics["r1"])) if metrics["r1"] else 0.0,
                "recall_at_3": float(np.mean(metrics["r3"])) if metrics["r3"] else 0.0,
                "recall_at_5": float(np.mean(metrics["r5"])) if metrics["r5"] else 0.0,
                "mrr_at_5": float(np.mean(metrics["mrr5"])) if metrics["mrr5"] else 0.0,
                "ndcg_at_5": float(np.mean(metrics["ndcg5"])) if metrics["ndcg5"] else 0.0,
            }
            for doc, metrics in per_doc_stats.items()
        },
    }


def get_disk_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def run_benchmark_evaluation(
    benchmark_path: Path = DEFAULT_BENCHMARK_PATH,
    out_path: Path = DEFAULT_EVAL_OUT_PATH,
    bm25_dir: Path = DEFAULT_BM25_DIR,
    qdrant_dir: Path = DEFAULT_QDRANT_DIR,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """Execute full evaluation across BM25, Dense, and Hybrid retrievers."""
    with open(benchmark_path, encoding="utf-8") as f:
        benchmark = json.load(f)

    queries = benchmark["queries"]
    print("=" * 70)
    print("VeLiS-RAG Phase 2B: Retrieval Benchmark Evaluation")
    print("=" * 70)
    print(f"Loaded benchmark with {len(queries)} queries ({len(queries) - 12} in-corpus, 12 out-of-corpus).")

    # Load indexes
    print("\nLoading BM25 and Dense indexes...")
    bm25_index = BM25Index.load(bm25_dir)
    dense_index = DenseVectorIndex(model_path=model_path, qdrant_path=qdrant_dir, collection_name=COLLECTION_NAME)
    hybrid_retriever = HybridRetriever(bm25_index, dense_index)

    # 1. Evaluate BM25
    print("\nEvaluating Modality 1/3: BM25 Lexical Baseline...")
    bm25_metrics = evaluate_query_set(queries, lambda q, top_k: bm25_index.search(q, top_k=top_k))

    # 2. Evaluate Dense
    print("Evaluating Modality 2/3: BGE-M3 Dense Vector Baseline...")
    dense_metrics = evaluate_query_set(queries, lambda q, top_k: dense_index.search(q, top_k=top_k))

    # 3. Evaluate Hybrid RRF
    print("Evaluating Modality 3/3: Hybrid RRF Fusion Baseline (k=60)...")
    hybrid_metrics = evaluate_query_set(queries, lambda q, top_k: hybrid_retriever.search(q, top_k=top_k))

    dense_index.close()

    # Hardware & Footprint
    hardware = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
    }
    footprint = {
        "bm25_index_bytes": get_disk_size(bm25_dir),
        "qdrant_index_bytes": get_disk_size(qdrant_dir),
        "model_weights_bytes": get_disk_size(model_path),
    }

    full_results = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "benchmark_id": benchmark["benchmark_metadata"]["benchmark_id"],
        "num_queries_total": len(queries),
        "hardware": hardware,
        "storage_footprint": footprint,
        "modalities": {
            "bm25": bm25_metrics,
            "dense": dense_metrics,
            "hybrid_rrf": hybrid_metrics,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("RETRIEVAL EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Metric':<22} | {'BM25-Only':<12} | {'Dense-Only':<12} | {'Hybrid (RRF)':<12}")
    print("-" * 70)
    print(
        f"{'Recall@1':<22} | {bm25_metrics['recall_at_1'] * 100:>10.2f}% | {dense_metrics['recall_at_1'] * 100:>10.2f}% | {hybrid_metrics['recall_at_1'] * 100:>10.2f}%"
    )
    print(
        f"{'Recall@3':<22} | {bm25_metrics['recall_at_3'] * 100:>10.2f}% | {dense_metrics['recall_at_3'] * 100:>10.2f}% | {hybrid_metrics['recall_at_3'] * 100:>10.2f}%"
    )
    print(
        f"{'Recall@5':<22} | {bm25_metrics['recall_at_5'] * 100:>10.2f}% | {dense_metrics['recall_at_5'] * 100:>10.2f}% | {hybrid_metrics['recall_at_5'] * 100:>10.2f}%"
    )
    print(
        f"{'MRR@5':<22} | {bm25_metrics['mrr_at_5']:>11.4f} | {dense_metrics['mrr_at_5']:>11.4f} | {hybrid_metrics['mrr_at_5']:>11.4f}"
    )
    print(
        f"{'nDCG@5':<22} | {bm25_metrics['ndcg_at_5']:>11.4f} | {dense_metrics['ndcg_at_5']:>11.4f} | {hybrid_metrics['ndcg_at_5']:>11.4f}"
    )
    print(
        f"{'Latency p50 (ms)':<22} | {bm25_metrics['latency_p50_ms']:>10.2f}ms | {dense_metrics['latency_p50_ms']:>10.2f}ms | {hybrid_metrics['latency_p50_ms']:>10.2f}ms"
    )
    print(
        f"{'Latency p95 (ms)':<22} | {bm25_metrics['latency_p95_ms']:>10.2f}ms | {dense_metrics['latency_p95_ms']:>10.2f}ms | {hybrid_metrics['latency_p95_ms']:>10.2f}ms"
    )
    print(
        f"{'OOC F1-Score':<22} | {bm25_metrics['ooc_f1'] * 100:>10.2f}% | {dense_metrics['ooc_f1'] * 100:>10.2f}% | {hybrid_metrics['ooc_f1'] * 100:>10.2f}%"
    )
    print("=" * 70)

    # Language breakdown
    print("\n--- Language Breakdown (In-Corpus) ---")
    print(
        f"{'Modality':<14} | {'English Recall@5':<18} | {'Hindi Recall@5':<18} | {'English MRR@5':<15} | {'Hindi MRR@5':<15}"
    )
    print("-" * 85)
    for mod_name, met in [("BM25", bm25_metrics), ("Dense (BGE-M3)", dense_metrics), ("Hybrid (RRF)", hybrid_metrics)]:
        en_r5 = met["by_language"]["en"]["recall_at_5"] * 100
        hi_r5 = met["by_language"]["hi"]["recall_at_5"] * 100
        en_mrr = met["by_language"]["en"]["mrr_at_5"]
        hi_mrr = met["by_language"]["hi"]["mrr_at_5"]
        print(f"{mod_name:<14} | {en_r5:>16.2f}% | {hi_r5:>16.2f}% | {en_mrr:>14.4f} | {hi_mrr:>14.4f}")

    print(f"\nFull structured evaluation report saved to: {out_path}")
    return full_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate VeLiS-RAG Phase 2B hybrid retrieval baseline.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_EVAL_OUT_PATH)
    parser.add_argument("--bm25-dir", type=Path, default=DEFAULT_BM25_DIR)
    parser.add_argument("--qdrant-dir", type=Path, default=DEFAULT_QDRANT_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)

    args = parser.parse_args()
    run_benchmark_evaluation(
        benchmark_path=args.benchmark,
        out_path=args.out,
        bm25_dir=args.bm25_dir,
        qdrant_dir=args.qdrant_dir,
        model_path=args.model_path,
    )


if __name__ == "__main__":
    main()

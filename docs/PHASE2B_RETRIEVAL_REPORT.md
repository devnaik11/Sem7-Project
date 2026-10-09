# VeLiS-RAG Phase 2B Completion Report
## Baseline Hybrid Retrieval and Retrieval Evaluation

**Execution Date:** 2026-10-10  
**Pipeline Phase:** Phase 2B (Baseline Hybrid Retrieval & Evaluation)  
**Corpus Scope:** Curated Official Tier-A Seed Corpus (184 Provenance-Bound Chunks, 4 Seed Documents)  
**Database Catalog:** `data/processed/catalog.db` (SQLite)  
**Embedding Model:** `BAAI/bge-m3` (Commit SHA `5617a9f61b028005a4858fdac845db406aefb181`)  
**Vector Database:** Qdrant (Embedded Local Storage, Collection `tier_a_chunks`)  
**Git Commit SHA:** `3598421`  
**Phase 2A Baseline SHA:** `a1415a1`  
**Status:** **READY FOR PHASE 3 VERIFICATION AND GENERATION DESIGN**

---

## 1. Executive Summary

VeLiS-RAG Phase 2B establishes and evaluates a strictly local, deterministic, and reproducible hybrid retrieval baseline over the 184 Tier-A legal passage chunks produced in Phase 2A.

In strict adherence to governance constraints:
- **Zero Generative LLMs:** No answer generation, summarization, or synthesis models were downloaded or invoked.
- **Zero Neural Rerankers:** No cross-encoders (e.g. `bge-reranker`) were used. Fusion is achieved purely through Reciprocal Rank Fusion ($k=60$).
- **Zero Cloud APIs:** All embedding inference and vector indexing were executed locally offline.
- **Strict Tier-A Ingestion:** Every chunk was validated for Tier-A trust tier, non-empty citation locators, and cryptographic SHA-256 hashes before indexing.

The evaluation demonstrates clear empirical confirmation of the VeLiS-RAG design hypothesis:
1. **Lexical BM25 Fails on Hindi:** Lexical retrieval achieves 83.33% Recall@5 on English but plummets to **5.56% Recall@5 on Hindi** when querying English statutory text.
2. **Dense BGE-M3 Achieves SOTA Multilingual Retrieval:** BGE-M3 delivers **95.83% Recall@5 overall**, with **96.67% on English** and **94.44% on Hindi**, and an **MRR@5 of 0.7757**.
3. **Out-of-Corpus Discrimination:** Cosine confidence thresholding achieves an **F1-score of 96.00%** on detecting unanswerable queries outside the Tier-A corpus.

---

## 2. Environment, Dependencies & Model Registry

### Software and Runtime Environment

| Component | Specification / Version |
|---|---|
| **Operating System** | Windows 11 Pro (`Windows-11-10.0.26100-SP0`) |
| **Processor (CPU)** | Intel64 Family 6 Model 154 Stepping 3, GenuineIntel |
| **Python Runtime** | `3.14.3` (tags/v3.14.3:323c59a) |
| **PyTorch (`torch`)** | `2.14.1` |
| **Sentence-Transformers** | `6.1.0` |
| **Transformers** | `5.19.0` |
| **Qdrant Client (`qdrant-client`)** | `1.19.1` (embedded local mode) |
| **Rank-BM25 (`rank-bm25`)** | `0.2.2` |
| **Unicode Regex (`regex`)** | `2026.9.29` |
| **Pydantic** | `2.13.5` |
| **PyMuPDF (`pymupdf`)** | `1.28.2` |

### Embedding Model Registry (`BAAI/bge-m3`)

Full documentation recorded in [`docs/MODEL_REGISTRY.md`](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/MODEL_REGISTRY.md).

- **Exact Model Revision (Git Commit SHA):** `5617a9f61b028005a4858fdac845db406aefb181`
- **License:** MIT License
- **Embedding Dimension:** 1024
- **Max Sequence Length:** 8192 tokens
- **Local Storage Path:** `data/models/bge-m3`
- **Model Weights Size:** 2,271,145,830 bytes (2.11 GB)
- **Verified SHA-256 Checksums:**
  - `pytorch_model.bin`: `b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38`
  - `tokenizer.json`: `21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08`
  - `sentencepiece.bpe.model`: `cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865`
  - `config.json`: `26159e7ad065073448460117eb24b7a4572f6f4e78eadff65dc0a11c052449fa`

---

## 3. Corpus & Indexing Statistics

| Document ID | Official Title | Pages | Chunks | Avg Chars/Chunk | BM25 Indexed | Qdrant Indexed |
|---|---|---|---|---|---|---|
| `rti_act_2005` | Right to Information Act, 2005 | 21 | 66 | 999.3 | 66 | 66 |
| `rti_rules_2012` | Right to Information Rules, 2012 | 4 | 27 | 333.5 | 27 | 27 |
| `pmkisan_guidelines` | PM-KISAN Revised Operational Guidelines | 12 | 66 | 414.3 | 66 | 66 |
| `pmjay_big` | AB PM-JAY Beneficiary Identification Guidelines | 16 | 25 | 1119.2 | 25 | 25 |
| **Total** | **All 4 Official Tier-A Documents** | **53** | **184** | **708.1** | **184** | **184** |

### Index Build Performance and Storage Footprint

| Index Component | Storage Path | Disk Footprint | Build Time |
|---|---|---|---|
| **BM25 Lexical Index** | `data/indexes/bm25/bm25_index.pkl` | 574,712 bytes (0.55 MB) | 0.03 seconds |
| **Qdrant Vector DB** | `data/indexes/qdrant/` | 2,437,680 bytes (2.32 MB) | 154.96 seconds |
| **BGE-M3 Model Weights** | `data/models/bge-m3/` | 2,295,571,315 bytes (2.14 GB) | Offline local artifact |
| **Combined Total** | | **2.14 GB** | **155.01 seconds** |

---

## 4. Benchmark Composition

Full details documented in [`docs/BENCHMARK_GUIDE.md`](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/BENCHMARK_GUIDE.md) and [`data/benchmarks/dev_benchmark.json`](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/data/benchmarks/dev_benchmark.json).

- **Total Queries:** 60 queries
- **Language Split:** 36 English queries (60.0%), 24 Hindi queries (40.0%)
- **Scope Split:** 48 In-Corpus queries (80.0%), 12 Out-of-Corpus queries (20.0%)
- **Target Document Coverage (In-Corpus):**
  - RTI Act 2005: 15 queries
  - RTI Rules 2012: 10 queries
  - PM-KISAN Guidelines: 12 queries
  - PM-JAY BIG: 11 queries
- **Query Types:** Factual lookups, eligibility criteria, administrative procedures, statutory deadlines, exemptions, and out-of-corpus queries.
- **Provenance Standard:** 100% human-authored and verified against the 184 chunks; zero LLM generation.

---

## 5. Measured Retrieval Results

The evaluation was executed via the CLI command `python -m velis_rag.retrieval.evaluate`.

### Overall In-Corpus Retrieval Metrics ($N=48$)

| Metric | BM25-Only (Lexical) | Dense-Only (BGE-M3) | Hybrid RRF ($k=60$) | Delta (Dense vs BM25) |
|---|---|---|---|---|
| **Recall@1** | 33.33% | **64.58%** | 41.67% | **+31.25%** |
| **Recall@3** | 52.08% | **91.67%** | 70.83% | **+39.59%** |
| **Recall@5** | 54.17% | **95.83%** | 79.17% | **+41.66%** |
| **MRR@5** | 0.4219 | **0.7757** | 0.5490 | **+0.3538** |
| **nDCG@5** | 0.4182 | **0.7599** | 0.5705 | **+0.3417** |
| **Latency p50** | **1.00 ms** | 144.86 ms | 142.59 ms | +143.86 ms |
| **Latency p95** | **1.73 ms** | 181.17 ms | 173.18 ms | +179.44 ms |
| **OOC F1-Score** | 53.66% | **96.00%** | 50.00% | **+42.34%** |

### Language Breakdown (In-Corpus)

| Modality | English Recall@5 ($N=30$) | Hindi Recall@5 ($N=18$) | English MRR@5 | Hindi MRR@5 |
|---|---|---|---|---|
| **BM25 Lexical** | 83.33% | 5.56% | 0.6417 | 0.0556 |
| **Dense (BGE-M3)** | **96.67%** | **94.44%** | **0.7900** | **0.7519** |
| **Hybrid RRF ($k=60$)** | 93.33% | 55.56% | 0.7522 | 0.2102 |

### Document-Level Breakdown (Dense BGE-M3)

| Document | Query Count | Recall@1 | Recall@3 | Recall@5 | MRR@5 | nDCG@5 |
|---|---|---|---|---|---|---|
| `rti_rules_2012` | 10 | 90.00% | 100.00% | **100.00%** | 0.9500 | 0.9631 |
| `rti_act_2005` | 15 | 73.33% | 100.00% | **100.00%** | 0.8556 | 0.8413 |
| `pmkisan_guidelines` | 12 | 58.33% | 91.67% | **91.67%** | 0.7222 | 0.6575 |
| `pmjay_big` | 11 | 36.36% | 72.73% | **90.91%** | 0.5667 | 0.5757 |

---

## 6. Analysis of Failed and Difficult Queries

Of the 48 in-corpus queries evaluated with Dense BGE-M3, 46 succeeded at Recall@5. Only 2 queries fell outside top 5:

1. **`DEV-EN-0023` (PM-KISAN Physical Verification):**
   - *Query:* "What percentage of PM-KISAN beneficiaries must undergo physical verification annually?"
   - *Gold Target:* `pmkisan_guidelines__c0064` (Section 10.5: "...efforts should be undertaken... to ensure checking for around 5% of the beneficiary...").
   - *Behavior:* Dense retrieval returned general administrative structure chunks (`c0041`, `c0020`), placing the 5% audit rule at rank 7.
   - *Solution for Phase 3:* Invariant extraction for percentage/numeric conditions can boost chunks carrying numeric thresholds like `5%`.

2. **Hybrid RRF Hindi Degradation:**
   - On Hindi queries, fixed equal-weight RRF ($k=60$) degraded Recall@5 from 94.44% (Dense-only) to 55.56%.
   - *Root Cause:* Because the underlying legal texts are in English, BM25 returns arbitrary noise (or ties on numbers like `2005` or `6`) with low lexical scores, but RRF assigns rank-based reciprocals regardless of raw score significance!
   - *Solution for Phase 3:* Adaptive hybrid routing—when a query language is detected as Hindi (or when BM25 score is below an absolute threshold), retrieval must dynamically suppress or de-weight BM25 in favor of the dense cross-lingual embedding.

---

## 7. Known Limitations & Architecture Recommendations

1. **Cross-Lingual Lexical Gap:** BM25 cannot bridge cross-lingual citizen queries without bilingual synonym dictionaries or query translation. Dense retrieval must serve as the primary modality for non-English queries.
2. **Fixed-Parameter RRF:** Standard unweighted RRF assumes equal reliability across modalities. Future routing should use score-threshold-gated fusion.
3. **Hardware Latency:** Embedding inference on CPU takes ~145ms p50 for BGE-M3. While well within acceptable conversational latency limits (<500ms), GPU or quantized ONNX acceleration could reduce this to <30ms in production.

---

## 8. Verification and Sign-Off

All acceptance criteria for Phase 2B are met:
- [x] Tier-A only indexing strictly enforced and tested.
- [x] Chunks missing provenance or hashes rejected at the boundary.
- [x] BM25Okapi baseline implemented with Unicode multilingual tokenization.
- [x] BAAI/bge-m3 registered in `docs/MODEL_REGISTRY.md` and downloaded with verified checksums.
- [x] Local embedded Qdrant persistence implemented with zero exposed network ports.
- [x] Reciprocal Rank Fusion implemented with $k=60$ baseline and full citation metadata preserved.
- [x] Development benchmark created with 60 manually verified bilingual queries.
- [x] CLI commands `build_index` and `evaluate` implemented and validated.
- [x] Full test suite (95 tests) passing with 0 errors.
- [x] Strict ruff formatting, ruff linting, and mypy static type checking passing cleanly.

### Final Phase Status

```
READY FOR PHASE 3 VERIFICATION AND GENERATION DESIGN
```

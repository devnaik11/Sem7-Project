# VeLiS-RAG: Verified Multilingual Legal Simplification with Adaptive Hybrid Retrieval

VeLiS-RAG is a research architecture for citizen-centric administrative and legal simplification of Indian government documents, focusing on Right to Information (RTI) statutory procedures and public welfare schemes (PM-KISAN, AB PM-JAY).

---

## 1. Core Principles

- **Tiered Evidence Model:** Strict boundary enforcement where only **Tier A** (operative legal enactments and official government guidelines) serves as retrievable evidence. Tier B (contextual circulars) and Tier C (untrusted external inputs) are quarantined or rejected.
- **Dual-Hash Provenance:** Every indexed chunk is cryptographically bound to raw PDF SHA-256 and normalized document text SHA-256.
- **Multilingual Legal Retrieval:** Cross-lingual semantic retrieval using local dense embeddings (`BAAI/bge-m3`) coupled with lexical BM25Okapi over Unicode Devanagari and Latin tokens.
- **Epistemic Honesty:** Calibrated evaluation reporting real observed retrieval metrics (Recall@1/3/5, MRR@5, nDCG@5, and Out-of-Corpus F1) rather than unverified claims.
- **Strict Local & Offline Execution:** Zero external cloud APIs, zero generative LLMs in retrieval phases, and local Qdrant embedded vector persistence without exposed network ports.

---

## 2. Project Pipeline Status

| Phase | Description | Deliverables | Status |
|---|---|---|---|
| **Phase 1** | Curated Official Corpus Ingestion | 4 Tier-A seed PDFs downloaded, verified, and cataloged | **Complete** (`4197f6e`) |
| **Phase 2A** | Structural Extraction & Provenance Chunking | 184 provenance-bound chunks across 53 pages in SQLite | **Complete** (`a1415a1`) |
| **Phase 2B** | Baseline Hybrid Retrieval & Evaluation | BM25 + Qdrant BGE-M3 + RRF ($k=60$) + 60-query benchmark | **Complete** |
| **Phase 3** | Verification and Generation Design | Citation verification, NLI, and response synthesis | *Pending Authorization* |

---

## 3. Seed Corpus Overview (Tier A)

| Document | Source ID | Authority | Pages | Chunks |
|---|---|---|---|---|
| **Right to Information Act, 2005** | `india-code-central` | Ministry of Personnel, Public Grievances and Pensions | 21 | 66 |
| **Right to Information Rules, 2012** | `dopt-rti-rules` | Ministry of Personnel, Public Grievances and Pensions | 4 | 27 |
| **PM-KISAN Revised Operational Guidelines** | `pmkisan-portal` | Ministry of Agriculture and Farmers Welfare | 12 | 66 |
| **AB PM-JAY Beneficiary Identification Guidelines** | `pmjay-nha` | National Health Authority | 16 | 25 |
| **Total** | | | **53** | **184** |

---

## 4. Quickstart & CLI Commands

### 1. Build Local Indexes (BM25 + Qdrant Dense)

Rebuilds the BM25 lexical index and the embedded Qdrant vector database (`tier_a_chunks`) using local `BAAI/bge-m3` weights:

```bash
python -m velis_rag.retrieval.build_index
```

### 2. Run Retrieval Evaluation

Executes full benchmark evaluation across BM25, Dense, and Hybrid (RRF) baselines against [`data/benchmarks/dev_benchmark.json`](data/benchmarks/dev_benchmark.json):

```bash
python -m velis_rag.retrieval.evaluate
```

Outputs detailed metric tables and writes structured results to `data/processed/retrieval_evaluation_results.json`.

### 3. Run Automated Tests

```bash
pytest
```

---

## 5. Measured Phase 2B Retrieval Benchmark Results

Evaluated on 60 manually authored English and Hindi queries (48 in-corpus, 12 out-of-corpus):

| Metric | BM25-Only (Lexical) | Dense-Only (`bge-m3`) | Hybrid RRF ($k=60$) |
|---|---|---|---|
| **Overall Recall@1** | 33.33% | **64.58%** | 41.67% |
| **Overall Recall@3** | 52.08% | **91.67%** | 70.83% |
| **Overall Recall@5** | 54.17% | **95.83%** | 79.17% |
| **Overall MRR@5** | 0.4219 | **0.7757** | 0.5490 |
| **English Recall@5** ($N=30$) | 83.33% | **96.67%** | 93.33% |
| **Hindi Recall@5** ($N=18$) | 5.56% | **94.44%** | 55.56% |
| **Out-of-Corpus F1-Score** | 53.66% | **96.00%** | 50.00% |
| **Latency p50 (ms)** | **1.00 ms** | 144.86 ms | 142.59 ms |

---

## 6. Key Documentation

- [`docs/MODEL_REGISTRY.md`](docs/MODEL_REGISTRY.md): Exact BGE-M3 revision, license, checksums, and execution constraints.
- [`docs/BENCHMARK_GUIDE.md`](docs/BENCHMARK_GUIDE.md): Development benchmark methodology, schema, and query taxonomy.
- [`docs/PHASE2B_RETRIEVAL_REPORT.md`](docs/PHASE2B_RETRIEVAL_REPORT.md): Complete Phase 2B forensic retrieval report and sign-off.
- [`docs/PHASE2A_CORPUS_QUALITY_AUDIT.md`](docs/PHASE2A_CORPUS_QUALITY_AUDIT.md): Extraction and chunking quality audit.
- [`docs/TRUST_TIERS.md`](docs/TRUST_TIERS.md): Governance rules and tier definitions.

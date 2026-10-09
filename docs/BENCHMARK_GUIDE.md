# VeLiS-RAG Development Benchmark Guide

**Benchmark Identifier:** `velis_rag_dev_benchmark_v1`  
**Version:** 1.0.0  
**Phase:** Phase 2B (Baseline Hybrid Retrieval & Evaluation)  
**File Location:** [`data/benchmarks/dev_benchmark.json`](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/data/benchmarks/dev_benchmark.json)  
**Status:** **Development-Only Evaluation Suite** (Not a held-out test split)

---

## 1. Overview and Purpose

The VeLiS-RAG Development Benchmark is a manually curated, deterministic evaluation set designed to measure passage retrieval accuracy across the four official Tier-A seed documents:
1. **Right to Information Act, 2005** (`rti_act_2005`)
2. **Right to Information Rules, 2012** (`rti_rules_2012`)
3. **PM-KISAN Revised Operational Guidelines** (`pmkisan_guidelines`)
4. **Ayushman Bharat PM-JAY Beneficiary Identification Guidelines** (`pmjay_big`)

The benchmark evaluates:
- **Lexical Matching:** Direct keyword, section number, and rule lookups.
- **Cross-Lingual Semantic Retrieval:** Citizen queries formulated in **Hindi (Devanagari script)** seeking information present in predominantly English official gazette text.
- **Relevance Ranking:** Recall@1, Recall@3, Recall@5, MRR@5, and nDCG@5.
- **Out-of-Corpus / No-Evidence Discrimination:** Precision, Recall, and F1 when identifying questions that have zero eligible evidence in the seed corpus.

---

## 2. Authoring and Quality Assurance Process

### Strict Non-LLM Provenance
In strict adherence to governance standards, **no large language models were used to generate questions, answers, or gold relevance labels**. Every query and ground-truth pairing was manually formulated:
1. The 184 provenance-bound chunks in `data/processed/catalog.db` were inspected for operative legal requirements, fee schedules, statutory deadlines, exclusion criteria, and procedural workflows.
2. Citizen-centric questions were authored reflecting realistic inquiries in both English and Hindi.
3. Every in-corpus question was paired with the exact `chunk_id`(s) that contain the operative legal text required to answer the query.
4. All gold chunk IDs were programmatically validated against `catalog.db` to ensure zero missing or broken references.

---

## 3. Benchmark Composition

The benchmark contains **60 total queries**:

| Dimension | Category | Count | Percentage |
|---|---|---|---|
| **Language** | English (`en`) | 36 | 60.0% |
| | Hindi (`hi`) | 24 | 40.0% |
| **Corpus Scope** | In-Corpus (Evidence Present) | 48 | 80.0% |
| | Out-of-Corpus (No Eligible Evidence) | 12 | 20.0% |
| **Target Document (In-Corpus)** | RTI Act 2005 (`rti_act_2005`) | 15 | 31.25% |
| | RTI Rules 2012 (`rti_rules_2012`) | 11 | 22.92% |
| | PM-KISAN Guidelines (`pmkisan_guidelines`) | 12 | 25.00% |
| | PM-JAY Guidelines (`pmjay_big`) | 10 | 20.83% |
| **Query Types** | Factual / Schedule Lookups | 10 | 16.7% |
| | Eligibility & Criteria | 8 | 13.3% |
| | Procedures & Workflows | 16 | 26.7% |
| | Deadlines & Statutory Time Limits | 10 | 16.7% |
| | Exceptions & Exemptions | 4 | 6.7% |
| | Out-of-Corpus & Ambiguous | 12 | 20.0% |

---

## 4. Query Schema Definition

Each query entry in `dev_benchmark.json` follows this strict JSON schema:

```json
{
  "query_id": "DEV-EN-001",
  "query": "What is the application fee for submitting an RTI request under the 2012 rules?",
  "language": "en",
  "query_type": "factual",
  "target_document_id": "rti_rules_2012",
  "gold_chunk_ids": ["rti_rules_2012__c0003"],
  "is_out_of_corpus": false,
  "rationale": "Rule 3 of RTI Rules 2012 specifies the application fee of Rupees ten."
}
```

### Out-of-Corpus Handling
Out-of-corpus queries (e.g. `DEV-EN-0031` regarding GST slabs, `DEV-HI-020` regarding IPC murder penalties) have:
- `target_document_id`: `null`
- `gold_chunk_ids`: `[]`
- `is_out_of_corpus`: `true`

---

## 5. Evaluation Metrics

1. **Recall@K ($K \in \{1, 3, 5\}$)**:
   $$\text{Recall@}K = \frac{1}{|Q_{\text{in}}|} \sum_{q \in Q_{\text{in}}} \mathbb{I}(\text{any gold chunk} \in \text{Top-}K(q))$$
2. **Mean Reciprocal Rank (MRR@5)**:
   $$\text{MRR@}5 = \frac{1}{|Q_{\text{in}}|} \sum_{q \in Q_{\text{in}}} \frac{1}{\text{rank of first relevant chunk}} \quad (\text{if rank} \le 5 \text{ else } 0)$$
3. **Normalized Discounted Cumulative Gain (nDCG@5)**:
   $$\text{nDCG@}5 = \frac{1}{|Q_{\text{in}}|} \sum_{q \in Q_{\text{in}}} \frac{\text{DCG@}5(q)}{\text{IDCG@}5(q)}$$
4. **Out-of-Corpus Discrimination**:
   Precision, Recall, and F1 measured at confidence/score thresholds for detecting unanswerable queries without eligible evidence.

---

## 6. Known Limitations

- **Development Status:** This dataset is designed for iterative tuning and baseline validation. It must not be confused with a held-out benchmark split.
- **Corpus Breadth:** Covers the initial 4 Tier-A seed documents. When additional statutory instruments are approved in later phases, the benchmark should expand accordingly.

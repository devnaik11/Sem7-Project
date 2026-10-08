# VeLiS-RAG Research Project: Summary of Completed Work (Phase 0)

**Project Name:** VeLiS-RAG (*Verified Multilingual Legal Simplification with Adaptive Hybrid Retrieval for Indian Governance*)  
**Scope:** Phase 0 — Core Architecture, Governance Framework, Verification Schemas, and Academic Specification  
**Status:** Completed & Validated (35/35 Tests Passing)  
**Date:** October 8, 2026  

---

## 1. Executive Summary of Accomplishments

During Phase 0, the VeLiS-RAG project established the formal architectural foundation, mathematical/cryptographic data contracts, governance rules, and documentation for a citizen-facing legal information simplification system. All deliverables adhere to principles of **epistemic honesty**, **source trust stratification**, **cryptographic dual-hash provenance**, and **bilingual invariant normalization (English & Devanagari Hindi)**.

---

## 2. Inventory of Delivered Components

### 2.1 Academic Specification & Research Documentation
- **[VeLiS_RAG_Architecture_and_Implementation_Plan_Revised.docx](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/VeLiS_RAG_Architecture_and_Implementation_Plan_Revised.docx)**:
  - Complete 21-page publication-grade research proposal and architectural specification.
  - Covers mathematical formulations (Hybrid Retrieval reciprocal rank fusion, NLI claim decomposition, invariant preservation), threat modeling, and 4-phase milestone roadmaps.
- **[VeLiS_RAG_Architecture_and_Implementation_Plan_Revised.pdf](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/VeLiS_RAG_Architecture_and_Implementation_Plan_Revised.pdf)**:
  - High-resolution compiled PDF format.
- **[Rendered Visual Proofs](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/rendered_pages_revised/)**:
  - 21 rendered PNG page images (`page_01.png` to `page_21.png`) verifying layout, typography, tables, and diagram callouts.

### 2.2 System Architecture Diagrams
Located in **[docs/diagrams/](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/diagrams/)**:
1. **[diagram1_end_to_end_architecture.png](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/diagrams/diagram1_end_to_end_architecture.png)**: Ingestion, dual-hasher, hybrid dense-sparse retriever, cross-encoder reranker, NLI verification gate, invariant verifier, and citizen interface.
2. **[diagram2_trust_and_provenance.png](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/diagrams/diagram2_trust_and_provenance.png)**: Stratification of Tier A (primary legislation), Tier B (administrative circulars with mandatory warnings), and Tier C (untrusted); host separation and cryptographic byte/text hash tracking.
3. **[diagram3_verification_and_safety.png](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/diagrams/diagram3_verification_and_safety.png)**: Atomic claim extraction, source-sufficiency gating, premise-hypothesis entailment checking, and anti-silent-repair invariant validation.
4. **[diagram4_roadmap_pyramid.png](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/diagrams/diagram4_roadmap_pyramid.png)**: Hierarchical milestone pyramid from Phase 0 (Foundation) through Phase 3 (Evaluation & User Studies).

### 2.3 Core Data Models & Schema Layer (`src/velis_rag/models/`)
Type-safe Pydantic v2 schemas defining all system contracts:
- **[enums.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/enums.py)**: Enums for `TrustTier` (Tier A/B/C), `DocumentType`, `VerificationStatus`, `AbstentionReason`, `Language` (EN, HI), and `InvariantType`.
- **[metadata.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/metadata.py)**: `LegalDocumentMetadata` capturing source URLs, issuing authorities, legal gazette identifiers, jurisdiction, and SHA-256 byte signatures.
- **[chunk.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/chunk.py)**: `PassageChunk` holding text chunks with cryptographic binding (`raw_file_sha256`, `normalized_text_sha256`), structural hierarchy (section, clause), and trust tier.
- **[query.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/query.py)**: `CitizenQuery` schema handling citizen language selection, query texts, and safety classification.
- **[invariant.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/invariant.py)**: `Invariant` contract capturing statutory fees, time windows, legal sections, and normalized numeric representations.
- **[verification.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/verification.py)**: `VerificationResult` containing atomic claims, premise chunk bindings, NLI probabilities, and entailment decisions.
- **[brief.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/brief.py)**: `CitizenBrief` schema outputting simplified guidance, mandatory Tier B disclaimers, explicit citations, and refusal/abstention notices.
- **[registry.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/models/registry.py)**: `SourceRegistryEntry` ensuring strict domain allowlisting.

### 2.4 Governance & Security Framework (`src/velis_rag/governance/`)
- **[provenance.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/governance/provenance.py)**:
  - Cryptographic dual-hashing functions: Raw byte SHA-256 and whitespace-normalized UTF-8 text SHA-256.
  - Tamper detection and verification routines.
- **[registry.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/governance/registry.py)**:
  - YAML-backed source domain allowlist manager.
  - Defense against open-redirects and SSRF via strict canonical host vs. file-delivery host separation.
- **[configs/source_allowlist.yaml](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/configs/source_allowlist.yaml)**:
  - Curated, approved official government domains (`indiacode.nic.in`, `rti.gov.in`, `pmkisan.gov.in`, `nha.gov.in`, `pmjay.gov.in`, etc.).

### 2.5 Invariant Normalization Engine (`src/velis_rag/normalization/`)
- **[invariants.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/src/velis_rag/normalization/invariants.py)**:
  - Multilingual invariant extraction and normalization.
  - Native Devanagari Hindi numeral conversion (`०-९` $\rightarrow$ `0-9`).
  - Statutory fee normalization (e.g., `₹10`, `Rs. 10`, `दस रुपये`).
  - Statutory deadline normalization (e.g., `30 days`, `48 hours` for RTI life or liberty).
  - Anti-silent-repair policy: Prevents hallucinated or arbitrary overwrites; flags discrepancies for rejection/human escalation.

### 2.6 Governance & Operational Markdown Guidelines (`docs/`)
- **[GOVERNANCE.md](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/GOVERNANCE.md)**: Architectural governance policies and principles.
- **[TRUST_TIERS.md](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/TRUST_TIERS.md)**: Tier A, Tier B, and Tier C operational boundaries and constraints.
- **[PROVENANCE.md](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/PROVENANCE.md)**: Cryptographic hashing specs and audit trail procedures.
- **[SOURCE_APPROVAL.md](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/SOURCE_APPROVAL.md)**: Procedures for vetting and approving new official government sources.
- **[PHASE1_ENTRY_REQUIREMENTS.md](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/PHASE1_ENTRY_REQUIREMENTS.md)**: Mandatory gate checklist required before initiating corpus ingestion in Phase 1.

### 2.7 Test Suite & Verification (`tests/`)
All tests run in isolated offline mode and pass 100%:
- **[tests/test_schemas.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/tests/test_schemas.py)**: Pydantic v2 validation across all models.
- **[tests/test_provenance.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/tests/test_provenance.py)**: Test vectors for raw byte and text SHA-256 hashes, integrity checking.
- **[tests/test_registry.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/tests/test_registry.py)**: Source allowlist validation, host spoofing prevention, host separation.
- **[tests/test_trust_tiers.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/tests/test_trust_tiers.py)**: Enforcing restrictions on Tier B and rejection of untrusted materials.
- **[tests/test_invariants.py](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/tests/test_invariants.py)**: Property-based testing (via Hypothesis) and unit tests for English and Devanagari Hindi numeric, currency, duration, and section invariants.

---

## 3. Test Execution Summary

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\devna\OneDrive\Desktop\Research_Project
configfile: pyproject.toml
testpaths: tests
plugins: hypothesis-6.168.0, asyncio-0.26.0

tests\test_invariants.py .......                                         [ 20%]
tests\test_provenance.py .......                                         [ 40%]
tests\test_registry.py ......                                            [ 57%]
tests\test_schemas.py .........                                          [ 82%]
tests\test_trust_tiers.py ......                                         [100%]

======================== 35 passed, 1 warning in 1.67s ========================
```

---

## 4. Current State & Readiness for Phase 1

Phase 0 has completed all architectural and baseline software prerequisites:
- [x] Pydantic models & data contracts created and tested.
- [x] Dual-hash cryptographic provenance implemented.
- [x] Official government source allowlist configured.
- [x] Multilingual statutory invariant normalizer tested with Hypothesis property tests.
- [x] Research proposal specification typeset and compiled to DOCX & PDF with 4 architectural diagrams.
- [x] Phase 1 entry gate checklist documented.

**Next Immediate Step:** Review the [PHASE1_ENTRY_REQUIREMENTS.md](file:///c:/Users/devna/OneDrive/Desktop/Research_Project/docs/PHASE1_ENTRY_REQUIREMENTS.md) checklist to begin the controlled ingestion of the seed corpus (RTI Act 2005, PM-KISAN, and PM-JAY operational guidelines).

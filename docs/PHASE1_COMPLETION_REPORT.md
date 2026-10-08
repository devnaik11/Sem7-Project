# Phase 1 Completion Report — Curated Official Corpus Ingestion

**Date:** 2026-10-09  
**Commit SHA:** `4197f6e`  
**Phase 0 baseline SHA:** `0700401`

---

## 1. Source Approval Review

All four seed sources were verified before download via direct HTTP probe (Content-Type, file size, PDF text inspection).

| # | Document | Source ID | Delivery Host | Trust Tier | Licensing Basis |
|---|----------|-----------|---------------|-----------|-----------------|
| 1 | Right to Information Act, 2005 | `india-code-central` | `cdnbbsr.s3waas.gov.in` | Tier A | Sec. 52(1)(q) Indian Copyright Act 1957 — official government enactment |
| 2 | RTI Rules, 2012 (G.S.R. 603-E) | `dopt-rti-rules` | `cdnbbsr.s3waas.gov.in` | Tier A | MoPP&P Gazette notification — official government enactment |
| 3 | PM-KISAN Revised Operational Guidelines (English) | `pmkisan-portal` | `pmkisan.gov.in` | Tier A | Ministry of Agriculture and Farmers Welfare |
| 4 | PM-JAY Beneficiary Identification Guidelines | `pmjay-nha` | `hem.nha.gov.in` | Tier A | National Health Authority |

---

## 2. Ingestion Results

| Document | Local Filename | Raw SHA-256 | Norm-text SHA-256 | Pages | Bytes |
|----------|----------------|-------------|-------------------|-------|-------|
| RTI Act 2005 | `rti_act_2005.pdf` | `489cf9bc...b7159` | `df2e7d1a...92cf6` | 21 | 851,200 |
| RTI Rules 2012 | `rti_rules_2012.pdf` | `69ff4f33...18168` | `81da3586...e4f9` | 4 | 159,699 |
| PM-KISAN Guidelines | `pmkisan_operational_guidelines.pdf` | `ae82cac8...97f` | `c1005a8a...7430` | 12 | 824,649 |
| PM-JAY BIG | `pmjay_beneficiary_identification_guidelines.pdf` | `5ce01373...b62` | `fa74d283...a19` | 16 | 3,560,550 |

**Full hashes:**

| File | raw_sha256 | norm_text_sha256 |
|------|-----------|-----------------|
| rti_act_2005.pdf | `489cf9bc21c775117503c54f2df7402905b94c83d4a40b72456454157bdb7159` | `df2e7d1a0e7f61953cbc6e2e83314d14ca07c47277a18ac33c76efac97092cf6` |
| rti_rules_2012.pdf | `69ff4f337ef8d84dc8e0432d4196c7610649f1c432e71c908ed32da4f4918168` | `81da3586d6a1fcc62b13c648cd926c8881246abab9ee8d25c819ed6ba9a0e4f9` |
| pmkisan_operational_guidelines.pdf | `ae82cac83f61a5fa5049387a7c13e00c6d55cef0e9163deb5497dc86c86d697f` | `c1005a8a37c8eb8e70e73df5f4eb491ecc9ebee911750b65c7c957cc4f4a7430` |
| pmjay_beneficiary_identification_guidelines.pdf | `5ce0137307176a67e883d063bfe14ab62cd18f081c1aec6ddbb2b323dedd9b62` | `fa74d283079b94d40562c71a412736e403d3c73322c227336fead9670fca3a19` |

All four: governance check passed, `%PDF` magic bytes verified, zero failures.

---

## 3. Files Created This Phase

| File | Description |
|------|-------------|
| `configs/source_allowlist.yaml` v1.1.0 | Updated with verified delivery hosts, path regex, trust tiers |
| `scripts/ingest_phase1.py` | Governance-gated downloader: registry validation → download → PDF check → dual hash → SQLite catalog |
| `data/raw/rti_act_2005.pdf` | RTI Act 2005 raw PDF |
| `data/raw/rti_rules_2012.pdf` | RTI Rules 2012 raw PDF |
| `data/raw/pmkisan_operational_guidelines.pdf` | PM-KISAN Operational Guidelines raw PDF |
| `data/raw/pmjay_beneficiary_identification_guidelines.pdf` | PM-JAY Beneficiary Identification Guidelines raw PDF |
| `data/processed/catalog.db` | SQLite provenance catalog (gitignored — regenerate with script) |

---

## 4. Scope Boundaries Confirmed

- No vector database initialized
- No AI/ML model weights downloaded
- No cloud inference API called
- No user interface built
- Phase 2 retrieval pipeline not started

---

## 5. Next Phase

Phase 2: bilingual chunking and normalization (PyMuPDF text extraction, clause-boundary segmentation, Devanagari numeral normalization, chunk-level provenance to catalog row IDs).

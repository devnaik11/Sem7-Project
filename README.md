# VeLiS-RAG: Verified Multilingual Legal Simplification with Adaptive Hybrid Retrieval

VeLiS-RAG is a research prototype for citizen-centric administrative and legal simplification of Indian government documents, focusing on Right to Information (RTI) procedures and public welfare schemes.

## Key Principles
- **Tiered Evidence Model:** Clear distinction between Tier A (operative legal enactments), Tier B (contextual circulars with mandatory warnings), and Tier C (untrusted user/external materials).
- **Epistemic Honesty:** Calibrated research evaluation (reporting observed unsupported-claim rates with 95% bootstrap confidence intervals) over unverifiable "zero-hallucination" guarantees.
- **Dual-Hash Provenance:** Every passage is cryptographically bound to raw file bytes SHA-256 and normalized text SHA-256.
- **Strict Invariant Consistency:** Normalized preservation of fees, dates, statutory deadlines, section numbers, and government entities across English and Hindi.
- **Data-Only Prompt-Injection Defense:** All evidence and user texts are treated strictly as data within immutable system instructions and schema boundaries.

# VeLiS-RAG Data Governance & Compliance Framework

## 1. Statutory Grounding & Epistemic Authority
VeLiS-RAG is a research prototype designed to simplify Indian legal and governmental texts for citizens. To guarantee integrity:
- Only official government legal enactments, notified rules, and operational guidelines serve as legal authority.
- The system must never extrapolate, predict judicial outcomes, or invent non-existent schemes, dates, fees, or authorities.
- The system is strictly an administrative simplification system, **not a legal advice or decision system**.

## 2. Source-by-Source Licensing & Intellectual Property
- **Statutory Authority:** Section 52(1)(q) of the **Indian Copyright Act, 1957** explicitly exempts from copyright infringement:
  - The reproduction or publication of any matter published in any Official Gazette.
  - Any Act of a Legislature.
  - Any report of a committee appointed by Government.
  - Any judgment or order of a court, tribunal or other judicial authority.
- **Open Government Data:** Data published under the **Government Open Data License - India (GODL-India)** or the National Data Sharing and Accessibility Policy (NDSAP) is attributed accordingly.
- **Source-by-Source Recording:** Blanket licensing assumptions are prohibited. Every document must register its specific reuse basis in `LegalDocumentMetadata.license_and_reuse_basis`.

## 3. Privacy & Data Minimization
- **Zero PII Policy:** No personal citizen data, RTI docket names, personal addresses, or litigant identities may be ingested.
- **Local Control:** All data is processed locally. Local storage avoids external inference API transmission, but local OS-level access, disk permissions, model checksum verification, and backup protections remain part of operational governance.

## 4. Pre-Publication Compliance Review
Before any dataset, benchmark, or model weights are published externally:
1. PII Scan: Automated regex and named entity checks for private individuals.
2. Licensing Verification: Confirmation that 100% of included documents have explicit statutory or open-data reuse bases.
3. Dual-Hash Audit: Integrity check confirming original file hashes match extracted text hashes without corrupted artifacts.

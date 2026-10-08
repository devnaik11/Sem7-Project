# Phase 1 Entry Requirements & Gate Checklist

Phase 1 encompasses the ingestion of the initial curated seed corpus. **Phase 1 must not begin until Phase 0 is formally approved.**

## Gate Checklist to Enter Phase 1
- [ ] Phase 0 test suite runs completely green in offline mode (`pytest` 100% pass).
- [ ] All Pydantic schemas validated for models:
  - `LegalDocumentMetadata`
  - `SourceRegistryEntry`
  - `PassageChunk`
  - `CitizenQuery`
  - `Invariant`
  - `VerificationResult`
  - `CitizenBrief`
- [ ] Source allowlist registry configured with separated canonical and file-delivery hosts.
- [ ] Dual-hash calculation functions verified against known test vectors.
- [ ] Tier B operative claim restriction enforced in test assertions.
- [ ] User gives explicit approval to proceed to Phase 1.

## Scope of Phase 1 (Once Approved)
- Ingest seed documents:
  1. *Right to Information Act, 2005* & *Central RTI Rules, 2012*.
  2. *PM Kisan Samman Nidhi Operational Guidelines*.
  3. *Ayushman Bharat - PM-JAY Operational Guidelines*.
- Verify raw file byte SHA-256 and normalized text SHA-256 upon fetch.
- Retain original files in `data/raw/` and parsed artifacts in `data/processed/`.
- No model weight downloads or vector indexing until Phase 2.

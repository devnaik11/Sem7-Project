# VeLiS-RAG Source Trust Tier Classification

VeLiS-RAG enforces a strict 3-tier evidence model to prevent unreliable or unauthorized sources from compromising legal facts.

## Trust Tier Matrix

| Tier | Name | Eligible Documents | Evidentiary Role | Restrictions & Rules |
| :--- | :--- | :--- | :--- | :--- |
| **Tier A** | **Authoritative Legal Ground Truth** | - Acts of Parliament / State Legislatures<br/>- Gazetted Statutory Rules (e.g. Central RTI Rules 2012)<br/>- Officially notified Operational Guidelines (e.g. PM-KISAN, PM-JAY) | **Binding Legal Evidence.**<br/>Only Tier A can support legally operative claims. | Must originate from an approved canonical host or approved file-delivery host. Full dual-hash provenance required. |
| **Tier B** | **Qualified Official Context** | - Ministry circulars & office memoranda<br/>- Explanatory FAQs & press notes<br/>- Draft notifications & consultation papers | **Context & Discovery Only.**<br/>May explain administrative context or background. | **PROHIBITED from supporting legally operative claims** (eligibility, fees, deadlines, penalties, legal rights, mandatory procedures). Must carry a prominent non-operative caveat. |
| **Tier C** | **Untrusted / Non-Evidence Material** | - User-uploaded documents (PDFs, scans)<br/>- Citizen queries & letters<br/>- Third-party websites, news, blogs | **Target Subject Matter Only.**<br/>Never treated as evidence. | **Untrusted by default.** Used only as the subject text to be simplified, audited, or cross-referenced against Tier A/B. Never indexed as legal ground truth. |

## Operative Claim Enforcement Rules
An **Operative Claim** is defined as any statement that asserts:
1. **Eligibility Criteria:** Who qualifies or does not qualify for a benefit/scheme.
2. **Statutory Fees:** Numerical amounts required to apply, appeal, or inspect records.
3. **Deadlines & Timelines:** Statutory disposal windows (e.g., 30 days, 48 hours), limitation periods for appeal.
4. **Penalties & Sanctions:** Fines, disciplinary actions, interest charges.
5. **Statutory Rights & Remedies:** Legal entitlements under an Act, mandatory appeal routes.
6. **Mandatory Procedures:** Compulsory procedural steps required by law.

**Rule:** If a claim is an Operative Claim, it MUST be supported exclusively by `Tier A` citations. Any attempt to ground an operative claim in `Tier B` or `Tier C` material must be rejected by the verification pipeline.

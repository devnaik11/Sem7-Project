# Source Approval & Registry Addition Workflow

No document may be fetched or ingested into VeLiS-RAG unless its canonical host and file delivery host are registered in `configs/source_allowlist.yaml`.

## 4-Step Governance Process

### Step 1: Proposal Submission
A research team member submits a Source Addition Request documenting:
- Proposed Source ID (e.g. `india-code-central`).
- Canonical Host (e.g. `www.indiacode.nic.in`).
- Approved File-Delivery Hosts (e.g. `cdnbbsr.s3waas.gov.in`).
- Target Document Types (e.g. `Central Act`, `Statutory Rules`).
- Allowed Path Regex Patterns.
- Proposed Trust Tier (`Tier_A` or `Tier_B`).
- Statutory or Licensing Basis.

### Step 2: Authority & Gazette Verification
The researcher verifies:
- Is the host an official ministry or legislative portal?
- Is the document an enacted statute or published gazette?
- Has it been superseded by subsequent amendments?
- If file delivery redirects to a CDN or S3 bucket, is that CDN an approved Government of India infrastructure provider (e.g., S3WaaS / NIC)?

### Step 3: Licensing & Reuse Check
- Check Section 52(1)(q) applicability or specific GODL-India terms.
- Confirm zero commercial copyright restrictions.
- Ensure no private commentary or proprietary headnotes exist in the source.

### Step 4: PI & Lead Engineer Sign-off
- Lead Research Engineer reviews the pull request.
- Automated tests run against `configs/source_allowlist.yaml` to ensure no wildcard hosts or malformed path patterns.
- Explicit approval merges the entry into the active allowlist.

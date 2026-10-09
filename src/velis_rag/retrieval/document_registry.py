"""Document metadata registry mapping document identifiers to official provenance attributes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class DocumentRegistryEntry:
    document_id: str
    title: str
    source_id: str
    issuing_authority: str
    jurisdiction: str
    doc_type: str
    canonical_url: str
    delivery_url: str
    raw_file_sha256: str
    norm_doc_text_sha256: str
    doc_version: str
    effective_date: str | None
    trust_tier: str = "Tier_A"


OFFICIAL_DOCUMENTS: Final[dict[str, DocumentRegistryEntry]] = {
    "rti_act_2005": DocumentRegistryEntry(
        document_id="rti_act_2005",
        title="Right to Information Act, 2005",
        source_id="india-code-central",
        issuing_authority="Ministry of Personnel, Public Grievances and Pensions",
        jurisdiction="IN-CENTRAL",
        doc_type="Central Act",
        canonical_url="https://www.indiacode.nic.in/handle/123456789/2065",
        delivery_url="https://cdnbbsr.s3waas.gov.in/s3169779d3852b32ce8b1a1724dbf5217d/uploads/2022/05/2022050955.pdf",
        raw_file_sha256="489cf9bc21c775117503c54f2df7402905b94c83d4a40b72456454157bdb7159",
        norm_doc_text_sha256="df2e7d1a0e7f61953cbc6e2e83314d14ca07c47277a18ac33c76efac97092cf6",
        doc_version="Act No. 22 of 2005 (as amended 2019)",
        effective_date="2005-10-12",
        trust_tier="Tier_A",
    ),
    "rti_rules_2012": DocumentRegistryEntry(
        document_id="rti_rules_2012",
        title="Right to Information Rules, 2012",
        source_id="dopt-rti-rules",
        issuing_authority="Ministry of Personnel, Public Grievances and Pensions",
        jurisdiction="IN-CENTRAL",
        doc_type="Statutory Rules",
        canonical_url="https://cdnbbsr.s3waas.gov.in/s3dcf6070a4ab7f3afbfd2809173e0824b/uploads/2025/08/202508301650981496.pdf",
        delivery_url="https://cdnbbsr.s3waas.gov.in/s3dcf6070a4ab7f3afbfd2809173e0824b/uploads/2025/08/202508301650981496.pdf",
        raw_file_sha256="69ff4f337ef8d84dc8e0432d4196c7610649f1c432e71c908ed32da4f4918168",
        norm_doc_text_sha256="81da3586d6a1fcc62b13c648cd926c8881246abab9ee8d25c819ed6ba9a0e4f9",
        doc_version="G.S.R. 603(E) dated 31 July 2012",
        effective_date="2012-07-31",
        trust_tier="Tier_A",
    ),
    "pmkisan_guidelines": DocumentRegistryEntry(
        document_id="pmkisan_guidelines",
        title="PM-KISAN Revised Operational Guidelines (English)",
        source_id="pmkisan-portal",
        issuing_authority="Ministry of Agriculture and Farmers Welfare",
        jurisdiction="IN-CENTRAL",
        doc_type="Operational Scheme Guidelines",
        canonical_url="https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        delivery_url="https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        raw_file_sha256="ae82cac83f61a5fa5049387a7c13e00c6d55cef0e9163deb5497dc86c86d697f",
        norm_doc_text_sha256="c1005a8a37c8eb8e70e73df5f4eb491ecc9ebee911750b65c7c957cc4f4a7430",
        doc_version="Revised Operational Guidelines (March 2020)",
        effective_date="2020-03-01",
        trust_tier="Tier_A",
    ),
    "pmjay_big": DocumentRegistryEntry(
        document_id="pmjay_big",
        title="Ayushman Bharat PM-JAY Beneficiary Identification Guidelines",
        source_id="pmjay-nha",
        issuing_authority="National Health Authority",
        jurisdiction="IN-CENTRAL",
        doc_type="Beneficiary Identification Guidelines",
        canonical_url="https://nha.gov.in/PM-JAY/operational-guidelines",
        delivery_url="https://hem.nha.gov.in/BeneficiaryIdentification.pdf",
        raw_file_sha256="5ce0137307176a67e883d063bfe14ab62cd18f081c1aec6ddbb2b323dedd9b62",
        norm_doc_text_sha256="fa74d283079b94d40562c71a412736e403d3c73322c227336fead9670fca3a19",
        doc_version="NHA Beneficiary Identification Guidelines",
        effective_date=None,
        trust_tier="Tier_A",
    ),
}

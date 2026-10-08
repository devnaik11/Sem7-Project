"""Schema validation and rejection tests for VeLiS-RAG models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from velis_rag.models.brief import BilingualBrief, CitizenBrief, CitizenBriefSection
from velis_rag.models.chunk import PassageChunk
from velis_rag.models.enums import (
    ClaimType,
    LanguageCode,
    TrustTier,
)
from velis_rag.models.metadata import LegalDocumentMetadata
from velis_rag.models.query import CitizenQuery
from velis_rag.models.registry import SourceRegistryEntry


def test_source_registry_entry_valid(sample_registry_entry: SourceRegistryEntry) -> None:
    """Test that a well-formed SourceRegistryEntry validates correctly."""
    assert sample_registry_entry.id == "sample-india-code"
    assert sample_registry_entry.canonical_host == "www.indiacode.nic.in"
    assert "cdnbbsr.s3waas.gov.in" in sample_registry_entry.approved_file_delivery_hosts


def test_source_registry_entry_rejects_wildcard_host() -> None:
    """Test that wildcard hosts in canonical_host or file_delivery_hosts are rejected."""
    with pytest.raises(ValidationError, match="Wildcards or spaces forbidden"):
        SourceRegistryEntry(
            id="bad-entry",
            canonical_host="*.indiacode.nic.in",
            approved_file_delivery_hosts=["www.indiacode.nic.in"],
            allowed_document_types=["Act"],
            allowed_path_patterns=[r"^/.*"],
            default_trust_tier=TrustTier.Tier_A,
            licensing_and_reuse_basis="Section 52(1)(q)",
        )

    with pytest.raises(ValidationError, match="Wildcards or spaces forbidden"):
        SourceRegistryEntry(
            id="bad-entry-2",
            canonical_host="www.indiacode.nic.in",
            approved_file_delivery_hosts=["*.s3waas.gov.in"],
            allowed_document_types=["Act"],
            allowed_path_patterns=[r"^/.*"],
            default_trust_tier=TrustTier.Tier_A,
            licensing_and_reuse_basis="Section 52(1)(q)",
        )


def test_legal_doc_metadata_valid(valid_doc_metadata: LegalDocumentMetadata) -> None:
    """Test that valid LegalDocumentMetadata instantiates correctly."""
    assert valid_doc_metadata.document_id == "RTI-ACT-2005-CENTRAL"
    assert len(valid_doc_metadata.raw_file_sha256) == 64
    assert len(valid_doc_metadata.extracted_text_sha256) == 64


def test_legal_doc_metadata_rejects_placeholder_hash() -> None:
    """Test that placeholder hashes are strictly rejected in runtime LegalDocumentMetadata."""
    with pytest.raises(ValidationError, match="Placeholder hashes strictly rejected"):
        LegalDocumentMetadata(
            document_id="RTI-ACT-2005-CENTRAL",
            title="Right to Information Act, 2005",
            issuing_authority="Ministry of Personnel",
            jurisdiction="Union of India",
            source_url="https://www.indiacode.nic.in/handle/123456789/2065",
            final_file_url="https://www.indiacode.nic.in/bitstream/123456789/2065/1/act.pdf",
            doc_type="Central Act",
            source_tier=TrustTier.Tier_A,
            document_version="2019",
            raw_file_sha256="PLACEHOLDER_HASH_RAW_FILE_BYTES_ONLY",
            extracted_text_sha256="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            download_timestamp=datetime.now(UTC),
            license_and_reuse_basis="Section 52(1)(q)",
        )


def test_legal_doc_metadata_rejects_malformed_url() -> None:
    """Test that invalid URL protocols are rejected."""
    with pytest.raises(ValidationError, match="Invalid URL protocol"):
        LegalDocumentMetadata(
            document_id="RTI-ACT-2005-CENTRAL",
            title="Right to Information Act, 2005",
            issuing_authority="Ministry of Personnel",
            jurisdiction="Union of India",
            source_url="ftp://www.indiacode.nic.in/handle/123456789/2065",
            final_file_url="https://www.indiacode.nic.in/act.pdf",
            doc_type="Central Act",
            source_tier=TrustTier.Tier_A,
            document_version="2019",
            raw_file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            extracted_text_sha256="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            download_timestamp=datetime.now(UTC),
            license_and_reuse_basis="Section 52(1)(q)",
        )


def test_passage_chunk_valid_and_placeholder_rejection() -> None:
    """Test PassageChunk creation and placeholder rejection."""
    chunk = PassageChunk(
        chunk_id="RTI-ACT-2005-SEC-6-1",
        document_id="RTI-ACT-2005-CENTRAL",
        section_hierarchy=["Chapter II", "Section 6", "Sub-section 1"],
        text_content="A person who desires to obtain any information under this Act...",
        source_tier=TrustTier.Tier_A,
        source_url="https://www.indiacode.nic.in/handle/123456789/2065",
        issuing_authority="Ministry of Personnel",
        jurisdiction="Union of India",
        document_version="2019",
        extracted_text_sha256="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
    )
    assert chunk.chunk_id == "RTI-ACT-2005-SEC-6-1"

    with pytest.raises(ValidationError, match="Placeholder hashes strictly rejected"):
        PassageChunk(
            chunk_id="RTI-ACT-2005-SEC-6-1",
            document_id="RTI-ACT-2005-CENTRAL",
            section_hierarchy=["Chapter II"],
            text_content="A person who desires to obtain any information...",
            source_tier=TrustTier.Tier_A,
            source_url="https://www.indiacode.nic.in/handle/123456789/2065",
            issuing_authority="Ministry of Personnel",
            jurisdiction="Union of India",
            document_version="2019",
            extracted_text_sha256="PLACEHOLDER_HASH_CHUNK",
        )


def test_citizen_query_schema() -> None:
    """Test CitizenQuery schema validation."""
    query = CitizenQuery(
        query_id="Q-001",
        query_text="What is the fee to file an RTI application?",
        language=LanguageCode.EN,
        target_claim_type=ClaimType.OPERATIVE,
    )
    assert query.query_id == "Q-001"
    assert query.language == LanguageCode.EN


def test_citizen_brief_mandatory_disclaimer() -> None:
    """Test that CitizenBrief fails validation if disclaimer_present is False."""
    section = CitizenBriefSection(
        title="Application Fee",
        content="The application fee for filing an RTI request is Rs. 10.",
        citations=["RTI-ACT-2005-SEC-6-1"],
    )
    with pytest.raises(ValidationError, match="Mandatory non-legal-advice disclaimer cannot be omitted"):
        CitizenBrief(
            query_id="Q-001",
            language=LanguageCode.EN,
            summary="RTI application fee is Rs. 10.",
            sections=[section],
            disclaimer_present=False,
        )


def test_bilingual_brief_language_enforcement() -> None:
    """Test that BilingualBrief validates english and hindi brief language codes."""
    section_en = CitizenBriefSection(
        title="Fee",
        content="The fee is Rs. 10.",
        citations=["RTI-ACT-2005-SEC-6-1"],
    )
    section_hi = CitizenBriefSection(
        title="शुल्क",
        content="आरटीआई आवेदन का शुल्क 10 रुपये है।",
        citations=["RTI-ACT-2005-SEC-6-1"],
    )

    brief_en = CitizenBrief(
        query_id="Q-001",
        language=LanguageCode.EN,
        summary="Fee is Rs. 10.",
        sections=[section_en],
        disclaimer_present=True,
    )
    brief_hi = CitizenBrief(
        query_id="Q-001",
        language=LanguageCode.HI,
        summary="शुल्क 10 रुपये है।",
        sections=[section_hi],
        disclaimer_present=True,
    )

    bilingual = BilingualBrief(
        query_id="Q-001",
        english_brief=brief_en,
        hindi_brief=brief_hi,
        invariants_match=True,
    )
    assert bilingual.query_id == "Q-001"

    # Inverting language should fail validation
    with pytest.raises(ValidationError, match="english_brief must have language 'en'"):
        BilingualBrief(
            query_id="Q-001",
            english_brief=brief_hi,
            hindi_brief=brief_en,
            invariants_match=True,
        )

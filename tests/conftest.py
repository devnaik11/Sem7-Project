"""Pytest configuration and shared fixtures for offline deterministic testing."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from velis_rag.governance.registry import SourceRegistry
from velis_rag.models.enums import TrustTier
from velis_rag.models.metadata import LegalDocumentMetadata
from velis_rag.models.registry import SourceRegistryEntry


@pytest.fixture
def sample_registry_entry() -> SourceRegistryEntry:
    """Fixture providing an approved sample source registry entry."""
    return SourceRegistryEntry(
        id="sample-india-code",
        canonical_host="www.indiacode.nic.in",
        approved_file_delivery_hosts=["www.indiacode.nic.in", "cdnbbsr.s3waas.gov.in"],
        allowed_document_types=["Central Act", "Statutory Rules"],
        allowed_path_patterns=[r"^/handle/[0-9]+/[0-9]+.*", r"^/s3waas/.*\.pdf$"],
        default_trust_tier=TrustTier.Tier_A,
        licensing_and_reuse_basis="Section 52(1)(q) Indian Copyright Act 1957",
        status="active",
    )


@pytest.fixture
def sample_registry(sample_registry_entry: SourceRegistryEntry) -> SourceRegistry:
    """Fixture providing a SourceRegistry instance with sample entries."""
    return SourceRegistry([sample_registry_entry])


@pytest.fixture
def active_config_registry() -> SourceRegistry:
    """Fixture loading the project's actual source allowlist configuration."""
    config_path = Path(__file__).parent.parent / "configs" / "source_allowlist.yaml"
    return SourceRegistry.from_yaml(config_path)


@pytest.fixture
def valid_doc_metadata() -> LegalDocumentMetadata:
    """Fixture providing valid document metadata with verified non-placeholder SHA-256 digests."""
    return LegalDocumentMetadata(
        document_id="RTI-ACT-2005-CENTRAL",
        title="Right to Information Act, 2005",
        issuing_authority="Ministry of Personnel, Public Grievances and Pensions",
        jurisdiction="Union of India",
        source_url="https://www.indiacode.nic.in/handle/123456789/2065",
        final_file_url="https://cdnbbsr.s3waas.gov.in/s3waas/rti_act_2005.pdf",
        doc_type="Central Act",
        source_tier=TrustTier.Tier_A,
        publication_date="2005-06-21",
        effective_date="2005-10-12",
        document_version="As amended by Act 24 of 2019",
        raw_file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        extracted_text_sha256="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
        download_timestamp=datetime.now(UTC),
        license_and_reuse_basis="Indian Copyright Act 1957 Section 52(1)(q)",
        compliance_checkpoint_passed=True,
    )

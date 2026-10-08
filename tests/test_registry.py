"""Tests for source allowlist registry and canonical/redirect host validation."""

from velis_rag.governance.registry import SourceRegistry


def test_approved_page_redirecting_to_approved_file_host(sample_registry: SourceRegistry) -> None:
    """Test approval when canonical page redirects to an approved official file-delivery host."""
    canonical_url = "https://www.indiacode.nic.in/handle/123456789/2065"
    # Approved redirect to official S3WaaS / NIC CDN host
    final_file_url = "https://cdnbbsr.s3waas.gov.in/s3waas/rti_act_2005.pdf"
    doc_type = "Central Act"

    approved, msg, entry = sample_registry.validate_source(canonical_url, final_file_url, doc_type)
    assert approved is True
    assert entry is not None
    assert entry.id == "sample-india-code"
    assert "approved" in msg.lower()


def test_rejection_of_redirect_to_unapproved_host(sample_registry: SourceRegistry) -> None:
    """Test strict rejection when canonical page redirects to an unapproved host."""
    canonical_url = "https://www.indiacode.nic.in/handle/123456789/2065"
    # Malicious or unapproved third-party host
    unapproved_file_url = "https://unauthorized-mirror.org/s3waas/rti_act_2005.pdf"
    doc_type = "Central Act"

    approved, msg, entry = sample_registry.validate_source(canonical_url, unapproved_file_url, doc_type)
    assert approved is False
    assert "Unapproved redirect/file-delivery host" in msg
    assert "unauthorized-mirror.org" in msg


def test_rejection_of_unknown_canonical_host(sample_registry: SourceRegistry) -> None:
    """Test rejection when canonical host is not in the approved registry."""
    canonical_url = "https://www.privatelegalblog.in/laws/rti-act"
    final_url = "https://www.privatelegalblog.in/downloads/rti.pdf"
    doc_type = "Central Act"

    approved, msg, entry = sample_registry.validate_source(canonical_url, final_url, doc_type)
    assert approved is False
    assert entry is None
    assert "Unknown or unapproved canonical host" in msg


def test_rejection_of_unapproved_path(sample_registry: SourceRegistry) -> None:
    """Test rejection when the URL path does not match approved regex patterns."""
    canonical_url = "https://www.indiacode.nic.in/unapproved-admin-endpoint"
    final_url = "https://www.indiacode.nic.in/unapproved-admin-endpoint"
    doc_type = "Central Act"

    approved, msg, entry = sample_registry.validate_source(canonical_url, final_url, doc_type)
    assert approved is False
    assert "does not match any allowed path pattern" in msg


def test_rejection_of_unapproved_doc_type(sample_registry: SourceRegistry) -> None:
    """Test rejection when doc_type is not registered for that source."""
    canonical_url = "https://www.indiacode.nic.in/handle/123456789/2065"
    final_url = "https://www.indiacode.nic.in/handle/123456789/2065"
    # Unapproved doc type for this entry
    doc_type = "Unofficial Commentary"

    approved, msg, entry = sample_registry.validate_source(canonical_url, final_url, doc_type)
    assert approved is False
    assert "Document type 'Unofficial Commentary' is not allowed" in msg


def test_project_active_config_registry(active_config_registry: SourceRegistry) -> None:
    """Test that the live configs/source_allowlist.yaml loads and validates key sources."""
    # Test India Code
    ok, msg, entry = active_config_registry.validate_source(
        canonical_url="https://www.indiacode.nic.in/handle/123456789/2065",
        final_url="https://cdnbbsr.s3waas.gov.in/s3waas/rti_act.pdf",
        doc_type="Central Act",
    )
    assert ok is True
    assert entry is not None
    assert entry.id == "india-code-central"

    # Test RTI Portal
    ok_rti, _, entry_rti = active_config_registry.validate_source(
        canonical_url="https://rti.gov.in/rules/rti-rules-2012.html",
        final_url="https://dopt.gov.in/circular/rti-rules-2012.pdf",
        doc_type="Statutory Rules",
    )
    assert ok_rti is True
    assert entry_rti is not None
    assert entry_rti.id == "rti-portal-central"

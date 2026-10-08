"""Source allowlist registry loader and URL/redirect validation engine."""

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

from velis_rag.models.registry import SourceRegistryEntry


class SourceRegistry:
    """Registry maintaining approved canonical hosts, file-delivery hosts, and path patterns."""

    def __init__(self, entries: list[SourceRegistryEntry] | None = None) -> None:
        self._entries: dict[str, SourceRegistryEntry] = {}
        if entries:
            for entry in entries:
                self._entries[entry.id] = entry

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> "SourceRegistry":
        """Load registry from YAML configuration file."""
        p = Path(yaml_path)
        if not p.exists():
            raise FileNotFoundError(f"Source allowlist configuration file not found at: {p}")

        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or "approved_sources" not in data:
            raise ValueError("Malformed source registry YAML: missing 'approved_sources' list.")

        entries: list[SourceRegistryEntry] = []
        for item in data["approved_sources"]:
            entries.append(SourceRegistryEntry.model_validate(item))

        return cls(entries)

    def get(self, source_id: str) -> SourceRegistryEntry | None:
        """Retrieve registry entry by ID."""
        return self._entries.get(source_id)

    def find_by_canonical_host(self, host: str) -> list[SourceRegistryEntry]:
        """Find active entries matching a canonical host."""
        host = host.strip().lower()
        return [e for e in self._entries.values() if e.canonical_host == host and e.status == "active"]

    def validate_source(
        self,
        canonical_url: str,
        final_url: str,
        doc_type: str,
    ) -> tuple[bool, str, SourceRegistryEntry | None]:
        """Validate canonical URL, resolved redirect URL, and doc_type against approved entries.

        Enforces:
        1. Canonical host must match an approved active source.
        2. Final resolved URL host must be in approved_file_delivery_hosts.
        3. Doc type must be in allowed_document_types.
        4. Canonical or final path must match allowed_path_patterns.
        """
        canonical_parsed = urlparse(canonical_url)
        final_parsed = urlparse(final_url)

        canonical_host = (canonical_parsed.hostname or "").lower()
        final_host = (final_parsed.hostname or "").lower()

        if not canonical_host:
            return False, f"Invalid canonical URL (missing host): {canonical_url}", None

        matching_entries = self.find_by_canonical_host(canonical_host)
        if not matching_entries:
            return False, f"Unknown or unapproved canonical host: '{canonical_host}'", None

        # Check each matching source candidate
        for entry in matching_entries:
            # 1. Validate redirect/file-delivery host
            if final_host not in entry.approved_file_delivery_hosts:
                return (
                    False,
                    f"Unapproved redirect/file-delivery host '{final_host}' for source '{entry.id}'. "
                    f"Approved delivery hosts are: {entry.approved_file_delivery_hosts}",
                    entry,
                )

            # 2. Validate document type
            if doc_type not in entry.allowed_document_types:
                return (
                    False,
                    f"Document type '{doc_type}' is not allowed for source '{entry.id}'. "
                    f"Allowed types: {entry.allowed_document_types}",
                    entry,
                )

            # 3. Validate path patterns (check both canonical path and final path)
            paths_to_check = [canonical_parsed.path, final_parsed.path]
            path_approved = False
            for path in paths_to_check:
                if any(re.compile(p).match(path) for p in entry.allowed_path_patterns):
                    path_approved = True
                    break

            if not path_approved:
                return (
                    False,
                    f"URL path '{canonical_parsed.path}' / '{final_parsed.path}' does not match "
                    f"any allowed path pattern for source '{entry.id}'.",
                    entry,
                )

            return True, "Source URL and redirect host approved.", entry

        return False, "Validation rejected by all matching source policies.", None

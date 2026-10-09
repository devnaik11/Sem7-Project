"""Structural legal hierarchy parser for Indian government PDFs.

Detects legal structural markers (Chapter, Section, Rule, Sub-section,
Proviso, Explanation, Schedule, Annexure) using document-class-aware
regex patterns. Returns a flat ordered list of HierarchyNode objects
that encode depth and parent breadcrumbs.
"""

from __future__ import annotations

import re

from velis_rag.models.phase2a import HierarchyNode, HierarchyNodeType

# ---------------------------------------------------------------------------
# Pattern bank (ordered from most-specific to least-specific)
# Each tuple: (node_type, depth, compiled_regex)
# The regex must have group(1) = label token, group(2) = title text (may be empty)
# ---------------------------------------------------------------------------

_SHARED_HIGH: list[tuple[HierarchyNodeType, int, re.Pattern[str]]] = [
    # Part  (e.g. "PART I", "Part I —")
    (
        HierarchyNodeType.PART,
        1,
        re.compile(
            r"^\s*PART\s+([IVXLCDM0-9]+)\s*[.\-\u2014]?\s*(.*)",
            re.IGNORECASE,
        ),
    ),
    # Chapter (e.g. "CHAPTER II", "Chapter 2 —")
    (
        HierarchyNodeType.CHAPTER,
        1,
        re.compile(
            r"^\s*CHAPTER\s+([IVXLCDM0-9]+)\s*[.\-\u2014]?\s*(.*)",
            re.IGNORECASE,
        ),
    ),
    # Schedule (e.g. "SCHEDULE", "SCHEDULE I", "First Schedule")
    (
        HierarchyNodeType.SCHEDULE,
        1,
        re.compile(
            r"^\s*(?:(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|[IVXLCDM]+)\s+)?SCHEDULE\b\s*(.*)",
            re.IGNORECASE,
        ),
    ),
    # Annexure (e.g. "Annexure A", "ANNEXURE-I")
    (
        HierarchyNodeType.ANNEXURE,
        1,
        re.compile(
            r"^\s*ANNEXURE[\s\-]?([A-Z0-9]*)\s*[.\-]?\s*(.*)",
            re.IGNORECASE,
        ),
    ),
]

_SHARED_LOW: list[tuple[HierarchyNodeType, int, re.Pattern[str]]] = [
    # Clause (e.g. "(a)", "(b)")
    (
        HierarchyNodeType.CLAUSE,
        4,
        re.compile(r"^\s*(\([a-z]{1,2}\))\s+(.{3,})"),
    ),
    # Proviso
    (
        HierarchyNodeType.PROVISO,
        4,
        re.compile(r"^\s*(Provided\s+that)\b(.*)", re.IGNORECASE),
    ),
    # Explanation
    (
        HierarchyNodeType.EXPLANATION,
        4,
        re.compile(r"^\s*(Explanation)\s*[.\-]?\s*(.*)", re.IGNORECASE),
    ),
]

_ACT_PATTERNS: list[tuple[HierarchyNodeType, int, re.Pattern[str]]] = [
    *_SHARED_HIGH,
    # Section (e.g. "Section 6.", "6. Right to information")
    (
        HierarchyNodeType.SECTION,
        2,
        re.compile(
            r"^\s*(?:Section|Sec\.)\s*([0-9]+[A-Z]?)\s*[.\u2014\-]?\s*(.*)",
            re.IGNORECASE,
        ),
    ),
    (
        HierarchyNodeType.SECTION,
        2,
        re.compile(
            r"^\s*([0-9]{1,3}[A-Z]?)\.\s+([A-Z\u0900-\u097F][^\n]{5,})",
        ),
    ),
    # Sub-section (e.g. "(1)", "(1a)")
    (
        HierarchyNodeType.SUB_SECTION,
        3,
        re.compile(r"^\s*(\([0-9]+[a-z]?\))\s+(.*)"),
    ),
    # Explicit Rule in Act context
    (
        HierarchyNodeType.RULE,
        2,
        re.compile(
            r"^\s*(?:Rule)\s*([0-9]+[A-Z]?)\s*[.\u2014\-]?\s*(.*)",
            re.IGNORECASE,
        ),
    ),
    *_SHARED_LOW,
]

_RULE_PATTERNS: list[tuple[HierarchyNodeType, int, re.Pattern[str]]] = [
    *_SHARED_HIGH,
    # Rule (e.g. "Rule 3.", "3. Application")
    (
        HierarchyNodeType.RULE,
        2,
        re.compile(
            r"^\s*(?:Rule)\s*([0-9]+[A-Z]?)\s*[.\u2014\-]?\s*(.*)",
            re.IGNORECASE,
        ),
    ),
    (
        HierarchyNodeType.RULE,
        2,
        re.compile(
            r"^\s*([0-9]{1,3}[A-Z]?)\.\s+([A-Z\u0900-\u097F][^\n]{5,})",
        ),
    ),
    # Sub-rule (e.g. "(1)", "(1a)")
    (
        HierarchyNodeType.SUB_RULE,
        3,
        re.compile(r"^\s*(\([0-9]+[a-z]?\))\s+(.*)"),
    ),
    # Explicit Section in Rules context
    (
        HierarchyNodeType.SECTION,
        2,
        re.compile(
            r"^\s*(?:Section|Sec\.)\s*([0-9]+[A-Z]?)\s*[.\u2014\-]?\s*(.*)",
            re.IGNORECASE,
        ),
    ),
    *_SHARED_LOW,
]


def _match_line(line: str, is_rules: bool = False) -> tuple[HierarchyNodeType, int, str, str] | None:
    """Try to match a line to a hierarchy pattern.

    Returns (node_type, depth, label, title) or None.
    """
    patterns = _RULE_PATTERNS if is_rules else _ACT_PATTERNS
    for node_type, depth, pattern in patterns:
        m = pattern.match(line)
        if m:
            groups = m.groups()
            label = groups[0].strip() if groups else ""
            title = groups[1].strip() if len(groups) > 1 else ""
            return node_type, depth, label, title
    return None


def parse_hierarchy(
    page_results: list[tuple[int, str]],  # (page_num, normalized_text)
    doc_type: str | None = None,
) -> list[HierarchyNode]:
    """Parse a sequence of (page_num, text) tuples into a flat ordered list of HierarchyNode.

    Tracks a breadcrumb stack to assign parent_path to every detected node.
    """
    head_text = " ".join(text for _, text in page_results[:2])
    is_rules = (doc_type is not None and "rule" in doc_type.lower()) or bool(
        re.search(
            r"\b(?:makes the following rules|Right to Information Rules|Statutory Rules|\bRules,\s*\d{4})\b",
            head_text,
            re.IGNORECASE,
        )
    )
    nodes: list[HierarchyNode] = []
    # Stack: list of (depth, label) for breadcrumb tracking
    stack: list[tuple[int, str]] = []

    def _breadcrumb() -> list[str]:
        return [lbl for _, lbl in stack]

    current_page = 1

    for page_num, text in page_results:
        current_page = page_num
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            result = _match_line(stripped, is_rules=is_rules)
            if result is None:
                continue
            node_type, depth, label_token, title_text = result

            # Build human-readable label
            if node_type in (HierarchyNodeType.SECTION, HierarchyNodeType.RULE):
                full_label = f"{node_type.value.title()} {label_token}"
            elif node_type in (HierarchyNodeType.SUB_SECTION, HierarchyNodeType.SUB_RULE, HierarchyNodeType.CLAUSE):
                full_label = label_token
            else:
                full_label = f"{node_type.value.title()} {label_token}".strip()

            # Trim stack to parent depth
            while stack and stack[-1][0] >= depth:
                stack.pop()

            parent_path = _breadcrumb()
            stack.append((depth, full_label))

            nodes.append(
                HierarchyNode(
                    node_type=node_type,
                    label=full_label,
                    title=title_text or None,
                    page_start=page_num,
                    depth=depth,
                    parent_path=parent_path,
                )
            )

    # Assign page_end: each node ends where the next sibling/ancestor starts
    for i, node in enumerate(nodes):
        if i + 1 < len(nodes):
            node.page_end = nodes[i + 1].page_start
        else:
            node.page_end = current_page

    return nodes

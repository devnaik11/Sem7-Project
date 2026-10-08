"""Build the comprehensive VeLiS-RAG Architecture and Implementation Plan Word document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

DOCS_DIR = Path("docs")
DIAGRAMS_DIR = DOCS_DIR / "diagrams"
OUTPUT_PATH = DOCS_DIR / "VeLiS_RAG_Architecture_and_Implementation_Plan.docx"

# Color Palette (Dark-blue professional academic palette)
HEX_PRIMARY = "1E3A8A"  # Deep Blue
HEX_SECONDARY = "2563EB"  # Royal Blue
HEX_DARK = "0F172A"  # Dark Slate Body
HEX_MUTED = "475569"  # Muted Grey Subtitles
HEX_LIGHT_BG = "F8FAFC"  # Table alternate row
HEX_HEADER_BG = "1E3A8A"  # Table header background
HEX_BORDER = "CBD5E1"  # Table borders
HEX_CALLOUT_BG = "F1F5F9"  # Callout background
HEX_CALLOUT_BORDER = "1E3A8A"  # Callout border

COLOR_PRIMARY = RGBColor(30, 58, 138)
COLOR_SECONDARY = RGBColor(37, 99, 235)
COLOR_DARK = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(71, 85, 105)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell padding in twips (1/20 of a pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, hex_color):
    """Set XML shading for a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_border(cell, **kwargs):
    """Set cell borders (top, bottom, left, right)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f"<w:tcBorders {nsdecls('w')}/>")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge_data = kwargs.get(edge)
        if edge_data:
            val, sz, color = edge_data
            border = parse_xml(f'<w:{edge} {nsdecls("w")} w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>')
            tcBorders.append(border)
    tcPr.append(tcBorders)


def add_callout(doc, text, title=""):
    """Add a styled callout box with a left border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)

    cell = tbl.cell(0, 0)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    set_cell_border(
        cell,
        left=("single", "24", HEX_CALLOUT_BORDER),
        top=("none", "0", "auto"),
        bottom=("none", "0", "auto"),
        right=("none", "0", "auto"),
    )

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if title:
        run_t = p.add_run(f"{title}\n")
        run_t.bold = True
        run_t.font.name = "Calibri"
        run_t.font.size = Pt(10)
        run_t.font.color.rgb = COLOR_PRIMARY
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(9.5)
    run.font.color.rgb = COLOR_DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_custom_heading(doc, text, level):
    """Add styled headings."""
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.bold = True

    if level == 1:
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        run.font.size = Pt(16)
        run.font.color.rgb = COLOR_PRIMARY
        # Bottom accent border on Heading 1
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="{HEX_PRIMARY}"/></w:pBdr>'
        )
        p._p.get_or_add_pPr().append(pBdr)
    elif level == 2:
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        run.font.size = Pt(13)
        run.font.color.rgb = COLOR_SECONDARY
    elif level == 3:
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(2)
        run.font.size = Pt(11)
        run.font.color.rgb = COLOR_DARK
    return p


def add_body_paragraph(doc, text="", bold_prefix="", space_after=6):
    """Add styled body paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = COLOR_DARK
    if text:
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10.5)
        r.font.color.rgb = COLOR_DARK
    return p


def add_bullet(doc, text, bold_prefix=""):
    """Add a styled bullet list item."""
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10)
        r_pre.font.color.rgb = COLOR_DARK
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.color.rgb = COLOR_DARK
    return p


def build_table(doc, headers, data, col_widths=None):
    """Build a beautifully formatted academic table."""
    tbl = doc.add_table(rows=len(data) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Header Row
    hdr_cells = tbl.rows[0].cells
    hdr_trPr = tbl.rows[0]._tr.get_or_add_trPr()
    hdr_trPr.append(parse_xml(f"<w:tblHeader {nsdecls('w')}/>"))
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], HEX_HEADER_BG)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        set_cell_border(
            hdr_cells[i],
            bottom=("single", "12", HEX_PRIMARY),
            top=("single", "6", HEX_BORDER),
            left=("none", "0", "auto"),
            right=("none", "0", "auto"),
        )
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        for r in p.runs:
            r.bold = True
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    # Make Header Repeat across pages
    trPr = tbl.rows[0]._tr.get_or_add_trPr()
    trPr.append(parse_xml(f"<w:tblHeader {nsdecls('w')}/>"))

    # Data Rows
    for row_idx, row_data in enumerate(data):
        row_cells = tbl.rows[row_idx + 1].cells
        bg_color = HEX_LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].text = str(text)
            set_cell_background(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=90, bottom=90, left=140, right=140)
            set_cell_border(
                row_cells[col_idx],
                bottom=("single", "4", HEX_BORDER),
                top=("none", "0", "auto"),
                left=("none", "0", "auto"),
                right=("none", "0", "auto"),
            )
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.1
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(9)
                r.font.color.rgb = COLOR_DARK

    # Apply Column Widths and prevent awkward page row splits
    for row in tbl.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f"<w:cantSplit {nsdecls('w')}/>"))
        if col_widths:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return tbl


def insert_diagram(doc, image_path, caption, explanation=""):
    """Insert diagram with centered alignment, figure caption, and explanation box."""
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(4)
    run = p_img.add_run()
    run.add_picture(str(image_path), width=Inches(6.4))

    # Caption
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(4)
    r_cap = p_cap.add_run(caption)
    r_cap.bold = True
    r_cap.font.name = "Calibri"
    r_cap.font.size = Pt(9.5)
    r_cap.font.color.rgb = COLOR_PRIMARY

    # Explanation text if provided
    if explanation:
        add_callout(doc, explanation, title="Architecture Diagram Notes")


def build_document():
    """Main document creation routine."""
    doc = Document()

    # Page Setup (Standard A4 Margins: 1 inch / 72pt)
    for s in doc.sections:
        s.page_width = Inches(8.27)  # A4
        s.page_height = Inches(11.69)  # A4
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # -------------------------------------------------------------
    # 1. TITLE PAGE
    # -------------------------------------------------------------
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(72)
    p_pre.paragraph_format.space_after = Pt(12)
    r_pre = p_pre.add_run("RESEARCH PROJECT SPECIFICATION & ARCHITECTURAL BLUEPRINT")
    r_pre.font.name = "Calibri"
    r_pre.font.size = Pt(11)
    r_pre.bold = True
    r_pre.font.color.rgb = COLOR_SECONDARY

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(12)
    p_title.paragraph_format.line_spacing = 1.15
    r_title = p_title.add_run(
        "VeLiS-RAG: Verified Multilingual Legal Simplification with Adaptive Hybrid Retrieval for Indian Government Documents"
    )
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(24)
    r_title.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(36)
    r_sub = p_sub.add_run("Architecture and Implementation Blueprint | Version 1.0 (Phase 0 Audit Baseline)")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = COLOR_MUTED

    add_callout(
        doc,
        "Project Mission: Build a local-first research prototype that accepts citizen queries or official Indian legal/administrative texts and returns simple, structured, bilingual (English & Hindi) explanations strictly grounded in official sources. The system enforces cryptographic provenance, source trust stratification, atomic claim entailment verification, and legal invariant consistency.",
        title="EXECUTIVE RESEARCH CHARTER",
    )

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(48)
    p_meta.paragraph_format.space_after = Pt(4)
    r_m1 = p_meta.add_run("Author / Research Engineering Team: ")
    r_m1.bold = True
    r_m1.font.color.rgb = COLOR_DARK
    p_meta.add_run("VeLiS-RAG Core Research Project Group\n")
    r_m2 = p_meta.add_run("Document Status: ")
    r_m2.bold = True
    p_meta.add_run("Phase 0 Verified with Required Fixes | Phase 1-6 Planned\n")
    r_m3 = p_meta.add_run("Classification: ")
    r_m3.bold = True
    p_meta.add_run("Academic Research Specification & Engineering Implementation Plan\n")
    r_m4 = p_meta.add_run("Date of Record: ")
    r_m4.bold = True
    p_meta.add_run("September 2026")

    doc.add_page_break()

    # Configure Header & Footer for Subsequent Pages
    header = doc.sections[0].header
    p_hdr = header.paragraphs[0]
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_hdr = p_hdr.add_run("VeLiS-RAG: Architecture & Implementation Plan | Confidential Research Document")
    r_hdr.font.name = "Calibri"
    r_hdr.font.size = Pt(8)
    r_hdr.font.color.rgb = COLOR_MUTED

    footer = doc.sections[0].footer
    p_ftr = footer.paragraphs[0]
    p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_ftr = p_ftr.add_run("Informational Simplification System — Not Legal Advice — Official Sources Only Grounding")
    r_ftr.font.name = "Calibri"
    r_ftr.font.size = Pt(8)
    r_ftr.font.color.rgb = COLOR_MUTED

    # -------------------------------------------------------------
    # 2. EXECUTIVE SUMMARY
    # -------------------------------------------------------------
    add_custom_heading(doc, "1. Executive Summary", level=1)

    add_body_paragraph(
        doc,
        "Every year, millions of Indian citizens attempt to navigate complex government welfare programs, administrative entitlements, and statutory processes such as the Right to Information (RTI) Act. These administrative frameworks are published in dense statutory legalese, sprawling gazette notifications, and fragmented administrative circulars. Commercial large language model (LLM) interfaces, while proficient at general conversational summarization, suffer from well-documented legal failure modes: they hallucinate deadlines, fabricate application fees, blur jurisdictional boundaries between central and state governments, extrapolate outdated statutory versions, and fail to provide verifiable citations to enacted law.",
    )

    add_body_paragraph(
        doc,
        "The VeLiS-RAG (Verified Multilingual Legal Simplification with Adaptive Hybrid Retrieval) research initiative establishes an open-source, reproducible, local-first research prototype designed to resolve these critical failure modes. The system accepts a natural language citizen inquiry or an uploaded official document and synthesizes a structured, simplified, bilingual citizen brief (initially English and Hindi) that is strictly grounded in allowlisted government enactments.",
    )

    add_body_paragraph(doc, "Core Architectural Innovations:", bold_prefix="Key Research Contributions: ")
    add_bullet(
        doc,
        "Distinguishes primary statutory enactments (Tier A) from contextual advisories (Tier B) and untrusted citizen uploads (Tier C), legally barring non-authoritative sources from supporting operative claims.",
        bold_prefix="1. Source Trust Stratification: ",
    )
    add_bullet(
        doc,
        "Every chunk is bound to the SHA-256 digest of original downloaded file bytes and the SHA-256 digest of canonically normalized extracted text, guaranteeing anti-tampering auditability.",
        bold_prefix="2. Cryptographic Dual-Hash Provenance: ",
    )
    add_bullet(
        doc,
        "A calibrated natural language inference (NLI) classifier examines whether retrieved passages contain all requisite legal dimensions prior to text generation, triggering structured abstention when facts are absent.",
        bold_prefix="3. Epistemic Source-Sufficiency Gating: ",
    )
    add_bullet(
        doc,
        "Draft briefs are split into atomic propositions and individually verified against cited Tier A passages using NLI cross-encoders. Unsupported extrapolations are pruned or regenerated.",
        bold_prefix="4. Claim-Level Entailment Verification: ",
    )
    add_bullet(
        doc,
        "Statutory numbers, calendar deadlines, percentages, section IDs, and Commission for Scientific and Technical Terminology (CSTT) administrative authorities are extracted and verified bidirectionally across English and Hindi views.",
        bold_prefix="5. Structured Invariant Normalization Engine: ",
    )
    add_bullet(
        doc,
        "Strict prohibition against silently rewriting bilingual discrepancies; triggers a single bounded regeneration from Tier A evidence, failing over to abstention with source details and an audit log.",
        bold_prefix="6. Safe Recovery & Anti-Silent-Repair Policy: ",
    )

    # -------------------------------------------------------------
    # 3. RESEARCH SCOPE AND BOUNDARIES
    # -------------------------------------------------------------
    add_custom_heading(doc, "2. Research Scope and Boundaries", level=1)

    add_body_paragraph(
        doc,
        "To ensure scientific rigor and experimental control, the initial scope of the VeLiS-RAG research prototype is strictly bounded:",
    )

    add_bullet(
        doc,
        "Right to Information Act, 2005 & Central RTI Rules, 2012 (Central Union Jurisdiction).",
        bold_prefix="Central Administrative Procedures: ",
    )
    add_bullet(
        doc,
        "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) Operational Guidelines (Ministry of Agriculture and Farmers Welfare).",
        bold_prefix="National Welfare Scheme 1: ",
    )
    add_bullet(
        doc,
        "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY) Operational Criteria (National Health Authority).",
        bold_prefix="National Welfare Scheme 2: ",
    )

    add_custom_heading(doc, "2.1 Source Trust Taxonomy", level=2)
    add_body_paragraph(
        doc, "The system classifies all documentary material into three explicit, non-overlapping trust tiers:"
    )

    tier_data = [
        (
            "Tier A: Authoritative Legal Ground Truth",
            "Acts of Parliament, State Enactments, Gazetted Statutory Rules, Officially Notified Operational Guidelines.",
            "Mandatory evidence for all legally operative claims (eligibility, fees, deadlines, penalties, statutory rights, procedures).",
            "Must match approved canonical and redirect hosts; full dual-hash provenance required.",
        ),
        (
            "Tier B: Qualified Official Context",
            "Departmental circulars, office memoranda, administrative FAQs, draft guidelines, consultation papers.",
            "Permitted for administrative background, contextual explanation, and discovery.",
            "STRICTLY PROHIBITED from supporting legally operative claims. Must display prominent caveat.",
        ),
        (
            "Tier C: Untrusted Material",
            "User-uploaded PDFs, citizen letters, third-party portals, blogs, news commentary.",
            "Analyzed strictly as target subject matter to be audited against Tier A/B holdings.",
            "Never indexed as legal truth; completely untrusted by default; isolated in sandbox.",
        ),
    ]
    build_table(
        doc,
        ["Trust Tier", "Eligible Material", "Permitted Evidentiary Role", "Enforcement Constraints"],
        tier_data,
        [1.5, 1.8, 1.8, 1.4],
    )

    add_custom_heading(doc, "2.2 What the System Refuses or Abstains From", level=2)
    add_body_paragraph(
        doc,
        "VeLiS-RAG incorporates hard functional boundaries and will explicitly refuse or abstain from the following:",
    )
    add_bullet(
        doc,
        "The system does not assess case merits, predict judge rulings, or recommend litigation strategies. Every output displays a non-removable administrative informational disclaimer.",
        bold_prefix="Legal Advice Refusal: ",
    )
    add_bullet(
        doc,
        "If a user query asks about a state rule or circular not in the verified corpus, the system halts generation and reports the exact missing regulatory dimension.",
        bold_prefix="Out-of-Scope / Missing Evidence Abstention: ",
    )
    add_bullet(
        doc,
        "If an uploaded document or query contains conflicting statutory versions, the system flags the temporal ambiguity rather than guessing applicability.",
        bold_prefix="Conflicting Circular Abstention: ",
    )
    add_bullet(
        doc,
        "The system refuses to process individual court dockets, FIR copies, or private citizen RTI dockets containing personal identifying data.",
        bold_prefix="Private Case & PII Refusal: ",
    )

    # -------------------------------------------------------------
    # 4. END-TO-END SYSTEM ARCHITECTURE
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "3. End-to-End System Architecture", level=1)

    add_body_paragraph(
        doc,
        "The VeLiS-RAG architecture couples hybrid retrieval with an epistemic verification pipeline that treats generative models as drafting engines bounded by deterministic safety gates. Figure 1 illustrates the end-to-end component flow and decision logic.",
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram1_end_to_end_architecture.png",
        "Figure 1: VeLiS-RAG End-to-End System Architecture & Decision Paths",
        "Diagram Notes: Figure 1 illustrates the six sequential stages from raw URL ingestion to verified bilingual brief delivery. Key decision diamonds highlight the four critical epistemic gates: (1) Allowlist Gate for host and path approval, (2) Source Sufficiency Gate preventing hallucination when evidence is incomplete, (3) Claim-Level Entailment Gate enforcing Tier A support for operative claims, and (4) Invariant Match Gate preventing bilingual divergence without silent repair.",
    )

    add_custom_heading(doc, "3.1 Core Decision Paths & Epistemic Gates", level=2)
    add_body_paragraph(doc, "The architecture guarantees that execution branches deterministically at four points:")
    add_bullet(
        doc,
        "If a source URL or its resolved redirect target is not in configs/source_allowlist.yaml, or if its document type is unapproved, ingestion terminates immediately with an alert log.",
        bold_prefix="Decision Path 1 (Approved vs Rejected Source): ",
    )
    add_bullet(
        doc,
        "If the calibrated NLI sufficiency classifier scores below threshold tau_suff, generation is bypassed and a structured abstention notice is emitted.",
        bold_prefix="Decision Path 2 (Sufficient vs Insufficient Evidence): ",
    )
    add_bullet(
        doc,
        "Every atomic claim in the draft brief must achieve an NLI entailment score >= tau_entail against its cited Tier A passage. Unsupported claims are pruned or trigger a single regeneration pass.",
        bold_prefix="Decision Path 3 (Verified vs Unsupported Claim): ",
    )
    add_bullet(
        doc,
        "If normalized numbers, deadlines, or authorities differ between English and Hindi, the system regenerates once from Tier A evidence. If the discrepancy persists, it abstains and logs an incident.",
        bold_prefix="Decision Path 4 (Matching vs Mismatching Invariants): ",
    )

    # -------------------------------------------------------------
    # 5. STEP-BY-STEP DATA FLOW
    # -------------------------------------------------------------
    add_custom_heading(doc, "4. Step-by-Step Data Flow", level=1)

    add_body_paragraph(
        doc,
        "Data traverses the VeLiS-RAG pipeline through 12 formal stages, each governed by input-output contracts, safety checks, and deterministic failure behaviors:",
    )

    stages = [
        (
            "1. Source Approval",
            "Candidate URL & Doc Type",
            "Check against configs/source_allowlist.yaml (canonical host, file host, path regex).",
            "Validated SourceRegistryEntry",
            "Reject wildcard hosts, unregistered domains, or disallowed document types.",
            "Drop source; emit security alert; halt ingestion.",
        ),
        (
            "2. Raw File Capture & Hashing",
            "Approved file download stream",
            "Download raw bytes directly; calculate SHA-256 before parsing.",
            "Original file on disk + raw_file_sha256",
            "Reject placeholder hashes, truncated bytes, or SSL handshake failures.",
            "Abort download; quarantine corrupted byte stream.",
        ),
        (
            "3. Metadata Catalog Recording",
            "Raw file + Provenance parameters",
            "Serialize to LegalDocumentMetadata schema; write to SQLite WAL catalog.",
            "ACID-committed catalog record",
            "Verify dual hashes are 64-char lowercase hex; check license basis.",
            "Database transaction rollback; reject record.",
        ),
        (
            "4. Legal Hierarchy Parsing",
            "Raw PDF / HTML bytes",
            "Structural parser extracts Chapter, Section, Sub-section, Rule, Clause hierarchies.",
            "Ordered list of PassageChunk objects",
            "Detect OCR character entropy; verify parent-child hierarchy integrity.",
            "Quarantine low-quality scans for dual-pass OCR review.",
        ),
        (
            "5. Hybrid Retrieval",
            "Citizen Query (EN/HI)",
            "Concurrent sparse BM25 query (Tantivy/Okapi) and dense embedding search (BGE-M3).",
            "Top-50 candidate passages",
            "Enforce query sanitization; apply temporal & jurisdiction pre-filters.",
            "Fall back to pure sparse search if dense index is unreachable.",
        ),
        (
            "6. Evidence Filtering & Fusion",
            "Top-50 candidates",
            "Reciprocal Rank Fusion (RRF, k=60); filter out Tier C; flag Tier B; rerank top-15.",
            "Top-N ranked Tier A/B passages",
            "Operative claims must be supported solely by Tier A evidence.",
            "Exclude Tier C completely; attach warning banner if Tier B used.",
        ),
        (
            "7. Structured Answer Planning",
            "Top-N evidence + Query",
            "Draft candidate brief outline: Direct Answer, Eligibility, Procedure, Invariant Table.",
            "Structured Brief Plan Schema",
            "Ensure all mandatory brief sections are mapped to retrieved passages.",
            "If plan cannot map core question, trigger early abstention.",
        ),
        (
            "8. Generation Synthesis",
            "Brief Plan + Evidence Text",
            "Local LLM (Qwen2.5-7B) synthesizes initial prose within strict XML data delimiters.",
            "Draft Citizen Brief text",
            "Isolate evidence within <evidence_data>; forbid system instruction overrides.",
            "Reject malformed JSON/markdown output; retry with constrained schema.",
        ),
        (
            "9. Claim Verification",
            "Draft Brief text + Citations",
            "Decompose into atomic claims; verify entailment against cited passage via NLI.",
            "VerificationResult audit object",
            "Verify 100% of operative claims are entailed exclusively by Tier A chunks.",
            "Prune unsupported claim; regenerate draft once from Tier A evidence.",
        ),
        (
            "10. Hindi Alignment",
            "Verified English Brief",
            "Synthesize Devanagari Hindi brief using CSTT standardized legal glossary dictionary.",
            "Paired Hindi Citizen Brief",
            "Ensure statutory terms match official Government of India terminology.",
            "Flag unmapped terminology; default to approved administrative term.",
        ),
        (
            "11. Invariant Validation",
            "English & Hindi Briefs",
            "Extract and normalize fees, days, hours, section IDs, and authority names.",
            "Bilingual Invariant Tuple Set",
            "Verify exact normalized value parity (INR, DURATION, SEC_ID, AUTH_ID).",
            "Regenerate once from Tier A; if still discrepant, abort and abstain.",
        ),
        (
            "12. Final Delivery & Audit",
            "Validated Bilingual Brief",
            "Format user brief with clickable citations, metadata provenance, and disclaimer.",
            "Final Citizen Brief + Audit Log",
            "Enforce presence of mandatory non-legal-advice disclaimer banner.",
            "Withhold output if disclaimer is missing; log audit incident.",
        ),
    ]

    for s_title, s_in, s_proc, s_out, s_chk, s_fail in stages:
        add_custom_heading(doc, s_title, level=2)
        s_data = [
            ("Input Data", s_in),
            ("Processing Logic", s_proc),
            ("Output Artifact", s_out),
            ("Safety Check", s_chk),
            ("Failure Behavior", s_fail),
        ]
        build_table(doc, ["Stage Attribute", "Specification Details"], s_data, [2.0, 4.5])

    # -------------------------------------------------------------
    # 6. TRUST AND PROVENANCE ARCHITECTURE
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "5. Trust and Provenance Architecture", level=1)

    add_body_paragraph(
        doc,
        "The trustworthiness of VeLiS-RAG rests on the principle that the system must never invent laws, circulars, or administrative authorities. Figure 2 details the cryptographic provenance chain and host whitelisting architecture.",
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram2_trust_and_provenance.png",
        "Figure 2: VeLiS-RAG Trust and Provenance Architecture",
        "Diagram Notes: Figure 2 details the three-tier trust separation, the reviewed host registry, and the dual-hash cryptographic verification mechanism. Notice that Tier B documents are explicitly quarantined from operative claims, and Tier C material is never indexed as legal truth.",
    )

    add_custom_heading(doc, "5.1 Canonical vs File-Delivery Host Separation", level=2)
    add_body_paragraph(
        doc,
        "Official Indian Government portals frequently separate public-facing portal interfaces from binary file distribution infrastructure. For example, a gazette notification listed on www.indiacode.nic.in may redirect to a binary file hosted on cdnbbsr.s3waas.gov.in (National Informatics Centre Secure S3 infrastructure).",
    )
    add_body_paragraph(
        doc,
        "To prevent malicious open-redirect attacks while supporting legitimate government delivery architectures, the VeLiS-RAG Source Registry records both canonical hosts and approved file-delivery hosts. Ingestion code validates both the initiating URL and the final resolved redirect URL against the registry. If a canonical page redirects to an unauthorized third-party CDN or commercial cloud bucket, the download is immediately rejected.",
    )

    add_custom_heading(doc, "5.2 Dual-Hash Mathematical Integrity", level=2)
    add_body_paragraph(doc, "To preserve evidentiary integrity across the pipeline:")
    add_bullet(
        doc,
        "Calculated directly over the raw byte sequence of the downloaded PDF or HTML file before any character decoding or text extraction occurs. This hash proves that the local cached file is an exact byte-for-byte replica of the official release.",
        bold_prefix="raw_file_sha256: ",
    )
    add_bullet(
        doc,
        "Calculated over the canonically normalized UTF-8 string (applying Unicode NFC normalization, BOM stripping, and canonical whitespace reduction). This hash binds database passage chunks directly to the extracted legal text, ensuring zero indexing corruption.",
        bold_prefix="extracted_text_sha256: ",
    )
    add_bullet(
        doc,
        "Runtime models strictly reject placeholder strings (such as 'PLACEHOLDER_HASH'). Only verified 64-character lowercase hexadecimal SHA-256 digests are accepted into production records.",
        bold_prefix="Runtime Placeholder Rejection: ",
    )

    # -------------------------------------------------------------
    # 7. VERIFICATION AND SAFETY ARCHITECTURE
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "6. Verification and Safety Architecture", level=1)

    add_body_paragraph(
        doc,
        "VeLiS-RAG enforces a strict separation between epistemic authority and instruction trust. While an official statute carries the highest legal authority for factual claims, it is never trusted as a source of system instructions. Figure 3 illustrates the verification and anti-prompt-injection architecture.",
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram3_verification_and_safety.png",
        "Figure 3: VeLiS-RAG Verification and Safety Architecture",
        "Diagram Notes: Figure 3 illustrates the multi-layered defense-in-depth architecture. Retrieved evidence passages are enclosed in strict XML data boundaries. Atomic claim entailment checks verify factual grounding, and the structured invariant engine prevents numerical or statutory drift across languages.",
    )

    add_custom_heading(doc, "6.1 Data-Only Prompt Injection Defense", level=2)
    add_body_paragraph(
        doc,
        "Prompt injection represents a critical security vector in legal RAG systems, either through adversarial user prompts or indirect prompt injection embedded within public circulars, gazette footnotes, or user-uploaded documents (Tier C).",
    )
    add_body_paragraph(
        doc,
        "VeLiS-RAG rejects the naive assumption that string sanitization or token stripping can neutralize prompt injection. Instead, it enforces structural defense-in-depth:",
    )
    add_bullet(
        doc,
        "The generator model operates under an immutable system prompt establishing that its sole role is administrative simplification within rigid schema constraints.",
        bold_prefix="Immutable System Instructions: ",
    )
    add_bullet(
        doc,
        "All retrieved evidence passages are enclosed within strict XML data tags: <evidence_data chunk_id='...'>...</evidence_data>. System instructions explicitly state that text inside evidence tags is untrusted data and must never be interpreted as operational directives.",
        bold_prefix="Structured Evidence Delimiters: ",
    )
    add_bullet(
        doc,
        "Output is constrained to deterministic Pydantic JSON schemas, preventing the model from emitting free-form hijacked control sequences.",
        bold_prefix="Schema-Constrained Generation: ",
    )

    add_custom_heading(doc, "6.2 Anti-Silent-Repair Policy", level=2)
    add_body_paragraph(
        doc,
        "In multilingual legal systems, translation drift is catastrophic: if an English brief correctly states an application fee of 'Rs. 10' but the Hindi translation accidentally states 'Rs. 100', a citizen may be disenfranchised.",
    )
    add_body_paragraph(
        doc,
        "VeLiS-RAG establishes a strict scientific policy: the system will never silently overwrite or repair an invariant mismatch to force an output. When a discrepancy between English and Hindi invariants is detected:",
    )
    add_bullet(
        doc,
        "The system triggers a single bounded regeneration from the verified Tier A passage.",
        bold_prefix="Step 1 (Bounded Regeneration): ",
    )
    add_bullet(
        doc,
        "If the bilingual discrepancy persists after one regeneration, the system halts, abstains from presenting the unaligned section, outputs the verified Tier A source citation, and writes an incident record to the audit catalog.",
        bold_prefix="Step 2 (Safe Abstention & Audit): ",
    )

    # -------------------------------------------------------------
    # 8. TECHNOLOGY STACK
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "7. Technology Stack", level=1)

    add_body_paragraph(
        doc,
        "To ensure scientific reproducibility, data privacy, and zero operational API costs, VeLiS-RAG is built as a local-first system. Table 2 delineates the Phase 2 baseline components versus planned future isolated ablations.",
    )

    stack_data = [
        (
            "API / Backend",
            "FastAPI (Python 3.11+) with Pydantic v2",
            "Litestar / AsyncIO",
            "Phase 2 Baseline",
            "High performance, async concurrency, strict runtime schema validation.",
        ),
        (
            "Keyword Search",
            "BM25Okapi (pure Python)",
            "Tantivy (Rust via tantivy-py)",
            "Phase 2 Baseline",
            "Zero native binary compile dependencies for robust local baseline.",
        ),
        (
            "Keyword Scale",
            "Tantivy (tantivy-py)",
            "Elasticsearch / OpenSearch",
            "Future Ablation",
            "Evaluates sub-millisecond indexing speedup over pure Python BM25.",
        ),
        (
            "Vector Store",
            "Qdrant (Local In-Process / Directory)",
            "Chroma / LanceDB / SQLite-vec",
            "Phase 2 Baseline",
            "Embedded directory mode; zero Docker required; fast SIMD HNSW vector search.",
        ),
        (
            "Embedding Model",
            "BAAI/bge-m3 (Dense 1024-dim)",
            "multilingual-e5-large / IndicBERT",
            "Phase 2 Baseline",
            "Native support for 100+ languages including Hindi; 8,192 token context window.",
        ),
        (
            "Reranker",
            "bge-reranker-v2-m3",
            "Cross-Encoder MiniLM / Cohere Cloud",
            "Future Ablation",
            "Evaluates precision boost of cross-encoder reranking over raw RRF fusion.",
        ),
        (
            "Generator Model",
            "Qwen2.5-7B-Instruct (4-bit GGUF)",
            "Llama-3.1-8B / Mistral-7B",
            "Phase 2 Baseline",
            "State-of-the-art open multilingual instruction following; native Hindi Devanagari.",
        ),
        (
            "Catalog & Provenance",
            "SQLite 3 (WAL Mode)",
            "DuckDB / PostgreSQL",
            "Phase 2 Baseline",
            "Serverless ACID persistence; handles metadata, dual hashes, and audit logs.",
        ),
        (
            "Testing & Quality",
            "Pytest, Hypothesis, MyPy, Ruff",
            "Unittest, Robot Framework",
            "Phase 0 Implemented",
            "Property-based invariant fuzzing, strict static typing, fast linting/formatting.",
        ),
        (
            "Routing / Graph",
            "Adaptive Complexity Router / KG",
            "Static Hybrid Fusion",
            "Future Ablation",
            "Evaluates multi-hop statutory decomposition against single-shot retrieval.",
        ),
    ]
    build_table(
        doc,
        ["Subsystem Layer", "Selected Component", "Evaluated Alternatives", "Lifecycle Status", "Selection Rationale"],
        stack_data,
        [1.2, 1.8, 1.4, 1.0, 1.1],
    )

    # -------------------------------------------------------------
    # 9. PHASED IMPLEMENTATION ROADMAP
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "8. Phased Implementation Roadmap", level=1)

    add_body_paragraph(
        doc,
        "VeLiS-RAG follows a strict phased research engineering lifecycle. Figure 4 illustrates the phased roadmap and the corresponding multi-tier testing pyramid.",
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram4_roadmap_pyramid.png",
        "Figure 4: VeLiS-RAG Phased Implementation Roadmap & Testing Pyramid",
        "Diagram Notes: Figure 4 presents the sequential progression from Phase 0 to Phase 6 alongside the five-tier testing pyramid. Notice that Phase 0 is verified with required fixes, while Phase 1 onwards remains planned.",
    )

    doc.add_page_break()
    add_custom_heading(doc, "8.1 Detailed Phase Deliverables & Stop Conditions", level=2)

    roadmap_data = [
        (
            "Phase 0: Foundations & Governance",
            "Repository structure, Pydantic domain models, source allowlist registry, dual-hash utilities, invariant engine.",
            "Schema validation, dual-hash vectors, Tier B operative prohibition, redirect checks.",
            "Full lint clean, MyPy strict pass, 35/35 tests passing (92% coverage).",
            "Failure of schema validation or reliance on cloud APIs.",
        ),
        (
            "Phase 1: Curated Corpus Ingestion",
            "Ingestion pipeline for RTI Act 2005, PM-KISAN, and PM-JAY. Structural hierarchy parser and SQLite catalog.",
            "Dual-hash verification on downloaded bytes, structural hierarchy chunking tests.",
            "100% of chunks carry verified raw & normalized hashes and Tier A/B tags.",
            "Broken legal section hierarchy or unverified redirect host in > 0% of chunks.",
        ),
        (
            "Phase 2: Baseline Hybrid Retrieval",
            "BM25Okapi + Qdrant embedded collection (BGE-M3). Reciprocal Rank Fusion (RRF). Reranking ablation.",
            "Top-K retrieval recall, latency benchmarks, metadata pre-filtering tests.",
            "Dev set Retrieval Recall@5 >= 88.0%; retrieval latency < 800ms.",
            "Recall@5 < 80.0% or inclusion of Tier C in evidence pool.",
        ),
        (
            "Phase 3: Sufficiency & Claim Entailment",
            "Source sufficiency classifier, plan-then-generate brief orchestrator, atomic claim NLI verifier, abstention module.",
            "Sufficiency threshold calibration, unanswerable query probe tests, claim entailment tests.",
            "Dev set: 100% abstention on unanswerable queries; unsupported claims < 2.0%.",
            "Single hallucinated statutory fee or non-existent section reference in test suite.",
        ),
        (
            "Phase 4: Multilingual & Invariant Engine",
            "Hindi generation pipeline via CSTT legal glossary. Structured Invariant Engine integration. Invariant comparison.",
            "Property-based invariant fuzzing, cross-lingual entity parity tests.",
            "100% invariant parity between English and Hindi briefs on release tests.",
            "Any normalized fee, deadline, or authority mismatch between EN and HI views.",
        ),
        (
            "Phase 5: Held-Out Research Evaluation",
            "Evaluation over hidden held-out benchmark (N=150-300). Bootstrap 95% CIs. Inter-annotator agreement (kappa, alpha).",
            "End-to-end benchmark execution, temporal split tests, jurisdiction split tests.",
            "Complete benchmark report generated reproducibly via single CLI command.",
            "Inability to run benchmark deterministically without human intervention.",
        ),
        (
            "Phase 6: Researcher Workbench",
            "Local FastAPI backend + lightweight inspection console. Visual citation highlighting, RRF and NLI drawer.",
            "Headless browser tests, local offline verification, export integrity tests.",
            "Console functions completely offline; zero external network egress.",
            "UI executes without prominent legal disclaimer or exposes host file paths.",
        ),
    ]
    build_table(
        doc,
        [
            "Phase Milestone",
            "Scope & Deliverables",
            "Automated Test Suite",
            "Acceptance Exit Criteria",
            "Hard Stop Conditions",
        ],
        roadmap_data,
        [1.3, 1.8, 1.4, 1.0, 1.0],
    )

    # -------------------------------------------------------------
    # 10. TEST AND EVALUATION STRATEGY
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "9. Test and Evaluation Strategy", level=1)

    add_body_paragraph(
        doc,
        "The VeLiS-RAG testing strategy enforces deterministic guarantees at the lower tiers while evaluating statistical research metrics across a hidden held-out benchmark.",
    )

    test_matrix = [
        (
            "Unit Tests",
            "Pydantic models, dual-hash utilities, text normalizers, invariant regexes.",
            "Deterministic Pytest assertions on synthetic fixtures.",
            "100% pass rate; zero schema regressions.",
        ),
        (
            "Integration Tests",
            "End-to-end flow from Query -> Router -> Retrieval -> Brief Synthesis.",
            "Mocked retrieval & LLM pipeline assertions.",
            "Valid BilingualBrief schema output without exceptions.",
        ),
        (
            "Source / Provenance Tests",
            "Canonical host matching, redirect validation, placeholder hash rejection.",
            "Host allowlist and dual-hash verification tests.",
            "Rejection of unapproved hosts, paths, and placeholders.",
        ),
        (
            "Retrieval Benchmarks",
            "Hybrid BM25 + Qdrant BGE-M3 retrieval against gold passage mappings.",
            "Automated rank-order evaluation on 50 dev queries.",
            "Recall@5 >= 88.0%; MRR@5 >= 0.82.",
        ),
        (
            "Hallucination & Citation Tests",
            "Atomic claim entailment checking against cited Tier A passages.",
            "NLI cross-encoder scoring on claim propositions.",
            "Observed unsupported-claim rate <= 2.0% [95% CI].",
        ),
        (
            "Adversarial Injection Tests",
            "Direct prompt jailbreaks, indirect injection via gazette text/footnotes.",
            "Red-team adversarial input test suite.",
            "Zero prompt overrides; evidence treated as data only.",
        ),
        (
            "Multilingual Invariant Tests",
            "Cross-lingual parity for fees, durations, sections, and authorities.",
            "Hypothesis property-based tests comparing EN and HI.",
            "Zero observed invariant drift on release test suite.",
        ),
        (
            "Regression Tests",
            "Frozen 30-query regression test suite executed before release commits.",
            "Automated metric regression assertions.",
            "Zero regression in faithfulness, recall, or abstention.",
        ),
        (
            "Human Legal Review",
            "Qualitative evaluation of 10 sampled briefs by legal domain researchers.",
            "Human review protocol for statutory fidelity and clarity.",
            "100% adherence to jurisdictional bounds and disclaimers.",
        ),
    ]
    build_table(
        doc,
        ["Test Category", "Target Subsystem", "Evaluation Methodology", "Target Pass Criteria"],
        test_matrix,
        [1.5, 1.8, 1.8, 1.4],
    )

    add_custom_heading(doc, "9.1 Planned Research Evaluation Metrics", level=2)

    metrics_data = [
        (
            "Retrieval Recall@5",
            "Proportion of target gold passages retrieved within top-5 candidates.",
            ">= 88.0% [84.5%, 91.2%]",
            "Automated rank evaluation",
        ),
        (
            "Retrieval MRR@5",
            "Mean Reciprocal Rank of the first relevant legal passage.",
            ">= 0.82 [0.77, 0.86]",
            "Automated rank evaluation",
        ),
        (
            "Unsupported-Claim Rate",
            "Proportion of generated atomic claims not entailed by cited Tier A chunks.",
            "<= 2.0% [0.5%, 3.5%]",
            "NLI cross-encoder entailment",
        ),
        (
            "Citation Precision",
            "Proportion of cited passages that directly entail the associated claim.",
            ">= 92.0% [88.0%, 95.5%]",
            "Claim-to-passage audit",
        ),
        (
            "Citation Recall",
            "Proportion of legally operative assertions that carry an exact citation.",
            ">= 85.0% [80.5%, 89.0%]",
            "Operative claim coverage",
        ),
        (
            "Abstention F1-Score",
            "Harmonic mean of precision and recall on unanswerable/out-of-scope queries.",
            ">= 90.0% [85.0%, 94.2%]",
            "Unanswerable query probe set",
        ),
        (
            "Invariant Parity Rate",
            "Proportion of briefs where EN and HI normalized invariant sets match identically.",
            "100.0% on release tests",
            "Deterministic invariant comparison",
        ),
        (
            "Query Latency (p95)",
            "95th percentile query execution time on local workstation hardware.",
            "< 8.0s (CPU) / < 4.5s (GPU)",
            "Benchmarked telemetry",
        ),
    ]
    build_table(
        doc,
        [
            "Evaluation Metric",
            "Metric Definition & Research Purpose",
            "Target Objective [95% CI]",
            "Measurement Method",
        ],
        metrics_data,
        [1.5, 2.3, 1.4, 1.3],
    )

    # -------------------------------------------------------------
    # 11. CURRENT PHASE 0 STATUS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "10. Current Phase 0 Status & Audit Findings", level=1)

    add_body_paragraph(
        doc,
        "Phase 0 (Foundations, Governance, Schemas, and Test Suite) was implemented and subjected to an exhaustive, read-only verification audit on September 18, 2026. The empirical findings are recorded below:",
    )

    add_bullet(
        doc,
        "All 35 automated tests in the Pytest suite execute cleanly in 1.05 seconds with zero failures.",
        bold_prefix="Automated Test Suite: ",
    )
    add_bullet(
        doc,
        "The test suite achieves 92% statement coverage across all core modules (722 statements, 56 missed).",
        bold_prefix="Test Coverage: ",
    )
    add_bullet(
        doc,
        "Static type checking via MyPy in strict mode passes with zero errors across all 21 source files.",
        bold_prefix="Static Type Checking: ",
    )
    add_bullet(doc, "All 27 project files comply with project formatting standards.", bold_prefix="Code Formatting: ")
    add_bullet(
        doc,
        "An unused import (DEVANAGARI_DIGITS in tests/test_invariants.py:11) causes 'ruff check .' to exit with code 1. This must be deleted before Phase 1.",
        bold_prefix="Finding 1 (Linter Issue): ",
    )
    add_bullet(
        doc,
        "While zero ML model weights or government documents were downloaded, Python development dependencies were downloaded from PyPI during pip install. Earlier walkthrough wording claiming 'zero external network downloads' has been formally corrected.",
        bold_prefix="Finding 2 (Network Dependency Download): ",
    )
    add_bullet(
        doc,
        "Zero real government documents, zero ML model weights (LLM, embeddings, reranker), zero vector databases, and zero cloud APIs have been downloaded or initialized.",
        bold_prefix="Finding 3 (Zero Premature Resources): ",
    )
    add_bullet(
        doc,
        "Git repository is initialized, but files remain untracked (no initial commit). A deterministic commit SHA must be recorded.",
        bold_prefix="Finding 4 (Git State): ",
    )
    add_bullet(
        doc,
        "Dependencies in pyproject.toml use bounded semver ranges rather than exact pinned lockfiles. A requirements.lock file must be generated.",
        bold_prefix="Finding 5 (Lockfile): ",
    )

    add_callout(
        doc,
        "Official Phase 0 Audit Conclusion: VERIFIED WITH REQUIRED FIXES\n"
        "All domain models, schemas, trust rules, provenance hashes, redirect validators, and invariant normalizers are fully verified. Three trivial maintenance actions are required before Phase 1: (1) remove unused import in test_invariants.py, (2) create initial Git commit, and (3) generate exact requirements.lock freeze file.",
        title="PHASE 0 AUDIT OUTCOME",
    )

    # -------------------------------------------------------------
    # 12. RISKS AND MITIGATIONS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "11. Comprehensive Risk Register & Mitigations", level=1)

    add_body_paragraph(
        doc,
        "Table 4 delineates the ten primary technical and regulatory risks identified for the VeLiS-RAG research prototype, alongside their evaluated severity and mitigation strategies.",
    )

    risks_data = [
        (
            "R-01: Outdated / Superseded Law",
            "High",
            "Critical",
            "Temporal metadata tagging (effective_date, version); reranker filters for latest enacted rules; prominent version warnings.",
            "Automated regression tests checking 2019 RTI amendment rules supersede 2005 rules.",
        ),
        (
            "R-02: Source Authority Errors",
            "High",
            "Critical",
            "Strict reviewed host registry; separate canonical and file delivery hosts; reject unauthorized domains.",
            "Automated URL and redirect host validation tests against configs/source_allowlist.yaml.",
        ),
        (
            "R-03: Gazette OCR Corruption",
            "Medium",
            "High",
            "Ingest only digitally native PDFs/HTML; dual-pass OCR with character entropy checks for legacy circulars.",
            "Character entropy check; automatic quarantine of chunks below word-density thresholds.",
        ),
        (
            "R-04: Indirect Prompt Injection",
            "High",
            "Critical",
            "Evidence treated strictly as data enclosed in <evidence_data>; immutable system instructions; JSON schemas.",
            "Adversarial test suite simulating prompt injection embedded in queries and PDF footnotes.",
        ),
        (
            "R-05: Retrieval Misses",
            "High",
            "Medium",
            "Hybrid BM25 + dense BGE-M3 retrieval; CSTT administrative synonym expansion; adaptive query routing.",
            "Retrieval Recall@5 evaluation over curated probe set of colloquial citizen inquiries.",
        ),
        (
            "R-06: Unsupported Claims",
            "High",
            "Critical",
            "Atomic proposition decomposition; strict NLI entailment gate; automatic pruning of unverified claims.",
            "Observed unsupported-claim rate reporting with 95% bootstrap confidence intervals.",
        ),
        (
            "R-07: Hindi Translation Drift",
            "Medium",
            "High",
            "CSTT standardized bilingual legal glossary; mandatory mapping of statutory administrative titles.",
            "Automated entity consistency check verifying Hindi terms match approved glossary.",
        ),
        (
            "R-08: Invariant Discrepancies",
            "Medium",
            "Critical",
            "Structured Invariant Normalization Engine; single regen from Tier A; safe abstention on mismatch.",
            "Bilingual invariant parity assertions; zero tolerance for observed numeric/date errors.",
        ),
        (
            "R-09: Licensing Uncertainty",
            "Low",
            "High",
            "Section 52(1)(q) Indian Copyright Act 1957 basis; source-by-source metadata; pre-publication review checkpoint.",
            "Formal pre-publication compliance review before releasing any corpus, dataset, or model.",
        ),
        (
            "R-10: Hardware Limitations",
            "Medium",
            "Medium",
            "Local 4-bit quantization (Qwen2.5-7B Q4_K_M); disk-based embedding cache; CPU-fallback support.",
            "Continuous telemetry tracking p50/p95 latency and peak RAM/VRAM footprint.",
        ),
    ]
    build_table(
        doc,
        ["Risk ID & Description", "Likelihood", "Severity", "Mitigation Strategy", "Audit / Detection Mechanism"],
        risks_data,
        [1.5, 0.9, 0.9, 1.8, 1.4],
    )

    # -------------------------------------------------------------
    # 13. CONCLUSION AND IMMEDIATE NEXT STEPS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "12. Conclusion and Immediate Next Steps", level=1)

    add_body_paragraph(
        doc,
        "The VeLiS-RAG project has established an exceptionally rigorous, scientifically grounded foundation in Phase 0. By combining cryptographic dual-hash provenance, strict source trust stratification, data-only prompt injection boundaries, claim-level NLI entailment, and bilingual invariant consistency, the system provides a credible, verifiable alternative to commercial black-box summarization engines.",
    )

    add_body_paragraph(doc, "The immediate technical actions required before initiating Phase 1 are strictly bounded:")
    add_bullet(
        doc,
        "Delete line 11 (DEVANAGARI_DIGITS) from tests/test_invariants.py so that 'ruff check .' exits with code 0.",
        bold_prefix="Action 1: Fix Phase 0 Linter Regression: ",
    )
    add_bullet(
        doc,
        "Execute 'git add .' and 'git commit -m \"chore: Phase 0 verified baseline\"' to establish a permanent Git commit SHA.",
        bold_prefix="Action 2: Record Initial Git Commit: ",
    )
    add_bullet(
        doc,
        "Execute 'pip freeze > requirements.lock' to create an exact, reproducible environment snapshot.",
        bold_prefix="Action 3: Generate Dependency Lockfile: ",
    )
    add_bullet(
        doc,
        "Confirm approval of the reviewed allowlist registry (configs/source_allowlist.yaml) for India Code, RTI Portal, PM-KISAN, and PM-JAY.",
        bold_prefix="Action 4: Formal Allowlist Approval: ",
    )
    add_bullet(
        doc,
        "Phase 1 (Curated Official Corpus Ingestion) will proceed only after explicit project lead authorization.",
        bold_prefix="Action 5: Phase 1 Authorization: ",
    )

    doc.save(OUTPUT_PATH)
    print(f"Document successfully created at: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_document()

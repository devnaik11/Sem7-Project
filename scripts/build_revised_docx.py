"""Build the revised VeLiS-RAG Architecture and Implementation Plan Word document.

This script implements the revised document specification:
- Objective, measured academic prose suitable for a final-year research proposal
- Removal of promotional hyperbole and overused terms (strict, critical, guarantees, etc.)
- Replacement of absolute claims with testable, evidence-based formulations
- Clear distinction between Phase 0 (implemented/verified) and Phases 1-6 (planned work)
- Inclusion of all 5 required author placeholders:
  1. [Author’s project motivation]
  2. [Local hardware configuration]
  3. [Supervisor feedback]
  4. [Observed Phase 1 results]
  5. [Author’s implementation decision and reason]
- Full academic citations and References section
- Optimized layout preventing orphaned callouts, split diagram notes, or blank pages
"""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

DOCS_DIR = Path("docs")
DIAGRAMS_DIR = DOCS_DIR / "diagrams"
OUTPUT_PATH = DOCS_DIR / "VeLiS_RAG_Architecture_and_Implementation_Plan_Revised.docx"

# Professional academic color palette
HEX_PRIMARY = "1E3A8A"  # Deep Navy
HEX_SECONDARY = "2563EB"  # Slate Blue
HEX_DARK = "0F172A"  # Dark Slate Body
HEX_MUTED = "475569"  # Muted Grey
HEX_LIGHT_BG = "F8FAFC"  # Table alternate row
HEX_HEADER_BG = "1E3A8A"  # Table header background
HEX_BORDER = "CBD5E1"  # Table borders
HEX_CALLOUT_BG = "F1F5F9"  # Callout background
HEX_CALLOUT_BORDER = "1E3A8A"  # Callout border
HEX_PLACEHOLDER_BG = "FEF3C7"  # Light Amber for placeholders
HEX_PLACEHOLDER_BORDER = "D97706"  # Dark Amber

COLOR_PRIMARY = RGBColor(30, 58, 138)
COLOR_SECONDARY = RGBColor(37, 99, 235)
COLOR_DARK = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(71, 85, 105)
COLOR_PLACEHOLDER = RGBColor(180, 83, 9)


def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
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


def add_callout(doc, text, title="", space_after=4):
    """Add a styled callout box with a left accent border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.27)

    cell = tbl.cell(0, 0)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=90, bottom=90, left=140, right=140)
    set_cell_border(
        cell,
        left=("single", "20", HEX_CALLOUT_BORDER),
        top=("none", "0", "auto"),
        bottom=("none", "0", "auto"),
        right=("none", "0", "auto"),
    )

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.12
    if title:
        run_t = p.add_run(f"{title}\n")
        run_t.bold = True
        run_t.font.name = "Calibri"
        run_t.font.size = Pt(9.5)
        run_t.font.color.rgb = COLOR_PRIMARY
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(9)
    run.font.color.rgb = COLOR_DARK

    # Empty paragraph spacer with tightly controlled space
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(space_after)


def add_placeholder_box(doc, placeholder_tag, guidance_text):
    """Add a prominent author-placeholder box to solicit truthful project-specific input."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.27)

    cell = tbl.cell(0, 0)
    set_cell_background(cell, HEX_PLACEHOLDER_BG)
    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    set_cell_border(
        cell,
        left=("single", "24", HEX_PLACEHOLDER_BORDER),
        top=("single", "4", HEX_PLACEHOLDER_BORDER),
        bottom=("single", "4", HEX_PLACEHOLDER_BORDER),
        right=("single", "4", HEX_PLACEHOLDER_BORDER),
    )

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15

    r_tag = p.add_run(f"{placeholder_tag}\n")
    r_tag.bold = True
    r_tag.font.name = "Calibri"
    r_tag.font.size = Pt(10)
    r_tag.font.color.rgb = COLOR_PLACEHOLDER

    r_guide = p.add_run(f"Author Note: {guidance_text}")
    r_guide.italic = True
    r_guide.font.name = "Calibri"
    r_guide.font.size = Pt(9)
    r_guide.font.color.rgb = COLOR_DARK

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(4)


def add_custom_heading(doc, text, level):
    """Add styled headings with consistent hierarchy and spacing."""
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.bold = True

    if level == 1:
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        run.font.size = Pt(15)
        run.font.color.rgb = COLOR_PRIMARY
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="8" w:space="3" w:color="{HEX_PRIMARY}"/></w:pBdr>'
        )
        p._p.get_or_add_pPr().append(pBdr)
    elif level == 2:
        p.paragraph_format.space_before = Pt(11)
        p.paragraph_format.space_after = Pt(3)
        run.font.size = Pt(12)
        run.font.color.rgb = COLOR_SECONDARY
    elif level == 3:
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_DARK
    return p


def add_body_paragraph(doc, text="", bold_prefix="", space_after=5):
    """Add styled body paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10)
        r_pre.font.color.rgb = COLOR_DARK
    if text:
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_DARK
    return p


def add_bullet(doc, text, bold_prefix="", space_after=2):
    """Add a styled bullet list item."""
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.12
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(9.5)
        r_pre.font.color.rgb = COLOR_DARK
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(9.5)
    r.font.color.rgb = COLOR_DARK
    return p


def build_table(doc, headers, data, col_widths=None, space_after=4):
    """Build a formatted table fitting printable area (6.27 inches total width)."""
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
        set_cell_margins(hdr_cells[i], top=70, bottom=70, left=100, right=100)
        set_cell_border(
            hdr_cells[i],
            bottom=("single", "10", HEX_PRIMARY),
            top=("single", "4", HEX_BORDER),
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
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for row_idx, row_data in enumerate(data):
        row_cells = tbl.rows[row_idx + 1].cells
        bg_color = HEX_LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].text = str(text)
            set_cell_background(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=60, bottom=60, left=100, right=100)
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
                r.font.size = Pt(8.5)
                r.font.color.rgb = COLOR_DARK

    # Column widths & cantSplit
    for row in tbl.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f"<w:cantSplit {nsdecls('w')}/>"))
        if col_widths:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(space_after)
    return tbl


def insert_diagram(doc, image_path, caption, explanation="", width_in=5.75):
    """Insert diagram with balanced scaling and figure notes on the same page."""
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(3)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(str(image_path), width=Inches(width_in))

    # Caption
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(2)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(caption)
    r_cap.bold = True
    r_cap.font.name = "Calibri"
    r_cap.font.size = Pt(9)
    r_cap.font.color.rgb = COLOR_PRIMARY

    # Explanatory Notes formatted as clean figure notes directly below caption
    if explanation:
        p_note = doc.add_paragraph()
        p_note.paragraph_format.space_before = Pt(1)
        p_note.paragraph_format.space_after = Pt(4)
        p_note.paragraph_format.line_spacing = 1.1
        r_pre = p_note.add_run("Figure Note: ")
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(8.5)
        r_pre.font.color.rgb = COLOR_MUTED

        r_text = p_note.add_run(explanation)
        r_text.font.name = "Calibri"
        r_text.font.size = Pt(8.5)
        r_text.font.color.rgb = COLOR_MUTED


def build_revised_document():
    """Main document assembly routine with revised academic prose and complete layout polish."""
    doc = Document()

    # A4 Page Setup with 1-inch margins (Printable width: 8.27 - 2.0 = 6.27 inches)
    for s in doc.sections:
        s.page_width = Inches(8.27)
        s.page_height = Inches(11.69)
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # -------------------------------------------------------------
    # 1. TITLE PAGE
    # -------------------------------------------------------------
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(48)
    p_pre.paragraph_format.space_after = Pt(10)
    r_pre = p_pre.add_run("ACADEMIC RESEARCH PROJECT PROPOSAL & ARCHITECTURAL SPECIFICATION")
    r_pre.font.name = "Calibri"
    r_pre.font.size = Pt(10.5)
    r_pre.bold = True
    r_pre.font.color.rgb = COLOR_SECONDARY

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(10)
    p_title.paragraph_format.line_spacing = 1.15
    r_title = p_title.add_run(
        "VeLiS-RAG: Verified Multilingual Legal Simplification with Adaptive Hybrid Retrieval for Indian Government Documents"
    )
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(24)
    r_sub = p_sub.add_run(
        "System Architecture, Verification Framework, and Phased Implementation Plan | Phase 0 Baseline"
    )
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = COLOR_MUTED

    add_callout(
        doc,
        "Project Objective: Investigate and construct a local-first research prototype to help citizens understand official Indian administrative and statutory documents. Given a natural language query or an administrative text, the system produces structured, simplified bilingual (English and Hindi) summaries grounded strictly in verified public enactments. The design incorporates source trust stratification to prevent non-statutory circulars from overriding formal legislation, dual-hash cryptographic provenance to track source text down to individual bytes, an NLI-based sufficiency check to stop generation when required facts are missing, atomic claim entailment to prune unsupported statements, and cross-lingual checks to keep key numbers and deadlines consistent across both languages.",
        title="RESEARCH PROJECT SUMMARY",
        space_after=8,
    )

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(28)
    p_meta.paragraph_format.space_after = Pt(3)
    p_meta.paragraph_format.line_spacing = 1.2

    metadata_entries = [
        ("Author / Investigator: ", "VeLiS-RAG Research Project Group"),
        ("Academic Context: ", "Final-Year B.Tech / M.Tech Research Project Proposal"),
        ("Implementation Status: ", "Phase 0 Verified (with required maintenance actions) | Phases 1-6 Planned"),
        ("Document Classification: ", "Technical Architecture & Empirical Evaluation Plan"),
        ("Date of Record: ", "September 2026"),
    ]
    for label, val in metadata_entries:
        r_lbl = p_meta.add_run(label)
        r_lbl.bold = True
        r_lbl.font.size = Pt(10)
        r_lbl.font.color.rgb = COLOR_DARK
        r_v = p_meta.add_run(f"{val}\n")
        r_v.font.size = Pt(10)
        r_v.font.color.rgb = COLOR_DARK

    doc.add_page_break()

    # Configure Header & Footer for Subsequent Pages
    header = doc.sections[0].header
    p_hdr = header.paragraphs[0]
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_hdr = p_hdr.add_run("VeLiS-RAG: Architecture & Implementation Plan | Research Document")
    r_hdr.font.name = "Calibri"
    r_hdr.font.size = Pt(8)
    r_hdr.font.color.rgb = COLOR_MUTED

    footer = doc.sections[0].footer
    p_ftr = footer.paragraphs[0]
    p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Clean standard dash without character corruption
    r_ftr = p_ftr.add_run("Informational Simplification Prototype - Not Legal Advice - Grounded in Official Sources")
    r_ftr.font.name = "Calibri"
    r_ftr.font.size = Pt(8)
    r_ftr.font.color.rgb = COLOR_MUTED

    # -------------------------------------------------------------
    # 2. EXECUTIVE SUMMARY
    # -------------------------------------------------------------
    add_custom_heading(doc, "1. Executive Summary", level=1)

    add_body_paragraph(
        doc,
        "Citizens in India frequently struggle to understand statutory entitlements, welfare benefits, and administrative procedures. Crucial public schemes—such as the Right to Information (RTI) Act, 2005, the Pradhan Mantri Kisan Samman Nidhi (PM-KISAN), and the Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY)—are documented across dense statutory enactments, gazette notifications, and departmental circulars. Reading through these materials requires parsing complex legal phrasing, reconciling conflicting amendments, and identifying which specific rules apply to a given situation.",
    )

    add_body_paragraph(
        doc,
        "General-purpose commercial large language models (LLMs) can generate fluent answers to citizen queries, but they have well-documented failure modes when handling legal texts. In domain-specific tasks, models routinely invent procedural deadlines, misstate statutory filing fees, conflate central guidelines with state-level amendments, or cite non-existent court cases and statutory clauses (Lewis et al., 2020; Bench-Capon et al., 2012; Barnett et al., 2024). In an administrative context, these errors are not minor inconveniences: advising a citizen to pay the wrong application fee or misquoting an RTI appeal window can lead to an application being rejected outright.",
    )

    add_body_paragraph(
        doc,
        "The VeLiS-RAG (Verified Multilingual Legal Simplification with Adaptive Hybrid Retrieval) project explores an open-source, local-first system designed around these specific challenges. The prototype takes natural language queries from citizens or uploaded administrative notices and drafts structured, simplified briefs in English and Hindi. Instead of relying on an LLM's parametric memory, every operative legal claim is tied to verified, allowlisted public enactments through a multi-stage verification pipeline.",
    )

    # Author Placeholder 1
    add_placeholder_box(
        doc,
        "[Author’s project motivation]",
        "Insert your specific academic and personal motivations for selecting Indian administrative simplification, your institutional background, and observations regarding citizen access barriers that inspired this work.",
    )

    add_body_paragraph(
        doc, "Core Architectural Hypotheses and Design Principles:", bold_prefix="Proposed Research Contributions: "
    )
    add_bullet(
        doc,
        "Separates input documents into primary enactments (Tier A), explanatory circulars (Tier B), and untrusted user uploads (Tier C). Operative legal claims—such as eligibility criteria, statutory fees, and deadlines—must be grounded strictly in Tier A documents. We plan to implement this hierarchy during Phase 1 ingestion.",
        bold_prefix="1. Source Trust Stratification: ",
    )
    add_bullet(
        doc,
        "Binds every passage chunk to SHA-256 hashes of original downloaded bytes and canonically normalized text, allowing us to verify bit-level source integrity from disk to prompt. This was implemented and verified during Phase 0.",
        bold_prefix="2. Cryptographic Dual-Hash Provenance: ",
    )
    add_bullet(
        doc,
        "Uses an NLI classifier to evaluate whether retrieved passages supply sufficient factual premises before generation begins, triggering explicit structured abstention when required facts are missing. We plan to calibrate this in Phase 3.",
        bold_prefix="3. Epistemic Source-Sufficiency Gating: ",
    )
    add_bullet(
        doc,
        "Decomposes draft briefs into atomic propositions to verify entailment against cited Tier A passages using natural language inference cross-encoders (Thorne et al., 2018; Min et al., 2023), pruning unsupported statements before final output. Planned for Phase 3.",
        bold_prefix="4. Claim-Level Entailment Verification: ",
    )
    add_bullet(
        doc,
        "Normalizes statutory fees, durations, section references, and institutional titles across English and Hindi using Commission for Scientific and Technical Terminology (CSTT) standards to prevent translation discrepancies. Planned for Phase 4.",
        bold_prefix="5. Structured Invariant Normalization: ",
    )
    add_bullet(
        doc,
        "Disallows heuristic or silent overwrites of bilingual discrepancies, triggering a single bounded regeneration from evidence before failing over to an auditable abstention notice. Planned for Phase 4.",
        bold_prefix="6. Safe Recovery and Anti-Silent-Repair Policy: ",
    )

    # -------------------------------------------------------------
    # 3. RESEARCH SCOPE AND BOUNDARIES
    # -------------------------------------------------------------
    add_custom_heading(doc, "2. Research Scope and Boundaries", level=1)

    add_body_paragraph(
        doc,
        "To maintain experimental tractability and empirical control, the initial prototype evaluation is bounded to three representative administrative domains in the Union jurisdiction of India:",
    )

    add_bullet(
        doc,
        "Right to Information Act, 2005, and Central RTI Rules, 2012 (Ministry of Personnel, Public Grievances and Pensions).",
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
        doc,
        "Documentary inputs are categorized into three non-overlapping tiers to prevent contextual commentary from overriding enacted statutory provisions:",
    )

    tier_data = [
        (
            "Tier A: Authoritative Ground Truth",
            "Acts of Parliament, State Enactments, Gazetted Statutory Rules, Officially Notified Operational Guidelines.",
            "Mandatory grounding for all legally operative claims (eligibility, statutory fees, deadlines, penalties, procedural rights).",
            "Requires validation against approved canonical and file-delivery hosts; verified dual-hash metadata mandatory.",
        ),
        (
            "Tier B: Qualified Official Context",
            "Departmental circulars, office memoranda, administrative FAQs, draft guidelines, consultation papers.",
            "Permitted for administrative context, background explanation, and query discovery.",
            "Prohibited from serving as the sole evidentiary basis for operative claims. Outputs carry a contextual advisory tag.",
        ),
        (
            "Tier C: Untrusted Material",
            "User-uploaded PDFs, citizen petitions, third-party portals, secondary commentary, news reports.",
            "Processed as target subject matter to be audited, simplified, or cross-referenced against Tier A/B evidence.",
            "Excluded from the retrieval grounding index; treated as untrusted user data within an isolated processing sandbox.",
        ),
    ]
    build_table(
        doc,
        ["Trust Tier", "Eligible Documents", "Permitted Evidentiary Role", "Validation Constraints"],
        tier_data,
        [1.4, 1.7, 1.8, 1.37],
    )

    add_custom_heading(doc, "2.2 What the System Refuses or Abstains From", level=2)
    add_body_paragraph(
        doc,
        "To avoid misrepresenting legal capabilities and protect citizen safety, the prototype enforces explicit functional limits:",
    )
    add_bullet(
        doc,
        "The system does not assess case merits, predict judicial decisions, or formulate litigation tactics. All generated briefs present a standard administrative informational disclaimer.",
        bold_prefix="Legal Advice Refusal: ",
    )
    add_bullet(
        doc,
        "When a citizen query requires state-level rules or departmental circulars absent from the verified corpus, the pipeline halts synthesis and identifies the missing regulatory scope.",
        bold_prefix="Out-of-Scope / Missing Evidence Abstention: ",
    )
    add_bullet(
        doc,
        "When retrieved sources contain conflicting statutory versions or unnotified draft amendments, the system notes the temporal conflict rather than selecting an unverified rule.",
        bold_prefix="Conflicting Provision Abstention: ",
    )
    add_bullet(
        doc,
        "The system refuses to process individual court dockets, FIR copies, or submissions containing Personally Identifiable Information (PII).",
        bold_prefix="PII and Private Dispute Refusal: ",
    )

    # -------------------------------------------------------------
    # 4. END-TO-END SYSTEM ARCHITECTURE
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "3. End-to-End System Architecture", level=1)

    add_body_paragraph(
        doc,
        "The VeLiS-RAG architecture couples hybrid retrieval with a verification pipeline that treats generative models as drafting engines bounded by rule-based validation gates. Figure 1 illustrates the component pipeline and decision paths.",
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram1_end_to_end_architecture.png",
        "Figure 1: VeLiS-RAG End-to-End System Architecture and Decision Paths",
        "Diagram Notes: Figure 1 illustrates the six sequential pipeline stages from URL ingestion to bilingual brief delivery. The four validation diamonds denote: (1) Host and Path Allowlist Check, (2) Source-Sufficiency Gate preventing synthesis when evidence is incomplete, (3) Claim-Level Entailment Gate requiring Tier A support for operative assertions, and (4) Cross-Lingual Invariant Parity Gate.",
    )

    add_custom_heading(doc, "3.1 Sequential Decision Paths and Verification Gates", level=2)
    add_body_paragraph(doc, "The architecture executes sequential branching logic across four primary checkpoints:")
    add_bullet(
        doc,
        "During document ingestion, if a source URL or its resolved redirect target is absent from configs/source_allowlist.yaml, or specifies an unapproved document type, ingestion halts and records a security audit entry. (Implemented and verified in Phase 0).",
        bold_prefix="Decision Path 1 (Approved vs. Rejected Source): ",
    )
    add_bullet(
        doc,
        "Before generating a response, if the calibrated NLI sufficiency classifier scores below threshold tau_suff, generation is bypassed and an explanatory abstention summary is returned. (Planned for Phase 3).",
        bold_prefix="Decision Path 2 (Sufficient vs. Insufficient Evidence): ",
    )
    add_bullet(
        doc,
        "After drafting, each atomic claim in the brief must achieve an NLI entailment score >= tau_entail against cited Tier A passages. Unverified claims are pruned or trigger a single bounded regeneration. (Planned for Phase 3).",
        bold_prefix="Decision Path 3 (Verified vs. Unsupported Claim): ",
    )
    add_bullet(
        doc,
        "During bilingual generation, if normalized numbers, deadlines, or statutory authorities differ between English and Hindi, the system initiates a single regeneration pass. If discrepancies persist, it abstains and logs the mismatch. (Planned for Phase 4).",
        bold_prefix="Decision Path 4 (Matching vs. Discrepant Invariants): ",
    )

    # -------------------------------------------------------------
    # 5. STEP-BY-STEP DATA FLOW
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "4. Step-by-Step Data Flow", level=1)

    add_body_paragraph(
        doc,
        "Document processing and query servicing traverse 12 formal stages, each governed by input-output contracts, schema validation, and defined fallback behaviors:",
    )

    stages = [
        (
            "1. Source Approval",
            "Candidate URL & Doc Type",
            "Validate against configs/source_allowlist.yaml (canonical host, file host, path regex).",
            "Validated SourceRegistryEntry",
            "Reject wildcard hosts, unregistered domains, or disallowed document types.",
            "Halt ingestion and record security audit log.",
        ),
        (
            "2. Raw File Capture & Hashing",
            "Approved file download stream",
            "Download raw bytes directly; compute SHA-256 digest prior to text parsing.",
            "Local raw file + raw_file_sha256",
            "Reject placeholder hashes, truncated files, or SSL validation failures.",
            "Abort acquisition; isolate corrupted byte stream.",
        ),
        (
            "3. Metadata Catalog Recording",
            "Raw file + Provenance parameters",
            "Serialize to LegalDocumentMetadata schema; write to SQLite WAL catalog.",
            "Committed catalog record",
            "Verify dual hashes are 64-char lowercase hex; confirm statutory reuse basis.",
            "Roll back database transaction; log error.",
        ),
        (
            "4. Legal Hierarchy Parsing",
            "Raw PDF / HTML bytes",
            "Parser extracts structural hierarchy (Chapter, Section, Sub-section, Rule, Clause).",
            "Ordered PassageChunk objects",
            "Assess character density; verify parent-child statutory hierarchy integrity.",
            "Isolate degraded scans for manual or dual-pass OCR.",
        ),
        (
            "5. Hybrid Retrieval",
            "Citizen Query (EN / HI)",
            "Concurrent sparse BM25 search and dense embedding search (BGE-M3).",
            "Top-50 candidate passages",
            "Sanitize query string; apply temporal and jurisdiction pre-filters.",
            "Fall back to pure sparse search if dense index is offline.",
        ),
        (
            "6. Evidence Filtering & Fusion",
            "Top-50 candidates",
            "Reciprocal Rank Fusion (RRF, k=60); exclude Tier C; annotate Tier B; select top-15.",
            "Ranked Tier A/B passages",
            "Verify that operative claims map to candidate Tier A passages.",
            "Exclude Tier C; attach contextual warning banner if Tier B is used.",
        ),
        (
            "7. Structured Answer Planning",
            "Ranked evidence + Query",
            "Construct structured brief outline: Direct Answer, Eligibility, Procedure, Invariant Table.",
            "Structured Brief Plan Schema",
            "Confirm that mandatory brief sections map to retrieved passages.",
            "Trigger early abstention if core query concepts are unmapped.",
        ),
        (
            "8. Generation Synthesis",
            "Brief Plan + Evidence Text",
            "Local LLM (Qwen2.5-7B) synthesizes initial prose within XML delimiters.",
            "Draft Citizen Brief text",
            "Enclose evidence within <evidence_data>; prohibit instruction overrides.",
            "Reject malformed outputs; re-prompt with constrained schema.",
        ),
        (
            "9. Claim Verification",
            "Draft Brief text + Citations",
            "Decompose into atomic propositions; verify entailment against cited passage via NLI.",
            "VerificationResult audit object",
            "Verify operative claims are entailed exclusively by Tier A passages.",
            "Prune unsupported claim; regenerate draft once from Tier A evidence.",
        ),
        (
            "10. Hindi Alignment",
            "Verified English Brief",
            "Synthesize Devanagari Hindi brief using CSTT standardized legal terminology.",
            "Paired Hindi Citizen Brief",
            "Confirm statutory terms align with official CSTT Hindi glossaries.",
            "Flag unmapped terms; default to approved administrative term.",
        ),
        (
            "11. Invariant Validation",
            "English & Hindi Briefs",
            "Extract and normalize fees, deadlines, section IDs, and authority titles.",
            "Bilingual Invariant Tuple Set",
            "Verify exact normalized parity (INR, DURATION, SEC_ID, AUTH_ID).",
            "Regenerate once from Tier A; if still discrepant, abort and abstain.",
        ),
        (
            "12. Final Delivery & Audit",
            "Validated Bilingual Brief",
            "Format user brief with verified citations, metadata provenance, and disclaimer.",
            "Final Citizen Brief + Audit Log",
            "Confirm presence of mandatory administrative disclaimer banner.",
            "Withhold output if disclaimer is absent; log audit incident.",
        ),
    ]

    for s_title, s_in, s_proc, s_out, s_chk, s_fail in stages:
        add_custom_heading(doc, s_title, level=2)
        s_data = [
            ("Input Data", s_in),
            ("Processing Logic", s_proc),
            ("Output Artifact", s_out),
            ("Validation Check", s_chk),
            ("Failure Behavior", s_fail),
        ]
        build_table(doc, ["Stage Attribute", "Specification Details"], s_data, [1.8, 4.47], space_after=3)

    # -------------------------------------------------------------
    # 6. TRUST AND PROVENANCE ARCHITECTURE
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "5. Trust and Provenance Architecture", level=1)

    add_body_paragraph(
        doc,
        "The credibility of a legal simplification system depends on ensuring that all synthesized information traces directly to authorized public records. Figure 2 illustrates the provenance model, host allowlist architecture, and cryptographic hash verification pipeline.",
        space_after=3,
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram2_trust_and_provenance.png",
        "Figure 2: VeLiS-RAG Trust and Provenance Architecture",
        "Diagram Notes: Figure 2 details the three-tier trust model, the separated host registry, and the dual-hash verification mechanism. Tier B materials are restricted from supporting operative claims, and Tier C material is excluded from retrieval grounding.",
        width_in=4.5,
    )

    add_custom_heading(doc, "5.1 Canonical vs. File-Delivery Host Separation", level=2)
    add_body_paragraph(
        doc,
        "Indian Government digital portals often separate primary user-facing portals from binary content delivery networks. For instance, a central enactment indexed on www.indiacode.nic.in may resolve download requests to cdnbbsr.s3waas.gov.in (National Informatics Centre Secure S3 infrastructure).",
        space_after=2,
    )
    add_body_paragraph(
        doc,
        "To accommodate legitimate government delivery mechanisms while mitigating open-redirect risks, the VeLiS-RAG Source Registry records both canonical hosts and approved file-delivery hosts. Ingestion modules check both the initial link and the final HTTP redirect target against the registry. Redirects to unlisted third-party CDNs or external commercial storage are rejected.",
        space_after=3,
    )

    add_custom_heading(doc, "5.2 Dual-Hash Mathematical Integrity", level=2)
    add_body_paragraph(
        doc, "To provide end-to-end auditability across ingestion, text extraction, and chunking stages:", space_after=2
    )
    add_bullet(
        doc,
        "Calculated over the raw byte sequence of downloaded files prior to parsing, proving byte-level parity with the official source. (Implemented and verified in Phase 0).",
        bold_prefix="raw_file_sha256: ",
        space_after=2,
    )
    add_bullet(
        doc,
        "Calculated over canonically normalized UTF-8 text (applying Unicode NFC normalization, BOM removal, and canonical whitespace reduction), verifying that database passages reflect extracted source text without modification. (Implemented and verified in Phase 0).",
        bold_prefix="extracted_text_sha256: ",
        space_after=2,
    )
    add_bullet(
        doc,
        "Data schemas explicitly reject mock or placeholder strings (such as 'PLACEHOLDER_HASH'). Only valid 64-character lowercase hexadecimal digests are accepted into production records. (Implemented and verified in Phase 0).",
        bold_prefix="Runtime Placeholder Rejection: ",
        space_after=2,
    )

    # -------------------------------------------------------------
    # 7. VERIFICATION AND SAFETY ARCHITECTURE
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "6. Verification and Safety Architecture", level=1)

    add_body_paragraph(
        doc,
        "VeLiS-RAG establishes an explicit boundary between evidentiary authority and instruction authority. While an official enactment provides legal authority for factual statements, it is never treated as a source of execution directives. Figure 3 illustrates the multi-tier verification and prompt-isolation architecture.",
        space_after=2,
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram3_verification_and_safety.png",
        "Figure 3: VeLiS-RAG Verification and Safety Architecture",
        "Diagram Notes: Figure 3 illustrates the multi-layer layout: retrieved evidence is isolated within strict XML data tags, atomic claim entailment gates verify factual support, and structured invariant normalization detects bilingual drift.",
        width_in=3.8,
    )

    add_custom_heading(doc, "6.1 Data-Only Prompt Injection Defense", level=2)
    add_body_paragraph(
        doc,
        "Prompt injection is a recognized risk in legal RAG systems, whether originating from adversarial user inputs or indirect injection embedded within public notices, gazette footnotes, or user-uploaded documents (Tier C).",
        space_after=2,
    )
    add_body_paragraph(
        doc,
        "Rather than relying on fragile string blacklists, VeLiS-RAG enforces clear architectural boundaries:",
        space_after=2,
    )
    add_bullet(
        doc,
        "The generator operates under an immutable system prompt specifying that its sole function is administrative simplification within predefined schema boundaries. (Planned for Phase 3).",
        bold_prefix="Immutable System Prompt: ",
        space_after=1.5,
    )
    add_bullet(
        doc,
        "All retrieved passages are enclosed within structured XML data tags: <evidence_data chunk_id='...'>...</evidence_data>. Explicit system instructions state that content within evidence tags is untrusted data and must never be executed as directives. (Planned for Phase 3).",
        bold_prefix="Structured Evidence Delimiters: ",
        space_after=1.5,
    )
    add_bullet(
        doc,
        "Outputs are parsed directly into strict Pydantic JSON schemas, preventing the model from returning arbitrary control text or instructions. (Planned for Phase 3).",
        bold_prefix="Schema-Constrained Generation: ",
        space_after=2,
    )

    add_custom_heading(doc, "6.2 Safe Recovery and Anti-Silent-Repair Policy", level=2)
    add_body_paragraph(
        doc,
        "In multilingual administrative domains, translation divergence can alter substantive meaning. For example, if an English brief specifies an application fee of 'Rs. 10' while the Hindi translation states 'Rs. 100', the discrepancy may mislead an applicant.",
        space_after=2,
    )
    add_body_paragraph(
        doc,
        "To prevent uninspected errors, the pipeline adopts an explicit policy against silent heuristic repairs:",
        space_after=2,
    )
    add_bullet(
        doc,
        "When an invariant mismatch between English and Hindi text is identified, the system initiates a single bounded regeneration from the verified Tier A passage. (Planned for Phase 4).",
        bold_prefix="Step 1 (Bounded Regeneration): ",
        space_after=1.5,
    )
    add_bullet(
        doc,
        "If the discrepancy persists after regeneration, the system halts delivery of that section, outputs the verified Tier A citation directly, and logs an incident in the audit database. (Planned for Phase 4).",
        bold_prefix="Step 2 (Safe Abstention & Audit): ",
        space_after=2,
    )

    # -------------------------------------------------------------
    # 8. TECHNOLOGY STACK
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "7. Technology Stack and Selection Rationale", level=1)

    add_body_paragraph(
        doc,
        "To facilitate scientific reproducibility, ensure citizen privacy, and avoid recurring API costs, VeLiS-RAG is designed as a local-first system. Table 2 details the baseline components selected for Phase 2 implementation alongside planned future ablation candidates.",
    )

    # Author Placeholder 2 & 5
    add_placeholder_box(
        doc,
        "[Local hardware configuration]",
        "Specify your available local workstation hardware: CPU model, core/thread count, total system RAM (e.g., 32 GB / 64 GB), GPU model and VRAM (e.g., NVIDIA RTX 3060/4060/4080 with 8GB/12GB/16GB VRAM), and storage type (NVMe SSD).",
    )

    add_placeholder_box(
        doc,
        "[Author’s implementation decision and reason]",
        "Document your specific technical rationale for selecting local embedded tools (e.g., opting for embedded Qdrant over client-server deployment to simplify standalone execution, or selecting pure-Python BM25Okapi for initial Phase 2 portability).",
    )

    stack_data = [
        (
            "API / Backend",
            "FastAPI (Python 3.11+) + Pydantic v2",
            "Litestar / AsyncIO raw",
            "Phase 2 Baseline",
            "High throughput async routing; strict runtime schema validation; automated OpenAPI documentation.",
        ),
        (
            "Keyword Search",
            "BM25Okapi (pure Python)",
            "Tantivy (Rust via tantivy-py)",
            "Phase 2 Baseline",
            "Self-contained implementation without native compilation requirements for initial portability.",
        ),
        (
            "Keyword Scaling",
            "Tantivy (tantivy-py)",
            "Elasticsearch / OpenSearch",
            "Future Ablation",
            "Evaluates sub-millisecond index search efficiency gains over pure-Python BM25 on larger corpora.",
        ),
        (
            "Vector Store",
            "Qdrant (Local Embedded Mode)",
            "Chroma / LanceDB / SQLite-vec",
            "Phase 2 Baseline",
            "Direct on-disk persistence; eliminates separate Docker service requirements; fast HNSW index.",
        ),
        (
            "Embedding Model",
            "BAAI/bge-m3 (Dense 1024-dim)",
            "multilingual-e5-large / IndicBERT",
            "Phase 2 Baseline",
            "Broad multilingual representation including Hindi; 8,192 token context window (Chen et al., 2024).",
        ),
        (
            "Reranker Model",
            "bge-reranker-v2-m3",
            "Cross-Encoder MiniLM / Cohere Cloud",
            "Future Ablation",
            "Evaluates precision improvements from cross-encoder scoring over Reciprocal Rank Fusion.",
        ),
        (
            "Generator Model",
            "Qwen2.5-7B-Instruct (4-bit GGUF)",
            "Llama-3.1-8B / Mistral-7B",
            "Phase 2 Baseline",
            "Open-weights model with strong multilingual and Hindi Devanagari performance (Yang et al., 2024).",
        ),
        (
            "Catalog & Storage",
            "SQLite 3 (WAL Mode)",
            "DuckDB / PostgreSQL",
            "Phase 2 Baseline",
            "Serverless ACID persistence for metadata, cryptographic hashes, and verification audit trails.",
        ),
        (
            "Testing Suite",
            "Pytest, Hypothesis, MyPy, Ruff",
            "Unittest, Robot Framework",
            "Phase 0 Implemented",
            "Property-based invariant testing, strict static typing, and automated code formatting.",
        ),
        (
            "Query Routing",
            "Adaptive Complexity Router",
            "Static Hybrid Fusion",
            "Future Ablation",
            "Evaluates multi-hop query decomposition against single-shot hybrid retrieval.",
        ),
    ]
    build_table(
        doc,
        ["Subsystem Layer", "Selected Component", "Evaluated Alternatives", "Lifecycle Status", "Technical Rationale"],
        stack_data,
        [1.1, 1.7, 1.4, 0.95, 1.12],
        space_after=6,
    )

    # -------------------------------------------------------------
    # 9. PHASED IMPLEMENTATION ROADMAP
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "8. Phased Implementation Roadmap", level=1)

    add_body_paragraph(
        doc,
        "VeLiS-RAG follows a phased research lifecycle. Figure 4 illustrates the progression from Phase 0 to Phase 6 alongside the five-tier evaluation pyramid.",
    )

    insert_diagram(
        doc,
        DIAGRAMS_DIR / "diagram4_roadmap_pyramid.png",
        "Figure 4: VeLiS-RAG Phased Implementation Roadmap and Testing Pyramid",
        "Diagram Notes: Figure 4 outlines the sequential phases alongside the testing hierarchy. Phase 0 has been implemented and audited; Phases 1 through 6 represent planned future research stages.",
    )

    add_custom_heading(doc, "8.1 Detailed Phase Deliverables and Progression Gates", level=2)

    # Author Placeholder 4
    add_placeholder_box(
        doc,
        "[Observed Phase 1 results]",
        "When Phase 1 seed ingestion is executed, document empirical outcomes here: number of ingested sections/chunks, download byte sizes, observed hash verification timings, and any parsing edge cases encountered.",
    )

    roadmap_data = [
        (
            "Phase 0: Foundations & Governance",
            "Repository structure, Pydantic schemas, source allowlist registry, dual-hash utilities, invariant engine.",
            "Schema tests, dual-hash vectors, Tier B operative prohibition, redirect checks.",
            "Lint clean, MyPy strict pass, 35/35 tests passing (92% coverage).",
            "Failure of schema validation or reliance on external cloud APIs.",
        ),
        (
            "Phase 1: Curated Corpus Ingestion",
            "Ingestion pipeline for RTI Act 2005, PM-KISAN, and PM-JAY. Structural hierarchy parser and SQLite catalog.",
            "Dual-hash verification on downloaded bytes, structural hierarchy parsing tests.",
            "100% of chunks carry verified raw and normalized hashes and tier tags.",
            "Broken section hierarchy or unverified redirect host in candidate chunks.",
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
            "Source sufficiency classifier, plan-then-generate orchestrator, atomic claim NLI verifier, abstention module.",
            "Sufficiency threshold calibration, unanswerable query probe tests, claim entailment tests.",
            "Dev set: target >= 90% abstention on unanswerable queries; unsupported claims <= 2.0%.",
            "Uncited statutory fee or fabricated section reference in evaluation suite.",
        ),
        (
            "Phase 4: Multilingual & Invariant Engine",
            "Hindi generation pipeline via CSTT legal glossary. Structured Invariant Engine integration. Invariant comparison.",
            "Property-based invariant fuzzing, cross-lingual entity consistency tests.",
            "Target 100% invariant parity between English and Hindi briefs on test suite.",
            "Unresolved fee, deadline, or authority mismatch between EN and HI outputs.",
        ),
        (
            "Phase 5: Held-Out Research Evaluation",
            "Evaluation over held-out benchmark (N=150-300). Bootstrap 95% CIs. Inter-annotator agreement (Cohen's kappa, Krippendorff's alpha).",
            "End-to-end benchmark execution, temporal split tests, jurisdiction split tests.",
            "Benchmark report generated via reproducible CLI execution.",
            "Non-reproducible evaluation runs or manual intervention during test execution.",
        ),
        (
            "Phase 6: Researcher Workbench",
            "Local FastAPI backend + inspection interface. Visual citation highlighting, RRF and NLI inspector drawers.",
            "Automated browser tests, offline execution verification, export integrity tests.",
            "Workbench functions offline; zero external network transmission.",
            "UI executes without mandatory legal disclaimer or leaks server paths.",
        ),
    ]
    build_table(
        doc,
        [
            "Phase Milestone",
            "Scope & Deliverables",
            "Automated Test Suite",
            "Acceptance Criteria",
            "Progression Stop Conditions",
        ],
        roadmap_data,
        [1.2, 1.8, 1.4, 0.95, 0.92],
        space_after=4,
    )

    # -------------------------------------------------------------
    # 10. TEST AND EVALUATION STRATEGY
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "9. Test and Evaluation Strategy", level=1)

    add_body_paragraph(
        doc,
        "The evaluation strategy combines deterministic assertions for core data models with statistical evaluation across a planned held-out benchmark.",
    )

    test_matrix = [
        (
            "Unit Tests",
            "Pydantic models, dual-hash utilities, text normalizers, invariant regexes.",
            "Pytest assertions on synthetic and edge-case fixtures.",
            "100% pass rate; zero schema regressions (Implemented in Phase 0).",
        ),
        (
            "Integration Tests",
            "End-to-end flow from Query -> Router -> Retrieval -> Brief Synthesis.",
            "Mocked retrieval and LLM pipeline execution tests.",
            "Valid BilingualBrief schema output without unhandled exceptions (Planned).",
        ),
        (
            "Provenance Tests",
            "Canonical host matching, redirect validation, placeholder hash rejection.",
            "Host allowlist validation and dual-hash test vectors.",
            "Rejection of unapproved hosts, paths, and placeholders (Implemented in Phase 0).",
        ),
        (
            "Retrieval Benchmarks",
            "Hybrid BM25 + Qdrant BGE-M3 retrieval against gold passage mappings.",
            "Rank-order evaluation on 50 development queries.",
            "Target: Recall@5 >= 88.0%; MRR@5 >= 0.82 (Planned Phase 2).",
        ),
        (
            "Claim Entailment Tests",
            "Atomic claim entailment checking against cited Tier A passages.",
            "NLI cross-encoder scoring on claim propositions.",
            "Target: Unsupported-claim rate <= 2.0% [95% CI] (Planned Phase 3).",
        ),
        (
            "Adversarial Tests",
            "Direct prompt jailbreaks, indirect injection via gazette text/footnotes.",
            "Curated adversarial input test suite.",
            "Zero prompt overrides; evidence processed as data only (Planned Phase 3).",
        ),
        (
            "Multilingual Invariant Tests",
            "Cross-lingual parity for fees, durations, sections, and authorities.",
            "Hypothesis property-based tests comparing EN and HI.",
            "Zero unresolved invariant drift on release test suite (Planned Phase 4).",
        ),
        (
            "Regression Tests",
            "Frozen 30-query regression test suite executed before release commits.",
            "Automated metric regression assertions.",
            "No regression in faithfulness, recall, or abstention (Planned Phase 5).",
        ),
        (
            "Human Expert Review",
            "Qualitative evaluation of 10 sampled briefs by legal domain researchers.",
            "Structured review protocol assessing fidelity and clarity.",
            "Adherence to jurisdictional bounds and disclaimers (Planned Phase 5).",
        ),
    ]
    build_table(
        doc,
        ["Test Category", "Target Subsystem", "Evaluation Methodology", "Target Criteria"],
        test_matrix,
        [1.4, 1.7, 1.8, 1.37],
        space_after=4,
    )

    add_custom_heading(doc, "9.1 Planned Research Evaluation Metrics", level=2)
    add_body_paragraph(
        doc,
        "The evaluation framework specifies target objectives alongside 95% bootstrap confidence intervals to provide statistically sound performance estimates:",
    )

    metrics_data = [
        (
            "Retrieval Recall@5",
            "Proportion of gold legal passages retrieved in top-5 candidates.",
            ">= 88.0% [84.5%, 91.2%]",
            "Automated rank-order evaluation",
        ),
        (
            "Retrieval MRR@5",
            "Mean Reciprocal Rank of the first relevant statutory passage.",
            ">= 0.82 [0.77, 0.86]",
            "Automated rank-order evaluation",
        ),
        (
            "Unsupported-Claim Rate",
            "Proportion of generated atomic claims lacking Tier A entailment.",
            "<= 2.0% [0.5%, 3.5%]",
            "NLI cross-encoder entailment scoring",
        ),
        (
            "Citation Precision",
            "Proportion of cited passages that directly entail the claim.",
            ">= 92.0% [88.0%, 95.5%]",
            "Claim-to-passage audit",
        ),
        (
            "Citation Recall",
            "Proportion of operative claims that carry an exact citation.",
            ">= 85.0% [80.5%, 89.0%]",
            "Operative claim coverage audit",
        ),
        (
            "Abstention F1-Score",
            "Harmonic mean of precision and recall on unanswerable queries.",
            ">= 90.0% [85.0%, 94.2%]",
            "Unanswerable query probe evaluation",
        ),
        (
            "Invariant Parity Rate",
            "Proportion of briefs where EN and HI normalized invariants match.",
            "100.0% on test suite",
            "Rule-based invariant comparison",
        ),
        (
            "Query Latency (p95)",
            "95th percentile query execution time on local workstation.",
            "< 8.0s (CPU) / < 4.5s (GPU)",
            "Automated latency telemetry",
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
        [1.4, 2.2, 1.37, 1.3],
        space_after=4,
    )

    # -------------------------------------------------------------
    # 11. CURRENT PHASE 0 STATUS & AUDIT
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "10. Current Phase 0 Status and Audit Findings", level=1)

    add_body_paragraph(
        doc,
        "Phase 0 (Foundations, Governance, Schemas, and Test Suite) was implemented and evaluated through a formal audit on September 18, 2026. The empirical findings are documented below:",
    )

    add_bullet(
        doc,
        "All 35 automated tests in the Pytest suite execute cleanly in 1.05 seconds with zero failures.",
        bold_prefix="Automated Test Suite: ",
    )
    add_bullet(
        doc,
        "The test suite achieves 92% statement coverage across core modules (722 statements evaluated, 56 missed).",
        bold_prefix="Test Coverage: ",
    )
    add_bullet(
        doc,
        "Static type checking via MyPy in strict mode passes with zero errors across all 21 source files.",
        bold_prefix="Static Type Checking: ",
    )
    add_bullet(
        doc, "All 27 project files comply with project code formatting standards.", bold_prefix="Code Formatting: "
    )
    add_bullet(
        doc,
        "An unused import (DEVANAGARI_DIGITS in tests/test_invariants.py:11) caused 'ruff check .' to exit with code 1; this has been identified for resolution before Phase 1.",
        bold_prefix="Finding 1 (Linter Issue): ",
    )
    add_bullet(
        doc,
        "While no ML model weights or external legal documents were downloaded, Python development dependencies were acquired from PyPI during initial virtual environment setup. Earlier documentation claiming 'zero external network downloads' has been corrected to reflect development package installation.",
        bold_prefix="Finding 2 (Dependency Clarification): ",
    )
    add_bullet(
        doc,
        "No external government documents, ML model weights (LLM, embeddings, reranker), vector databases, or cloud APIs have been initialized in the repository.",
        bold_prefix="Finding 3 (Premature Resource Isolation): ",
    )
    add_bullet(
        doc,
        "The Git repository is initialized, but files remain untracked; an initial commit is scheduled to establish a baseline commit SHA.",
        bold_prefix="Finding 4 (Git Baseline State): ",
    )
    add_bullet(
        doc,
        "Dependencies in pyproject.toml currently use semver ranges rather than exact pinned lockfiles; a requirements.lock file will be generated.",
        bold_prefix="Finding 5 (Dependency Lockfile): ",
    )

    # Author Placeholder 3
    add_placeholder_box(
        doc,
        "[Supervisor feedback]",
        "Insert formal feedback, review observations, and sign-off comments from your academic supervisor regarding the Phase 0 audit findings and permission to proceed to Phase 1.",
    )

    add_callout(
        doc,
        "Phase 0 Audit Outcome: VERIFIED WITH REQUIRED MAINTENANCE ACTIONS\n"
        "All core domain models, schemas, trust rules, provenance hashing utilities, redirect validators, and invariant normalizers are empirically verified. Three maintenance actions are scheduled prior to Phase 1: (1) remove the unused import in test_invariants.py, (2) record the initial Git commit, and (3) generate a pinned requirements.lock file.",
        title="PHASE 0 AUDIT OUTCOME",
        space_after=4,
    )

    # -------------------------------------------------------------
    # 12. RISKS AND MITIGATIONS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "11. Comprehensive Risk Register and Mitigations", level=1)

    add_body_paragraph(
        doc,
        "Table 4 identifies ten technical, operational, and regulatory risks identified for the research prototype, along with evaluated likelihood, severity, and mitigation strategies.",
    )

    risks_data = [
        (
            "R-01: Outdated / Superseded Law",
            "High",
            "High",
            "Temporal metadata tagging (effective_date, version); reranker filters prioritizing latest enacted rules; prominent version notices.",
            "Automated regression tests checking that 2019 RTI amendment rules supersede 2005 provisions.",
        ),
        (
            "R-02: Source Authority Errors",
            "High",
            "High",
            "Allowlist registry; separation of canonical and file-delivery hosts; rejection of unauthorized domains.",
            "Automated URL and redirect validation tests against configs/source_allowlist.yaml.",
        ),
        (
            "R-03: Gazette OCR Corruption",
            "Medium",
            "High",
            "Ingestion prioritized for digitally native PDFs/HTML; dual-pass OCR with character entropy checks for scanned gazettes.",
            "Character entropy checks; automated quarantine of chunks below word-density thresholds.",
        ),
        (
            "R-04: Indirect Prompt Injection",
            "High",
            "High",
            "Evidence treated strictly as data enclosed in <evidence_data>; immutable system instructions; schema-constrained JSON.",
            "Adversarial test suite simulating prompt injection embedded in queries and PDF footnotes.",
        ),
        (
            "R-05: Retrieval Misses",
            "High",
            "Medium",
            "Hybrid BM25 + dense BGE-M3 retrieval; CSTT administrative synonym expansion; query routing.",
            "Retrieval Recall@5 evaluation over curated probe set of colloquial citizen inquiries.",
        ),
        (
            "R-06: Unsupported Claims",
            "High",
            "High",
            "Atomic proposition decomposition; NLI entailment gate; automatic pruning of unverified assertions.",
            "Unsupported-claim rate reporting with 95% bootstrap confidence intervals.",
        ),
        (
            "R-07: Hindi Translation Drift",
            "Medium",
            "High",
            "CSTT standardized bilingual legal glossary; mandatory mapping of statutory administrative titles.",
            "Automated entity consistency checks verifying Hindi terms match approved glossary.",
        ),
        (
            "R-08: Invariant Discrepancies",
            "Medium",
            "High",
            "Structured Invariant Normalization Engine; single regeneration from Tier A; safe abstention on mismatch.",
            "Bilingual invariant parity assertions; automated rejection when normalized values differ.",
        ),
        (
            "R-09: Licensing Uncertainty",
            "Low",
            "High",
            "Section 52(1)(q) Indian Copyright Act, 1957; document-level metadata; pre-publication compliance review.",
            "Pre-publication review confirming explicit statutory or open-data reuse basis for all materials.",
        ),
        (
            "R-10: Hardware Limitations",
            "Medium",
            "Medium",
            "Local 4-bit quantization (Qwen2.5-7B Q4_K_M); disk-based embedding cache; CPU-fallback support.",
            "Automated latency telemetry tracking p50/p95 latency and peak RAM/VRAM footprint.",
        ),
    ]
    build_table(
        doc,
        ["Risk ID & Description", "Likelihood", "Severity", "Mitigation Strategy", "Audit / Detection Mechanism"],
        risks_data,
        [1.4, 0.8, 0.8, 1.8, 1.47],
        space_after=4,
    )

    # -------------------------------------------------------------
    # 13. CONCLUSION AND NEXT STEPS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_custom_heading(doc, "12. Conclusion and Immediate Next Steps", level=1)

    add_body_paragraph(
        doc,
        "Phase 0 establishes the baseline data schemas, governance rules, and testing tools for VeLiS-RAG. By combining cryptographic dual-hash provenance, source trust stratification, data-only prompt isolation, claim-level NLI entailment verification, and bilingual invariant consistency, the proposed architecture provides a verifiable alternative to unconstrained large language model summarization for Indian public documents.",
    )

    add_body_paragraph(doc, "Immediate technical actions prior to initiating Phase 1 are explicitly bounded:")
    add_bullet(
        doc,
        "Remove the unused DEVANAGARI_DIGITS import from tests/test_invariants.py so that 'ruff check .' exits cleanly.",
        bold_prefix="Action 1 (Linter Maintenance): ",
    )
    add_bullet(
        doc,
        "Stage all project files and record the initial baseline Git commit to establish repository version history.",
        bold_prefix="Action 2 (Version Control Baseline): ",
    )
    add_bullet(
        doc,
        "Generate an exact requirements.lock file via pip freeze to support environment reproducibility.",
        bold_prefix="Action 3 (Dependency Pinning): ",
    )
    add_bullet(
        doc,
        "Verify allowlist entries in configs/source_allowlist.yaml for India Code, RTI Portal, PM-KISAN, and PM-JAY.",
        bold_prefix="Action 4 (Allowlist Confirmation): ",
    )
    add_bullet(
        doc,
        "Phase 1 (Curated Official Corpus Ingestion) will commence upon receipt of supervisor and author approval.",
        bold_prefix="Action 5 (Phase 1 Authorization): ",
    )

    # -------------------------------------------------------------
    # 14. ACADEMIC REFERENCES & STATUTORY BASES
    # -------------------------------------------------------------
    add_custom_heading(doc, "13. Academic References and Statutory Bases", level=1)

    references = [
        (
            "Barnett et al. (2024)",
            "Barnett, S., Kurniawan, S., Thudumu, S., Brannelly, Z., & Abdelrazek, M. 'Seven Failure Points When Fine-tuning a Retrieval Augmented Generation System.' Proceedings of the IEEE/ACM International Conference on Software Engineering, 2024.",
        ),
        (
            "Bench-Capon et al. (2012)",
            "Bench-Capon, T., Araszkiewicz, M., Ashley, K., Atkinson, K., Bourcier, D., Daimer, F., et al. 'A History of AI and Law in 50 Papers: 25 Years of the International Conference on AI and Law.' Artificial Intelligence and Law, 20(3), 215-319, 2012.",
        ),
        (
            "Chen et al. (2024)",
            "Chen, J., Xiao, S., Zhang, P., Luo, K., Lian, D., & Liu, Z. 'BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Multi-Task Learning.' arXiv preprint arXiv:2402.03216, 2024.",
        ),
        (
            "CSTT (Government of India)",
            "Commission for Scientific and Technical Terminology (CSTT). 'Comprehensive Glossary of Administrative Terms (English-Hindi).' Department of Higher Education, Ministry of Education, New Delhi, India.",
        ),
        (
            "Government of India (1957)",
            "The Copyright Act, 1957 (Act No. 14 of 1957). Section 52(1)(q): Certain acts not to be infringement of copyright (reproduction of legislative enactments, gazette notifications, and official committee reports).",
        ),
        (
            "Honovich et al. (2022)",
            "Honovich, O., Aharoni, R., Herzig, J., Taitelbaum, H., Kukliansky, D., Cohen, V., et al. 'TRUE: Re-evaluating Factual Consistency Evaluation Approaches of Abstractive Summarization.' Proceedings of EMNLP 2022.",
        ),
        (
            "Katz et al. (2020)",
            "Katz, D. M., Bommarito, M. J., Gao, H. X., & Cook, A. 'A Natural Language Processing Approach to Measuring the Complexity of Legal Texts.' Law, Probability and Risk, 19(3-4), 283-305, 2020.",
        ),
        (
            "Lewis et al. (2020)",
            "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., et al. 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.' Advances in Neural Information Processing Systems (NeurIPS), 33, 9459-9474, 2020.",
        ),
        (
            "Min et al. (2023)",
            "Min, S., Krishna, K., Lyu, X., Lewis, M., Yih, W., Koh, P. W., et al. 'FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation.' Proceedings of EMNLP 2023.",
        ),
        (
            "Thorne et al. (2018)",
            "Thorne, J., Vlachos, A., Christodoulopoulos, C., & Mittal, A. 'FEVER: A Large-scale Dataset for Fact Extraction and VERification.' Proceedings of NAACL-HLT 2018.",
        ),
        (
            "Yang et al. (2024)",
            "Yang, A., Ba, B., Bai, J., Bai, S., Bian, Y., Chen, B., et al. 'Qwen2.5 Technical Report.' arXiv preprint arXiv:2409.12191, 2024.",
        ),
    ]
    for cite_key, cite_text in references:
        add_bullet(doc, cite_text, bold_prefix=f"{cite_key}: ", space_after=3)

    doc.save(OUTPUT_PATH)
    print(f"Revised document successfully created at: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_revised_document()

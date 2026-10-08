"""Generate high-resolution architecture diagrams for VeLiS-RAG."""

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

# Output directory for diagrams
OUTPUT_DIR = Path("docs/diagrams")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Visual Styling Tokens (Dark-blue professional academic palette)
COLOR_BG = "#FFFFFF"
COLOR_TEXT = "#0F172A"  # Slate 900
COLOR_PRIMARY = "#1E3A8A"  # Deep Blue 900
COLOR_ACCENT = "#2563EB"  # Royal Blue 600
COLOR_LIGHT = "#F8FAFC"  # Slate 50
COLOR_BORDER = "#94A3B8"  # Slate 400
COLOR_SUCCESS = "#15803D"  # Green 700
COLOR_DANGER = "#B91C1C"  # Red 700
COLOR_WARN = "#B45309"  # Amber 700
COLOR_BOX_BG = "#F1F5F9"  # Slate 100


def create_diagram_1():
    """Diagram 1: End-to-End System Architecture with Decision Paths."""
    fig, ax = plt.subplots(figsize=(14, 18), dpi=300)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 130)
    ax.axis("off")

    # Title
    ax.text(
        50,
        126,
        "VeLiS-RAG: End-to-End System Architecture",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )
    ax.text(
        50,
        123,
        "Verified Multilingual Simplification Pipeline with Epistemic Decision Paths",
        ha="center",
        va="center",
        fontsize=11,
        fontstyle="italic",
        color="#475569",
    )

    # Helper for drawing blocks
    def draw_box(x, y, w, h, title, subtitle="", bg=COLOR_BOX_BG, border=COLOR_BORDER, title_color=COLOR_PRIMARY):
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.5,rounding_size=0.8", linewidth=1.5, edgecolor=border, facecolor=bg
        )
        ax.add_patch(rect)
        if subtitle:
            ax.text(
                x + w / 2,
                y + h * 0.62,
                title,
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color=title_color,
            )
            ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center", fontsize=7.5, color="#334155")
        else:
            ax.text(
                x + w / 2,
                y + h * 0.5,
                title,
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color=title_color,
            )

    def draw_diamond(cx, cy, size, text, bg="#FEF3C7", border="#D97706"):
        pts = [(cx, cy + size), (cx + size * 1.3, cy), (cx, cy - size), (cx - size * 1.3, cy)]
        poly = patches.Polygon(pts, closed=True, linewidth=1.5, edgecolor=border, facecolor=bg)
        ax.add_patch(poly)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#92400E")

    def draw_arrow(x1, y1, x2, y2, label="", color=COLOR_ACCENT, dashed=False, label_offset=(1.5, 0)):
        style = "Simple,tail_width=0.8,head_width=4,head_length=5"
        kw = dict(arrowstyle=style, color=color, lw=1.2)
        if dashed:
            kw["linestyle"] = "--"
        patch = patches.FancyArrowPatch((x1, y1), (x2, y2), **kw)
        ax.add_patch(patch)
        if label:
            mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
            ax.text(
                mx,
                my,
                label,
                fontsize=7.5,
                fontweight="bold",
                color=color,
                va="center",
                ha="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9),
            )

    # STAGE 1: Ingestion & Governance
    ax.text(5, 117, "STAGE 1: CURATED INGESTION & PROVENANCE", fontsize=10, fontweight="bold", color=COLOR_PRIMARY)
    draw_box(5, 108, 22, 6, "Candidate URL / Doc", "Official .gov.in / nic.in Host", bg="#EFF6FF", border=COLOR_ACCENT)
    draw_diamond(38, 111, 3.2, "Allowlist\nGate?", bg="#FEF3C7", border="#D97706")
    draw_box(
        50, 108, 22, 6, "Dual-Hash Provenance", "raw_file_sha256 & text_sha256", bg="#F0FDF4", border=COLOR_SUCCESS
    )
    draw_box(78, 108, 17, 6, "Catalog Store", "SQLite WAL Metadata", bg=COLOR_BOX_BG, border=COLOR_BORDER)
    draw_box(
        38,
        97,
        18,
        5,
        "REJECT SOURCE",
        "Alert Logged & Halted",
        bg="#FEE2E2",
        border=COLOR_DANGER,
        title_color=COLOR_DANGER,
    )

    draw_arrow(27, 111, 33.8, 111)
    draw_arrow(42.2, 111, 50, 111, label="Approved", label_offset=(0, 2.2))
    draw_arrow(38, 107.8, 38, 102, label="Reject", color=COLOR_DANGER, label_offset=(3.5, 0))
    draw_arrow(72, 111, 78, 111)

    # STAGE 2: Chunking & Indexing
    ax.text(5, 93, "STAGE 2: LEGAL CHUNKING & HYBRID INDEXES", fontsize=10, fontweight="bold", color=COLOR_PRIMARY)
    draw_box(5, 83, 24, 6, "Structural Parser", "Preserve Chapter/Section/Rule", bg=COLOR_BOX_BG)
    draw_box(38, 83, 24, 6, "BM25 Sparse Index", "Tantivy / Okapi Keyword Index", bg="#EFF6FF", border=COLOR_ACCENT)
    draw_box(71, 83, 24, 6, "Dense Vector Index", "Qdrant Embedded (BGE-M3)", bg="#EFF6FF", border=COLOR_ACCENT)

    draw_arrow(86, 108, 86, 92, dashed=True)
    draw_arrow(17, 108, 17, 89)
    draw_arrow(29, 86, 38, 86)
    draw_arrow(62, 86, 71, 86)

    # STAGE 3: Query Processing & Retrieval
    ax.text(5, 75, "STAGE 3: CITIZEN QUERY & ADAPTIVE RETRIEVAL", fontsize=10, fontweight="bold", color=COLOR_PRIMARY)
    draw_box(
        5, 65, 24, 6, "Citizen Query", "English or Hindi Input", bg="#FDF4FF", border="#A855F7", title_color="#7E22CE"
    )
    draw_box(36, 65, 24, 6, "Data Isolation Boundary", "<evidence_data> Container", bg="#FEF9C3", border="#CA8A04")
    draw_box(
        68,
        65,
        27,
        6,
        "RRF Fusion & Trust Filter",
        "Enforce Tier A / Tier B Caveats",
        bg="#F0FDF4",
        border=COLOR_SUCCESS,
    )

    draw_arrow(29, 68, 36, 68)
    draw_arrow(60, 68, 68, 68)
    draw_arrow(50, 83, 50, 75, dashed=True)
    draw_arrow(83, 83, 83, 75, dashed=True)

    # STAGE 4: Source Sufficiency Gate
    ax.text(5, 57, "STAGE 4: EPISTEMIC SUFFICIENCY GATE", fontsize=10, fontweight="bold", color=COLOR_PRIMARY)
    draw_diamond(50, 48, 3.8, "Source\nSufficient?", bg="#FEF3C7", border="#D97706")
    draw_box(
        76,
        45,
        20,
        6,
        "ABSTAIN",
        "Return Missing Dimensions",
        bg="#FEE2E2",
        border=COLOR_DANGER,
        title_color=COLOR_DANGER,
    )

    draw_arrow(81.5, 65, 50, 52)
    draw_arrow(55, 48, 76, 48, label="No Evidence", color=COLOR_DANGER, label_offset=(0, 2.2))

    # STAGE 5: Plan-then-Generate & Claim Verification
    ax.text(
        5, 39, "STAGE 5: PLAN-THEN-GENERATE & CLAIM ENTAILMENT", fontsize=10, fontweight="bold", color=COLOR_PRIMARY
    )
    draw_box(
        5, 28, 25, 6, "Structured Plan Synthesizer", "Outline -> Legal Brief Draft", bg="#EFF6FF", border=COLOR_ACCENT
    )
    draw_diamond(43, 31, 3.5, "Claims\nEntailed?", bg="#FEF3C7", border="#D97706")
    draw_box(
        65,
        28,
        28,
        6,
        "Hallucination Pruning",
        "Regenerate Once from Tier A",
        bg="#FFFBEB",
        border="#F59E0B",
        title_color="#B45309",
    )

    draw_arrow(50, 44, 17, 34, label="Sufficient", label_offset=(-2.0, 2.2))
    draw_arrow(30, 31, 38.5, 31)
    draw_arrow(47.5, 31, 65, 31, label="Unverified", color=COLOR_WARN, label_offset=(0, 2.2))
    draw_arrow(79, 34, 79, 37, color=COLOR_WARN)
    draw_arrow(79, 37, 17, 37, color=COLOR_WARN)  # Loop back to plan

    # STAGE 6: Multilingual & Invariant Normalization
    ax.text(
        5, 20, "STAGE 6: BILINGUAL CONSISTENCY & SAFE DELIVERY", fontsize=10, fontweight="bold", color=COLOR_PRIMARY
    )
    draw_box(5, 8, 24, 7, "Bilingual Synthesis", "English & Hindi Briefs", bg="#EFF6FF", border=COLOR_ACCENT)
    draw_diamond(38, 11.5, 3.2, "Invariants\nMatch?", bg="#FEF3C7", border="#D97706")
    draw_box(
        55,
        8,
        22,
        7,
        "Mismatch Handler",
        "Regen Once -> Abstain + Log",
        bg="#FEE2E2",
        border=COLOR_DANGER,
        title_color=COLOR_DANGER,
    )
    draw_box(
        82,
        8,
        16,
        7,
        "Final Brief",
        "Verified Citations & Disclaimer",
        bg="#F0FDF4",
        border=COLOR_SUCCESS,
        title_color=COLOR_SUCCESS,
    )

    draw_arrow(43, 27.5, 17, 15, label="Verified", label_offset=(-2.0, 2.2))
    draw_arrow(29, 11.5, 33.8, 11.5)
    draw_arrow(38, 8.3, 55, 11.5, label="Mismatch", color=COLOR_DANGER, label_offset=(2.0, 2.2))
    draw_arrow(42.2, 11.5, 82, 11.5, label="Match", color=COLOR_SUCCESS, label_offset=(0, 2.2))

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "diagram1_end_to_end_architecture.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Generated Diagram 1.")


def create_diagram_2():
    """Diagram 2: Trust and Provenance Architecture."""
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Title
    ax.text(
        50,
        96,
        "VeLiS-RAG: Trust and Provenance Architecture",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )
    ax.text(
        50,
        92.5,
        "Source Trust Stratification, Host Whitelisting, and Cryptographic Dual-Hash Pipeline",
        ha="center",
        va="center",
        fontsize=10.5,
        fontstyle="italic",
        color="#475569",
    )

    # Helper
    def draw_box(x, y, w, h, title, subtitle="", bg=COLOR_BOX_BG, border=COLOR_BORDER, title_color=COLOR_PRIMARY):
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.4,rounding_size=0.6", linewidth=1.5, edgecolor=border, facecolor=bg
        )
        ax.add_patch(rect)
        if subtitle:
            ax.text(
                x + w / 2,
                y + h * 0.62,
                title,
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color=title_color,
            )
            ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center", fontsize=7.5, color="#334155")
        else:
            ax.text(
                x + w / 2,
                y + h * 0.5,
                title,
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color=title_color,
            )

    def draw_arrow(x1, y1, x2, y2, label="", color=COLOR_ACCENT, dashed=False):
        style = "Simple,tail_width=0.8,head_width=4,head_length=5"
        kw = dict(arrowstyle=style, color=color, lw=1.2)
        if dashed:
            kw["linestyle"] = "--"
        patch = patches.FancyArrowPatch((x1, y1), (x2, y2), **kw)
        ax.add_patch(patch)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my + 1.5, label, fontsize=7.5, fontweight="bold", color=color, ha="center")

    # Three Tier Columns
    ax.text(17, 85, "TIER A: AUTHORITATIVE", ha="center", fontsize=11, fontweight="bold", color=COLOR_SUCCESS)
    ax.text(50, 85, "TIER B: CONTEXTUAL ONLY", ha="center", fontsize=11, fontweight="bold", color=COLOR_WARN)
    ax.text(83, 85, "TIER C: UNTRUSTED MATERIAL", ha="center", fontsize=11, fontweight="bold", color=COLOR_DANGER)

    draw_box(
        4,
        69,
        26,
        13,
        "Enacted Acts & Gazettes",
        "Acts of Parliament, Gazetted Rules\nNotified Scheme Guidelines\nSole Evidence for Operative Claims",
        bg="#F0FDF4",
        border=COLOR_SUCCESS,
        title_color=COLOR_SUCCESS,
    )
    draw_box(
        37,
        69,
        26,
        13,
        "Official Circulars & Drafts",
        "Department Memoranda, FAQs, Drafts\nPermitted for Discovery & Context\nPROHIBITED from Operative Claims",
        bg="#FFFBEB",
        border=COLOR_WARN,
        title_color=COLOR_WARN,
    )
    draw_box(
        70,
        69,
        26,
        13,
        "User Uploads & 3rd Party",
        "Citizen PDFs, Letters, Summaries\nUntrusted by Default\nSubject Matter Only - Never Evidence",
        bg="#FEF2F2",
        border=COLOR_DANGER,
        title_color=COLOR_DANGER,
    )

    # Registry & Redirection Layer
    ax.text(
        50, 60, "SOURCE REGISTRY & HOST VERIFICATION", ha="center", fontsize=10, fontweight="bold", color=COLOR_PRIMARY
    )
    draw_box(
        6,
        45,
        24,
        10,
        "Canonical Host Registry",
        "configs/source_allowlist.yaml\ne.g. www.indiacode.nic.in\nExplicit Regex Path Patterns",
        bg="#EFF6FF",
        border=COLOR_ACCENT,
    )
    draw_box(
        38,
        45,
        24,
        10,
        "Redirect & Delivery Gate",
        "Validates Final File Host\ne.g. cdnbbsr.s3waas.gov.in\nRejects Unauthorized CDNs",
        bg="#EFF6FF",
        border=COLOR_ACCENT,
    )
    draw_box(
        70,
        45,
        24,
        10,
        "Pre-Publication Review",
        "License Basis & Copyright Check\nGODL-India & Sec 52(1)(q)\nZero Citizen PII Guarantee",
        bg="#F8FAFC",
        border=COLOR_BORDER,
    )

    draw_arrow(17, 69, 17, 55)
    draw_arrow(50, 69, 50, 55)
    draw_arrow(83, 69, 83, 55, color=COLOR_DANGER, label="Quarantine")
    draw_arrow(30, 50, 38, 50)
    draw_arrow(62, 50, 70, 50)

    # Provenance Dual Hash Layer
    ax.text(
        50,
        37,
        "CRYPTOGRAPHIC DUAL-HASH PROVENANCE PIPELINE",
        ha="center",
        fontsize=10,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )
    draw_box(
        8,
        20,
        38,
        12,
        "raw_file_sha256",
        "Computed on Exact Raw Downloaded Bytes\nPreserves Byte-Level Original in data/raw/\nGuarantees Upstream Anti-Tampering",
        bg="#F1F5F9",
        border=COLOR_BORDER,
    )
    draw_box(
        54,
        20,
        38,
        12,
        "extracted_text_sha256",
        "Computed on Normalized UTF-8 Text\nUnicode NFC + Whitespace + BOM Canonicalized\nBinds Chunks Directly to DB Record",
        bg="#F1F5F9",
        border=COLOR_BORDER,
    )

    draw_arrow(27, 45, 27, 32)
    draw_arrow(50, 45, 50, 32)
    draw_arrow(46, 26, 54, 26, label="Parse")

    # Bottom Catalog & Audit
    draw_box(
        20,
        4,
        60,
        10,
        "SQLite WAL Legal Catalog & Audit Log",
        "Columns: doc_id, raw_sha256, norm_sha256, source_tier, version, effective_date, URL\nRuntime Rejection of Placeholder Hashes | Immutable Audit Trails",
        bg="#F0FDF4",
        border=COLOR_SUCCESS,
        title_color=COLOR_SUCCESS,
    )

    draw_arrow(27, 20, 35, 14)
    draw_arrow(73, 20, 65, 14)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "diagram2_trust_and_provenance.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Generated Diagram 2.")


def create_diagram_3():
    """Diagram 3: Verification and Safety Architecture."""
    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Title
    ax.text(
        50,
        96,
        "VeLiS-RAG: Verification and Safety Architecture",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )
    ax.text(
        50,
        92.5,
        "Data-Only Boundary Isolation, Claim-Level Entailment, and Structured Invariant Repair",
        ha="center",
        va="center",
        fontsize=10.5,
        fontstyle="italic",
        color="#475569",
    )

    # Helper
    def draw_box(x, y, w, h, title, subtitle="", bg=COLOR_BOX_BG, border=COLOR_BORDER, title_color=COLOR_PRIMARY):
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.4,rounding_size=0.6", linewidth=1.5, edgecolor=border, facecolor=bg
        )
        ax.add_patch(rect)
        if subtitle:
            ax.text(
                x + w / 2,
                y + h * 0.62,
                title,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color=title_color,
            )
            ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center", fontsize=7.2, color="#334155")
        else:
            ax.text(
                x + w / 2,
                y + h * 0.5,
                title,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color=title_color,
            )

    def draw_diamond(cx, cy, size, text, bg="#FEF3C7", border="#D97706"):
        pts = [(cx, cy + size), (cx + size * 1.3, cy), (cx, cy - size), (cx - size * 1.3, cy)]
        poly = patches.Polygon(pts, closed=True, linewidth=1.5, edgecolor=border, facecolor=bg)
        ax.add_patch(poly)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=8, fontweight="bold", color="#92400E")

    def draw_arrow(x1, y1, x2, y2, label="", color=COLOR_ACCENT, dashed=False):
        style = "Simple,tail_width=0.8,head_width=4,head_length=5"
        kw = dict(arrowstyle=style, color=color, lw=1.2)
        if dashed:
            kw["linestyle"] = "--"
        patch = patches.FancyArrowPatch((x1, y1), (x2, y2), **kw)
        ax.add_patch(patch)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my + 1.5, label, fontsize=7.5, fontweight="bold", color=color, ha="center")

    # Boundary Layer 1: Prompt Injection Defense
    ax.text(
        50,
        85,
        "LAYER 1: DATA-ONLY BOUNDARY ISOLATION (ANTI-PROMPT INJECTION)",
        ha="center",
        fontsize=10,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )
    draw_box(
        4,
        70,
        28,
        11,
        "Citizen Query / Upload",
        "Untrusted User Input\nDirect Injection Defense\nIsolated as Raw Parameter",
        bg="#FEF2F2",
        border=COLOR_DANGER,
        title_color=COLOR_DANGER,
    )
    draw_box(
        36,
        70,
        28,
        11,
        "Retrieved Evidence Text",
        "Tier A & B Statutory Passages\nEpistemic Authority != Instruction Trust\nEnclosed in <evidence_data> Tags",
        bg="#FEF9C3",
        border="#CA8A04",
        title_color="#A16207",
    )
    draw_box(
        68,
        70,
        28,
        11,
        "Immutable System Persona",
        "Fixed System Instructions\nStrict JSON/Pydantic Output Schemas\nIgnore Injected Override Directives",
        bg="#F0FDF4",
        border=COLOR_SUCCESS,
        title_color=COLOR_SUCCESS,
    )

    draw_arrow(32, 75.5, 36, 75.5)
    draw_arrow(64, 75.5, 68, 75.5)

    # Layer 2: Sufficiency & Entailment
    ax.text(
        50,
        61,
        "LAYER 2: SOURCE SUFFICIENCY & CLAIM-LEVEL ENTAILMENT",
        ha="center",
        fontsize=10,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )
    draw_diamond(25, 48, 3.8, "Source\nSufficient?", bg="#FEF3C7", border="#D97706")
    draw_box(
        45,
        43,
        22,
        10,
        "Atomic Claim Splitter",
        "Deconstructs Brief Draft\ninto Atomic Propositions\nClassifies Operative vs Contextual",
        bg="#EFF6FF",
        border=COLOR_ACCENT,
    )
    draw_diamond(82, 48, 3.8, "Claim\nEntailed?", bg="#FEF3C7", border="#D97706")

    draw_box(
        4,
        32,
        22,
        9,
        "Structured Abstention",
        "Missing Legal Dimension Notice\nClarification Prompt to User",
        bg="#FEE2E2",
        border=COLOR_DANGER,
        title_color=COLOR_DANGER,
    )

    draw_arrow(50, 70, 25, 52)
    draw_arrow(25, 44, 15, 41, label="No", color=COLOR_DANGER)
    draw_arrow(30, 48, 45, 48, label="Yes", color=COLOR_SUCCESS)
    draw_arrow(67, 48, 77, 48)

    # Layer 3: Invariant Normalization & Safe Regeneration
    ax.text(
        50,
        31,
        "LAYER 3: STRUCTURED INVARIANT AUDITING & SAFE RECOVERY",
        ha="center",
        fontsize=10,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )
    draw_box(
        4,
        14,
        25,
        11,
        "Bilingual Generation",
        "English Brief + Hindi Brief\nCSTT Official Terminology Map\nPreserve Statutory Identifiers",
        bg="#EFF6FF",
        border=COLOR_ACCENT,
    )
    draw_box(
        33,
        14,
        28,
        11,
        "Structured Invariant Engine",
        "Normalizes Fees (INR:10.00)\nDurations (30_DAYS, 48_HOURS)\nAuthorities (AUTH_ID:PIO, CPIO)",
        bg="#F0FDF4",
        border=COLOR_SUCCESS,
    )
    draw_diamond(73, 19.5, 3.8, "Invariants\nMatch?", bg="#FEF3C7", border="#D97706")
    draw_box(
        86, 14, 12, 11, "Final Brief", "Verified\nOutput", bg="#F0FDF4", border=COLOR_SUCCESS, title_color=COLOR_SUCCESS
    )

    draw_box(
        55,
        1,
        36,
        8,
        "Safe Recovery: Regen Once -> Abstain + Log",
        "No Silent Repair Policy | Creates Audit Incident Record",
        bg="#FEF2F2",
        border=COLOR_DANGER,
        title_color=COLOR_DANGER,
    )

    draw_arrow(82, 44, 17, 25, label="Pass Tier A")
    draw_arrow(87, 48, 87, 56, color=COLOR_WARN)
    draw_arrow(87, 56, 56, 53, label="Prune / Regen Once", color=COLOR_WARN)
    draw_arrow(29, 19.5, 33, 19.5)
    draw_arrow(61, 19.5, 68, 19.5)
    draw_arrow(78, 19.5, 86, 19.5, label="Match", color=COLOR_SUCCESS)
    draw_arrow(73, 15.5, 73, 9, label="Mismatch", color=COLOR_DANGER)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "diagram3_verification_and_safety.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Generated Diagram 3.")


def create_diagram_4():
    """Diagram 4: Implementation Roadmap & Testing Pyramid."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), dpi=300, gridspec_kw={"width_ratios": [1.2, 1]})
    fig.patch.set_facecolor(COLOR_BG)

    # AX1: Roadmap
    ax1.set_facecolor(COLOR_BG)
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    ax1.axis("off")
    ax1.text(
        50,
        96,
        "VeLiS-RAG Phased Implementation Roadmap",
        ha="center",
        fontsize=13,
        fontweight="bold",
        color=COLOR_PRIMARY,
    )

    phases = [
        (
            "Phase 0",
            "Foundations & Schemas",
            "Pydantic Models, Source Allowlist, 35 Tests (Verified w/ Fixes)",
            "#15803D",
            "#F0FDF4",
        ),
        (
            "Phase 1",
            "Curated Official Ingestion",
            "RTI Act/Rules, PM-KISAN, PM-JAY | Dual Hashing (Planned)",
            COLOR_PRIMARY,
            "#EFF6FF",
        ),
        (
            "Phase 2",
            "Baseline Hybrid Retrieval",
            "BM25Okapi + Qdrant Embedded + BGE-M3 Dense (Planned)",
            COLOR_PRIMARY,
            "#EFF6FF",
        ),
        (
            "Phase 3",
            "Verification & Guardrails",
            "Source Sufficiency + NLI Claim Entailment + Abstention (Planned)",
            COLOR_PRIMARY,
            "#EFF6FF",
        ),
        (
            "Phase 4",
            "Multilingual & Invariants",
            "Hindi Synthesis + CSTT Map + Invariant Comparison (Planned)",
            COLOR_PRIMARY,
            "#EFF6FF",
        ),
        (
            "Phase 5",
            "Held-Out Research Eval",
            "150-300 Held-Out Benchmark + Ablation Analysis (Planned)",
            COLOR_PRIMARY,
            "#EFF6FF",
        ),
        (
            "Phase 6",
            "Researcher Workbench",
            "FastAPI Inspection Console + Visual Citation Audit (Planned)",
            COLOR_PRIMARY,
            "#EFF6FF",
        ),
    ]

    y = 82
    for p_id, title, desc, border, bg in phases:
        rect = patches.FancyBboxPatch(
            (4, y), 92, 9, boxstyle="round,pad=0.3,rounding_size=0.5", linewidth=1.4, edgecolor=border, facecolor=bg
        )
        ax1.add_patch(rect)
        ax1.text(7, y + 5.5, p_id, fontsize=9.5, fontweight="bold", color=border)
        ax1.text(23, y + 5.5, title, fontsize=9.5, fontweight="bold", color=COLOR_TEXT)
        ax1.text(23, y + 2.2, desc, fontsize=7.5, color="#475569")
        if p_id != "Phase 6":
            ax1.annotate("", xy=(50, y - 1), xytext=(50, y), arrowprops=dict(arrowstyle="->", color=COLOR_BORDER, lw=1))
        y -= 12.5

    # AX2: Testing Pyramid
    ax2.set_facecolor(COLOR_BG)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.axis("off")
    ax2.text(
        50, 96, "VeLiS-RAG Multi-Tier Testing Pyramid", ha="center", fontsize=13, fontweight="bold", color=COLOR_PRIMARY
    )

    tiers = [
        ("Manual Legal Review (10 Gold Briefs)", 75, 87, 44, 12, "#FEF2F2", COLOR_DANGER),
        ("Adversarial & Injection Red-Teaming", 60, 72, 54, 12, "#FFFBEB", COLOR_WARN),
        ("Multilingual Invariant Consistency (100% Target)", 45, 57, 66, 12, "#EFF6FF", COLOR_ACCENT),
        ("Retrieval & Claim Entailment (Held-Out Benchmark)", 30, 42, 78, 12, "#EFF6FF", COLOR_PRIMARY),
        ("Deterministic Unit & Schema Tests (Property Fuzzing)", 15, 27, 90, 12, "#F0FDF4", COLOR_SUCCESS),
    ]

    for label, y_bot, _y_top, width, height, bg, border in tiers:
        x_left = (100 - width) / 2
        rect = patches.FancyBboxPatch(
            (x_left, y_bot),
            width,
            height,
            boxstyle="round,pad=0.2,rounding_size=0.4",
            linewidth=1.4,
            edgecolor=border,
            facecolor=bg,
        )
        ax2.add_patch(rect)
        ax2.text(50, y_bot + height / 2, label, ha="center", va="center", fontsize=8, fontweight="bold", color=border)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "diagram4_roadmap_pyramid.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Generated Diagram 4.")


if __name__ == "__main__":
    create_diagram_1()
    create_diagram_2()
    create_diagram_3()
    create_diagram_4()
    print("All 4 architecture diagrams generated successfully in docs/diagrams/.")

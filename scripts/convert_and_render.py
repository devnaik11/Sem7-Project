"""Convert DOCX to PDF using Word COM and render pages as images using PyMuPDF."""

import os
from pathlib import Path

import fitz  # PyMuPDF

DOCS_DIR = Path("docs")
DOCX_PATH = (DOCS_DIR / "VeLiS_RAG_Architecture_and_Implementation_Plan.docx").resolve()
PDF_PATH = (DOCS_DIR / "VeLiS_RAG_Architecture_and_Implementation_Plan.pdf").resolve()
PAGES_DIR = DOCS_DIR / "rendered_pages"
PAGES_DIR.mkdir(parents=True, exist_ok=True)


def convert_docx_to_pdf():
    # Use PowerShell Word COM for robust conversion
    cmd = f"""powershell -Command "$word = New-Object -ComObject Word.Application; $word.Visible = $false; $doc = $word.Documents.Open('{str(DOCX_PATH)}'); $doc.SaveAs('{str(PDF_PATH)}', 17); $doc.Close(); $word.Quit()" """
    ret = os.system(cmd)
    if ret != 0 or not PDF_PATH.exists():
        raise RuntimeError(f"Word COM conversion failed with return code {ret}")
    print(f"PDF successfully created at: {PDF_PATH}")


def render_pdf_to_images():
    doc = fitz.open(str(PDF_PATH))
    page_count = len(doc)
    print(f"Total PDF Page Count: {page_count}")
    image_paths = []
    for i, page in enumerate(doc):
        # 150 DPI rendering
        pix = page.get_pixmap(dpi=150)
        img_path = PAGES_DIR / f"page_{i + 1:02d}.png"
        pix.save(str(img_path))
        image_paths.append(img_path)
        print(f"Rendered Page {i + 1} -> {img_path.name}")
    return page_count, image_paths


if __name__ == "__main__":
    convert_docx_to_pdf()
    render_pdf_to_images()

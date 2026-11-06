from io import BytesIO
from pypdf import PdfReader
from docx import Document as DocxDocument
from .text_utils import clean_text

def extract_pages(filename: str, payload: bytes) -> list[tuple[int | None, str]]:
    """Extract page-aware PDF text, or a single text body for DOCX/TXT."""
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        reader = PdfReader(BytesIO(payload))
        pages = [(i + 1, clean_text(page.extract_text() or "")) for i, page in enumerate(reader.pages)]
        pages = [(number, text) for number, text in pages if text]
        if not pages:
            raise ValueError("PDF contains no extractable text (it may be empty or scanned).")
        return pages
    if suffix == "docx":
        doc = DocxDocument(BytesIO(payload))
        text = clean_text("\n".join(p.text for p in doc.paragraphs))
        if not text: raise ValueError("DOCX contains no extractable text.")
        return [(None, text)]
    if suffix == "txt":
        text = clean_text(payload.decode("utf-8-sig"))
        if not text: raise ValueError("Text file is empty.")
        return [(None, text)]
    raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")


import os

import fitz


class PDFExtractError(ValueError):
    """Raised when a PDF cannot be read or contains no extractable text."""


def extract_pdf(pdf_path):
    """Extract text from a PDF file.

    Always closes the document (no handle leaks), rejects encrypted
    files, and raises :class:`PDFExtractError` for missing/unreadable
    files or documents with no extractable text (e.g. scanned images
    without OCR).
    """
    if not pdf_path or not os.path.isfile(pdf_path):
        raise PDFExtractError(f"PDF file not found: {pdf_path}")
    if not str(pdf_path).lower().endswith(".pdf"):
        raise PDFExtractError("Only PDF files are supported")

    try:
        with fitz.open(pdf_path) as doc:
            if getattr(doc, "is_encrypted", False) or getattr(doc, "needs_pass", False):
                raise PDFExtractError("PDF is encrypted and cannot be read")
            if doc.page_count == 0:
                raise PDFExtractError("PDF has no pages")
            parts = []
            for page in doc:
                try:
                    parts.append(page.get_text() or "")
                except Exception:
                    parts.append("")
            text = "".join(parts).strip()
    except PDFExtractError:
        raise
    except Exception as e:
        raise PDFExtractError(f"Could not read PDF: {e}")

    if not text:
        raise PDFExtractError(
            "No extractable text found (scanned image PDF without OCR?)"
        )
    return text

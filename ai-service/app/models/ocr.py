# app/models/ocr.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the OCR /ocr/extract endpoint.
#
# WHY DOES THIS FILE EXIST?
#   Every API endpoint needs a defined "contract" — what does
#   the response JSON look like? Pydantic models enforce this
#   contract. If our code forgets to include 'ocrUsed', FastAPI
#   will raise an error BEFORE the response reaches the client.
#   This catches bugs at the server, not in the browser.
#
# HOW IS THIS DIFFERENT FROM models/extraction.py?
#   The OCR response includes extra fields that text extraction
#   doesn't need: ocrUsed, characterCount, processingTimeMs,
#   and language. Keeping separate models means neither response
#   has fields that don't make sense for it.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Literal


class OcrResponse(BaseModel):
    """
    JSON response returned by POST /ocr/extract.

    All fields are required. FastAPI validates the response
    against this schema before sending it to the client.
    """

    success: bool

    # What kind of file was uploaded?
    # Literal means only these exact string values are valid.
    documentType: Literal["pdf_searchable", "pdf_scanned", "jpg", "jpeg", "png"]

    # Was OCR actually used for this document?
    #   True  → scanned PDF or image file
    #   False → searchable PDF (text extracted directly, no OCR)
    ocrUsed: bool

    # For PDFs: actual number of pages
    # For images: always 1
    pageCount: int

    # Total words across all extracted text
    wordCount: int

    # Total characters (useful for billing, quality checks, etc.)
    characterCount: int

    # How long the extraction took in milliseconds.
    # OCR on a 50-page scanned PDF can take 30+ seconds.
    # This helps users understand why it's slow.
    processingTimeMs: int

    # Language detected / used for OCR.
    # For now: always "English" (Tesseract eng data).
    # Future: auto-detect with langdetect library.
    language: str

    # The full extracted text
    text: str


class OcrError(BaseModel):
    """Returned when OCR extraction fails."""
    success: bool = False
    error: str

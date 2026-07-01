# app/models/extraction.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the /extract-text endpoint.
#
# What is Pydantic?
#   FastAPI uses Pydantic models to:
#   1. VALIDATE incoming request data automatically
#   2. SERIALIZE outgoing response data to JSON
#   3. Generate the /docs Swagger UI schema
#
# You define the "shape" of data as a Python class.
# FastAPI does the rest — validation, error messages, docs.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Literal


class ExtractionResponse(BaseModel):
    """
    JSON response returned by POST /extract-text.

    All fields are required — FastAPI will raise a 500 if
    the service accidentally omits any of them.
    """

    success: bool

    # Literal restricts the value to exactly these three strings.
    # FastAPI will document this as an enum in /docs.
    documentType: Literal["pdf", "docx", "txt"]

    # pageCount:
    #   PDF  → actual number of pages in the document
    #   DOCX → number of paragraphs (Word has no hard "pages")
    #   TXT  → number of lines in the file
    pageCount: int

    # Total whitespace-delimited word count across all extracted text
    wordCount: int

    # The full extracted text as a single string.
    # Paragraphs/pages are separated by double newlines (\n\n).
    text: str


class ExtractionError(BaseModel):
    """Returned when extraction fails."""
    success: bool = False
    error: str

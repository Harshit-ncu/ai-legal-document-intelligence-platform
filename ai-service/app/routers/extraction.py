# app/routers/extraction.py
# ─────────────────────────────────────────────────────────
# FastAPI router for the /extract-text endpoint.
#
# This file's ONLY job is HTTP concerns:
#   - Receive the uploaded file
#   - Detect file type from extension + MIME type
#   - Save the file temporarily to disk
#   - Call the correct service function
#   - Clean up the temp file
#   - Return JSON (or a proper HTTP error)
#
# All actual parsing logic lives in app/services/extractor.py.
# ─────────────────────────────────────────────────────────

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.services.extractor import (
    extract_pdf_text,
    extract_docx_text,
    extract_txt_text,
)
from app.models.extraction import ExtractionResponse

# APIRouter is FastAPI's way of grouping related endpoints.
# The prefix and tags are applied to every route in this file.
# main.py mounts this router under a path prefix.
router = APIRouter(
    prefix="/extract",
    tags=["Text Extraction"],
)

# ── Allowed MIME types ─────────────────────────────────────
# Maps MIME type → (documentType label, extractor function)
SUPPORTED_TYPES: dict[str, tuple[str, callable]] = {
    "application/pdf": (
        "pdf",
        extract_pdf_text,
    ),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        "docx",
        extract_docx_text,
    ),
    "text/plain": (
        "txt",
        extract_txt_text,
    ),
}

# Fallback: detect by file extension if MIME type is generic
EXTENSION_MAP: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt":  "text/plain",
}


@router.post(
    "/text",
    response_model=ExtractionResponse,
    summary="Extract text from a legal document",
    description=(
        "Upload a PDF, DOCX, or TXT file and receive the extracted "
        "plain text along with word count, page count, and document type."
    ),
)
async def extract_text(
    file: UploadFile = File(
        ...,  # '...' means this field is required (no default)
        description="The document to extract text from (PDF, DOCX, or TXT)",
    ),
):
    """
    POST /extract/text

    Accepts: multipart/form-data with field name 'file'
    Returns: ExtractionResponse JSON
    """

    # ── Step 1: Detect file type ───────────────────────────
    # First try the Content-Type the client sent.
    # Then fall back to file extension (some clients send
    # 'application/octet-stream' for all uploads).
    content_type = file.content_type or ""
    file_extension = Path(file.filename or "").suffix.lower()

    # ── Validate the file extension first ────────────────────
    # We require the extension to be in our allowed set regardless
    # of what MIME type the client claims. This prevents a file
    # named 'contract.png' from slipping through just because
    # its extension can be mapped to a text type.
    if file_extension not in EXTENSION_MAP:
        raise HTTPException(
            status_code=415,
            detail={
                "success": False,
                "error": (
                    f"Unsupported file extension '{file_extension}'. "
                    "Only .pdf, .docx, and .txt files are accepted."
                ),
            },
        )

    # If the MIME type is generic (e.g. 'application/octet-stream'),
    # resolve it from the extension so we pick the right extractor.
    if content_type not in SUPPORTED_TYPES and file_extension in EXTENSION_MAP:
        content_type = EXTENSION_MAP[file_extension]

    if content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415,
            detail={
                "success": False,
                "error": (
                    f"Unsupported file type '{file.content_type}'. "
                    "Only PDF, DOCX, and TXT files are accepted."
                ),
            },
        )

    doc_type_label, extractor_fn = SUPPORTED_TYPES[content_type]

    # ── Step 2: Save to a temp file ────────────────────────
    # We must write to disk because PyMuPDF and python-docx
    # both need a real file path — they cannot stream from memory.
    #
    # tempfile.NamedTemporaryFile creates a uniquely-named temp file.
    # delete=False: we control deletion ourselves in the finally block.
    # suffix: preserves the file extension so libraries detect format.
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension or f".{doc_type_label}",
        ) as tmp:
            tmp_path = tmp.name
            # Read the uploaded file in chunks to handle large files
            # without loading the entire thing into memory at once.
            while chunk := await file.read(1024 * 64):  # 64 KB chunks
                tmp.write(chunk)

        # ── Step 3: Extract text ───────────────────────────
        # Call the appropriate extractor function.
        # It returns: { documentType, pageCount, wordCount, text }
        result = extractor_fn(tmp_path)

    except ValueError as e:
        # ValueError = we know what went wrong (bad file, empty PDF, etc.)
        raise HTTPException(status_code=422, detail={"success": False, "error": str(e)})

    except RuntimeError as e:
        # RuntimeError = unexpected parsing failure
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

    except Exception as e:
        # Catch-all for anything unexpected
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": f"Unexpected error: {str(e)}"},
        )

    finally:
        # ── Step 4: Always clean up the temp file ─────────
        # 'finally' runs whether or not an exception was raised.
        # This prevents temp files from piling up on the server.
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # ── Step 5: Return the response ────────────────────────
    # FastAPI validates this against ExtractionResponse automatically.
    return ExtractionResponse(
        success=True,
        documentType=result["documentType"],
        pageCount=result["pageCount"],
        wordCount=result["wordCount"],
        text=result["text"],
    )

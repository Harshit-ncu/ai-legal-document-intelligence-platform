# app/routers/ocr.py
# ─────────────────────────────────────────────────────────
# FastAPI router for POST /ocr/extract.
#
# WHY DOES THIS FILE EXIST?
#   This is the "door" to the OCR system. It handles everything
#   HTTP-related so the service and utilities don't have to:
#   - Receiving the uploaded file
#   - Validating the file extension
#   - Saving to a temp file on disk
#   - Calling the service
#   - Translating Python exceptions → proper HTTP status codes
#   - Cleaning up the temp file (always, even on errors)
#
# WHY SEPARATE FROM /extract/text (Module 2A)?
#   Module 2A handles native text files (PDF, DOCX, TXT).
#   Module 2B handles OCR inputs (images + scanned PDFs).
#   They have different response schemas, different validation,
#   different error types. Keeping them separate makes each
#   endpoint simpler and independently testable.
# ─────────────────────────────────────────────────────────

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services.ocr import process_document
from app.models.ocr import OcrResponse

router = APIRouter(
    prefix="/ocr",
    tags=["OCR — Scanned Document Extraction"],
)

# ── Supported file extensions for this endpoint ───────────
# Note: .pdf is intentionally allowed here too.
# The router doesn't know yet if it's searchable or scanned —
# detect_pdf_type() inside the service figures that out.
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# Human-readable label for error messages
ALLOWED_EXTENSIONS_STR = ".pdf, .jpg, .jpeg, .png"


@router.post(
    "/extract",
    response_model=OcrResponse,
    summary="Extract text using OCR (supports scanned documents and images)",
    description=(
        "Upload a scanned PDF, searchable PDF, JPG, JPEG, or PNG. "
        "Automatically detects whether the PDF is searchable or scanned. "
        "Returns extracted text with OCR metadata."
    ),
)
async def extract_with_ocr(
    file: UploadFile = File(
        ...,
        description="Document to process: .pdf (searchable or scanned), .jpg, .jpeg, or .png",
    ),
):
    """
    POST /ocr/extract

    Accepts: multipart/form-data, field name 'file'
    Returns: OcrResponse JSON
    """

    # ── Step 1: Validate file extension ───────────────────
    file_extension = Path(file.filename or "").suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={
                "success": False,
                "error": (
                    f"Unsupported file type '{file_extension}'. "
                    f"Accepted types: {ALLOWED_EXTENSIONS_STR}"
                ),
            },
        )

    # ── Step 2: Write upload to a temp file ───────────────
    # pytesseract, pdf2image, and Pillow all need a real file
    # path on disk — they cannot read from a network stream.
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
        ) as tmp:
            tmp_path = tmp.name
            # Stream in 64 KB chunks — avoids loading huge files
            # (e.g. a 50-page scanned PDF) entirely into RAM.
            while chunk := await file.read(1024 * 64):
                tmp.write(chunk)

        # ── Step 3: Run OCR pipeline ──────────────────────
        # process_document() handles detection + extraction + timing.
        # It raises ValueError or RuntimeError on failure.
        result = process_document(tmp_path, file_extension)

    # ── Error mapping ──────────────────────────────────────
    # Python exceptions → HTTP status codes
    #
    # 422 Unprocessable Entity:  we received the file but it's bad
    #   (corrupted, password-protected, empty, wrong format)
    #
    # 503 Service Unavailable:   our system is missing a tool
    #   (Tesseract or poppler not installed)
    #
    # 500 Internal Server Error: something unexpected happened
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(e)},
        )

    except RuntimeError as e:
        error_msg = str(e)
        # If the error is about missing system tools, use 503
        # (Service Unavailable) — the server isn't ready, not a bad request.
        if "not installed" in error_msg or "not in PATH" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": error_msg,
                },
            )
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": error_msg},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": f"Unexpected error: {str(e)}"},
        )

    finally:
        # ── Step 4: Always clean up the temp file ─────────
        # 'finally' runs whether an exception was raised or not.
        # Without this, failed OCR jobs leave temp files on disk
        # that accumulate and eventually fill up the server storage.
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # ── Step 5: Build and return the response ─────────────
    # FastAPI validates this against OcrResponse before sending.
    return OcrResponse(
        success=True,
        documentType=result["documentType"],
        ocrUsed=result["ocrUsed"],
        pageCount=result["pageCount"],
        wordCount=result["wordCount"],
        characterCount=result["characterCount"],
        processingTimeMs=result["processingTimeMs"],
        language=result["language"],
        text=result["text"],
    )

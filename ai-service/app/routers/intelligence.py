# app/routers/intelligence.py
# ─────────────────────────────────────────────────────────
# FastAPI router for the /intelligence/analyze endpoint.
#
# WHY DOES THIS FILE EXIST?
#   This is the entry point for Feature 4. It accepts an
#   uploaded file (PDF, DOCX, TXT, Image), saves it securely
#   to a temporary location, and calls the intelligence service.
#   It handles all HTTP layer errors and translates them to
#   proper status codes (400, 415, 422, 500).
# ─────────────────────────────────────────────────────────

import os
import tempfile
import logging
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services.intelligence import analyze_document
from app.models.intelligence import IntelligenceResponse

router = APIRouter(
    prefix="/intelligence",
    tags=["Document Intelligence"],
)

logger = logging.getLogger("document_intelligence.router")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"}


@router.post(
    "/analyze",
    response_model=IntelligenceResponse,
    summary="Analyze a document and extract structured intelligence",
    description="Upload any supported file type to extract cleaned text, statistics, language, and classification.",
)
async def analyze_document_route(
    file: UploadFile = File(..., description="Document to analyze")
):
    """
    POST /intelligence/analyze
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        logger.warning(f"Rejected unsupported file extension: {file_extension}")
        raise HTTPException(
            status_code=415,
            detail={
                "success": False,
                "error": f"Unsupported file extension '{file_extension}'."
            }
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
            tmp_path = tmp.name
            while chunk := await file.read(1024 * 64):
                tmp.write(chunk)

        # Delegate to the orchestration service
        result = analyze_document(tmp_path, file_extension, file.filename)
        
        return IntelligenceResponse(success=True, **result)

    except ValueError as e:
        logger.error(f"Validation error during processing: {e}")
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(e)}
        )
    except RuntimeError as e:
        logger.error(f"Runtime error during processing: {e}")
        # Map system issues (like missing Tesseract) to 503 Service Unavailable
        if "not installed" in str(e) or "not in PATH" in str(e):
            raise HTTPException(
                status_code=503,
                detail={"success": False, "error": str(e)}
            )
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": f"Unexpected error: {str(e)}"}
        )
    finally:
        # Always clean up temp files
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

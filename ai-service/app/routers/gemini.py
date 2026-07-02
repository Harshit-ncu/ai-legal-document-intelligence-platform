# app/routers/gemini.py
# ─────────────────────────────────────────────────────────
# FastAPI router for Gemini SDK infrastructure endpoints.
#
# ENDPOINTS:
#   POST /gemini/test        → Send a test prompt, get a response.
#   GET  /gemini/health      → Check Gemini connectivity (no credentials exposed).
#
# NOTE: /gemini/test is a DEVELOPMENT/VERIFICATION endpoint only.
#       It will be replaced by purpose-built endpoints (summarize, etc.)
#       as individual AI features are implemented in later modules.
# ─────────────────────────────────────────────────────────

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.gemini_service import generate_text, gemini_health_check

router = APIRouter(
    prefix="/gemini",
    tags=["Gemini AI"],
)

logger = logging.getLogger("gemini_service.router")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)


# ── Request / Response models ──────────────────────────────

class GeminiTestRequest(BaseModel):
    """Input schema for the test endpoint."""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Prompt to send to Gemini (2000 char max for test endpoint).",
        examples=["Hello, what is a non-disclosure agreement?"],
    )


class GeminiTestResponse(BaseModel):
    """Output schema for the test endpoint."""
    success: bool
    response: str


class GeminiHealthResponse(BaseModel):
    """Output schema for the health check endpoint."""
    available: bool
    model: str
    error: str | None = None


# ── Endpoints ─────────────────────────────────────────────

@router.post(
    "/test",
    response_model=GeminiTestResponse,
    summary="[DEV] Send a test prompt to Gemini",
    description=(
        "Development/verification endpoint. "
        "Sends a prompt to Gemini and returns the response. "
        "DO NOT use this to process real document text."
    ),
)
async def gemini_test(request: GeminiTestRequest):
    """
    POST /gemini/test

    Sends `prompt` to the Gemini API and returns the generated text.
    Validates that the SDK, credentials, and network are all configured correctly.
    """
    logger.info("POST /gemini/test — request received")

    try:
        text = generate_text(request.prompt)
        logger.info("POST /gemini/test — response generated successfully")
        return GeminiTestResponse(success=True, response=text)

    except RuntimeError as exc:
        logger.error("POST /gemini/test — Gemini error: %s", exc)

        # Map known failure types to appropriate HTTP codes
        msg = str(exc)
        if "not configured" in msg or "not initialised" in msg:
            raise HTTPException(status_code=503, detail={"success": False, "error": msg})
        if "invalid" in msg.lower() and "key" in msg.lower():
            raise HTTPException(status_code=401, detail={"success": False, "error": msg})
        if "rate limit" in msg.lower():
            raise HTTPException(status_code=429, detail={"success": False, "error": msg})

        raise HTTPException(status_code=502, detail={"success": False, "error": msg})


@router.get(
    "/health",
    response_model=GeminiHealthResponse,
    summary="Check Gemini API connectivity",
    description="Sends a minimal probe to verify the Gemini API is reachable. Never exposes credentials.",
)
async def gemini_health():
    """
    GET /gemini/health

    Returns whether the Gemini API is reachable and which model is active.
    Credentials are never included in the response.
    """
    logger.info("GET /gemini/health — checking connectivity")
    result = gemini_health_check()
    logger.info("GET /gemini/health — available=%s", result["available"])
    return GeminiHealthResponse(**result)

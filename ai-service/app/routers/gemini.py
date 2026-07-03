# app/routers/gemini.py
# ─────────────────────────────────────────────────────────
# FastAPI router for all Gemini AI endpoints.
#
# ENDPOINTS:
#   POST /gemini/summarize           → AI-powered legal document summarization.
#   POST /gemini/risk-analysis       → AI-powered legal risk and compliance analysis.
#   POST /gemini/clause-intelligence → AI-powered clause breakdown and recommendations.
#   POST /gemini/test                → [DEV] Send a test prompt, get a response.
#   GET  /gemini/health              → Check Gemini connectivity (no credentials exposed).
# ─────────────────────────────────────────────────────────

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.gemini_service import generate_text, gemini_health_check
from app.services.summarization_service import summarize_document
from app.models.summarization import SummarizeRequest, SummarizeResponse
from app.services.risk_analysis_service import analyze_document_risk
from app.models.risk_analysis import RiskAnalysisRequest, RiskAnalysisResponse
from app.services.clause_intelligence_service import analyze_clause_intelligence
from app.models.clause_intelligence import ClauseIntelligenceRequest, ClauseIntelligenceResponse

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


# ── Summarization Endpoint ─────────────────────────────────

def _map_runtime_error_to_http(exc: RuntimeError) -> HTTPException:
    """Convert a RuntimeError from the service layer to the correct HTTP status code."""
    msg = str(exc)
    if "not configured" in msg or "not initialised" in msg:
        return HTTPException(status_code=503, detail={"success": False, "error": msg})
    if "invalid" in msg.lower() and "key" in msg.lower():
        return HTTPException(status_code=401, detail={"success": False, "error": msg})
    if "rate limit" in msg.lower():
        return HTTPException(status_code=429, detail={"success": False, "error": msg})
    return HTTPException(status_code=502, detail={"success": False, "error": msg})


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize a legal document using Gemini AI",
    description=(
        "Accepts extracted document text and returns a structured AI summary including "
        "executive summary, key points, important clauses, obligations, risks, and "
        "suggested next actions. Uses Gemini 2.5 Pro exclusively."
    ),
)
async def summarize(request: SummarizeRequest):
    """
    POST /gemini/summarize

    Input:  { "text": "...", "documentType": "NDA" }
    Output: Structured JSON summary from Gemini 2.5 Pro.

    The document text should come from the /intelligence/analyze pipeline.
    This endpoint only performs AI summarization — extraction happens upstream.
    """
    logger.info(
        "POST /gemini/summarize — request received. document_type=%s text_length=%d",
        request.documentType,
        len(request.text),
    )

    try:
        result = summarize_document(
            text=request.text,
            document_type=request.documentType,
        )
        logger.info(
            "POST /gemini/summarize — completed. duration_ms=%d",
            result["processingTimeMs"],
        )
        return SummarizeResponse(success=True, **result)

    except ValueError as exc:
        # Validation errors: text too short, JSON parse failure, etc.
        logger.warning("POST /gemini/summarize — validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        )

    except RuntimeError as exc:
        # Gemini API errors: rate limit, bad key, server error, etc.
        logger.error("POST /gemini/summarize — Gemini error: %s", exc)
        raise _map_runtime_error_to_http(exc)


# ── Risk Analysis Endpoint ─────────────────────────────────

@router.post(
    "/risk-analysis",
    response_model=RiskAnalysisResponse,
    summary="Analyze a legal document for risks using Gemini AI",
    description=(
        "Accepts extracted document text and returns a structured AI risk analysis including "
        "overall risk score, specific risk factors, missing clauses, and obligations."
    ),
)
async def risk_analysis(request: RiskAnalysisRequest):
    """
    POST /gemini/risk-analysis

    Input:  { "text": "...", "documentType": "NDA" }
    Output: Structured JSON risk analysis from Gemini 2.5 Pro.
    """
    logger.info(
        "POST /gemini/risk-analysis — request received. document_type=%s text_length=%d",
        request.documentType,
        len(request.text),
    )

    try:
        result = analyze_document_risk(
            text=request.text,
            document_type=request.documentType,
        )
        logger.info(
            "POST /gemini/risk-analysis — completed. duration_ms=%d",
            result["processingTimeMs"],
        )
        return RiskAnalysisResponse(success=True, **result)

    except ValueError as exc:
        logger.warning("POST /gemini/risk-analysis — validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        )

    except RuntimeError as exc:
        logger.error("POST /gemini/risk-analysis — Gemini error: %s", exc)
        raise _map_runtime_error_to_http(exc)


# ── Clause Intelligence Endpoint ───────────────────────────

@router.post(
    "/clause-intelligence",
    response_model=ClauseIntelligenceResponse,
    summary="Analyze a specific legal clause using Gemini AI",
    description=(
        "Accepts a specific legal clause text and returns a highly detailed breakdown, "
        "including plain English translations, legal meaning, negotiation tips, "
        "and prioritized suggestions."
    ),
)
async def clause_intelligence(request: ClauseIntelligenceRequest):
    """
    POST /gemini/clause-intelligence

    Input:  { "clause": "...", "documentType": "NDA" }
    Output: Structured JSON clause analysis from Gemini 2.5 Pro.
    """
    logger.info(
        "POST /gemini/clause-intelligence — request received. document_type=%s clause_length=%d",
        request.documentType,
        len(request.clause),
    )

    try:
        result = analyze_clause_intelligence(
            text=request.clause,
            document_type=request.documentType,
        )
        logger.info(
            "POST /gemini/clause-intelligence — completed. duration_ms=%d",
            result["processingTimeMs"],
        )
        return ClauseIntelligenceResponse(success=True, **result)

    except ValueError as exc:
        logger.warning("POST /gemini/clause-intelligence — validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        )

    except RuntimeError as exc:
        logger.error("POST /gemini/clause-intelligence — Gemini error: %s", exc)
        raise _map_runtime_error_to_http(exc)

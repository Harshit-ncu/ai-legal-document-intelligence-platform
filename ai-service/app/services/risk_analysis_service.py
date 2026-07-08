# app/services/risk_analysis_service.py
# ─────────────────────────────────────────────────────────
# Legal Risk Analysis Service — Module 3.3
#
# RESPONSIBILITIES:
#   - Accept cleaned document text and document type.
#   - Build the legal risk prompt via risk_prompts.py.
#   - Call generate_text() from gemini_service.py.
#   - Parse and validate the structured JSON returned by Gemini.
#   - Return a clean Python dict matching the RiskAnalysisResponse schema.
#   - Handle every failure mode gracefully without crashing.
# ─────────────────────────────────────────────────────────

import json
import time
import logging

from app.services.gemini_service import generate_text
from app.utils.risk_prompts import build_risk_analysis_prompt

logger = logging.getLogger("risk_analysis_service")
logger.setLevel(logging.INFO)
logger.propagate = False  # records handled by this logger's own StreamHandler only
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# ── Constants ─────────────────────────────────────────────
RISK_MODEL = "gemini-2.5-pro"
MIN_TEXT_LENGTH = 50


def _parse_gemini_json(raw_text: str) -> dict:
    """Extract and parse the JSON object from Gemini's raw response text."""
    text = raw_text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned a response that could not be parsed as JSON. "
            f"First 200 chars: {raw_text[:200]!r}"
        ) from exc


def _validate_structure(data: dict) -> dict:
    """Validate that all required fields are present and fill defaults."""
    
    # Handle overall Risk and Score
    if "overallRisk" not in data or data["overallRisk"] not in ["Low", "Medium", "High"]:
        logger.warning("Invalid or missing 'overallRisk'. Defaulting to Medium.")
        data["overallRisk"] = "Medium"
        
    if "overallScore" not in data or not isinstance(data["overallScore"], int):
        logger.warning("Invalid or missing 'overallScore'. Defaulting to 50.")
        data["overallScore"] = 50
    else:
        # Clamp to 0-100
        data["overallScore"] = max(0, min(100, data["overallScore"]))

    # List defaults
    defaults = {
        "risks": [],
        "missingClauses": [],
        "obligations": [],
        "recommendations": ["No specific recommendations could be generated."],
    }

    for field, default in defaults.items():
        if field not in data or not isinstance(data[field], list):
            logger.warning("Gemini response missing or invalid field '%s'. Using default.", field)
            data[field] = default

    return data


def analyze_document_risk(text: str, document_type: str = "Unknown") -> dict:
    """
    Generate a structured legal risk analysis.

    Args:
        text:          The cleaned document text.
        document_type: Document classification label.

    Returns:
        dict containing all RiskAnalysisResponse fields (excluding 'success').

    Raises:
        ValueError: If the text is too short or the response cannot be parsed.
        RuntimeError: If the Gemini API call fails.
    """
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        raise ValueError(
            f"Document text is too short to analyze for risk "
            f"(minimum {MIN_TEXT_LENGTH} characters, got {len(text.strip())})."
        )

    start_time = time.perf_counter()

    logger.info(
        "Risk analysis started. document_type=%s text_length=%d model=%s",
        document_type,
        len(text),
        RISK_MODEL,
    )

    prompt = build_risk_analysis_prompt(text, document_type)
    raw_response = generate_text(prompt, model=RISK_MODEL)

    parsed = _parse_gemini_json(raw_response)
    validated = _validate_structure(parsed)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    logger.info(
        "Risk analysis completed. document_type=%s score=%d duration_ms=%d model=%s",
        document_type,
        validated["overallScore"],
        elapsed_ms,
        RISK_MODEL,
    )

    return {
        "overallRisk":        validated["overallRisk"],
        "overallScore":       validated["overallScore"],
        "risks":              validated["risks"],
        "missingClauses":     validated["missingClauses"],
        "obligations":        validated["obligations"],
        "recommendations":    validated["recommendations"],
        "processingTimeMs":   elapsed_ms,
        "modelUsed":          RISK_MODEL,
    }

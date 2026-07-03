# app/services/clause_intelligence_service.py
# ─────────────────────────────────────────────────────────
# Clause Intelligence Service — Module 3.4
#
# RESPONSIBILITIES:
#   - Accept extracted clause text and document type.
#   - Build the clause intelligence prompt via clause_prompts.py.
#   - Call generate_text() from gemini_service.py.
#   - Parse and validate the structured JSON returned by Gemini.
#   - Return a clean Python dict matching the ClauseIntelligenceResponse schema.
#   - Handle every failure mode gracefully without crashing.
# ─────────────────────────────────────────────────────────

import json
import time
import logging

from app.services.gemini_service import generate_text
from app.utils.clause_prompts import build_clause_intelligence_prompt

logger = logging.getLogger("clause_intelligence_service")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# ── Constants ─────────────────────────────────────────────
CLAUSE_MODEL = "gemini-2.5-pro"
MIN_TEXT_LENGTH = 10


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
    
    # Handle Risk Level
    if "riskLevel" not in data or data["riskLevel"] not in ["Low", "Medium", "High"]:
        logger.warning("Invalid or missing 'riskLevel'. Defaulting to Medium.")
        data["riskLevel"] = "Medium"
        
    # Handle Confidence Score
    if "confidence" not in data or not isinstance(data["confidence"], int):
        logger.warning("Invalid or missing 'confidence'. Defaulting to 50.")
        data["confidence"] = 50
    else:
        # Clamp to 0-100
        data["confidence"] = max(0, min(100, data["confidence"]))

    # Standard string fields
    string_fields = [
        "title",
        "plainEnglish",
        "legalMeaning",
        "businessImpact",
        "whyImportant",
        "industryBestPractice",
        "negotiationTip",
        "suggestedReplacementClause"
    ]
    
    for field in string_fields:
        if field not in data or not data[field]:
            logger.warning("Gemini response missing or invalid string field '%s'. Using default.", field)
            data[field] = "Not specified."

    # List fields
    list_fields = {
        "redFlags": [],
        "importantPoints": [],
        "suggestions": []
    }

    for field, default in list_fields.items():
        if field not in data or not isinstance(data[field], list):
            logger.warning("Gemini response missing or invalid list field '%s'. Using default.", field)
            data[field] = default

    return data


def analyze_clause_intelligence(text: str, document_type: str = "Unknown") -> dict:
    """
    Generate a structured legal clause intelligence analysis.

    Args:
        text:          The specific legal clause text.
        document_type: Document classification label.

    Returns:
        dict containing all ClauseIntelligenceResponse fields (excluding 'success').

    Raises:
        ValueError: If the text is too short or the response cannot be parsed.
        RuntimeError: If the Gemini API call fails.
    """
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        raise ValueError(
            f"Clause text is too short to analyze "
            f"(minimum {MIN_TEXT_LENGTH} characters, got {len(text.strip())})."
        )

    start_time = time.perf_counter()

    logger.info(
        "Clause intelligence started. document_type=%s text_length=%d model=%s",
        document_type,
        len(text),
        CLAUSE_MODEL,
    )

    prompt = build_clause_intelligence_prompt(text, document_type)
    raw_response = generate_text(prompt, model=CLAUSE_MODEL)

    parsed = _parse_gemini_json(raw_response)
    validated = _validate_structure(parsed)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    logger.info(
        "Clause intelligence completed. document_type=%s confidence=%d duration_ms=%d model=%s",
        document_type,
        validated["confidence"],
        elapsed_ms,
        CLAUSE_MODEL,
    )

    return {
        "title":                      validated["title"],
        "plainEnglish":               validated["plainEnglish"],
        "legalMeaning":               validated["legalMeaning"],
        "businessImpact":             validated["businessImpact"],
        "riskLevel":                  validated["riskLevel"],
        "whyImportant":               validated["whyImportant"],
        "industryBestPractice":       validated["industryBestPractice"],
        "negotiationTip":             validated["negotiationTip"],
        "suggestedReplacementClause": validated["suggestedReplacementClause"],
        "redFlags":                   validated["redFlags"],
        "importantPoints":            validated["importantPoints"],
        "suggestions":                validated["suggestions"],
        "confidence":                 validated["confidence"],
        "processingTimeMs":           elapsed_ms,
        "modelUsed":                  CLAUSE_MODEL,
    }

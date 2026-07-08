# app/services/summarization_service.py
# ─────────────────────────────────────────────────────────
# AI Summarization Service — Module 3.2
#
# RESPONSIBILITIES:
#   - Accept cleaned document text and document type.
#   - Build the legal-document prompt via summarization_prompts.py.
#   - Call generate_text() from gemini_service.py (the ONLY Gemini
#     interaction point in the entire codebase).
#   - Parse and validate the structured JSON returned by Gemini.
#   - Return a clean Python dict matching the SummarizeResponse schema.
#   - Handle every failure mode gracefully — never crash the server.
#
# WHAT THIS FILE DOES NOT DO:
#   - Does not touch the Gemini client directly.
#   - Does not accept files or paths (the router layer handles that).
#   - Does not log document text or sensitive content.
# ─────────────────────────────────────────────────────────

import json
import time
import logging

from app.services.gemini_service import generate_text, _DEFAULT_MODEL
from app.utils.summarization_prompts import build_summarization_prompt

# ── Logging ───────────────────────────────────────────────
logger = logging.getLogger("summarization_service")
logger.setLevel(logging.INFO)
logger.propagate = False  # records handled by this logger's own StreamHandler only
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# ── Constants ─────────────────────────────────────────────
# Gemini 2.5 Pro is the single authoritative model for all AI features.
SUMMARIZATION_MODEL = "gemini-2.5-pro"

# Minimum meaningful text length. Anything shorter cannot be reliably summarized.
MIN_TEXT_LENGTH = 50


def _parse_gemini_json(raw_text: str) -> dict:
    """
    Extract and parse the JSON object from Gemini's raw response text.

    Gemini sometimes wraps the JSON in markdown code fences even when
    instructed not to. This function handles that defensively.

    Args:
        raw_text: The raw string returned by generate_text().

    Returns:
        Parsed dict on success.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove the opening fence line (```json or ```)
        lines = lines[1:]
        # Remove the closing fence line if present
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
    """
    Validate that all required fields are present in the parsed JSON.
    Fills missing fields with safe defaults so the response always has the right shape.

    Args:
        data: The parsed dict from _parse_gemini_json().

    Returns:
        The dict with all required fields guaranteed to be present.
    """
    defaults = {
        "executiveSummary": "Unable to determine.",
        "keyPoints": ["Unable to determine."],
        "importantClauses": [{"title": "Unable to determine", "description": "Unable to determine."}],
        "obligations": [{"party": "Unable to determine", "obligation": "Unable to determine."}],
        "risks": [{"severity": "Low", "description": "Unable to determine."}],
        "suggestedNextActions": ["Unable to determine."],
    }

    for field, default in defaults.items():
        if field not in data or not data[field]:
            logger.warning("Gemini response missing field '%s'. Using default.", field)
            data[field] = default

    return data


def summarize_document(text: str, document_type: str = "Unknown") -> dict:
    """
    Generate a structured AI summary of a legal document.

    Args:
        text:          The cleaned document text (from intelligence pipeline).
        document_type: Document classification label (e.g. 'NDA', 'Lease').

    Returns:
        dict containing all SummarizeResponse fields (excluding 'success').

    Raises:
        ValueError: If the text is too short or the response cannot be parsed.
        RuntimeError: If the Gemini API call fails (propagated from gemini_service).
    """
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        raise ValueError(
            f"Document text is too short to summarize "
            f"(minimum {MIN_TEXT_LENGTH} characters, got {len(text.strip())})."
        )

    start_time = time.perf_counter()

    # Log metadata only — never the document text itself
    logger.info(
        "Summarization started. document_type=%s text_length=%d model=%s",
        document_type,
        len(text),
        SUMMARIZATION_MODEL,
    )

    # Build the prompt (pure function — no side effects)
    prompt = build_summarization_prompt(text, document_type)

    # The ONLY call to the Gemini layer — all Gemini interaction stays in gemini_service
    raw_response = generate_text(prompt, model=SUMMARIZATION_MODEL)

    # Parse and validate the response
    parsed = _parse_gemini_json(raw_response)
    validated = _validate_structure(parsed)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    logger.info(
        "Summarization completed. document_type=%s duration_ms=%d model=%s",
        document_type,
        elapsed_ms,
        SUMMARIZATION_MODEL,
    )

    return {
        "executiveSummary":   validated["executiveSummary"],
        "keyPoints":          validated["keyPoints"],
        "importantClauses":   validated["importantClauses"],
        "obligations":        validated["obligations"],
        "risks":              validated["risks"],
        "suggestedNextActions": validated["suggestedNextActions"],
        "processingTimeMs":   elapsed_ms,
        "modelUsed":          SUMMARIZATION_MODEL,
    }

# app/services/document_chat_service.py
# ─────────────────────────────────────────────────────────
# Verified AI Contract Assistant Service — Module 3.5
#
# RESPONSIBILITIES:
#   - Accept extracted document text, document type, and a user's question.
#   - Build the chat prompt via chat_prompts.py.
#   - Call generate_text() from gemini_service.py (no SDK duplication).
#   - Parse and validate the structured JSON returned by Gemini.
#   - Return a clean Python dict matching the DocumentChatResponse schema.
#   - Handle every failure mode gracefully without crashing.
# ─────────────────────────────────────────────────────────

import json
import time
import logging

from app.services.gemini_service import generate_text
from app.utils.chat_prompts import build_chat_prompt

logger = logging.getLogger("document_chat_service")
logger.setLevel(logging.INFO)
logger.propagate = False  # records handled by this logger's own StreamHandler only
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# ── Constants ─────────────────────────────────────────────
CHAT_MODEL = "gemini-2.5-pro"
MIN_TEXT_LENGTH = 50
MIN_QUESTION_LENGTH = 3

# Standard fallback answer when the document doesn't contain the information
UNKNOWN_ANSWER = "I cannot determine this from the provided document."


def _parse_gemini_json(raw_text: str) -> dict:
    """Extract and parse the JSON object from Gemini's raw response text."""
    text = raw_text.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
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


def _validate_source_references(refs: list) -> list:
    """Ensure each source reference has the required fields; drop malformed entries."""
    validated = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        validated.append(
            {
                "section": ref.get("section", "Unknown Section"),
                "clause":  ref.get("clause", "Unknown Clause"),
                "excerpt": ref.get("excerpt", "Not specified."),
            }
        )
    return validated


def _validate_structure(data: dict) -> dict:
    """Validate that all required fields are present and fill safe defaults."""

    # Confidence: must be an integer clamped to 0-100
    if "confidence" not in data or not isinstance(data["confidence"], int):
        logger.warning("Invalid or missing 'confidence'. Defaulting to 0.")
        data["confidence"] = 0
    else:
        data["confidence"] = max(0, min(100, data["confidence"]))

    # String fields — fall back to UNKNOWN_ANSWER to stay truthful
    for field in ("answer", "reasoning"):
        if field not in data or not str(data[field]).strip():
            logger.warning("Gemini response missing string field '%s'. Using safe default.", field)
            data[field] = UNKNOWN_ANSWER

    # sourceReferences: list of objects
    if "sourceReferences" not in data or not isinstance(data["sourceReferences"], list):
        logger.warning("Gemini response missing 'sourceReferences'. Using empty list.")
        data["sourceReferences"] = []
    else:
        data["sourceReferences"] = _validate_source_references(data["sourceReferences"])

    # limitations: list of strings
    if "limitations" not in data or not isinstance(data["limitations"], list):
        logger.warning("Gemini response missing 'limitations'. Using empty list.")
        data["limitations"] = []

    # followUpQuestions: list of strings
    if "followUpQuestions" not in data or not isinstance(data["followUpQuestions"], list):
        logger.warning("Gemini response missing 'followUpQuestions'. Using empty list.")
        data["followUpQuestions"] = []

    return data


def answer_document_question(text: str, document_type: str, question: str) -> dict:
    """
    Generate a structured answer to a user's question about a document.

    Args:
        text:          The extracted document text.
        document_type: Document classification label.
        question:      The user's natural language question.

    Returns:
        dict containing all DocumentChatResponse fields (excluding 'success').

    Raises:
        ValueError:   If text/question too short, or the response cannot be parsed.
        RuntimeError: If the Gemini API call fails (rate limit, auth, server error).
    """
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        raise ValueError(
            f"Document text is too short to query "
            f"(minimum {MIN_TEXT_LENGTH} characters, got {len(text.strip())})."
        )
    if not question or len(question.strip()) < MIN_QUESTION_LENGTH:
        raise ValueError(
            f"Question is too short (minimum {MIN_QUESTION_LENGTH} characters)."
        )

    start_time = time.perf_counter()

    # Log operational metadata only — never log document text or question body
    logger.info(
        "Document chat started. document_type=%s text_length=%d question_length=%d model=%s",
        document_type,
        len(text),
        len(question),
        CHAT_MODEL,
    )

    prompt = build_chat_prompt(text, document_type, question)
    raw_response = generate_text(prompt, model=CHAT_MODEL)

    parsed = _parse_gemini_json(raw_response)
    validated = _validate_structure(parsed)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    logger.info(
        "Document chat completed. document_type=%s confidence=%d duration_ms=%d model=%s",
        document_type,
        validated["confidence"],
        elapsed_ms,
        CHAT_MODEL,
    )

    return {
        "answer":             validated["answer"],
        "confidence":         validated["confidence"],
        "reasoning":          validated["reasoning"],
        "sourceReferences":   validated["sourceReferences"],
        "limitations":        validated["limitations"],
        "followUpQuestions":  validated["followUpQuestions"],
        "processingTimeMs":   elapsed_ms,
        "modelUsed":          CHAT_MODEL,
    }

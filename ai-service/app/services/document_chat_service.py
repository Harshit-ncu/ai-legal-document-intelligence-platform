# app/services/document_chat_service.py
# ─────────────────────────────────────────────────────────
# AI Contract Assistant Service — Module 3.5
#
# RESPONSIBILITIES:
#   - Accept extracted document text, document type, and a user's question.
#   - Build the chat prompt via chat_prompts.py.
#   - Call generate_text() from gemini_service.py.
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
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# ── Constants ─────────────────────────────────────────────
CHAT_MODEL = "gemini-2.5-pro"
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
    
    # Handle Confidence Score
    if "confidence" not in data or not isinstance(data["confidence"], int):
        logger.warning("Invalid or missing 'confidence'. Defaulting to 0.")
        data["confidence"] = 0
    else:
        # Clamp to 0-100
        data["confidence"] = max(0, min(100, data["confidence"]))

    # Standard string fields
    string_fields = ["answer", "reasoning"]
    for field in string_fields:
        if field not in data or not data[field]:
            logger.warning("Gemini response missing or invalid string field '%s'. Using default.", field)
            data[field] = "I cannot determine this from the provided document."

    # List fields
    list_fields = {
        "referencedSections": [],
        "limitations": []
    }
    for field, default in list_fields.items():
        if field not in data or not isinstance(data[field], list):
            logger.warning("Gemini response missing or invalid list field '%s'. Using default.", field)
            data[field] = default

    return data


def answer_document_question(text: str, document_type: str, question: str) -> dict:
    """
    Generate a structured legal answer to a user's question about a document.

    Args:
        text:          The document text.
        document_type: Document classification label.
        question:      The user's question.

    Returns:
        dict containing all DocumentChatResponse fields (excluding 'success').

    Raises:
        ValueError: If the text is too short or the response cannot be parsed.
        RuntimeError: If the Gemini API call fails.
    """
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        raise ValueError(
            f"Document text is too short to query "
            f"(minimum {MIN_TEXT_LENGTH} characters, got {len(text.strip())})."
        )
    if not question or len(question.strip()) < 3:
        raise ValueError("Question is too short.")

    start_time = time.perf_counter()

    # DO NOT log the actual document text or full question in production if they are sensitive
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
        "referencedSections": validated["referencedSections"],
        "limitations":        validated["limitations"],
        "processingTimeMs":   elapsed_ms,
        "modelUsed":          CHAT_MODEL,
    }

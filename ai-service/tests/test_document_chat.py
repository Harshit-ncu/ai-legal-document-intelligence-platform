# tests/test_document_chat.py
# ─────────────────────────────────────────────────────────
# Comprehensive unit tests for Module 3.5 – Verified AI Contract Assistant.
# All Gemini API calls are fully mocked. No network calls made.
# ─────────────────────────────────────────────────────────

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.utils.chat_prompts import build_chat_prompt, MAX_DOCUMENT_CHARS
from app.services.document_chat_service import (
    answer_document_question,
    _parse_gemini_json,
    _validate_structure,
    _validate_source_references,
    CHAT_MODEL,
    UNKNOWN_ANSWER,
)
from main import app

client = TestClient(app)

# ── Test fixtures ─────────────────────────────────────────

VALID_DOC_TEXT = (
    "This Non-Disclosure Agreement (NDA) is entered into between Alice Corp (Disclosing Party) "
    "and Bob Ltd (Receiving Party). Clause 9 – Termination: Either party may terminate this "
    "agreement with 30 days written notice. Clause 10 – Governing Law: This agreement is "
    "governed by the laws of England and Wales."
)

VALID_QUESTION = "Who are the parties to this agreement?"

VALID_GEMINI_JSON = {
    "answer": "The parties are Alice Corp (Disclosing Party) and Bob Ltd (Receiving Party).",
    "confidence": 99,
    "reasoning": "The introduction of the NDA explicitly names both parties.",
    "sourceReferences": [
        {
            "section": "Introduction",
            "clause": "Clause 1",
            "excerpt": "Alice Corp (Disclosing Party) and Bob Ltd (Receiving Party)",
        }
    ],
    "limitations": [],
    "followUpQuestions": [
        "What are the obligations of the Receiving Party?",
        "How long does this NDA last?",
        "Under what law is this NDA governed?",
    ],
}

UNKNOWN_ANSWER_JSON = {
    "answer": UNKNOWN_ANSWER,
    "confidence": 100,
    "reasoning": "Payment terms are not mentioned anywhere in the provided document.",
    "sourceReferences": [],
    "limitations": ["This NDA may reference external agreements not provided."],
    "followUpQuestions": [
        "What termination rights exist?",
        "Who owns intellectual property under this agreement?",
    ],
}


def _raw(data: dict) -> str:
    return json.dumps(data)


# ── SECTION A: Prompt Builder ──────────────────────────────

class TestBuildChatPrompt:
    def test_includes_document_type(self):
        prompt = build_chat_prompt(VALID_DOC_TEXT, "Lease", VALID_QUESTION)
        assert "Lease" in prompt

    def test_includes_question(self):
        prompt = build_chat_prompt(VALID_DOC_TEXT, "NDA", VALID_QUESTION)
        assert VALID_QUESTION in prompt

    def test_includes_anti_hallucination_rules(self):
        prompt = build_chat_prompt(VALID_DOC_TEXT, "NDA", VALID_QUESTION)
        assert "Never invent" in prompt or "never invent" in prompt.lower()
        assert "cannot determine" in prompt

    def test_truncates_very_long_document(self):
        long_text = "A" * (MAX_DOCUMENT_CHARS + 500)
        prompt = build_chat_prompt(long_text, "Contract", VALID_QUESTION)
        assert "A" * MAX_DOCUMENT_CHARS in prompt
        assert "A" * (MAX_DOCUMENT_CHARS + 1) not in prompt
        assert "truncated" in prompt.lower()

    def test_no_truncation_note_for_short_documents(self):
        prompt = build_chat_prompt("Short doc text for testing", "NDA", VALID_QUESTION)
        assert "truncated" not in prompt.lower()


# ── SECTION B: JSON Parser ────────────────────────────────

class TestParseGeminiJson:
    def test_parses_clean_json(self):
        raw = json.dumps({"confidence": 80})
        assert _parse_gemini_json(raw) == {"confidence": 80}

    def test_strips_json_markdown_fence(self):
        raw = "```json\n{\"answer\": \"yes\"}\n```"
        assert _parse_gemini_json(raw) == {"answer": "yes"}

    def test_strips_plain_markdown_fence(self):
        raw = "```\n{\"answer\": \"yes\"}\n```"
        assert _parse_gemini_json(raw) == {"answer": "yes"}

    def test_raises_value_error_on_invalid_json(self):
        with pytest.raises(ValueError, match="could not be parsed"):
            _parse_gemini_json("This is not JSON at all.")

    def test_raises_value_error_on_empty_response(self):
        with pytest.raises(ValueError):
            _parse_gemini_json("   ")


# ── SECTION C: Source Reference Validator ─────────────────

class TestValidateSourceReferences:
    def test_returns_valid_refs_unchanged(self):
        refs = [{"section": "Termination", "clause": "Clause 9", "excerpt": "30 days notice."}]
        result = _validate_source_references(refs)
        assert len(result) == 1
        assert result[0]["section"] == "Termination"

    def test_fills_missing_fields_with_defaults(self):
        refs = [{"section": "IP Rights"}]  # missing clause and excerpt
        result = _validate_source_references(refs)
        assert result[0]["clause"] == "Unknown Clause"
        assert result[0]["excerpt"] == "Not specified."

    def test_drops_non_dict_entries(self):
        refs = ["not a dict", None, 123, {"section": "S", "clause": "C", "excerpt": "E"}]
        result = _validate_source_references(refs)
        assert len(result) == 1

    def test_empty_list_returns_empty_list(self):
        assert _validate_source_references([]) == []


# ── SECTION D: Structure Validator ────────────────────────

class TestValidateStructure:
    def test_returns_valid_data_unchanged(self):
        result = _validate_structure(dict(VALID_GEMINI_JSON))
        assert result["answer"] == VALID_GEMINI_JSON["answer"]
        assert result["confidence"] == 99

    def test_clamps_confidence_above_100(self):
        data = dict(VALID_GEMINI_JSON)
        data["confidence"] = 150
        result = _validate_structure(data)
        assert result["confidence"] == 100

    def test_clamps_confidence_below_0(self):
        data = dict(VALID_GEMINI_JSON)
        data["confidence"] = -10
        result = _validate_structure(data)
        assert result["confidence"] == 0

    def test_defaults_non_integer_confidence(self):
        data = {"confidence": "high"}
        result = _validate_structure(data)
        assert result["confidence"] == 0

    def test_fills_missing_answer_with_unknown_default(self):
        data = {"confidence": 50}
        result = _validate_structure(data)
        assert result["answer"] == UNKNOWN_ANSWER

    def test_fills_missing_reasoning_with_safe_default(self):
        data = {"confidence": 50}
        result = _validate_structure(data)
        assert result["reasoning"] == UNKNOWN_ANSWER

    def test_fills_missing_source_references(self):
        data = {"confidence": 50}
        result = _validate_structure(data)
        assert isinstance(result["sourceReferences"], list)
        assert result["sourceReferences"] == []

    def test_fills_missing_limitations(self):
        data = {"confidence": 50}
        result = _validate_structure(data)
        assert isinstance(result["limitations"], list)

    def test_fills_missing_follow_up_questions(self):
        data = {"confidence": 50}
        result = _validate_structure(data)
        assert isinstance(result["followUpQuestions"], list)


# ── SECTION E: Service Logic ──────────────────────────────

class TestAnswerDocumentQuestion:
    def test_happy_path_returns_all_fields(self):
        with patch("app.services.document_chat_service.generate_text", return_value=_raw(VALID_GEMINI_JSON)):
            result = answer_document_question(VALID_DOC_TEXT, "NDA", VALID_QUESTION)

        assert result["answer"] == VALID_GEMINI_JSON["answer"]
        assert result["confidence"] == 99
        assert result["modelUsed"] == CHAT_MODEL
        assert result["processingTimeMs"] >= 0
        assert len(result["sourceReferences"]) == 1
        assert result["sourceReferences"][0]["section"] == "Introduction"
        assert len(result["followUpQuestions"]) == 3

    def test_unknown_answer_path(self):
        with patch("app.services.document_chat_service.generate_text", return_value=_raw(UNKNOWN_ANSWER_JSON)):
            result = answer_document_question(VALID_DOC_TEXT, "NDA", "What are the payment terms?")

        assert UNKNOWN_ANSWER in result["answer"]
        assert result["sourceReferences"] == []

    def test_raises_value_error_for_short_document(self):
        with pytest.raises(ValueError, match="too short"):
            answer_document_question("Short", "NDA", VALID_QUESTION)

    def test_raises_value_error_for_short_question(self):
        with pytest.raises(ValueError, match="too short"):
            answer_document_question(VALID_DOC_TEXT, "NDA", "Hi")

    def test_raises_value_error_on_malformed_json(self):
        with patch("app.services.document_chat_service.generate_text", return_value="Not JSON"):
            with pytest.raises(ValueError, match="could not be parsed"):
                answer_document_question(VALID_DOC_TEXT, "NDA", VALID_QUESTION)

    def test_propagates_rate_limit_runtime_error(self):
        with patch(
            "app.services.document_chat_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded."),
        ):
            with pytest.raises(RuntimeError, match="rate limit"):
                answer_document_question(VALID_DOC_TEXT, "NDA", VALID_QUESTION)

    def test_propagates_unavailable_runtime_error(self):
        with patch(
            "app.services.document_chat_service.generate_text",
            side_effect=RuntimeError("Gemini client is not initialized. Service unavailable."),
        ):
            with pytest.raises(RuntimeError, match="unavailable"):
                answer_document_question(VALID_DOC_TEXT, "NDA", VALID_QUESTION)

    def test_processing_time_is_positive(self):
        with patch("app.services.document_chat_service.generate_text", return_value=_raw(VALID_GEMINI_JSON)):
            result = answer_document_question(VALID_DOC_TEXT, "NDA", VALID_QUESTION)
        assert result["processingTimeMs"] >= 0


# ── SECTION F: Endpoint POST /gemini/chat ────────────────

class TestDocumentChatEndpoint:
    def test_returns_200_with_full_schema_on_success(self):
        with patch("app.services.document_chat_service.generate_text", return_value=_raw(VALID_GEMINI_JSON)):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT,
                    "documentType": "NDA",
                    "question": VALID_QUESTION,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["answer"] == VALID_GEMINI_JSON["answer"]
        assert data["confidence"] == 99
        assert len(data["sourceReferences"]) == 1
        assert data["sourceReferences"][0]["section"] == "Introduction"
        assert len(data["followUpQuestions"]) == 3

    def test_returns_422_when_gemini_returns_non_json(self):
        with patch("app.services.document_chat_service.generate_text", return_value="Not JSON"):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT,
                    "documentType": "NDA",
                    "question": VALID_QUESTION,
                },
            )
        assert response.status_code == 422

    def test_returns_422_when_document_text_too_short(self):
        response = client.post(
            "/gemini/chat",
            json={
                "documentText": "short",
                "documentType": "NDA",
                "question": VALID_QUESTION,
            },
        )
        assert response.status_code == 422

    def test_returns_429_on_rate_limit(self):
        with patch(
            "app.services.document_chat_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded."),
        ):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT,
                    "documentType": "NDA",
                    "question": VALID_QUESTION,
                },
            )
        assert response.status_code == 429

    def test_returns_503_when_client_not_initialized(self):
        with patch(
            "app.services.document_chat_service.generate_text",
            side_effect=RuntimeError("Gemini client is not initialized. Service unavailable."),
        ):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT,
                    "documentType": "NDA",
                    "question": VALID_QUESTION,
                },
            )
        assert response.status_code == 503

    def test_returns_401_on_invalid_api_key(self):
        with patch(
            "app.services.document_chat_service.generate_text",
            side_effect=RuntimeError("Invalid API key. Gemini authentication failed."),
        ):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT,
                    "documentType": "NDA",
                    "question": VALID_QUESTION,
                },
            )
        assert response.status_code == 401

    def test_uses_default_document_type_when_not_provided(self):
        with patch("app.services.document_chat_service.generate_text", return_value=_raw(VALID_GEMINI_JSON)):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT,
                    "question": VALID_QUESTION,
                    # documentType omitted — defaults to "Unknown"
                },
            )
        assert response.status_code == 200

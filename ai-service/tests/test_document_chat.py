# tests/test_document_chat.py
# ─────────────────────────────────────────────────────────
# Comprehensive unit tests for Module 3.5 – AI Contract Assistant.
# All Gemini API calls are fully mocked.
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
    CHAT_MODEL,
)
from main import app

client = TestClient(app)

VALID_DOC_TEXT = "This NDA is between Alice and Bob. It expires in 5 years."
VALID_QUESTION = "Who are the parties?"

VALID_GEMINI_JSON = {
    "answer": "The parties are Alice and Bob.",
    "confidence": 99,
    "reasoning": "The document explicitly states 'This NDA is between Alice and Bob.'",
    "referencedSections": ["Introduction"],
    "limitations": []
}

UNKNOWN_GEMINI_JSON = {
    "answer": "I cannot determine this from the provided document.",
    "confidence": 100,
    "reasoning": "The payment terms are not mentioned in the provided text.",
    "referencedSections": [],
    "limitations": ["Assumes no other external agreements apply."]
}

def _make_mock_response(data: dict) -> str:
    return json.dumps(data)


# ── SECTION A: Prompt Builder ──────────────────────────────

class TestBuildChatPrompt:
    def test_includes_document_type_and_question(self):
        prompt = build_chat_prompt(VALID_DOC_TEXT, "Lease", "What is the rent?")
        assert "Lease" in prompt
        assert "What is the rent?" in prompt

    def test_truncates_long_text(self):
        long_text = "x" * (MAX_DOCUMENT_CHARS + 100)
        prompt = build_chat_prompt(long_text, "Contract", VALID_QUESTION)
        assert "x" * MAX_DOCUMENT_CHARS in prompt
        assert "x" * (MAX_DOCUMENT_CHARS + 1) not in prompt
        assert "truncated" in prompt.lower()


# ── SECTION B: JSON Parsing ──────────────────────────────

class TestParseGeminiJson:
    def test_parses_clean_json(self):
        raw = json.dumps({"confidence": 50})
        assert _parse_gemini_json(raw) == {"confidence": 50}

    def test_strips_markdown_code_fence(self):
        raw = "```json\n{\"key\": \"value\"}\n```"
        assert _parse_gemini_json(raw) == {"key": "value"}

    def test_raises_on_invalid_json(self):
        with pytest.raises(ValueError, match="could not be parsed"):
            _parse_gemini_json("Not JSON")


# ── SECTION C: Structure Validation ──────────────────────

class TestValidateStructure:
    def test_returns_data_unchanged_when_complete(self):
        result = _validate_structure(dict(VALID_GEMINI_JSON))
        assert result["answer"] == "The parties are Alice and Bob."
        assert result["confidence"] == 99

    def test_defaults_invalid_confidence(self):
        data = {"confidence": 150}
        result = _validate_structure(data)
        assert result["confidence"] == 100  # clamped to max 100
        
        data2 = {"confidence": "High"}
        result2 = _validate_structure(data2)
        assert result2["confidence"] == 0

    def test_fills_missing_strings_with_safe_defaults(self):
        data = {"confidence": 50}
        result = _validate_structure(data)
        assert result["answer"] == "I cannot determine this from the provided document."
        assert result["reasoning"] == "I cannot determine this from the provided document."
        
    def test_fills_missing_lists(self):
        data = {"confidence": 50}
        result = _validate_structure(data)
        assert isinstance(result["referencedSections"], list)
        assert isinstance(result["limitations"], list)


# ── SECTION D: Service Logic ─────────────────────────────

class TestAnswerDocumentQuestion:
    def test_happy_path_returns_all_fields(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.document_chat_service.generate_text", return_value=raw_json):
            result = answer_document_question(VALID_DOC_TEXT * 10, "NDA", VALID_QUESTION)

        assert result["answer"] == "The parties are Alice and Bob."
        assert result["confidence"] == 99
        assert result["modelUsed"] == CHAT_MODEL
        assert result["processingTimeMs"] >= 0
        
    def test_unknown_answer_path(self):
        raw_json = _make_mock_response(UNKNOWN_GEMINI_JSON)
        with patch("app.services.document_chat_service.generate_text", return_value=raw_json):
            result = answer_document_question(VALID_DOC_TEXT * 10, "NDA", "What is the rent?")

        assert "cannot determine" in result["answer"]

    def test_raises_for_short_text(self):
        with pytest.raises(ValueError, match="too short"):
            answer_document_question("Short", "NDA", VALID_QUESTION)
            
    def test_raises_for_short_question(self):
        with pytest.raises(ValueError, match="too short"):
            answer_document_question(VALID_DOC_TEXT * 10, "NDA", "Hi")

    def test_propagates_rate_limit(self):
        with patch(
            "app.services.document_chat_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded.")
        ):
            with pytest.raises(RuntimeError, match="rate limit"):
                answer_document_question(VALID_DOC_TEXT * 10, "NDA", VALID_QUESTION)


# ── SECTION E: Endpoint POST /gemini/chat ────────────────

class TestDocumentChatEndpoint:
    def test_returns_200_with_full_schema_on_success(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.document_chat_service.generate_text", return_value=raw_json):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT * 10, 
                    "documentType": "NDA",
                    "question": VALID_QUESTION
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["answer"] == "The parties are Alice and Bob."
        assert data["confidence"] == 99

    def test_returns_422_when_json_parsing_fails(self):
        with patch("app.services.document_chat_service.generate_text", return_value="Not JSON"):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT * 10, 
                    "documentType": "NDA",
                    "question": VALID_QUESTION
                }
            )
        assert response.status_code == 422

    def test_returns_429_on_rate_limit(self):
        with patch(
            "app.services.document_chat_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded.")
        ):
            response = client.post(
                "/gemini/chat",
                json={
                    "documentText": VALID_DOC_TEXT * 10, 
                    "documentType": "NDA",
                    "question": VALID_QUESTION
                }
            )
        assert response.status_code == 429

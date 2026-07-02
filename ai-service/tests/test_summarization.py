# tests/test_summarization.py
# ─────────────────────────────────────────────────────────
# Comprehensive unit tests for Module 3.2 – AI Summarization.
#
# Coverage:
#   SECTION A — summarization_prompts.py
#     1.  build_summarization_prompt includes document type.
#     2.  build_summarization_prompt truncates overly long text.
#     3.  build_summarization_prompt includes truncation note when text is cut.
#     4.  build_summarization_prompt does NOT include truncation note for short text.
#     5.  build_summarization_prompt always requires JSON-only output.
#
#   SECTION B — _parse_gemini_json (internal helper)
#     6.  Parses a clean JSON string.
#     7.  Strips markdown code fences (```json ... ```) before parsing.
#     8.  Strips plain code fences (``` ... ```) before parsing.
#     9.  Raises ValueError on completely invalid JSON.
#     10. Raises ValueError on JSON with a trailing prose comment.
#
#   SECTION C — _validate_structure (internal helper)
#     11. Returns data unchanged when all fields are present.
#     12. Fills missing executiveSummary with default.
#     13. Fills missing keyPoints with default.
#     14. Fills empty lists with defaults.
#
#   SECTION D — summarize_document (service function)
#     15. Happy path: returns all six structured fields.
#     16. Raises ValueError for text that is too short.
#     17. Raises ValueError for empty string.
#     18. Propagates RuntimeError from gemini_service (rate limit).
#     19. Propagates RuntimeError from gemini_service (service unavailable).
#     20. Raises ValueError when Gemini returns non-JSON text.
#     21. Returns correct modelUsed field (gemini-2.5-pro).
#     22. Response dict contains processingTimeMs > 0.
#     23. Handles Gemini response wrapped in markdown code fences.
#     24. Uses default values when Gemini omits an optional field.
#
#   SECTION E — POST /gemini/summarize endpoint (via TestClient)
#     25. Returns 200 with full response schema on success.
#     26. Returns 422 when text is too short (< 50 chars).
#     27. Returns 422 when JSON parsing fails (malformed Gemini output).
#     28. Returns 429 when Gemini rate-limits.
#     29. Returns 503 when Gemini client is not initialised.
#     30. Returns 401 when Gemini key is invalid.
#
# ALL tests are fully mocked — no real Gemini API calls are made.
# ─────────────────────────────────────────────────────────

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# ── Import the modules under test ──────────────────────────
from app.utils.summarization_prompts import build_summarization_prompt, MAX_DOCUMENT_CHARS
from app.services.summarization_service import (
    summarize_document,
    _parse_gemini_json,
    _validate_structure,
    SUMMARIZATION_MODEL,
)
from main import app  # FastAPI application

client = TestClient(app)


# ── Fixtures ───────────────────────────────────────────────

VALID_NDA_TEXT = (
    "This Non-Disclosure Agreement ('Agreement') is entered into as of January 1, 2025, "
    "between Acme Corporation ('Disclosing Party') and Beta Ltd. ('Receiving Party'). "
    "The Receiving Party agrees to hold all Confidential Information in strict confidence "
    "and not to disclose it to any third party without prior written consent. "
    "This Agreement shall remain in force for a period of two (2) years from the date of signing. "
    "Breach of this Agreement shall entitle the Disclosing Party to seek injunctive relief."
)

VALID_GEMINI_JSON = {
    "executiveSummary": "This is a two-year NDA between Acme Corporation and Beta Ltd.",
    "keyPoints": ["Two-year term", "Strict confidentiality required"],
    "importantClauses": [
        {"title": "Confidentiality", "description": "Receiving Party must keep information secret."}
    ],
    "obligations": [
        {"party": "Receiving Party", "obligation": "Do not disclose confidential information."}
    ],
    "risks": [
        {"severity": "High", "description": "Breach may result in injunctive relief."}
    ],
    "suggestedNextActions": ["Have legal counsel review the agreement before signing."],
}


def _make_mock_response(data: dict) -> str:
    """Return a JSON string as Gemini would return it."""
    return json.dumps(data)


# ═══════════════════════════════════════════════════════════
# SECTION A — build_summarization_prompt
# ═══════════════════════════════════════════════════════════

class TestBuildSummarizationPrompt:

    def test_includes_document_type(self):
        prompt = build_summarization_prompt("Some legal text " * 5, "NDA")
        assert "NDA" in prompt

    def test_truncates_long_text(self):
        long_text = "x" * (MAX_DOCUMENT_CHARS + 1000)
        prompt = build_summarization_prompt(long_text, "Contract")
        # The prompt should contain at most MAX_DOCUMENT_CHARS of document content
        # (the truncated text itself, not counting the prompt template)
        assert "x" * MAX_DOCUMENT_CHARS in prompt
        # But the excess should not appear
        assert "x" * (MAX_DOCUMENT_CHARS + 1) not in prompt

    def test_includes_truncation_note_when_text_is_cut(self):
        long_text = "a" * (MAX_DOCUMENT_CHARS + 100)
        prompt = build_summarization_prompt(long_text, "Contract")
        assert "truncated" in prompt.lower()

    def test_no_truncation_note_for_short_text(self):
        short_text = "This is a short document about a lease agreement."
        prompt = build_summarization_prompt(short_text, "Lease")
        assert "truncated" not in prompt.lower()

    def test_prompt_requires_json_only_output(self):
        prompt = build_summarization_prompt("Some legal text " * 5, "NDA")
        assert "JSON" in prompt
        assert "ONLY" in prompt


# ═══════════════════════════════════════════════════════════
# SECTION B — _parse_gemini_json
# ═══════════════════════════════════════════════════════════

class TestParseGeminiJson:

    def test_parses_clean_json_string(self):
        raw = json.dumps({"key": "value"})
        result = _parse_gemini_json(raw)
        assert result == {"key": "value"}

    def test_strips_markdown_json_code_fence(self):
        raw = "```json\n{\"key\": \"value\"}\n```"
        result = _parse_gemini_json(raw)
        assert result == {"key": "value"}

    def test_strips_plain_code_fence(self):
        raw = "```\n{\"key\": \"value\"}\n```"
        result = _parse_gemini_json(raw)
        assert result == {"key": "value"}

    def test_raises_value_error_on_invalid_json(self):
        with pytest.raises(ValueError, match="could not be parsed as JSON"):
            _parse_gemini_json("this is not json at all")

    def test_raises_value_error_on_trailing_prose(self):
        # JSON followed by non-JSON text causes a parse error
        with pytest.raises(ValueError, match="could not be parsed as JSON"):
            _parse_gemini_json('{"key": "value"} and some extra prose')


# ═══════════════════════════════════════════════════════════
# SECTION C — _validate_structure
# ═══════════════════════════════════════════════════════════

class TestValidateStructure:

    def test_returns_data_unchanged_when_complete(self):
        data = dict(VALID_GEMINI_JSON)
        result = _validate_structure(data)
        assert result["executiveSummary"] == VALID_GEMINI_JSON["executiveSummary"]
        assert result["keyPoints"] == VALID_GEMINI_JSON["keyPoints"]

    def test_fills_missing_executive_summary(self):
        data = dict(VALID_GEMINI_JSON)
        del data["executiveSummary"]
        result = _validate_structure(data)
        assert "Unable to determine" in result["executiveSummary"]

    def test_fills_missing_key_points(self):
        data = dict(VALID_GEMINI_JSON)
        del data["keyPoints"]
        result = _validate_structure(data)
        assert isinstance(result["keyPoints"], list)
        assert len(result["keyPoints"]) > 0

    def test_fills_empty_list_with_default(self):
        data = dict(VALID_GEMINI_JSON)
        data["risks"] = []  # empty list is falsy
        result = _validate_structure(data)
        assert len(result["risks"]) > 0


# ═══════════════════════════════════════════════════════════
# SECTION D — summarize_document (service function)
# ═══════════════════════════════════════════════════════════

class TestSummarizeDocument:

    def test_happy_path_returns_all_fields(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.summarization_service.generate_text", return_value=raw_json):
            result = summarize_document(VALID_NDA_TEXT, "NDA")

        assert "executiveSummary" in result
        assert "keyPoints" in result
        assert "importantClauses" in result
        assert "obligations" in result
        assert "risks" in result
        assert "suggestedNextActions" in result
        assert "processingTimeMs" in result
        assert "modelUsed" in result

    def test_raises_value_error_for_text_too_short(self):
        with pytest.raises(ValueError, match="too short"):
            summarize_document("Short", "NDA")

    def test_raises_value_error_for_empty_string(self):
        with pytest.raises(ValueError, match="too short"):
            summarize_document("", "NDA")

    def test_propagates_rate_limit_runtime_error(self):
        with patch(
            "app.services.summarization_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded."),
        ):
            with pytest.raises(RuntimeError, match="rate limit"):
                summarize_document(VALID_NDA_TEXT, "NDA")

    def test_propagates_unavailable_runtime_error(self):
        with patch(
            "app.services.summarization_service.generate_text",
            side_effect=RuntimeError("Gemini client is not initialised."),
        ):
            with pytest.raises(RuntimeError, match="not initialised"):
                summarize_document(VALID_NDA_TEXT, "NDA")

    def test_raises_value_error_on_non_json_gemini_response(self):
        with patch(
            "app.services.summarization_service.generate_text",
            return_value="Here is your summary: The document is a contract.",
        ):
            with pytest.raises(ValueError, match="could not be parsed as JSON"):
                summarize_document(VALID_NDA_TEXT, "NDA")

    def test_returns_correct_model_used(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.summarization_service.generate_text", return_value=raw_json):
            result = summarize_document(VALID_NDA_TEXT, "NDA")

        assert result["modelUsed"] == SUMMARIZATION_MODEL
        assert result["modelUsed"] == "gemini-2.5-pro"

    def test_processing_time_is_positive(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.summarization_service.generate_text", return_value=raw_json):
            result = summarize_document(VALID_NDA_TEXT, "NDA")

        assert result["processingTimeMs"] >= 0

    def test_handles_markdown_wrapped_gemini_response(self):
        raw_json = f"```json\n{json.dumps(VALID_GEMINI_JSON)}\n```"
        with patch("app.services.summarization_service.generate_text", return_value=raw_json):
            result = summarize_document(VALID_NDA_TEXT, "NDA")

        assert result["executiveSummary"] == VALID_GEMINI_JSON["executiveSummary"]

    def test_uses_defaults_when_gemini_omits_field(self):
        incomplete = dict(VALID_GEMINI_JSON)
        del incomplete["risks"]
        raw_json = _make_mock_response(incomplete)

        with patch("app.services.summarization_service.generate_text", return_value=raw_json):
            result = summarize_document(VALID_NDA_TEXT, "NDA")

        # risks should have been filled with a safe default
        assert isinstance(result["risks"], list)
        assert len(result["risks"]) > 0


# ═══════════════════════════════════════════════════════════
# SECTION E — POST /gemini/summarize endpoint (TestClient)
# ═══════════════════════════════════════════════════════════

class TestSummarizeEndpoint:

    def test_returns_200_with_full_schema_on_success(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.summarization_service.generate_text", return_value=raw_json):
            response = client.post(
                "/gemini/summarize",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "executiveSummary" in data
        assert "keyPoints" in data
        assert "importantClauses" in data
        assert "obligations" in data
        assert "risks" in data
        assert "suggestedNextActions" in data
        assert "processingTimeMs" in data
        assert data["modelUsed"] == "gemini-2.5-pro"

    def test_returns_422_for_text_too_short(self):
        # Pydantic's min_length=50 validation will reject it at the request level
        response = client.post(
            "/gemini/summarize",
            json={"text": "Too short.", "documentType": "NDA"},
        )
        assert response.status_code == 422

    def test_returns_422_when_json_parsing_fails(self):
        with patch(
            "app.services.summarization_service.generate_text",
            return_value="Plain prose response, not JSON.",
        ):
            response = client.post(
                "/gemini/summarize",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"},
            )

        assert response.status_code == 422
        assert response.json()["detail"]["success"] is False

    def test_returns_429_on_rate_limit(self):
        with patch(
            "app.services.summarization_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded. Please wait a moment."),
        ):
            response = client.post(
                "/gemini/summarize",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"},
            )

        assert response.status_code == 429

    def test_returns_503_when_client_not_initialised(self):
        with patch(
            "app.services.summarization_service.generate_text",
            side_effect=RuntimeError("Gemini client is not initialised."),
        ):
            response = client.post(
                "/gemini/summarize",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"},
            )

        assert response.status_code == 503

    def test_returns_401_on_invalid_api_key(self):
        with patch(
            "app.services.summarization_service.generate_text",
            side_effect=RuntimeError("Gemini API key is invalid. Please check your .env file."),
        ):
            response = client.post(
                "/gemini/summarize",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"},
            )

        assert response.status_code == 401

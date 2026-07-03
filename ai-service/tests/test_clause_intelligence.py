# tests/test_clause_intelligence.py
# ─────────────────────────────────────────────────────────
# Comprehensive unit tests for Module 3.4 – Clause Intelligence.
# All Gemini API calls are fully mocked.
# ─────────────────────────────────────────────────────────

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.utils.clause_prompts import build_clause_intelligence_prompt, MAX_CLAUSE_CHARS
from app.services.clause_intelligence_service import (
    analyze_clause_intelligence,
    _parse_gemini_json,
    _validate_structure,
    CLAUSE_MODEL,
)
from main import app

client = TestClient(app)

VALID_CLAUSE_TEXT = "The Receiving Party shall keep all Confidential Information strictly confidential and shall not disclose it."

VALID_GEMINI_JSON = {
    "title": "Confidentiality Obligation",
    "plainEnglish": "You must keep the information secret.",
    "legalMeaning": "Creates a binding obligation to prevent disclosure of defined confidential info.",
    "businessImpact": "Requires internal security measures to prevent leaks.",
    "riskLevel": "Medium",
    "whyImportant": "It protects trade secrets from competitors.",
    "industryBestPractice": "Include exceptions for legally compelled disclosures.",
    "negotiationTip": "Ensure the definition of confidential information isn't too broad.",
    "suggestedReplacementClause": "The Receiving Party shall maintain confidentiality, subject to standard exclusions.",
    "redFlags": ["Doesn't mention compelled disclosure"],
    "importantPoints": ["Creates strict liability"],
    "suggestions": [
        {
            "priority": "High",
            "title": "Add Exceptions",
            "reason": "Missing standard carve-outs.",
            "recommendedAction": "Negotiate standard exceptions to confidentiality."
        }
    ],
    "confidence": 95
}

def _make_mock_response(data: dict) -> str:
    return json.dumps(data)


# ── SECTION A: Prompt Builder ──────────────────────────────

class TestBuildClauseIntelligencePrompt:
    def test_includes_document_type(self):
        prompt = build_clause_intelligence_prompt(VALID_CLAUSE_TEXT, "Lease")
        assert "Lease" in prompt

    def test_truncates_long_text(self):
        long_text = "x" * (MAX_CLAUSE_CHARS + 100)
        prompt = build_clause_intelligence_prompt(long_text, "Contract")
        assert "x" * MAX_CLAUSE_CHARS in prompt
        assert "x" * (MAX_CLAUSE_CHARS + 1) not in prompt
        assert "truncated" in prompt.lower()


# ── SECTION B: JSON Parsing ──────────────────────────────

class TestParseGeminiJson:
    def test_parses_clean_json(self):
        raw = json.dumps({"riskLevel": "Low"})
        assert _parse_gemini_json(raw) == {"riskLevel": "Low"}

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
        assert result["riskLevel"] == "Medium"
        assert result["confidence"] == 95
        assert len(result["suggestions"]) == 1

    def test_defaults_invalid_risk_and_confidence(self):
        data = {"riskLevel": "Extreme", "confidence": 150}
        result = _validate_structure(data)
        assert result["riskLevel"] == "Medium"
        assert result["confidence"] == 100  # clamped to max 100

    def test_fills_missing_strings(self):
        data = {"riskLevel": "Low"}
        result = _validate_structure(data)
        assert result["title"] == "Not specified."
        assert result["plainEnglish"] == "Not specified."
        
    def test_fills_missing_lists(self):
        data = {"riskLevel": "Low"}
        result = _validate_structure(data)
        assert isinstance(result["redFlags"], list)
        assert isinstance(result["suggestions"], list)
        assert len(result["suggestions"]) == 0


# ── SECTION D: Service Logic ─────────────────────────────

class TestAnalyzeClauseIntelligence:
    def test_happy_path_returns_all_fields(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.clause_intelligence_service.generate_text", return_value=raw_json):
            result = analyze_clause_intelligence(VALID_CLAUSE_TEXT, "NDA")

        assert result["riskLevel"] == "Medium"
        assert result["confidence"] == 95
        assert result["modelUsed"] == CLAUSE_MODEL
        assert result["processingTimeMs"] >= 0

    def test_raises_for_short_text(self):
        with pytest.raises(ValueError, match="too short"):
            analyze_clause_intelligence("Short")

    def test_propagates_rate_limit(self):
        with patch(
            "app.services.clause_intelligence_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded.")
        ):
            with pytest.raises(RuntimeError, match="rate limit"):
                analyze_clause_intelligence(VALID_CLAUSE_TEXT, "NDA")


# ── SECTION E: Endpoint POST /gemini/clause-intelligence ─

class TestClauseIntelligenceEndpoint:
    def test_returns_200_with_full_schema_on_success(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.clause_intelligence_service.generate_text", return_value=raw_json):
            response = client.post(
                "/gemini/clause-intelligence",
                json={"clause": VALID_CLAUSE_TEXT, "documentType": "NDA"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["riskLevel"] == "Medium"
        assert data["confidence"] == 95
        assert len(data["suggestions"]) == 1

    def test_returns_422_when_json_parsing_fails(self):
        with patch("app.services.clause_intelligence_service.generate_text", return_value="Not JSON"):
            response = client.post(
                "/gemini/clause-intelligence",
                json={"clause": VALID_CLAUSE_TEXT, "documentType": "NDA"}
            )
        assert response.status_code == 422

    def test_returns_429_on_rate_limit(self):
        with patch(
            "app.services.clause_intelligence_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded.")
        ):
            response = client.post(
                "/gemini/clause-intelligence",
                json={"clause": VALID_CLAUSE_TEXT, "documentType": "NDA"}
            )
        assert response.status_code == 429

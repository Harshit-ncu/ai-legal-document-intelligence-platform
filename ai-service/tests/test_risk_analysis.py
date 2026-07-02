# tests/test_risk_analysis.py
# ─────────────────────────────────────────────────────────
# Comprehensive unit tests for Module 3.3 – Legal Risk Analysis.
# All Gemini API calls are fully mocked.
# ─────────────────────────────────────────────────────────

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.utils.risk_prompts import build_risk_analysis_prompt, MAX_DOCUMENT_CHARS
from app.services.risk_analysis_service import (
    analyze_document_risk,
    _parse_gemini_json,
    _validate_structure,
    RISK_MODEL,
)
from main import app

client = TestClient(app)

VALID_NDA_TEXT = "Sample NDA text for risk analysis testing." * 10

VALID_GEMINI_JSON = {
    "overallRisk": "Medium",
    "overallScore": 65,
    "risks": [
        {
            "title": "Unlimited Liability",
            "severity": "High",
            "category": "Liability",
            "description": "No cap on damages.",
            "recommendation": "Negotiate a liability cap."
        }
    ],
    "missingClauses": [
        {
            "name": "Dispute Resolution",
            "importance": "High",
            "reason": "Essential for resolving conflicts without immediate litigation."
        }
    ],
    "obligations": [
        {
            "party": "Receiving Party",
            "obligation": "Maintain confidentiality",
            "deadline": "5 years"
        }
    ],
    "recommendations": ["Review with external counsel."]
}

def _make_mock_response(data: dict) -> str:
    return json.dumps(data)


# ── SECTION A: Prompt Builder ──────────────────────────────

class TestBuildRiskAnalysisPrompt:
    def test_includes_document_type(self):
        prompt = build_risk_analysis_prompt(VALID_NDA_TEXT, "Lease")
        assert "Lease" in prompt

    def test_truncates_long_text(self):
        long_text = "x" * (MAX_DOCUMENT_CHARS + 100)
        prompt = build_risk_analysis_prompt(long_text, "Contract")
        assert "x" * MAX_DOCUMENT_CHARS in prompt
        assert "x" * (MAX_DOCUMENT_CHARS + 1) not in prompt
        assert "truncated" in prompt.lower()


# ── SECTION B: JSON Parsing ──────────────────────────────

class TestParseGeminiJson:
    def test_parses_clean_json(self):
        raw = json.dumps({"overallRisk": "Low"})
        assert _parse_gemini_json(raw) == {"overallRisk": "Low"}

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
        assert result["overallRisk"] == "Medium"
        assert result["overallScore"] == 65
        assert len(result["risks"]) == 1

    def test_defaults_invalid_risk_and_score(self):
        data = {"overallRisk": "Extreme", "overallScore": 150}
        result = _validate_structure(data)
        assert result["overallRisk"] == "Medium"
        assert result["overallScore"] == 100  # clamped to max 100

    def test_fills_missing_lists(self):
        data = {"overallRisk": "Low", "overallScore": 10}
        result = _validate_structure(data)
        assert isinstance(result["risks"], list)
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0


# ── SECTION D: Service Logic ─────────────────────────────

class TestAnalyzeDocumentRisk:
    def test_happy_path_returns_all_fields(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.risk_analysis_service.generate_text", return_value=raw_json):
            result = analyze_document_risk(VALID_NDA_TEXT, "NDA")

        assert result["overallRisk"] == "Medium"
        assert result["overallScore"] == 65
        assert result["modelUsed"] == RISK_MODEL
        assert result["processingTimeMs"] >= 0

    def test_raises_for_short_text(self):
        with pytest.raises(ValueError, match="too short"):
            analyze_document_risk("Short")

    def test_propagates_rate_limit(self):
        with patch(
            "app.services.risk_analysis_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded.")
        ):
            with pytest.raises(RuntimeError, match="rate limit"):
                analyze_document_risk(VALID_NDA_TEXT, "NDA")


# ── SECTION E: Endpoint POST /gemini/risk-analysis ───────

class TestRiskAnalysisEndpoint:
    def test_returns_200_with_full_schema_on_success(self):
        raw_json = _make_mock_response(VALID_GEMINI_JSON)
        with patch("app.services.risk_analysis_service.generate_text", return_value=raw_json):
            response = client.post(
                "/gemini/risk-analysis",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["overallRisk"] == "Medium"
        assert len(data["risks"]) == 1

    def test_returns_422_when_json_parsing_fails(self):
        with patch("app.services.risk_analysis_service.generate_text", return_value="Not JSON"):
            response = client.post(
                "/gemini/risk-analysis",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"}
            )
        assert response.status_code == 422

    def test_returns_429_on_rate_limit(self):
        with patch(
            "app.services.risk_analysis_service.generate_text",
            side_effect=RuntimeError("Gemini API rate limit exceeded.")
        ):
            response = client.post(
                "/gemini/risk-analysis",
                json={"text": VALID_NDA_TEXT, "documentType": "NDA"}
            )
        assert response.status_code == 429

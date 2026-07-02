# tests/test_gemini_service.py
# ─────────────────────────────────────────────────────────
# Unit tests for app/services/gemini_service.py
#
# ALL Gemini API calls are mocked — no real API calls are made.
# This keeps tests fast, deterministic, and free (no quota usage).
#
# Test coverage:
#   1. generate_text() returns text on a successful mock response.
#   2. generate_text() raises RuntimeError when client is None (no key).
#   3. generate_text() raises RuntimeError on a ClientError (bad key).
#   4. generate_text() raises RuntimeError on rate-limit (429).
#   5. generate_text() raises RuntimeError on a ServerError (5xx).
#   6. generate_text() raises RuntimeError on unexpected exceptions.
#   7. gemini_health_check() returns available=True on success.
#   8. gemini_health_check() returns available=False when client is None.
#   9. gemini_health_check() returns available=False when generate_text raises.
# ─────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch, MagicMock

import app.services.gemini_service as svc


# ── Helpers ───────────────────────────────────────────────

def _make_response(text: str) -> MagicMock:
    """Build a mock GenerateContentResponse object with a .text attribute."""
    mock_response = MagicMock()
    mock_response.text = text
    return mock_response


# ── generate_text tests ───────────────────────────────────

class TestGenerateText:

    def test_returns_generated_text_on_success(self):
        """Happy path: SDK returns a response, we return its .text."""
        mock_resp = _make_response("This is a test response from Gemini.")

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp

        with patch.object(svc, "_client", mock_client):
            result = svc.generate_text("Hello Gemini")

        assert result == "This is a test response from Gemini."
        mock_client.models.generate_content.assert_called_once()

    def test_raises_when_client_is_none(self):
        """If _client is None (no API key), raise RuntimeError immediately."""
        with patch.object(svc, "_client", None):
            with pytest.raises(RuntimeError, match="not initialised"):
                svc.generate_text("Hello")

    def test_raises_on_invalid_api_key(self):
        """ClientError containing 'API_KEY_INVALID' maps to a clear RuntimeError."""
        from google.genai import errors as genai_errors

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = genai_errors.ClientError(
            400,
            {"error": {"message": "API_KEY_INVALID: The API key is invalid.", "status": "INVALID_ARGUMENT"}},
        )

        with patch.object(svc, "_client", mock_client):
            with pytest.raises(RuntimeError, match="API key is invalid"):
                svc.generate_text("Hello")

    def test_raises_on_rate_limit(self):
        """ClientError containing 'RESOURCE_EXHAUSTED' maps to a rate-limit RuntimeError."""
        from google.genai import errors as genai_errors

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = genai_errors.ClientError(
            429,
            {"error": {"message": "RESOURCE_EXHAUSTED: Quota exceeded.", "status": "RESOURCE_EXHAUSTED"}},
        )

        with patch.object(svc, "_client", mock_client):
            with pytest.raises(RuntimeError, match="rate limit"):
                svc.generate_text("Hello")

    def test_raises_on_server_error(self):
        """ServerError (5xx) is wrapped in a RuntimeError."""
        from google.genai import errors as genai_errors

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = genai_errors.ServerError(
            500,
            {"error": {"message": "Internal server error.", "status": "INTERNAL"}},
        )

        with patch.object(svc, "_client", mock_client):
            with pytest.raises(RuntimeError, match="Gemini server error"):
                svc.generate_text("Hello")

    def test_raises_on_network_failure(self):
        """Any unexpected exception (e.g., ConnectionError) is wrapped."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = ConnectionError("Network unreachable")

        with patch.object(svc, "_client", mock_client):
            with pytest.raises(RuntimeError, match="Unexpected error"):
                svc.generate_text("Hello")

    def test_uses_custom_model_when_specified(self):
        """Passing a model argument overrides the default."""
        mock_resp = _make_response("custom model response")

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp

        with patch.object(svc, "_client", mock_client):
            result = svc.generate_text("Hello", model="gemini-2.0-flash")

        call_kwargs = mock_client.models.generate_content.call_args
        assert call_kwargs.kwargs["model"] == "gemini-2.0-flash"
        assert result == "custom model response"


# ── gemini_health_check tests ──────────────────────────────

class TestGeminiHealthCheck:

    def test_returns_available_true_when_gemini_responds(self):
        """Health check returns available=True when generate_text succeeds."""
        mock_resp = _make_response("OK")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp

        with patch.object(svc, "_client", mock_client):
            result = svc.gemini_health_check()

        assert result["available"] is True
        assert result["error"] is None
        assert "model" in result

    def test_returns_available_false_when_client_is_none(self):
        """Health check returns available=False when client was never created."""
        with patch.object(svc, "_client", None):
            result = svc.gemini_health_check()

        assert result["available"] is False
        assert "GEMINI_API_KEY" in result["error"]

    def test_returns_available_false_on_api_error(self):
        """Health check returns available=False when generate_text raises."""
        with patch.object(svc, "generate_text", side_effect=RuntimeError("API error")):
            with patch.object(svc, "_client", MagicMock()):
                result = svc.gemini_health_check()

        assert result["available"] is False
        assert "API error" in result["error"]

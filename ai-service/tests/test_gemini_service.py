# tests/test_gemini_service.py
# ─────────────────────────────────────────────────────────
# Unit tests for app/services/gemini_service.py
#
# ALL Groq API calls are mocked — no real API calls are made.
# This keeps tests fast, deterministic, and free (no quota usage).
#
# Test coverage:
#   1. generate_text() returns text on a successful mock response.
#   2. generate_text() raises RuntimeError when client is None (no key).
#   3. generate_text() raises RuntimeError on AuthenticationError (bad key).
#   4. generate_text() raises RuntimeError on RateLimitError (429).
#   5. generate_text() raises RuntimeError on APIStatusError (5xx).
#   6. generate_text() raises RuntimeError on unexpected exceptions.
#   7. generate_text() passes the correct model name to the SDK.
#   8. gemini_health_check() returns available=True on success.
#   9. gemini_health_check() returns available=False when client is None.
#  10. gemini_health_check() returns available=False when generate_text raises.
# ─────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch, MagicMock

import groq as groq_sdk
import app.services.gemini_service as svc


# ── Helpers ───────────────────────────────────────────────

def _make_groq_response(text: str) -> MagicMock:
    """
    Build a mock Groq ChatCompletion object that mirrors the real SDK shape:
      response.choices[0].message.content == text
    """
    mock_message = MagicMock()
    mock_message.content = text

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def _make_groq_client(response=None, side_effect=None) -> MagicMock:
    """
    Build a mock Groq client whose chat.completions.create() either
    returns `response` or raises `side_effect`.
    """
    mock_client = MagicMock(spec=groq_sdk.Groq)
    create = mock_client.chat.completions.create
    if side_effect is not None:
        create.side_effect = side_effect
    elif response is not None:
        create.return_value = response
    return mock_client


# ── generate_text tests ───────────────────────────────────

class TestGenerateText:

    def test_returns_generated_text_on_success(self):
        """Happy path: SDK returns a chat completion, we return its text."""
        mock_resp = _make_groq_response("This is a test response from Groq.")
        mock_client = _make_groq_client(response=mock_resp)

        with patch.object(svc, "_client", mock_client):
            result = svc.generate_text("Hello Groq")

        assert result == "This is a test response from Groq."
        mock_client.chat.completions.create.assert_called_once()

    def test_raises_when_client_is_none(self):
        """If _client is None (no API key), raise RuntimeError immediately."""
        with patch.object(svc, "_client", None):
            with pytest.raises(RuntimeError, match="not initialised"):
                svc.generate_text("Hello")

    def test_raises_on_invalid_api_key(self):
        """AuthenticationError (401) maps to a clear RuntimeError."""
        auth_error = groq_sdk.AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401),
            body={"error": {"message": "Invalid API Key", "type": "invalid_request_error"}},
        )
        mock_client = _make_groq_client(side_effect=auth_error)

        with patch.object(svc, "_client", mock_client):
            with pytest.raises(RuntimeError, match="API key is invalid"):
                svc.generate_text("Hello")

    def test_raises_on_rate_limit(self):
        """RateLimitError (429) maps to a rate-limit RuntimeError."""
        rate_error = groq_sdk.RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429, headers={}),
            body={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}},
        )
        mock_client = _make_groq_client(side_effect=rate_error)

        with patch.object(svc, "_client", mock_client):
            # After _MAX_RETRIES exhausted, should raise
            with pytest.raises(RuntimeError, match="rate limit"):
                svc.generate_text("Hello")

    def test_raises_on_server_error(self):
        """APIStatusError (5xx) is wrapped in a RuntimeError."""
        server_error = groq_sdk.APIStatusError(
            message="Internal server error",
            response=MagicMock(status_code=500),
            body={"error": {"message": "Internal server error", "type": "server_error"}},
        )
        mock_client = _make_groq_client(side_effect=server_error)

        with patch.object(svc, "_client", mock_client):
            with pytest.raises(RuntimeError, match="Groq API error"):
                svc.generate_text("Hello")

    def test_raises_on_network_failure(self):
        """Any unexpected exception is wrapped in a RuntimeError."""
        mock_client = _make_groq_client(side_effect=ConnectionError("Network unreachable"))

        with patch.object(svc, "_client", mock_client):
            with pytest.raises(RuntimeError, match="Unexpected error"):
                svc.generate_text("Hello")

    def test_uses_custom_model_when_specified(self):
        """Passing a model argument overrides the default."""
        mock_resp = _make_groq_response("custom model response")
        mock_client = _make_groq_client(response=mock_resp)

        with patch.object(svc, "_client", mock_client):
            result = svc.generate_text("Hello", model="llama-3.1-8b-instant")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "llama-3.1-8b-instant"
        assert result == "custom model response"


# ── gemini_health_check tests ──────────────────────────────

class TestGeminiHealthCheck:

    def test_returns_available_true_when_groq_responds(self):
        """Health check returns available=True when generate_text succeeds."""
        with patch.object(svc, "generate_text", return_value="OK"):
            with patch.object(svc, "_client", MagicMock()):
                result = svc.gemini_health_check()

        assert result["available"] is True
        assert result["error"] is None
        assert "model" in result

    def test_returns_available_false_when_client_is_none(self):
        """Health check returns available=False when client was never created."""
        with patch.object(svc, "_client", None):
            result = svc.gemini_health_check()

        assert result["available"] is False
        assert "GROQ_API_KEY" in result["error"]

    def test_returns_available_false_on_api_error(self):
        """Health check returns available=False when generate_text raises."""
        with patch.object(svc, "generate_text", side_effect=RuntimeError("API error")):
            with patch.object(svc, "_client", MagicMock()):
                result = svc.gemini_health_check()

        assert result["available"] is False
        assert "API error" in result["error"]

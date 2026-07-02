# app/services/gemini_service.py
# ─────────────────────────────────────────────────────────
# Gemini SDK Integration — Module 3, Section 3.1
#
# RESPONSIBILITIES:
#   - Load the Gemini API key securely from environment variables.
#   - Initialize the google-genai client once at module load.
#   - Expose generate_text() as a reusable, error-safe function.
#   - Expose gemini_health_check() to verify connectivity.
#
# WHAT THIS FILE DOES NOT DO:
#   - Does not implement summarization (that is Module 3.2).
#   - Does not log the API key or prompt contents.
#   - Does not expose the raw client outside this module.
# ─────────────────────────────────────────────────────────

import os
import time
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

# ── Logging ───────────────────────────────────────────────
# Use a dedicated logger so all Gemini log lines are clearly
# identifiable and can be filtered independently.
logger = logging.getLogger("gemini_service")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# ── Load environment variables ─────────────────────────────
# First try the root project .env (one level above ai-service/),
# then fall back to the local ai-service/.env.
_root_env = Path(__file__).resolve().parents[3] / ".env"
_local_env = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(dotenv_path=_root_env, override=False)   # root takes priority
load_dotenv(dotenv_path=_local_env, override=False)  # local as fallback

# ── API Key Validation ─────────────────────────────────────
_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

if not _API_KEY:
    # Log a clear startup warning — do not raise so the service still boots.
    # Individual calls to generate_text() will fail gracefully.
    logger.warning(
        "GEMINI_API_KEY is not set. "
        "Gemini features will be unavailable until the key is configured in .env"
    )

# ── Default model ──────────────────────────────────────────
# Read from env so it can be changed without touching code.
_DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Client singleton ───────────────────────────────────────
# Create the client once at module level (cheap object, thread-safe).
# If the key is None, the client object still exists but calls will fail —
# that error is handled inside generate_text().
_client: genai.Client | None = None

if _API_KEY:
    try:
        _client = genai.Client(api_key=_API_KEY)
        logger.info("Gemini client initialised successfully. Model: %s", _DEFAULT_MODEL)
    except Exception as exc:
        logger.error("Failed to initialise Gemini client: %s", exc)
        _client = None


# ── Public API ─────────────────────────────────────────────

def generate_text(prompt: str, model: str | None = None) -> str:
    """
    Send a prompt to the Gemini API and return the generated text.

    Args:
        prompt:  The text prompt to send to the model.
        model:   Optional model override (defaults to GEMINI_MODEL env var).

    Returns:
        The generated text string on success.

    Raises:
        RuntimeError: For any Gemini API or network error — the caller
                      should catch this and convert to an HTTP error.
    """
    if _client is None:
        raise RuntimeError(
            "Gemini client is not initialised. "
            "Ensure GEMINI_API_KEY is set in your .env file."
        )

    target_model = model or _DEFAULT_MODEL
    start_time = time.perf_counter()

    # Log request metadata — NEVER log the prompt itself because it
    # will contain confidential legal document text in production.
    logger.info("Gemini request started. model=%s", target_model)

    try:
        response = _client.models.generate_content(
            model=target_model,
            contents=prompt,
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Gemini request completed. model=%s duration_ms=%d", target_model, elapsed_ms
        )

        # google-genai returns a GenerateContentResponse object.
        # .text is a convenience property that concatenates all text parts.
        return response.text

    except genai_errors.ClientError as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        exc_str = str(exc)

        # 401 / invalid API key
        # google-genai 2.x format: "400 INVALID_ARGUMENT. {...API_KEY_INVALID...}"
        if "API_KEY_INVALID" in exc_str or "INVALID_ARGUMENT" in exc_str:
            logger.error("Gemini auth failure: invalid API key. duration_ms=%d", elapsed_ms)
            raise RuntimeError(
                "Gemini API key is invalid. Please check GEMINI_API_KEY in your .env file."
            ) from exc

        # 429 / rate limit
        # google-genai 2.x format: "429 RESOURCE_EXHAUSTED. {...}"
        if "RESOURCE_EXHAUSTED" in exc_str or "429" in exc_str:
            logger.warning("Gemini rate limit hit. duration_ms=%d", elapsed_ms)
            raise RuntimeError(
                "Gemini API rate limit exceeded. Please wait a moment before retrying."
            ) from exc

        # Other 4xx errors (bad request, unsupported model, etc.)
        logger.error("Gemini client error: %s duration_ms=%d", exc, elapsed_ms)
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    except genai_errors.ServerError as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        # google-genai 2.x format: "500 INTERNAL. {...}"
        logger.error("Gemini server error: %s duration_ms=%d", exc, elapsed_ms)
        raise RuntimeError(f"Gemini server error: {exc}") from exc

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        # Catch network timeouts, connection refused, etc.
        logger.error(
            "Unexpected Gemini error: %s (%s) duration_ms=%d",
            exc,
            type(exc).__name__,
            elapsed_ms,
        )
        raise RuntimeError(f"Unexpected error communicating with Gemini: {exc}") from exc


def gemini_health_check() -> dict:
    """
    Verify Gemini connectivity by sending a minimal harmless prompt.

    Returns a dict with:
        - available (bool): True if Gemini responded correctly.
        - model  (str):  The model that was used.
        - error  (str | None): Error description if unavailable.

    NOTE: This function does NOT expose the API key in its output.
    """
    if _client is None:
        return {
            "available": False,
            "model": _DEFAULT_MODEL,
            "error": "GEMINI_API_KEY is not configured.",
        }

    try:
        result = generate_text("Reply with the single word: OK", model=_DEFAULT_MODEL)
        return {
            "available": True,
            "model": _DEFAULT_MODEL,
            "error": None,
        }
    except RuntimeError as exc:
        return {
            "available": False,
            "model": _DEFAULT_MODEL,
            "error": str(exc),
        }

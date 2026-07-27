# app/services/gemini_service.py
# ─────────────────────────────────────────────────────────
# AI SDK Integration — powered by Groq
#
# RESPONSIBILITIES:
#   - Load the Groq API key securely from environment variables.
#   - Initialize the Groq client once at module load.
#   - Expose generate_text() as a reusable, error-safe function.
#   - Expose gemini_health_check() to verify connectivity.
#
# The public API (generate_text, gemini_health_check) is identical
# to the previous google-genai version so all callers are unchanged.
# ─────────────────────────────────────────────────────────

import os
import re
import time
import logging
from pathlib import Path

from dotenv import load_dotenv
import groq as groq_sdk

# ── Logging ───────────────────────────────────────────────
logger = logging.getLogger("gemini_service")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

# ── Load environment variables ─────────────────────────────
_root_env = Path(__file__).resolve().parents[3] / ".env"
_local_env = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(dotenv_path=_root_env, override=False)
load_dotenv(dotenv_path=_local_env, override=False)

# ── API Key ───────────────────────────────────────────────
# Accepts either GROQ_API_KEY (preferred) or the legacy GEMINI_API_KEY
# so Railway env vars work whichever name was used.
_API_KEY: str | None = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")

if not _API_KEY:
    logger.warning(
        "GROQ_API_KEY is not set. "
        "AI features will be unavailable until the key is configured."
    )

# ── Default model ──────────────────────────────────────────
# llama-3.3-70b-versatile is Groq's most capable free-tier model.
# Override with GROQ_MODEL or legacy GEMINI_MODEL env var.
_DEFAULT_MODEL: str = (
    os.getenv("GROQ_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "llama-3.3-70b-versatile"
)

# ── Client singleton ───────────────────────────────────────
_client: groq_sdk.Groq | None = None

if _API_KEY:
    try:
        _client = groq_sdk.Groq(api_key=_API_KEY)
        logger.info("Groq client initialised successfully. Model: %s", _DEFAULT_MODEL)
    except Exception as exc:
        logger.error("Failed to initialise Groq client: %s", exc)
        _client = None

# ── Retry configuration ────────────────────────────────────
# Retry only genuine per-minute RPM 429s, not daily quota exhaustion.
_MAX_RETRIES: int = 2
_RETRY_BASE_DELAY_S: float = 5.0


# ── Internal helpers ───────────────────────────────────────

def _extract_retry_after_groq(exc: groq_sdk.RateLimitError) -> float | None:
    """
    Extract the Retry-After value from a Groq RateLimitError.

    Groq includes the retry delay in the response headers as
    'retry-after' (seconds) or 'x-ratelimit-reset-requests'.
    Falls back to None if neither is present.
    """
    try:
        resp = getattr(exc, "response", None)
        if resp is not None:
            headers = dict(resp.headers)
            # Standard Retry-After header (value in seconds)
            ra = headers.get("retry-after") or headers.get("Retry-After")
            if ra:
                return float(ra)
            # Groq-specific: time until request quota resets (in seconds)
            xrr = headers.get("x-ratelimit-reset-requests")
            if xrr:
                # May be like "1s", "500ms", or a plain float string
                match = re.match(r"([0-9.]+)", str(xrr))
                if match:
                    return float(match.group(1))
    except Exception:
        pass
    return None


def _is_daily_quota_exhausted(exc: groq_sdk.RateLimitError) -> bool:
    """
    Distinguish between a temporary per-minute RPM rate limit (retryable)
    and a daily token/request quota exhaustion (not retryable until tomorrow).

    Groq error bodies for daily exhaustion typically contain phrases like
    'daily limit', 'tokens per day', or 'requests per day'.
    """
    try:
        body = str(getattr(exc, "body", "") or "")
        message = str(getattr(exc, "message", "") or "")
        combined = (body + message).lower()
        daily_signals = ["per day", "daily", "tokens_per_day", "requests_per_day"]
        return any(sig in combined for sig in daily_signals)
    except Exception:
        return False


# ── Public API ─────────────────────────────────────────────

def _call_with_retry(target_model: str, prompt: str) -> str:
    """
    Call the Groq Chat Completions API with selective retry on RPM 429s.

    Retry policy:
      - RETRIED:     per-minute rate limit (429, temporary)
      - NOT RETRIED: daily quota exhausted (429, resets tomorrow)
      - NOT RETRIED: 401 invalid key
      - NOT RETRIED: any other 4xx
      - NOT RETRIED: 5xx server errors
    """
    delay = _RETRY_BASE_DELAY_S
    last_exc: RuntimeError | None = None

    for attempt in range(1 + _MAX_RETRIES):
        try:
            completion = _client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,    # Lower temperature for more consistent legal analysis
                max_tokens=8192,
            )
            return completion.choices[0].message.content

        except groq_sdk.AuthenticationError as exc:
            # 401 — key is wrong or revoked
            logger.error(
                "Groq authentication failed. http_code=401 message=%s",
                getattr(exc, "message", str(exc)),
            )
            raise RuntimeError(
                f"Groq API key is invalid (HTTP 401). "
                f"Check GROQ_API_KEY in Railway environment variables. "
                f"Error: {getattr(exc, 'message', str(exc))}"
            ) from exc

        except groq_sdk.RateLimitError as exc:
            # 429 — could be per-minute RPM or daily quota
            if _is_daily_quota_exhausted(exc):
                logger.error(
                    "Groq daily quota exhausted (non-retryable). message=%s",
                    getattr(exc, "message", str(exc)),
                )
                raise RuntimeError(
                    f"Groq daily quota exhausted (HTTP 429). "
                    f"This resets at midnight UTC. "
                    f"Error: {getattr(exc, 'message', str(exc))}"
                ) from exc

            # Per-minute RPM limit — retryable
            retry_after = _extract_retry_after_groq(exc)
            wait = retry_after if retry_after is not None else delay

            if attempt < _MAX_RETRIES:
                logger.warning(
                    "Groq rate limit hit (attempt %d/%d). Retrying in %.1fs.",
                    attempt + 1, 1 + _MAX_RETRIES, wait,
                )
                time.sleep(wait)
                delay *= 2
                last_exc = RuntimeError(
                    f"Groq rate limit exceeded (HTTP 429). "
                    f"Retry-After: {wait:.1f}s. "
                    f"Error: {getattr(exc, 'message', str(exc))}"
                )
                last_exc.__cause__ = exc
                continue
            else:
                logger.warning("Groq rate limit retries exhausted.")
                raise RuntimeError(
                    f"Groq rate limit exceeded after {_MAX_RETRIES} retries (HTTP 429). "
                    f"Error: {getattr(exc, 'message', str(exc))}"
                ) from exc

        except groq_sdk.BadRequestError as exc:
            logger.error(
                "Groq bad request. http_code=400 message=%s",
                getattr(exc, "message", str(exc)),
            )
            raise RuntimeError(
                f"Groq bad request (HTTP 400): {getattr(exc, 'message', str(exc))}"
            ) from exc

        except groq_sdk.APIStatusError as exc:
            status_code = getattr(exc, "status_code", "unknown")
            logger.error(
                "Groq API error. http_code=%s message=%s",
                status_code, getattr(exc, "message", str(exc)),
            )
            raise RuntimeError(
                f"Groq API error (HTTP {status_code}): {getattr(exc, 'message', str(exc))}"
            ) from exc

        except groq_sdk.APIConnectionError as exc:
            logger.error("Groq connection error: %s", exc)
            raise RuntimeError(
                f"Could not connect to Groq API: {exc}"
            ) from exc

        except Exception as exc:
            logger.error(
                "Unexpected error communicating with Groq: %s: %s",
                type(exc).__name__, exc,
            )
            raise RuntimeError(
                f"Unexpected error communicating with Groq ({type(exc).__name__}): {exc}"
            ) from exc

    raise last_exc  # type: ignore[misc]


def generate_text(prompt: str, model: str | None = None) -> str:
    """
    Send a prompt to the Groq API and return the generated text.

    This is a drop-in replacement for the previous Google Gemini
    implementation. The function signature and behaviour are identical
    so all callers (summarization, risk analysis, clause intelligence,
    document chat) work without any changes.

    Args:
        prompt:  The text prompt to send to the model.
        model:   Optional model override (defaults to GROQ_MODEL env var
                 or 'llama-3.3-70b-versatile').

    Returns:
        The generated text string on success.

    Raises:
        RuntimeError: For any API or network error. The original Groq
                      exception is always available via __cause__.
    """
    if _client is None:
        raise RuntimeError(
            "Groq client is not initialised. "
            "Ensure GROQ_API_KEY is set in your environment variables."
        )

    target_model = model or _DEFAULT_MODEL
    start_time = time.perf_counter()

    logger.info("Groq request started. model=%s", target_model)

    try:
        text = _call_with_retry(target_model, prompt)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Groq request completed. model=%s duration_ms=%d",
            target_model, elapsed_ms,
        )
        return text

    except RuntimeError as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        cause = exc.__cause__
        http_code = getattr(cause, "status_code", "N/A")
        logger.error(
            "Groq request failed. model=%s duration_ms=%d http_code=%s error=%s",
            target_model, elapsed_ms, http_code, exc,
        )
        raise


def gemini_health_check() -> dict:
    """
    Verify Groq API connectivity by sending a minimal probe.

    Returns a dict with:
        - available (bool): True if Groq responded successfully.
        - model     (str):  The model that was tested.
        - error     (str | None): Error description if unavailable.

    The function name is kept as gemini_health_check for API compatibility
    with the router that imports it.
    """
    if _client is None:
        return {
            "available": False,
            "model": _DEFAULT_MODEL,
            "error": "GROQ_API_KEY is not configured.",
        }

    try:
        generate_text("Reply with the single word: OK", model=_DEFAULT_MODEL)
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

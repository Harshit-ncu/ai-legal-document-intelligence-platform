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
import re
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
logger.propagate = False  # records handled by this logger's own StreamHandler only
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


# ── Retry configuration ────────────────────────────────────
# Applied ONLY to genuine per-minute RPM rate limits (retryable 429).
# NEVER retried: 401 (invalid key), 400 (bad request), billing/daily
# quota exhaustion (429 with free_tier metrics and limit=0), 5xx errors.
_MAX_RETRIES: int = 2
_RETRY_BASE_DELAY_S: float = 1.0  # first wait; doubles each attempt


# ── Internal helpers ───────────────────────────────────────

def _extract_quota_violations(exc: genai_errors.APIError) -> list[dict]:
    """
    Parse the structured QuotaFailure details from a Google API error response.

    Returns a list of violation dicts, each containing:
      - quotaMetric: the quota identifier (e.g. generate_content_free_tier_requests)
      - quotaId:     the specific limit bucket (e.g. GenerateRequestsPerDayPerProjectPerModel-FreeTier)
      - model:       which model triggered the violation

    Returns an empty list if no quota details are present.
    """
    try:
        details_list = exc.details.get("error", {}).get("details", [])
        for detail in details_list:
            if detail.get("@type", "").endswith("QuotaFailure"):
                return detail.get("violations", [])
    except (AttributeError, TypeError, KeyError):
        pass
    return []


def _is_billing_quota_exhausted(exc: genai_errors.APIError) -> bool:
    """
    Return True when the 429 is a NON-RETRYABLE billing/daily quota exhaustion.

    Distinguishes between two very different 429 causes:

    1. RETRYABLE — per-minute RPM limit hit temporarily:
       Violations contain time-bounded quotaIds like:
         GenerateRequestsPerMinutePerProjectPerModel-FreeTier
       The 'limit' value in the message is > 0.
       These resolve after waiting the Retry-After delay.

    2. NOT RETRYABLE — daily or billing quota fully exhausted:
       Violations contain:
         GenerateRequestsPerDayPerProjectPerModel-FreeTier
         GenerateContentInputTokensPerModelPerMinute-FreeTier (with limit=0)
       The message says "limit: 0" which means the quota ceiling is zero —
       no amount of waiting will fix this until the billing period resets
       or a billing account is attached.

    Detection strategy: presence of "free_tier" in any quotaMetric AND
    "limit: 0" in the human-readable error message (which Google includes
    only when the ceiling itself is 0, not when temporarily depleted).
    """
    if exc.code != 429:
        return False

    message = exc.message or ""
    violations = _extract_quota_violations(exc)

    has_free_tier_metric = any(
        "free_tier" in v.get("quotaMetric", "") for v in violations
    )
    # "limit: 0" in the message means the quota ceiling is zero —
    # distinct from a temporary per-minute burst exceeded.
    has_zero_limit = "limit: 0" in message
    # Daily per-day exhaustion
    has_daily_violation = any(
        "PerDay" in v.get("quotaId", "") for v in violations
    )

    return has_free_tier_metric and (has_zero_limit or has_daily_violation)


def _extract_retry_after(exc: genai_errors.APIError) -> float | None:
    """
    Extract the suggested retry delay from the Google API error.

    Priority order:
      1. Structured RetryInfo detail block (most reliable).
      2. Human-readable "Please retry in Xs" suffix in the message.
      3. None — caller uses exponential backoff default.
    """
    # 1. Structured RetryInfo block in error.details
    try:
        details_list = exc.details.get("error", {}).get("details", [])
        for detail in details_list:
            if detail.get("@type", "").endswith("RetryInfo"):
                # retryDelay is a string like "18s" or "60s"
                delay_str = detail.get("retryDelay", "")
                match = re.match(r"^([0-9.]+)s?$", delay_str.strip())
                if match:
                    return float(match.group(1))
    except (AttributeError, TypeError, KeyError):
        pass

    # 2. Human-readable fallback: "Please retry in 18.62s"
    message = exc.message or ""
    match = re.search(r"retry in ([0-9.]+)s", message, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return None


def _build_error_context(exc: genai_errors.APIError) -> dict:
    """
    Build a structured diagnostic dict from an APIError for logging.
    Never includes the API key. Safe to log in production.
    """
    violations = _extract_quota_violations(exc)
    retry_after = _extract_retry_after(exc)

    return {
        "http_code":    exc.code,
        "google_status": exc.status,
        "message":      exc.message,
        "is_billing_exhaustion": _is_billing_quota_exhausted(exc),
        "retry_after_s": retry_after,
        "quota_violations": [
            {
                "metric": v.get("quotaMetric", ""),
                "quota_id": v.get("quotaId", ""),
                "model": v.get("quotaDimensions", {}).get("model", ""),
            }
            for v in violations
        ],
    }


# ── Public API ─────────────────────────────────────────────

def _call_with_retry(target_model: str, prompt: str) -> str:
    """
    Internal: call the Gemini API with selective retry on genuine RPM 429s.

    Retry policy:
      - RETRIED:     per-minute rate limit (429, free_tier metric, limit > 0)
      - NOT RETRIED: daily/billing quota exhausted (429, limit=0 or PerDay violation)
      - NOT RETRIED: 401 invalid key
      - NOT RETRIED: any 4xx other than 429
      - NOT RETRIED: 5xx server errors

    Preserves the full original Google exception as __cause__ on every
    RuntimeError raised, so callers and routers can inspect the original
    http_code, status, message, and details without losing information.
    """
    delay = _RETRY_BASE_DELAY_S
    last_exc: RuntimeError | None = None

    for attempt in range(1 + _MAX_RETRIES):  # attempt 0 is the first try
        try:
            response = _client.models.generate_content(
                model=target_model,
                contents=prompt,
            )
            return response.text

        except genai_errors.ClientError as exc:
            ctx = _build_error_context(exc)

            # ── 401 / invalid API key — not retryable ─────────────
            if exc.code == 401 or exc.status in ("UNAUTHENTICATED",) or "API_KEY_INVALID" in (exc.message or ""):
                logger.error(
                    "Gemini authentication failed. "
                    "http_code=%d google_status=%s message=%s",
                    ctx["http_code"], ctx["google_status"], ctx["message"],
                )
                raise RuntimeError(
                    f"Gemini API key is invalid (HTTP {exc.code} {exc.status}). "
                    f"Check GEMINI_API_KEY in your environment. "
                    f"Google error: {exc.message}"
                ) from exc

            # ── 429 / quota exceeded ───────────────────────────────
            if exc.code == 429:

                # Case A: billing/daily quota exhausted — NOT retryable
                if _is_billing_quota_exhausted(exc):
                    logger.error(
                        "Gemini quota exhausted (billing or daily limit). "
                        "http_code=%d google_status=%s retry_after_s=%s "
                        "violations=%s message=%s",
                        ctx["http_code"], ctx["google_status"],
                        ctx["retry_after_s"], ctx["quota_violations"],
                        ctx["message"],
                    )
                    raise RuntimeError(
                        f"Gemini free-tier quota exhausted (HTTP {exc.code} {exc.status}). "
                        f"This is a billing/daily limit, not a temporary rate limit. "
                        f"Enable billing at https://aistudio.google.com or wait for quota reset. "
                        f"Violated metrics: "
                        f"{[v['metric'] for v in ctx['quota_violations']]}. "
                        f"Google error: {exc.message}"
                    ) from exc

                # Case B: per-minute RPM limit — retryable with backoff
                retry_after = ctx["retry_after_s"]
                wait = retry_after if retry_after is not None else delay

                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "Gemini per-minute rate limit hit (attempt %d/%d). "
                        "http_code=%d retry_after_s=%.1f waiting=%.1fs "
                        "violations=%s",
                        attempt + 1, 1 + _MAX_RETRIES,
                        ctx["http_code"], wait, wait,
                        ctx["quota_violations"],
                    )
                    time.sleep(wait)
                    delay *= 2  # exponential backoff
                    last_exc = RuntimeError(
                        f"Gemini per-minute rate limit exceeded (HTTP {exc.code} {exc.status}). "
                        f"Retry-After: {wait:.1f}s. "
                        f"Google error: {exc.message}"
                    )
                    last_exc.__cause__ = exc
                    continue
                else:
                    logger.warning(
                        "Gemini rate limit retries exhausted. "
                        "http_code=%d retry_after_s=%s violations=%s",
                        ctx["http_code"], ctx["retry_after_s"],
                        ctx["quota_violations"],
                    )
                    raise RuntimeError(
                        f"Gemini per-minute rate limit exceeded after {_MAX_RETRIES} retries "
                        f"(HTTP {exc.code} {exc.status}). "
                        f"Retry-After: {wait:.1f}s. "
                        f"Google error: {exc.message}"
                    ) from exc

            # ── Other 4xx (400 INVALID_ARGUMENT, 403 PERMISSION_DENIED, etc.) ──
            logger.error(
                "Gemini client error (non-retryable). "
                "http_code=%d google_status=%s message=%s",
                ctx["http_code"], ctx["google_status"], ctx["message"],
            )
            raise RuntimeError(
                f"Gemini API error (HTTP {exc.code} {exc.status}): {exc.message}"
            ) from exc

        except genai_errors.ServerError as exc:
            # 5xx — not retried here (brief transient issues resolve quickly;
            # Railway's health checks will restart a crashed container).
            logger.error(
                "Gemini server error. http_code=%d google_status=%s message=%s",
                exc.code, exc.status, exc.message,
            )
            raise RuntimeError(
                f"Gemini server error (HTTP {exc.code} {exc.status}): {exc.message}"
            ) from exc

        except Exception as exc:
            logger.error(
                "Unexpected error communicating with Gemini: %s: %s",
                type(exc).__name__, exc,
            )
            raise RuntimeError(
                f"Unexpected error communicating with Gemini ({type(exc).__name__}): {exc}"
            ) from exc

    # Should only reach here if all retries were per-minute rate-limited
    raise last_exc  # type: ignore[misc]


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
                      The original Google exception is always available
                      via RuntimeError.__cause__ for full diagnostics.
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
        text = _call_with_retry(target_model, prompt)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Gemini request completed. model=%s duration_ms=%d http_status=200",
            target_model, elapsed_ms,
        )
        return text

    except RuntimeError as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        # Determine the Google HTTP code from __cause__ if available for structured logging
        cause = exc.__cause__
        http_code = getattr(cause, "code", "N/A")
        google_status = getattr(cause, "status", "N/A")
        logger.error(
            "Gemini request failed. model=%s duration_ms=%d "
            "http_code=%s google_status=%s error=%s",
            target_model, elapsed_ms, http_code, google_status, exc,
        )
        raise


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

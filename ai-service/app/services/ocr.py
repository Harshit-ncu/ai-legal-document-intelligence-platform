# app/services/ocr.py
# ─────────────────────────────────────────────────────────
# OCR service — orchestrates the extraction pipeline.
#
# WHY DOES THIS FILE EXIST?
#   The router (routers/ocr.py) handles HTTP.
#   The utils (utils/ocr_helpers.py) do low-level work.
#   This service sits in between: it adds timing, validates
#   the result, and builds the final response dictionary.
#
#   If we later add retry logic, caching, or logging,
#   it goes here — not in the router or the utilities.
#
# WHAT DOES THIS FILE DO?
#   1. Records the start time
#   2. Calls extract_text() from ocr_helpers
#   3. Records the end time → calculates processing duration
#   4. Returns the complete dict the router needs
# ─────────────────────────────────────────────────────────

import time
from app.utils.ocr_helpers import extract_text


def process_document(file_path: str, file_extension: str) -> dict:
    """
    Main OCR service function called by the router.

    Adds timing around the extraction so the response can
    include processingTimeMs — useful for users to understand
    why OCR takes longer than direct text extraction.

    Args:
        file_path:      Absolute path to the uploaded file on disk.
        file_extension: Lowercase file extension ('.pdf', '.jpg', etc.)

    Returns:
        dict: All fields needed to construct an OcrResponse.
              Includes processingTimeMs computed here.

    Raises:
        ValueError:  Known bad input — let the router map to 422.
        RuntimeError: System tools missing — let the router map to 503.
    """
    # time.perf_counter() gives high-resolution elapsed time.
    # We use it instead of time.time() because perf_counter is
    # specifically designed for measuring short durations accurately.
    start = time.perf_counter()

    # Delegate to the helpers — all logic lives there
    result = extract_text(file_path, file_extension)

    # Calculate elapsed time in milliseconds
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # Add processingTimeMs to the result dict
    result["processingTimeMs"] = elapsed_ms

    return result

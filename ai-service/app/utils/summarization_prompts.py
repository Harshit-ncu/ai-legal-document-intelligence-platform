# app/utils/summarization_prompts.py
# ─────────────────────────────────────────────────────────
# Legal document prompt builder for Module 3.2 – AI Summarization.
#
# WHY A SEPARATE FILE?
#   Prompts are complex, version-controlled artifacts. Keeping
#   them isolated from business logic means they can be reviewed,
#   improved, and A/B tested independently without touching any
#   service or router code.
#
# DESIGN PRINCIPLES:
#   1. Role-play framing: the model is asked to act as a senior
#      legal analyst, which grounds the tone and vocabulary.
#   2. Strict JSON output: the prompt forbids prose, markdown code
#      fences, and commentary outside the JSON object.
#   3. Explicit schema: every field, type, and constraint is
#      described inside the prompt so the model has no ambiguity.
#   4. Defensive instructions: the prompt explicitly handles the
#      case where a field cannot be determined ("Unable to determine").
# ─────────────────────────────────────────────────────────

# Maximum characters of document text to include in the prompt.
# Gemini 2.5 Pro supports a very large context window, but we
# apply a practical limit to control cost and latency.
MAX_DOCUMENT_CHARS = 80_000


def build_summarization_prompt(document_text: str, document_type: str) -> str:
    """
    Build the full prompt sent to Gemini for legal document summarization.

    Args:
        document_text: The cleaned, extracted text of the document.
        document_type: A label describing the document (e.g. 'NDA', 'Lease').

    Returns:
        A fully-formed prompt string ready to pass to generate_text().
    """
    # Truncate to prevent exceeding context limits, with a clear notice.
    truncated = document_text[:MAX_DOCUMENT_CHARS]
    was_truncated = len(document_text) > MAX_DOCUMENT_CHARS
    truncation_note = (
        "\n[NOTE: The document was truncated to the first 80,000 characters for analysis.]\n"
        if was_truncated
        else ""
    )

    prompt = f"""You are a senior legal analyst with 20 years of experience reviewing contracts, \
NDAs, lease agreements, employment agreements, and other legal documents.

Your task is to analyze the following legal document (type: {document_type}) and produce a \
structured JSON summary that a non-lawyer executive can understand immediately.

RULES:
- Respond with ONLY a valid JSON object. No markdown, no code fences, no commentary.
- Every field must be present. Use "Unable to determine" for any field where the document \
provides insufficient information.
- The "keyPoints" field must be a JSON array of plain-English strings (3 to 8 items).
- The "importantClauses" field must be a JSON array of objects with "title" and "description".
- The "obligations" field must be a JSON array of objects with "party" and "obligation".
- The "risks" field must be a JSON array of objects with "severity" (Low/Medium/High) and "description".
- The "suggestedNextActions" field must be a JSON array of plain-English action strings (2 to 5 items).
- All text values must be clear, concise, and free of unexplained legal jargon.
- The "executiveSummary" must be 2 to 4 sentences maximum.

REQUIRED JSON SCHEMA (respond with exactly this structure):
{{
  "executiveSummary": "string (2-4 sentences)",
  "keyPoints": ["string", "..."],
  "importantClauses": [
    {{"title": "string", "description": "string"}}
  ],
  "obligations": [
    {{"party": "string", "obligation": "string"}}
  ],
  "risks": [
    {{"severity": "Low|Medium|High", "description": "string"}}
  ],
  "suggestedNextActions": ["string", "..."]
}}

DOCUMENT TO ANALYZE:
{truncation_note}
---
{truncated}
---

Respond now with ONLY the JSON object. Do not include any text before or after it."""

    return prompt

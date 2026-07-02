# app/utils/risk_prompts.py
# ─────────────────────────────────────────────────────────
# Legal document prompt builder for Module 3.3 – Legal Risk Analysis.
#
# DESIGN PRINCIPLES:
#   1. Behave as an experienced legal contract reviewer.
#   2. Hunt specifically for unbalanced obligations, unlimited liability,
#      missing standard clauses, and ambiguous wording.
#   3. Output strictly conforming JSON based on the provided schema.
# ─────────────────────────────────────────────────────────

MAX_DOCUMENT_CHARS = 80_000


def build_risk_analysis_prompt(document_text: str, document_type: str) -> str:
    """
    Build the full prompt sent to Gemini for legal risk analysis.

    Args:
        document_text: The cleaned, extracted text of the document.
        document_type: A label describing the document (e.g. 'NDA', 'Lease').

    Returns:
        A fully-formed prompt string ready to pass to generate_text().
    """
    truncated = document_text[:MAX_DOCUMENT_CHARS]
    was_truncated = len(document_text) > MAX_DOCUMENT_CHARS
    truncation_note = (
        "\n[NOTE: The document was truncated to the first 80,000 characters for analysis.]\n"
        if was_truncated
        else ""
    )

    prompt = f"""You are an experienced legal contract reviewer and risk analyst.

Your task is to analyze the following legal document (type: {document_type}) and produce a \
comprehensive Legal Risk Analysis in a strictly structured JSON format.

Specifically, you must identify:
- Unbalanced obligations or one-sided agreements
- Unlimited liability or excessive penalties
- Missing standard clauses (e.g., termination, confidentiality, governing law, dispute resolution, payment terms, IP rights)
- Ambiguous language or suspicious legal wording
- General compliance concerns

RULES:
- Respond with ONLY a valid JSON object. No markdown, no code fences, no commentary.
- Every field must be present.
- The "overallRisk" must be exactly "Low", "Medium", or "High".
- The "overallScore" must be an integer from 0 (lowest risk/perfect) to 100 (highest risk/terrible).
- For missing fields or when something cannot be determined, use "None" or "Not specified".

REQUIRED JSON SCHEMA (respond with exactly this structure):
{{
  "overallRisk": "Low|Medium|High",
  "overallScore": 0,
  "risks": [
    {{
      "title": "string",
      "severity": "Low|Medium|High",
      "category": "string",
      "description": "string",
      "recommendation": "string"
    }}
  ],
  "missingClauses": [
    {{
      "name": "string",
      "importance": "Low|Medium|High",
      "reason": "string"
    }}
  ],
  "obligations": [
    {{
      "party": "string",
      "obligation": "string",
      "deadline": "string"
    }}
  ],
  "recommendations": ["string", "string"]
}}

DOCUMENT TO ANALYZE:
{truncation_note}
---
{truncated}
---

Respond now with ONLY the JSON object. Do not include any text before or after it."""

    return prompt

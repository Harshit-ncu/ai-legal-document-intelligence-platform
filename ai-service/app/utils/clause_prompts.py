# app/utils/clause_prompts.py
# ─────────────────────────────────────────────────────────
# Prompt builder for Module 3.4 – Clause Intelligence
#
# DESIGN PRINCIPLES:
#   1. Behave as a senior corporate lawyer advising non-lawyer clients.
#   2. Output strictly conforming JSON based on the provided schema.
#   3. Detail risks, business impact, best practices, and alternatives.
# ─────────────────────────────────────────────────────────

MAX_CLAUSE_CHARS = 20_000


def build_clause_intelligence_prompt(clause_text: str, document_type: str) -> str:
    """
    Build the full prompt sent to Gemini for clause intelligence analysis.

    Args:
        clause_text: The specific legal clause text to analyze.
        document_type: A label describing the document (e.g. 'NDA', 'Lease').

    Returns:
        A fully-formed prompt string ready to pass to generate_text().
    """
    truncated = clause_text[:MAX_CLAUSE_CHARS]
    was_truncated = len(clause_text) > MAX_CLAUSE_CHARS
    truncation_note = (
        "\n[NOTE: The clause was truncated to the first 20,000 characters for analysis.]\n"
        if was_truncated
        else ""
    )

    prompt = f"""You are a senior corporate lawyer reviewing contracts for clients who are NOT lawyers.

Your task is to analyze the following specific legal clause extracted from a {document_type} and produce a \
comprehensive Clause Intelligence report in a strictly structured JSON format.

Specifically, you must:
1. Explain it in simple English.
2. Explain its legal meaning.
3. Explain business impact.
4. Explain why it matters.
5. Identify risk level.
6. Highlight hidden risks.
7. Suggest negotiation points.
8. Suggest safer alternative wording.
9. Mention industry best practice.
10. Produce actionable recommendations.
11. Produce confidence score.

Priority Recommendation Engine Rules:
When generating recommendations in the "suggestions" array, categorize priority strictly as follows:
- Critical: Unlimited liability, missing termination, missing confidentiality, missing governing law.
- High: Ambiguous language, excessive penalties, missing payment terms.
- Medium: Weak notice period, weak dispute resolution.
- Low: Minor drafting improvements.

RULES:
- Respond with ONLY a valid JSON object. No markdown, no code fences, no commentary.
- Every field must be present. Use "None" or "Not specified" if a field cannot be determined.
- The "riskLevel" must be exactly "Low", "Medium", or "High".
- The "confidence" must be an integer from 0 to 100.
- For lists ("redFlags", "importantPoints", "suggestions"), if none exist, return an empty array [].

REQUIRED JSON SCHEMA (respond with exactly this structure):
{{
  "title": "string",
  "plainEnglish": "string",
  "legalMeaning": "string",
  "businessImpact": "string",
  "riskLevel": "Low|Medium|High",
  "whyImportant": "string",
  "industryBestPractice": "string",
  "negotiationTip": "string",
  "suggestedReplacementClause": "string",
  "redFlags": [
    "string"
  ],
  "importantPoints": [
    "string"
  ],
  "suggestions": [
    {{
      "priority": "Critical|High|Medium|Low",
      "title": "string",
      "reason": "string",
      "recommendedAction": "string"
    }}
  ],
  "confidence": 95
}}

CLAUSE TO ANALYZE:
{truncation_note}
---
{truncated}
---

Respond now with ONLY the JSON object. Do not include any text before or after it."""

    return prompt

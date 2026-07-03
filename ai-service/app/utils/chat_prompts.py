# app/utils/chat_prompts.py
# ─────────────────────────────────────────────────────────
# Prompt builder for Module 3.5 – AI Contract Assistant
#
# DESIGN PRINCIPLES:
#   1. Behave as an experienced legal contract analyst.
#   2. Strict grounding: Never invent facts. Only use the provided document.
#   3. Return "I cannot determine this from the provided document." if the answer isn't present.
#   4. Output strictly conforming JSON based on the provided schema.
# ─────────────────────────────────────────────────────────

MAX_DOCUMENT_CHARS = 80_000


def build_chat_prompt(document_text: str, document_type: str, question: str) -> str:
    """
    Build the full prompt sent to Gemini for document chat.

    Args:
        document_text: The extracted text of the document.
        document_type: A label describing the document (e.g. 'NDA', 'Lease').
        question: The user's question about the document.

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

    prompt = f"""You are an experienced legal contract analyst.

Your task is to answer a user's question about the following {document_type} in a strictly structured JSON format.

RULES:
- Answer ONLY using the supplied document.
- Never invent facts, fabricate clauses, or assume information.
- If the answer is not present in the document, your answer must be: "I cannot determine this from the provided document."
- Explain answers in plain English.
- Respond with ONLY a valid JSON object. No markdown, no code fences, no commentary.
- Every field must be present. Use "None" or an empty array [] if a field cannot be determined.
- The "confidence" must be an integer from 0 to 100.

REQUIRED JSON SCHEMA (respond with exactly this structure):
{{
  "answer": "string",
  "confidence": 94,
  "reasoning": "string",
  "referencedSections": [
    "string"
  ],
  "limitations": [
    "string"
  ]
}}

USER's QUESTION:
{question}

DOCUMENT TO ANALYZE:
{truncation_note}
---
{truncated}
---

Respond now with ONLY the JSON object. Do not include any text before or after it."""

    return prompt

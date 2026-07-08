# app/utils/chat_prompts.py
# ─────────────────────────────────────────────────────────
# Prompt builder for Module 3.5 – Verified AI Contract Assistant.
#
# DESIGN PRINCIPLES:
#   1. Behave as an experienced legal contract analyst.
#   2. Strict grounding: ONLY use the supplied document.
#   3. Never invent facts, clauses, or assumptions.
#   4. Return structured JSON with source references and follow-up questions.
# ─────────────────────────────────────────────────────────

MAX_DOCUMENT_CHARS = 80_000


def build_chat_prompt(document_text: str, document_type: str, question: str) -> str:
    """
    Build the full prompt sent to Gemini for document Q&A.

    Args:
        document_text: The extracted text of the document.
        document_type: A label describing the document (e.g. 'NDA', 'Lease').
        question:      The user's natural language question.

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

    prompt = f"""You are an experienced legal contract analyst reviewing a {document_type} for a client who is NOT a lawyer.

Your task is to answer the user's question about the document in a strictly structured JSON format.

ABSOLUTE RULES:
1. Answer ONLY from the supplied document. Never invent, fabricate, or assume facts.
2. If the answer does not exist in the document, your answer must be exactly:
   "I cannot determine this from the provided document."
3. Never fabricate clause references. Only cite clauses you can actually identify in the text.
4. Explain answers in clear English suitable for non-lawyers.
5. Keep answers concise but accurate.
6. Cite the supporting section or clause whenever possible.
7. Respond with ONLY a valid JSON object. No markdown, no code fences, no commentary.
8. Every field must be present. Use an empty array [] if lists have no entries.
9. The "confidence" must be an integer from 0 to 100.

REQUIRED JSON SCHEMA (respond with exactly this structure):
{{
  "answer": "string",
  "confidence": 95,
  "reasoning": "string",
  "sourceReferences": [
    {{
      "section": "string",
      "clause": "string",
      "excerpt": "Short relevant quotation or paraphrase from the document."
    }}
  ],
  "limitations": [
    "string"
  ],
  "followUpQuestions": [
    "string",
    "string",
    "string"
  ]
}}

USER'S QUESTION:
{question}

DOCUMENT TO ANALYZE ({document_type}):
{truncation_note}
---
{truncated}
---

Respond now with ONLY the JSON object. Do not include any text before or after it."""

    return prompt

# app/models/summarization.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the POST /gemini/summarize endpoint.
#
# WHY ARE THESE SEPARATE FROM intelligence.py models?
#   The summarization response is fundamentally different from
#   the intelligence response: it contains AI-generated structured
#   content (arrays, nested objects) rather than computed metrics.
#   Keeping them in separate files preserves single-responsibility.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


# ── Nested models ──────────────────────────────────────────

class ImportantClause(BaseModel):
    """A significant clause identified in the document."""
    title: str = Field(..., description="Short name for the clause (e.g. 'Termination Clause')")
    description: str = Field(..., description="Plain-English explanation of what the clause means")


class Obligation(BaseModel):
    """A specific obligation placed on a named party."""
    party: str = Field(..., description="The party who has this obligation (e.g. 'Recipient')")
    obligation: str = Field(..., description="Plain-English description of the obligation")


class Risk(BaseModel):
    """A potential risk or concern identified in the document."""
    severity: str = Field(..., description="Risk level: Low, Medium, or High")
    description: str = Field(..., description="Plain-English description of the risk")


# ── Request model ──────────────────────────────────────────

class SummarizeRequest(BaseModel):
    """
    Input schema for POST /gemini/summarize.

    Accepts the cleaned document text and document type label that are
    already computed by the /intelligence/analyze pipeline.
    """
    text: str = Field(
        ...,
        min_length=50,
        description="The cleaned document text to summarize. Minimum 50 characters.",
    )
    documentType: str = Field(
        default="Unknown",
        description="Document classification label (e.g. 'NDA', 'Lease', 'Unknown').",
    )


# ── Response model ─────────────────────────────────────────

class SummarizeResponse(BaseModel):
    """
    Output schema for POST /gemini/summarize.

    All six analysis fields are always present. Fields that cannot be
    determined from the document text default to a descriptive string.
    """
    success: bool

    # AI-generated structured fields
    executiveSummary: str = Field(
        ..., description="2–4 sentence plain-English summary for executives."
    )
    keyPoints: list[str] = Field(
        ..., description="3–8 bullet-point takeaways."
    )
    importantClauses: list[ImportantClause] = Field(
        ..., description="Significant clauses with plain-English explanations."
    )
    obligations: list[Obligation] = Field(
        ..., description="Party-specific obligations."
    )
    risks: list[Risk] = Field(
        ..., description="Identified risks with severity ratings."
    )
    suggestedNextActions: list[str] = Field(
        ..., description="2–5 recommended actions."
    )

    # Processing metadata
    processingTimeMs: int = Field(
        ..., description="Total time taken to generate the summary in milliseconds."
    )
    modelUsed: str = Field(
        ..., description="The Gemini model that produced this summary."
    )

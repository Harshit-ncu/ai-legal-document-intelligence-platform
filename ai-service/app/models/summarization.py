# app/models/summarization.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the POST /gemini/summarize endpoint.
#
# WHY ARE THESE SEPARATE FROM intelligence.py models?
#   The summarization response is fundamentally different from
#   the intelligence response: it contains AI-generated structured
#   content (arrays, nested objects) rather than computed metrics.
#   Keeping them in separate files preserves single-responsibility.
#
# NOTE ON ARRAY TYPES:
#   All list fields use list[str] because the summarization service
#   normalises every array element to a plain string before returning.
#   The LLM may return objects ({title, description}, {party, obligation},
#   {severity, description}) — these are flattened to human-readable
#   strings in summarization_service._normalise_array() so the React
#   frontend always receives string arrays.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


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

    All list fields contain plain strings — any object arrays returned
    by the LLM are normalised to strings in the service layer.
    """
    success: bool

    # AI-generated structured fields — all arrays are list[str]
    executiveSummary: str = Field(
        ..., description="2–4 sentence plain-English summary for executives."
    )
    keyPoints: list[str] = Field(
        ..., description="3–8 bullet-point takeaways."
    )
    importantClauses: list[str] = Field(
        ..., description="Significant clauses as readable strings."
    )
    obligations: list[str] = Field(
        ..., description="Party-specific obligations as readable strings."
    )
    risks: list[str] = Field(
        ..., description="Identified risks as readable strings."
    )
    suggestedNextActions: list[str] = Field(
        ..., description="2–5 recommended actions."
    )

    # Processing metadata
    processingTimeMs: int = Field(
        ..., description="Total time taken to generate the summary in milliseconds."
    )
    modelUsed: str = Field(
        ..., description="The model that produced this summary."
    )

# app/models/clause_intelligence.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the POST /gemini/clause-intelligence endpoint.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


# ── Nested models ──────────────────────────────────────────

class ClauseSuggestion(BaseModel):
    """A prioritized actionable recommendation based on the clause analysis."""
    priority: str = Field(..., description="Priority level: Critical, High, Medium, or Low")
    title: str = Field(..., description="Short title of the recommendation")
    reason: str = Field(..., description="Explanation of why this action is necessary")
    recommendedAction: str = Field(..., description="Actionable step to mitigate risk or improve wording")


# ── Request model ──────────────────────────────────────────

class ClauseIntelligenceRequest(BaseModel):
    """Input schema for POST /gemini/clause-intelligence."""
    clause: str = Field(
        ...,
        min_length=10,
        description="The specific legal clause text to analyze. Minimum 10 characters.",
    )
    documentType: str = Field(
        default="Unknown",
        description="Document classification label (e.g., 'NDA', 'Lease', 'Unknown').",
    )


# ── Response model ─────────────────────────────────────────

class ClauseIntelligenceResponse(BaseModel):
    """Output schema for POST /gemini/clause-intelligence."""
    success: bool
    title: str = Field(
        ..., description="Short descriptive title of the clause"
    )
    plainEnglish: str = Field(
        ..., description="Explanation of the clause in plain, non-legal English"
    )
    legalMeaning: str = Field(
        ..., description="Detailed explanation of the clause's legal effect"
    )
    businessImpact: str = Field(
        ..., description="How this clause impacts day-to-day business operations"
    )
    riskLevel: str = Field(
        ..., description="Overall risk level: Low, Medium, or High"
    )
    whyImportant: str = Field(
        ..., description="Why this clause matters in the context of the document type"
    )
    industryBestPractice: str = Field(
        ..., description="What the industry standard is for this type of clause"
    )
    negotiationTip: str = Field(
        ..., description="Tactical advice for negotiating this clause"
    )
    suggestedReplacementClause: str = Field(
        ..., description="Safer or more standard alternative wording for the clause"
    )
    redFlags: list[str] = Field(
        ..., description="Hidden risks, ambiguous terms, or trap doors"
    )
    importantPoints: list[str] = Field(
        ..., description="Key takeaways from the clause"
    )
    suggestions: list[ClauseSuggestion] = Field(
        ..., description="Prioritized recommendations for improving or handling the clause"
    )
    confidence: int = Field(
        ..., description="Confidence score from 0 to 100"
    )
    
    # Processing metadata
    processingTimeMs: int = Field(
        ..., description="Total time taken to generate the analysis in milliseconds"
    )
    modelUsed: str = Field(
        ..., description="The Gemini model that produced this analysis"
    )

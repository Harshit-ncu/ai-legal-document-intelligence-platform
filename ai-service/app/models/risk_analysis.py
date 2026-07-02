# app/models/risk_analysis.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the POST /gemini/risk-analysis endpoint.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


# ── Nested models ──────────────────────────────────────────

class RiskItem(BaseModel):
    """A specific risk identified in the document."""
    title: str = Field(..., description="Short title of the risk")
    severity: str = Field(..., description="Risk level: Low, Medium, or High")
    category: str = Field(..., description="Category (e.g., Liability, Compliance, Operational)")
    description: str = Field(..., description="Detailed explanation of the risk")
    recommendation: str = Field(..., description="Suggested action to mitigate this risk")


class MissingClause(BaseModel):
    """A standard clause that is suspiciously absent."""
    name: str = Field(..., description="Name of the missing clause (e.g., Termination, Governing Law)")
    importance: str = Field(..., description="Importance level: Low, Medium, or High")
    reason: str = Field(..., description="Why this clause is necessary for this type of document")


class RiskObligation(BaseModel):
    """An obligation identified with a deadline."""
    party: str = Field(..., description="The party responsible")
    obligation: str = Field(..., description="The specific obligation")
    deadline: str = Field(..., description="Deadline or timeframe (or 'None specified')")


# ── Request model ──────────────────────────────────────────

class RiskAnalysisRequest(BaseModel):
    """Input schema for POST /gemini/risk-analysis."""
    text: str = Field(
        ...,
        min_length=50,
        description="The extracted document text to analyze. Minimum 50 characters.",
    )
    documentType: str = Field(
        default="Unknown",
        description="Document classification label (e.g., 'NDA', 'Lease', 'Unknown').",
    )


# ── Response model ─────────────────────────────────────────

class RiskAnalysisResponse(BaseModel):
    """Output schema for POST /gemini/risk-analysis."""
    success: bool
    overallRisk: str = Field(
        ..., description="Overall risk level: Low, Medium, or High"
    )
    overallScore: int = Field(
        ..., description="Risk score from 0 (lowest risk) to 100 (highest risk)"
    )
    risks: list[RiskItem] = Field(
        ..., description="List of identified risks"
    )
    missingClauses: list[MissingClause] = Field(
        ..., description="List of standard clauses missing from the document"
    )
    obligations: list[RiskObligation] = Field(
        ..., description="Obligations extracted with their deadlines"
    )
    recommendations: list[str] = Field(
        ..., description="General strategic recommendations"
    )
    
    # Processing metadata
    processingTimeMs: int = Field(
        ..., description="Total time taken to generate the analysis in milliseconds"
    )
    modelUsed: str = Field(
        ..., description="The Gemini model that produced this analysis"
    )

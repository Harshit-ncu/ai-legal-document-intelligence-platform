# app/models/document_chat.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the POST /gemini/chat endpoint.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


# ── Request model ──────────────────────────────────────────

class DocumentChatRequest(BaseModel):
    """Input schema for POST /gemini/chat."""
    documentText: str = Field(
        ...,
        min_length=50,
        description="The extracted document text to query. Minimum 50 characters.",
    )
    documentType: str = Field(
        default="Unknown",
        description="Document classification label (e.g., 'NDA', 'Lease', 'Unknown').",
    )
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The natural language question to ask about the document.",
    )


# ── Response model ─────────────────────────────────────────

class DocumentChatResponse(BaseModel):
    """Output schema for POST /gemini/chat."""
    success: bool
    answer: str = Field(
        ..., description="The plain English answer based ONLY on the provided document."
    )
    confidence: int = Field(
        ..., description="Confidence score from 0 to 100."
    )
    reasoning: str = Field(
        ..., description="Brief explanation of how the answer was derived."
    )
    referencedSections: list[str] = Field(
        ..., description="Sections or clauses cited from the text."
    )
    limitations: list[str] = Field(
        ..., description="Caveats or conditions applicable to the answer."
    )
    
    # Processing metadata
    processingTimeMs: int = Field(
        ..., description="Total time taken to generate the answer in milliseconds."
    )
    modelUsed: str = Field(
        ..., description="The Gemini model that produced this answer."
    )

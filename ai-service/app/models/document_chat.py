# app/models/document_chat.py
# ─────────────────────────────────────────────────────────
# Pydantic models for Module 3.5 – Verified AI Contract Assistant.
# POST /gemini/chat
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


# ── Nested models ──────────────────────────────────────────

class SourceReference(BaseModel):
    """A specific section or clause from the document that supports the answer."""
    section: str = Field(
        ...,
        description="Name of the section (e.g., 'Termination', 'Confidentiality')",
    )
    clause: str = Field(
        ...,
        description="Clause number or identifier (e.g., 'Clause 9', 'Section 4.2')",
    )
    excerpt: str = Field(
        ...,
        description="Short relevant quotation or paraphrase from the document.",
    )


# ── Request model ──────────────────────────────────────────

class DocumentChatRequest(BaseModel):
    """Input schema for POST /gemini/chat."""
    documentText: str = Field(
        ...,
        min_length=50,
        description="The extracted document text. Minimum 50 characters.",
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
        ...,
        description=(
            "Plain English answer grounded strictly in the provided document. "
            "If the answer cannot be found, this will be "
            "'I cannot determine this from the provided document.'"
        ),
    )
    confidence: int = Field(
        ...,
        description="Confidence score from 0 to 100.",
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of how the answer was derived.",
    )
    sourceReferences: list[SourceReference] = Field(
        ...,
        description="Structured references to clauses/sections that support the answer.",
    )
    limitations: list[str] = Field(
        ...,
        description="Caveats or conditions applicable to the answer.",
    )
    followUpQuestions: list[str] = Field(
        ...,
        description="Suggested follow-up questions relevant to the document and topic.",
    )

    # Processing metadata
    processingTimeMs: int = Field(
        ...,
        description="Total time taken to generate the answer in milliseconds.",
    )
    modelUsed: str = Field(
        ...,
        description="The Gemini model that produced this answer.",
    )

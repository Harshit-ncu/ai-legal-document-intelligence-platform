# app/models/intelligence.py
# ─────────────────────────────────────────────────────────
# Pydantic models for the Feature 4 /intelligence/analyze endpoint.
#
# WHY DOES THIS FILE EXIST?
#   FastAPI uses Pydantic to guarantee that the JSON we send
#   to the frontend exactly matches this shape. It's a contract.
#   This model combines the text extraction output with the
#   new Document Intelligence metrics.
# ─────────────────────────────────────────────────────────

from pydantic import BaseModel


class IntelligenceResponse(BaseModel):
    """
    JSON response returned by POST /intelligence/analyze.
    """
    success: bool
    documentType: str
    
    # Document Classification
    classification: str
    classificationConfidence: float
    
    # Processing Metadata
    ocrUsed: bool
    
    # Text Statistics
    pageCount: int
    wordCount: int
    characterCount: int
    paragraphCount: int
    sentenceCount: int
    estimatedReadingTimeMinutes: int
    
    # Language Detection
    language: str
    languageConfidence: float
    
    # Performance Metric
    processingTimeMs: int
    
    # The cleaned document text
    text: str

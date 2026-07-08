# main.py
# ─────────────────────────────────────────────────────────
# Entry point for the FastAPI AI service.
# FastAPI automatically generates API docs at /docs (Swagger UI).
# ─────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import extraction  # Module 2A: text extraction
from app.routers import ocr          # Module 2B: OCR + scanned docs
from app.routers import intelligence # Feature 4: Document Intelligence
from app.routers import gemini       # Module 3.1: Gemini SDK infrastructure

app = FastAPI(
    title="Legal AI Service",
    description="Analyzes legal documents using NLP and AI",
    version="1.0.0",
)

# Allow requests from the Node.js backend (and direct browser calls
# during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ─────────────────────────────────────────
# extraction.router handles:  POST /extract/text
app.include_router(extraction.router)

# ocr.router handles:         POST /ocr/extract
app.include_router(ocr.router)

# intelligence.router handles: POST /intelligence/analyze
app.include_router(intelligence.router)

# gemini.router handles all Gemini-powered AI endpoints (Modules 3.1–3.5):
#   POST /gemini/test               — 3.1 infrastructure smoke-test
#   GET  /gemini/health             — 3.1 connectivity health check
#   POST /gemini/summarize          — 3.2 AI document summarization
#   POST /gemini/risk-analysis      — 3.3 legal risk analysis
#   POST /gemini/clause-intelligence— 3.4 clause breakdown & recommendations
#   POST /gemini/chat               — 3.5 AI contract Q&A assistant
app.include_router(gemini.router)


@app.get("/health")
def health_check():
    """Quick health check — returns 200 if the service is running."""
    return {"status": "ok", "service": "legal-ai-service"}

# main.py
# ─────────────────────────────────────────────────────────
# Entry point for the FastAPI AI service.
# FastAPI automatically generates API docs at /docs (Swagger UI).
# ─────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import extraction  # Module 2A: text extraction

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

# Future modules will be added here:
#   app.include_router(summarize.router)   # Module 3
#   app.include_router(clauses.router)     # Module 4


@app.get("/health")
def health_check():
    """Quick health check — returns 200 if the service is running."""
    return {"status": "ok", "service": "legal-ai-service"}

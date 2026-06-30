# main.py
# ─────────────────────────────────────────────────────────
# Entry point for the FastAPI AI service.
# FastAPI automatically generates API docs at /docs (Swagger UI).
# ─────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Legal AI Service",
    description="Analyzes legal documents using NLP and AI",
    version="1.0.0",
)

# Allow requests from the Node.js backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers will be included here as we build each module ──
# Example:
#   from app.routers import analyze
#   app.include_router(analyze.router, prefix="/analyze")

@app.get("/health")
def health_check():
    """Quick health check — returns 200 if the service is running."""
    return {"status": "ok", "service": "legal-ai-service"}

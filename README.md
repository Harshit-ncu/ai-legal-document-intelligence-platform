# ⚖️ AI Legal Document Analyzer

> An intelligent full-stack application that analyzes legal documents using AI to extract key clauses, summarize content, and flag risks.

---

## 🏗️ Architecture

```
legal-ai/
├── frontend/        → React + Vite         (port 5173)
├── backend/         → Node.js + Express    (port 3001)
├── ai-service/      → Python + FastAPI     (port 8000)
└── shared/          → Shared constants & types
```

**Request flow:**
```
Browser → React Frontend → Express Backend → FastAPI AI Service
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js v20+
- Python 3.11+
- npm 9+

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd legal-ai
```

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. Start the Backend
```bash
cd backend
npm install
npm run dev
# → http://localhost:3001
# Health check: GET http://localhost:3001/api/health
```

### 4. Start the AI Service
```bash
cd ai-service
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# → http://localhost:8000
# Interactive API docs: http://localhost:8000/docs
```

---

## 📁 Project Structure

```
legal-ai/
│
├── frontend/                    # React + Vite UI
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page-level components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API call functions
│   │   └── utils/               # Frontend helpers
│   └── vite.config.js
│
├── backend/                     # Node.js + Express API
│   ├── src/
│   │   ├── routes/              # Express route definitions
│   │   ├── controllers/         # Request/response handlers
│   │   ├── middleware/          # Auth, file validation, errors
│   │   ├── services/            # Business logic
│   │   ├── config/              # DB & service configs
│   │   └── utils/               # Backend helpers
│   ├── uploads/                 # Temp storage for uploaded files
│   └── .env                     # Environment variables (not committed)
│
├── ai-service/                  # Python + FastAPI
│   ├── app/
│   │   ├── routers/             # FastAPI route handlers
│   │   ├── services/            # AI processing logic
│   │   ├── models/              # Pydantic request/response models
│   │   └── utils/               # Text cleaning, parsing helpers
│   ├── tests/                   # pytest test files
│   ├── main.py                  # FastAPI entry point
│   └── requirements.txt         # Python dependencies
│
└── shared/                      # Shared between frontend & backend
    └── constants/               # File size limits, status codes, etc.
```

---

## 🧩 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 19 + Vite | User interface |
| Backend | Node.js + Express | API gateway, auth, file handling |
| AI Service | Python + FastAPI | Document parsing, NLP, AI |
| HTTP | REST + JSON | Communication between services |

---

## 📈 Modules (Build Order)

- [x] Module 0 — Project Setup
- [ ] Module 1 — File Upload (backend + frontend)
- [ ] Module 2 — PDF/DOCX Text Extraction (ai-service)
- [ ] Module 3 — AI Summarization (ai-service)
- [ ] Module 4 — Clause Extraction (ai-service)
- [ ] Module 5 — Risk Flagging (ai-service)
- [ ] Module 6 — Results UI (frontend)

---

## 👤 Author

Built by **Harshit Singh** as a portfolio project.

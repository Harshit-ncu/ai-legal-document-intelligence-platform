# API Documentation

## Express Backend (`http://localhost:3001`)

### `GET /api/health`
**Purpose:** Health check for the Node.js API Gateway.
- **Request:** None
- **Response:** `200 OK`
```json
{
  "status": "ok",
  "service": "legal-ai-backend"
}
```

### `POST /api/documents/upload`
**Purpose:** Uploads a document, extracts text, and returns document classification.
- **Request:** `multipart/form-data` with key `document`
- **Response:** `200 OK`
```json
{
  "success": true,
  "text": "Extracted text here...",
  "documentType": "NDA",
  "classification": "NDA",
  "classificationConfidence": 0.95,
  "originalName": "contract.pdf"
}
```
- **Errors:** 
  - `400 Bad Request` - No file uploaded
  - `413 Payload Too Large` - File exceeds 5MB
  - `415 Unsupported Media Type` - Invalid file type
  - `503 Service Unavailable` - Python AI service offline

---

## FastAPI AI Service (`http://localhost:8000`)

### `POST /gemini/summarize`
**Purpose:** Generates a plain-English summary of the document.
- **Request:** `application/json`
```json
{
  "text": "Full document text...",
  "documentType": "NDA"
}
```
- **Response:** `200 OK`
```json
{
  "summary": "This document is a mutual non-disclosure agreement...",
  "key_points": ["Point 1", "Point 2"]
}
```

### `POST /gemini/risk-analysis`
**Purpose:** Flags potential legal risks, unusual terms, and missing standard clauses.
- **Request:** Same as Summarize
- **Response:** `200 OK`
```json
{
  "risk_score": "High",
  "risks": [{"severity": "High", "description": "Uncapped liability"}]
}
```

### `POST /gemini/clause-intelligence`
**Purpose:** Analyzes a specific clause for fairness, market standard, and implications.
- **Request:** `application/json`
```json
{
  "clause": "The receiving party shall hold the information in strict confidence forever.",
  "documentType": "NDA"
}
```
- **Response:** `200 OK`

### `POST /gemini/chat`
**Purpose:** Q&A interaction with the document text.
- **Request:** `application/json`
```json
{
  "documentText": "Full text...",
  "documentType": "NDA",
  "question": "Who are the parties?"
}
```
- **Response:** `200 OK`
```json
{
  "answer": "The parties are Acme Corp and Globex.",
  "relevant_quotes": ["This agreement is between Acme Corp and Globex."]
}
```

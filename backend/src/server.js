// src/server.js
// ─────────────────────────────────────────────────────────
// Entry point for the Express backend.
// This file does ONE thing: start the HTTP server.
// All app configuration lives in app.js (separation of concerns).
// ─────────────────────────────────────────────────────────

const app = require('./app');

// PORT comes from .env; fallback to 3001 for local development
const PORT = process.env.PORT || 3001;

app.listen(PORT, () => {
  console.log(`✅  Backend running on http://localhost:${PORT}`);
});

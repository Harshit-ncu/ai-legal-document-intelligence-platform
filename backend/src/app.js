// src/app.js
// ─────────────────────────────────────────────────────────
// Express application factory.
// Registers all global middleware and mounts route groups.
// Keeping this separate from server.js makes the app easier
// to test (you can import 'app' without starting a real server).
// ─────────────────────────────────────────────────────────

const express = require('express');
const cors    = require('cors');
const morgan  = require('morgan');
require('dotenv').config();

const app = express();

// ── Middleware ────────────────────────────────────────────

// CORS: allow requests from the React dev server (port 5173)
app.use(cors({ origin: process.env.FRONTEND_URL || 'http://localhost:5173' }));

// Parse JSON request bodies
app.use(express.json());

// HTTP request logger (shows method, url, status, response time)
app.use(morgan('dev'));

// ── Routes ────────────────────────────────────────────────
// Routes will be added here as we build each module.
// Example pattern:
//   const documentRoutes = require('./routes/documents');
//   app.use('/api/documents', documentRoutes);

// Health-check endpoint — always useful to verify the server is up
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', service: 'legal-ai-backend' });
});

// ── 404 catch-all ─────────────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

module.exports = app;

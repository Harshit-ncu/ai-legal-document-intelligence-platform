// src/app.js
// ─────────────────────────────────────────────────────────
// Express application factory.
// Registers all global middleware and mounts route groups.
// Keeping this separate from server.js makes the app easier
// to test (you can import 'app' without starting a real server).
// ─────────────────────────────────────────────────────────

const express      = require('express');
const cors         = require('cors');
const morgan       = require('morgan');
const path         = require('path');
require('dotenv').config();

const documentRoutes = require('./routes/documents');
const errorHandler   = require('./middleware/errorHandler');

const app = express();

// ── Middleware ────────────────────────────────────────────

// CORS: allow requests from the React dev server (port 5173)
app.use(cors({ origin: process.env.FRONTEND_URL || 'http://localhost:5173' }));

// Parse JSON request bodies
app.use(express.json());

// HTTP request logger (shows method, url, status, response time)
app.use(morgan('dev'));

// ── Routes ────────────────────────────────────────────────

// Health-check endpoint — always useful to verify the server is up
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', service: 'legal-ai-backend' });
});

// Document upload routes → mounted at /api/documents
// e.g. POST /api/documents/upload
app.use('/api/documents', documentRoutes);

// ── 404 catch-all ─────────────────────────────────────────
// Runs when NO route above matched the incoming URL.
// Must come AFTER all routes but BEFORE the error handler.
// Returns JSON (not HTML) so the React frontend can read it.
app.use((_req, res) => {
  res.status(404).json({ success: false, error: 'Route not found.' });
});

// ── Error Handler ─────────────────────────────────────────
// IMPORTANT: Must be registered LAST — after routes and 404.
// Express identifies error handlers by their 4-parameter signature.
// Catches all errors thrown by Multer, controllers, etc.
app.use(errorHandler);

module.exports = app;

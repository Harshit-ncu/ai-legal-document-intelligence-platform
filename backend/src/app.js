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

// CORS: allow requests from React dev server and production Vercel frontend
const defaultOrigins = [
  'http://localhost:5173',
  'https://ai-legal-document-intelligence-plat-xi.vercel.app'
];
const allowedOrigins = process.env.FRONTEND_URL 
  ? process.env.FRONTEND_URL.split(',') 
  : defaultOrigins;

const corsOptions = {
  origin: allowedOrigins,
  credentials: true,
};

app.use(cors(corsOptions));

// Parse JSON request bodies
app.use(express.json());

// HTTP request logger (shows method, url, status, response time)
app.use(morgan('dev'));

// ── Routes ────────────────────────────────────────────────

// Health-check endpoint — a named handler is shared between both
// /api/health (canonical) and /health (alias for load-balancers and
// orchestration health probes that expect a root-level /health path).
function handleHealthCheck(_req, res) {
  res.json({ status: 'ok', service: 'legal-ai-backend' });
}

app.get('/api/health', handleHealthCheck); // canonical
app.get('/health',     handleHealthCheck); // alias

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

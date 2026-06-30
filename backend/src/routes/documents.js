// src/routes/documents.js
// ─────────────────────────────────────────────────────────
// Express router for all /api/documents/* endpoints.
//
// Think of routes as the "menu" of your API.
// They say: "when THIS URL + METHOD is called, run THESE
// middleware functions in order, then call THIS controller."
//
// Middleware order on the upload route:
//   1. upload.single('document')  → Multer parses + saves file
//   2. uploadDocument             → Controller sends JSON response
// ─────────────────────────────────────────────────────────

const express    = require('express');
const router     = express.Router();
const upload     = require('../middleware/upload');
const { uploadDocument } = require('../controllers/documents');

// ── POST /api/documents/upload ────────────────────────────
// upload.single('document') tells Multer to look for ONE file
// in the form field named "document".
// The field name MUST match the FormData field name in React.
router.post('/upload', upload.single('document'), uploadDocument);

// More routes will be added here in future modules:
// router.get('/:id',    getDocument);
// router.delete('/:id', deleteDocument);

module.exports = router;

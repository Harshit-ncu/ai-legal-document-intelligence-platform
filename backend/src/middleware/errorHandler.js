// src/middleware/errorHandler.js
// ─────────────────────────────────────────────────────────
// Global error handling middleware.
//
// In Express, a middleware with 4 parameters (err, req, res, next)
// is automatically treated as an ERROR handler.
// It must be registered LAST (after all routes) in app.js.
//
// When Multer throws an error (e.g. file too large, wrong type),
// it calls next(error), which skips all remaining middleware and
// lands here. This gives us one central place to format errors.
// ─────────────────────────────────────────────────────────

const multer = require('multer');

// eslint-disable-next-line no-unused-vars
const errorHandler = (err, _req, res, _next) => {
  console.error(`❌ Error: ${err.message}`);

  // ── Multer-specific errors ─────────────────────────────
  if (err instanceof multer.MulterError) {
    // MulterError codes: https://github.com/expressjs/multer/blob/master/lib/make-error.js
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(413).json({
        success: false,
        error:   'File is too large. Maximum allowed size is 5 MB.',
      });
    }
    // Catch any other Multer errors generically
    return res.status(400).json({
      success: false,
      error:   `Upload error: ${err.message}`,
    });
  }

  // ── Our custom file type error (thrown in fileFilter) ──
  if (err.message === 'INVALID_FILE_TYPE') {
    return res.status(415).json({
      success: false,
      error:   'Invalid file type. Only PDF and DOCX files are allowed.',
    });
  }

  // ── Catch-all for unexpected errors ───────────────────
  return res.status(500).json({
    success: false,
    error:   'An unexpected server error occurred.',
  });
};

module.exports = errorHandler;

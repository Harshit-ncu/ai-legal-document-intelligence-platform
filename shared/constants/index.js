// shared/constants/index.js
// ─────────────────────────────────────────────────────────
// Constants shared between frontend and backend.
// Import this file wherever you need these values.
// ─────────────────────────────────────────────────────────

// Maximum file size the user can upload (5 MB)
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

// Supported document MIME types
const ALLOWED_FILE_TYPES = [
  'application/pdf',                                       // PDF
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'text/plain',                                            // .txt
];

// Document analysis status values
const ANALYSIS_STATUS = {
  PENDING:    'pending',
  PROCESSING: 'processing',
  COMPLETED:  'completed',
  FAILED:     'failed',
};

module.exports = { MAX_FILE_SIZE_BYTES, ALLOWED_FILE_TYPES, ANALYSIS_STATUS };

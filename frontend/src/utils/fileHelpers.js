// src/utils/fileHelpers.js
// ─────────────────────────────────────────────────────────
// Pure utility functions for file validation and formatting.
//
// "Pure" means: given the same input, always returns the
// same output. No side effects. No state. Easy to test.
// ─────────────────────────────────────────────────────────

// Allowed MIME types (mirrors backend upload.js for consistency)
export const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

export const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];

// 5 MB in bytes
export const MAX_SIZE_BYTES = 5 * 1024 * 1024;

/**
 * Validate a File object before uploading.
 * Returns an error message string, or null if the file is valid.
 *
 * @param {File} file
 * @returns {string|null}
 */
export const validateFile = (file) => {
  if (!file) return 'Please select a file.';

  // Check file type by MIME type
  if (!ALLOWED_TYPES.includes(file.type)) {
    return 'Only PDF and DOCX files are allowed.';
  }

  // Check file size
  if (file.size > MAX_SIZE_BYTES) {
    return `File is too large (${formatFileSize(file.size)}). Maximum is 5 MB.`;
  }

  return null; // null = no error = valid
};

/**
 * Format bytes into a human-readable string.
 *   formatFileSize(204800) → "200 KB"
 *   formatFileSize(5242880) → "5.0 MB"
 *
 * @param {number} bytes
 * @returns {string}
 */
export const formatFileSize = (bytes) => {
  if (bytes < 1024)        return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * Get the file extension for display.
 *   getFileExtension('contract.pdf') → 'PDF'
 *
 * @param {string} filename
 * @returns {string}
 */
export const getFileExtension = (filename) => {
  return filename.split('.').pop().toUpperCase();
};

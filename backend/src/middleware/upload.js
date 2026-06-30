// src/middleware/upload.js
// ─────────────────────────────────────────────────────────
// Multer configuration for handling file uploads.
//
// What is Multer?
//   Express cannot parse multipart/form-data (the format
//   browsers use to send files). Multer is the middleware
//   that reads the binary stream and saves it to disk.
//
// This file exports ONE thing: a configured Multer instance
// that the route can use as middleware before the controller.
// ─────────────────────────────────────────────────────────

const multer  = require('multer');
const path    = require('path');
const crypto  = require('crypto'); // Built-in Node module — no install needed

// ── 1. Where and how to store uploaded files ──────────────
const storage = multer.diskStorage({

  // destination: which folder to save files in.
  // The callback signature is (err, folderPath).
  // Passing null as first arg means "no error".
  destination: (_req, _file, cb) => {
    cb(null, path.join(__dirname, '../../uploads'));
    // __dirname = /backend/src/middleware
    // '../../uploads' = /backend/uploads
  },

  // filename: what to call the saved file.
  // We prepend a timestamp + random hex so two users uploading
  // "contract.pdf" never overwrite each other.
  //   e.g. 1751234567890-a3f2c1-contract.pdf
  filename: (_req, file, cb) => {
    const timestamp  = Date.now();
    const randomHex  = crypto.randomBytes(3).toString('hex'); // 6 random hex chars
    const cleanName  = file.originalname.replace(/\s+/g, '-'); // replace spaces with -
    cb(null, `${timestamp}-${randomHex}-${cleanName}`);
  },
});

// ── 2. File type filter (first layer of validation) ───────
// This runs BEFORE the file is saved to disk.
// If the file type is wrong, Multer rejects it immediately.
const fileFilter = (_req, file, cb) => {
  const ALLOWED_MIME_TYPES = [
    'application/pdf',
    // .docx MIME type (the official IANA type for Word 2007+)
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ];

  if (ALLOWED_MIME_TYPES.includes(file.mimetype)) {
    cb(null, true); // Accept the file
  } else {
    // Passing an Error as the first argument rejects the file
    // and sends it to our error handler middleware.
    cb(new Error('INVALID_FILE_TYPE'), false);
  }
};

// ── 3. Assemble the Multer instance ───────────────────────
const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 5 * 1024 * 1024, // 5 MB — matches shared/constants/index.js
  },
});

module.exports = upload;

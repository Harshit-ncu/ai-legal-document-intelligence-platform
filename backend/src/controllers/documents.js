// src/controllers/documents.js
// ─────────────────────────────────────────────────────────
// Controller for document-related operations.
//
// A controller is the bridge between the route and the
// business logic. It:
//   1. Reads from req (the incoming request)
//   2. Calls services or middleware results
//   3. Sends a response with res
//
// By the time this controller runs, Multer has already:
//   - Validated the file type
//   - Saved the file to disk
//   - Populated req.file with metadata
// ─────────────────────────────────────────────────────────

/**
 * POST /api/documents/upload
 *
 * Expected: multipart/form-data with a field named "document"
 * Returns:  JSON with file metadata on success, error on failure
 */
const uploadDocument = (req, res) => {
  // If Multer rejected the file (wrong type, too large),
  // req.file will be undefined. We handle that edge case here.
  if (!req.file) {
    return res.status(400).json({
      success: false,
      error: 'No file was uploaded. Please attach a PDF or DOCX file.',
    });
  }

  // req.file is populated by Multer and contains:
  //   fieldname    → "document" (the HTML input name)
  //   originalname → "my-contract.pdf" (what the user named it)
  //   filename     → "1751234567890-a3f2c1-my-contract.pdf" (saved name)
  //   mimetype     → "application/pdf"
  //   size         → 204800 (bytes)
  //   path         → "/backend/uploads/1751234567890-a3f2c1-my-contract.pdf"
  const { originalname, filename, mimetype, size } = req.file;

  console.log(`✅ File uploaded: ${filename} (${(size / 1024).toFixed(1)} KB)`);

  // Return a clean JSON response to the frontend.
  // We DO NOT return the full file path — that would expose
  // your server's directory structure, which is a security risk.
  return res.status(200).json({
    success:      true,
    filename,        // the unique saved name (used to retrieve the file later)
    originalName: originalname,
    size,            // bytes
    mimeType:     mimetype,
    uploadedAt:   new Date().toISOString(),
  });
};

module.exports = { uploadDocument };

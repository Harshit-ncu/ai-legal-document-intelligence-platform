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

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

/**
 * POST /api/documents/upload
 *
 * Expected: multipart/form-data with a field named "document"
 * Returns:  JSON with file metadata AND intelligence analysis on success.
 */
const uploadDocument = async (req, res) => {
  if (!req.file) {
    return res.status(400).json({
      success: false,
      error: 'No file was uploaded. Please attach a PDF, DOCX, TXT, or Image file.',
    });
  }

  const { originalname, filename, mimetype, size, path } = req.file;
  const startTime = Date.now();

  try {
    // 1. Prepare FormData to send to Python AI Service
    const form = new FormData();
    form.append('file', fs.createReadStream(path), {
      filename: originalname,
      contentType: mimetype,
    });

    // 2. Send request to Python FastAPI Service
    const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';
    
    // axios throws on non-2xx status codes by default
    const aiResponse = await axios.post(`${aiServiceUrl}/intelligence/analyze`, form, {
      headers: form.getHeaders(),
      timeout: 60000, // 60-second timeout for large OCR tasks
    });

    const processingTime = Date.now() - startTime;

    // 3. Operational Logging (No sensitive text)
    console.log(`✅ Integration Success: [${filename}] processed in ${processingTime}ms`);

    // 4. Augment Python response with Express file metadata
    const finalResponse = {
      ...aiResponse.data,     // The exact unchanged Python JSON (success, classification, stats, etc.)
      originalName: originalname,
      filename: filename,
      size: size,
      uploadTime: new Date().toISOString(),
      backendProcessingTimeMs: processingTime,
    };

    return res.status(200).json(finalResponse);

  } catch (err) {
    const processingTime = Date.now() - startTime;
    console.error(`❌ Integration Error: [${filename}] failed after ${processingTime}ms.`, err.message);

    // Python Service returned an error (e.g., 415 Unsupported Media Type, 422 Validation Error)
    if (err.response) {
      return res.status(err.response.status).json({
        success: false,
        error: err.response.data?.detail?.error || err.response.data?.detail || 'AI Service returned an error.',
      });
    }

    // Network Errors (e.g., Python service offline, Timeout)
    if (err.code === 'ECONNREFUSED') {
      return res.status(503).json({
        success: false,
        error: 'AI Analysis Service is currently unavailable. Please try again later.',
      });
    }

    if (err.code === 'ECONNABORTED') {
      return res.status(504).json({
        success: false,
        error: 'AI Analysis Service timed out. The document may be too large or complex.',
      });
    }

    // Generic fallback error
    return res.status(500).json({
      success: false,
      error: 'An unexpected error occurred while communicating with the AI service.',
    });
  }
};

module.exports = { uploadDocument };

// src/services/api.js
// ─────────────────────────────────────────────────────────
// Centralized API service layer.
//
// Why have a separate services/ file?
//   If you ever change the API URL or need to add auth headers,
//   you change it in ONE place here — not in every component.
//   Components should not know about axios or URLs.
//
// Why axios over fetch()?
//   axios has onUploadProgress — fetch() does not.
//   Real upload % progress is only possible with XHR/axios.
// ─────────────────────────────────────────────────────────

import axios from 'axios';

// Base URL: Vite's proxy (vite.config.js) forwards /api → Express.
// In production you'd set this to your deployed backend URL.
const API_BASE = '/api';

/**
 * Upload a document file to the backend.
 *
 * @param {File} file - The File object from the input or drop event
 * @param {function} onProgress - Callback called with % complete (0-100)
 * @returns {Promise<object>} - The JSON response from the backend
 */
export const uploadDocument = async (file, onProgress) => {
  // FormData is how browsers send files over HTTP.
  // It creates a multipart/form-data body automatically.
  const formData = new FormData();

  // 'document' MUST match the field name in our Multer route:
  //   upload.single('document')
  formData.append('document', file);

  const response = await axios.post(`${API_BASE}/documents/upload`, formData, {
    headers: {
      // Don't set Content-Type manually!
      // axios/browser will set it to 'multipart/form-data; boundary=...'
      // automatically (the boundary is required for parsing).
    },

    // onUploadProgress is an axios-specific option (uses XHR under the hood)
    // progressEvent has: loaded (bytes sent) and total (total bytes)
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  // axios wraps the response body in response.data
  return response.data;
};

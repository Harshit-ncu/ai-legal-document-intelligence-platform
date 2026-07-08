import axios from 'axios';

const API_BASE = '/api';

/**
 * Upload a document to the backend.
 * @param {File} file 
 * @param {Function} onProgress 
 */
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('document', file);

  const response = await axios.post(`${API_BASE}/documents/upload`, formData, {
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        if (onProgress) onProgress(percent);
      }
    },
  });

  return response.data;
};

// Future API methods for fetching document status/metadata will go here

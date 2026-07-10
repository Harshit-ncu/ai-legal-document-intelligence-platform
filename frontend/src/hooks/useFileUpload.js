// src/hooks/useFileUpload.js
// ─────────────────────────────────────────────────────────
// Custom React hook that manages upload logic.
// Refactored to consume the global DocumentContext.
// ─────────────────────────────────────────────────────────

import { useCallback, useState } from 'react';
import { uploadDocument } from '../services/api';
import { validateFile } from '../utils/fileHelpers';
import { useDocumentContext } from '../contexts/DocumentContext';
import { toast } from 'react-hot-toast';

export const UPLOAD_STATE = {
  IDLE:       'idle',
  SELECTED:   'selected',
  UPLOADING:  'uploading',
  SUCCESS:    'success',
  ERROR:      'error',
};

const useFileUpload = () => {
  const { state, setUploadedFile, setUploadProgress, setUploadSuccess, setExtractionData, setError, resetDocument } = useDocumentContext();

  // Local state for the upload result (we could also put this in context, but keeping it here for now unless needed globally)
  const [result, setResult] = useState(null);

  // Map global state to hook output for backward compatibility
  const uploadState = state.uploadStatus;
  const selectedFile = state.uploadedFile;
  const progress = state.uploadProgress;
  const error = state.error;

  const selectFile = useCallback((file) => {
    resetDocument();
    setResult(null);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      toast.error(validationError);
      return;
    }

    setUploadedFile(file);
  }, [resetDocument, setError, setUploadedFile]);

  const upload = useCallback(async () => {
    if (!state.uploadedFile) return;

    setUploadProgress(0);

    try {
      const data = await uploadDocument(state.uploadedFile, (percent) => {
        setUploadProgress(percent);
      });

      setResult(data);
      setUploadSuccess();
      toast.success('Document uploaded & analyzed successfully!');
      
      // Also set the extraction data into global context
      setExtractionData({
        extractedText: data.text, // Assuming data contains text
        documentType: data.documentType,
        language: data.language
      });

    } catch (err) {
      const message = err.response?.data?.error || 'Upload failed. Please try again.';
      setError(message);
      toast.error(message);
    }
  }, [state.uploadedFile, setUploadProgress, setUploadSuccess, setExtractionData, setError]);

  const reset = useCallback(() => {
    resetDocument();
    setResult(null);
  }, [resetDocument]);

  return {
    uploadState: state.uploadedFile && state.uploadStatus === 'idle' ? UPLOAD_STATE.SELECTED : uploadState,
    selectedFile,
    progress,
    result,
    error,
    selectFile,
    upload,
    reset,
  };
};

export default useFileUpload;

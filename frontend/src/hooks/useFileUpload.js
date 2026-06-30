// src/hooks/useFileUpload.js
// ─────────────────────────────────────────────────────────
// Custom React hook that manages all upload state and logic.
//
// Why extract this into a hook?
//   The UploadPage component would be very long if it contained
//   both the UI code (JSX) AND all the state management.
//   This hook handles ALL state; the component only renders.
//
// What is a custom hook?
//   A regular JS function whose name starts with "use" and
//   that can call other React hooks (useState, useCallback).
//   It's the standard React pattern for sharing stateful logic.
// ─────────────────────────────────────────────────────────

import { useState, useCallback } from 'react';
import { uploadDocument } from '../services/api';
import { validateFile } from '../utils/fileHelpers';

// The possible states our upload flow can be in.
// Using a string enum makes debugging easy — you can log the state.
export const UPLOAD_STATE = {
  IDLE:       'idle',       // no file selected yet
  SELECTED:   'selected',   // file chosen, not yet uploaded
  UPLOADING:  'uploading',  // upload in progress
  SUCCESS:    'success',    // upload completed
  ERROR:      'error',      // something went wrong
};

const useFileUpload = () => {
  // ── State ───────────────────────────────────────────────
  const [uploadState, setUploadState] = useState(UPLOAD_STATE.IDLE);
  const [selectedFile, setSelectedFile] = useState(null);   // File object
  const [progress, setProgress]         = useState(0);       // 0-100
  const [result, setResult]             = useState(null);    // backend response
  const [error, setError]               = useState(null);    // error message string

  // ── selectFile ──────────────────────────────────────────
  // Called when the user picks a file (drop or click).
  // useCallback memoizes the function so React doesn't
  // recreate it on every render (small perf optimization).
  const selectFile = useCallback((file) => {
    // Reset previous state first
    setError(null);
    setResult(null);
    setProgress(0);

    // Validate before accepting the file
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setUploadState(UPLOAD_STATE.ERROR);
      return;
    }

    setSelectedFile(file);
    setUploadState(UPLOAD_STATE.SELECTED);
  }, []);

  // ── upload ──────────────────────────────────────────────
  // Called when the user clicks "Analyze Document".
  // Sends the file to the backend and tracks progress.
  const upload = useCallback(async () => {
    if (!selectedFile) return;

    setUploadState(UPLOAD_STATE.UPLOADING);
    setProgress(0);
    setError(null);

    try {
      // uploadDocument(file, progressCallback) → from services/api.js
      const data = await uploadDocument(selectedFile, (percent) => {
        setProgress(percent);
      });

      setResult(data);
      setUploadState(UPLOAD_STATE.SUCCESS);
      setProgress(100);

    } catch (err) {
      // axios wraps HTTP error responses in err.response
      const message = err.response?.data?.error || 'Upload failed. Please try again.';
      setError(message);
      setUploadState(UPLOAD_STATE.ERROR);
    }
  }, [selectedFile]);

  // ── reset ───────────────────────────────────────────────
  // Clears everything so the user can start a new upload.
  const reset = useCallback(() => {
    setUploadState(UPLOAD_STATE.IDLE);
    setSelectedFile(null);
    setProgress(0);
    setResult(null);
    setError(null);
  }, []);

  // Return everything the component needs
  return {
    uploadState,
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

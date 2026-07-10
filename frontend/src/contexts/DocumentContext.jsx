import React, { createContext, useContext, useReducer } from 'react';

// ── Initial State ─────────────────────────────────────────
export const initialState = {
  uploadedFile: null,      // The original File object
  documentId: null,        // Server-side ID if applicable
  extractedText: null,     // The full text of the document
  documentType: null,      // Classification (e.g. NDA, Lease)
  language: null,          // Detected language
  uploadStatus: 'idle',    // idle | uploading | success | error
  extractionStatus: 'idle',// idle | processing | success | error
  analysisStatus: 'idle',  // idle | processing | success | error
  uploadProgress: 0,       // 0 - 100
  currentPage: 1,          // For PDF viewer or pagination
  processing: false,       // Global busy indicator for operations
  error: null,             // Any fatal error string
};

// ── Action Types ──────────────────────────────────────────
const ACTIONS = {
  SET_FILE: 'SET_FILE',
  SET_PROGRESS: 'SET_PROGRESS',
  SET_UPLOAD_SUCCESS: 'SET_UPLOAD_SUCCESS',
  SET_EXTRACTION_DATA: 'SET_EXTRACTION_DATA',
  SET_PROCESSING: 'SET_PROCESSING',
  SET_PAGE: 'SET_PAGE',
  SET_ERROR: 'SET_ERROR',
  RESET: 'RESET',
};

// ── Reducer ───────────────────────────────────────────────
export function documentReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_FILE:
      return {
        ...state,
        uploadedFile: action.payload,
        uploadStatus: 'idle',
        error: null,
        uploadProgress: 0,
      };
    case ACTIONS.SET_PROGRESS:
      return {
        ...state,
        uploadStatus: 'uploading',
        uploadProgress: action.payload,
        processing: true,
        error: null,
      };
    case ACTIONS.SET_UPLOAD_SUCCESS:
      return {
        ...state,
        uploadStatus: 'success',
        uploadProgress: 100,
        processing: false,
        // we can store intermediate result data here if returned
      };
    case ACTIONS.SET_EXTRACTION_DATA:
      return {
        ...state,
        extractedText: action.payload.extractedText,
        documentType: action.payload.documentType,
        language: action.payload.language,
        extractionStatus: 'success',
        analysisStatus: 'success', // if classification is done at upload
      };
    case ACTIONS.SET_PROCESSING:
      return { ...state, processing: action.payload };
    case ACTIONS.SET_PAGE:
      return { ...state, currentPage: action.payload };
    case ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        uploadStatus: state.uploadStatus === 'uploading' ? 'error' : state.uploadStatus,
        extractionStatus: state.extractionStatus === 'processing' ? 'error' : state.extractionStatus,
        analysisStatus: state.analysisStatus === 'processing' ? 'error' : state.analysisStatus,
        processing: false,
      };
    case ACTIONS.RESET:
      return { ...initialState };
    default:
      return state;
  }
}

// ── Context ───────────────────────────────────────────────
const DocumentContext = createContext(null);

export const DocumentProvider = ({ children }) => {
  const [state, dispatch] = useReducer(documentReducer, initialState);

  // ── Action Creators (Clean API for consumers) ───────────
  const actions = {
    setUploadedFile: (file) => dispatch({ type: ACTIONS.SET_FILE, payload: file }),
    setUploadProgress: (progress) => dispatch({ type: ACTIONS.SET_PROGRESS, payload: progress }),
    setUploadSuccess: () => dispatch({ type: ACTIONS.SET_UPLOAD_SUCCESS }),
    setExtractionData: (data) => dispatch({ type: ACTIONS.SET_EXTRACTION_DATA, payload: data }),
    setProcessing: (isProcessing) => dispatch({ type: ACTIONS.SET_PROCESSING, payload: isProcessing }),
    setCurrentPage: (page) => dispatch({ type: ACTIONS.SET_PAGE, payload: page }),
    setError: (error) => dispatch({ type: ACTIONS.SET_ERROR, payload: error }),
    resetDocument: () => dispatch({ type: ACTIONS.RESET }),
  };

  return (
    <DocumentContext.Provider value={{ state, ...actions }}>
      {children}
    </DocumentContext.Provider>
  );
};

// ── Custom Hook ───────────────────────────────────────────
export const useDocumentContext = () => {
  const context = useContext(DocumentContext);
  if (!context) {
    throw new Error('useDocumentContext must be used within a DocumentProvider');
  }
  return context;
};

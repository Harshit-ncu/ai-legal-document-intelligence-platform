import axios from 'axios';

// Direct connection to the FastAPI AI service which has CORS enabled for frontend
const AI_API_BASE = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8000/gemini';

/**
 * Request an executive summary from the AI service.
 * @param {string} documentText 
 * @param {string} documentType 
 */
export const summarizeDocument = async (documentText, documentType) => {
  const response = await axios.post(`${AI_API_BASE}/summarize`, {
    text: documentText,
    documentType: documentType || 'Unknown'
  });
  return response.data;
};

/**
 * Request a legal risk analysis from the AI service.
 * @param {string} documentText 
 * @param {string} documentType 
 */
export const analyzeRisk = async (documentText, documentType) => {
  const response = await axios.post(`${AI_API_BASE}/risk-analysis`, {
    text: documentText,
    documentType: documentType || 'Unknown'
  });
  return response.data;
};

/**
 * Request clause intelligence from the AI service.
 * @param {string} clause 
 * @param {string} documentType 
 */
export const analyzeClause = async (clause, documentType) => {
  const response = await axios.post(`${AI_API_BASE}/clause-intelligence`, {
    clause: clause,
    documentType: documentType || 'Unknown'
  });
  return response.data;
};

/**
 * Send a chat message to the AI contract assistant.
 * @param {string} documentText 
 * @param {string} documentType 
 * @param {string} question 
 */
export const sendChatMessage = async (documentText, documentType, question) => {
  const response = await axios.post(`${AI_API_BASE}/chat`, {
    documentText,
    documentType: documentType || 'Unknown',
    question,
  });
  return response.data;
};

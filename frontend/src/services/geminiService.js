import axios from 'axios';

// Uses the AI Service port mapped via Vite proxy, or the express backend which forwards it
const AI_API_BASE = '/api/gemini'; // Assuming proxy handles the routing

/**
 * Request an executive summary from the AI service.
 * @param {string} documentText 
 * @param {string} documentType 
 */
export const summarizeDocument = async (documentText, documentType) => {
  // Placeholder - logic to be implemented later
  console.log("summarizeDocument called", { documentType });
  return null;
};

/**
 * Request a legal risk analysis from the AI service.
 * @param {string} documentText 
 * @param {string} documentType 
 */
export const analyzeRisk = async (documentText, documentType) => {
  // Placeholder - logic to be implemented later
  console.log("analyzeRisk called", { documentType });
  return null;
};

/**
 * Request clause intelligence from the AI service.
 * @param {string} clause 
 * @param {string} documentType 
 */
export const analyzeClause = async (clause, documentType) => {
  // Placeholder - logic to be implemented later
  console.log("analyzeClause called", { documentType });
  return null;
};

/**
 * Send a chat message to the AI contract assistant.
 * @param {string} documentText 
 * @param {string} documentType 
 * @param {string} question 
 */
export const sendChatMessage = async (documentText, documentType, question) => {
  // Placeholder - logic to be implemented later
  console.log("sendChatMessage called", { documentType, question });
  return null;
};

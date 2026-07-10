# Deployment Guide

This guide explains how to deploy the AI Legal Document Analyzer to production using modern cloud platforms.

## 1. Frontend Deployment (Vercel/Netlify)

The frontend is a static React Single Page Application (SPA) built with Vite. It can be hosted on any static file hosting service.

### Recommended Platform: Vercel
1. Connect your GitHub repository to Vercel.
2. Ensure the Framework Preset is set to **Vite**.
3. **Build Command:** `npm run build`
4. **Output Directory:** `dist`
5. **Environment Variables:**
   - `VITE_AI_SERVICE_URL`: Set this to your deployed FastAPI service URL (e.g., `https://legal-ai-service.railway.app/gemini`).

*Note: Since this is an SPA, ensure your hosting provider rewrites all traffic to `index.html` (Vercel does this automatically for Vite).*

---

## 2. Express API Gateway (Railway/Render)

The Express backend acts as the file upload handler and proxies large files to the AI service.

### Recommended Platform: Railway
1. Create a new service from your GitHub repo.
2. Set the Root Directory to `/backend`.
3. **Build Command:** `npm install`
4. **Start Command:** `npm start` (or `node src/server.js`)
5. **Environment Variables:**
   - `PORT`: (Provided automatically by Railway)
   - `FRONTEND_URL`: Set this to your Vercel URL (e.g., `https://my-legal-app.vercel.app`) to restrict CORS.
   - `AI_SERVICE_URL`: Set this to your deployed FastAPI service URL.

---

## 3. FastAPI AI Service (Railway/Render)

The Python backend handles the heavy lifting, OCR, and communication with Google Gemini.

### Recommended Platform: Railway
1. Create a new service from your GitHub repo.
2. Set the Root Directory to `/ai-service`.
3. **Build Command:** `pip install -r requirements.txt` (Railway typically auto-detects this).
4. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables:**
   - `PORT`: (Provided automatically by Railway)
   - `ALLOWED_ORIGINS`: Comma-separated list of origins for CORS. Include both the Vercel URL and the Express backend URL. (e.g., `https://my-legal-app.vercel.app,https://my-express-api.railway.app`).
   - `GEMINI_API_KEY`: Your Google Gemini API key.

---

## Common Deployment Issues & Troubleshooting

1. **CORS Errors on the Frontend:**
   - *Symptom:* The browser console shows "Blocked by CORS policy".
   - *Fix:* Ensure `ALLOWED_ORIGINS` in the FastAPI service contains the exact origin of your frontend (without trailing slashes).
   
2. **503 Service Unavailable on Uploads:**
   - *Symptom:* Uploading a document fails immediately.
   - *Fix:* Verify that `AI_SERVICE_URL` in the Express backend environment variables is correct and points to the live FastAPI deployment.

3. **Rate Limits from Gemini:**
   - *Symptom:* AI endpoints return 429 errors.
   - *Fix:* This happens if you are using the free tier of the Gemini API and hitting request limits. The app is built with exponential backoff, but you may need to wait 60 seconds or upgrade your API tier.

4. **Missing Environment Variables:**
   - *Symptom:* The app crashes on startup or fails silently.
   - *Fix:* Double-check all three environments (Frontend, Backend, AI Service) in your deployment dashboard against their respective `.env.example` files.

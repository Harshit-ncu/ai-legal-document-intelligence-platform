// src/main.jsx
// ─────────────────────────────────────────────────────────
// React application entry point.
//
// ReactDOM.createRoot() is the React 18 way to mount an app.
// It enables "concurrent mode" — React can pause and resume
// rendering, making the app more responsive.
//
// StrictMode runs every component twice in development to
// help catch side-effects and bugs early. It has no effect
// in production builds.
// ─────────────────────────────────────────────────────────

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import './index.css';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </ErrorBoundary>
  </StrictMode>,
);

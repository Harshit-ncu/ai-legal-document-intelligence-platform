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

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

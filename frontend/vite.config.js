// vite.config.js
// ─────────────────────────────────────────────────────────
// Vite configuration.
//
// @vitejs/plugin-react enables:
//   - JSX transformation (turns <div> into React.createElement)
//   - Fast Refresh (updates component state on save without reload)
//
// The proxy setting is crucial for development:
//   When React calls "/api/...", Vite forwards it to Express.
//   This avoids CORS issues during development because the
//   request appears to come from the same origin (localhost:5173).
// ─────────────────────────────────────────────────────────

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  test: {
    environment: 'jsdom',
    setupFiles: './setupTests.js',
    globals: true,
    pool: 'threads',
    css: false
  },
  server: {
    port: 5173,
    // Proxy: any request starting with /api is forwarded to Express
    proxy: {
      '/api': {
        target:      'http://localhost:3001', // Express backend
        changeOrigin: true,                   // rewrites the Host header
      },
    },
  },
});

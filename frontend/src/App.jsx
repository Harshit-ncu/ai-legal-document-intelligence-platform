// src/App.jsx
// ─────────────────────────────────────────────────────────
// Root application component.
//
// Right now this app has one page (UploadPage).
// In future modules we'll add react-router-dom here to handle
// multiple pages (e.g. /upload, /documents/:id, /results).
//
// Keeping App.jsx separate from UploadPage lets us add routing
// without touching any page-level components.
// ─────────────────────────────────────────────────────────

import UploadPage from './pages/UploadPage';

const App = () => {
  // Future: <Router><Route path="/" element={<UploadPage />} /></Router>
  return <UploadPage />;
};

export default App;

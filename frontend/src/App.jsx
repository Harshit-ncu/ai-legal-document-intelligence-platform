// src/App.jsx
// ─────────────────────────────────────────────────────────
// Root application component.
// Configures React Router and all application routes.
// ─────────────────────────────────────────────────────────

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Layout
import { AppLayout } from './components/layout/AppLayout';

// Pages
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import SummaryPage from './pages/SummaryPage';
import RiskAnalysisPage from './pages/RiskAnalysisPage';
import ClauseIntelligencePage from './pages/ClauseIntelligencePage';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/summary" element={<SummaryPage />} />
          <Route path="/risk" element={<RiskAnalysisPage />} />
          <Route path="/clauses" element={<ClauseIntelligencePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;

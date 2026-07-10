import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { PageHeader } from '../components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import styles from './SettingsPage.module.css';

// ── Static info rows ──────────────────────────────────────
const AI_INFO = [
  { label: 'AI Provider', value: 'Google Gemini', badge: null },
  { label: 'Model', value: 'Gemini 2.5 Pro', badge: 'Active' },
  { label: 'Text Extraction', value: 'Native + Tesseract OCR', badge: null },
  { label: 'Document Classification', value: 'Auto-detect', badge: null },
];

const CAPABILITIES = [
  { icon: '📝', title: 'AI Document Summary', status: 'Available' },
  { icon: '🚨', title: 'Legal Risk Analysis', status: 'Available' },
  { icon: '🔍', title: 'Clause Intelligence', status: 'Available' },
  { icon: '💬', title: 'AI Document Chat', status: 'Available' },
];

const SettingsPage = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={styles.container}>
      <PageHeader
        title="Settings"
        description="Manage your application preferences and view system information."
      />

      {/* ── Appearance ── */}
      <Card className={styles.settingsCard}>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={styles.settingRow}>
            <div className={styles.settingInfo}>
              <span className={styles.settingLabel}>Theme</span>
              <span className={styles.settingDesc}>
                {isDark ? 'Dark mode is active' : 'Light mode is active'}
              </span>
            </div>
            <div className={styles.settingControl}>
              <Badge variant={isDark ? 'info' : 'warning'}>
                {isDark ? '🌙 Dark' : '☀️ Light'}
              </Badge>
              <Button variant="outline" onClick={toggleTheme}>
                Switch to {isDark ? 'Light' : 'Dark'} Mode
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── AI Configuration ── */}
      <Card className={styles.settingsCard}>
        <CardHeader>
          <CardTitle>AI Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={styles.infoTable}>
            {AI_INFO.map((row) => (
              <div key={row.label} className={styles.infoRow}>
                <span className={styles.infoLabel}>{row.label}</span>
                <span className={styles.infoValue}>
                  {row.value}
                  {row.badge && (
                    <Badge variant="success" className={styles.infoBadge}>{row.badge}</Badge>
                  )}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── Available Capabilities ── */}
      <Card className={styles.settingsCard}>
        <CardHeader>
          <CardTitle>Available Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={styles.capabilityGrid}>
            {CAPABILITIES.map((cap) => (
              <div key={cap.title} className={styles.capabilityItem}>
                <span className={styles.capabilityIcon}>{cap.icon}</span>
                <div className={styles.capabilityBody}>
                  <span className={styles.capabilityTitle}>{cap.title}</span>
                  <Badge variant="success">{cap.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── About ── */}
      <Card className={styles.settingsCard}>
        <CardHeader>
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={styles.infoTable}>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Platform</span>
              <span className={styles.infoValue}>AI Legal Document Intelligence Platform</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Version</span>
              <span className={styles.infoValue}>1.0.0</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Frontend</span>
              <span className={styles.infoValue}>React + Vite</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Backend</span>
              <span className={styles.infoValue}>Node.js / Express + FastAPI</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;


import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentContext } from '../contexts/DocumentContext';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { Badge } from '../components/ui/Badge';
import { FileText, Globe, Hash, File, AlertTriangle, Search, MessageSquare, FileDigit } from 'lucide-react';
import styles from './DashboardPage.module.css';

// ── Feature cards config ──────────────────────────────────
const FEATURES = [
  {
    path: '/summary',
    icon: <FileText size={24} />,
    title: 'AI Document Summary',
    description: 'Generate a plain-English executive summary of the full document.',
    badge: null,
  },
  {
    path: '/risk',
    icon: <AlertTriangle size={24} />,
    title: 'Legal Risk Analysis',
    description: 'Identify high, medium, and low severity risks and missing clauses.',
    badge: 'Gemini 2.5 Pro',
  },
  {
    path: '/clauses',
    icon: <Search size={24} />,
    title: 'Clause Intelligence',
    description: 'Get a deep breakdown of any clause with negotiation tips and red flags.',
    badge: null,
  },
  {
    path: '/chat',
    icon: <MessageSquare size={24} />,
    title: 'AI Document Chat',
    description: 'Ask natural language questions. Answers are grounded strictly in the document.',
    badge: 'New',
  },
];

// ── Status badge helper ───────────────────────────────────
function statusBadge(status) {
  if (status === 'success') return <Badge variant="success">Ready</Badge>;
  if (status === 'uploading' || status === 'processing') return <Badge variant="warning">Processing</Badge>;
  if (status === 'error') return <Badge variant="error">Error</Badge>;
  return <Badge variant="info">Idle</Badge>;
}

const DashboardPage = () => {
  const navigate = useNavigate();
  const { state } = useDocumentContext();
  const {
    uploadedFile, extractedText, documentType, language,
    uploadStatus, extractionStatus,
  } = state;

  const hasDocument = Boolean(extractedText);

  return (
    <div className={styles.container}>
      <PageHeader
        title="Dashboard"
        description="Overview of the uploaded document and AI analysis tools."
        actions={
          !hasDocument && (
            <Button onClick={() => navigate('/upload')} variant="primary">
              Upload a Document
            </Button>
          )
        }
      />

      {/* ── Document Status ── */}
      {hasDocument ? (
        <>
          {/* Stat row */}
          <div className={styles.statsGrid}>
            <StatCard
              title="Document Type"
              value={documentType || 'Unknown'}
              description="Detected classification"
              icon={<FileDigit size={24} />}
            />
            <StatCard
              title="Language"
              value={language || 'Unknown'}
              description="Detected language"
              icon={<Globe size={24} />}
            />
            <StatCard
              title="Characters"
              value={extractedText.length.toLocaleString()}
              description="Extracted text length"
              icon={<Hash size={24} />}
            />
            <StatCard
              title="File"
              value={uploadedFile?.name ?? 'Uploaded'}
              description={uploadedFile ? `${(uploadedFile.size / 1024).toFixed(1)} KB` : ''}
              icon={<File size={24} />}
            />
          </div>

          {/* Pipeline status card */}
          <Card className={styles.statusCard}>
            <CardHeader>
              <CardTitle>Processing Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={styles.pipelineGrid}>
                <div className={styles.pipelineItem}>
                  <span className={styles.pipelineLabel}>Upload</span>
                  {statusBadge(uploadStatus)}
                </div>
                <div className={styles.pipelineDivider}>→</div>
                <div className={styles.pipelineItem}>
                  <span className={styles.pipelineLabel}>Text Extraction</span>
                  {statusBadge(extractionStatus)}
                </div>
                <div className={styles.pipelineDivider}>→</div>
                <div className={styles.pipelineItem}>
                  <span className={styles.pipelineLabel}>AI Analysis</span>
                  <Badge variant="success">Available</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick-action cards */}
          <div className={styles.sectionHeading}>AI Analysis Tools</div>
          <div className={styles.featuresGrid}>
            {FEATURES.map((f) => (
              <Card
                key={f.path}
                className={styles.featureCard}
                onClick={() => navigate(f.path)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && navigate(f.path)}
              >
                <CardContent className={styles.featureContent}>
                  <div className={styles.featureIcon}>{f.icon}</div>
                  <div className={styles.featureBody}>
                    <div className={styles.featureTitleRow}>
                      <h3 className={styles.featureTitle}>{f.title}</h3>
                      {f.badge && <Badge variant="info">{f.badge}</Badge>}
                    </div>
                    <p className={styles.featureDesc}>{f.description}</p>
                  </div>
                  <span className={styles.featureArrow}>›</span>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Reset CTA */}
          <div className={styles.resetRow}>
            <Button onClick={() => navigate('/upload')} variant="outline">
              Upload a Different Document
            </Button>
          </div>
        </>
      ) : (
        <EmptyState
          icon={<File size={48} className={styles.emptyIcon} />}
          title="No Document Loaded"
          description="Upload a legal document to unlock AI-powered summary, risk analysis, clause intelligence, and Q&A."
          action={
            <Button onClick={() => navigate('/upload')} variant="primary">
              Upload a Document
            </Button>
          }
        />
      )}
    </div>
  );
};

export default DashboardPage;


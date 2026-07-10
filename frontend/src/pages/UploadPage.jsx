// src/pages/UploadPage.jsx
// ─────────────────────────────────────────────────────────
// The main upload page.
//
// This component is intentionally thin — all state lives in
// useFileUpload(). This component's only job is to decide
// WHICH sub-components to render based on the current state.
//
// State machine visualization:
//
//   IDLE ──────(file selected)──────▶ SELECTED
//   SELECTED ──(upload clicked)─────▶ UPLOADING
//   UPLOADING ─(success)────────────▶ SUCCESS
//   UPLOADING ─(error)──────────────▶ ERROR
//   SUCCESS ───(upload another)─────▶ IDLE
//   ERROR ─────(try again)──────────▶ IDLE
// ─────────────────────────────────────────────────────────

import useFileUpload, { UPLOAD_STATE } from '../hooks/useFileUpload';
import DropZone    from '../components/DropZone';
import FileInfo    from '../components/FileInfo';
import ProgressBar from '../components/ProgressBar';
import { formatFileSize } from '../utils/fileHelpers';
import { Scale, CheckCircle, AlertCircle, Search, FileText, Flag } from 'lucide-react';
import styles from './UploadPage.module.css';

const UploadPage = () => {
  const {
    uploadState,
    selectedFile,
    progress,
    result,
    error,
    selectFile,
    upload,
    reset,
  } = useFileUpload();

  const isUploading = uploadState === UPLOAD_STATE.UPLOADING;

  return (
    <main className={styles.page}>
      {/* ── Page Header ────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.logo} aria-hidden="true">
          <Scale size={40} />
        </div>
        <h1 className={styles.title}>Legal Document Analyzer</h1>
        <p className={styles.subtitle}>
          Upload a contract or legal document to extract key clauses,
          summarize content, and flag potential risks using AI.
        </p>
      </header>

      {/* ── Upload Card ────────────────────────────────── */}
      <section className={styles.card} aria-label="Document upload">

        {/* ── Step 1: Drop Zone (always visible unless uploading/done) ── */}
        {uploadState === UPLOAD_STATE.IDLE && (
          <DropZone onFileSelect={selectFile} disabled={false} />
        )}

        {/* ── Step 2: File selected — show info + upload button ─────── */}
        {uploadState === UPLOAD_STATE.SELECTED && (
          <>
            <DropZone onFileSelect={selectFile} disabled={false} />
            <FileInfo
              file={selectedFile}
              onRemove={reset}
              disabled={false}
            />
            <button
              type="button"
              className={styles.uploadBtn}
              onClick={upload}
              id="upload-btn"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              Analyze Document
            </button>
          </>
        )}

        {/* ── Step 3: Uploading — show progress bar ─────────────────── */}
        {uploadState === UPLOAD_STATE.UPLOADING && (
          <>
            <FileInfo
              file={selectedFile}
              onRemove={() => {}}
              disabled={true}
            />
            <ProgressBar progress={progress} />
          </>
        )}

        {/* ── Step 4: Success — show result ─────────────────────────── */}
        {uploadState === UPLOAD_STATE.SUCCESS && result && (
          <div className={styles.successPanel} role="status" aria-live="polite">
            <div className={styles.successIcon} aria-hidden="true">
              <CheckCircle size={48} className={styles.successIconSvg} />
            </div>
            <h2 className={styles.successTitle}>Upload Successful!</h2>

            <dl className={styles.resultGrid}>
              <div className={styles.resultRow}>
                <dt>File Name</dt>
                <dd>{result.originalName}</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Document Type</dt>
                <dd className={styles.mono}>{result.documentType?.toUpperCase() || 'UNKNOWN'}</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Classification</dt>
                <dd>{result.classification} ({(result.classificationConfidence * 100).toFixed(0)}%)</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Language</dt>
                <dd>{result.language}</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Word Count</dt>
                <dd>{result.wordCount?.toLocaleString()}</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Character Count</dt>
                <dd>{result.characterCount?.toLocaleString()}</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Sentence Count</dt>
                <dd>{result.sentenceCount?.toLocaleString()}</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Reading Time</dt>
                <dd>~{result.estimatedReadingTimeMinutes} min</dd>
              </div>
              <div className={styles.resultRow}>
                <dt>Processing Time</dt>
                <dd>{result.processingTimeMs} ms</dd>
              </div>
            </dl>

            <p className={styles.nextHint}>
              🚀 Your document is ready for AI analysis.
            </p>

            <button
              type="button"
              className={styles.resetBtn}
              onClick={reset}
              id="upload-another-btn"
            >
              Upload Another Document
            </button>
          </div>
        )}

        {/* ── Error state ────────────────────────────────────────────── */}
        {uploadState === UPLOAD_STATE.ERROR && (
          <div className={styles.errorPanel} role="alert" aria-live="assertive">
            <div className={styles.errorIcon} aria-hidden="true">
              <AlertCircle size={48} className={styles.errorIconSvg} />
            </div>
            <p className={styles.errorMessage}>{error}</p>
            <button
              type="button"
              className={styles.resetBtn}
              onClick={reset}
              id="try-again-btn"
            >
              Try Again
            </button>
          </div>
        )}

      </section>

      {/* ── Features preview (coming soon) ──────────────── */}
      <section className={styles.features} aria-label="Upcoming features">
        <FeatureCard icon={<Search size={24} />} title="Clause Extraction" desc="Identifies and categorizes key legal clauses automatically." />
        <FeatureCard icon={<FileText size={24} />} title="AI Summarization" desc="Generates a plain-English summary of complex legal text." />
        <FeatureCard icon={<Flag size={24} />} title="Risk Flagging" desc="Highlights potentially unfavorable or unusual terms." />
      </section>
    </main>
  );
};

// Small inline component — doesn't need its own file at this size
const FeatureCard = ({ icon, title, desc }) => (
  <article className={styles.featureCard}>
    <span className={styles.featureIcon} aria-hidden="true">{icon}</span>
    <h3 className={styles.featureTitle}>{title}</h3>
    <p className={styles.featureDesc}>{desc}</p>
    <span className={styles.comingSoon}>Available Now</span>
  </article>
);

export default UploadPage;

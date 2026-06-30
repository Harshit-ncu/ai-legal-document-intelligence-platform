// src/components/FileInfo.jsx
// ─────────────────────────────────────────────────────────
// Displays the selected file's metadata before upload.
// Shows: file type badge, name, size, and a "change file" button.
// ─────────────────────────────────────────────────────────

import { formatFileSize, getFileExtension } from '../utils/fileHelpers';
import styles from './FileInfo.module.css';

// Icons as small inline SVG components keep the bundle lightweight.
// We avoid an icon library dependency for just 2 icons.
const PdfIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"/>
    <path d="M9 13h2v4H9zm4-3h2v7h-2zm-4-3h2v2H9z"/>
  </svg>
);

const DocxIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"/>
    <path d="M9 13h6v1.5H9zm0 2.5h6V17H9zm0-5h6v1.5H9z"/>
  </svg>
);

const FileInfo = ({ file, onRemove, disabled }) => {
  const ext = getFileExtension(file.name);
  const isPdf = ext === 'PDF';

  return (
    <div className={styles.card} role="region" aria-label="Selected file details">
      {/* File type icon + badge */}
      <div className={`${styles.iconBadge} ${isPdf ? styles.pdf : styles.docx}`}>
        {isPdf ? <PdfIcon /> : <DocxIcon />}
        <span className={styles.extLabel}>{ext}</span>
      </div>

      {/* File name and size */}
      <div className={styles.info}>
        {/* title attribute shows full name on hover if truncated */}
        <p className={styles.name} title={file.name}>
          {file.name}
        </p>
        <p className={styles.meta}>
          {formatFileSize(file.size)}
          <span className={styles.dot} aria-hidden="true">·</span>
          Ready to upload
        </p>
      </div>

      {/* Remove / change file button */}
      {!disabled && (
        <button
          type="button"
          className={styles.removeBtn}
          onClick={onRemove}
          aria-label={`Remove ${file.name}`}
          id="remove-file-btn"
        >
          {/* × icon */}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      )}
    </div>
  );
};

export default FileInfo;

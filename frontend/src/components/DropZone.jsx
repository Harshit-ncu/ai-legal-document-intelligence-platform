// src/components/DropZone.jsx
// ─────────────────────────────────────────────────────────
// Drag-and-drop file upload zone component.
//
// This component handles THREE ways to select a file:
//   1. Drag a file from the OS and drop it here
//   2. Click anywhere in the zone to open a file picker
//   3. Click the "Browse Files" button
//
// It is a "dumb" (presentational) component — it doesn't
// manage upload state. It just calls onFileSelect(file)
// and lets the parent (UploadPage) decide what to do.
// ─────────────────────────────────────────────────────────

import { useState, useRef, useCallback } from 'react';
import { ALLOWED_EXTENSIONS } from '../utils/fileHelpers';
import styles from './DropZone.module.css';

const DropZone = ({ onFileSelect, disabled }) => {
  // isDragging tracks whether something is being dragged OVER the zone
  // We use it to show the highlighted/active state
  const [isDragging, setIsDragging] = useState(false);

  // useRef gives us direct access to the hidden <input type="file">
  // so we can trigger it programmatically when the zone is clicked
  const inputRef = useRef(null);

  // ── Drag event handlers ─────────────────────────────────

  // dragover fires continuously while dragging over the element.
  // We MUST call preventDefault() to allow dropping (browser default
  // is to open the file, not drop it into the page).
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  // drop fires when the user releases the mouse button over the zone.
  // e.dataTransfer.files contains the dropped file(s).
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;

    // DataTransfer.files is a FileList (array-like).
    // We only support one file at a time, so we take index [0].
    const file = e.dataTransfer.files[0];
    if (file) onFileSelect(file);
  }, [disabled, onFileSelect]);

  // ── File picker (click) handler ─────────────────────────

  // When the zone or button is clicked, programmatically click
  // the hidden <input type="file"> to open the OS file picker.
  const handleClick = useCallback(() => {
    if (!disabled) inputRef.current?.click();
  }, [disabled]);

  // Called when the user selects a file from the file picker dialog
  const handleInputChange = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      onFileSelect(file);
      // Reset input value so the same file can be re-selected
      e.target.value = '';
    }
  }, [onFileSelect]);

  // ── Keyboard accessibility ──────────────────────────────
  // The zone should be activatable with Enter or Space for
  // keyboard-only users (important for accessibility/a11y).
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }, [handleClick]);

  const zoneClass = [
    styles.zone,
    isDragging  ? styles.dragging  : '',
    disabled    ? styles.disabled  : '',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={zoneClass}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      // Make it focusable for keyboard navigation
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload a legal document by dragging and dropping or clicking to browse"
      aria-disabled={disabled}
    >
      {/* Hidden file input — only PDF and DOCX */}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        onChange={handleInputChange}
        className={styles.hiddenInput}
        // aria-hidden because it's controlled by the visible zone div
        aria-hidden="true"
        tabIndex={-1}
      />

      {/* Upload icon */}
      <div className={styles.iconWrapper} aria-hidden="true">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>

      <div className={styles.textContent}>
        <p className={styles.primaryText}>
          {isDragging ? 'Drop your document here' : 'Drag & drop your document'}
        </p>
        <p className={styles.secondaryText}>or</p>
        <button
          type="button"
          className={styles.browseButton}
          onClick={(e) => {
            // Stop propagation so the zone click handler doesn't also fire
            e.stopPropagation();
            handleClick();
          }}
          disabled={disabled}
          id="browse-files-btn"
        >
          Browse Files
        </button>
        <p className={styles.hint}>
          Supports {ALLOWED_EXTENSIONS.join(', ')} · Max 5 MB
        </p>
      </div>
    </div>
  );
};

export default DropZone;

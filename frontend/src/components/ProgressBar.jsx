// src/components/ProgressBar.jsx
// ─────────────────────────────────────────────────────────
// Animated upload progress bar.
//
// Accessibility note:
//   We use role="progressbar" with aria-valuenow, aria-valuemin,
//   and aria-valuemax so screen readers can announce progress.
// ─────────────────────────────────────────────────────────

import styles from './ProgressBar.module.css';

const ProgressBar = ({ progress }) => {
  // Clamp between 0 and 100 to be safe
  const safeProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className={styles.wrapper} aria-label="Upload progress">
      {/* Label row */}
      <div className={styles.labelRow}>
        <span className={styles.label}>Uploading...</span>
        <span className={styles.percent} aria-live="polite">
          {safeProgress}%
        </span>
      </div>

      {/* Track (the grey background bar) */}
      <div className={styles.track}>
        {/* Fill (the colored bar that grows) */}
        <div
          className={styles.fill}
          style={{ width: `${safeProgress}%` }}
          role="progressbar"
          aria-valuenow={safeProgress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Upload ${safeProgress}% complete`}
        />
      </div>
    </div>
  );
};

export default ProgressBar;

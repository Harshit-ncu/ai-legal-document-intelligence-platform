import React from 'react';
import styles from './ErrorMessage.module.css';

export const ErrorMessage = ({ title = "Error", message, className = '', ...props }) => {
  if (!message) return null;
  
  return (
    <div className={`${styles.errorContainer} ${className}`} role="alert" {...props}>
      <div className={styles.icon} aria-hidden="true">⚠️</div>
      <div className={styles.content}>
        <h4 className={styles.title}>{title}</h4>
        <p className={styles.message}>{message}</p>
      </div>
    </div>
  );
};

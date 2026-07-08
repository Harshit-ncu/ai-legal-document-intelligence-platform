import React from 'react';
import styles from './PageHeader.module.css';

export const PageHeader = ({ title, description, actions, children, className = '', ...props }) => {
  return (
    <header className={`${styles.header} ${className}`} {...props}>
      <div className={styles.content}>
        <h1 className={styles.title}>{title}</h1>
        {description && <p className={styles.description}>{description}</p>}
        {children}
      </div>
      {actions && (
        <div className={styles.actions}>
          {actions}
        </div>
      )}
    </header>
  );
};

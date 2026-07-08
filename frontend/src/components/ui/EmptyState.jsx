import React from 'react';
import styles from './EmptyState.module.css';

export const EmptyState = ({ 
  icon = "📄", 
  title = "No Data Available", 
  description, 
  action,
  className = '',
  ...props 
}) => {
  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.iconWrapper} aria-hidden="true">
        <span className={styles.icon}>{icon}</span>
      </div>
      <h3 className={styles.title}>{title}</h3>
      {description && <p className={styles.description}>{description}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
};

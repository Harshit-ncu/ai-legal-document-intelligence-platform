import React from 'react';
import styles from './Badge.module.css';

export const Badge = ({ children, variant = 'default', className = '', ...props }) => {
  return (
    <span className={`${styles.badge} ${styles[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
};

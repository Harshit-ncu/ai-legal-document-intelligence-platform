import React from 'react';
import styles from './Spinner.module.css';

export const Spinner = ({ size = 'md', className = '', ...props }) => {
  return (
    <span 
      className={`${styles.spinner} ${styles[size]} ${className}`} 
      aria-hidden="true"
      {...props}
    />
  );
};

import React from 'react';
import styles from './Skeleton.module.css';

export const Skeleton = ({ className = '', width, height, borderRadius, ...props }) => {
  return (
    <div 
      className={`skeleton-shimmer ${styles.skeleton} ${className}`} 
      style={{ width, height, borderRadius }}
      {...props}
    />
  );
};

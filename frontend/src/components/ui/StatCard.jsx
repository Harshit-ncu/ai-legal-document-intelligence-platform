import React from 'react';
import { Card, CardContent } from './Card';
import styles from './StatCard.module.css';

export const StatCard = ({ title, value, icon, description, trend, className = '', ...props }) => {
  return (
    <Card className={`${styles.statCard} ${className}`} {...props}>
      <CardContent className={styles.content}>
        <div className={styles.info}>
          <h4 className={styles.title}>{title}</h4>
          <div className={styles.valueContainer}>
            <span className={styles.value}>{value}</span>
            {trend && (
              <span className={`${styles.trend} ${trend > 0 ? styles.positive : styles.negative}`}>
                {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
              </span>
            )}
          </div>
          {description && <p className={styles.description}>{description}</p>}
        </div>
        {icon && (
          <div className={styles.iconWrapper} aria-hidden="true">
            {icon}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

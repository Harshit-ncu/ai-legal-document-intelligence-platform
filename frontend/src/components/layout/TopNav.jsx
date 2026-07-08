import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import styles from './TopNav.module.css';

export const TopNav = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className={styles.topnav}>
      <div className={styles.search}>
        {/* Placeholder for global search */}
      </div>
      
      <div className={styles.actions}>
        <button 
          className={styles.themeToggle} 
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
        >
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
        
        <div className={styles.profile}>
          <div className={styles.avatar} aria-hidden="true">U</div>
          <span className={styles.userName}>User</span>
        </div>
      </div>
    </header>
  );
};

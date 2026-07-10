import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { Sun, Moon, User } from 'lucide-react';
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
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
        
        <div className={styles.profile}>
          <div className={styles.avatar} aria-hidden="true">
            <User size={18} />
          </div>
          <span className={styles.userName}>User</span>
        </div>
      </div>
    </header>
  );
};

import React from 'react';
import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/upload', label: 'Upload Document', icon: '📤' },
  { path: '/summary', label: 'Executive Summary', icon: '📝' },
  { path: '/risk', label: 'Risk Analysis', icon: '🚩' },
  { path: '/clauses', label: 'Clause Intelligence', icon: '🔍' },
  { path: '/chat', label: 'AI Contract Assistant', icon: '🤖' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export const Sidebar = () => {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <span className={styles.logoIcon} aria-hidden="true">⚖️</span>
        <span className={styles.logoText}>Legal AI</span>
      </div>
      
      <nav className={styles.nav}>
        <ul className={styles.navList}>
          {navItems.map((item) => (
            <li key={item.path} className={styles.navItem}>
              <NavLink 
                to={item.path} 
                className={({ isActive }) => 
                  `${styles.navLink} ${isActive ? styles.active : ''}`
                }
              >
                <span className={styles.icon} aria-hidden="true">{item.icon}</span>
                <span className={styles.label}>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      
      <div className={styles.footer}>
        <p className={styles.version}>v1.0.0-beta</p>
      </div>
    </aside>
  );
};

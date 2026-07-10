import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, FileText, AlertTriangle, Search, Bot, Settings, Scale } from 'lucide-react';
import styles from './Sidebar.module.css';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/upload', label: 'Upload Document', icon: UploadCloud },
  { path: '/summary', label: 'Executive Summary', icon: FileText },
  { path: '/risk', label: 'Risk Analysis', icon: AlertTriangle },
  { path: '/clauses', label: 'Clause Intelligence', icon: Search },
  { path: '/chat', label: 'AI Contract Assistant', icon: Bot },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar = () => {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <Scale className={styles.logoIcon} aria-hidden="true" size={28} />
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
                <span className={styles.icon} aria-hidden="true">
                  <item.icon size={20} />
                </span>
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

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * THEME TOGGLE - Compact Theme Switcher
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Simplified theme toggle for header integration
 * Falls back to FloatingThemeButton functionality
 */

import React from 'react';
import { useTheme } from '../../../contexts/ThemeContext';
import styles from './ThemeToggle.module.css';

export const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();

  const getThemeIcon = () => {
    switch (theme) {
      case 'dark':
        return '🌙';
      case 'light':
        return '☀️';
      case 'win11':
        return '🪟';
      case 'cyberpunk':
        return '🌃';
      default:
        return '🎨';
    }
  };

  return (
    <button
      onClick={toggleTheme}
      className={styles.toggle}
      aria-label={`Current theme: ${theme}. Click to change theme`}
      title={`Theme: ${theme}`}
    >
      <span className={styles.icon}>{getThemeIcon()}</span>
    </button>
  );
};

export default ThemeToggle;

/**
 * CompactThemeSelector - Discrete Theme Switcher for Header
 *
 * 🎯 ZERO INLINE STYLES - 100% CSS Module
 * ✅ Theme-agnostic (Matrix + Enterprise)
 * ✅ Matches MaximusHeader design
 */

import React, { useState, useEffect } from "react";
import styles from "./CompactThemeSelector.module.css";

const THEMES = [
  {
    id: "default",
    icon: "🟢",
    name: "Matrix",
    description: "Cyberpunk style",
  },
  {
    id: "enterprise",
    icon: "💼",
    name: "Enterprise",
    description: "Professional flat",
  },
];

export const CompactThemeSelector = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentTheme, setCurrentTheme] = useState("default");

  useEffect(() => {
    // Load current theme from localStorage or data attribute
    const savedTheme = localStorage.getItem("theme") || "default";
    const rootTheme =
      document.documentElement.getAttribute("data-theme") || "default";
    setCurrentTheme(rootTheme || savedTheme);
  }, []);

  const handleThemeChange = (themeId) => {
    setCurrentTheme(themeId);
    document.documentElement.setAttribute("data-theme", themeId);
    localStorage.setItem("theme", themeId);
    setIsOpen(false);
  };

  const currentThemeData =
    THEMES.find((t) => t.id === currentTheme) || THEMES[0];

  return (
    <div className={styles.container}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={styles.toggle}
        title={`Theme: ${currentThemeData.name}`}
        aria-label="Theme selector"
        aria-expanded={isOpen}
      >
        {currentThemeData.icon}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          role="menu"
          aria-label="Theme selection menu"
          tabIndex={-1}
          className={styles.dropdown}
          onMouseLeave={() => setIsOpen(false)}
        >
          {/* Header */}
          <div className={styles.dropdownHeader}>🎨 Theme</div>

          {/* Theme Options */}
          {THEMES.map((theme) => (
            <button
              key={theme.id}
              onClick={() => handleThemeChange(theme.id)}
              className={`${styles.themeButton} ${currentTheme === theme.id ? styles.active : ""}`}
              role="menuitem"
              aria-current={currentTheme === theme.id ? "true" : undefined}
            >
              <span className={styles.themeIcon}>{theme.icon}</span>
              <div className={styles.themeName}>
                {theme.name}
                <div className={styles.themeDescription}>
                  {theme.description}
                </div>
              </div>
              {currentTheme === theme.id && (
                <span className={styles.checkmark}>✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default CompactThemeSelector;

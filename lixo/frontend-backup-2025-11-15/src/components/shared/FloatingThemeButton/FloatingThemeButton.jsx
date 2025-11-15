/**
 * FloatingThemeButton Component - PAGANI Quality
 * ===============================================
 *
 * Floating action button for instant theme discovery
 * Always visible, smooth interactions, delightful UX
 *
 * Features:
 * - Click outside to close
 * - Escape key support
 * - Keyboard navigation
 * - Smooth animations
 * - Category grouping
 * - Active theme indicator
 * - Mobile responsive
 * - Accessibility first
 *
 * @example
 * <FloatingThemeButton position="top-right" />
 */

import React, { useState, useCallback, useEffect } from "react";
import PropTypes from "prop-types";
import { useTheme } from "../../../hooks/useTheme";
import { useClickOutside } from "../../../hooks/useClickOutside";
import { themes, themeCategories } from "../../../themes";
import styles from "./FloatingThemeButton.module.css";

export const FloatingThemeButton = ({
  position = "top-right",
  pulseOnMount = true,
  pulseDelay = 3000,
}) => {
  const { theme, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [shouldPulse, setShouldPulse] = useState(false);

  // Click outside to close
  const dropdownRef = useClickOutside(
    useCallback(() => setIsOpen(false), []),
    isOpen,
  );

  // Pulse animation on first mount (attention grabber)
  useEffect(() => {
    if (!pulseOnMount) return;

    const timer = setTimeout(() => {
      setShouldPulse(true);
      // Stop pulse after 3 cycles (6 seconds)
      setTimeout(() => setShouldPulse(false), 6000);
    }, pulseDelay);

    return () => clearTimeout(timer);
  }, [pulseOnMount, pulseDelay]);

  // Toggle dropdown
  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
    setShouldPulse(false); // Stop pulse when user interacts
  }, []);

  // Handle theme selection
  const handleThemeSelect = useCallback(
    (themeId) => {
      setTheme(themeId);
      setIsOpen(false);
    },
    [setTheme],
  );

  // Group themes by category
  const themesByCategory = themes.reduce((acc, themeItem) => {
    const category = themeItem.category || "other";
    if (!acc[category]) acc[category] = [];
    acc[category].push(themeItem);
    return acc;
  }, {});

  // Get position class
  const positionClass = position.replace("-", "");
  const positionClassName =
    positionClass.charAt(0).toLowerCase() +
    positionClass.slice(1).replace(/[A-Z]/g, (match) => match);

  return (
    <div
      ref={dropdownRef}
      className={`${styles.floatingButton} ${styles[positionClassName]}`}
      data-position={position}
    >
      {/* Main Floating Button */}
      <button
        type="button"
        onClick={handleToggle}
        className={`${styles.button} ${isOpen ? styles.open : ""} ${shouldPulse ? styles.pulse : ""}`}
        aria-label="Change theme"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        title="Choose Theme"
      >
        <span className={styles.icon} aria-hidden="true">
          🎨
        </span>
      </button>

      {/* Dropdown Menu */}
      <div
        className={`${styles.dropdown} ${isOpen ? styles.open : ""}`}
        role="menu"
        aria-label="Theme selector"
      >
        {/* Header */}
        <div className={styles.dropdownHeader}>
          <h3 className={styles.dropdownTitle}>Choose Theme</h3>
        </div>

        {/* Theme Categories */}
        {Object.entries(themesByCategory).map(
          ([categoryId, categoryThemes]) => {
            const categoryInfo = themeCategories[categoryId] || {
              name: categoryId,
              icon: "📦",
              description: "Themes",
            };

            return (
              <div key={categoryId} className={styles.categorySection}>
                {/* Category Label */}
                <div className={styles.categoryLabel}>
                  <span aria-hidden="true">{categoryInfo.icon}</span>
                  <span>{categoryInfo.name}</span>
                </div>

                {/* Theme Cards */}
                {categoryThemes.map((themeItem) => (
                  <button
                    key={themeItem.id}
                    type="button"
                    onClick={() => handleThemeSelect(themeItem.id)}
                    className={`${styles.themeCard} ${theme === themeItem.id ? styles.active : ""}`}
                    role="menuitem"
                    aria-current={theme === themeItem.id ? "true" : "false"}
                    title={themeItem.description}
                  >
                    {/* Theme Preview/Icon */}
                    <div
                      className={styles.themePreview}
                      style={{
                        background: themeItem.primary,
                        color: themeItem.id === "windows11" ? "#000" : "#fff",
                      }}
                      aria-hidden="true"
                    >
                      {themeItem.icon}
                    </div>

                    {/* Theme Info */}
                    <div className={styles.themeInfo}>
                      <p className={styles.themeName}>{themeItem.name}</p>
                      <p className={styles.themeDescription}>
                        {themeItem.description}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            );
          },
        )}
      </div>
    </div>
  );
};

FloatingThemeButton.propTypes = {
  /** Position of the floating button */
  position: PropTypes.oneOf([
    "top-right",
    "top-left",
    "bottom-right",
    "bottom-left",
  ]),
  /** Enable pulse animation on mount */
  pulseOnMount: PropTypes.bool,
  /** Delay before pulse animation starts (ms) */
  pulseDelay: PropTypes.number,
};

export default FloatingThemeButton;

import React from "react";
import styles from "./LoadingSpinner.module.css";

/**
 * Boris Cherny Standard - GAP #82 FIX: Add role="status" and aria-label for accessibility
 */
export const LoadingSpinner = ({
  size = "md",
  variant = "cyber",
  text,
  fullScreen = false,
  className = "",
  ariaLabel,
  ...props
}) => {
  const containerClasses = [
    styles.container,
    fullScreen && styles.fullScreen,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const spinnerClasses = [styles.spinner, styles[size], styles[variant]]
    .filter(Boolean)
    .join(" ");

  // Determine aria-label: use custom ariaLabel, or fallback to text, or default
  const accessibleLabel = ariaLabel || text || "Loading...";

  return (
    <div
      className={containerClasses}
      role="status"
      aria-label={accessibleLabel}
      aria-live="polite"
      {...props}
    >
      <div className={spinnerClasses} aria-hidden="true">
        <div className={styles.ring}></div>
        <div className={styles.ring}></div>
        <div className={styles.ring}></div>
        <div className={styles.ring}></div>
      </div>
      {text && (
        <p className={styles.text} aria-hidden="true">
          {text}
        </p>
      )}
      {/* Visually hidden text for screen readers */}
      <span className="sr-only">{accessibleLabel}</span>
    </div>
  );
};

export default LoadingSpinner;

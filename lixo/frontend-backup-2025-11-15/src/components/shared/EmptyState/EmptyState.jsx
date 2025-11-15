/**
 * EmptyState Component
 * Boris Cherny Standard - Reusable empty state with consistent UX
 *
 * Usage:
 * <EmptyState
 *   icon="🔍"
 *   title="No results found"
 *   message="Try adjusting your search criteria"
 *   action={<Button onClick={handleReset}>Reset Filters</Button>}
 * />
 */

import React from "react";
import PropTypes from "prop-types";
import styles from "./EmptyState.module.css";

export const EmptyState = ({
  icon = "📭",
  title = "No data available",
  message,
  action,
  variant = "default",
  size = "md",
  className = "",
}) => {
  const sizeClasses = {
    sm: styles.sm,
    md: styles.md,
    lg: styles.lg,
  };

  return (
    <div
      className={`${styles.container} ${styles[variant]} ${sizeClasses[size]} ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className={styles.iconWrapper} aria-hidden="true">
        <span className={styles.icon}>{icon}</span>
      </div>

      <div className={styles.content}>
        <h3 className={styles.title}>{title}</h3>
        {message && <p className={styles.message}>{message}</p>}
      </div>

      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
};

EmptyState.propTypes = {
  icon: PropTypes.node,
  title: PropTypes.string.isRequired,
  message: PropTypes.string,
  action: PropTypes.node,
  variant: PropTypes.oneOf(["default", "cyber", "osint", "analytics"]),
  size: PropTypes.oneOf(["sm", "md", "lg"]),
  className: PropTypes.string,
};

export default EmptyState;

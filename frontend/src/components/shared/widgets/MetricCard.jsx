/**
 * MetricCard - Reusable Metric Display Widget
 *
 * Generic metric card component used across all dashboards.
 * Displays a label and value with optional loading state and custom styling.
 *
 * Usage:
 * <MetricCard
 *   label="Active Scans"
 *   value={42}
 *   loading={false}
 *   variant="primary"
 *   className="custom-class"
 * />
 *
 * @param {string} label - Metric label text
 * @param {number|string} value - Metric value to display
 * @param {boolean} loading - Show loading state
 * @param {string} variant - Color variant (primary, success, warning, danger, info)
 * @param {string} className - Additional CSS classes
 * @param {string} loadingText - Text to show when loading (default: "...")
 */

import React from 'react';
import PropTypes from 'prop-types';
import './MetricCard.css';

export const MetricCard = ({
  label,
  value,
  loading = false,
  variant = 'primary',
  className = '',
  loadingText = '...',
  ariaLabel
}) => {
  const cardClasses = `metric-card metric-card-${variant} ${className}`;

  return (
    <div className={cardClasses} aria-label={ariaLabel || `${label}: ${value}`}>
      <span className="metric-card-label">{label}</span>
      <span className="metric-card-value">
        {loading ? loadingText : value}
      </span>
    </div>
  );
};

MetricCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
  loading: PropTypes.bool,
  variant: PropTypes.oneOf(['primary', 'success', 'warning', 'danger', 'info']),
  className: PropTypes.string,
  loadingText: PropTypes.string,
  ariaLabel: PropTypes.string
};

export default MetricCard;

/**
 * Enhanced Loading Component with Skeleton Screens
 * MAXIMUS Vértice - Frontend Phase 3
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import styles from './LoadingStates.module.css';

/**
 * Spinner component - themed loading indicator
 */
export const Spinner = ({ size = 'md', color = 'primary', className = '' }) => {
  const sizeClasses = {
    sm: styles.spinnerSm,
    md: styles.spinnerMd,
    lg: styles.spinnerLg,
    xl: styles.spinnerXl
  };

  return (
    <div 
      className={`${styles.spinner} ${sizeClasses[size]} ${styles[`spinner${color.charAt(0).toUpperCase() + color.slice(1)}`]} ${className}`}
      role="status"
      aria-label="Loading"
    >
      <span className={styles.spinnerInner}></span>
    </div>
  );
};

/**
 * Full-page dashboard loader
 */
export const DashboardLoader = ({ message }) => {
  const { t } = useTranslation();
  
  return (
    <div className={styles.dashboardLoader}>
      <div className={styles.loaderContent}>
        <Spinner size="xl" />
        <p className={styles.loaderText}>
          {message || t('common.loading').toUpperCase()}...
        </p>
        <div className={styles.loaderPulse}></div>
      </div>
    </div>
  );
};

/**
 * Skeleton card for content loading
 */
export const SkeletonCard = ({ lines = 3, hasImage = false }) => {
  return (
    <div className={styles.skeletonCard}>
      {hasImage && <div className={styles.skeletonImage}></div>}
      <div className={styles.skeletonContent}>
        <div className={styles.skeletonTitle}></div>
        {Array.from({ length: lines }).map((_, i) => (
          <div 
            key={i} 
            className={styles.skeletonLine}
            style={{ width: `${100 - (i * 10)}%` }}
          ></div>
        ))}
      </div>
    </div>
  );
};

/**
 * Skeleton list for loading lists
 */
export const SkeletonList = ({ items = 5 }) => {
  return (
    <div className={styles.skeletonList}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className={`${styles.skeletonItem} stagger-${i + 1}`}>
          <div className={styles.skeletonItemIcon}></div>
          <div className={styles.skeletonItemContent}>
            <div className={styles.skeletonItemTitle}></div>
            <div className={styles.skeletonItemText}></div>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Progress bar with animation
 */
export const ProgressBar = ({ 
  progress = 0, 
  label = '', 
  showPercentage = true,
  variant = 'primary' 
}) => {
  return (
    <div className={styles.progressContainer}>
      {label && (
        <div className={styles.progressLabel}>
          <span>{label}</span>
          {showPercentage && <span>{progress}%</span>}
        </div>
      )}
      <div className={styles.progressTrack}>
        <div 
          className={`${styles.progressBar} ${styles[`progress${variant.charAt(0).toUpperCase() + variant.slice(1)}`]}`}
          style={{ width: `${progress}%` }}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin="0"
          aria-valuemax="100"
        ></div>
      </div>
    </div>
  );
};

/**
 * Pulse loader - simple animated dots
 */
export const PulseLoader = () => {
  return (
    <div className={styles.pulseLoader}>
      <span className={styles.pulseDot}></span>
      <span className={styles.pulseDot}></span>
      <span className={styles.pulseDot}></span>
    </div>
  );
};

/**
 * Loading overlay for inline content
 */
export const LoadingOverlay = ({ isLoading, children, blur = true }) => {
  if (!isLoading) return children;

  return (
    <div className={styles.loadingOverlayContainer}>
      <div className={blur ? styles.loadingOverlayBlurred : ''}>
        {children}
      </div>
      <div className={styles.loadingOverlay}>
        <Spinner size="lg" />
      </div>
    </div>
  );
};

export default DashboardLoader;

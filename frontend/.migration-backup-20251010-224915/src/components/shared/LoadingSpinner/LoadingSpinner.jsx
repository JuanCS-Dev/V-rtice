import React from 'react';
import styles from './LoadingSpinner.module.css';

export const LoadingSpinner = ({
  size = 'md',
  variant = 'cyber',
  text,
  fullScreen = false,
  className = '',
  ...props
}) => {
  const containerClasses = [
    styles.container,
    fullScreen && styles.fullScreen,
    className
  ].filter(Boolean).join(' ');

  const spinnerClasses = [
    styles.spinner,
    styles[size],
    styles[variant]
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses} {...props}>
      <div className={spinnerClasses}>
        <div className={styles.ring}></div>
        <div className={styles.ring}></div>
        <div className={styles.ring}></div>
        <div className={styles.ring}></div>
      </div>
      {text && <p className={styles.text}>{text}</p>}
    </div>
  );
};

export default LoadingSpinner;

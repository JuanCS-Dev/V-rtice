import React from 'react';
import styles from './Button.module.css';

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  const buttonClasses = [
    styles.button,
    styles[variant],
    styles[size],
    loading && styles.loading,
    fullWidth && styles.fullWidth,
    className
  ].filter(Boolean).join(' ');

  // Boris Cherny Standard - GAP #85 FIX: Add aria-busy for loading state
  return (
    <button
      className={buttonClasses}
      disabled={disabled || loading}
      onClick={onClick}
      type={type}
      aria-busy={loading}
      aria-disabled={disabled || loading}
      {...props}
    >
      {loading && <span className={styles.spinner} aria-hidden="true" />}
      {!loading && icon && iconPosition === 'left' && (
        <i className={`${styles.icon} ${icon}`} aria-hidden="true" />
      )}
      <span className={styles.content}>{children}</span>
      {!loading && icon && iconPosition === 'right' && (
        <i className={`${styles.icon} ${icon}`} aria-hidden="true" />
      )}
    </button>
  );
};

export default Button;

import React from 'react';
import styles from './Alert.module.css';

export const Alert = ({
  children,
  variant = 'info',
  title,
  icon,
  onClose,
  className = '',
  ...props
}) => {
  const alertClasses = [
    styles.alert,
    styles[variant],
    className
  ].filter(Boolean).join(' ');

  const getDefaultIcon = () => {
    switch (variant) {
      case 'success':
        return <i className="fas fa-check-circle" aria-hidden="true"></i>;
      case 'warning':
        return <i className="fas fa-exclamation-triangle" aria-hidden="true"></i>;
      case 'error':
        return <i className="fas fa-times-circle" aria-hidden="true"></i>;
      case 'info':
      default:
        return <i className="fas fa-info-circle" aria-hidden="true"></i>;
    }
  };

  return (
    <div
      className={alertClasses}
      role="alert"
      aria-live={variant === 'error' ? 'assertive' : 'polite'}
      aria-atomic="true"
      {...props}
    >
      <div className={styles.icon}>
        {icon || getDefaultIcon()}
      </div>

      <div className={styles.content}>
        {title && <div className={styles.title}>{title}</div>}
        <div className={styles.message}>{children}</div>
      </div>

      {onClose && (
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Fechar"
        >
          <i className="fas fa-times" aria-hidden="true"></i>
        </button>
      )}
    </div>
  );
};

export default Alert;

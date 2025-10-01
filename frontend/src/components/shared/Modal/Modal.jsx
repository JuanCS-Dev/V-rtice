import React, { useEffect } from 'react';
import { useKeyPress } from '../../../hooks';
import styles from './Modal.module.css';

export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  variant = 'cyber',
  size = 'md',
  footer,
  closeOnEscape = true,
  closeOnBackdrop = true,
  className = '',
  ...props
}) => {
  const escapePressed = useKeyPress('Escape');

  useEffect(() => {
    if (escapePressed && closeOnEscape && isOpen) {
      onClose();
    }
  }, [escapePressed, closeOnEscape, isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const modalClasses = [
    styles.modal,
    styles[variant],
    styles[size],
    className
  ].filter(Boolean).join(' ');

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && closeOnBackdrop) {
      onClose();
    }
  };

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={modalClasses} {...props}>
        {/* Header */}
        <div className={styles.header}>
          {title && <h3 className={styles.title}>{title}</h3>}
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Fechar"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>

        {/* Body */}
        <div className={styles.body}>
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className={styles.footer}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export default Modal;

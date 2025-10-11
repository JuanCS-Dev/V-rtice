/* eslint-disable react-refresh/only-export-components */
/**
 * Toast Notification System
 * MAXIMUS Vértice - Frontend Phase 3
 * 
 * Purpose: Rich feedback for user actions
 * - Success celebrations
 * - Error shake animations
 * - Warning pulse
 * - Info fade-in
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import styles from './Toast.module.css';

const ToastContext = createContext();

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

let toastId = 0;

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, options = {}) => {
    const id = toastId++;
    const toast = {
      id,
      message,
      type: options.type || 'info', // success, error, warning, info
      duration: options.duration || 5000,
      icon: options.icon,
      action: options.action,
      ...options
    };

    setToasts(prev => [...prev, toast]);

    // Auto-dismiss
    if (toast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, toast.duration);
    }

    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.map(toast => 
      toast.id === id ? { ...toast, closing: true } : toast
    ));

    // Remove after animation
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id));
    }, 300);
  }, []);

  const success = useCallback((message, options) => {
    return addToast(message, { ...options, type: 'success' });
  }, [addToast]);

  const error = useCallback((message, options) => {
    return addToast(message, { ...options, type: 'error' });
  }, [addToast]);

  const warning = useCallback((message, options) => {
    return addToast(message, { ...options, type: 'warning' });
  }, [addToast]);

  const info = useCallback((message, options) => {
    return addToast(message, { ...options, type: 'info' });
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ success, error, warning, info, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
};

const ToastContainer = ({ toasts, onClose }) => {
  if (toasts.length === 0) return null;

  return createPortal(
    <div className={styles.toastContainer} aria-live="polite" aria-atomic="true">
      {toasts.map((toast, index) => (
        <Toast 
          key={toast.id} 
          toast={toast} 
          onClose={() => onClose(toast.id)}
          index={index}
        />
      ))}
    </div>,
    document.body
  );
};

const Toast = ({ toast, onClose, index }) => {
  const { type, message, icon, action, closing } = toast;

  const icons = {
    success: (
      <svg className={styles.toastIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M5 13l4 4L19 7"
          className={styles.successCheckmark}
        />
      </svg>
    ),
    error: (
      <svg className={styles.toastIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M6 18L18 6M6 6l12 12"
          className={styles.errorX}
        />
      </svg>
    ),
    warning: (
      <svg className={styles.toastIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
    ),
    info: (
      <svg className={styles.toastIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    )
  };

  return (
    <div 
      className={`${styles.toast} ${styles[type]} ${closing ? styles.closing : ''}`}
      role="alert"
      style={{ '--index': index }}
    >
      <div className={styles.toastContent}>
        <div className={styles.toastIconContainer}>
          {icon || icons[type]}
        </div>
        <div className={styles.toastMessage}>
          {message}
        </div>
        {action && (
          <button 
            className={styles.toastAction}
            onClick={(e) => {
              e.stopPropagation();
              action.onClick();
            }}
          >
            {action.label}
          </button>
        )}
        <button 
          className={styles.toastClose}
          onClick={onClose}
          aria-label="Close notification"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className={styles.toastProgress}></div>
    </div>
  );
};

export default ToastProvider;

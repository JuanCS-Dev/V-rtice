/**
 * Frontend Error Logger
 * =====================
 *
 * Centralized error logging to backend for observability.
 * Boris Cherny Pattern: Type-safe error handling with structured logging.
 *
 * Usage:
 * ```javascript
 * import { logError, logWarning, logInfo } from '@/utils/errorLogger';
 *
 * try {
 *   await fetchData();
 * } catch (error) {
 *   logError('Failed to fetch data', error, { component: 'Dashboard' });
 * }
 * ```
 *
 * Governed by: Constituição Vértice v2.7 - ADR-004
 */

import { apiClient } from '../api/client';
import logger from './logger';

/**
 * Log error to backend
 *
 * @param {string} message - Error message
 * @param {Error|string} error - Error object or string
 * @param {Object} context - Additional context (component, action, etc.)
 */
export const logError = async (message, error = null, context = {}) => {
  try {
    const errorData = {
      level: 'error',
      message,
      stack: error instanceof Error ? error.stack : undefined,
      context: {
        ...context,
        errorType: error?.name,
        errorMessage: error?.message,
      },
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    };

    // Send to backend (fire and forget - don't block on logging)
    apiClient.post('/api/errors/log', errorData).catch((logErr) => {
      // Don't let logging errors crash the app
      logger.warn('Failed to log error to backend:', logErr);
    });

    // Also log locally for development
    logger.error(message, error, context);
  } catch (err) {
    // Fail silently - don't break app if logging fails
    logger.warn('Error logger failed:', err);
  }
};

/**
 * Log warning to backend
 *
 * @param {string} message - Warning message
 * @param {Object} context - Additional context
 */
export const logWarning = async (message, context = {}) => {
  try {
    const warningData = {
      level: 'warn',
      message,
      context,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    };

    apiClient.post('/api/errors/log', warningData).catch((logErr) => {
      logger.warn('Failed to log warning to backend:', logErr);
    });

    logger.warn(message, context);
  } catch (err) {
    logger.warn('Warning logger failed:', err);
  }
};

/**
 * Log info to backend
 *
 * @param {string} message - Info message
 * @param {Object} context - Additional context
 */
export const logInfo = async (message, context = {}) => {
  try {
    const infoData = {
      level: 'info',
      message,
      context,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };

    apiClient.post('/api/errors/log', infoData).catch((logErr) => {
      logger.warn('Failed to log info to backend:', logErr);
    });

    logger.info(message, context);
  } catch (err) {
    logger.warn('Info logger failed:', err);
  }
};

/**
 * Global error handler
 * Automatically logs unhandled errors
 */
export const setupGlobalErrorHandler = () => {
  // Catch unhandled errors
  window.addEventListener('error', (event) => {
    logError(
      'Unhandled error',
      event.error,
      {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      }
    );
  });

  // Catch unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    logError(
      'Unhandled promise rejection',
      event.reason,
      {
        promise: 'unhandled',
      }
    );
  });

  logger.info('Global error handlers configured');
};

export default {
  logError,
  logWarning,
  logInfo,
  setupGlobalErrorHandler,
};

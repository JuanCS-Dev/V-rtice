/**
 * Logging Utility - Production-Safe Logger
 * =========================================
 *
 * Centralizes logging with environment-aware behavior:
 * - Development: Full logging to console
 * - Production: Suppresses debug/info, keeps errors
 *
 * Usage:
 *   import logger from '@/utils/logger';
 *   logger.debug('Debug info', data);
 *   logger.info('Info message');
 *   logger.warn('Warning', context);
 *   logger.error('Error occurred', error);
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4
};

class Logger {
  constructor() {
    // In production, only show warnings and errors
    this.level = import.meta.env.PROD
      ? LOG_LEVELS.WARN
      : LOG_LEVELS.DEBUG;
  }

  debug(...args) {
    if (this.level <= LOG_LEVELS.DEBUG) {
      console.debug('[DEBUG]', ...args);
    }
  }

  info(...args) {
    if (this.level <= LOG_LEVELS.INFO) {
      console.info('[INFO]', ...args);
    }
  }

  warn(...args) {
    if (this.level <= LOG_LEVELS.WARN) {
      console.warn('[WARN]', ...args);
    }
  }

  error(...args) {
    if (this.level <= LOG_LEVELS.ERROR) {
      console.error('[ERROR]', ...args);
    }
  }

  // Group logging for complex data
  group(label, callback) {
    if (this.level <= LOG_LEVELS.INFO) {
      console.group(label);
      if (typeof callback === 'function') {
        callback();
      }
      console.groupEnd();
    }
  }

  // Table logging for structured data
  table(data) {
    if (this.level <= LOG_LEVELS.INFO) {
      console.table(data);
    }
  }

  // Set log level programmatically
  setLevel(level) {
    if (LOG_LEVELS.hasOwnProperty(level)) {
      this.level = LOG_LEVELS[level];
    }
  }
}

// Export singleton instance
const logger = new Logger();
export default logger;

// Export LOG_LEVELS for external configuration
export { LOG_LEVELS };

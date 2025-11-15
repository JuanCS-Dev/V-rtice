/**
 * Centralized Error Handling Utilities
 *
 * DOUTRINA VÉRTICE - GAP #6 (P1)
 * Standardized error handling with user-friendly messages
 *
 * Following Boris Cherny's principle: "Errors should be actionable"
 */

import type { ErrorResponse } from '../types/errors';

// ============================================================================
// Error Code to User Message Mapping
// ============================================================================

/**
 * User-friendly error messages for error codes
 *
 * Maps technical error codes to messages users can understand and act on
 */
export const ERROR_MESSAGES: Record<string, string> = {
  // Authentication errors
  AUTH_001: 'Please log in to continue.',
  AUTH_002: 'Invalid authentication token. Please log in again.',
  AUTH_003: 'Your session has expired. Please log in again.',
  AUTH_004: 'You do not have permission to perform this action.',

  // Validation errors
  VAL_422: 'Please check your input and try again.',
  VAL_001: 'Required field is missing.',
  VAL_002: 'Invalid format provided.',
  VAL_003: 'Value out of acceptable range.',

  // Rate limiting
  RATE_429: 'Too many requests. Please wait a moment and try again.',
  RATE_001: 'Request quota exceeded. Please try again later.',

  // System errors
  SYS_500: 'An unexpected error occurred. Please try again later.',
  SYS_503: 'Service temporarily unavailable. Please try again in a few moments.',
  SYS_504: 'Request timed out. Please try again.',

  // External service errors
  EXT_001: 'External service is temporarily unavailable.',
  EXT_002: 'External service request timed out.',
  EXT_003: 'Received invalid response from external service.',

  // Resource errors
  RES_001: 'Requested resource not found.',
  RES_002: 'Resource already exists.',
  RES_003: 'Resource is locked and cannot be modified.',

  // Default fallback
  UNKNOWN: 'An error occurred. Please try again or contact support.',
};

// ============================================================================
// Error Severity Levels
// ============================================================================

export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

/**
 * Map error codes to severity levels
 */
export function getErrorSeverity(errorCode: string): ErrorSeverity {
  if (errorCode.startsWith('AUTH_')) {
    return ErrorSeverity.WARNING;
  }

  if (errorCode.startsWith('VAL_')) {
    return ErrorSeverity.INFO;
  }

  if (errorCode.startsWith('RATE_')) {
    return ErrorSeverity.WARNING;
  }

  if (errorCode.startsWith('SYS_') || errorCode.startsWith('EXT_')) {
    return ErrorSeverity.ERROR;
  }

  return ErrorSeverity.ERROR;
}

// ============================================================================
// Error Type Definitions
// ============================================================================

/**
 * Standardized error interface
 */
export interface ApiError {
  message: string;
  errorCode: string;
  requestId: string;
  path: string;
  severity: ErrorSeverity;
  timestamp: string;
  validationErrors?: Array<{
    field: string;
    message: string;
  }>;
}

// ============================================================================
// Error Parsing Functions
// ============================================================================

/**
 * Parse API error response into standardized format
 *
 * @param error - Error from API call
 * @returns Standardized ApiError object
 */
export function parseApiError(error: any): ApiError {
  // Extract error details
  const errorCode = error?.error_code || error?.errorCode || 'UNKNOWN';
  const requestId = error?.request_id || error?.requestId || 'unknown';
  const path = error?.path || 'unknown';
  const timestamp = error?.timestamp || new Date().toISOString();

  // Get user-friendly message
  const message = ERROR_MESSAGES[errorCode] || error?.detail || ERROR_MESSAGES.UNKNOWN;

  // Parse validation errors if present
  const validationErrors = error?.validation_errors?.map((ve: any) => ({
    field: ve.loc.join('.'),
    message: ve.msg,
  }));

  return {
    message,
    errorCode,
    requestId,
    path,
    severity: getErrorSeverity(errorCode),
    timestamp,
    validationErrors,
  };
}

/**
 * Format validation errors for display
 *
 * @param validationErrors - Array of validation errors
 * @returns Formatted error message
 */
export function formatValidationErrors(
  validationErrors: Array<{ field: string; message: string }>
): string {
  if (validationErrors.length === 0) {
    return 'Please check your input and try again.';
  }

  if (validationErrors.length === 1) {
    return validationErrors[0].message;
  }

  return validationErrors.map((e) => `${e.field}: ${e.message}`).join('\n');
}

// ============================================================================
// Error Handling Functions
// ============================================================================

/**
 * Handle API error and return user-friendly message
 *
 * @param error - Error from API call
 * @returns User-friendly error message
 *
 * @example
 * ```typescript
 * try {
 *   await apiClient.post('/api/v1/scan/start', data);
 * } catch (error) {
 *   const message = handleApiError(error);
 *   toast.error(message);
 * }
 * ```
 */
export function handleApiError(error: any): string {
  const parsed = parseApiError(error);

  if (parsed.validationErrors && parsed.validationErrors.length > 0) {
    return formatValidationErrors(parsed.validationErrors);
  }

  return parsed.message;
}

/**
 * Log error with request ID for debugging
 *
 * @param error - Parsed API error
 * @param context - Additional context (e.g., component name)
 */
export function logError(error: ApiError, context?: string) {
  const logData = {
    requestId: error.requestId,
    errorCode: error.errorCode,
    path: error.path,
    severity: error.severity,
    timestamp: error.timestamp,
    context,
  };

  if (error.severity === ErrorSeverity.CRITICAL) {
    console.error('[CRITICAL ERROR]', logData);
  } else if (error.severity === ErrorSeverity.ERROR) {
    console.error('[ERROR]', logData);
  } else if (error.severity === ErrorSeverity.WARNING) {
    console.warn('[WARNING]', logData);
  } else {
    console.info('[INFO]', logData);
  }
}

/**
 * Check if error is retryable
 *
 * @param errorCode - Error code
 * @returns Whether the error is retryable
 */
export function isRetryableError(errorCode: string): boolean {
  const retryableErrors = [
    'SYS_503', // Service unavailable
    'SYS_504', // Timeout
    'EXT_001', // External service unavailable
    'EXT_002', // External service timeout
    'RATE_429', // Rate limit (can retry after delay)
  ];

  return retryableErrors.includes(errorCode);
}

/**
 * Get retry delay for retryable errors
 *
 * @param errorCode - Error code
 * @param attempt - Retry attempt number (0-indexed)
 * @returns Delay in milliseconds
 */
export function getRetryDelay(errorCode: string, attempt: number = 0): number {
  // Exponential backoff: 2^attempt seconds
  const baseDelay = Math.pow(2, attempt) * 1000;

  // Cap at 30 seconds
  return Math.min(baseDelay, 30000);
}

// ============================================================================
// React Hook for Error Handling
// ============================================================================

import { useState, useCallback } from 'react';

/**
 * Hook for handling API errors
 *
 * @example
 * ```typescript
 * function MyComponent() {
 *   const { error, showError, clearError } = useErrorHandler();
 *
 *   async function handleSubmit() {
 *     try {
 *       await apiClient.post('/api/v1/scan/start', data);
 *     } catch (err) {
 *       showError(err);
 *     }
 *   }
 *
 *   return (
 *     <div>
 *       {error && <ErrorAlert error={error} onClose={clearError} />}
 *       <button onClick={handleSubmit}>Submit</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useErrorHandler() {
  const [error, setError] = useState<ApiError | null>(null);

  const showError = useCallback((err: any, context?: string) => {
    const parsed = parseApiError(err);
    logError(parsed, context);
    setError(parsed);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return { error, showError, clearError };
}

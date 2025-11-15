/**
 * Sentry Error Tracking - Frontend
 *
 * DOUTRINA VÉRTICE - GAP #8 (P2)
 * Production error tracking for React frontend
 *
 * Following Boris Cherny: "Errors should be observable"
 */

import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';

// ============================================================================
// CONFIGURATION
// ============================================================================

interface SentryConfig {
  dsn: string;
  environment: string;
  release?: string;
  tracesSampleRate: number;
  replaysSessionSampleRate: number;
  replaysOnErrorSampleRate: number;
}

const config: SentryConfig = {
  dsn: import.meta.env.VITE_SENTRY_DSN || '',
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',
  release: import.meta.env.VITE_RELEASE_VERSION || 'unknown',
  tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 1.0),
  replaysSessionSampleRate: Number(import.meta.env.VITE_SENTRY_REPLAYS_SESSION || 0.1),
  replaysOnErrorSampleRate: Number(import.meta.env.VITE_SENTRY_REPLAYS_ERROR || 1.0),
};

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize Sentry for React application.
 *
 * Call this once at app startup (in main.tsx):
 *   initSentry();
 *
 * Environment Variables:
 *   VITE_SENTRY_DSN: Your Sentry DSN (required)
 *   VITE_ENVIRONMENT: Environment (development, staging, production)
 *   VITE_RELEASE_VERSION: Release version
 *   VITE_SENTRY_TRACES_SAMPLE_RATE: Performance tracing sample rate (0.0-1.0)
 *   VITE_SENTRY_REPLAYS_SESSION: Session replay sample rate (0.0-1.0)
 *   VITE_SENTRY_REPLAYS_ERROR: Replay sample rate for errors (0.0-1.0)
 */
export function initSentry(): void {
  if (!config.dsn) {
    console.warn('[Sentry] DSN not configured. Error tracking disabled.');
    return;
  }

  try {
    Sentry.init({
      dsn: config.dsn,
      environment: config.environment,
      release: config.release,

      // Integrations
      integrations: [
        // Performance monitoring
        new BrowserTracing({
          // Track React Router navigation
          routingInstrumentation: Sentry.reactRouterV6Instrumentation(
            // React Router useEffect, useLocation, useNavigationType, createRoutesFromChildren, matchRoutes
          ),
        }),

        // Session replay (captures user interactions)
        new Sentry.Replay({
          maskAllText: true,          // Mask text (PII protection)
          blockAllMedia: true,         // Block images/video (PII + performance)
        }),
      ],

      // Performance monitoring
      tracesSampleRate: config.tracesSampleRate,

      // Session replay
      replaysSessionSampleRate: config.replaysSessionSampleRate,  // 10% of sessions
      replaysOnErrorSampleRate: config.replaysOnErrorSampleRate, // 100% when error occurs

      // Privacy
      beforeSend: beforeSendFilter,

      // Error handling
      ignoreErrors: [
        // Browser extensions
        'ResizeObserver loop',
        'Non-Error promise rejection captured',

        // Network errors
        'NetworkError',
        'Failed to fetch',

        // User aborted
        'AbortError',
      ],
    });

    console.log(`[Sentry] Initialized for environment: ${config.environment}`);
  } catch (error) {
    console.error('[Sentry] Failed to initialize:', error);
  }
}

// ============================================================================
// FILTERING & PRIVACY
// ============================================================================

function beforeSendFilter(event: Sentry.Event, hint: Sentry.EventHint): Sentry.Event | null {
  /**
   * Filter events before sending to Sentry.
   *
   * Use this to:
   * - Remove sensitive data
   * - Filter out noisy errors
   * - Add custom context
   */

  // Remove PII from request data
  if (event.request) {
    // Remove cookies
    if (event.request.cookies) {
      event.request.cookies = {};
    }

    // Remove auth headers
    if (event.request.headers) {
      delete event.request.headers['Authorization'];
      delete event.request.headers['Cookie'];
    }
  }

  // Filter console warnings (too noisy)
  if (event.level === 'warning' && event.logger === 'console') {
    return null;
  }

  return event;
}

// ============================================================================
// CONTEXT MANAGEMENT
// ============================================================================

/**
 * Set user context for error reports.
 *
 * Call this after login:
 *   setUserContext({ id: user.id, email: user.email, username: user.username });
 */
export function setUserContext(user: {
  id: string;
  email?: string;
  username?: string;
}): void {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
  });
}

/**
 * Clear user context.
 *
 * Call this on logout:
 *   clearUserContext();
 */
export function clearUserContext(): void {
  Sentry.setUser(null);
}

/**
 * Set custom context for error reports.
 *
 * Example:
 *   setCustomContext('scan', { target: 'example.com', scanId: 'scan-123' });
 */
export function setCustomContext(key: string, data: Record<string, any>): void {
  Sentry.setContext(key, data);
}

/**
 * Add breadcrumb for debugging trail.
 *
 * Breadcrumbs show the sequence of events leading to an error.
 *
 * Example:
 *   addBreadcrumb('API request started', 'http', 'info', {
 *     url: '/api/v1/scans',
 *     method: 'GET'
 *   });
 */
export function addBreadcrumb(
  message: string,
  category: string = 'custom',
  level: Sentry.SeverityLevel = 'info',
  data?: Record<string, any>
): void {
  Sentry.addBreadcrumb({
    message,
    category,
    level,
    data,
  });
}

// ============================================================================
// ERROR CAPTURING
// ============================================================================

/**
 * Manually capture an exception.
 *
 * Use for caught exceptions you want to track:
 *   try {
 *     riskyOperation();
 *   } catch (error) {
 *     captureException(error, 'warning', { context: '...' });
 *   }
 */
export function captureException(
  error: Error,
  level: Sentry.SeverityLevel = 'error',
  extras?: Record<string, any>
): string {
  if (extras) {
    Sentry.setContext('extras', extras);
  }

  return Sentry.captureException(error, { level });
}

/**
 * Capture a message (not an exception).
 *
 * Use for important events:
 *   captureMessage('Rate limit exceeded', 'warning', { endpoint: '/api/scans' });
 */
export function captureMessage(
  message: string,
  level: Sentry.SeverityLevel = 'info',
  extras?: Record<string, any>
): string {
  if (extras) {
    Sentry.setContext('extras', extras);
  }

  return Sentry.captureMessage(message, level);
}

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

/**
 * Start a performance transaction.
 *
 * Example:
 *   const transaction = startTransaction('fetchScans', 'http.client');
 *   // ... do work ...
 *   transaction.finish();
 */
export function startTransaction(name: string, op: string = 'function'): Sentry.Transaction {
  return Sentry.startTransaction({
    name,
    op,
  });
}

/**
 * Measure function execution time.
 *
 * Example:
 *   const result = await measurePerformance('fetchScans', async () => {
 *     return await fetch('/api/v1/scans');
 *   });
 */
export async function measurePerformance<T>(
  name: string,
  fn: () => Promise<T>
): Promise<T> {
  const transaction = startTransaction(name);

  try {
    const result = await fn();
    transaction.setStatus('ok');
    return result;
  } catch (error) {
    transaction.setStatus('internal_error');
    throw error;
  } finally {
    transaction.finish();
  }
}

// ============================================================================
// REACT ERROR BOUNDARY
// ============================================================================

/**
 * Sentry Error Boundary wrapper.
 *
 * Usage:
 *   <SentryErrorBoundary fallback={<ErrorFallback />}>
 *     <YourComponent />
 *   </SentryErrorBoundary>
 */
export const SentryErrorBoundary = Sentry.ErrorBoundary;

/**
 * Fallback component for error boundary.
 */
export function ErrorFallback({ error, resetError }: {
  error: Error;
  resetError: () => void;
}) {
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h2>Something went wrong</h2>
      <p style={{ color: '#666' }}>{error.message}</p>
      <button
        onClick={resetError}
        style={{
          marginTop: '1rem',
          padding: '0.5rem 1rem',
          background: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '0.25rem',
          cursor: 'pointer',
        }}
      >
        Try again
      </button>
    </div>
  );
}

// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Check if Sentry is enabled.
 */
export function isEnabled(): boolean {
  return Boolean(config.dsn);
}

/**
 * Flush pending events to Sentry.
 *
 * Call before app shutdown or navigation:
 *   await flush(2000);
 */
export function flush(timeout: number = 2000): Promise<boolean> {
  return Sentry.flush(timeout);
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

/*
// In main.tsx:

import { initSentry } from './lib/sentry';

initSentry();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// In App.tsx:

import { SentryErrorBoundary, ErrorFallback } from './lib/sentry';

function App() {
  return (
    <SentryErrorBoundary fallback={<ErrorFallback />}>
      <YourApp />
    </SentryErrorBoundary>
  );
}

// In auth flow:

import { setUserContext, clearUserContext } from './lib/sentry';

async function handleLogin(email: string, password: string) {
  const response = await loginUser(email, password);

  // Set user context
  setUserContext({
    id: response.user.id,
    email: response.user.email,
    username: response.user.username,
  });
}

async function handleLogout() {
  await logoutUser();

  // Clear user context
  clearUserContext();
}

// In components:

import { captureException, addBreadcrumb } from './lib/sentry';

function ScanComponent() {
  async function startScan() {
    try {
      addBreadcrumb('Starting scan', 'scan', 'info', { target: 'example.com' });

      const result = await fetch('/api/v1/scan/start', {...});

      return result;
    } catch (error) {
      captureException(error as Error, 'error', {
        action: 'start_scan',
        target: 'example.com',
      });

      throw error;
    }
  }
}
*/

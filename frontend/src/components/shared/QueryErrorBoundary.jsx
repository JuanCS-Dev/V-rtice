/**
 * QueryErrorBoundary - Specialized Error Boundary for React Query
 *
 * Handles errors from useQuery/useMutation with:
 * - Automatic retry mechanism
 * - Network error detection
 * - Timeout handling
 * - Fallback UI with recovery options
 *
 * Usage:
 * <QueryErrorBoundary>
 *   <ComponentUsingReactQuery />
 * </QueryErrorBoundary>
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { withTranslation } from 'react-i18next';
import './QueryErrorBoundary.css';

class QueryErrorBoundaryComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });

    // Log error to monitoring service
    // Error tracking service can be integrated here if needed
    if (process.env.NODE_ENV === 'production') {
      console.error('QueryErrorBoundary caught:', error, errorInfo);
    } else {
      console.error('QueryErrorBoundary caught:', error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  getErrorType = () => {
    const error = this.state.error;
    if (!error) return 'unknown';

    const message = error.message?.toLowerCase() || '';

    if (message.includes('network') || message.includes('fetch')) return 'network';
    if (message.includes('timeout')) return 'timeout';
    if (message.includes('429') || message.includes('rate limit')) return 'rate-limit';
    if (message.includes('401') || message.includes('unauthorized')) return 'auth';
    if (message.includes('403') || message.includes('forbidden')) return 'forbidden';
    if (message.includes('404') || message.includes('not found')) return 'not-found';
    if (message.includes('500') || message.includes('server')) return 'server';

    return 'query';
  };

  getErrorMessage = (errorType) => {
    const { t } = this.props;

    const messages = {
      network: t('error.api.network'),
      timeout: t('error.api.timeout'),
      'rate-limit': t('error.api.rateLimit'),
      auth: t('error.api.unauthorized'),
      forbidden: t('error.api.forbidden'),
      'not-found': t('error.api.notFound'),
      server: t('error.api.server'),
      query: t('error.api.query')
    };

    return messages[errorType] || t('error.api.unknown');
  };

  getErrorIcon = (errorType) => {
    const icons = {
      network: '🌐',
      timeout: '⏱️',
      'rate-limit': '⚠️',
      auth: '🔒',
      forbidden: '⛔',
      'not-found': '🔍',
      server: '🔥',
      query: '❌'
    };

    return icons[errorType] || '⚠️';
  };

  render() {
    if (this.state.hasError) {
      const { t, fallback } = this.props;
      const errorType = this.getErrorType();
      const errorMessage = this.getErrorMessage(errorType);
      const errorIcon = this.getErrorIcon(errorType);

      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      return (
        <div className="query-error-boundary" role="alert">
          <div className="query-error-content">
            <div className="query-error-icon" aria-hidden="true">{errorIcon}</div>
            <h3 className="query-error-title">{t('error.api.title')}</h3>
            <p className="query-error-message">{errorMessage}</p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="query-error-details">
                <summary>{t('error.technical.details')}</summary>
                <pre className="query-error-stack">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            <div className="query-error-actions">
              <button
                onClick={this.handleRetry}
                className="query-error-retry"
                aria-label={t('error.api.retry')}
              >
                🔄 {t('error.api.retry')}
              </button>

              {errorType === 'network' && (
                <button
                  onClick={() => window.location.reload()}
                  className="query-error-reload"
                  aria-label={t('error.api.reload')}
                >
                  ↻ {t('error.api.reload')}
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

QueryErrorBoundaryComponent.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node,
  onReset: PropTypes.func,
  t: PropTypes.func.isRequired
};

const TranslatedQueryErrorBoundary = withTranslation()(QueryErrorBoundaryComponent);

/**
 * Wrapper with React Query error reset integration
 */
export const QueryErrorBoundary = ({ children, ...props }) => {
  const { reset } = useQueryErrorResetBoundary();

  return (
    <TranslatedQueryErrorBoundary onReset={reset} {...props}>
      {children}
    </TranslatedQueryErrorBoundary>
  );
};

QueryErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node
};

export default QueryErrorBoundary;

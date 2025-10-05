/**
 * WidgetErrorBoundary - Lightweight Error Boundary for widgets/components
 *
 * Provides graceful degradation for individual widgets without
 * breaking the entire dashboard.
 *
 * Features:
 * - Compact error UI
 * - Widget name display
 * - Retry functionality
 * - Collapse/expand details
 *
 * Usage:
 * <WidgetErrorBoundary widgetName="Network Scanner">
 *   <NetworkScannerWidget />
 * </WidgetErrorBoundary>
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import './WidgetErrorBoundary.css';

class WidgetErrorBoundaryComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });

    // Log to console
    console.error(`Widget "${this.props.widgetName}" error:`, error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null, showDetails: false });
  };

  toggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  render() {
    if (this.state.hasError) {
      const { t } = this.props;
      const widgetName = this.props.widgetName || t('common.widget');

      return (
        <div className="widget-error-boundary" role="alert">
          <div className="widget-error-header">
            <span className="widget-error-icon" aria-hidden="true">⚠️</span>
            <div className="widget-error-title">
              <strong>{widgetName}</strong>
              <span className="widget-error-subtitle">{t('error.boundary.title')}</span>
            </div>
          </div>

          <p className="widget-error-message">
            {this.state.error?.message || t('error.boundary.message')}
          </p>

          <div className="widget-error-actions">
            <button
              onClick={this.handleRetry}
              className="widget-error-retry"
              aria-label={t('error.boundary.retry')}
            >
              🔄 {t('error.boundary.retry')}
            </button>

            {process.env.NODE_ENV === 'development' && (
              <button
                onClick={this.toggleDetails}
                className="widget-error-details-toggle"
                aria-label="Toggle error details"
                aria-expanded={this.state.showDetails}
              >
                {this.state.showDetails ? '▼' : '▶'} {t('error.technical.details')}
              </button>
            )}
          </div>

          {this.state.showDetails && process.env.NODE_ENV === 'development' && (
            <pre className="widget-error-stack">
              {this.state.error?.toString()}
              {this.state.errorInfo?.componentStack}
            </pre>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

WidgetErrorBoundaryComponent.propTypes = {
  children: PropTypes.node.isRequired,
  widgetName: PropTypes.string,
  t: PropTypes.func.isRequired
};

/**
 * Wrapper with i18n support
 */
export const WidgetErrorBoundary = ({ children, widgetName }) => {
  const { t } = useTranslation();

  return (
    <WidgetErrorBoundaryComponent widgetName={widgetName} t={t}>
      {children}
    </WidgetErrorBoundaryComponent>
  );
};

WidgetErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  widgetName: PropTypes.string
};

export default WidgetErrorBoundary;

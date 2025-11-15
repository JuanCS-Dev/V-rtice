/* eslint-disable react-refresh/only-export-components */
/**
 * Error Boundary Component
 * Catches React errors and prevents dashboard crashes
 *
 * Features:
 * - Graceful error handling
 * - User-friendly fallback UI
 * - Telemetry integration ready (Sentry)
 * - Retry mechanism
 * - Error context logging
 * i18n: Fully internationalized with pt-BR and en-US support
 */

import React from "react";
import PropTypes from "prop-types";
import { withTranslation } from "react-i18next";
import logger from "@/utils/logger";
import "./ErrorBoundary.css";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    logger.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState((prevState) => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Log to telemetry service (ready for Sentry integration)
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error, errorInfo) => {
    const errorData = {
      timestamp: new Date().toISOString(),
      message: error?.toString() || "Unknown error",
      stack: error?.stack || "No stack trace",
      componentStack: errorInfo?.componentStack || "No component stack",
      context: this.props.context || "Unknown context",
      errorCount: this.state.errorCount + 1,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // Error tracking via backend logging endpoint
    // (Sentry integration can be added later if needed)

    // Log para console em desenvolvimento
    if (process.env.NODE_ENV === "development") {
      logger.group("🚨 Error Boundary - Telemetry Data");
      logger.error("Error:", errorData);
      logger.groupEnd();
    }

    // Enviar para endpoint de logging (se disponível)
    try {
      fetch("/api/errors/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(errorData),
      }).catch(() => {
        // Fail silently se endpoint não existir
      });
    } catch (e) {
      // Fail silently
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    // Callback para parent component
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI customizado (se fornecido)
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          errorInfo: this.state.errorInfo,
          resetError: this.handleReset,
        });
      }

      // Fallback UI padrão
      const { t } = this.props;

      return (
        <div className="error-boundary-container">
          <div className="error-boundary-content">
            <div className="error-boundary-icon" aria-hidden="true">
              ⚠️
            </div>
            <h2 className="error-boundary-title">
              {this.props.title || t("error.boundary.title")}
            </h2>
            <p className="error-boundary-message">
              {this.props.message || t("error.boundary.message")}
            </p>

            {process.env.NODE_ENV === "development" && this.state.error && (
              <details className="error-boundary-details">
                <summary>Error Details (Dev Only)</summary>
                <pre className="error-boundary-stack">
                  {this.state.error.toString()}
                  {"\n\n"}
                  {this.state.error.stack}
                </pre>
              </details>
            )}

            <div className="error-boundary-actions">
              <button
                onClick={this.handleReset}
                className="error-boundary-btn error-boundary-btn-primary"
                aria-label={t("error.boundary.retry")}
              >
                🔄 {t("error.boundary.retry")}
              </button>

              <button
                onClick={() => (window.location.href = "/")}
                className="error-boundary-btn error-boundary-btn-secondary"
                aria-label={t("error.boundary.backHome")}
              >
                🏠 {t("error.boundary.backHome")}
              </button>
            </div>

            {this.state.errorCount > 2 && (
              <p className="error-boundary-warning" role="alert">
                ⚠️ {t("error.boundary.multipleErrors")}
              </p>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  context: PropTypes.string,
  fallback: PropTypes.func,
  title: PropTypes.string,
  message: PropTypes.string,
  onReset: PropTypes.func,
  t: PropTypes.func.isRequired, // from withTranslation HOC
};

export default withTranslation()(ErrorBoundary);

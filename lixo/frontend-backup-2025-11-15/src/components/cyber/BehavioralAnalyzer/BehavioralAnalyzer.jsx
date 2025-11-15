/**
 * BEHAVIORAL ANALYZER - Behavioral Anomaly Detection Tool
 *
 * Real-time behavioral anomaly detection visualization
 * Displays entity behavior analysis and anomaly alerts
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="behavioral-analyzer"
 * - <header> for tool header
 * - <section> for metrics dashboard
 * - <section> for analysis form
 * - <section> for results display
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="behavioral-analyzer"
 * - Monitor analysis via data-maximus-status
 * - Access metrics via data-maximus-section="metrics"
 * - Interpret results via semantic structure
 *
 * i18n: react-i18next
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  formatDateTime,
  formatDate,
  formatTime,
  getTimestamp,
} from "@/utils/dateHelpers";
import { behavioralAnalyzerService } from "../../../api/defensiveToolsServices";
import styles from "./BehavioralAnalyzer.module.css";

export const BehavioralAnalyzer = () => {
  const { t } = useTranslation();
  const [entityId, setEntityId] = useState("");
  const [eventType, setEventType] = useState("login");
  const [metadata, setMetadata] = useState("{}");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState(null);

  // Load metrics on mount
  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    const response = await behavioralAnalyzerService.getMetrics();
    if (response.success) {
      setMetrics(response.data);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const parsedMetadata = JSON.parse(metadata);
      const response = await behavioralAnalyzerService.analyzeEvent({
        entityId,
        eventType,
        metadata: parsedMetadata,
      });

      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case "CRITICAL":
        return "#ff0000";
      case "HIGH":
        return "#ff6600";
      case "MEDIUM":
        return "#ffaa00";
      case "LOW":
        return "#00ff00";
      default:
        return "#888888";
    }
  };

  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="behavioral-analyzer-title"
      data-maximus-tool="behavioral-analyzer"
      data-maximus-category="defensive"
      data-maximus-status={loading ? "analyzing" : "ready"}
    >
      <header className={styles.header} data-maximus-section="tool-header">
        <h2 id="behavioral-analyzer-title">
          <span aria-hidden="true">🧠</span>{" "}
          {t("defensive.behavioral.title", "Behavioral Analyzer")}
        </h2>
        <p className={styles.subtitle}>
          {t(
            "defensive.behavioral.subtitle",
            "Detect anomalous behavior patterns",
          )}
        </p>
      </header>

      {/* Metrics Dashboard */}
      {metrics && (
        <section
          className={styles.metrics}
          role="region"
          aria-label="Behavioral metrics"
          data-maximus-section="metrics"
        >
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Total Analyzed</span>
            <span className={styles.metricValue}>{metrics.total_analyzed}</span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Anomalies</span>
            <span className={styles.metricValue}>
              {metrics.anomalies_detected}
            </span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>False Positive</span>
            <span className={styles.metricValue}>
              {(metrics.false_positive_rate * 100).toFixed(1)}%
            </span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Avg Time</span>
            <span className={styles.metricValue}>
              {metrics.avg_processing_time_ms.toFixed(0)}ms
            </span>
          </div>
        </section>
      )}

      {/* Analysis Form */}
      <section
        role="region"
        aria-label="Analysis form"
        data-maximus-section="form"
      >
        <form onSubmit={handleAnalyze} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="entityId">Entity ID</label>
            <input
              id="entityId"
              type="text"
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
              placeholder="user@domain.com or 192.168.1.100"
              required
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="eventType">Event Type</label>
            <select
              id="eventType"
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className={styles.select}
            >
              <option value="login">Login</option>
              <option value="file_access">File Access</option>
              <option value="network_connection">Network Connection</option>
              <option value="privilege_escalation">Privilege Escalation</option>
              <option value="data_transfer">Data Transfer</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="metadata">Metadata (JSON)</label>
            {/* Boris Cherny Standard - GAP #76 FIX: Add maxLength validation */}
            <textarea
              id="metadata"
              value={metadata}
              onChange={(e) => setMetadata(e.target.value)}
              placeholder='{"source_ip": "192.168.1.100", "bytes": 1024}'
              rows={3}
              maxLength={5000}
              className={styles.textarea}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !entityId}
            className={styles.submitBtn}
          >
            {loading ? "Analyzing..." : "Analyze Behavior"}
          </button>
        </form>
      </section>

      {/* Error Display */}
      {error && (
        <div className={styles.error} role="alert" aria-live="assertive">
          <span className={styles.errorIcon}>⚠️</span>
          {error}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <section
          className={styles.result}
          role="region"
          aria-label="Analysis results"
          data-maximus-section="results"
        >
          <div
            className={styles.resultHeader}
            style={{ borderLeftColor: getRiskColor(result.risk_level) }}
          >
            <h3>
              {result.is_anomalous
                ? "🚨 Anomaly Detected"
                : "✅ Normal Behavior"}
            </h3>
            <span
              className={styles.riskBadge}
              style={{ backgroundColor: getRiskColor(result.risk_level) }}
            >
              {result.risk_level}
            </span>
          </div>

          <div className={styles.resultContent}>
            <div className={styles.resultRow}>
              <span className={styles.label}>Entity:</span>
              <span className={styles.value}>{result.entity_id}</span>
            </div>
            <div className={styles.resultRow}>
              <span className={styles.label}>Anomaly Score:</span>
              <span className={styles.value}>
                {(result.anomaly_score * 100).toFixed(2)}%
              </span>
            </div>
            <div className={styles.resultRow}>
              <span className={styles.label}>Features Analyzed:</span>
              <span className={styles.value}>{result.features_analyzed}</span>
            </div>
            <div className={styles.resultExplanation}>
              <span className={styles.label}>Explanation:</span>
              <p>{result.explanation}</p>
            </div>
            <div className={styles.resultRow}>
              <span className={styles.label}>Timestamp:</span>
              <span className={styles.value}>
                {formatDateTime(result.timestamp)}
              </span>
            </div>
          </div>
        </section>
      )}
    </article>
  );
};

export default BehavioralAnalyzer;

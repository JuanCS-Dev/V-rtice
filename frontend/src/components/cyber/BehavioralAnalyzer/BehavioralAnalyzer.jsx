/**
 * Behavioral Analyzer Widget
 * 
 * Real-time behavioral anomaly detection visualization
 * Displays entity behavior analysis and anomaly alerts
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { behavioralAnalyzerService } from '../../../api/defensiveToolsServices';
import styles from './BehavioralAnalyzer.module.css';

export const BehavioralAnalyzer = () => {
  const { t } = useTranslation();
  const [entityId, setEntityId] = useState('');
  const [eventType, setEventType] = useState('login');
  const [metadata, setMetadata] = useState('{}');
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
        metadata: parsedMetadata
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
      case 'CRITICAL': return '#ff0000';
      case 'HIGH': return '#ff6600';
      case 'MEDIUM': return '#ffaa00';
      case 'LOW': return '#00ff00';
      default: return '#888888';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>🧠 {t('defensive.behavioral.title', 'Behavioral Analyzer')}</h2>
        <p className={styles.subtitle}>
          {t('defensive.behavioral.subtitle', 'Detect anomalous behavior patterns')}
        </p>
      </div>

      {/* Metrics Dashboard */}
      {metrics && (
        <div className={styles.metrics}>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Total Analyzed</span>
            <span className={styles.metricValue}>{metrics.total_analyzed}</span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Anomalies</span>
            <span className={styles.metricValue}>{metrics.anomalies_detected}</span>
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
        </div>
      )}

      {/* Analysis Form */}
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
          <textarea
            id="metadata"
            value={metadata}
            onChange={(e) => setMetadata(e.target.value)}
            placeholder='{"source_ip": "192.168.1.100", "bytes": 1024}'
            rows={3}
            className={styles.textarea}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !entityId}
          className={styles.submitBtn}
        >
          {loading ? 'Analyzing...' : 'Analyze Behavior'}
        </button>
      </form>

      {/* Error Display */}
      {error && (
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠️</span>
          {error}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className={styles.result}>
          <div
            className={styles.resultHeader}
            style={{ borderLeftColor: getRiskColor(result.risk_level) }}
          >
            <h3>
              {result.is_anomalous ? '🚨 Anomaly Detected' : '✅ Normal Behavior'}
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
                {new Date(result.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BehavioralAnalyzer;

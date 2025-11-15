/**
 * ENCRYPTED TRAFFIC ANALYZER - Encrypted Network Flow Analysis Tool
 *
 * Analyze encrypted network flows for threats
 * Detects C2 communication, data exfiltration, tunneling
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="encrypted-traffic-analyzer"
 * - <header> for tool header
 * - <section> for metrics dashboard
 * - <section> for analysis form
 * - <section> for results display
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="encrypted-traffic-analyzer"
 * - Monitor analysis via data-maximus-status
 * - Access metrics via data-maximus-section="metrics"
 * - Interpret threat scores via semantic structure
 *
 * i18n: react-i18next
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { formatDateTime, formatDate, formatTime, getTimestamp } from '@/utils/dateHelpers';
import { encryptedTrafficService } from '../../../api/defensiveToolsServices';
import styles from './EncryptedTrafficAnalyzer.module.css';

export const EncryptedTrafficAnalyzer = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    sourceIp: '',
    destIp: '',
    sourcePort: 0,
    destPort: 443,
    protocol: 'tcp',
    tlsVersion: 'TLS 1.3',
    cipherSuite: 'TLS_AES_256_GCM_SHA384',
    sni: '',
    flowDuration: 0
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    const response = await encryptedTrafficService.getMetrics();
    if (response.success) {
      setMetrics(response.data);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await encryptedTrafficService.analyzeFlow({
        ...formData,
        sourcePort: parseInt(formData.sourcePort),
        destPort: parseInt(formData.destPort),
        flowDuration: parseFloat(formData.flowDuration)
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

  const getThreatColor = (score) => {
    if (score >= 0.8) return '#ff0000';
    if (score >= 0.6) return '#ff6600';
    if (score >= 0.4) return '#ffaa00';
    return '#00ff00';
  };

  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="encrypted-traffic-title"
      data-maximus-tool="encrypted-traffic-analyzer"
      data-maximus-category="defensive"
      data-maximus-status={loading ? 'analyzing' : 'ready'}>

      <header
        className={styles.header}
        data-maximus-section="tool-header">
        <h2 id="encrypted-traffic-title"><span aria-hidden="true">🔐</span> {t('defensive.traffic.title', 'Encrypted Traffic Analyzer')}</h2>
        <p className={styles.subtitle}>
          {t('defensive.traffic.subtitle', 'Detect threats in encrypted communications')}
        </p>
      </header>

      {/* Metrics */}
      {metrics && (
        <section
          className={styles.metrics}
          role="region"
          aria-label="Traffic metrics"
          data-maximus-section="metrics">
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Total Analyzed</span>
            <span className={styles.metricValue}>{metrics.total_analyzed}</span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Threats Detected</span>
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
        </section>
      )}

      {/* Analysis Form */}
      <section
        role="region"
        aria-label="Traffic analysis form"
        data-maximus-section="form">
        <form onSubmit={handleAnalyze} className={styles.form}>
        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label htmlFor="sourceIp">Source IP</label>
            <input
              id="sourceIp"
              name="sourceIp"
              type="text"
              value={formData.sourceIp}
              onChange={handleChange}
              placeholder="192.168.1.100"
              required
              className={styles.input}
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="sourcePort">Source Port</label>
            <input
              id="sourcePort"
              name="sourcePort"
              type="number"
              value={formData.sourcePort}
              onChange={handleChange}
              min="0"
              max="65535"
              required
              className={styles.input}
            />
          </div>
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label htmlFor="destIp">Destination IP</label>
            <input
              id="destIp"
              name="destIp"
              type="text"
              value={formData.destIp}
              onChange={handleChange}
              placeholder="203.0.113.42"
              required
              className={styles.input}
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="destPort">Dest Port</label>
            <input
              id="destPort"
              name="destPort"
              type="number"
              value={formData.destPort}
              onChange={handleChange}
              min="0"
              max="65535"
              required
              className={styles.input}
            />
          </div>
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label htmlFor="protocol">Protocol</label>
            <select
              id="protocol"
              name="protocol"
              value={formData.protocol}
              onChange={handleChange}
              className={styles.select}
            >
              <option value="tcp">TCP</option>
              <option value="udp">UDP</option>
            </select>
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="flowDuration">Duration (seconds)</label>
            <input
              id="flowDuration"
              name="flowDuration"
              type="number"
              value={formData.flowDuration}
              onChange={handleChange}
              step="0.1"
              min="0"
              required
              className={styles.input}
            />
          </div>
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label htmlFor="tlsVersion">TLS Version</label>
            <select
              id="tlsVersion"
              name="tlsVersion"
              value={formData.tlsVersion}
              onChange={handleChange}
              className={styles.select}
            >
              <option value="TLS 1.3">TLS 1.3</option>
              <option value="TLS 1.2">TLS 1.2</option>
              <option value="TLS 1.1">TLS 1.1</option>
              <option value="TLS 1.0">TLS 1.0</option>
            </select>
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="sni">SNI (Optional)</label>
            <input
              id="sni"
              name="sni"
              type="text"
              value={formData.sni}
              onChange={handleChange}
              placeholder="example.com"
              className={styles.input}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !formData.sourceIp || !formData.destIp}
          className={styles.submitBtn}
        >
          {loading ? 'Analyzing...' : 'Analyze Traffic'}
        </button>
      </form>
      </section>

      {/* Error */}
      {error && (
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠️</span>
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <section
          className={styles.result}
          role="region"
          aria-label="Traffic analysis results"
          data-maximus-section="results">
          <div
            className={styles.resultHeader}
            style={{ borderLeftColor: getThreatColor(result.threat_score) }}
          >
            <h3>
              {result.is_threat ? '🚨 Threat Detected' : '✅ Traffic Normal'}
            </h3>
            <div className={styles.threatScore}>
              <span className={styles.scoreLabel}>Threat Score</span>
              <span
                className={styles.scoreValue}
                style={{ color: getThreatColor(result.threat_score) }}
              >
                {(result.threat_score * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className={styles.resultContent}>
            <div className={styles.resultRow}>
              <span className={styles.label}>Confidence:</span>
              <span className={styles.value}>{result.confidence_level}</span>
            </div>
            
            {result.threat_types && result.threat_types.length > 0 && (
              <div className={styles.threatTypes}>
                <span className={styles.label}>Threat Types:</span>
                <div className={styles.threatTags}>
                  {result.threat_types.map((type, idx) => (
                    <span key={idx} className={styles.threatTag}>
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className={styles.resultExplanation}>
              <span className={styles.label}>Analysis:</span>
              <p>{result.explanation}</p>
            </div>

            <div className={styles.flowInfo}>
              <div className={styles.flowDetail}>
                <span className={styles.label}>Source:</span>
                <span className={styles.value}>{result.source_ip}</span>
              </div>
              <div className={styles.flowDetail}>
                <span className={styles.label}>Destination:</span>
                <span className={styles.value}>{result.dest_ip}</span>
              </div>
              <div className={styles.flowDetail}>
                <span className={styles.label}>Timestamp:</span>
                <span className={styles.value}>
                  {formatDateTime(result.timestamp)}
                </span>
              </div>
            </div>
          </div>
        </section>
      )}
    </article>
  );
};

export default EncryptedTrafficAnalyzer;

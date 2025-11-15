/**
 * NETWORK SCANNER - Network Reconnaissance Tool
 *
 * Advanced network reconnaissance
 * Port scanning, service detection, vulnerability assessment
 * Philosophy: Ethical boundaries enforced
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="network-scanner"
 * - <header> for tool header with risk indicators
 * - <section> for form (scan configuration)
 * - <section> for results display
 * - <footer> for status bar
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="network-scanner"
 * - Monitor scan status via data-maximus-status
 * - Access scan configuration via semantic form structure
 * - Interpret results via semantic sections
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
import {
  networkScannerService,
  toolRegistryService,
} from "../../../api/offensiveToolsServices";
import styles from "./NetworkScanner.module.css";

export const NetworkScanner = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    target: "",
    ports: "",
    timeout: 5.0,
    operationMode: "defensive",
    justification: "",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toolInfo, setToolInfo] = useState(null);

  useEffect(() => {
    loadToolInfo();
  }, []);

  const loadToolInfo = async () => {
    const response = await toolRegistryService.getTool("network_scanner");
    if (response.success) {
      setToolInfo(response.data);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleScan = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const scanData = {
        target: formData.target,
        ports: formData.ports
          ? formData.ports.split(",").map((p) => parseInt(p.trim()))
          : null,
        timeout: parseFloat(formData.timeout),
        operationMode: formData.operationMode,
        justification: formData.justification,
      };

      const response = await networkScannerService.scan(scanData);

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

  const getModeClass = (mode) => {
    switch (mode) {
      case "defensive":
        return styles.defensive;
      case "research":
        return styles.research;
      case "red_team":
        return styles.redTeam;
      default:
        return "";
    }
  };

  const getRiskClass = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case "low":
        return styles.low;
      case "medium":
        return styles.medium;
      case "high":
        return styles.high;
      default:
        return "";
    }
  };

  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="network-scanner-title"
      data-maximus-tool="network-scanner"
      data-maximus-category="offensive"
      data-maximus-status={loading ? "scanning" : "ready"}
    >
      <header className={styles.header} data-maximus-section="tool-header">
        <h2 id="network-scanner-title">
          <span aria-hidden="true">🔍</span>{" "}
          {t("offensive.scanner.title", "Network Scanner")}
        </h2>
        <p className={styles.subtitle}>
          {t(
            "offensive.scanner.subtitle",
            "Advanced port scanning and service detection",
          )}
        </p>
      </header>

      {/* Tool Info */}
      {toolInfo && (
        <section
          className={styles.toolInfo}
          role="region"
          aria-label="Tool information"
          data-maximus-section="tool-info"
        >
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Category:</span>
            <span className={styles.infoBadge}>{toolInfo.category}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Risk Level:</span>
            <span
              className={`${styles.riskBadge} ${getRiskClass(toolInfo.risk_level)}`}
            >
              {toolInfo.risk_level}
            </span>
          </div>
        </section>
      )}

      {/* Scan Form */}
      <section
        role="region"
        aria-label="Scan configuration"
        data-maximus-section="form"
      >
        <form onSubmit={handleScan} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="target">Target (IP or Hostname)</label>
            <input
              id="target"
              name="target"
              type="text"
              value={formData.target}
              onChange={handleChange}
              placeholder="192.168.1.100 or example.com"
              required
              className={styles.input}
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="ports">Ports (comma-separated, optional)</label>
              <input
                id="ports"
                name="ports"
                type="text"
                value={formData.ports}
                onChange={handleChange}
                placeholder="22,80,443,8080"
                className={styles.input}
              />
              <span className={styles.hint}>
                Leave empty for common ports scan
              </span>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="timeout">Timeout (seconds)</label>
              <input
                id="timeout"
                name="timeout"
                type="number"
                value={formData.timeout}
                onChange={handleChange}
                min="0.1"
                max="60"
                step="0.1"
                className={styles.input}
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="operationMode">Operation Mode</label>
            <select
              id="operationMode"
              name="operationMode"
              value={formData.operationMode}
              onChange={handleChange}
              className={`${styles.select} ${getModeClass(formData.operationMode)}`}
            >
              <option value="defensive">Defensive (Blue Team)</option>
              <option value="research">Research (Security Testing)</option>
              <option value="red_team">Red Team (Authorized Only)</option>
            </select>
          </div>

          {formData.operationMode !== "defensive" && (
            <div className={styles.formGroup}>
              <label htmlFor="justification">Justification (Required)</label>
              <textarea
                id="justification"
                name="justification"
                value={formData.justification}
                onChange={handleChange}
                placeholder="Describe authorization and purpose..."
                rows={3}
                required
                className={styles.textarea}
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !formData.target}
            className={styles.submitBtn}
          >
            {loading ? "Scanning..." : "Launch Scan"}
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

      {/* Results */}
      {result && (
        <section
          className={styles.result}
          role="region"
          aria-label="Scan results"
          data-maximus-section="results"
        >
          <div className={styles.resultHeader}>
            <h3>{result.success ? "✅ Scan Complete" : "❌ Scan Failed"}</h3>
            <div className={styles.timing}>
              <span className={styles.timingLabel}>Execution Time:</span>
              <span className={styles.timingValue}>
                {result.execution_time_ms.toFixed(2)}ms
              </span>
            </div>
          </div>

          <div className={styles.resultContent}>
            <div className={styles.resultRow}>
              <span className={styles.label}>Tool:</span>
              <span className={styles.value}>{result.tool_name}</span>
            </div>
            <div className={styles.resultRow}>
              <span className={styles.label}>Mode:</span>
              <span
                className={`${styles.value} ${getModeClass(result.operation_mode)}`}
              >
                {result.operation_mode}
              </span>
            </div>

            {result.data && (
              <>
                {result.data.open_ports &&
                  result.data.open_ports.length > 0 && (
                    <div className={styles.portsSection}>
                      <h4>Open Ports ({result.data.open_ports.length})</h4>
                      <div className={styles.portsList}>
                        {result.data.open_ports.map((port, idx) => (
                          <div key={idx} className={styles.portCard}>
                            <span className={styles.portNumber}>{port}</span>
                            <span className={styles.portStatus}>OPEN</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {result.data.services && (
                  <div className={styles.servicesSection}>
                    <h4>Detected Services</h4>
                    <div className={styles.servicesList}>
                      {Object.entries(result.data.services).map(
                        ([port, service]) => (
                          <div key={port} className={styles.serviceCard}>
                            <span className={styles.servicePort}>
                              Port {port}:
                            </span>
                            <span className={styles.serviceName}>
                              {service}
                            </span>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}
              </>
            )}

            <div className={styles.timestamp}>
              Scanned at: {formatDateTime(result.timestamp)}
            </div>
          </div>
        </section>
      )}
    </article>
  );
};

export default NetworkScanner;

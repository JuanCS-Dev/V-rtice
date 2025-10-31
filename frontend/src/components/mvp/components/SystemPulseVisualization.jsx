/**
 * SystemPulseVisualization - Visualização do Pulso do Sistema
 * ===========================================================
 *
 * Métricas animadas em tempo real do sistema.
 * Design inspirado em monitores médicos/vitais.
 */

import React from "react";
import styles from "./SystemPulseVisualization.module.css";

export const SystemPulseVisualization = ({ pulse, metrics, isLoading }) => {
  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Carregando system pulse...</p>
      </div>
    );
  }

  const getHealthColor = (value) => {
    if (value >= 0.9) return "green";
    if (value >= 0.7) return "yellow";
    if (value >= 0.5) return "orange";
    return "red";
  };

  const systemHealth = pulse?.health || 0.85;
  const healthColor = getHealthColor(systemHealth);

  return (
    <div className={styles.pulse}>
      {/* Main Pulse Display */}
      <div className={styles.mainPulse}>
        <div className={styles.pulseRing}>
          <div className={`${styles.pulseCircle} ${styles[healthColor]}`}>
            <div className={styles.pulseValue}>
              <span className={styles.pulseNumber}>
                {(systemHealth * 100).toFixed(0)}
              </span>
              <span className={styles.pulseUnit}>%</span>
            </div>
            <div className={styles.pulseLabel}>System Health</div>
          </div>
        </div>

        {/* Heartbeat Animation */}
        <div className={styles.heartbeat}>
          <div
            className={`${styles.heartbeatLine} ${styles[healthColor]}`}
          ></div>
        </div>
      </div>

      {/* Vital Signs Grid */}
      <div className={styles.vitals}>
        <h3 className={styles.vitalsTitle}>💓 Sinais Vitais</h3>

        <div className={styles.vitalsGrid}>
          {/* CPU */}
          <div className={styles.vital}>
            <div className={styles.vitalHeader}>
              <span className={styles.vitalIcon}>🖥️</span>
              <span className={styles.vitalName}>CPU Usage</span>
            </div>
            <div className={styles.vitalValue}>
              {metrics?.cpu_usage
                ? `${(metrics.cpu_usage * 100).toFixed(1)}%`
                : "N/A"}
            </div>
            <div className={styles.vitalBar}>
              <div
                className={`${styles.vitalFill} ${styles[getHealthColor(1 - (metrics?.cpu_usage || 0))]}`}
                style={{ width: `${(metrics?.cpu_usage || 0) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Memory */}
          <div className={styles.vital}>
            <div className={styles.vitalHeader}>
              <span className={styles.vitalIcon}>💾</span>
              <span className={styles.vitalName}>Memory Usage</span>
            </div>
            <div className={styles.vitalValue}>
              {metrics?.memory_usage
                ? `${(metrics.memory_usage * 100).toFixed(1)}%`
                : "N/A"}
            </div>
            <div className={styles.vitalBar}>
              <div
                className={`${styles.vitalFill} ${styles[getHealthColor(1 - (metrics?.memory_usage || 0))]}`}
                style={{ width: `${(metrics?.memory_usage || 0) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Response Time */}
          <div className={styles.vital}>
            <div className={styles.vitalHeader}>
              <span className={styles.vitalIcon}>⚡</span>
              <span className={styles.vitalName}>Response Time</span>
            </div>
            <div className={styles.vitalValue}>
              {metrics?.avg_response_time
                ? `${metrics.avg_response_time}ms`
                : "N/A"}
            </div>
            <div className={styles.vitalBar}>
              <div
                className={`${styles.vitalFill} ${styles.blue}`}
                style={{
                  width: `${Math.min((metrics?.avg_response_time || 0) / 10, 100)}%`,
                }}
              ></div>
            </div>
          </div>

          {/* Throughput */}
          <div className={styles.vital}>
            <div className={styles.vitalHeader}>
              <span className={styles.vitalIcon}>📊</span>
              <span className={styles.vitalName}>Throughput</span>
            </div>
            <div className={styles.vitalValue}>
              {metrics?.throughput ? `${metrics.throughput} req/s` : "N/A"}
            </div>
            <div className={styles.vitalBar}>
              <div
                className={`${styles.vitalFill} ${styles.green}`}
                style={{
                  width: `${Math.min((metrics?.throughput || 0) * 10, 100)}%`,
                }}
              ></div>
            </div>
          </div>

          {/* Error Rate */}
          <div className={styles.vital}>
            <div className={styles.vitalHeader}>
              <span className={styles.vitalIcon}>⚠️</span>
              <span className={styles.vitalName}>Error Rate</span>
            </div>
            <div className={styles.vitalValue}>
              {metrics?.error_rate
                ? `${(metrics.error_rate * 100).toFixed(2)}%`
                : "N/A"}
            </div>
            <div className={styles.vitalBar}>
              <div
                className={`${styles.vitalFill} ${styles[getHealthColor(1 - (metrics?.error_rate || 0))]}`}
                style={{ width: `${(metrics?.error_rate || 0) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Uptime */}
          <div className={styles.vital}>
            <div className={styles.vitalHeader}>
              <span className={styles.vitalIcon}>⏰</span>
              <span className={styles.vitalName}>Uptime</span>
            </div>
            <div className={styles.vitalValue}>
              {metrics?.uptime_hours ? `${metrics.uptime_hours}h` : "N/A"}
            </div>
            <div className={styles.vitalBar}>
              <div
                className={`${styles.vitalFill} ${styles.green}`}
                style={{ width: "100%" }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {pulse?.status_messages && pulse.status_messages.length > 0 && (
        <div className={styles.statusMessages}>
          <h3 className={styles.messagesTitle}>📢 Status do Sistema</h3>
          <div className={styles.messages}>
            {pulse.status_messages.map((msg, index) => (
              <div key={index} className={styles.message}>
                <span className={styles.messageTime}>
                  {new Date(msg.timestamp).toLocaleTimeString("pt-BR")}
                </span>
                <span className={styles.messageText}>{msg.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemPulseVisualization;

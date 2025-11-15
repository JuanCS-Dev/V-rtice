/**
 * AnomalyHeatmap - Mapa de Calor de Anomalias
 * ============================================
 *
 * Calendar heatmap view mostrando anomalias ao longo do tempo.
 * Similar ao GitHub contribution graph.
 */

import React, { useMemo } from "react";
import styles from "./AnomalyHeatmap.module.css";
import { formatDateTime } from "../../../utils/dateHelpers";

export const AnomalyHeatmap = ({ anomalies, timeline, isLoading }) => {
  // Generate calendar data (last 12 weeks)
  const calendarData = useMemo(() => {
    const weeks = [];
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - 83); // 12 weeks

    for (let week = 0; week < 12; week++) {
      const days = [];
      for (let day = 0; day < 7; day++) {
        const date = new Date(startDate);
        date.setDate(startDate.getDate() + week * 7 + day);

        const dateStr = date.toISOString().split("T")[0];
        const dayAnomalies = timeline?.filter((a) => a.date === dateStr) || [];
        const count = dayAnomalies.length;

        days.push({
          date: dateStr,
          count,
          intensity: Math.min(count / 5, 1), // 0-1 scale
          anomalies: dayAnomalies,
        });
      }
      weeks.push(days);
    }

    return weeks;
  }, [timeline]);

  // Get severity stats
  const severityStats = useMemo(() => {
    if (!anomalies) return { critical: 0, high: 0, medium: 0, low: 0 };

    return anomalies.reduce(
      (acc, anomaly) => {
        acc[anomaly.severity] = (acc[anomaly.severity] || 0) + 1;
        return acc;
      },
      { critical: 0, high: 0, medium: 0, low: 0 },
    );
  }, [anomalies]);

  const getIntensityClass = (intensity) => {
    if (intensity === 0) return styles.level0;
    if (intensity < 0.25) return styles.level1;
    if (intensity < 0.5) return styles.level2;
    if (intensity < 0.75) return styles.level3;
    return styles.level4;
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "critical":
        return "red";
      case "high":
        return "orange";
      case "medium":
        return "yellow";
      case "low":
        return "blue";
      default:
        return "gray";
    }
  };

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Carregando anomalias...</p>
      </div>
    );
  }

  return (
    <div className={styles.heatmap}>
      {/* Severity Stats */}
      <div className={styles.statsBar}>
        <div className={styles.stat}>
          <span className={styles.statIcon}>🔴</span>
          <span className={styles.statLabel}>Critical:</span>
          <span className={styles.statValue}>{severityStats.critical}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statIcon}>🟠</span>
          <span className={styles.statLabel}>High:</span>
          <span className={styles.statValue}>{severityStats.high}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statIcon}>🟡</span>
          <span className={styles.statLabel}>Medium:</span>
          <span className={styles.statValue}>{severityStats.medium}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statIcon}>🔵</span>
          <span className={styles.statLabel}>Low:</span>
          <span className={styles.statValue}>{severityStats.low}</span>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className={styles.calendar}>
        <div className={styles.calendarHeader}>
          <h3 className={styles.calendarTitle}>📅 Últimas 12 Semanas</h3>
          <div className={styles.legend}>
            <span className={styles.legendLabel}>Menos</span>
            <div className={`${styles.legendBox} ${styles.level0}`}></div>
            <div className={`${styles.legendBox} ${styles.level1}`}></div>
            <div className={`${styles.legendBox} ${styles.level2}`}></div>
            <div className={`${styles.legendBox} ${styles.level3}`}></div>
            <div className={`${styles.legendBox} ${styles.level4}`}></div>
            <span className={styles.legendLabel}>Mais</span>
          </div>
        </div>

        <div className={styles.grid}>
          {/* Day labels */}
          <div className={styles.dayLabels}>
            <span>Dom</span>
            <span>Seg</span>
            <span>Ter</span>
            <span>Qua</span>
            <span>Qui</span>
            <span>Sex</span>
            <span>Sáb</span>
          </div>

          {/* Weeks */}
          <div className={styles.weeks}>
            {calendarData.map((week, weekIndex) => (
              <div key={weekIndex} className={styles.week}>
                {week.map((day, dayIndex) => (
                  <div
                    key={dayIndex}
                    className={`${styles.day} ${getIntensityClass(day.intensity)}`}
                    title={`${day.date}: ${day.count} anomalia(s)`}
                  >
                    <span className={styles.dayCount}>
                      {day.count > 0 ? day.count : ""}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Anomalies List */}
      <div className={styles.recentList}>
        <h3 className={styles.listTitle}>🚨 Anomalias Recentes</h3>
        {!anomalies || anomalies.length === 0 ? (
          <div className={styles.empty}>
            <p>✅ Nenhuma anomalia detectada</p>
          </div>
        ) : (
          <div className={styles.anomalies}>
            {anomalies.slice(0, 10).map((anomaly, index) => (
              <div
                key={index}
                className={`${styles.anomaly} ${styles[getSeverityColor(anomaly.severity)]}`}
              >
                <div className={styles.anomalyHeader}>
                  <span className={styles.severity}>
                    {anomaly.severity.toUpperCase()}
                  </span>
                  <span className={styles.timestamp}>
                    {formatDateTime(anomaly.detected_at, "Data indisponível")}
                  </span>
                </div>
                <div className={styles.anomalyContent}>
                  <p className={styles.description}>{anomaly.description}</p>
                  {anomaly.metric_name && (
                    <div className={styles.metric}>
                      <span className={styles.metricLabel}>Métrica:</span>
                      <code className={styles.metricValue}>
                        {anomaly.metric_name}
                      </code>
                    </div>
                  )}
                  {anomaly.threshold && (
                    <div className={styles.metric}>
                      <span className={styles.metricLabel}>Threshold:</span>
                      <span className={styles.metricValue}>
                        {anomaly.threshold}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnomalyHeatmap;

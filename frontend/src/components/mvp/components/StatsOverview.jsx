/**
 * StatsOverview - Visão Geral de Estatísticas MVP
 * ================================================
 *
 * Mostra métricas principais de narrativas por tone.
 */

import React from "react";
import styles from "./StatsOverview.module.css";

export const StatsOverview = ({ stats }) => {
  if (!stats) return null;

  const metrics = [
    {
      label: "Total Narrativas",
      value: stats.total || 0,
      icon: "📚",
      color: "purple",
    },
    {
      label: "Analytical",
      value: stats.analytical || 0,
      icon: "🔬",
      color: "blue",
    },
    {
      label: "Poetic",
      value: stats.poetic || 0,
      icon: "🎭",
      color: "pink",
    },
    {
      label: "Technical",
      value: stats.technical || 0,
      icon: "⚙️",
      color: "gray",
    },
    {
      label: "NQS Médio",
      value: stats.avg_nqs ? `${(stats.avg_nqs * 100).toFixed(0)}%` : "N/A",
      icon: "⭐",
      color: "gold",
    },
    {
      label: "Última 24h",
      value: stats.last_24h || 0,
      icon: "🕐",
      color: "green",
    },
  ];

  return (
    <div className={styles.overview}>
      {metrics.map((metric, index) => (
        <div key={index} className={`${styles.metric} ${styles[metric.color]}`}>
          <span className={styles.icon}>{metric.icon}</span>
          <div className={styles.content}>
            <div className={styles.value}>{metric.value}</div>
            <div className={styles.label}>{metric.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatsOverview;

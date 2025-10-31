/**
 * StatsOverview - Visão Geral de Estatísticas MABA
 * =================================================
 *
 * Mostra métricas principais do agente MABA em cards compactos.
 */

import React from "react";
import styles from "./StatsOverview.module.css";

export const StatsOverview = ({ stats }) => {
  if (!stats) return null;

  const metrics = [
    {
      label: "Total Sessions",
      value: stats.total_sessions || 0,
      icon: "🌐",
      color: "blue",
    },
    {
      label: "Active Sessions",
      value: stats.active_sessions || 0,
      icon: "🟢",
      color: "green",
    },
    {
      label: "Páginas Mapeadas",
      value: stats.pages_mapped || 0,
      icon: "📄",
      color: "cyan",
    },
    {
      label: "Elementos Aprendidos",
      value: stats.elements_learned || 0,
      icon: "🧩",
      color: "purple",
    },
    {
      label: "Screenshots",
      value: stats.total_screenshots || 0,
      icon: "📸",
      color: "yellow",
    },
    {
      label: "Navegações",
      value: stats.total_navigations || 0,
      icon: "🧭",
      color: "orange",
    },
  ];

  return (
    <div className={styles.overview}>
      {metrics.map((metric, index) => (
        <div key={index} className={`${styles.metric} ${styles[metric.color]}`}>
          <span className={styles.icon}>{metric.icon}</span>
          <div className={styles.content}>
            <div className={styles.value}>{metric.value.toLocaleString()}</div>
            <div className={styles.label}>{metric.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatsOverview;

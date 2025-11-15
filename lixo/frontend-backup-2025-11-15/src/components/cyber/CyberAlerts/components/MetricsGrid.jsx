import React from "react";
import styles from "./MetricsGrid.module.css";

export const MetricsGrid = ({ threatData }) => {
  const metrics = [
    { label: "AMEAÇAS", value: threatData.totalThreats, variant: "critical" },
    { label: "DOMÍNIOS", value: threatData.activeDomains, variant: "warning" },
    { label: "IPS", value: threatData.suspiciousIPs, variant: "high" },
    { label: "ALERTAS", value: threatData.networkAlerts, variant: "cyber" },
  ];

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>MÉTRICAS EM TEMPO REAL</h3>
      <div className={styles.grid}>
        {metrics.map((metric, index) => (
          <div
            key={index}
            className={`${styles.metric} ${styles[metric.variant]}`}
          >
            <div className={styles.value}>{metric.value}</div>
            <div className={styles.label}>{metric.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MetricsGrid;

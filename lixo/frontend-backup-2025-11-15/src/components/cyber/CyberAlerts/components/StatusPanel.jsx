import React from "react";
import styles from "./StatusPanel.module.css";

const STATUS_ITEMS = [
  { label: "THREAT INTEL", value: "active", showIndicator: true },
  { label: "APIs ATIVAS", value: "7/7" },
  { label: "FEEDS ATIVOS", value: "12" },
  { label: "LATÊNCIA", value: "89ms" },
];

export const StatusPanel = () => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>STATUS CYBER OPS</h3>
      <div className={styles.items}>
        {STATUS_ITEMS.map((item, index) => (
          <div key={index} className={styles.item}>
            <span className={styles.label}>{item.label}</span>
            {item.showIndicator ? (
              <div className={styles.indicator} />
            ) : (
              <span className={styles.value}>{item.value}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatusPanel;

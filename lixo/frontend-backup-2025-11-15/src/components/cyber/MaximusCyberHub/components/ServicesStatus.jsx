import React from "react";
import styles from "./ServicesStatus.module.css";

export const ServicesStatus = ({ services }) => {
  return (
    <div className={styles.container}>
      <div className={styles.label}>Available Services</div>
      <div className={styles.list}>
        {Object.entries(services).map(([id, service]) => (
          <div key={id} className={styles.service}>
            <span className={styles.serviceInfo}>
              <span className={styles.icon}>{service.icon}</span>
              {service.name}
            </span>
            <div className={`${styles.indicator} ${styles[service.status]}`} />
          </div>
        ))}
      </div>
    </div>
  );
};

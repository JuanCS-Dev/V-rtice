import React from "react";
import styles from "./IpAnalysisResults.module.css";

/**
 * A memoized component to display a single identified service.
 */
const IdentifiedService = ({ service }) => {
  return (
    <div className={styles.serviceCard}>
      <div className={styles.serviceHeader}>
        <span className={styles.servicePort}>Porto {service.port}</span>
        <span className={styles.serviceName}>{service.service}</span>
      </div>
      <div className={styles.serviceVersion}>{service.version}</div>
    </div>
  );
};

export default React.memo(IdentifiedService);

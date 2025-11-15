import React from "react";
import { Button } from "../../../shared";
import styles from "./NetworkMonitorHeader.module.css";

/**
 * Displays the header section of the Network Monitor, including title, description,
 * and a button to start/stop monitoring.
 */
const NetworkMonitorHeader = ({ isMonitoring, onToggleMonitoring }) => {
  return (
    <div className={styles.headerContainer}>
      <div className={styles.headerLeft}>
        <h2 className={styles.title}>NETWORK MONITORING CENTER</h2>
        <p className={styles.description}>
          Monitoramento de tráfego de rede em tempo real
        </p>
      </div>

      <Button
        onClick={onToggleMonitoring}
        variant={isMonitoring ? "danger" : "success"}
        size="lg"
      >
        {isMonitoring ? "PARAR MONITORAMENTO" : "INICIAR MONITORAMENTO"}
      </Button>
    </div>
  );
};

export default React.memo(NetworkMonitorHeader);

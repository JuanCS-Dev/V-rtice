import React from "react";
import NetworkEvent from "./NetworkEvent";
import styles from "./NetworkEventStream.module.css";

/**
 * Displays a real-time stream of network events.
 */
const NetworkEventStream = ({
  isMonitoring,
  networkEvents,
  getSeverityClass,
}) => {
  return (
    <div className={styles.eventStreamContainer}>
      <div className={styles.streamHeader}>
        <h3 className={styles.streamTitle}>STREAM DE EVENTOS DE REDE</h3>
        <div className={styles.statusIndicator}>
          <div
            className={`${styles.statusDot} ${isMonitoring ? styles.active : styles.inactive}`}
          ></div>
          <span className={styles.statusText}>
            {isMonitoring ? "MONITORAMENTO ATIVO" : "MONITORAMENTO INATIVO"}
          </span>
        </div>
      </div>

      <ul className={styles.eventList}>
        {networkEvents.length === 0 ? (
          <div className={styles.noEvents}>
            <div className={styles.noEventsIcon}>📡</div>
            <h3 className={styles.noEventsTitle}>
              {isMonitoring ? "AGUARDANDO EVENTOS..." : "NETWORK MONITOR READY"}
            </h3>
            <p className={styles.noEventsDescription}>
              {isMonitoring
                ? "Escutando tráfego de rede..."
                : 'Clique em "INICIAR MONITORAMENTO" para começar'}
            </p>
          </div>
        ) : (
          networkEvents.map((event) => (
            <NetworkEvent
              key={event.id}
              event={event}
              getSeverityClass={getSeverityClass}
            />
          ))
        )}
      </ul>
    </div>
  );
};

export default React.memo(NetworkEventStream);

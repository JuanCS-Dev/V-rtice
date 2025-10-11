import React from 'react';
import styles from './NetworkEventStream.module.css';

/**
 * A memoized component to display a single network event.
 * Prevents re-rendering if the event prop does not change.
 */
const NetworkEvent = ({ event, getSeverityClass }) => {
  return (
    <li className={`${styles.eventCard} ${styles[getSeverityClass(event.severity)]}`}>
      <div className={styles.eventHeader}>
        <div className={styles.eventTypeTimestamp}>
          <span className={styles.eventType}>{event.type}</span>
          <span className={styles.eventTimestamp}>{event.timestamp}</span>
        </div>
        <span className={`${styles.eventSeverity} ${styles[getSeverityClass(event.severity)]}`}>
          {event.severity}
        </span>
      </div>
      <p className={styles.eventAction}>{event.action}</p>
      <div className={styles.eventDetails}>
        <div>IP Origem: {event.source_ip}</div>
        <div>Porta Destino: {event.destination_port}</div>
        <div>{event.details}</div>
      </div>
    </li>
  );
};

export default React.memo(NetworkEvent);

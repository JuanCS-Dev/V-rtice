import React from 'react';
import { Badge } from '../../../shared';
import styles from './EventsList.module.css';

const getSeverityVariant = (severity) => {
  const variants = {
    'critical': 'critical',
    'high': 'high',
    'medium': 'medium',
    'info': 'cyber'
  };
  return variants[severity] || 'default';
};

export const EventsList = ({ events }) => {
  if (events.length === 0) {
    return (
      <div className={styles.emptyState}>
        <i className="fas fa-satellite-dish"></i>
        <p>Aguardando eventos de rede...</p>
        <span className={styles.hint}>Inicie o monitoramento para ver eventos em tempo real</span>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h5 className={styles.title}>
          <i className="fas fa-stream"></i>
          Eventos em Tempo Real ({events.length})
        </h5>
      </div>

      <div className={styles.eventsList}>
        {events.map((event) => (
          <div key={event.id} className={styles.eventCard}>
            <div className={styles.eventHeader}>
              <Badge variant={getSeverityVariant(event.severity)} size="sm">
                {event.type}
              </Badge>
              <span className={styles.timestamp}>{event.timestamp}</span>
            </div>

            <div className={styles.eventBody}>
              <p className={styles.action}>{event.action}</p>
              <div className={styles.eventDetails}>
                <span className={styles.detail}>
                  <i className="fas fa-network-wired"></i>
                  {event.source_ip}
                </span>
                <span className={styles.detail}>
                  <i className="fas fa-ethernet"></i>
                  Port: {event.destination_port}
                </span>
              </div>
              {event.details && (
                <p className={styles.additionalDetails}>{event.details}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EventsList;

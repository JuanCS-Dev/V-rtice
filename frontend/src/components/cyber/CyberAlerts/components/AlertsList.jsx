import React from 'react';
import { Badge } from '../../../shared';
import { getSeverityVariant, getSeverityIcon } from '../utils/alertUtils';
import styles from './AlertsList.module.css';

export const AlertsList = ({ alerts }) => {
  if (alerts.length === 0) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon}>🛡️</div>
        <p>Sistema monitorando...</p>
        <p>Aguardando ameaças...</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>ALERTAS EM TEMPO REAL</h3>
      <div className={styles.list}>
        {alerts.map((alert) => (
          <div key={alert.id} className={styles.alert}>
            <div className={styles.alertHeader}>
              <div className={styles.alertType}>
                <span className={styles.icon}>{getSeverityIcon(alert.severity)}</span>
                <Badge variant={getSeverityVariant(alert.severity)} size="sm">
                  {alert.type}
                </Badge>
              </div>
              <span className={styles.timestamp}>{alert.timestamp}</span>
            </div>
            <p className={styles.message}>{alert.message}</p>
            {alert.source && (
              <div className={styles.source}>Origem: {alert.source}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsList;

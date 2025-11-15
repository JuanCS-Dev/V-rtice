import React from 'react';
import { Badge } from '../../../shared';
import styles from './ServicesPanel.module.css';

export const ServicesPanel = ({ data }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>SERVIÇOS DETECTADOS</h3>

      <div className={styles.fields}>
        {/* Open Ports */}
        <div className={styles.field}>
          <span className={styles.label}>PORTAS ABERTAS</span>
          <div className={styles.ports}>
            {data.open_ports.map((port, index) => (
              <Badge key={index} variant="warning" size="sm">
                {port}
              </Badge>
            ))}
          </div>
        </div>

        {/* Identified Services */}
        <div className={styles.field}>
          <span className={styles.label}>SERVIÇOS IDENTIFICADOS</span>
          <div className={styles.services}>
            {data.services.map((service, index) => (
              <div key={index} className={styles.serviceCard}>
                <div className={styles.serviceHeader}>
                  <span className={styles.servicePort}>Porto {service.port}</span>
                  <span className={styles.serviceName}>{service.service}</span>
                </div>
                <div className={styles.serviceVersion}>{service.version}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServicesPanel;

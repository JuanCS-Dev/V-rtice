import React from 'react';
import { Badge, Alert } from '../../../shared';
import { getPortStateVariant, getServiceRiskVariant, getRiskIcon } from '../utils/scanUtils';
import styles from './ScanResults.module.css';

export const ScanResults = ({ result }) => {
  if (!result.success) {
    return (
      <Alert variant="critical">
        Erro no scan: {result.errors?.join(', ')}
      </Alert>
    );
  }

  const { data } = result;

  return (
    <div className={styles.container}>
      {/* Scan Info */}
      <div className={styles.header}>
        <h3 className={styles.title}>📡 Resultados do Scan</h3>
        <div className={styles.info}>
          <span>Comando: {data.nmap_command}</span>
          <span>Duração: {data.scan_duration}s</span>
          <span>Hosts: {data.hosts_count}</span>
        </div>
      </div>

      {/* Hosts */}
      {data.hosts?.map((host, idx) => (
        <div key={idx} className={styles.host}>
          <div className={styles.hostHeader}>
            <div>
              <h4 className={styles.hostTitle}>{host.ip}</h4>
              {host.hostname && <span className={styles.hostname}>{host.hostname}</span>}
            </div>
            <Badge variant={host.status === 'up' ? 'success' : 'default'}>
              {host.status.toUpperCase()}
            </Badge>
          </div>

          {host.os_info && (
            <div className={styles.osInfo}>
              <strong>OS:</strong> {host.os_info}
            </div>
          )}

          {/* Ports */}
          {host.ports && host.ports.length > 0 && (
            <div className={styles.ports}>
              <h5 className={styles.portsTitle}>Portas Abertas ({host.ports.length})</h5>
              <div className={styles.portsList}>
                {host.ports.map((port, portIdx) => (
                  <div key={portIdx} className={styles.portCard}>
                    <div className={styles.portHeader}>
                      <span className={styles.portNumber}>
                        {getRiskIcon(port.service)} {port.port}/{port.protocol}
                      </span>
                      <Badge variant={getPortStateVariant(port.state)} size="sm">
                        {port.state}
                      </Badge>
                    </div>
                    <div className={styles.portInfo}>
                      <span className={styles.service}>
                        <Badge variant={getServiceRiskVariant(port.service)} size="sm">
                          {port.service}
                        </Badge>
                      </span>
                      {port.product && <span className={styles.product}>{port.product}</span>}
                      {port.version && <span className={styles.version}>v{port.version}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Security Assessment */}
      {data.security_assessment && (
        <div className={styles.assessment}>
          <h4 className={styles.assessmentTitle}>🔒 Avaliação de Segurança</h4>

          {data.security_assessment.recommendations?.length > 0 && (
            <div className={styles.recommendations}>
              <h5>Recomendações:</h5>
              {data.security_assessment.recommendations.map((rec, idx) => (
                <Alert key={idx} variant="warning" size="sm">
                  {rec}
                </Alert>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ScanResults;

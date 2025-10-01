/**
 * Network Monitor Widget - REFATORADO
 *
 * Monitoramento de tráfego de rede em tempo real.
 * Este componente orquestra a UI, delegando a lógica para o hook
 * useNetworkMonitoring e a apresentação para subcomponentes dedicados.
 *
 * @version 2.0.0
 * @author Gemini
 */

import React from 'react';
import { Card } from '../../shared/Card';
import NetworkMonitorHeader from './components/NetworkMonitorHeader';
import NetworkStatistics from './components/NetworkStatistics';
import NetworkEventStream from './components/NetworkEventStream';
import NetworkAdvancedControls from './components/NetworkAdvancedControls';
import { useNetworkMonitoring } from './hooks/useNetworkMonitoring';
import styles from './NetworkMonitor.module.css';

export const NetworkMonitor = () => {
  const {
    isMonitoring,
    networkEvents,
    statistics,
    toggleMonitoring,
    getSeverityClass
  } = useNetworkMonitoring();

  return (
    <Card
      title="NETWORK MONITORING CENTER"
      badge="CYBER"
      variant="cyber"
    >
      <div className={styles.widgetBody}>
        <NetworkMonitorHeader
          isMonitoring={isMonitoring}
          onToggleMonitoring={toggleMonitoring}
        />

        <NetworkStatistics statistics={statistics} />

        <NetworkEventStream
          isMonitoring={isMonitoring}
          networkEvents={networkEvents}
          getSeverityClass={getSeverityClass}
        />

        <NetworkAdvancedControls isMonitoring={isMonitoring} />
      </div>
    </Card>
  );
};

export default NetworkMonitor;
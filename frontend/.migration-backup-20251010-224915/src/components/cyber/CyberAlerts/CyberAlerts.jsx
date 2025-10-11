import React from 'react';
import { StatusPanel } from './components/StatusPanel';
import { MetricsGrid } from './components/MetricsGrid';
import { AlertsList } from './components/AlertsList';
import { QuickActions } from './components/QuickActions';
import styles from './CyberAlerts.module.css';

/**
 * CyberAlerts - Painel de alertas e status do sistema Cyber
 * Exibe status, métricas em tempo real, stream de alertas e ações rápidas
 */
export const CyberAlerts = ({ alerts = [], threatData = {} }) => {
  return (
    <div className={styles.container}>
      <StatusPanel />
      <MetricsGrid threatData={threatData} />
      <AlertsList alerts={alerts} />
      <QuickActions />
    </div>
  );
};

export default CyberAlerts;

import React from 'react';
import { Button } from '../../../shared';
import styles from './NetworkAdvancedControls.module.css';

/**
 * Displays advanced controls for network monitoring, including filters, automatic actions, and quick actions.
 */
const NetworkAdvancedControls = ({ isMonitoring }) => {
  if (!isMonitoring) return null;

  return (
    <div className={styles.controlsGrid}>
      <div className={styles.controlCard}>
        <h4 className={styles.controlTitle}>FILTROS ATIVOS</h4>
        <div className={styles.optionGroup}>
          <label className={styles.optionLabel}>
            <input type="checkbox" className={styles.optionCheckbox} defaultChecked />
            <span>Port Scans</span>
          </label>
          <label className={styles.optionLabel}>
            <input type="checkbox" className={styles.optionCheckbox} defaultChecked />
            <span>SYN Floods</span>
          </label>
          <label className={styles.optionLabel}>
            <input type="checkbox" className={styles.optionCheckbox} />
            <span>Conexões Normais</span>
          </label>
        </div>
      </div>

      <div className={styles.controlCard}>
        <h4 className={styles.controlTitle}>AÇÕES AUTOMÁTICAS</h4>
        <div className={styles.optionGroup}>
          <label className={styles.optionLabel}>
            <input type="checkbox" className={styles.optionCheckbox} defaultChecked />
            <span>Auto-block suspeitos</span>
          </label>
          <label className={styles.optionLabel}>
            <input type="checkbox" className={styles.optionCheckbox} />
            <span>Notificações push</span>
          </label>
          <label className={styles.optionLabel}>
            <input type="checkbox" className={styles.optionCheckbox} defaultChecked />
            <span>Log detalhado</span>
          </label>
        </div>
      </div>

      <div className={styles.controlCard}>
        <h4 className={styles.controlTitle}>AÇÕES RÁPIDAS</h4>
        <div className={styles.optionGroup}>
          <Button variant="danger" size="md" className={styles.actionButton}>
            BLOQUEAR IP
          </Button>
          <Button variant="warning" size="md" className={styles.actionButton}>
            SCAN REVERSO
          </Button>
          <Button variant="cyber" size="md" className={styles.actionButton}>
            EXPORTAR LOG
          </Button>
        </div>
      </div>
    </div>
  );
};

export default React.memo(NetworkAdvancedControls);

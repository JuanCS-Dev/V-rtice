import React from 'react';
import { Button } from '../../../shared';
import styles from './QuickActions.module.css';

export const QuickActions = () => {
  return (
    <div className={styles.container}>
      <h4 className={styles.title}>AÇÕES RÁPIDAS</h4>
      <div className={styles.actions}>
        <Button variant="critical" size="sm" fullWidth>
          🚨 ALERTA GERAL
        </Button>
        <Button variant="warning" size="sm" fullWidth>
          🔍 SCAN EMERGENCIAL
        </Button>
        <Button variant="cyber" size="sm" fullWidth>
          📊 RELATÓRIO SITUACIONAL
        </Button>
      </div>
    </div>
  );
};

export default QuickActions;

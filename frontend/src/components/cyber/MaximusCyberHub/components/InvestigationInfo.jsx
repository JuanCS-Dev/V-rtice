import React from 'react';
import { INVESTIGATION_TYPES } from '../utils/investigationUtils';
import styles from './InvestigationInfo.module.css';

export const InvestigationInfo = ({ investigation }) => {
  if (!investigation) return null;

  const investigationTypeName = INVESTIGATION_TYPES.find(t => t.id === investigation.type)?.name;

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <div className={styles.left}>
          <div className={styles.id}>Investigation #{investigation.id}</div>
          <div className={styles.target}>Target: {investigation.target}</div>
        </div>
        <div className={styles.right}>
          <div className={styles.type}>{investigationTypeName}</div>
          <div className={styles.status}>
            {investigation.status === 'running' ? 'Running...' : 'Completed'}
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import styles from './HubHeader.module.css';

export const HubHeader = () => {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <div className={styles.branding}>
          <div className={styles.icon}>
            <span>🤖</span>
          </div>
          <div className={styles.info}>
            <h2 className={styles.title}>AURORA CYBER INTEL HUB</h2>
            <p className={styles.subtitle}>Autonomous investigation orchestrator</p>
          </div>
        </div>
        <div className={styles.status}>
          <div className={styles.indicator}></div>
          <span className={styles.statusText}>ONLINE</span>
        </div>
      </div>
    </div>
  );
};

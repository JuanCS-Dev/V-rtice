/**
 * OffensiveFooter - Red Team Status Footer
 * Displays system status and operational information
 */

import React, { useState, useEffect } from 'react';
import styles from './OffensiveFooter.module.css';

export const OffensiveFooter = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [networkStatus, setNetworkStatus] = useState('ONLINE');

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    // Monitor network status
    const handleOnline = () => setNetworkStatus('ONLINE');
    const handleOffline = () => setNetworkStatus('OFFLINE');

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      clearInterval(timer);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <footer className={styles.footer}>
      <div className={styles.leftSection}>
        <div className={styles.statusItem}>
          <span className={styles.label}>SYSTEM:</span>
          <span className={`${styles.value} ${styles.statusOnline}`}>
            {networkStatus}
          </span>
        </div>
        <div className={styles.statusItem}>
          <span className={styles.label}>MODE:</span>
          <span className={styles.value}>RED TEAM</span>
        </div>
        <div className={styles.statusItem}>
          <span className={styles.label}>OPSEC:</span>
          <span className={`${styles.value} ${styles.statusEnabled}`}>ENABLED</span>
        </div>
      </div>

      <div className={styles.centerSection}>
        <span className={styles.footerBrand}>
          VERTICE OFFENSIVE OPS | MAXIMUS AI INTEGRATION
        </span>
      </div>

      <div className={styles.rightSection}>
        <div className={styles.statusItem}>
          <span className={styles.label}>UTC:</span>
          <span className={styles.value}>
            {currentTime.toUTCString().slice(-12, -4)}
          </span>
        </div>
        <div className={styles.statusItem}>
          <span className={styles.label}>LOCAL:</span>
          <span className={styles.value}>
            {currentTime.toLocaleTimeString()}
          </span>
        </div>
      </div>
    </footer>
  );
};

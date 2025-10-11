/**
 * PurpleFooter - Purple Team Status Footer
 */

import React, { useState, useEffect } from 'react';
import styles from './PurpleFooter.module.css';

export const PurpleFooter = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <footer className={styles.footer}>
      <div className={styles.leftSection}>
        <div className={styles.statusItem}>
          <span className={styles.label}>MODE:</span>
          <span className={styles.value}>PURPLE TEAM</span>
        </div>
        <div className={styles.statusItem}>
          <span className={styles.label}>CORRELATION:</span>
          <span className={`${styles.value} ${styles.statusEnabled}`}>ACTIVE</span>
        </div>
      </div>

      <div className={styles.centerSection}>
        <span className={styles.footerBrand}>
          VERTICE PURPLE TEAM OPS | UNIFIED RED & BLUE TEAM COORDINATION
        </span>
      </div>

      <div className={styles.rightSection}>
        <div className={styles.statusItem}>
          <span className={styles.label}>TIME:</span>
          <span className={styles.value}>{currentTime.toLocaleTimeString()}</span>
        </div>
      </div>
    </footer>
  );
};

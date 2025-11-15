import React from 'react';
import styles from './EmptyState.module.css';

export const EmptyState = () => {
  return (
    <div className={styles.container}>
      <div className={styles.icon}>🎯</div>
      <h3 className={styles.title}>IP INTELLIGENCE READY</h3>
      <p className={styles.description}>
        Digite um endereço IP para análise completa de geolocalização e ameaças
      </p>
    </div>
  );
};

export default EmptyState;

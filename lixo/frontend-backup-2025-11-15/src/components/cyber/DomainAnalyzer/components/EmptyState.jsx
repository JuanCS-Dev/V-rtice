import React from "react";
import styles from "./EmptyState.module.css";

export const EmptyState = () => {
  return (
    <div className={styles.container}>
      <div className={styles.icon}>🌐</div>
      <h3 className={styles.title}>DOMAIN ANALYZER READY</h3>
      <p className={styles.description}>
        Digite um domínio para iniciar a análise de inteligência
      </p>
    </div>
  );
};

export default EmptyState;

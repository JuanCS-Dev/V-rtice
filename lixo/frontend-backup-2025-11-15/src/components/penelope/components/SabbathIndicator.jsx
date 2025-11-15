/**
 * SabbathIndicator - Indicador de Modo Sabbath
 * ============================================
 *
 * Mostra visualmente quando o sistema está em modo Sabbath (domingo).
 * Durante o Sabbath, apenas monitoramento é permitido (zero patches).
 *
 * Fundamento bíblico: Êxodo 20:8-11
 * "Lembra-te do dia de sábado, para o santificar."
 */

import React from 'react';
import styles from './SabbathIndicator.module.css';

export const SabbathIndicator = ({ isSabbath }) => {
  if (!isSabbath) {
    return (
      <div className={styles.indicator} style={{ background: 'rgba(0, 255, 136, 0.1)', borderColor: '#00ff88' }}>
        <span className={styles.icon}>⚙️</span>
        <div className={styles.content}>
          <div className={styles.title}>OPERATIONAL MODE</div>
          <div className={styles.description}>Auto-healing ativo - Patches permitidos</div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.indicator} style={{ background: 'rgba(155, 89, 182, 0.1)', borderColor: '#9b59b6' }}>
      <span className={styles.icon}>🕊️</span>
      <div className={styles.content}>
        <div className={styles.title} style={{ color: '#9b59b6' }}>
          SABBATH MODE ATIVO
        </div>
        <div className={styles.description}>
          Apenas monitoramento - Zero patches (Êxodo 20:8-11)
        </div>
      </div>
    </div>
  );
};

export default SabbathIndicator;

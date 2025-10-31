/**
 * HealingTimeline - Timeline de Eventos de Healing
 * ================================================
 *
 * Mostra histórico de patches aplicados com outcomes e métricas.
 */

import React from 'react';
import styles from './HealingTimeline.module.css';

export const HealingTimeline = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className={styles.empty}>
        <p>📝 Nenhum evento de healing registrado ainda</p>
      </div>
    );
  }

  const getOutcomeStyle = (outcome) => {
    switch (outcome) {
      case 'success':
        return { borderColor: '#00ff88', backgroundColor: 'rgba(0, 255, 136, 0.1)' };
      case 'failed':
        return { borderColor: '#ff6b6b', backgroundColor: 'rgba(255, 107, 107, 0.1)' };
      case 'escalated':
        return { borderColor: '#ffaa00', backgroundColor: 'rgba(255, 170, 0, 0.1)' };
      default:
        return { borderColor: 'rgba(255, 255, 255, 0.3)', backgroundColor: 'rgba(255, 255, 255, 0.05)' };
    }
  };

  const getOutcomeIcon = (outcome) => {
    switch (outcome) {
      case 'success':
        return '✅';
      case 'failed':
        return '❌';
      case 'escalated':
        return '⚠️';
      default:
        return '🔄';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={styles.timeline}>
      <h3 className={styles.title}>📋 Histórico de Healing</h3>
      <div className={styles.events}>
        {events.map((event, index) => {
          const outcomeStyle = getOutcomeStyle(event.outcome);
          const outcomeIcon = getOutcomeIcon(event.outcome);

          return (
            <div key={event.event_id || index} className={styles.event} style={outcomeStyle}>
              {/* Left indicator */}
              <div className={styles.indicator} style={{ borderColor: outcomeStyle.borderColor }}>
                <span className={styles.outcomeIcon}>{outcomeIcon}</span>
              </div>

              {/* Event content */}
              <div className={styles.content}>
                <div className={styles.header}>
                  <span className={styles.timestamp}>{formatTimestamp(event.timestamp)}</span>
                  <span className={styles.outcome} style={{ color: outcomeStyle.borderColor }}>
                    {event.outcome.toUpperCase()}
                  </span>
                </div>

                <div className={styles.body}>
                  <div className={styles.anomaly}>{event.anomaly_detected}</div>

                  <div className={styles.metrics}>
                    <div className={styles.metric}>
                      <span className={styles.metricLabel}>Confiança:</span>
                      <span className={styles.metricValue}>
                        {(event.diagnosis_confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    {event.patch_size_lines && (
                      <div className={styles.metric}>
                        <span className={styles.metricLabel}>Patch:</span>
                        <span className={styles.metricValue}>{event.patch_size_lines} linhas</span>
                      </div>
                    )}

                    {event.mansidao_score && (
                      <div className={styles.metric}>
                        <span className={styles.metricLabel}>Mansidão:</span>
                        <span className={styles.metricValue}>
                          {(event.mansidao_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}

                    {event.sabbath_mode && (
                      <div className={styles.metric}>
                        <span className={styles.metricLabel}>Modo:</span>
                        <span className={styles.metricValue} style={{ color: '#9b59b6' }}>
                          🕊️ Sabbath
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default HealingTimeline;

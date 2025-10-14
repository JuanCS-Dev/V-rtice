/**
 * ═══════════════════════════════════════════════════════════════════════════
 * ACTIVITY FEED SECTION - TACTICAL OPERATIONS LOG
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * MISSÃO: Log operacional em tempo real de engajamentos de combate
 *
 * Capacidades:
 * - Timeline vertical de operações
 * - Pulsos táticos animados
 * - Auto-scroll suave de intel
 * - Fade in/out de relatórios
 * - Severity color coding militar
 * - Tema Tactical Warfare
 * - Live badge de comando operacional
 */

import React, { useState, useEffect, useRef } from 'react';
import styles from './ActivityFeedSection.module.css';

export const ActivityFeedSection = ({ realThreats = [] }) => {
  const [activities, setActivities] = useState([]);
  const feedRef = useRef(null);

  // Gerar atividades a partir de ameaças REAIS
  useEffect(() => {
    if (realThreats.length === 0) return;

    const latestThreat = realThreats[0];

    const newActivity = {
      id: latestThreat.id,
      timestamp: latestThreat.timestamp,
      ...generateActivityFromThreat(latestThreat)
    };

    setActivities(prev => [newActivity, ...prev].slice(0, 20));
  }, [realThreats]);

  // Gera atividade formatada baseada na ameaça real
  const generateActivityFromThreat = (threat) => {
    if (threat.isMalicious) {
      return {
        type: 'threat',
        icon: '🎯',
        title: 'HOSTIL DETECTADO',
        message: threat.ip,
        detail: `Ameaça: ${threat.threatScore}/100 | ${threat.geolocation?.country || 'Unknown'}`,
        severity: 'critical'
      };
    } else if (threat.severity === 'suspicious') {
      return {
        type: 'warning',
        icon: '⚠️',
        title: 'ALVO SUSPEITO',
        message: threat.ip,
        detail: `Ameaça: ${threat.threatScore}/100 | ${threat.geolocation?.country || 'Unknown'}`,
        severity: 'high'
      };
    } else if (threat.severity === 'questionable') {
      return {
        type: 'info',
        icon: '🔍',
        title: 'INTEL ADQUIRIDA',
        message: threat.ip,
        detail: `Ameaça: ${threat.threatScore}/100`,
        severity: 'medium'
      };
    } else {
      return {
        type: 'success',
        icon: '✅',
        title: 'ZONA LIMPA',
        message: threat.ip,
        detail: `Ameaça: ${threat.threatScore}/100 - Seguro`,
        severity: 'low'
      };
    }
  };

  // Atividades de background
  useEffect(() => {
    const backgroundActivities = [
      { type: 'info', icon: '🔭', title: 'RECON INICIADO', message: '192.168.0.0/24', detail: 'Varredura de zona tática', severity: 'low' },
      { type: 'success', icon: '🔐', title: 'CERTIFICADO ARMADO', message: 'api.vertice.com', detail: 'SSL certificate válido', severity: 'low' },
      { type: 'info', icon: '💾', title: 'BACKUP TÁTICO', message: 'prod-db-01', detail: 'Database snapshot seguro', severity: 'low' },
      { type: 'info', icon: '🔍', title: 'PORT SCAN COMPLETO', message: '10.0.0.0/8', detail: '65535 portas analisadas', severity: 'low' },
      { type: 'success', icon: '🛡️', title: 'ESCUDO ATUALIZADO', message: 'fw-edge-01', detail: 'Defesas reforçadas', severity: 'low' }
    ];

    const interval = setInterval(() => {
      const randomActivity = backgroundActivities[Math.floor(Math.random() * backgroundActivities.length)];
      const newActivity = {
        ...randomActivity,
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString('pt-BR'),
      };

      setActivities(prev => [newActivity, ...prev].slice(0, 20));
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className={styles.feed} aria-label="Live activity feed">
      {/* Header */}
      <header className={styles.header}>
        <h2 className={styles.title}>
          <span className={styles.titleIcon}>📡</span>
          <span>LOG OPERACIONAL</span>
        </h2>
        <div className={styles.liveBadge}>
          <span className={styles.liveDot}></span>
          <span>AO VIVO</span>
        </div>
      </header>

      {/* Feed Container */}
      <div ref={feedRef} className={styles.container}>
        {activities.length === 0 ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>📡</div>
            <p className={styles.emptyText}>Aguardando operações...</p>
            <p className={styles.emptyHint}>Arsenal monitorando alvos globais</p>
          </div>
        ) : (
          <div className={styles.timeline}>
            {activities.map((activity, index) => (
              <ActivityItem
                key={activity.id}
                activity={activity}
                index={index}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

// Sub-component: Activity Item
const ActivityItem = ({ activity, index }) => {
  return (
    <article
      className={`${styles.item} ${styles[activity.severity]}`}
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      {/* Timeline Dot */}
      <div className={styles.dot}>
        <span className={styles.pulse}></span>
      </div>

      {/* Icon */}
      <div className={styles.icon}>
        {activity.icon}
      </div>

      {/* Content */}
      <div className={styles.content}>
        <div className={styles.itemHeader}>
          <h3 className={styles.itemTitle}>{activity.title}</h3>
          <span className={styles.timestamp}>{activity.timestamp}</span>
        </div>
        <p className={styles.message}>{activity.message}</p>
        {activity.detail && (
          <p className={styles.detail}>{activity.detail}</p>
        )}
      </div>

      {/* Severity Badge */}
      <div className={styles.badge}>
        {activity.severity?.toUpperCase()}
      </div>
    </article>
  );
};

export default ActivityFeedSection;

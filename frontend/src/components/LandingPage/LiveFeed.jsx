/**
 * LiveFeed - Feed de Atividades em Tempo Real
 */

import React, { useState, useEffect } from 'react';

export const LiveFeed = () => {
  const [activities, setActivities] = useState([]);

  const activityTypes = [
    { type: 'scan', icon: '🔍', text: 'Scan de rede iniciado em', target: '192.168.1.0/24' },
    { type: 'threat', icon: '⚠️', text: 'Ameaça detectada em', target: 'server-prod-01' },
    { type: 'block', icon: '🚫', text: 'IP bloqueado:', target: '45.123.45.67' },
    { type: 'alert', icon: '🔔', text: 'Alerta de vulnerabilidade:', target: 'CVE-2024-1234' },
    { type: 'success', icon: '✅', text: 'Patch aplicado com sucesso em', target: 'web-app-02' },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      const randomActivity = activityTypes[Math.floor(Math.random() * activityTypes.length)];
      const newActivity = {
        ...randomActivity,
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString('pt-BR'),
      };

      setActivities(prev => [newActivity, ...prev].slice(0, 10));
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="live-feed-section">
      <h2 className="section-title">
        <span className="title-icon">📡</span>
        Atividades em Tempo Real
        <span className="live-badge">
          <span className="pulse-dot-small"></span>
          LIVE
        </span>
      </h2>

      <div className="live-feed">
        {activities.length === 0 ? (
          <div className="feed-empty">
            <i className="fas fa-satellite-dish"></i>
            <p>Aguardando atividades...</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div key={activity.id} className={`feed-item feed-${activity.type}`}>
              <span className="feed-icon">{activity.icon}</span>
              <div className="feed-content">
                <span className="feed-text">{activity.text}</span>
                <span className="feed-target">{activity.target}</span>
              </div>
              <span className="feed-time">{activity.timestamp}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

/**
 * StatsPanel - Estatísticas em Tempo Real
 */

import React from 'react';

export const StatsPanel = ({ stats }) => {
  const statCards = [
    {
      icon: '🛡️',
      label: 'Ameaças Detectadas',
      value: stats.threatsDetected,
      trend: '+12%',
      color: 'red'
    },
    {
      icon: '👁️',
      label: 'Monitoramento Ativo',
      value: stats.activeMonitoring,
      trend: 'Estável',
      color: 'cyan'
    },
    {
      icon: '🌐',
      label: 'Redes Escaneadas',
      value: stats.networksScanned,
      trend: '+8%',
      color: 'green'
    },
    {
      icon: '⚡',
      label: 'Uptime',
      value: stats.uptime,
      trend: '30 dias',
      color: 'yellow'
    }
  ];

  return (
    <div className="stats-panel">
      {statCards.map((stat, index) => (
        <div key={index} className={`stat-card stat-${stat.color}`}>
          <div className="stat-icon">{stat.icon}</div>
          <div className="stat-content">
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-trend">{stat.trend}</div>
          </div>
          <div className="stat-pulse"></div>
        </div>
      ))}
    </div>
  );
};

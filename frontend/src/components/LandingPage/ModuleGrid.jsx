/**
 * ModuleGrid - Grid de Módulos Disponíveis
 */

import React from 'react';

export const ModuleGrid = ({ setCurrentView }) => {
  const modules = [
    {
      id: 'maximus',
      name: 'MAXIMUS AI',
      description: 'Autonomous Intelligence Platform',
      icon: '🧠',
      color: 'gradient-ai',
      features: ['AI Chat & Orchestration', 'Self-Improvement', 'Workflows', 'Terminal CLI']
    },
    {
      id: 'defensive',
      name: 'DEFENSIVE OPS',
      description: 'Blue Team Security Operations',
      icon: '🛡️',
      color: 'cyan',
      features: ['Threat Detection', 'Network Monitor', 'Malware Analysis', 'SIEM']
    },
    {
      id: 'offensive',
      name: 'OFFENSIVE OPS',
      description: 'Red Team Attack Operations',
      icon: '⚔️',
      color: 'red',
      features: ['Network Recon', 'Vuln Intel', 'Web Attack', 'C2 Control', 'BAS']
    },
    {
      id: 'purple',
      name: 'PURPLE TEAM',
      description: 'Unified Red & Blue Coordination',
      icon: '🟣',
      color: 'purple',
      features: ['Attack-Defense Correlation', 'Gap Analysis', 'Coverage Metrics']
    },
    {
      id: 'osint',
      name: 'OSINT Intelligence',
      description: 'Open Source Investigation',
      icon: '🕵️',
      color: 'blue',
      features: ['Social Media', 'Breach Data', 'Dark Web Monitoring']
    },
    {
      id: 'admin',
      name: 'ADMIN PANEL',
      description: 'System Administration',
      icon: '⚙️',
      color: 'yellow',
      features: ['System Logs', 'User Management', 'API Configuration']
    }
  ];

  return (
    <div className="module-section">
      <h2 className="section-title">
        <span className="title-icon">⚡</span>
        Módulos Disponíveis
      </h2>

      <div className="module-grid">
        {modules.map((module) => (
          <div
            key={module.id}
            className={`module-card module-${module.color}`}
            onClick={() => setCurrentView(module.id)}
          >
            <div className="module-header">
              <span className="module-icon">{module.icon}</span>
              <h3 className="module-name">{module.name}</h3>
            </div>

            <p className="module-description">{module.description}</p>

            <div className="module-features">
              {module.features.map((feature, i) => (
                <span key={i} className="feature-tag">
                  {feature}
                </span>
              ))}
            </div>

            <div className="module-action">
              <span>ACESSAR MÓDULO</span>
              <i className="fas fa-arrow-right"></i>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

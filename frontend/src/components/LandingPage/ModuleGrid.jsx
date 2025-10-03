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
      features: ['Self-Improvement', 'Malware Analysis', 'AI Insights']
    },
    {
      id: 'cyber',
      name: 'Cyber Security',
      description: 'Análise de Redes e Ameaças Digitais',
      icon: '🛡️',
      color: 'cyan',
      features: ['Threat Map', 'Vulnerability Scanner', 'Network Monitor']
    },
    {
      id: 'osint',
      name: 'OSINT Intelligence',
      description: 'Investigação em Mídias Sociais',
      icon: '🕵️',
      color: 'purple',
      features: ['Social Media', 'Breach Data', 'Dark Web Monitoring']
    },
    {
      id: 'terminal',
      name: 'Terminal CLI',
      description: 'Console Avançado para Especialistas',
      icon: '💻',
      color: 'orange',
      features: ['Command Line', 'Script Automation', 'Custom Tools']
    },
    {
      id: 'admin',
      name: 'Administração',
      description: 'Monitoramento e Configurações',
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

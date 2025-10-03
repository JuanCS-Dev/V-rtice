/**
 * ═══════════════════════════════════════════════════════════════════════════
 * AI INSIGHTS PANEL - Unified Intelligence Dashboard
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dashboard consolidado mostrando:
 * - Visão geral de todos os componentes de AI
 * - Métricas combinadas ORÁCULO + EUREKA
 * - Stream de atividade da AI em tempo real
 * - Status de saúde dos serviços
 * - Workflow de integração completo
 */

import React, { useState } from 'react';
import './Panels.css';

export const AIInsightsPanel = ({ aiStatus, brainActivity }) => {
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);

  // Calculate combined metrics
  const combinedMetrics = {
    totalOperations: (aiStatus.oraculo.suggestions || 0) + (aiStatus.eureka.threatsDetected || 0),
    aiUptime: aiStatus.core.uptime,
    systemHealth: aiStatus.core.status === 'online' ? 100 : 50,
    activeModules: [
      aiStatus.oraculo.status !== 'offline',
      aiStatus.eureka.status !== 'offline',
      aiStatus.core.status === 'online'
    ].filter(Boolean).length
  };

  const workflows = [
    {
      id: 'analyze-and-respond',
      name: 'Analyze & Respond',
      description: 'Workflow completo: EUREKA → ADR Core → Auto Response',
      icon: '🔄',
      steps: [
        { name: 'EUREKA Analysis', status: 'ready', icon: '🔬' },
        { name: 'Playbook Generation', status: 'ready', icon: '📋' },
        { name: 'ADR Core Loading', status: 'ready', icon: '⚙️' },
        { name: 'Auto Execution', status: 'ready', icon: '🚀' }
      ]
    },
    {
      id: 'self-improvement',
      name: 'Self-Improvement Cycle',
      description: 'ORÁCULO escaneia, analisa e melhora o próprio código',
      icon: '🔮',
      steps: [
        { name: 'Codebase Scan', status: 'ready', icon: '🔍' },
        { name: 'AI Suggestions', status: 'ready', icon: '💡' },
        { name: 'Safe Implementation', status: 'ready', icon: '🛡️' },
        { name: 'Testing & Validation', status: 'ready', icon: '✅' }
      ]
    },
    {
      id: 'supply-chain-guardian',
      name: 'Supply Chain Guardian',
      description: 'ORÁCULO + EUREKA protegem supply chain',
      icon: '🛡️',
      steps: [
        { name: 'Dependency Scan', status: 'ready', icon: '📦' },
        { name: 'Code Analysis', status: 'ready', icon: '🔬' },
        { name: 'Threat Detection', status: 'ready', icon: '⚠️' },
        { name: 'Auto Mitigation', status: 'ready', icon: '🔧' }
      ]
    }
  ];

  const getHealthColor = (health) => {
    if (health >= 80) return 'health-excellent';
    if (health >= 60) return 'health-good';
    if (health >= 40) return 'health-fair';
    return 'health-poor';
  };

  const getActivitySeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🔴';
      case 'warning': return '🟡';
      case 'success': return '🟢';
      default: return '🔵';
    }
  };

  return (
    <div className="insights-panel">
      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* TOP SECTION - System Overview */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="system-overview">
        <div className="overview-grid">
          {/* Brain Visual */}
          <div className="brain-visual-card">
            <div className="brain-container">
              <div className="brain-icon">🧠</div>
              <div className="brain-pulse"></div>
              <div className="brain-status">
                <span className={`status-text ${aiStatus.core.status === 'online' ? 'status-online' : 'status-offline'}`}>
                  {aiStatus.core.status === 'online' ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>
            </div>
            <div className="brain-label">MAXIMUS AI CORE</div>
            <div className="brain-metrics">
              <div className="metric-item">
                <span className="metric-icon">⏱️</span>
                <span className="metric-text">Uptime: {combinedMetrics.aiUptime}</span>
              </div>
              <div className="metric-item">
                <span className="metric-icon">🔧</span>
                <span className="metric-text">Modules: {combinedMetrics.activeModules}/3</span>
              </div>
            </div>
          </div>

          {/* Health Meter */}
          <div className="health-meter-card">
            <h3>System Health</h3>
            <div className="health-display">
              <div className={`health-value ${getHealthColor(combinedMetrics.systemHealth)}`}>
                {combinedMetrics.systemHealth}%
              </div>
              <div className="health-bar">
                <div
                  className={`health-fill ${getHealthColor(combinedMetrics.systemHealth)}`}
                  style={{ width: `${combinedMetrics.systemHealth}%` }}
                ></div>
              </div>
            </div>
            <div className="health-indicators">
              <div className={`indicator ${aiStatus.core.status === 'online' ? 'indicator-active' : ''}`}>
                <span>🔵</span>
                <span>Core Engine</span>
              </div>
              <div className={`indicator ${aiStatus.oraculo.status !== 'offline' ? 'indicator-active' : ''}`}>
                <span>🔮</span>
                <span>Oráculo</span>
              </div>
              <div className={`indicator ${aiStatus.eureka.status !== 'offline' ? 'indicator-active' : ''}`}>
                <span>🔬</span>
                <span>Eureka</span>
              </div>
            </div>
          </div>

          {/* Combined Stats */}
          <div className="combined-stats-card">
            <h3>Estatísticas Consolidadas</h3>
            <div className="stats-list">
              <div className="stat-row">
                <span className="stat-label">🔮 Sugestões Oráculo:</span>
                <span className="stat-number">{aiStatus.oraculo.suggestions || 0}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">🔬 Ameaças Eureka:</span>
                <span className="stat-number">{aiStatus.eureka.threatsDetected || 0}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">⚡ Total de Operações:</span>
                <span className="stat-number">{combinedMetrics.totalOperations}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">🧠 Atividades Registradas:</span>
                <span className="stat-number">{brainActivity.length}</span>
              </div>
            </div>
          </div>

          {/* Last Activities */}
          <div className="last-activities-card">
            <h3>Última Atividade</h3>
            <div className="activities-list">
              {aiStatus.oraculo.lastRun && (
                <div className="activity-row">
                  <span className="activity-icon">🔮</span>
                  <div className="activity-info">
                    <span className="activity-name">Análise Oráculo</span>
                    <span className="activity-time">{aiStatus.oraculo.lastRun}</span>
                  </div>
                </div>
              )}
              {aiStatus.eureka.lastAnalysis && (
                <div className="activity-row">
                  <span className="activity-icon">🔬</span>
                  <div className="activity-info">
                    <span className="activity-name">Análise Eureka</span>
                    <span className="activity-time">{aiStatus.eureka.lastAnalysis}</span>
                  </div>
                </div>
              )}
              {!aiStatus.oraculo.lastRun && !aiStatus.eureka.lastAnalysis && (
                <div className="no-activity">
                  <span>⏳</span>
                  <span>Nenhuma atividade recente</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* MIDDLE SECTION - Integrated Workflows */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="workflows-section">
        <h2 className="section-title">
          <span className="title-icon">🔄</span>
          Workflows Integrados
        </h2>

        <div className="workflows-grid">
          {workflows.map(workflow => (
            <div
              key={workflow.id}
              className={`workflow-card ${selectedWorkflow === workflow.id ? 'workflow-selected' : ''}`}
              onClick={() => setSelectedWorkflow(workflow.id)}
            >
              <div className="workflow-header">
                <span className="workflow-icon">{workflow.icon}</span>
                <div className="workflow-info">
                  <h3 className="workflow-name">{workflow.name}</h3>
                  <p className="workflow-description">{workflow.description}</p>
                </div>
              </div>

              <div className="workflow-steps">
                {workflow.steps.map((step, index) => (
                  <div key={index} className="workflow-step">
                    <span className="step-icon">{step.icon}</span>
                    <span className="step-name">{step.name}</span>
                    <span className={`step-status step-status-${step.status}`}>
                      {step.status}
                    </span>
                  </div>
                ))}
              </div>

              <button className="workflow-execute-btn">
                🚀 Executar Workflow
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* BOTTOM SECTION - Live Activity Stream */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="live-stream-section">
        <h2 className="section-title">
          <span className="title-icon">📡</span>
          Live Activity Stream
          <span className="activity-count-badge">{brainActivity.length}</span>
        </h2>

        <div className="stream-container">
          {brainActivity.length === 0 ? (
            <div className="stream-empty">
              <div className="empty-icon">🔇</div>
              <h3>Aguardando atividade da AI</h3>
              <p>O stream mostrará ações em tempo real dos componentes MAXIMUS</p>
            </div>
          ) : (
            <div className="stream-list">
              {brainActivity.map(activity => (
                <div key={activity.id} className={`stream-item stream-${activity.severity}`}>
                  <div className="stream-timestamp">{activity.timestamp}</div>
                  <div className="stream-content">
                    <span className="stream-type-badge">{activity.type}</span>
                    <span className="stream-severity-icon">
                      {getActivitySeverityIcon(activity.severity)}
                    </span>
                    <span className="stream-action">{activity.action}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* ARCHITECTURE DIAGRAM */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="architecture-section">
        <h2 className="section-title">
          <span className="title-icon">🏗️</span>
          Arquitetura MAXIMUS AI
        </h2>

        <div className="architecture-diagram">
          <div className="arch-layer arch-layer-1">
            <div className="arch-component arch-integration">
              <span className="arch-icon">🌐</span>
              <span className="arch-name">MAXIMUS Integration</span>
              <span className="arch-port">:8099</span>
            </div>
          </div>

          <div className="arch-layer arch-layer-2">
            <div className="arch-component arch-oraculo">
              <span className="arch-icon">🔮</span>
              <span className="arch-name">ORÁCULO</span>
              <span className="arch-desc">Self-Improvement</span>
            </div>

            <div className="arch-component arch-eureka">
              <span className="arch-icon">🔬</span>
              <span className="arch-name">EUREKA</span>
              <span className="arch-desc">Malware Analysis</span>
            </div>

            <div className="arch-component arch-core">
              <span className="arch-icon">🧠</span>
              <span className="arch-name">MAXIMUS Core</span>
              <span className="arch-desc">:8001</span>
            </div>
          </div>

          <div className="arch-layer arch-layer-3">
            <div className="arch-component arch-adr">
              <span className="arch-icon">⚙️</span>
              <span className="arch-name">ADR Core</span>
              <span className="arch-port">:8050</span>
            </div>

            <div className="arch-component arch-services">
              <span className="arch-icon">🔧</span>
              <span className="arch-name">Backend Services</span>
              <span className="arch-desc">IP Intel | Threat Intel | Malware</span>
            </div>
          </div>

          {/* Connection Lines (CSS Animations) */}
          <svg className="arch-connections" width="100%" height="100%">
            <line x1="50%" y1="20%" x2="33%" y2="50%" className="connection-line" />
            <line x1="50%" y1="20%" x2="50%" y2="50%" className="connection-line" />
            <line x1="50%" y1="20%" x2="67%" y2="50%" className="connection-line" />
            <line x1="33%" y1="60%" x2="33%" y2="80%" className="connection-line" />
            <line x1="67%" y1="60%" x2="67%" y2="80%" className="connection-line" />
          </svg>
        </div>

        <div className="architecture-legend">
          <div className="legend-item">
            <span className="legend-dot legend-online"></span>
            <span>Online & Operacional</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot legend-idle"></span>
            <span>Idle (Pronto para uso)</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot legend-offline"></span>
            <span>Offline</span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* QUICK ACTIONS */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="quick-actions-section">
        <h2 className="section-title">
          <span className="title-icon">⚡</span>
          Quick Actions
        </h2>

        <div className="quick-actions-grid">
          <button className="quick-action-btn quick-action-primary">
            <span className="action-icon">🔮</span>
            <span className="action-text">Run Self-Improvement</span>
          </button>

          <button className="quick-action-btn quick-action-danger">
            <span className="action-icon">🔬</span>
            <span className="action-text">Analyze Malware</span>
          </button>

          <button className="quick-action-btn quick-action-info">
            <span className="action-icon">📊</span>
            <span className="action-text">View Full Stats</span>
          </button>

          <button className="quick-action-btn quick-action-success">
            <span className="action-icon">🔄</span>
            <span className="action-text">Execute Workflow</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIInsightsPanel;

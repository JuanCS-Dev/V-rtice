/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MAXIMUS AI 3.0 PANEL - Neural Architecture Dashboard
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dashboard para visualizar os componentes neurais do MAXIMUS AI 3.0:
 * - NEUROMODULAÇÃO: Dopamina, Serotonina, Acetilcolina, Noradrenalina
 * - CONSOLIDAÇÃO DE MEMÓRIA: Hippocampal Replay, Sleep/Wake Cycles
 * - HSAS: Hybrid Skill Acquisition System
 * - PLANEJAMENTO ESTRATÉGICO: Córtex Pré-frontal Digital
 * - SISTEMA IMUNOLÓGICO: Imunidade Inata + Adaptativa
 *
 * Design Philosophy: Neuroscience meets Cybersecurity
 */

import React, { useState, useEffect } from 'react';
import { NeuromodulationWidget } from './widgets/NeuromodulationWidget';
import { MemoryConsolidationWidget } from './widgets/MemoryConsolidationWidget';
import { HSASWidget } from './widgets/HSASWidget';
import { StrategicPlanningWidget } from './widgets/StrategicPlanningWidget';
import { ImmunisWidget } from './widgets/ImmunisWidget';
import { ThreatPredictionWidget } from './widgets/ThreatPredictionWidget';
import { ImmuneEnhancementWidget } from './widgets/ImmuneEnhancementWidget';
import { DistributedTopologyWidget } from './widgets/DistributedTopologyWidget';
import './MaximusAI3Panel.css';

export const MaximusAI3Panel = ({ aiStatus, setAiStatus }) => {
  const [selectedWidget, setSelectedWidget] = useState('overview'); // 'overview', 'neuro', 'memory', 'hsas', 'planning', 'immunis', 'cognition', 'immune-enhance', 'distributed'
  const [systemHealth, setSystemHealth] = useState({
    neuromodulation: { status: 'checking', uptime: 0 },
    memory_consolidation: { status: 'checking', uptime: 0 },
    hsas: { status: 'checking', uptime: 0 },
    strategic_planning: { status: 'checking', uptime: 0 },
    immunis: { status: 'checking', uptime: 0 },
    enhanced_cognition: { status: 'online', uptime: 0 },
    immune_enhancement: { status: 'online', uptime: 0 },
    distributed_organism: { status: 'online', uptime: 0 }
  });
  const [neuralActivity, setNeuralActivity] = useState([]); // Neural activity stream

  // Check all services health
  useEffect(() => {
    const checkAllServices = async () => {
      const services = [
        { key: 'neuromodulation', port: 8001, name: 'Neuromodulation' },
        { key: 'memory_consolidation', port: 8002, name: 'Memory Consolidation' },
        { key: 'hsas', port: 8003, name: 'HSAS' },
        { key: 'strategic_planning', port: 8004, name: 'Strategic Planning' },
        { key: 'immunis', port: 8005, name: 'Immunis System' }
      ];

      const healthPromises = services.map(async (service) => {
        try {
          const response = await fetch(`http://localhost:${service.port}/health`);
          if (response.ok) {
            const data = await response.json();
            return {
              key: service.key,
              status: data.status === 'healthy' ? 'online' : 'degraded',
              uptime: data.uptime_seconds || 0
            };
          }
        } catch (error) {
          console.error(`${service.name} health check failed:`, error);
        }
        return {
          key: service.key,
          status: 'offline',
          uptime: 0
        };
      });

      const results = await Promise.all(healthPromises);

      const newHealth = {};
      results.forEach(result => {
        newHealth[result.key] = {
          status: result.status,
          uptime: result.uptime
        };
      });

      setSystemHealth(newHealth);
    };

    checkAllServices();
    const interval = setInterval(checkAllServices, 15000); // Every 15s
    return () => clearInterval(interval);
  }, []);

  // Simulate neural activity stream
  useEffect(() => {
    const activities = [
      { module: 'DOPAMINA', action: 'RPE: +0.45 → Learning rate increased', severity: 'success', icon: '🧬' },
      { module: 'SEROTONINA', action: 'Exploration rate: 0.15 → Exploitation mode', severity: 'info', icon: '🧬' },
      { module: 'ACETILCOLINA', action: 'Novelty detected → Attention gain boosted', severity: 'warning', icon: '🧬' },
      { module: 'NORADRENALINA', action: 'Threat level HIGH → Temperature lowered', severity: 'critical', icon: '🧬' },
      { module: 'MEMORY', action: 'Sleep cycle: 127 experiences consolidated', severity: 'success', icon: '💾' },
      { module: 'HSAS', action: 'Model-free action selected (low uncertainty)', severity: 'info', icon: '🎯' },
      { module: 'HSAS', action: 'New skill acquired: block_ip_advanced', severity: 'success', icon: '🎯' },
      { module: 'PLANNING', action: 'High-impact action approved: Policy change', severity: 'warning', icon: '🧠' },
      { module: 'IMMUNIS', action: 'Neutrophils activated → Pathogen eliminated', severity: 'success', icon: '🦠' },
      { module: 'IMMUNIS', action: 'Antibody produced: IgG targeting malware_xyz', severity: 'success', icon: '🦠' }
    ];

    const interval = setInterval(() => {
      if (Math.random() > 0.6) {
        const randomActivity = activities[Math.floor(Math.random() * activities.length)];
        const newActivity = {
          id: Date.now(),
          ...randomActivity,
          timestamp: new Date().toLocaleTimeString('pt-BR')
        };
        setNeuralActivity(prev => [newActivity, ...prev].slice(0, 100));
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const widgets = [
    { id: 'overview', name: 'OVERVIEW', icon: '🧠', description: 'System Overview' },
    { id: 'neuro', name: 'NEUROMODULAÇÃO', icon: '🧬', description: 'Dopamine, Serotonin, ACh, NE' },
    { id: 'memory', name: 'MEMÓRIA', icon: '💾', description: 'Consolidation Engine' },
    { id: 'hsas', name: 'SKILLS', icon: '🎯', description: 'Hybrid Skill Acquisition' },
    { id: 'planning', name: 'PLANEJAMENTO', icon: '📋', description: 'Strategic Planning' },
    { id: 'immunis', name: 'IMMUNIS', icon: '🦠', description: 'Immune System' },
    { id: 'cognition', name: 'COGNIÇÃO', icon: '🔮', description: 'Threat Prediction & Analysis' },
    { id: 'immune-enhance', name: 'IMMUNE++', icon: '🛡️', description: 'FP Suppression & LTM' },
    { id: 'distributed', name: 'DISTRIBUÍDO', icon: '🌐', description: 'Edge Topology & Metrics' }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'status-online';
      case 'degraded': return 'status-degraded';
      case 'offline': return 'status-offline';
      case 'checking': return 'status-checking';
      default: return 'status-unknown';
    }
  };

  const renderOverview = () => {
    const services = [
      { key: 'neuromodulation', name: 'Neuromodulation', icon: '🧬', port: 8001 },
      { key: 'memory_consolidation', name: 'Memory Consolidation', icon: '💾', port: 8002 },
      { key: 'hsas', name: 'HSAS', icon: '🎯', port: 8003 },
      { key: 'strategic_planning', name: 'Strategic Planning', icon: '📋', port: 8004 },
      { key: 'immunis', name: 'Immunis System', icon: '🦠', port: 8005 }
    ];

    const onlineCount = Object.values(systemHealth).filter(s => s.status === 'online').length;
    const overallHealth = (onlineCount / services.length) * 100;

    return (
      <div className="ai3-overview">
        {/* System Health Summary */}
        <div className="overview-header">
          <div className="health-gauge">
            <div className="gauge-container">
              <svg className="gauge-svg" viewBox="0 0 200 120">
                <path
                  className="gauge-background"
                  d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                  stroke="#1f2937"
                  strokeWidth="20"
                />
                <path
                  className="gauge-fill"
                  d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                  stroke={overallHealth > 80 ? '#10b981' : overallHealth > 50 ? '#f59e0b' : '#ef4444'}
                  strokeWidth="20"
                  strokeDasharray={`${(overallHealth / 100) * 251.2} 251.2`}
                  strokeLinecap="round"
                />
                <text x="100" y="90" className="gauge-text" textAnchor="middle" fontSize="32" fill="#fff">
                  {overallHealth.toFixed(0)}%
                </text>
                <text x="100" y="110" className="gauge-label" textAnchor="middle" fontSize="12" fill="#9ca3af">
                  SYSTEM HEALTH
                </text>
              </svg>
            </div>
          </div>

          <div className="overview-stats">
            <div className="stat-card">
              <div className="stat-value">{onlineCount}/{services.length}</div>
              <div className="stat-label">Services Online</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{neuralActivity.length}</div>
              <div className="stat-label">Neural Events</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">23,033</div>
              <div className="stat-label">Lines of Code</div>
            </div>
          </div>
        </div>

        {/* Services Grid */}
        <div className="services-grid">
          {services.map(service => {
            const health = systemHealth[service.key];
            return (
              <div key={service.key} className={`service-card ${getStatusColor(health.status)}`}>
                <div className="service-header">
                  <span className="service-icon">{service.icon}</span>
                  <div className="service-info">
                    <h3 className="service-name">{service.name}</h3>
                    <span className="service-port">Port {service.port}</span>
                  </div>
                  <span className={`status-indicator ${getStatusColor(health.status)}`}>
                    {health.status === 'checking' ? '⏳' : health.status === 'online' ? '✓' : '✗'}
                  </span>
                </div>
                <div className="service-body">
                  <div className="service-stat">
                    <span className="stat-label">Status:</span>
                    <span className={`stat-value ${getStatusColor(health.status)}`}>
                      {health.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="service-stat">
                    <span className="stat-label">Uptime:</span>
                    <span className="stat-value">
                      {health.uptime > 0 ? `${(health.uptime / 3600).toFixed(1)}h` : 'N/A'}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (service.key === 'neuromodulation') setSelectedWidget('neuro');
                    else if (service.key === 'memory_consolidation') setSelectedWidget('memory');
                    else if (service.key === 'hsas') setSelectedWidget('hsas');
                    else if (service.key === 'strategic_planning') setSelectedWidget('planning');
                    else if (service.key === 'immunis') setSelectedWidget('immunis');
                  }}
                  className="btn-service-details"
                  disabled={health.status === 'offline'}
                >
                  View Details →
                </button>
              </div>
            );
          })}
        </div>

        {/* Recent Neural Activity */}
        <div className="recent-activity">
          <h3 className="activity-title">🧠 Recent Neural Activity</h3>
          <div className="activity-list">
            {neuralActivity.slice(0, 10).map(activity => (
              <div key={activity.id} className={`activity-item activity-${activity.severity}`}>
                <span className="activity-icon">{activity.icon}</span>
                <span className="activity-time">{activity.timestamp}</span>
                <span className="activity-module">[{activity.module}]</span>
                <span className="activity-action">{activity.action}</span>
              </div>
            ))}
            {neuralActivity.length === 0 && (
              <div className="activity-empty">
                <span>⏳ Aguardando atividade neural...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderActiveWidget = () => {
    switch (selectedWidget) {
      case 'neuro':
        return <NeuromodulationWidget systemHealth={systemHealth.neuromodulation} />;
      case 'memory':
        return <MemoryConsolidationWidget systemHealth={systemHealth.memory_consolidation} />;
      case 'hsas':
        return <HSASWidget systemHealth={systemHealth.hsas} />;
      case 'planning':
        return <StrategicPlanningWidget systemHealth={systemHealth.strategic_planning} />;
      case 'immunis':
        return <ImmunisWidget systemHealth={systemHealth.immunis} />;
      case 'cognition':
        return <ThreatPredictionWidget />;
      case 'immune-enhance':
        return <ImmuneEnhancementWidget />;
      case 'distributed':
        return <DistributedTopologyWidget />;
      default:
        return renderOverview();
    }
  };

  return (
    <div className="maximus-ai3-panel">
      {/* Widget Navigation */}
      <div className="widget-navigation">
        {widgets.map(widget => (
          <button
            key={widget.id}
            onClick={() => setSelectedWidget(widget.id)}
            className={`widget-tab ${selectedWidget === widget.id ? 'widget-tab-active' : ''}`}
          >
            <span className="widget-icon">{widget.icon}</span>
            <div className="widget-info">
              <span className="widget-name">{widget.name}</span>
              <span className="widget-desc">{widget.description}</span>
            </div>
            {widget.id !== 'overview' && (
              <span className={`widget-status ${getStatusColor(systemHealth[
                widget.id === 'neuro' ? 'neuromodulation' :
                widget.id === 'memory' ? 'memory_consolidation' :
                widget.id === 'hsas' ? 'hsas' :
                widget.id === 'planning' ? 'strategic_planning' :
                widget.id === 'immunis' ? 'immunis' :
                widget.id === 'cognition' ? 'enhanced_cognition' :
                widget.id === 'immune-enhance' ? 'immune_enhancement' :
                widget.id === 'distributed' ? 'distributed_organism' :
                'immunis'
              ]?.status)}`}></span>
            )}
          </button>
        ))}
      </div>

      {/* Active Widget Content */}
      <div className="widget-content">
        {renderActiveWidget()}
      </div>
    </div>
  );
};

export default MaximusAI3Panel;

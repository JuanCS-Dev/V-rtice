/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MAXIMUS AI DASHBOARD - O Cérebro do Vértice
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dashboard cinematográfico para visualizar os componentes de AI do MAXIMUS:
 * - ORÁCULO: Self-improvement engine
 * - EUREKA: Deep malware analysis
 * - AI INSIGHTS: Unified intelligence view
 *
 * Design Philosophy: Cyberpunk meets Military Intelligence
 */

import React, { useState, useEffect } from 'react';
import { OraculoPanel } from './OraculoPanel';
import { EurekaPanel } from './EurekaPanel';
import { AIInsightsPanel } from './AIInsightsPanel';
import { MaximusAI3Panel } from './MaximusAI3Panel';
import { MaximusCore } from './MaximusCore';
import { WorkflowsPanel } from './WorkflowsPanel';
import TerminalEmulator from '../terminal/TerminalEmulator';
import { BackgroundEffect, EffectSelector } from './BackgroundEffects';
import './MaximusDashboard.css';

export const MaximusDashboard = ({ setCurrentView }) => {
  const [activePanel, setActivePanel] = useState('core'); // 'core', 'insights', 'ai3', 'oraculo', 'eureka', 'workflows', 'terminal'
  const [backgroundEffect, setBackgroundEffect] = useState('matrix'); // 'scanline', 'matrix', 'particles', 'none'
  const [aiStatus, setAiStatus] = useState({
    oraculo: { status: 'idle', lastRun: null, suggestions: 0 },
    eureka: { status: 'idle', lastAnalysis: null, threatsDetected: 0 },
    core: { status: 'online', uptime: '99.9%', reasoning: 'ready' }
  });
  const [currentTime, setCurrentTime] = useState(new Date());
  const [brainActivity, setBrainActivity] = useState([]); // AI activity stream

  // Debug log
  console.log('🧠 MAXIMUS Dashboard renderizando...', { backgroundEffect, activePanel });

  // Update clock
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Check MAXIMUS services health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('http://localhost:8099/health');
        if (response.ok) {
          const data = await response.json();
          setAiStatus(prev => ({
            ...prev,
            core: {
              status: data.status === 'healthy' ? 'online' : 'degraded',
              uptime: data.uptime_seconds ? `${(data.uptime_seconds / 3600).toFixed(1)}h` : prev.core.uptime,
              reasoning: data.services.maximus_core === 'external' ? 'ready' : 'offline'
            }
          }));
        }
      } catch (error) {
        console.error('MAXIMUS health check failed:', error);
        setAiStatus(prev => ({
          ...prev,
          core: { ...prev.core, status: 'offline' }
        }));
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Every 30s
    return () => clearInterval(interval);
  }, []);

  // Simulate AI brain activity (in production, this would be real-time WebSocket)
  useEffect(() => {
    const activities = [
      { type: 'ORÁCULO', action: 'Scanning codebase for improvements...', severity: 'info' },
      { type: 'EUREKA', action: 'Pattern detection: Analyzing file signatures', severity: 'info' },
      { type: 'CORE', action: 'Chain-of-thought reasoning initiated', severity: 'success' },
      { type: 'ADR', action: 'Playbook execution completed', severity: 'success' },
      { type: 'ORÁCULO', action: 'Suggestion generated: Security enhancement', severity: 'warning' },
      { type: 'EUREKA', action: 'IOC extracted: Suspicious domain detected', severity: 'critical' }
    ];

    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const randomActivity = activities[Math.floor(Math.random() * activities.length)];
        const newActivity = {
          id: Date.now(),
          ...randomActivity,
          timestamp: new Date().toLocaleTimeString('pt-BR')
        };
        setBrainActivity(prev => [newActivity, ...prev].slice(0, 50));
      }
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  const panels = [
    { id: 'core', name: 'AI CORE', icon: '🤖', description: 'Chat & Orchestration' },
    { id: 'workflows', name: 'WORKFLOWS', icon: '🔄', description: 'AI-Driven Automation' },
    { id: 'terminal', name: 'TERMINAL', icon: '⚡', description: 'Vertice CLI Interface' },
    { id: 'insights', name: 'AI INSIGHTS', icon: '🧠', description: 'Unified Intelligence View' },
    { id: 'ai3', name: 'MAXIMUS AI 3.0', icon: '🧬', description: 'Neural Architecture' },
    { id: 'oraculo', name: 'ORÁCULO', icon: '🔮', description: 'Self-Improvement Engine' },
    { id: 'eureka', name: 'EUREKA', icon: '🔬', description: 'Deep Malware Analysis' }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'text-green-400';
      case 'idle': return 'text-blue-400';
      case 'running': return 'text-purple-400 animate-pulse';
      case 'degraded': return 'text-yellow-400';
      case 'offline': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const renderActivePanel = () => {
    switch (activePanel) {
      case 'core':
        return <MaximusCore aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'workflows':
        return <WorkflowsPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'terminal':
        return (
          <div style={{ height: '100%', padding: '1rem' }}>
            <TerminalEmulator isFullscreen={false} />
          </div>
        );
      case 'ai3':
        return <MaximusAI3Panel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'oraculo':
        return <OraculoPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'eureka':
        return <EurekaPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'insights':
        return <AIInsightsPanel aiStatus={aiStatus} brainActivity={brainActivity} />;
      default:
        return <MaximusCore aiStatus={aiStatus} setAiStatus={setAiStatus} />;
    }
  };

  return (
    <div className="maximus-dashboard" style={{ minHeight: '100vh', width: '100%' }}>
      {/* Animated Background Grid */}
      <div className="maximus-grid-bg"></div>

      {/* Background Effect (Scanline/Matrix/Particles) */}
      <BackgroundEffect effectId={backgroundEffect} />

      {/* Effect Selector */}
      <EffectSelector
        currentEffect={backgroundEffect}
        onEffectChange={setBackgroundEffect}
      />

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* HEADER - Mission Control */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <header className="maximus-header">
        <div className="header-content">
          {/* Logo & Title */}
          <div className="header-left">
            <div className="maximus-logo">
              <div className="logo-icon">
                <span className="logo-brain">🧠</span>
                <div className="logo-pulse"></div>
              </div>
            </div>
            <div className="header-title-section">
              <h1 className="maximus-title">
                MAXIMUS AI
                <span className="title-version">v1.0.0</span>
              </h1>
              <p className="maximus-subtitle">Autonomous Intelligence Platform</p>
            </div>
          </div>

          {/* System Status Indicators */}
          <div className="header-center">
            <div className="status-indicators">
              <div className="status-indicator">
                <span className={`status-dot ${aiStatus.core.status === 'online' ? 'status-online' : 'status-offline'}`}></span>
                <div className="status-info">
                  <span className="status-label">CORE</span>
                  <span className={`status-value ${getStatusColor(aiStatus.core.status)}`}>
                    {aiStatus.core.status.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="status-indicator">
                <span className={`status-dot ${aiStatus.oraculo.status === 'running' ? 'status-running' : 'status-idle'}`}></span>
                <div className="status-info">
                  <span className="status-label">ORÁCULO</span>
                  <span className={`status-value ${getStatusColor(aiStatus.oraculo.status)}`}>
                    {aiStatus.oraculo.status.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="status-indicator">
                <span className={`status-dot ${aiStatus.eureka.status === 'running' ? 'status-running' : 'status-idle'}`}></span>
                <div className="status-info">
                  <span className="status-label">EUREKA</span>
                  <span className={`status-value ${getStatusColor(aiStatus.eureka.status)}`}>
                    {aiStatus.eureka.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Clock & Actions */}
          <div className="header-right">
            <div className="header-clock">
              <div className="clock-time">{currentTime.toLocaleTimeString('pt-BR')}</div>
              <div className="clock-date">{currentTime.toLocaleDateString('pt-BR')}</div>
            </div>
            <button
              onClick={() => setCurrentView('main')}
              className="btn-back-vertice"
            >
              <span>← VÉRTICE</span>
            </button>
          </div>
        </div>

        {/* Panel Navigation */}
        <div className="panel-navigation">
          {panels.map(panel => (
            <button
              key={panel.id}
              onClick={() => setActivePanel(panel.id)}
              className={`panel-tab ${activePanel === panel.id ? 'panel-tab-active' : ''}`}
            >
              <span className="panel-icon">{panel.icon}</span>
              <div className="panel-info">
                <span className="panel-name">{panel.name}</span>
                <span className="panel-desc">{panel.description}</span>
              </div>
            </button>
          ))}
        </div>
      </header>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* MAIN CONTENT - Active Panel */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <main className="maximus-main">
        {renderActivePanel()}
      </main>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* FOOTER - AI Activity Stream */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <footer className="maximus-footer">
        <div className="footer-header">
          <span className="footer-title">🧠 AI BRAIN ACTIVITY</span>
          <span className="footer-count">{brainActivity.length} eventos registrados</span>
        </div>
        <div className="activity-stream">
          {brainActivity.length === 0 ? (
            <div className="activity-empty">
              <span>⏳ Aguardando atividade da AI...</span>
            </div>
          ) : (
            brainActivity.slice(0, 5).map(activity => (
              <div key={activity.id} className={`activity-item activity-${activity.severity}`}>
                <span className="activity-time">{activity.timestamp}</span>
                <span className="activity-type">[{activity.type}]</span>
                <span className="activity-action">{activity.action}</span>
              </div>
            ))
          )}
        </div>
      </footer>

      {/* Classification Banner */}
      <div className="classification-banner">
        <span>🔒 CLASSIFICAÇÃO: RESTRITO</span>
        <span>|</span>
        <span>MAXIMUS AI PLATFORM</span>
        <span>|</span>
        <span>PROJETO VÉRTICE</span>
      </div>
    </div>
  );
};

export default MaximusDashboard;

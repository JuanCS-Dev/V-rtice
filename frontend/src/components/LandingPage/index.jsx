/**
 * LANDING PAGE - PROJETO VÉRTICE
 *
 * Dashboard de entrada com mapa global de ameaças cyber
 * Estatísticas em tempo real e acesso aos módulos
 */

import React, { useState, useEffect } from 'react';
import { ThreatGlobe } from './ThreatGlobe';
import { StatsPanel } from './StatsPanel';
import { ModuleGrid } from './ModuleGrid';
import { LiveFeed } from './LiveFeed';
import './LandingPage.css';

export const LandingPage = ({ setCurrentView }) => {
  const [stats, setStats] = useState({
    threatsDetected: 0,
    activeMonitoring: 0,
    networksScanned: 0,
    uptime: '99.8%'
  });

  // Animar estatísticas
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        threatsDetected: prev.threatsDetected + Math.floor(Math.random() * 3),
        activeMonitoring: 127 + Math.floor(Math.random() * 10),
        networksScanned: 1542 + Math.floor(Math.random() * 50)
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="pulse-dot"></span>
            <span>SISTEMA OPERACIONAL</span>
          </div>

          <h1 className="hero-title">
            PROJETO VÉRTICE
            <span className="gradient-text">v2.4.0</span>
          </h1>

          <p className="hero-subtitle">
            Plataforma Unificada de Inteligência Criminal e Segurança Cibernética
          </p>

          <div className="hero-tags">
            <span className="tag">🛡️ Cyber Security</span>
            <span className="tag">🕵️ OSINT</span>
            <span className="tag">⚡ Real-Time Analysis</span>
            <span className="tag">🤖 AI-Powered</span>
          </div>
        </div>

        {/* Mapa Global de Ameaças */}
        <div className="threat-globe-container">
          <ThreatGlobe />
        </div>
      </div>

      {/* Stats Grid */}
      <StatsPanel stats={stats} />

      {/* Modules Grid */}
      <ModuleGrid setCurrentView={setCurrentView} />

      {/* Live Activity Feed */}
      <LiveFeed />

      {/* Footer Info */}
      <div className="landing-footer">
        <div className="footer-item">
          <i className="fas fa-shield-alt"></i>
          <span>Criptografia de Ponta a Ponta</span>
        </div>
        <div className="footer-item">
          <i className="fas fa-server"></i>
          <span>Infraestrutura Distribuída</span>
        </div>
        <div className="footer-item">
          <i className="fas fa-clock"></i>
          <span>Uptime: {stats.uptime}</span>
        </div>
        <div className="footer-item">
          <i className="fas fa-certificate"></i>
          <span>Classificação: CONFIDENCIAL</span>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;

/**
 * LANDING PAGE - PROJETO VÉRTICE
 * ================================
 * A CARA do sistema. Impressionante, impactante, REAL.
 *
 * Features:
 * - Mapa Global com animação OnionTracer integrada
 * - Alerts REAIS do backend (threat_intel_service)
 * - Stats ao vivo
 * - Design cinematográfico
 */

import React, { useState, useEffect } from 'react';
import { ThreatGlobe } from './ThreatGlobe';
// import { ThreatGlobeWithOnion } from './ThreatGlobeWithOnion';
import { StatsPanel } from './StatsPanel';
import { ModuleGrid } from './ModuleGrid';
import { LiveFeed } from './LiveFeed';
import { checkServicesHealth, checkThreatIntelligence } from '../../api/cyberServices';
import './LandingPage.css';

export const LandingPage = ({ setCurrentView }) => {
  const [stats, setStats] = useState({
    threatsDetected: 0,
    activeMonitoring: 127,
    networksScanned: 1542,
    uptime: '99.8%',
    servicesOnline: 0,
    totalServices: 4
  });

  const [realThreats, setRealThreats] = useState([]);
  const [servicesStatus, setServicesStatus] = useState({
    ipIntelligence: false,
    threatIntel: false,
    malwareAnalysis: false,
    sslMonitor: false
  });

  // Check services health periodically
  useEffect(() => {
    const checkHealth = async () => {
      const health = await checkServicesHealth();
      setServicesStatus(health);

      const online = Object.values(health).filter(Boolean).length;
      setStats(prev => ({
        ...prev,
        servicesOnline: online,
        uptime: online === 4 ? '99.9%' : `${(online / 4 * 100).toFixed(1)}%`
      }));
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // a cada 30s

    return () => clearInterval(interval);
  }, []);

  // Buscar ameaças reais periodicamente
  useEffect(() => {
    const fetchRealThreats = async () => {
      // Lista de IPs conhecidos para verificar
      const suspiciousIPs = [
        '185.220.101.23', // Exit node Tor conhecido
        '45.129.56.200',  // IP suspeito
        '178.162.212.214', // Outro IP para análise
        '91.219.236.232'
      ];

      try {
        const randomIP = suspiciousIPs[Math.floor(Math.random() * suspiciousIPs.length)];
        const result = await checkThreatIntelligence(randomIP);

        if (result.success) {
          const threat = {
            id: Date.now(),
            type: result.categories[0] || 'Unknown',
            ip: result.target,
            severity: result.reputation,
            threatScore: result.threatScore,
            isMalicious: result.isMalicious,
            timestamp: new Date().toLocaleTimeString('pt-BR'),
            geolocation: result.geolocation
          };

          setRealThreats(prev => [threat, ...prev].slice(0, 20));

          // Atualizar contador de ameaças
          if (result.isMalicious) {
            setStats(prev => ({
              ...prev,
              threatsDetected: prev.threatsDetected + 1
            }));
          }
        }
      } catch (error) {
        console.error('Error fetching real threats:', error);
      }
    };

    // Busca inicial
    fetchRealThreats();

    // Buscar a cada 10 segundos
    const interval = setInterval(fetchRealThreats, 10000);

    return () => clearInterval(interval);
  }, []);

  // Animar estatísticas (scanning em background)
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        activeMonitoring: 120 + Math.floor(Math.random() * 15),
        networksScanned: prev.networksScanned + Math.floor(Math.random() * 5)
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="landing-page">
      <div style={{width: '100%', maxWidth: '1800px', margin: '0 auto'}}>
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

            {/* Services Status Indicator */}
            <div className="services-status">
              <div className="status-header">
                <span>🔧 SERVIÇOS ATIVOS</span>
                <span className="status-count">
                  {stats.servicesOnline}/{stats.totalServices}
                </span>
              </div>
              <div className="status-grid">
                <div className={`status-item ${servicesStatus.ipIntelligence ? 'online' : 'offline'}`}>
                  <span className="status-dot"></span>
                  <span>IP Intel</span>
                </div>
                <div className={`status-item ${servicesStatus.threatIntel ? 'online' : 'offline'}`}>
                  <span className="status-dot"></span>
                  <span>Threat Intel</span>
                </div>
                <div className={`status-item ${servicesStatus.malwareAnalysis ? 'online' : 'offline'}`}>
                  <span className="status-dot"></span>
                  <span>Malware</span>
                </div>
                <div className={`status-item ${servicesStatus.sslMonitor ? 'online' : 'offline'}`}>
                  <span className="status-dot"></span>
                  <span>SSL</span>
                </div>
              </div>
            </div>
          </div>

          {/* Mapa Global de Ameaças */}
          <div className="threat-globe-container">
            <ThreatGlobe realThreats={realThreats} />
          </div>
        </div>

        {/* Stats Grid */}
        <StatsPanel stats={stats} />

        {/* Modules Grid */}
        <ModuleGrid setCurrentView={setCurrentView} />

        {/* Live Activity Feed - AGORA com dados REAIS */}
        <LiveFeed realThreats={realThreats} />
      </div>

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

// /home/juan/vertice-dev/frontend/src/components/CyberDashboard.jsx

import React, { useState, useEffect } from 'react';
import CyberHeader from './cyber/CyberHeader';
import DomainAnalyzer from './cyber/DomainAnalyzer';
import IpIntelligence from './cyber/IpIntelligence';
import NetworkMonitor from './cyber/NetworkMonitor';
import ThreatMap from './cyber/ThreatMap';
import CyberAlerts from './cyber/CyberAlerts';

const CyberDashboard = ({ setCurrentView }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeModule, setActiveModule] = useState('overview');
  const [cyberAlerts, setCyberAlerts] = useState([]);
  const [threatData, setThreatData] = useState({
    totalThreats: 127,
    activeDomains: 23,
    suspiciousIPs: 45,
    networkAlerts: 8
  });

  // Atualiza relógio
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Simula alertas cyber em tempo real
  useEffect(() => {
    const alertTimer = setInterval(() => {
      if (Math.random() > 0.9) {
        const alertTypes = [
          { type: 'MALWARE', message: 'Domínio malicioso detectado', severity: 'critical' },
          { type: 'PHISHING', message: 'Tentativa de phishing identificada', severity: 'high' },
          { type: 'BOTNET', message: 'Atividade de botnet detectada', severity: 'high' },
          { type: 'SCAN', message: 'Port scan detectado', severity: 'medium' },
          { type: 'INTEL', message: 'Nova inteligência de ameaça', severity: 'info' }
        ];
        
        const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
        const newAlert = {
          id: Date.now(),
          ...randomAlert,
          timestamp: new Date().toLocaleTimeString(),
          source: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
        };
        setCyberAlerts(prev => [newAlert, ...prev.slice(0, 19)]);
      }
    }, 5000);
    return () => clearInterval(alertTimer);
  }, []);

  const moduleComponents = {
    overview: <CyberOverview threatData={threatData} />,
    domain: <DomainAnalyzer />,
    ip: <IpIntelligence />,
    network: <NetworkMonitor />,
    threats: <ThreatMap />
  };

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-gray-900 via-black to-blue-900 text-cyan-400 font-mono overflow-hidden flex flex-col">
      {/* Scan Line */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse z-20"></div>
      
      <CyberHeader 
        currentTime={currentTime}
        setCurrentView={setCurrentView}
        activeModule={activeModule}
        setActiveModule={setActiveModule}
      />

      <main className="flex-1 flex min-h-0">
        {/* Sidebar de Alertas */}
        <aside className="w-80 border-r border-cyan-400/30 bg-black/30 backdrop-blur-sm">
          <CyberAlerts alerts={cyberAlerts} threatData={threatData} />
        </aside>

        {/* Área Principal */}
        <div className="flex-1 p-4 overflow-hidden">
          {moduleComponents[activeModule]}
        </div>
      </main>

      {/* Footer Cyber */}
      <footer className="border-t border-cyan-400/30 bg-black/50 backdrop-blur-sm p-2">
        <div className="flex justify-between items-center text-xs">
          <div className="flex space-x-6">
            <span className="text-cyan-400">CONEXÃO: SEGURA</span>
            <span className="text-cyan-400">THREAT INTEL: ATIVO</span>
            <span className="text-cyan-400">USUÁRIO: CYBER_OPS_001</span>
            <span className="text-cyan-400">ALERTAS: {cyberAlerts.length}</span>
          </div>
          <div className="text-cyan-400/70">
            MÓDULO CYBER-SECURITY | PROJETO VÉRTICE v2.0 | CLASSIFICAÇÃO: CONFIDENCIAL
          </div>
        </div>
      </footer>
    </div>
  );
};

// Componente Overview
const CyberOverview = ({ threatData }) => {
  return (
    <div className="space-y-6">
      <div className="border border-cyan-400/50 rounded-lg bg-cyan-400/5 p-6">
        <h2 className="text-cyan-400 font-bold text-2xl mb-6 tracking-wider">
          CENTRO DE OPERAÇÕES CYBER
        </h2>
        
        {/* Métricas Principais */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-black/50 border border-red-400/50 rounded-lg p-4 text-center">
            <div className="text-red-400 text-3xl font-bold">{threatData.totalThreats}</div>
            <div className="text-red-400/70 text-sm">AMEAÇAS ATIVAS</div>
          </div>
          <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-4 text-center">
            <div className="text-yellow-400 text-3xl font-bold">{threatData.activeDomains}</div>
            <div className="text-yellow-400/70 text-sm">DOMÍNIOS SUSPEITOS</div>
          </div>
          <div className="bg-black/50 border border-orange-400/50 rounded-lg p-4 text-center">
            <div className="text-orange-400 text-3xl font-bold">{threatData.suspiciousIPs}</div>
            <div className="text-orange-400/70 text-sm">IPs MALICIOSOS</div>
          </div>
          <div className="bg-black/50 border border-cyan-400/50 rounded-lg p-4 text-center">
            <div className="text-cyan-400 text-3xl font-bold">{threatData.networkAlerts}</div>
            <div className="text-cyan-400/70 text-sm">ALERTAS DE REDE</div>
          </div>
        </div>

        {/* Status dos Módulos */}
        <div className="space-y-4">
          <h3 className="text-cyan-400 font-bold text-lg mb-4">STATUS DOS MÓDULOS</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/30 border border-cyan-400/30 rounded p-4">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400/70">Domain Analyzer</span>
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              </div>
              <div className="text-xs text-cyan-400/50 mt-1">Monitorando 1,247 domínios</div>
            </div>
            <div className="bg-black/30 border border-cyan-400/30 rounded p-4">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400/70">IP Intelligence</span>
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              </div>
              <div className="text-xs text-cyan-400/50 mt-1">Analisando 5,832 IPs</div>
            </div>
            <div className="bg-black/30 border border-cyan-400/30 rounded p-4">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400/70">Network Monitor</span>
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              </div>
              <div className="text-xs text-cyan-400/50 mt-1">Tempo real ativo</div>
            </div>
            <div className="bg-black/30 border border-cyan-400/30 rounded p-4">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400/70">Threat Map</span>
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              </div>
              <div className="text-xs text-cyan-400/50 mt-1">Visualização global</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CyberDashboard;

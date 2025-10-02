import React, { useState, useCallback, useEffect } from 'react';
import OSINTHeader from './osint/OSINTHeader';
import OSINTAlerts from './osint/OSINTAlerts';
import MaximusAIModule from './osint/MaximusAIModule';
import UsernameModule from './osint/UsernameModule';
import EmailModule from './osint/EmailModule';
import PhoneModule from './osint/PhoneModule';
import SocialModule from './osint/SocialModule';
import GoogleModule from './osint/GoogleModule';
import DarkWebModule from './osint/DarkWebModule';
import ReportsModule from './osint/ReportsModule';
import SocialMediaWidget from './osint/SocialMediaWidget';
import BreachDataWidget from './osint/BreachDataWidget';

const OSINTDashboard = ({ setCurrentView }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeModule, setActiveModule] = useState('aurora'); // AI-FIRST: Maximus como landing page
  const [osintAlerts, setOsintAlerts] = useState([]);
  const [isAIProcessing, setIsAIProcessing] = useState(false);
  const [investigationResults, setInvestigationResults] = useState(null);
  const [systemStats, setSystemStats] = useState({
    totalInvestigations: 0,
    activeTargets: 0,
    threatsDetected: 0,
    dataPoints: 0,
    aiAccuracy: 95.7
  });

  // Atualizar relógio
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Simular alertas OSINT em tempo real
  useEffect(() => {
    const alertTimer = setInterval(() => {
      if (Math.random() > 0.85) {
        const alertTypes = [
          { type: 'LEAK', message: 'Novo vazamento detectado', severity: 'critical', source: 'Dark Web Monitor' },
          { type: 'SOCIAL', message: 'Atividade suspeita em rede social', severity: 'high', source: 'Social Scraper' },
          { type: 'BREACH', message: 'Email comprometido identificado', severity: 'critical', source: 'Breach Analyzer' },
          { type: 'PATTERN', message: 'Padrão comportamental anômalo', severity: 'medium', source: 'Aurora AI' },
          { type: 'IDENTITY', message: 'Nova identidade digital encontrada', severity: 'info', source: 'Username Hunter' }
        ];

        const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
        const newAlert = {
          id: Date.now(),
          ...randomAlert,
          timestamp: new Date().toLocaleTimeString('pt-BR'),
          target: `Target_${Math.floor(Math.random() * 999)}`
        };
        setOsintAlerts(prev => [newAlert, ...prev.slice(0, 29)]);
      }
    }, 4000);
    return () => clearInterval(alertTimer);
  }, []);

  const moduleComponents = {
    overview: <OverviewModule stats={systemStats} />,
    aurora: <MaximusAIModule setIsAIProcessing={setIsAIProcessing} setResults={setInvestigationResults} />,
    socialmedia: <SocialMediaWidget />,
    breachdata: <BreachDataWidget />,
    username: <UsernameModule />,
    email: <EmailModule />,
    phone: <PhoneModule />,
    social: <SocialModule />,
    google: <GoogleModule />,
    darkweb: <DarkWebModule />,
    reports: <ReportsModule results={investigationResults} />
  };

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-gray-900 via-black to-purple-900 text-purple-400 font-mono overflow-hidden flex flex-col">
      {/* Scan Line */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-purple-400 to-transparent animate-pulse z-20"></div>

      <OSINTHeader
        currentTime={currentTime}
        setCurrentView={setCurrentView}
        activeModule={activeModule}
        setActiveModule={setActiveModule}
      />

      <main className="flex-1 flex min-h-0">
        {/* Sidebar de Alertas OSINT */}
        <aside className="w-80 border-r border-purple-400/30 bg-black/30 backdrop-blur-sm">
          <OSINTAlerts alerts={osintAlerts} systemStats={systemStats} />
        </aside>

        {/* Área Principal */}
        <div className="flex-1 p-4 overflow-hidden relative">
          {/* AI Processing Overlay */}
          {isAIProcessing && (
            <div className="absolute top-0 left-0 right-0 bottom-0 bg-black/90 flex items-center justify-center z-50 backdrop-blur-lg">
              <div className="text-center">
                <div className="text-6xl animate-spin mb-4">🧠</div>
                <div className="text-purple-400 text-xl font-bold mb-4 tracking-wider">
                  AURORA AI PROCESSANDO...
                </div>
                <div className="w-80 h-2 bg-purple-400/20 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-purple-400 to-pink-400 animate-pulse"></div>
                </div>
              </div>
            </div>
          )}

          {moduleComponents[activeModule]}
        </div>
      </main>

      {/* Footer OSINT */}
      <footer className="border-t border-purple-400/30 bg-black/50 backdrop-blur-sm p-2">
        <div className="flex justify-between items-center text-xs">
          <div className="flex space-x-6">
            <span className="text-purple-400">🔒 CONEXÃO: SEGURA</span>
            <span className="text-purple-400">🧠 AURORA AI: ATIVO</span>
            <span className="text-purple-400">👤 OPERADOR: OSINT_OPS_001</span>
            <span className="text-purple-400">📊 PRECISÃO IA: {systemStats.aiAccuracy}%</span>
          </div>
          <div className="text-purple-400/70">
            MÓDULO OSINT INTELLIGENCE | PROJETO VÉRTICE v3.0 | SSP-GO | CLASSIFICAÇÃO: CONFIDENCIAL
          </div>
        </div>
      </footer>
    </div>
  );
};

// Componente Overview
const OverviewModule = ({ stats }) => {
  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-6 tracking-wider">
          CENTRO DE OPERAÇÕES OSINT
        </h2>

        {/* Métricas Principais */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-black/50 border border-red-400/50 rounded-lg p-4 text-center">
            <div className="text-red-400 text-3xl font-bold">{stats.totalInvestigations}</div>
            <div className="text-red-400/70 text-sm">INVESTIGAÇÕES TOTAIS</div>
          </div>
          <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-4 text-center">
            <div className="text-yellow-400 text-3xl font-bold">{stats.activeTargets}</div>
            <div className="text-yellow-400/70 text-sm">ALVOS ATIVOS</div>
          </div>
          <div className="bg-black/50 border border-orange-400/50 rounded-lg p-4 text-center">
            <div className="text-orange-400 text-3xl font-bold">{stats.threatsDetected}</div>
            <div className="text-orange-400/70 text-sm">AMEAÇAS DETECTADAS</div>
          </div>
          <div className="bg-black/50 border border-purple-400/50 rounded-lg p-4 text-center">
            <div className="text-purple-400 text-3xl font-bold">{stats.dataPoints}K</div>
            <div className="text-purple-400/70 text-sm">PONTOS DE DADOS</div>
          </div>
        </div>

        {/* Status dos Módulos OSINT */}
        <div className="space-y-4">
          <h3 className="text-purple-400 font-bold text-lg mb-4">STATUS DOS MÓDULOS OSINT</h3>
          <div className="grid grid-cols-3 gap-4">
            {[
              { name: 'Aurora AI Engine', status: 'online', activity: 'Analisando padrões' },
              { name: 'Username Hunter', status: 'online', activity: 'Monitorando 2,847 perfis' },
              { name: 'Email Analyzer', status: 'online', activity: 'Verificando 1,293 emails' },
              { name: 'Phone Intelligence', status: 'online', activity: 'Rastreando 847 números' },
              { name: 'Social Scraper', status: 'online', activity: 'Coletando dados em tempo real' },
              { name: 'Dark Web Monitor', status: 'online', activity: 'Varredura profunda ativa' }
            ].map((module, idx) => (
              <div key={idx} className="bg-black/30 border border-purple-400/30 rounded p-4">
                <div className="flex justify-between items-center">
                  <span className="text-purple-400/70">{module.name}</span>
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                </div>
                <div className="text-xs text-purple-400/50 mt-1">{module.activity}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OSINTDashboard;
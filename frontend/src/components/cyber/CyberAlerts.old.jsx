// /home/juan/vertice-dev/frontend/src/components/cyber/CyberAlerts.jsx

import React from 'react';

const CyberAlerts = ({ alerts, threatData }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'border-red-400 bg-red-400/10 text-red-400';
      case 'high': return 'border-orange-400 bg-orange-400/10 text-orange-400';
      case 'medium': return 'border-yellow-400 bg-yellow-400/10 text-yellow-400';
      case 'info': return 'border-cyan-400 bg-cyan-400/10 text-cyan-400';
      default: return 'border-gray-400 bg-gray-400/10 text-gray-400';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '🔍';
      case 'info': return 'ℹ️';
      default: return '📋';
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Status do Sistema Cyber */}
      <div className="p-4 border-b border-cyan-400/30">
        <h3 className="text-cyan-400 font-bold mb-3 tracking-wide">STATUS CYBER OPS</h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-cyan-400/70">THREAT INTEL</span>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-cyan-400/70">APIs ATIVAS</span>
            <span className="text-cyan-400">7/7</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-cyan-400/70">FEEDS ATIVOS</span>
            <span className="text-cyan-400">12</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-cyan-400/70">LATÊNCIA</span>
            <span className="text-cyan-400">89ms</span>
          </div>
        </div>
      </div>

      {/* Métricas Rápidas */}
      <div className="p-4 border-b border-cyan-400/30">
        <h3 className="text-cyan-400 font-bold mb-3 tracking-wide">MÉTRICAS EM TEMPO REAL</h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-red-400/20 border border-red-400/50 rounded p-2 text-center">
            <div className="text-red-400 font-bold text-lg">{threatData.totalThreats}</div>
            <div className="text-red-400/70">AMEAÇAS</div>
          </div>
          <div className="bg-yellow-400/20 border border-yellow-400/50 rounded p-2 text-center">
            <div className="text-yellow-400 font-bold text-lg">{threatData.activeDomains}</div>
            <div className="text-yellow-400/70">DOMÍNIOS</div>
          </div>
          <div className="bg-orange-400/20 border border-orange-400/50 rounded p-2 text-center">
            <div className="text-orange-400 font-bold text-lg">{threatData.suspiciousIPs}</div>
            <div className="text-orange-400/70">IPS</div>
          </div>
          <div className="bg-cyan-400/20 border border-cyan-400/50 rounded p-2 text-center">
            <div className="text-cyan-400 font-bold text-lg">{threatData.networkAlerts}</div>
            <div className="text-cyan-400/70">ALERTAS</div>
          </div>
        </div>
      </div>

      {/* Stream de Alertas */}
      <div className="flex-1 p-4 overflow-hidden">
        <h3 className="text-cyan-400 font-bold mb-3 tracking-wide">ALERTAS EM TEMPO REAL</h3>
        <div className="space-y-2 max-h-full overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-cyan-400/50 text-xs text-center py-8">
              <div className="text-4xl mb-2">🛡️</div>
              <p>Sistema monitorando...</p>
              <p>Aguardando ameaças...</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div 
                key={alert.id}
                className={`p-3 rounded border-l-4 ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex justify-between items-start mb-1">
                  <div className="flex items-center space-x-2">
                    <span>{getSeverityIcon(alert.severity)}</span>
                    <span className="text-xs font-semibold">{alert.type}</span>
                  </div>
                  <span className="text-xs opacity-70">{alert.timestamp}</span>
                </div>
                <p className="text-xs mb-2">{alert.message}</p>
                {alert.source && (
                  <div className="text-xs opacity-60 font-mono">
                    Origem: {alert.source}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Actions Rápidas */}
      <div className="p-4 border-t border-cyan-400/30 space-y-2">
        <h4 className="text-cyan-400 font-bold text-sm mb-2">AÇÕES RÁPIDAS</h4>
        <button className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white font-bold py-2 px-3 rounded text-xs hover:from-red-500 hover:to-red-600 transition-all">
          🚨 ALERTA GERAL
        </button>
        <button className="w-full bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-2 px-3 rounded text-xs hover:from-orange-500 hover:to-orange-600 transition-all">
          🔍 SCAN EMERGENCIAL
        </button>
        <button className="w-full bg-gradient-to-r from-cyan-600 to-cyan-700 text-white font-bold py-2 px-3 rounded text-xs hover:from-cyan-500 hover:to-cyan-600 transition-all">
          📊 RELATÓRIO SITUACIONAL
        </button>
      </div>
    </div>
  );
};

export default CyberAlerts;

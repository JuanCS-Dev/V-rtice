import React from 'react';

const OSINTAlerts = ({ alerts, systemStats }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'border-red-400 bg-red-400/10 text-red-400';
      case 'high': return 'border-orange-400 bg-orange-400/10 text-orange-400';
      case 'medium': return 'border-yellow-400 bg-yellow-400/10 text-yellow-400';
      case 'info': return 'border-purple-400 bg-purple-400/10 text-purple-400';
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
      {/* Status do Sistema OSINT */}
      <div className="p-4 border-b border-purple-400/30">
        <h3 className="text-purple-400 font-bold mb-3 tracking-wide">STATUS OSINT OPS</h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-purple-400/70">AURORA AI</span>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-purple-400/70">MÓDULOS ATIVOS</span>
            <span className="text-purple-400">6/6</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-purple-400/70">PRECISÃO IA</span>
            <span className="text-purple-400">{systemStats?.aiAccuracy}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-purple-400/70">LATÊNCIA</span>
            <span className="text-purple-400">142ms</span>
          </div>
        </div>
      </div>

      {/* Métricas Rápidas */}
      <div className="p-4 border-b border-purple-400/30">
        <h3 className="text-purple-400 font-bold mb-3 tracking-wide">MÉTRICAS EM TEMPO REAL</h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-red-400/20 border border-red-400/50 rounded p-2 text-center">
            <div className="text-red-400 font-bold text-lg">{systemStats?.totalInvestigations || 0}</div>
            <div className="text-red-400/70">INVESTIG.</div>
          </div>
          <div className="bg-yellow-400/20 border border-yellow-400/50 rounded p-2 text-center">
            <div className="text-yellow-400 font-bold text-lg">{systemStats?.activeTargets || 0}</div>
            <div className="text-yellow-400/70">ALVOS</div>
          </div>
          <div className="bg-orange-400/20 border border-orange-400/50 rounded p-2 text-center">
            <div className="text-orange-400 font-bold text-lg">{systemStats?.threatsDetected || 0}</div>
            <div className="text-orange-400/70">AMEAÇAS</div>
          </div>
          <div className="bg-purple-400/20 border border-purple-400/50 rounded p-2 text-center">
            <div className="text-purple-400 font-bold text-lg">{systemStats?.dataPoints || 0}K</div>
            <div className="text-purple-400/70">DADOS</div>
          </div>
        </div>
      </div>

      {/* Stream de Alertas OSINT */}
      <div className="flex-1 p-4 overflow-hidden">
        <h3 className="text-purple-400 font-bold mb-3 tracking-wide">🚨 OSINT ALERTS</h3>
        <div className="space-y-2 max-h-full overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-purple-400/50 text-xs text-center py-8">
              <div className="text-4xl mb-2">🔍</div>
              <p>Sistema operando normalmente</p>
              <p>Aguardando eventos OSINT...</p>
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
                <div className="flex justify-between text-xs opacity-60 font-mono">
                  {alert.target && (
                    <span>🎯 {alert.target}</span>
                  )}
                  {alert.source && (
                    <span>📡 {alert.source}</span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Actions Rápidas OSINT */}
      <div className="p-4 border-t border-purple-400/30 space-y-2">
        <h4 className="text-purple-400 font-bold text-sm mb-2">AÇÕES RÁPIDAS</h4>
        <button className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-bold py-2 px-3 rounded text-xs hover:from-purple-500 hover:to-purple-600 transition-all">
          🧠 AURORA SCAN
        </button>
        <button className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold py-2 px-3 rounded text-xs hover:from-blue-500 hover:to-blue-600 transition-all">
          🔍 BUSCA RÁPIDA
        </button>
        <button className="w-full bg-gradient-to-r from-indigo-600 to-indigo-700 text-white font-bold py-2 px-3 rounded text-xs hover:from-indigo-500 hover:to-indigo-600 transition-all">
          📊 RELATÓRIO OSINT
        </button>
      </div>
    </div>
  );
};

export default OSINTAlerts;
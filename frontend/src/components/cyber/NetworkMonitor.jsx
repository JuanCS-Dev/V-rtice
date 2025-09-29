// /home/juan/vertice-dev/frontend/src/components/cyber/NetworkMonitor.jsx

import React, { useState, useEffect } from 'react';

const NetworkMonitor = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [networkEvents, setNetworkEvents] = useState([]);
  const [realTimeData, setRealTimeData] = useState(null);
  const [statistics, setStatistics] = useState({
    connectionsToday: 0,
    portScansDetected: 0,
    suspiciousIPs: 0,
    blockedAttempts: 0
  });

  // Simula eventos de rede em tempo real
  useEffect(() => {
    if (!isMonitoring) return;

    const eventInterval = setInterval(() => {
      const eventTypes = [
        { type: 'CONNECTION', severity: 'info', action: 'Nova conexão estabelecida' },
        { type: 'PORT_SCAN', severity: 'high', action: 'Varredura de portas detectada' },
        { type: 'SYN_FLOOD', severity: 'critical', action: 'Possível ataque SYN flood' },
        { type: 'BLOCKED', severity: 'medium', action: 'Conexão suspeita bloqueada' },
        { type: 'FIRST_SEEN', severity: 'info', action: 'Primeiro contato de IP' }
      ];

      if (Math.random() > 0.3) {
        const randomEvent = eventTypes[Math.floor(Math.random() * eventTypes.length)];
        const newEvent = {
          id: Date.now(),
          ...randomEvent,
          source_ip: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
          destination_port: Math.floor(Math.random() * 65535),
          timestamp: new Date().toLocaleTimeString(),
          details: `Protocolo: TCP, Bytes: ${Math.floor(Math.random() * 10000)}`
        };

        setNetworkEvents(prev => [newEvent, ...prev.slice(0, 99)]);
        
        // Atualiza estatísticas
        setStatistics(prev => ({
          ...prev,
          connectionsToday: prev.connectionsToday + 1,
          portScansDetected: randomEvent.type === 'PORT_SCAN' ? prev.portScansDetected + 1 : prev.portScansDetected,
          suspiciousIPs: randomEvent.severity === 'high' || randomEvent.severity === 'critical' ? prev.suspiciousIPs + 1 : prev.suspiciousIPs,
          blockedAttempts: randomEvent.type === 'BLOCKED' ? prev.blockedAttempts + 1 : prev.blockedAttempts
        }));
      }
    }, 2000);

    return () => clearInterval(eventInterval);
  }, [isMonitoring]);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'border-red-400 bg-red-400/10 text-red-400';
      case 'high': return 'border-orange-400 bg-orange-400/10 text-orange-400';
      case 'medium': return 'border-yellow-400 bg-yellow-400/10 text-yellow-400';
      case 'info': return 'border-cyan-400 bg-cyan-400/10 text-cyan-400';
      default: return 'border-gray-400 bg-gray-400/10 text-gray-400';
    }
  };

  // Carrega dados reais do backend
  const fetchNetworkData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/network/monitor');
      const data = await response.json();
      if (data.success) {
        setRealTimeData(data.data);
        // Atualiza estatísticas com dados reais
        setStatistics(prev => ({
          ...prev,
          connectionsToday: data.data.active_connections?.length || 0,
          portScansDetected: data.data.suspicious_activity?.port_scans || 0,
          suspiciousIPs: data.data.suspicious_activity?.suspicious_ips || 0,
          blockedAttempts: data.data.security_events?.blocked_attempts || 0
        }));
      }
    } catch (error) {
      console.error('Erro ao carregar dados de rede:', error);
    }
  };

  // Busca dados do backend quando o monitoramento está ativo
  useEffect(() => {
    if (isMonitoring) {
      fetchNetworkData();
      const interval = setInterval(fetchNetworkData, 10000); // Atualiza a cada 10 segundos
      return () => clearInterval(interval);
    }
  }, [isMonitoring]);

  const toggleMonitoring = () => {
    setIsMonitoring(!isMonitoring);
    if (!isMonitoring) {
      setNetworkEvents([]);
      setRealTimeData(null);
      setStatistics({
        connectionsToday: 0,
        portScansDetected: 0,
        suspiciousIPs: 0,
        blockedAttempts: 0
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header do Módulo */}
      <div className="border border-cyan-400/50 rounded-lg bg-cyan-400/5 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-cyan-400 font-bold text-2xl tracking-wider">
              NETWORK MONITORING CENTER
            </h2>
            <p className="text-cyan-400/70 mt-1">Monitoramento de tráfego de rede em tempo real</p>
          </div>
          
          <button
            onClick={toggleMonitoring}
            className={`px-6 py-3 rounded-lg font-bold tracking-wider transition-all duration-300 ${
              isMonitoring 
                ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white'
                : 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-black'
            }`}
          >
            {isMonitoring ? 'PARAR MONITORAMENTO' : 'INICIAR MONITORAMENTO'}
          </button>
        </div>

        {/* Estatísticas em Tempo Real */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-black/50 border border-cyan-400/50 rounded-lg p-4 text-center">
            <div className="text-cyan-400 text-2xl font-bold">{statistics.connectionsToday}</div>
            <div className="text-cyan-400/70 text-sm">CONEXÕES HOJE</div>
          </div>
          <div className="bg-black/50 border border-orange-400/50 rounded-lg p-4 text-center">
            <div className="text-orange-400 text-2xl font-bold">{statistics.portScansDetected}</div>
            <div className="text-orange-400/70 text-sm">PORT SCANS</div>
          </div>
          <div className="bg-black/50 border border-red-400/50 rounded-lg p-4 text-center">
            <div className="text-red-400 text-2xl font-bold">{statistics.suspiciousIPs}</div>
            <div className="text-red-400/70 text-sm">IPS SUSPEITOS</div>
          </div>
          <div className="bg-black/50 border border-yellow-400/50 rounded-lg p-4 text-center">
            <div className="text-yellow-400 text-2xl font-bold">{statistics.blockedAttempts}</div>
            <div className="text-yellow-400/70 text-sm">BLOQUEADOS</div>
          </div>
        </div>
      </div>

      {/* Stream de Eventos */}
      <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-cyan-400 font-bold text-lg">STREAM DE EVENTOS DE REDE</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isMonitoring ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
            <span className="text-cyan-400/70 text-sm">
              {isMonitoring ? 'MONITORAMENTO ATIVO' : 'MONITORAMENTO INATIVO'}
            </span>
          </div>
        </div>

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {networkEvents.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">📡</div>
              <h3 className="text-cyan-400 text-xl mb-2">
                {isMonitoring ? 'AGUARDANDO EVENTOS...' : 'NETWORK MONITOR READY'}
              </h3>
              <p className="text-cyan-400/70">
                {isMonitoring ? 'Escutando tráfego de rede...' : 'Clique em "INICIAR MONITORAMENTO" para começar'}
              </p>
            </div>
          ) : (
            networkEvents.map((event) => (
              <div 
                key={event.id}
                className={`p-3 rounded border-l-4 ${getSeverityColor(event.severity)}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold px-2 py-1 rounded bg-black/50">
                      {event.type}
                    </span>
                    <span className="text-xs opacity-70">{event.timestamp}</span>
                  </div>
                  <span className={`text-xs font-bold uppercase ${
                    event.severity === 'critical' ? 'text-red-400' :
                    event.severity === 'high' ? 'text-orange-400' :
                    event.severity === 'medium' ? 'text-yellow-400' : 'text-cyan-400'
                  }`}>
                    {event.severity}
                  </span>
                </div>
                
                <p className="text-sm mb-2">{event.action}</p>
                
                <div className="grid grid-cols-3 gap-4 text-xs opacity-70 font-mono">
                  <div>IP Origem: {event.source_ip}</div>
                  <div>Porta Destino: {event.destination_port}</div>
                  <div>{event.details}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Controles Avançados */}
      {isMonitoring && (
        <div className="grid grid-cols-3 gap-4">
          <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
            <h4 className="text-cyan-400 font-bold mb-3">FILTROS ATIVOS</h4>
            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-cyan-400/70 text-sm">Port Scans</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-cyan-400/70 text-sm">SYN Floods</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" />
                <span className="text-cyan-400/70 text-sm">Conexões Normais</span>
              </label>
            </div>
          </div>

          <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
            <h4 className="text-cyan-400 font-bold mb-3">AÇÕES AUTOMÁTICAS</h4>
            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-cyan-400/70 text-sm">Auto-block suspeitos</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" />
                <span className="text-cyan-400/70 text-sm">Notificações push</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-cyan-400/70 text-sm">Log detalhado</span>
              </label>
            </div>
          </div>

          <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
            <h4 className="text-cyan-400 font-bold mb-3">AÇÕES RÁPIDAS</h4>
            <div className="space-y-2">
              <button className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-red-500 hover:to-red-600 transition-all">
                BLOQUEAR IP
              </button>
              <button className="w-full bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-orange-500 hover:to-orange-600 transition-all">
                SCAN REVERSO
              </button>
              <button className="w-full bg-gradient-to-r from-cyan-600 to-cyan-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-cyan-500 hover:to-cyan-600 transition-all">
                EXPORTAR LOG
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NetworkMonitor;

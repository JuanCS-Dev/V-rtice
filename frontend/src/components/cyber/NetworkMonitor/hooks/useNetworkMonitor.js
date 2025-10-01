import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for network monitoring
 * Handles real-time events, statistics, and monitoring state
 */
export const useNetworkMonitor = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [networkEvents, setNetworkEvents] = useState([]);
  const [statistics, setStatistics] = useState({
    connectionsToday: 0,
    portScansDetected: 0,
    suspiciousIPs: 0,
    blockedAttempts: 0
  });

  // Simula eventos de rede em tempo real
  useEffect(() => {
    if (!isMonitoring) return;

    const eventTypes = [
      { type: 'CONNECTION', severity: 'info', action: 'Nova conexão estabelecida' },
      { type: 'PORT_SCAN', severity: 'high', action: 'Varredura de portas detectada' },
      { type: 'SYN_FLOOD', severity: 'critical', action: 'Possível ataque SYN flood' },
      { type: 'BLOCKED', severity: 'medium', action: 'Conexão suspeita bloqueada' },
      { type: 'FIRST_SEEN', severity: 'info', action: 'Primeiro contato de IP' }
    ];

    const eventInterval = setInterval(() => {
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

  const toggleMonitoring = useCallback(() => {
    setIsMonitoring(prev => !prev);
  }, []);

  const clearEvents = useCallback(() => {
    setNetworkEvents([]);
    setStatistics({
      connectionsToday: 0,
      portScansDetected: 0,
      suspiciousIPs: 0,
      blockedAttempts: 0
    });
  }, []);

  return {
    isMonitoring,
    networkEvents,
    statistics,
    toggleMonitoring,
    clearEvents
  };
};

export default useNetworkMonitor;

import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for managing network monitoring logic and state.
 */
export const useNetworkMonitoring = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [networkEvents, setNetworkEvents] = useState([]);
  const [realTimeData, setRealTimeData] = useState(null);
  const [statistics, setStatistics] = useState({
    connectionsToday: 0,
    portScansDetected: 0,
    suspiciousIPs: 0,
    blockedAttempts: 0
  });

  // Helper to get severity class based on design tokens
  const getSeverityClass = useCallback((severity) => {
    switch (severity) {
      case 'critical': return 'critical';
      case 'high': return 'high';
      case 'medium': return 'medium';
      case 'info': return 'info';
      default: return 'default';
    }
  }, []);

  // Simulates real-time network events
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
        
        // Update statistics
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

  // Fetches real-time data from backend
  const fetchNetworkData = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/network/monitor'); // Assuming this API exists
      const data = await response.json();

      setRealTimeData(data);
      // Update statistics with real data
      setStatistics(prev => ({
        ...prev,
        connectionsToday: data.active_connections || 0,
        portScansDetected: 0, // Placeholder, backend needs to provide this
        suspiciousIPs: data.unique_ips || 0,
        blockedAttempts: data.total_alerts || 0
      }));
    } catch (error) {
      console.error('Erro ao carregar dados de rede:', error);
    }
  }, []);

  // Fetch data from backend when monitoring is active
  useEffect(() => {
    if (isMonitoring) {
      fetchNetworkData();
      const interval = setInterval(fetchNetworkData, 10000); // Update every 10 seconds
      return () => clearInterval(interval);
    }
  }, [isMonitoring, fetchNetworkData]);

  const toggleMonitoring = useCallback(() => {
    setIsMonitoring(prev => !prev);
    if (isMonitoring) { // If it was monitoring, reset states
      setNetworkEvents([]);
      setRealTimeData(null);
      setStatistics({
        connectionsToday: 0,
        portScansDetected: 0,
        suspiciousIPs: 0,
        blockedAttempts: 0
      });
    }
  }, [isMonitoring]);

  return {
    isMonitoring,
    networkEvents,
    realTimeData,
    statistics,
    toggleMonitoring,
    getSeverityClass
  };
};

export default useNetworkMonitoring;

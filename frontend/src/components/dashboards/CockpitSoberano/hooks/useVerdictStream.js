/**
 * useVerdictStream - Real-time Verdict WebSocket Hook
 * 
 * Connects to Verdict Engine WebSocket stream for live verdict updates
 * NO MOCKS - Real WebSocket connection to backend
 * 
 * @version 1.0.0
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = import.meta.env.VITE_VERDICT_ENGINE_WS || 'ws://34.148.161.131:8000/ws/verdicts';
const RECONNECT_DELAY = 3000;
const MAX_VERDICTS = 100;

export const useVerdictStream = () => {
  const [verdicts, setVerdicts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalReceived: 0,
    activeCritical: 0,
    activeHigh: 0,
    activeMedium: 0,
    activeLow: 0
  });

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('[VerdictStream] Connected to Verdict Engine');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const verdict = JSON.parse(event.data);
          
          setVerdicts(prev => {
            const updated = [verdict, ...prev].slice(0, MAX_VERDICTS);
            return updated;
          });

          setStats(prev => ({
            totalReceived: prev.totalReceived + 1,
            activeCritical: prev.activeCritical + (verdict.severity === 'CRITICAL' ? 1 : 0),
            activeHigh: prev.activeHigh + (verdict.severity === 'HIGH' ? 1 : 0),
            activeMedium: prev.activeMedium + (verdict.severity === 'MEDIUM' ? 1 : 0),
            activeLow: prev.activeLow + (verdict.severity === 'LOW' ? 1 : 0)
          }));
        } catch (err) {
          console.error('[VerdictStream] Failed to parse verdict:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('[VerdictStream] WebSocket error:', err);
        setError('Connection error');
      };

      ws.onclose = () => {
        console.log('[VerdictStream] Disconnected, reconnecting in 3s...');
        setIsConnected(false);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, RECONNECT_DELAY);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[VerdictStream] Failed to connect:', err);
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const dismissVerdict = useCallback((verdictId) => {
    setVerdicts(prev => prev.filter(v => v.id !== verdictId));
    
    setStats(prev => {
      const verdict = verdicts.find(v => v.id === verdictId);
      if (!verdict) return prev;

      return {
        ...prev,
        activeCritical: prev.activeCritical - (verdict.severity === 'CRITICAL' ? 1 : 0),
        activeHigh: prev.activeHigh - (verdict.severity === 'HIGH' ? 1 : 0),
        activeMedium: prev.activeMedium - (verdict.severity === 'MEDIUM' ? 1 : 0),
        activeLow: prev.activeLow - (verdict.severity === 'LOW' ? 1 : 0)
      };
    });
  }, [verdicts]);

  return {
    verdicts,
    isConnected,
    error,
    stats,
    dismissVerdict
  };
};

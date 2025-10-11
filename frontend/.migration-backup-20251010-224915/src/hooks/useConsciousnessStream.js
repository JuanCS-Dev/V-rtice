import { useEffect, useRef, useState, useCallback } from 'react';

const getGatewayBase = () => {
  const env = import.meta?.env;
  const base = (env?.VITE_API_GATEWAY_URL || env?.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
  return base;
};

const getApiKey = () => {
  const env = import.meta?.env;
  return env?.VITE_API_KEY || localStorage.getItem('MAXIMUS_API_KEY') || '';
};

export function useConsciousnessStream({ enabled = true, onMessage, onError } = {}) {
  const [connectionType, setConnectionType] = useState('idle');
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);

  const wsRef = useRef(null);
  const sseRef = useRef(null);
  const reconnectTimer = useRef(null);

  const clearConnections = useCallback(() => {
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
  }, []);

  const handleMessage = useCallback(
    (message) => {
      setLastEvent(message);
      if (onMessage) {
        onMessage(message);
      }
    },
    [onMessage]
  );

  const startWebSocket = useCallback(() => {
    const gateway = getGatewayBase();
    const apiKey = getApiKey();
    const wsUrl = `${gateway.replace(/^http/, 'ws')}/stream/consciousness/ws${apiKey ? `?api_key=${apiKey}` : ''}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    setConnectionType('websocket');

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onclose = () => {
      setIsConnected(false);
      reconnectTimer.current = setTimeout(() => {
        startEventSource();
      }, 1000);
    };

    ws.onerror = (error) => {
      if (onError) onError(error);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleMessage(message);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };
  }, [handleMessage, onError]);

  const startEventSource = useCallback(() => {
    const gateway = getGatewayBase();
    const apiKey = getApiKey();
    const sseUrl = `${gateway}/stream/consciousness/sse${apiKey ? `?api_key=${apiKey}` : ''}`;

    try {
      const eventSource = new EventSource(sseUrl, { withCredentials: false });
      sseRef.current = eventSource;
      setConnectionType('sse');

      eventSource.onopen = () => {
        setIsConnected(true);
      };

      eventSource.onerror = (error) => {
        setIsConnected(false);
        eventSource.close();
        sseRef.current = null;
        if (onError) onError(error);
        reconnectTimer.current = setTimeout(() => {
          startWebSocket();
        }, 1000);
      };

      eventSource.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (err) {
          console.error('Error parsing SSE message:', err);
        }
      };
    } catch (error) {
      if (onError) onError(error);
      startWebSocket();
    }
  }, [handleMessage, onError, startWebSocket]);

  useEffect(() => {
    if (!enabled) return;
    startEventSource();
    return () => clearConnections();
  }, [enabled, startEventSource, clearConnections]);

  return {
    connectionType,
    isConnected,
    lastEvent,
  };
}

export default useConsciousnessStream;

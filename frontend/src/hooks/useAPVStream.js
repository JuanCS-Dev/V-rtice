/**
 * useAPVStream Hook - Real-time APV WebSocket Stream
 * ===================================================
 * 
 * PAGANI Quality WebSocket hook for Adaptive Immunity System
 * Connects to backend WebSocket for real-time APV updates
 * 
 * Biological Analogy: Neural pathways carrying threat signals
 * - Dendritic cells (Oráculo) → T cells (Eureka)
 * - Real-time antigen presentation
 * - Immediate immune response triggering
 * 
 * Backend Endpoint: ws://localhost:8001/ws/adaptive-immunity
 * 
 * Message Types:
 * - apv: New vulnerability detected
 * - patch: Remediation status update
 * - metrics: System health snapshot
 * - heartbeat: Keep-alive signal
 * 
 * @example
 * const { apvs, metrics, status, error } = useAPVStream({
 *   autoConnect: true,
 *   onApv: (apv) => console.log('New threat:', apv)
 * });
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import logger from '@/utils/logger';

// WebSocket connection states
export const WS_STATES = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
  RECONNECTING: 'reconnecting'
};

/**
 * useAPVStream - Real-time APV WebSocket hook
 * 
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {string} options.url - WebSocket URL (default: ws://localhost:8001/ws/adaptive-immunity)
 * @param {number} options.reconnectDelay - Delay between reconnect attempts in ms (default: 3000)
 * @param {number} options.maxReconnectAttempts - Max reconnect attempts (default: 5)
 * @param {Function} options.onApv - Callback when new APV received
 * @param {Function} options.onPatch - Callback when patch update received
 * @param {Function} options.onMetrics - Callback when metrics received
 * @param {Function} options.onConnect - Callback when connected
 * @param {Function} options.onDisconnect - Callback when disconnected
 * @param {Function} options.onError - Callback on error
 * 
 * @returns {Object} Stream state and controls
 */
export const useAPVStream = ({
  autoConnect = true,
  url = 'ws://localhost:8001/ws/adaptive-immunity',
  reconnectDelay = 3000,
  maxReconnectAttempts = 5,
  onApv = null,
  onPatch = null,
  onMetrics = null,
  onConnect = null,
  onDisconnect = null,
  onError = null
} = {}) => {
  // State
  const [status, setStatus] = useState(WS_STATES.DISCONNECTED);
  const [apvs, setApvs] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [lastHeartbeat, setLastHeartbeat] = useState(null);
  const [error, setError] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Refs (persist across renders)
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const callbacksRef = useRef({ onApv, onPatch, onMetrics, onConnect, onDisconnect, onError });

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = { onApv, onPatch, onMetrics, onConnect, onDisconnect, onError };
  }, [onApv, onPatch, onMetrics, onConnect, onDisconnect, onError]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Prevent multiple connections
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      logger.warn('[useAPVStream] Already connected');
      return;
    }

    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    logger.info(`[useAPVStream] Connecting to ${url}...`);
    setStatus(WS_STATES.CONNECTING);
    setError(null);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      // Connection opened
      ws.onopen = () => {
        logger.info('[useAPVStream] ✅ Connected');
        setStatus(WS_STATES.CONNECTED);
        setReconnectAttempts(0);
        setError(null);
        
        if (callbacksRef.current.onConnect) {
          callbacksRef.current.onConnect();
        }
      };

      // Message received
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const { type, timestamp, payload } = message;

          logger.debug(`[useAPVStream] Message received: ${type}`, payload);

          switch (type) {
            case 'apv':
              // New APV detected
              setApvs(prev => [payload, ...prev].slice(0, 100)); // Keep last 100
              if (callbacksRef.current.onApv) {
                callbacksRef.current.onApv(payload);
              }
              break;

            case 'patch':
              // Patch status update
              if (callbacksRef.current.onPatch) {
                callbacksRef.current.onPatch(payload);
              }
              break;

            case 'metrics':
              // System metrics snapshot
              setMetrics(payload);
              if (callbacksRef.current.onMetrics) {
                callbacksRef.current.onMetrics(payload);
              }
              break;

            case 'heartbeat':
              // Keep-alive signal
              setLastHeartbeat(new Date(timestamp));
              break;

            default:
              logger.warn(`[useAPVStream] Unknown message type: ${type}`);
          }
        } catch (err) {
          logger.error('[useAPVStream] Failed to parse message:', err);
        }
      };

      // Connection closed
      ws.onclose = (event) => {
        logger.warn(`[useAPVStream] Connection closed (code: ${event.code})`);
        setStatus(WS_STATES.DISCONNECTED);
        wsRef.current = null;

        if (callbacksRef.current.onDisconnect) {
          callbacksRef.current.onDisconnect(event);
        }

        // Attempt reconnect if not at max attempts
        if (reconnectAttempts < maxReconnectAttempts && autoConnect) {
          const attempt = reconnectAttempts + 1;
          setReconnectAttempts(attempt);
          setStatus(WS_STATES.RECONNECTING);
          
          logger.info(`[useAPVStream] Reconnecting in ${reconnectDelay}ms (attempt ${attempt}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        } else {
          if (reconnectAttempts >= maxReconnectAttempts) {
            logger.error('[useAPVStream] Max reconnect attempts reached');
            setError('Max reconnect attempts reached');
          }
        }
      };

      // Error occurred
      ws.onerror = (event) => {
        logger.error('[useAPVStream] WebSocket error:', event);
        setStatus(WS_STATES.ERROR);
        const errorMsg = 'WebSocket connection error';
        setError(errorMsg);

        if (callbacksRef.current.onError) {
          callbacksRef.current.onError(errorMsg);
        }
      };

    } catch (err) {
      logger.error('[useAPVStream] Failed to create WebSocket:', err);
      setStatus(WS_STATES.ERROR);
      setError(err.message);
    }
  }, [url, reconnectDelay, maxReconnectAttempts, autoConnect, reconnectAttempts]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    logger.info('[useAPVStream] Disconnecting...');

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setStatus(WS_STATES.DISCONNECTED);
    setReconnectAttempts(0);
  }, []);

  /**
   * Send message to WebSocket (for control commands)
   */
  const send = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const payload = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(payload);
      logger.debug('[useAPVStream] Message sent:', message);
      return true;
    } else {
      logger.warn('[useAPVStream] Cannot send message - not connected');
      return false;
    }
  }, []);

  /**
   * Clear APV history
   */
  const clearApvs = useCallback(() => {
    setApvs([]);
    logger.info('[useAPVStream] APV history cleared');
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]); // Only run once on mount

  // Return stream state and controls
  return {
    // State
    status,
    apvs,
    metrics,
    lastHeartbeat,
    error,
    reconnectAttempts,
    
    // Computed
    isConnected: status === WS_STATES.CONNECTED,
    isConnecting: status === WS_STATES.CONNECTING,
    isReconnecting: status === WS_STATES.RECONNECTING,
    hasError: status === WS_STATES.ERROR,
    
    // Controls
    connect,
    disconnect,
    send,
    clearApvs
  };
};

export default useAPVStream;

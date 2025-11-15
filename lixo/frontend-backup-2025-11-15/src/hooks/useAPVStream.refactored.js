/**
 * useAPVStream Hook - Real-time APV WebSocket Stream (REFACTORED)
 * ================================================================
 *
 * Refactored to use WebSocketManager for centralized connection management
 *
 * PAGANI Quality WebSocket hook for Adaptive Immunity System
 * Connects to backend WebSocket for real-time APV updates
 *
 * Biological Analogy: Neural pathways carrying threat signals
 * - Dendritic cells (Oráculo) → T cells (Eureka)
 * - Real-time antigen presentation
 * - Immediate immune response triggering
 *
 * Backend Endpoint: ws://34.148.161.131:8000/stream/apv/ws
 *
 * Message Types:
 * - apv: New vulnerability detected
 * - patch: Remediation status update
 * - metrics: System health snapshot
 * - heartbeat: Keep-alive signal
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002
 *
 * @example
 * const { apvs, metrics, status, error } = useAPVStream({
 *   autoConnect: true,
 *   onApv: (apv) => console.log('New threat:', apv)
 * });
 */

import { useState, useCallback } from 'react';
import { useWebSocketManager } from './useWebSocketManager';
import logger from '@/utils/logger';

// WebSocket connection states (for backward compatibility)
export const WS_STATES = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
  RECONNECTING: 'reconnecting',
};

/**
 * useAPVStream - Real-time APV WebSocket hook
 *
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
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
  onApv = null,
  onPatch = null,
  onMetrics = null,
  onConnect = null,
  onDisconnect = null,
  onError = null,
} = {}) => {
  const [apvs, setApvs] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  // Message handler
  const handleMessage = useCallback(
    (data) => {
      logger.debug('[useAPVStream] Message received:', data.type);

      switch (data.type) {
        case 'apv':
          // New APV vulnerability
          setApvs((prev) => [data.data, ...prev].slice(0, 100)); // Keep last 100
          if (onApv) {
            onApv(data.data);
          }
          break;

        case 'patch':
          // Patch status update
          if (onPatch) {
            onPatch(data.data);
          }
          break;

        case 'metrics':
          // System health metrics
          setMetrics(data.data);
          if (onMetrics) {
            onMetrics(data.data);
          }
          break;

        case 'heartbeat':
          logger.debug('[useAPVStream] Heartbeat received');
          break;

        case 'pong':
          logger.debug('[useAPVStream] Pong received');
          break;

        case 'connection':
          // Handle connection events
          if (data.status === 'connected') {
            setError(null);
            if (onConnect) {
              onConnect();
            }
          } else if (data.status === 'disconnected') {
            if (onDisconnect) {
              onDisconnect();
            }
          } else if (data.status === 'error') {
            setError(data.error);
            if (onError) {
              onError(data.error);
            }
          }
          break;

        case 'error':
          logger.error('[useAPVStream] Server error:', data.message);
          setError(data.message);
          if (onError) {
            onError(data.message);
          }
          break;

        default:
          logger.warn('[useAPVStream] Unknown message type:', data.type);
      }
    },
    [onApv, onPatch, onMetrics, onConnect, onDisconnect, onError]
  );

  // Use centralized WebSocketManager
  const {
    isConnected,
    isConnecting,
    isDisconnected,
    isError,
    reconnectAttempts,
    send,
    reconnect,
  } = useWebSocketManager('apv.stream', {
    enabled: autoConnect,
    onMessage: handleMessage,
    connectionOptions: {
      reconnect: true,
      maxReconnectAttempts: 5,
      reconnectInterval: 3000,
      heartbeatInterval: 25000,
      debug: false,
    },
  });

  // Map states to legacy WS_STATES for backward compatibility
  let status = WS_STATES.DISCONNECTED;
  if (isConnecting) status = WS_STATES.CONNECTING;
  else if (isConnected) status = WS_STATES.CONNECTED;
  else if (isError) status = WS_STATES.ERROR;
  else if (reconnectAttempts > 0) status = WS_STATES.RECONNECTING;
  else if (isDisconnected) status = WS_STATES.DISCONNECTED;

  // Connect/disconnect functions
  const connect = reconnect;
  const disconnect = useCallback(() => {
    logger.info('[useAPVStream] Disconnect requested');
    // WebSocketManager handles disconnect automatically on unmount
  }, []);

  // Clear APVs
  const clearApvs = useCallback(() => {
    setApvs([]);
  }, []);

  return {
    // State
    apvs,
    metrics,
    status,
    error,
    isConnected,
    isConnecting,
    isDisconnected,
    isError,
    reconnectAttempts,

    // Controls
    connect,
    disconnect,
    send,
    clearApvs,
  };
};

export default useAPVStream;

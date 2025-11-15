/**
 * WebSocketManager Hook
 * ======================
 *
 * React hook wrapper for WebSocketManager.
 * Provides React-friendly interface for centralized WebSocket management.
 *
 * Boris Cherny Pattern: Use existing robust implementation (WebSocketManager)
 * instead of reimplementing WebSocket logic in hooks.
 *
 * Features (delegated to WebSocketManager):
 * - Connection pooling (single connection per endpoint)
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong
 * - Message queuing for offline resilience
 * - Fallback to SSE/polling
 * - Pub/sub pattern for multiple subscribers
 *
 * Usage:
 * ```javascript
 * const { data, isConnected, send } = useWebSocketManager('/api/stream');
 * ```
 *
 * Migrating from useWebSocket:
 * ```javascript
 * // OLD (direct WebSocket, 330 lines of duplicate logic)
 * const { data, send } = useWebSocket(wsUrl, options);
 *
 * // NEW (uses WebSocketManager, 50 lines, zero duplication)
 * const { data, send } = useWebSocketManager('/api/stream', options);
 * ```
 *
 * Governed by: Constituição Vértice v2.7 - ADR-002
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import WebSocketManager from '@/services/websocket/WebSocketManager';
import logger from '@/utils/logger';

/**
 * React hook for WebSocketManager
 *
 * @param {string} endpointPath - WebSocket endpoint (e.g., '/api/stream')
 * @param {Object} options - Connection options
 * @param {boolean} options.reconnect - Enable auto-reconnect (default: true)
 * @param {number} options.reconnectInterval - Base reconnect delay in ms
 * @param {number} options.maxReconnectAttempts - Max reconnect attempts
 * @param {number} options.heartbeatInterval - Heartbeat interval in ms
 * @param {boolean} options.fallbackToSSE - Enable SSE fallback
 * @param {boolean} options.fallbackToPolling - Enable polling fallback
 * @param {Function} options.onOpen - Callback on connection open
 * @param {Function} options.onClose - Callback on connection close
 * @param {Function} options.onError - Callback on error
 * @param {Function} options.onMessage - Callback on message (receives parsed data)
 * @param {boolean} options.debug - Enable debug logging
 *
 * @returns {Object} WebSocket state and methods
 * @returns {any} data - Latest received message data
 * @returns {boolean} isConnected - Connection status
 * @returns {Function} send - Send message function
 * @returns {Function} disconnect - Disconnect function
 * @returns {string} connectionState - Connection state (IDLE, CONNECTING, CONNECTED, etc.)
 * @returns {Error|null} error - Last error
 */
export const useWebSocketManager = (endpointPath, options = {}) => {
  // State
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('IDLE');
  const [error, setError] = useState(null);

  // Refs
  const unsubscribeRef = useRef(null);
  const optionsRef = useRef(options);

  // Update options ref when they change
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  // Send message
  const send = useCallback(
    (message) => {
      try {
        WebSocketManager.send(endpointPath, message);
      } catch (err) {
        logger.error(\`[useWebSocketManager] Failed to send message:\`, err);
        setError(err);
      }
    },
    [endpointPath]
  );

  // Disconnect
  const disconnect = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }

    WebSocketManager.disconnect(endpointPath);
    setIsConnected(false);
    setConnectionState('DISCONNECTED');
  }, [endpointPath]);

  // Subscribe to WebSocket messages
  useEffect(() => {
    if (!endpointPath) {
      logger.warn('[useWebSocketManager] No endpoint provided');
      return;
    }

    // Message handler
    const handleMessage = (message) => {
      // Handle different message types
      if (message.type === 'state') {
        // Connection state update
        setConnectionState(message.state);
        setIsConnected(message.state === 'CONNECTED');

        // Call user callbacks
        if (message.state === 'CONNECTED' && optionsRef.current.onOpen) {
          optionsRef.current.onOpen();
        } else if (message.state === 'DISCONNECTED' && optionsRef.current.onClose) {
          optionsRef.current.onClose();
        } else if (message.state === 'ERROR' && optionsRef.current.onError) {
          optionsRef.current.onError(message.error);
          setError(message.error);
        }
      } else if (message.type === 'error') {
        // Error message
        setError(message.error);
        if (optionsRef.current.onError) {
          optionsRef.current.onError(message.error);
        }
      } else {
        // Regular data message
        setData(message);

        if (optionsRef.current.onMessage) {
          optionsRef.current.onMessage(message);
        }
      }
    };

    // Subscribe to endpoint
    const unsubscribe = WebSocketManager.subscribe(
      endpointPath,
      handleMessage,
      options
    );

    unsubscribeRef.current = unsubscribe;

    // Cleanup on unmount
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
    };
  }, [endpointPath]); // Only re-subscribe if endpoint changes

  return {
    data,
    isConnected,
    connectionState,
    error,
    send,
    disconnect,
  };
};

export default useWebSocketManager;

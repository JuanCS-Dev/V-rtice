/**
 * useWebSocketManager Hook
 * =========================
 *
 * React hook for WebSocketManager integration
 * Provides declarative WebSocket connections with automatic cleanup
 *
 * Features:
 * - Automatic subscription/unsubscription
 * - Connection state management
 * - Message sending
 * - Error handling
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002
 *
 * Usage:
 * const { data, isConnected, send, status } = useWebSocketManager('maximus.stream');
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { webSocketManager, ConnectionState } from '@/services/websocket';
import logger from '@/utils/logger';

/**
 * Hook to connect to WebSocket endpoint via WebSocketManager
 *
 * @param {string} endpointPath - Endpoint path (e.g., 'maximus.stream')
 * @param {Object} options - Hook options
 * @param {boolean} options.enabled - Enable connection (default: true)
 * @param {Function} options.onMessage - Message callback
 * @param {Function} options.onConnect - Connection callback
 * @param {Function} options.onDisconnect - Disconnection callback
 * @param {Function} options.onError - Error callback
 * @param {Object} options.connectionOptions - Connection options for WebSocketManager
 * @returns {Object} Hook state and controls
 */
export const useWebSocketManager = (endpointPath, options = {}) => {
  const {
    enabled = true,
    onMessage = null,
    onConnect = null,
    onDisconnect = null,
    onError = null,
    connectionOptions = {},
  } = options;

  const [data, setData] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const unsubscribeRef = useRef(null);

  // Update status periodically
  useEffect(() => {
    if (!enabled) return;

    const updateStatus = () => {
      const currentStatus = webSocketManager.getStatus(endpointPath);
      setStatus(currentStatus);
    };

    // Initial status
    updateStatus();

    // Update every second
    const interval = setInterval(updateStatus, 1000);

    return () => {
      clearInterval(interval);
    };
  }, [endpointPath, enabled]);

  // Message handler
  const handleMessage = useCallback(
    (message) => {
      // Handle connection messages
      if (message.type === 'connection') {
        if (message.status === 'connected') {
          if (onConnect) onConnect();
        } else if (message.status === 'disconnected') {
          if (onDisconnect) onDisconnect();
        } else if (message.status === 'error') {
          setError(message.error);
          if (onError) onError(message.error);
        }
        return;
      }

      // Handle data messages
      setData(message);
      if (onMessage) {
        onMessage(message);
      }
    },
    [onMessage, onConnect, onDisconnect, onError]
  );

  // Subscribe to WebSocket
  useEffect(() => {
    if (!enabled) return;

    logger.debug('[useWebSocketManager] Subscribing to', endpointPath);

    unsubscribeRef.current = webSocketManager.subscribe(
      endpointPath,
      handleMessage,
      connectionOptions
    );

    // Cleanup on unmount
    return () => {
      if (unsubscribeRef.current) {
        logger.debug('[useWebSocketManager] Unsubscribing from', endpointPath);
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
    };
  }, [endpointPath, enabled, handleMessage, connectionOptions]);

  // Send message
  const send = useCallback(
    (message) => {
      return webSocketManager.send(endpointPath, message);
    },
    [endpointPath]
  );

  // Reconnect
  const reconnect = useCallback(() => {
    // Disconnect and reconnect
    webSocketManager.disconnect(endpointPath);
    // Manager will auto-reconnect on next subscribe
  }, [endpointPath]);

  return {
    data,
    status,
    error,
    isConnected: status?.isConnected || false,
    isConnecting: status?.state === ConnectionState.CONNECTING,
    isDisconnected: status?.state === ConnectionState.DISCONNECTED || status?.state === ConnectionState.IDLE,
    isError: status?.state === ConnectionState.ERROR,
    isFallback: status?.state === ConnectionState.FALLBACK,
    queuedMessages: status?.queuedMessages || 0,
    reconnectAttempts: status?.reconnectAttempts || 0,
    connectionId: status?.connectionId,
    send,
    reconnect,
  };
};

/**
 * Hook to send messages to WebSocket without subscribing
 *
 * @param {string} endpointPath - Endpoint path
 * @returns {Function} Send function
 */
export const useWebSocketSend = (endpointPath) => {
  return useCallback(
    (message) => {
      return webSocketManager.send(endpointPath, message);
    },
    [endpointPath]
  );
};

/**
 * Hook to get status of all WebSocket connections
 *
 * @returns {Object} Status map
 */
export const useWebSocketStatus = () => {
  const [allStatus, setAllStatus] = useState({});

  useEffect(() => {
    const updateStatus = () => {
      setAllStatus(webSocketManager.getAllStatus());
    };

    // Initial status
    updateStatus();

    // Update every second
    const interval = setInterval(updateStatus, 1000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  return allStatus;
};

export default useWebSocketManager;

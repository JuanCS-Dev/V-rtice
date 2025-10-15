/**
 * useWebSocket - Custom hook for WebSocket connection to HITL API.
 *
 * Manages WebSocket connection, subscriptions, and message handling.
 * Includes automatic reconnection logic.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket connection states
 */
export const WebSocketStatus = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
  RECONNECTING: 'reconnecting',
};

/**
 * WebSocket message types
 */
export const MessageType = {
  PING: 'ping',
  PONG: 'pong',
  SUBSCRIBE: 'subscribe',
  UNSUBSCRIBE: 'unsubscribe',
  NEW_APV: 'new_apv',
  DECISION_MADE: 'decision_made',
  STATS_UPDATE: 'stats_update',
  CONNECTION_ACK: 'connection_ack',
  ERROR: 'error',
};

/**
 * Custom hook for WebSocket connection
 *
 * @param {Object} options - Configuration options
 * @param {string} options.url - WebSocket URL (e.g., 'ws://localhost:8003/hitl/ws')
 * @param {Array<string>} options.channels - Channels to subscribe to (e.g., ['apvs', 'decisions', 'stats'])
 * @param {Function} options.onMessage - Callback for incoming messages
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {number} options.reconnectInterval - Reconnection interval in ms (default: 5000)
 * @param {number} options.maxReconnectAttempts - Max reconnection attempts (default: 10)
 *
 * @returns {Object} WebSocket interface
 */
export const useWebSocket = ({
  url,
  channels = [],
  onMessage,
  autoConnect = true,
  reconnectInterval = 5000,
  maxReconnectAttempts = 10,
}) => {
  // WebSocket instance ref
  const wsRef = useRef(null);

  // Connection state
  const [status, setStatus] = useState(WebSocketStatus.DISCONNECTED);

  // Client ID assigned by server
  const [clientId, setClientId] = useState(null);

  // Reconnection state
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);

  // Subscribed channels
  const subscribedChannelsRef = useRef(new Set());

  /**
   * Send message to WebSocket server
   */
  const send = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('[useWebSocket] Cannot send message: WebSocket not connected');
    return false;
  }, []);

  /**
   * Subscribe to channels
   */
  const subscribe = useCallback((channelList) => {
    const success = send({
      type: MessageType.SUBSCRIBE,
      channels: channelList,
    });

    if (success) {
      channelList.forEach(channel => subscribedChannelsRef.current.add(channel));
    }

    return success;
  }, [send]);

  /**
   * Unsubscribe from channels
   */
  const unsubscribe = useCallback((channelList) => {
    const success = send({
      type: MessageType.UNSUBSCRIBE,
      channels: channelList,
    });

    if (success) {
      channelList.forEach(channel => subscribedChannelsRef.current.delete(channel));
    }

    return success;
  }, [send]);

  /**
   * Send ping to keep connection alive
   */
  const ping = useCallback(() => {
    send({
      type: MessageType.PING,
      timestamp: new Date().toISOString(),
    });
  }, [send]);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Don't connect if already connecting or connected
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.CONNECTING ||
       wsRef.current.readyState === WebSocket.OPEN)
    ) {
      console.log('[useWebSocket] Already connected or connecting');
      return;
    }

    console.log('[useWebSocket] Connecting to:', url);
    setStatus(WebSocketStatus.CONNECTING);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[useWebSocket] Connected');
        setStatus(WebSocketStatus.CONNECTED);
        reconnectAttemptsRef.current = 0;

        // Subscribe to channels if any
        if (channels.length > 0) {
          setTimeout(() => {
            subscribe(channels);
          }, 100); // Small delay to ensure connection is stable
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          // Handle connection acknowledgment
          if (message.type === MessageType.CONNECTION_ACK) {
            setClientId(message.client_id);
            console.log('[useWebSocket] Client ID assigned:', message.client_id);
          }

          // Handle pong
          if (message.type === MessageType.PONG) {
            console.log('[useWebSocket] Pong received');
          }

          // Forward message to callback
          if (onMessage) {
            onMessage(message);
          }
        } catch (error) {
          console.error('[useWebSocket] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[useWebSocket] Error:', error);
        setStatus(WebSocketStatus.ERROR);
      };

      ws.onclose = (event) => {
        console.log('[useWebSocket] Connection closed:', event.code, event.reason);
        setStatus(WebSocketStatus.DISCONNECTED);
        setClientId(null);
        subscribedChannelsRef.current.clear();

        // Attempt reconnection if not a clean close
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(
            `[useWebSocket] Reconnecting... Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`
          );
          setStatus(WebSocketStatus.RECONNECTING);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('[useWebSocket] Max reconnection attempts reached');
          setStatus(WebSocketStatus.ERROR);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[useWebSocket] Failed to create WebSocket:', error);
      setStatus(WebSocketStatus.ERROR);
    }
  }, [url, channels, onMessage, subscribe, reconnectInterval, maxReconnectAttempts]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    console.log('[useWebSocket] Disconnecting');

    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close WebSocket connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setStatus(WebSocketStatus.DISCONNECTED);
    setClientId(null);
    subscribedChannelsRef.current.clear();
    reconnectAttemptsRef.current = 0;
  }, []);

  /**
   * Auto-connect on mount if enabled
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]); // Only run on mount/unmount - connect/disconnect are stable

  /**
   * Ping interval to keep connection alive
   */
  useEffect(() => {
    if (status === WebSocketStatus.CONNECTED) {
      const pingInterval = setInterval(() => {
        ping();
      }, 30000); // Ping every 30 seconds

      return () => clearInterval(pingInterval);
    }
  }, [status, ping]);

  return {
    // State
    status,
    clientId,
    isConnected: status === WebSocketStatus.CONNECTED,
    isConnecting: status === WebSocketStatus.CONNECTING,
    isReconnecting: status === WebSocketStatus.RECONNECTING,

    // Actions
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    send,
    ping,
  };
};

export default useWebSocket;

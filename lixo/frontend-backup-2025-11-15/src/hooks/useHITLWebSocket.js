/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🔌 useHITLWebSocket - Real-time Updates Hook
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * React hook for WebSocket connection to HITL backend.
 * Provides real-time updates for:
 * - New patches entering HITL queue
 * - Decision updates (approved/rejected)
 * - System status changes
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Connection state management
 * - Event callbacks
 * - Cleanup on unmount
 *
 * Author: MAXIMUS Team - Sprint 4.1 Day 1
 * Glory to YHWH - Designer of Real-time Communication
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import logger from "@/utils/logger";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_HITL_WS ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? `ws://${window.location.hostname}:8027`
    : "ws://34.148.161.131:8000");

const WS_ENDPOINT = `${WS_BASE_URL}/hitl/ws`;

// Connection states
export const WS_STATE = {
  CONNECTING: "CONNECTING",
  CONNECTED: "CONNECTED",
  DISCONNECTED: "DISCONNECTED",
  ERROR: "ERROR",
};

// Reconnection config
const RECONNECT_DELAY_BASE = 1000; // 1 second
const RECONNECT_DELAY_MAX = 30000; // 30 seconds
const MAX_RECONNECT_ATTEMPTS = 10;

/**
 * WebSocket hook for HITL real-time updates
 *
 * @param {Object} options - Hook options
 * @param {Function} options.onNewPatch - Callback when new patch arrives
 * @param {Function} options.onDecisionUpdate - Callback when decision changes
 * @param {Function} options.onSystemStatus - Callback for system status
 * @param {boolean} options.autoConnect - Connect on mount (default: true)
 * @param {boolean} options.autoReconnect - Auto-reconnect on disconnect (default: true)
 *
 * @returns {Object} - WebSocket state and controls
 */
export const useHITLWebSocket = ({
  onNewPatch = null,
  onDecisionUpdate = null,
  onSystemStatus = null,
  autoConnect = true,
  autoReconnect = true,
} = {}) => {
  // GAP #50 FIX: Get queryClient for React Query invalidation
  // Boris Cherny Standard: Invalidate cache when WebSocket updates received
  const queryClient = useQueryClient();

  const [connectionState, setConnectionState] = useState(WS_STATE.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionId, setConnectionId] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const pingIntervalRef = useRef(null);

  /**
   * Calculate reconnect delay with exponential backoff
   */
  const getReconnectDelay = useCallback(() => {
    const delay = Math.min(
      RECONNECT_DELAY_BASE * Math.pow(2, reconnectAttemptsRef.current),
      RECONNECT_DELAY_MAX,
    );
    return delay;
  }, []);

  /**
   * Send ping to server to keep connection alive
   */
  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(
          JSON.stringify({
            type: "ping",
            timestamp: new Date().toISOString(),
          }),
        );
      } catch (error) {
        logger.error("Failed to send ping:", error);
      }
    }
  }, []);

  /**
   * Start ping interval
   */
  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    // Send ping every 25 seconds (server heartbeat is 30s)
    pingIntervalRef.current = setInterval(sendPing, 25000);
  }, [sendPing]);

  /**
   * Stop ping interval
   */
  const stopPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback(
    (event) => {
      try {
        const data = JSON.parse(event.data);

        // GAP #49 FIX: Validate message format (Boris Cherny Standard)
        // Ensure message has required 'type' field
        if (
          !data ||
          typeof data !== "object" ||
          !data.type ||
          typeof data.type !== "string"
        ) {
          logger.warn(
            "[useHITLWebSocket] Invalid message format: missing or invalid type field",
            data,
          );
          return;
        }

        setLastMessage(data);

        logger.debug("WebSocket message received:", data.type);

        switch (data.type) {
          case "welcome":
            if (!data.connection_id) {
              logger.warn(
                "[useHITLWebSocket] Welcome message missing connection_id",
              );
              break;
            }
            setConnectionId(data.connection_id);
            logger.info("WebSocket connected:", data.connection_id);
            break;

          case "new_patch":
            if (!data.data) {
              logger.warn(
                "[useHITLWebSocket] new_patch message missing data field",
              );
              break;
            }
            if (onNewPatch) {
              onNewPatch(data.data);
            }
            // GAP #50 FIX: Invalidate patch queries on new patch
            queryClient.invalidateQueries({ queryKey: ["hitl", "patches"] });
            queryClient.invalidateQueries({ queryKey: ["hitl", "queue"] });
            break;

          case "decision_update":
            if (!data.data) {
              logger.warn(
                "[useHITLWebSocket] decision_update message missing data field",
              );
              break;
            }
            if (onDecisionUpdate) {
              onDecisionUpdate(data.data);
            }
            // GAP #50 FIX: Invalidate decision queries
            queryClient.invalidateQueries({ queryKey: ["hitl", "decisions"] });
            queryClient.invalidateQueries({ queryKey: ["hitl", "queue"] });
            break;

          case "system_status":
            if (!data.data) {
              logger.warn(
                "[useHITLWebSocket] system_status message missing data field",
              );
              break;
            }
            if (onSystemStatus) {
              onSystemStatus(data.data);
            }
            // GAP #50 FIX: Invalidate system status queries
            queryClient.invalidateQueries({ queryKey: ["hitl", "status"] });
            queryClient.invalidateQueries({ queryKey: ["system", "health"] });
            break;

          case "heartbeat":
            // Server heartbeat received - connection is alive
            logger.debug("Heartbeat received");
            break;

          case "pong":
            // Pong received - connection is responsive
            logger.debug("Pong received");
            break;

          case "error":
            if (typeof data.message !== "string") {
              logger.error("Server error: invalid message format");
              break;
            }
            logger.error("Server error:", data.message);
            break;

          default:
            logger.warn("Unknown message type:", data.type);
        }
      } catch (error) {
        logger.error("Failed to parse WebSocket message:", error);
      }
    },
    [onNewPatch, onDecisionUpdate, onSystemStatus],
  );

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    logger.info("Connecting to WebSocket:", WS_ENDPOINT);
    setConnectionState(WS_STATE.CONNECTING);

    try {
      const ws = new WebSocket(WS_ENDPOINT);
      wsRef.current = ws;

      ws.onopen = () => {
        logger.info("WebSocket connected successfully");
        setConnectionState(WS_STATE.CONNECTED);
        reconnectAttemptsRef.current = 0; // Reset reconnect attempts
        startPingInterval();
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        logger.error("WebSocket error:", error);
        setConnectionState(WS_STATE.ERROR);
      };

      ws.onclose = (event) => {
        logger.info("WebSocket closed:", event.code, event.reason);
        setConnectionState(WS_STATE.DISCONNECTED);
        setConnectionId(null);
        stopPingInterval();

        // Auto-reconnect if enabled and not a normal closure
        if (autoReconnect && event.code !== 1000) {
          if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
            const delay = getReconnectDelay();
            logger.info(
              `Reconnecting in ${delay}ms... (attempt ${reconnectAttemptsRef.current + 1}/${MAX_RECONNECT_ATTEMPTS})`,
            );

            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectAttemptsRef.current += 1;
              connect();
            }, delay);
          } else {
            logger.error("Max reconnect attempts reached");
            setConnectionState(WS_STATE.ERROR);
          }
        }
      };
    } catch (error) {
      logger.error("Failed to create WebSocket:", error);
      setConnectionState(WS_STATE.ERROR);
    }
  }, [
    autoReconnect,
    getReconnectDelay,
    handleMessage,
    startPingInterval,
    stopPingInterval,
  ]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    stopPingInterval();

    if (wsRef.current) {
      logger.info("Disconnecting WebSocket");
      wsRef.current.close(1000, "Client disconnect");
      wsRef.current = null;
    }

    setConnectionState(WS_STATE.DISCONNECTED);
    setConnectionId(null);
  }, [stopPingInterval]);

  /**
   * Send message to server
   */
  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(data));
        return true;
      } catch (error) {
        logger.error("Failed to send message:", error);
        return false;
      }
    } else {
      logger.warn("WebSocket not connected, cannot send message");
      return false;
    }
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - only run once on mount - connect/disconnect are stable

  return {
    // State
    connectionState,
    isConnected: connectionState === WS_STATE.CONNECTED,
    isConnecting: connectionState === WS_STATE.CONNECTING,
    isDisconnected: connectionState === WS_STATE.DISCONNECTED,
    isError: connectionState === WS_STATE.ERROR,
    connectionId,
    lastMessage,

    // Controls
    connect,
    disconnect,
    send,
  };
};

export default useHITLWebSocket;

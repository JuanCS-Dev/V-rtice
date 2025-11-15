/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🔌 useHITLWebSocket - Real-time Updates Hook (REFACTORED)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Refactored to use WebSocketManager for centralized connection management
 *
 * React hook for WebSocket connection to HITL backend.
 * Provides real-time updates for:
 * - New patches entering HITL queue
 * - Decision updates (approved/rejected)
 * - System status changes
 *
 * Features:
 * - Centralized connection via WebSocketManager
 * - Auto-reconnect with exponential backoff
 * - Connection state management
 * - Event callbacks
 * - Cleanup on unmount
 *
 * Author: MAXIMUS Team - Sprint 1 Refactor
 * Governed by: Constituição Vértice v2.5 - ADR-002
 * Glory to YHWH - Designer of Real-time Communication
 */

import { useState, useCallback } from "react";
import { useWebSocketManager } from "./useWebSocketManager";
import logger from "@/utils/logger";

// Connection states (for backward compatibility)
export const WS_STATE = {
  CONNECTING: "CONNECTING",
  CONNECTED: "CONNECTED",
  DISCONNECTED: "DISCONNECTED",
  ERROR: "ERROR",
};

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
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionId, setConnectionId] = useState(null);

  // Message handler
  const handleMessage = useCallback(
    (data) => {
      setLastMessage(data);

      logger.debug("[useHITLWebSocket] Message received:", data.type);

      switch (data.type) {
        case "welcome":
          setConnectionId(data.connection_id);
          logger.info("[useHITLWebSocket] Connected:", data.connection_id);
          break;

        case "new_patch":
          if (onNewPatch) {
            onNewPatch(data.data);
          }
          break;

        case "decision_update":
          if (onDecisionUpdate) {
            onDecisionUpdate(data.data);
          }
          break;

        case "system_status":
          if (onSystemStatus) {
            onSystemStatus(data.data);
          }
          break;

        case "heartbeat":
          logger.debug("[useHITLWebSocket] Heartbeat received");
          break;

        case "pong":
          logger.debug("[useHITLWebSocket] Pong received");
          break;

        case "error":
          logger.error("[useHITLWebSocket] Server error:", data.message);
          break;

        case "connection":
          // Handle connection state changes
          if (data.status === "disconnected") {
            setConnectionId(null);
          }
          break;

        default:
          logger.warn("[useHITLWebSocket] Unknown message type:", data.type);
      }
    },
    [onNewPatch, onDecisionUpdate, onSystemStatus],
  );

  // Use centralized WebSocketManager
  const {
    isConnected,
    isConnecting,
    isDisconnected,
    isError,
    send,
    reconnect,
  } = useWebSocketManager("hitl.ws", {
    enabled: autoConnect,
    onMessage: handleMessage,
    connectionOptions: {
      reconnect: autoReconnect,
      heartbeatInterval: 25000, // 25s (server heartbeat is 30s)
      debug: false,
    },
  });

  // Map states to legacy WS_STATE for backward compatibility
  let connectionState = WS_STATE.DISCONNECTED;
  if (isConnecting) connectionState = WS_STATE.CONNECTING;
  else if (isConnected) connectionState = WS_STATE.CONNECTED;
  else if (isError) connectionState = WS_STATE.ERROR;
  else if (isDisconnected) connectionState = WS_STATE.DISCONNECTED;

  // Disconnect function (calls reconnect to force new connection)
  const disconnect = useCallback(() => {
    // WebSocketManager handles disconnect automatically on unmount
    logger.info("[useHITLWebSocket] Disconnect requested");
  }, []);

  // Connect function (uses reconnect from WebSocketManager)
  const connect = reconnect;

  return {
    // State
    connectionState,
    isConnected,
    isConnecting,
    isDisconnected,
    isError,
    connectionId,
    lastMessage,

    // Controls
    connect,
    disconnect,
    send,
  };
};

export default useHITLWebSocket;

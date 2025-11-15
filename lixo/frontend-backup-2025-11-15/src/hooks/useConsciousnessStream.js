/**
 * useConsciousnessStream Hook
 * ============================
 *
 * Refactored to use WebSocketManager
 * Connects to consciousness stream endpoint
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002
 */

import { useCallback } from "react";
import { useWebSocketManager } from "./useWebSocketManager";

export function useConsciousnessStream({
  enabled = true,
  onMessage,
  onError,
} = {}) {
  // Use centralized WebSocketManager
  const {
    data: lastEvent,
    isConnected,
    isFallback,
    status,
  } = useWebSocketManager("consciousness.stream", {
    enabled,
    onMessage: useCallback(
      (message) => {
        if (onMessage) {
          onMessage(message);
        }
      },
      [onMessage],
    ),
    onError: useCallback(
      (error) => {
        if (onError) {
          onError(error);
        }
      },
      [onError],
    ),
    connectionOptions: {
      fallbackToSSE: true,
      fallbackToPolling: false,
      debug: false,
    },
  });

  // Determine connection type
  const connectionType = isFallback
    ? "sse"
    : isConnected
      ? "websocket"
      : "idle";

  return {
    connectionType,
    isConnected,
    lastEvent,
    status,
  };
}

export default useConsciousnessStream;

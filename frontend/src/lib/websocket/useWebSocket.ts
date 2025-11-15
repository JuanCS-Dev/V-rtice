import { useEffect, useRef, useState } from "react";
import type { WSEventType } from "@/types";

type EventHandler<T = unknown> = (data: T) => void;

interface UseWebSocketOptions {
  url: string;
  token?: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: Event | null;
}

export function useWebSocket<T = unknown>(
  eventType?: WSEventType,
  handler?: EventHandler<T>,
  options: UseWebSocketOptions = { url: "", autoConnect: true },
) {
  const {
    url,
    token,
    autoConnect = true,
    reconnect = true,
    reconnectAttempts = 10,
    reconnectDelay = 1000,
    heartbeatInterval = 30000,
    onOpen,
    onClose,
    onError,
  } = options;

  const ws = useRef<WebSocket | null>(null);
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
  });

  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
    null,
  );

  const connect = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setState((prev) => ({ ...prev, isConnecting: true }));

    const wsUrl = token ? `${url}?token=${token}` : url;

    try {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log("[useWebSocket] Connected to", url);
        setState({ isConnected: true, isConnecting: false, error: null });
        reconnectAttemptsRef.current = 0;
        startHeartbeat();
        onOpen?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle heartbeat response
          if (data.type === "pong") {
            return;
          }

          // Call handler if event type matches
          if (eventType && data.type === eventType && handler) {
            handler(data.data || data);
          }
        } catch (error) {
          console.error("[useWebSocket] Failed to parse message:", error);
        }
      };

      ws.current.onerror = (error) => {
        console.error("[useWebSocket] Error:", error);
        setState((prev) => ({ ...prev, error }));
        onError?.(error);
      };

      ws.current.onclose = () => {
        console.log("[useWebSocket] Disconnected from", url);
        setState({ isConnected: false, isConnecting: false, error: null });
        stopHeartbeat();
        onClose?.();

        // Attempt reconnect if enabled
        if (reconnect && reconnectAttemptsRef.current < reconnectAttempts) {
          attemptReconnect();
        }
      };
    } catch (error) {
      console.error("[useWebSocket] Connection failed:", error);
      setState({
        isConnected: false,
        isConnecting: false,
        error: error as Event,
      });

      if (reconnect && reconnectAttemptsRef.current < reconnectAttempts) {
        attemptReconnect();
      }
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    stopHeartbeat();

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    reconnectAttemptsRef.current = 0;
    setState({ isConnected: false, isConnecting: false, error: null });
  };

  const send = (data: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    } else {
      console.warn("[useWebSocket] Cannot send, not connected");
    }
  };

  const startHeartbeat = () => {
    stopHeartbeat();
    heartbeatIntervalRef.current = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: "ping" }));
      }
    }, heartbeatInterval);
  };

  const stopHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  };

  const attemptReconnect = () => {
    reconnectAttemptsRef.current++;
    const delay = Math.min(
      reconnectDelay * Math.pow(2, reconnectAttemptsRef.current - 1),
      30000,
    );

    console.log(
      `[useWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`,
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  };

  useEffect(() => {
    if (autoConnect && url) {
      connect();
    }

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, token, autoConnect]);

  return {
    ...state,
    connect,
    disconnect,
    send,
  };
}

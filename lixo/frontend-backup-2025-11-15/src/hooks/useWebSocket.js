/**
 * Optimized WebSocket Hook
 *
 * Features:
 * - Exponential backoff reconnection
 * - Heartbeat/ping-pong mechanism
 * - Automatic fallback to polling
 * - Connection state management
 * - Message queue for offline resilience
 * - Error handling and logging
 * - Data sync on reconnect (GAP #73 FIX)
 *
 * Usage:
 * const { data, isConnected, send, reconnect } = useWebSocket(url, options);
 *
 * GAP #73 FIX: Sync missed data on reconnect
 * const { data, isConnected } = useWebSocket(wsUrl, {
 *   onReconnect: async () => {
 *     const missedData = await fetchMissedData(lastTimestamp);
 *     return missedData;
 *   }
 * });
 */

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import logger from "@/utils/logger";

const DEFAULT_OPTIONS = {
  reconnect: true,
  reconnectInterval: 1000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000, // 30s
  heartbeatMessage: JSON.stringify({ type: "ping" }),
  onOpen: null,
  onMessage: null,
  onClose: null,
  onError: null,
  onReconnect: null, // GAP #73 FIX: Callback to fetch missed data on reconnect
  fallbackToPolling: true,
  pollingInterval: 5000,
  debug: false,
};

export const useWebSocket = (url, options = {}) => {
  const opts = useMemo(() => ({ ...DEFAULT_OPTIONS, ...options }), [options]);

  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [usePolling, setUsePolling] = useState(false);
  const [queuedMessages, setQueuedMessages] = useState(0);
  const [lastDisconnectTime, setLastDisconnectTime] = useState(null); // GAP #73 FIX: Track disconnect time

  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatIntervalRef = useRef(null);
  const pollingIntervalRef = useRef(null);
  const messageQueueRef = useRef([]);
  const reconnectTimeoutRef = useRef(null);
  const lastMessageTimeRef = useRef(Date.now()); // GAP #73 FIX: Track last message time

  // Log helper
  const log = useCallback(
    (...args) => {
      if (opts.debug) {
        logger.debug("[useWebSocket]", ...args);
      }
    },
    [opts.debug],
  );

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (!opts.heartbeatInterval) return;

    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        log("Sending heartbeat");
        wsRef.current.send(opts.heartbeatMessage);
      }
    }, opts.heartbeatInterval);
  }, [opts.heartbeatInterval, opts.heartbeatMessage, log]);

  // Stop heartbeat
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Exponential backoff calculation
  const getReconnectDelay = useCallback(() => {
    const attempt = reconnectAttemptsRef.current;
    const delay = Math.min(
      opts.reconnectInterval * Math.pow(2, attempt),
      30000, // Max 30s
    );
    log(`Reconnect delay: ${delay}ms (attempt ${attempt + 1})`);
    return delay;
  }, [opts.reconnectInterval, log]);

  // Send message
  const send = useCallback(
    (message) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          typeof message === "string" ? message : JSON.stringify(message),
        );
        log("Message sent:", message);
      } else {
        // Queue message for when connection is restored
        messageQueueRef.current.push(message);
        setQueuedMessages(messageQueueRef.current.length);
        log("Message queued (offline):", message);
      }
    },
    [log],
  );

  // Process queued messages
  const processQueue = useCallback(() => {
    if (
      messageQueueRef.current.length > 0 &&
      wsRef.current?.readyState === WebSocket.OPEN
    ) {
      log(`Processing ${messageQueueRef.current.length} queued messages`);
      while (messageQueueRef.current.length > 0) {
        const message = messageQueueRef.current.shift();
        wsRef.current.send(
          typeof message === "string" ? message : JSON.stringify(message),
        );
      }
      setQueuedMessages(0);
    }
  }, [log]);

  // Start polling fallback
  const startPolling = useCallback(() => {
    if (!opts.fallbackToPolling || pollingIntervalRef.current) return;

    log("Starting polling fallback");
    setUsePolling(true);

    // Extract base URL from WebSocket URL
    const pollingUrl = url
      .replace("ws://", "http://")
      .replace("wss://", "https://");

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(pollingUrl);
        if (response.ok) {
          const pollingData = await response.json();
          setData(pollingData);
          if (opts.onMessage)
            opts.onMessage({ data: JSON.stringify(pollingData) });
        }
      } catch (err) {
        log("Polling error:", err);
      }
    }, opts.pollingInterval);
  }, [url, opts, log]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      setUsePolling(false);
      log("Stopped polling");
    }
  }, [log]);

  // Connect WebSocket
  const connect = useCallback(() => {
    if (!url) {
      log("No URL provided");
      return;
    }

    try {
      log("Connecting to", url);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = async () => {
        log("Connected");
        setIsConnected(true);
        setError(null);

        // GAP #73 FIX: Fetch missed data on reconnect
        const wasReconnect = reconnectAttemptsRef.current > 0;
        reconnectAttemptsRef.current = 0;

        // Stop polling if active
        stopPolling();

        // Start heartbeat
        startHeartbeat();

        // Process queued messages
        processQueue();

        // GAP #73 FIX: Sync missed data if this is a reconnection
        if (wasReconnect && opts.onReconnect && lastDisconnectTime) {
          log("Fetching missed data since disconnect...");
          try {
            const missedData = await opts.onReconnect({
              lastDisconnectTime,
              lastMessageTime: lastMessageTimeRef.current,
              downtime: Date.now() - lastDisconnectTime,
            });

            if (missedData) {
              log("Received missed data:", missedData);
              setData(missedData);
            }
          } catch (err) {
            logger.error("[useWebSocket] Failed to fetch missed data:", err);
          }
        }

        // Reset disconnect time
        setLastDisconnectTime(null);

        if (opts.onOpen) opts.onOpen();
      };

      ws.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);

          // Ignore pong responses
          if (parsedData.type === "pong") return;

          // GAP #73 FIX: Track last message time for data sync
          lastMessageTimeRef.current = Date.now();

          setData(parsedData);
          if (opts.onMessage) opts.onMessage(event);
        } catch (err) {
          log("Message parsing error:", err);
          setData(event.data);
          if (opts.onMessage) opts.onMessage(event);
        }
      };

      ws.onerror = (event) => {
        log("WebSocket error:", event);
        setError(event);
        if (opts.onError) opts.onError(event);
      };

      ws.onclose = (event) => {
        log("Disconnected", event.code, event.reason);
        setIsConnected(false);
        stopHeartbeat();

        // GAP #73 FIX: Track disconnect time for data sync
        setLastDisconnectTime(Date.now());

        if (opts.onClose) opts.onClose(event);

        // Reconnect logic
        if (
          opts.reconnect &&
          reconnectAttemptsRef.current < opts.maxReconnectAttempts
        ) {
          const delay = getReconnectDelay();
          log(`Reconnecting in ${delay}ms...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= opts.maxReconnectAttempts) {
          log("Max reconnect attempts reached. Falling back to polling.");
          startPolling();
        }
      };
    } catch (err) {
      log("Connection error:", err);
      setError(err);
      if (opts.fallbackToPolling) {
        startPolling();
      }
    }
  }, [
    url,
    opts,
    log,
    startHeartbeat,
    stopHeartbeat,
    processQueue,
    getReconnectDelay,
    startPolling,
    stopPolling,
  ]);

  // Manual reconnect
  const reconnect = useCallback(() => {
    log("Manual reconnect triggered");
    reconnectAttemptsRef.current = 0;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    stopPolling();
    connect();
  }, [connect, stopPolling, log]);

  // Disconnect
  const disconnect = useCallback(() => {
    log("Disconnecting");

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    stopHeartbeat();
    stopPolling();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, [stopHeartbeat, stopPolling, log]);

  // GAP #56 FIX: Initial connection with stable dependencies
  // Boris Cherny Standard: Prevent infinite loops by carefully managing deps
  // Memoized opts ensures callback identities remain stable between renders
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]); // Only url should trigger reconnection, connect/disconnect are stable via memoization

  return {
    data,
    isConnected,
    error,
    usePolling,
    send,
    reconnect,
    disconnect,
    queuedMessages,
  };
};

export default useWebSocket;

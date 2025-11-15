/**
 * useRealTimeExecutions Hook
 * Real-time monitoring of offensive operations (scans, exploits, attacks)
 *
 * Uses optimized useWebSocket hook with:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat mechanism
 * - Polling fallback
 * - Message queueing
 *
 * SECURITY (Boris Cherny Standard):
 * - GAP #1 FIXED: Prevents state updates after unmount
 *
 * NO MOCKS - Real data from:
 * - WebSocket connection to Offensive Gateway
 * - Polling fallback for execution updates
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useWebSocket } from "../../../../hooks/useWebSocket";
import logger from "@/utils/logger";

import { WS_ENDPOINTS } from "../../../../config/api";
const GATEWAY_WS = WS_ENDPOINTS.executions;

export const useRealTimeExecutions = () => {
  const [executions, setExecutions] = useState([]);
  // GAP #1 FIX: Track component mount status
  const isMountedRef = useRef(true);

  // Use optimized WebSocket hook
  const { data: wsData, isConnected } = useWebSocket(GATEWAY_WS, {
    reconnect: true,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
    fallbackToPolling: true,
    pollingInterval: 3000,
    debug: process.env.NODE_ENV === "development",
  });

  const addExecution = useCallback((execution) => {
    // GAP #1 FIX: Only update state if component is still mounted
    if (!isMountedRef.current) return;

    setExecutions((prev) => {
      // Check if execution already exists
      const exists = prev.some((e) => e.id === execution.id);
      if (exists) {
        // Update existing execution
        return prev.map((e) => (e.id === execution.id ? execution : e));
      }
      // Add new execution (keep last 20)
      return [execution, ...prev].slice(0, 20);
    });
  }, []);

  const removeExecution = useCallback((executionId) => {
    // GAP #1 FIX: Only update state if component is still mounted
    if (!isMountedRef.current) return;

    setExecutions((prev) => prev.filter((e) => e.id !== executionId));
  }, []);

  // Handle WebSocket data
  useEffect(() => {
    if (!wsData || !isMountedRef.current) return;

    try {
      if (wsData.type === "execution_update") {
        addExecution(wsData.execution);
      } else if (wsData.type === "execution_complete") {
        // Update execution status
        addExecution({ ...wsData.execution, status: "completed" });
      } else if (wsData.type === "executions_list" && wsData.executions) {
        // Polling fallback data
        if (isMountedRef.current) {
          setExecutions(wsData.executions.slice(0, 20));
        }
      }
    } catch (err) {
      logger.error("Error processing execution data:", err);
    }
  }, [wsData, addExecution]);

  // GAP #1 FIX: Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return {
    executions,
    addExecution,
    removeExecution,
    isConnected,
  };
};

/**
import logger from '@/utils/logger';
 * useRealTimeExecutions Hook
 * Real-time monitoring of offensive operations (scans, exploits, attacks)
 *
 * Uses optimized useWebSocket hook with:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat mechanism
 * - Polling fallback
 * - Message queueing
 *
 * NO MOCKS - Real data from:
 * - WebSocket connection to Offensive Gateway
 * - Polling fallback for execution updates
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../../../../hooks/useWebSocket';

const GATEWAY_WS = 'ws://localhost:8037/ws/executions';

export const useRealTimeExecutions = () => {
  const [executions, setExecutions] = useState([]);

  // Use optimized WebSocket hook
  const { data: wsData, isConnected } = useWebSocket(GATEWAY_WS, {
    reconnect: true,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
    fallbackToPolling: true,
    pollingInterval: 3000,
    debug: process.env.NODE_ENV === 'development'
  });

  const addExecution = useCallback((execution) => {
    setExecutions(prev => {
      // Check if execution already exists
      const exists = prev.some(e => e.id === execution.id);
      if (exists) {
        // Update existing execution
        return prev.map(e => e.id === execution.id ? execution : e);
      }
      // Add new execution (keep last 20)
      return [execution, ...prev].slice(0, 20);
    });
  }, []);

  const removeExecution = useCallback((executionId) => {
    setExecutions(prev => prev.filter(e => e.id !== executionId));
  }, []);

  // Handle WebSocket data
  useEffect(() => {
    if (!wsData) return;

    try {
      if (wsData.type === 'execution_update') {
        addExecution(wsData.execution);
      } else if (wsData.type === 'execution_complete') {
        // Update execution status
        addExecution({ ...wsData.execution, status: 'completed' });
      } else if (wsData.type === 'executions_list' && wsData.executions) {
        // Polling fallback data
        setExecutions(wsData.executions.slice(0, 20));
      }
    } catch (err) {
      logger.error('Error processing execution data:', err);
    }
  }, [wsData, addExecution]);

  return {
    executions,
    addExecution,
    removeExecution,
    isConnected
  };
};

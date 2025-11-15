/**
 * useOffensiveExecutions Hook
 * ============================
 *
 * Real-time offensive operations execution updates
 * Uses WebSocketManager for centralized connection
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002
 */

import { useState, useCallback } from 'react';
import { useWebSocketManager } from './useWebSocketManager';
import logger from '@/utils/logger';

/**
 * Hook for real-time offensive execution updates
 *
 * @param {Object} options - Hook options
 * @param {boolean} options.enabled - Enable connection (default: true)
 * @param {Function} options.onExecution - Callback for new execution
 * @returns {Object} Executions state
 */
export const useOffensiveExecutions = ({ enabled = true, onExecution = null } = {}) => {
  const [executions, setExecutions] = useState([]);

  // Message handler
  const handleMessage = useCallback(
    (data) => {
      logger.debug('[useOffensiveExecutions] Message:', data.type);

      if (data.type === 'execution' || data.type === 'new_execution') {
        // Add new execution to list (keep last 50)
        setExecutions((prev) => [data.data || data, ...prev].slice(0, 50));

        if (onExecution) {
          onExecution(data.data || data);
        }
      } else if (data.type === 'execution_update') {
        // Update existing execution
        setExecutions((prev) =>
          prev.map((exec) =>
            exec.id === data.data?.id ? { ...exec, ...data.data } : exec
          )
        );
      }
    },
    [onExecution]
  );

  // Use WebSocketManager
  const { isConnected, status } = useWebSocketManager('offensive.executions', {
    enabled,
    onMessage: handleMessage,
    connectionOptions: {
      reconnect: true,
      heartbeatInterval: 30000,
    },
  });

  return {
    executions,
    isConnected,
    status,
  };
};

export default useOffensiveExecutions;

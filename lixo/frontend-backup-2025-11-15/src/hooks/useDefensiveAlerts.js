/**
 * useDefensiveAlerts Hook
 * ========================
 *
 * Real-time defensive security alerts
 * Uses WebSocketManager for centralized connection
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002
 */

import { useState, useCallback } from "react";
import { useWebSocketManager } from "./useWebSocketManager";
import logger from "@/utils/logger";

/**
 * Hook for real-time defensive alerts
 *
 * @param {Object} options - Hook options
 * @param {boolean} options.enabled - Enable connection (default: true)
 * @param {Function} options.onAlert - Callback for new alert
 * @returns {Object} Alerts state
 */
export const useDefensiveAlerts = ({ enabled = true, onAlert = null } = {}) => {
  const [alerts, setAlerts] = useState([]);

  // Message handler
  const handleMessage = useCallback(
    (data) => {
      logger.debug("[useDefensiveAlerts] Message:", data.type);

      if (data.type === "alert" || data.type === "new_alert") {
        // Add new alert to list (keep last 100)
        setAlerts((prev) => [data.data || data, ...prev].slice(0, 100));

        if (onAlert) {
          onAlert(data.data || data);
        }
      } else if (data.type === "alert_update") {
        // Update existing alert
        setAlerts((prev) =>
          prev.map((alert) =>
            alert.id === data.data?.id ? { ...alert, ...data.data } : alert,
          ),
        );
      } else if (data.type === "alert_resolved") {
        // Mark alert as resolved
        setAlerts((prev) =>
          prev.map((alert) =>
            alert.id === data.data?.id
              ? {
                  ...alert,
                  status: "resolved",
                  resolved_at: new Date().toISOString(),
                }
              : alert,
          ),
        );
      }
    },
    [onAlert],
  );

  // Use WebSocketManager
  const { isConnected, status } = useWebSocketManager("defensive.alerts", {
    enabled,
    onMessage: handleMessage,
    connectionOptions: {
      reconnect: true,
      heartbeatInterval: 30000,
    },
  });

  // Add alert manually (for testing/demo)
  const addAlert = useCallback((alert) => {
    setAlerts((prev) => [alert, ...prev].slice(0, 100));
  }, []);

  return {
    alerts,
    isConnected,
    status,
    addAlert,
  };
};

export default useDefensiveAlerts;

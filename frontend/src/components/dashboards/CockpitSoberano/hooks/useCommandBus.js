/**
 * useCommandBus - Sovereign Command & Control Hook
 * 
 * Handles C2L command execution (MUTE, ISOLATE, TERMINATE)
 * NO MOCKS - Real API calls to Command Bus Service
 * 
 * @version 1.0.0
 */

import { useState, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_COMMAND_BUS_API || 'http://localhost:8092';

const COMMAND_TYPES = {
  MUTE: 'MUTE',
  ISOLATE: 'ISOLATE',
  TERMINATE: 'TERMINATE'
};

export const useCommandBus = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastCommand, setLastCommand] = useState(null);

  const sendCommand = useCallback(async (commandType, targetAgents, parameters = {}) => {
    setLoading(true);
    setError(null);

    try {
      const payload = {
        command_type: commandType,
        target_agents: Array.isArray(targetAgents) ? targetAgents : [targetAgents],
        parameters,
        operator_id: localStorage.getItem('operatorId') || 'sovereign-operator',
        timestamp: new Date().toISOString()
      };

      const response = await axios.post(`${API_URL}/commands`, payload, {
        headers: {
          'Content-Type': 'application/json',
          'X-Operator-Role': 'SOVEREIGN_OPERATOR'
        },
        timeout: 10000
      });

      setLastCommand({
        id: response.data.id,
        type: commandType,
        targets: targetAgents,
        status: response.data.status,
        timestamp: new Date()
      });

      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Command failed';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const muteAgent = useCallback((agentId, duration = 300) => {
    return sendCommand(COMMAND_TYPES.MUTE, agentId, { duration_seconds: duration });
  }, [sendCommand]);

  const isolateAgent = useCallback((agentId, reason = 'Sovereign decision') => {
    return sendCommand(COMMAND_TYPES.ISOLATE, agentId, { reason });
  }, [sendCommand]);

  const terminateAgent = useCallback((agentId, cascade = false) => {
    return sendCommand(COMMAND_TYPES.TERMINATE, agentId, { cascade });
  }, [sendCommand]);

  const getCommandStatus = useCallback(async (commandId) => {
    try {
      const response = await axios.get(`${API_URL}/commands/${commandId}`);
      return response.data;
    } catch (err) {
      console.error('[CommandBus] Failed to get status:', err);
      throw err;
    }
  }, []);

  return {
    sendCommand,
    muteAgent,
    isolateAgent,
    terminateAgent,
    getCommandStatus,
    loading,
    error,
    lastCommand
  };
};

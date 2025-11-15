/**
 * useAllianceGraph - Real-time Alliance Network Hook
 * 
 * Fetches and maintains alliance graph data from Narrative Filter
 * NO MOCKS - Real API data
 * 
 * @version 1.0.0
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api';

const API_URL = API_ENDPOINTS.narrativeFilter;
const POLL_INTERVAL = 10000; // 10 seconds

export const useAllianceGraph = () => {
  const [graphData, setGraphData] = useState({
    nodes: [],
    edges: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchGraph = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/alliances/graph`, {
        timeout: 5000
      });

      const { nodes, edges } = response.data;

      setGraphData({
        nodes: nodes.map(node => ({
          id: node.agent_id,
          label: node.agent_name,
          status: node.status,
          threat_level: node.threat_level || 0,
          last_activity: node.last_activity
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.agent_a,
          target: edge.agent_b,
          strength: edge.strength,
          type: edge.alliance_type || 'COOPERATIVE'
        }))
      });

      setError(null);
    } catch (err) {
      logger.error('[AllianceGraph] Failed to fetch:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGraph();

    const interval = setInterval(fetchGraph, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchGraph]);

  return { graphData, loading, error, refresh: fetchGraph };
};

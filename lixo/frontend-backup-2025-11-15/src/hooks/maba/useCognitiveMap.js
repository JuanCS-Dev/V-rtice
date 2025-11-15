/**
 * useCognitiveMap - MABA Cognitive Map Hook
 *
 * Fetches and queries the Neo4j cognitive map (graph of learned web pages).
 * Returns nodes (pages) and edges (links/navigations) for D3.js visualization.
 *
 * Port: 8155
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @param {Object} query - Query parameters (domain, url_pattern, limit)
 * @param {Object} options - Hook options (pollingInterval, enabled)
 * @returns {Object} { graph, isLoading, error, refetch }
 */

import { useState, useEffect, useCallback } from 'react';
import { mabaService } from '../../services/maba/mabaService';
import logger from '../../utils/logger';

const DEFAULT_POLLING_INTERVAL = 60000; // 60s (less frequent, large data)

export const useCognitiveMap = (query = {}, options = {}) => {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    enabled = true,
  } = options;

  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCognitiveMap = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);
      const response = await mabaService.queryCognitiveMap(query);

      // Transform response to D3.js format if needed
      const graphData = {
        nodes: response.nodes || response.pages || [],
        edges: response.edges || response.links || [],
      };

      setGraph(graphData);
      setIsLoading(false);
      logger.debug('[useCognitiveMap] Graph updated:', {
        nodes: graphData.nodes.length,
        edges: graphData.edges.length,
      });
    } catch (err) {
      logger.error('[useCognitiveMap] Failed to fetch cognitive map:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [enabled, JSON.stringify(query)]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchCognitiveMap();

    // Periodic polling
    const interval = setInterval(fetchCognitiveMap, pollingInterval);

    return () => clearInterval(interval);
  }, [enabled, pollingInterval, fetchCognitiveMap]);

  return {
    graph,
    nodes: graph.nodes,
    edges: graph.edges,
    nodeCount: graph.nodes.length,
    edgeCount: graph.edges.length,
    isLoading,
    error,
    refetch: fetchCognitiveMap,
  };
};

export default useCognitiveMap;

/**
 * useBrowserSessions - MABA Browser Sessions Hook
 *
 * Fetches and monitors active browser sessions.
 * Provides methods to create, close, and manage browser sessions.
 *
 * Port: 8155
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @param {Object} options - Hook options (pollingInterval, enabled)
 * @returns {Object} { sessions, isLoading, error, createSession, closeSession, refetch }
 */

import { useState, useEffect, useCallback } from 'react';
import { mabaService } from '../../services/maba/mabaService';
import logger from '../../utils/logger';

const DEFAULT_POLLING_INTERVAL = 10000; // 10s (more frequent for real-time monitoring)

export const useBrowserSessions = (options = {}) => {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    enabled = true,
  } = options;

  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSessions = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);
      const response = await mabaService.listSessions();
      setSessions(response);
      setIsLoading(false);
      logger.debug(`[useBrowserSessions] Fetched ${response.length} sessions`);
    } catch (err) {
      logger.error('[useBrowserSessions] Failed to fetch sessions:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchSessions();

    // Periodic polling
    const interval = setInterval(fetchSessions, pollingInterval);

    return () => clearInterval(interval);
  }, [enabled, pollingInterval, fetchSessions]);

  // Create new browser session
  const createSession = useCallback(async (sessionOptions = {}) => {
    try {
      const newSession = await mabaService.createSession(sessionOptions);
      logger.info('[useBrowserSessions] Session created:', newSession.session_id);

      // Refresh sessions list
      await fetchSessions();

      return newSession;
    } catch (err) {
      logger.error('[useBrowserSessions] Failed to create session:', err);
      throw err;
    }
  }, [fetchSessions]);

  // Close browser session
  const closeSession = useCallback(async (sessionId) => {
    try {
      await mabaService.closeSession(sessionId);
      logger.info('[useBrowserSessions] Session closed:', sessionId);

      // Refresh sessions list
      await fetchSessions();
    } catch (err) {
      logger.error('[useBrowserSessions] Failed to close session:', err);
      throw err;
    }
  }, [fetchSessions]);

  return {
    sessions,
    activeSessions: sessions.filter(s => s.status === 'active'),
    sessionCount: sessions.length,
    isLoading,
    error,
    createSession,
    closeSession,
    refetch: fetchSessions,
  };
};

export default useBrowserSessions;

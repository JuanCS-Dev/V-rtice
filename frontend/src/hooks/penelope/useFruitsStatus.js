/**
 * useFruitsStatus - 9 Frutos do Espírito Status Hook
 *
 * Fetches and monitors the status of the 9 Fruits of the Spirit (Gálatas 5:22-23):
 * - ❤️ Agape (Amor)
 * - 😊 Chara (Alegria)
 * - 🕊️ Eirene (Paz)
 * - 💪 Enkrateia (Domínio Próprio)
 * - 🤝 Pistis (Fidelidade)
 * - 🐑 Praotes (Mansidão)
 * - 🙏 Tapeinophrosyne (Humildade)
 * - 📖 Aletheia (Verdade)
 * - 🦉 Sophia (Sabedoria)
 *
 * Port: 8154
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @param {Object} options - Hook options (pollingInterval, enabled)
 * @returns {Object} { fruits, isLoading, error, overallScore, refetch }
 */

import { useState, useEffect, useCallback } from 'react';
import { penelopeService } from '../../services/penelope/penelopeService';
import logger from '../../utils/logger';

const DEFAULT_POLLING_INTERVAL = 30000; // 30s

export const useFruitsStatus = (options = {}) => {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    enabled = true,
  } = options;

  const [fruits, setFruits] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFruits = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);
      const response = await penelopeService.getFruitsStatus();
      setFruits(response.fruits || response);
      setIsLoading(false);
      logger.debug('[useFruitsStatus] Fruits status updated:', response);
    } catch (err) {
      logger.error('[useFruitsStatus] Failed to fetch fruits:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchFruits();

    // Periodic polling
    const interval = setInterval(fetchFruits, pollingInterval);

    return () => clearInterval(interval);
  }, [enabled, pollingInterval, fetchFruits]);

  // Calculate overall score (average of all 9 fruits)
  const overallScore = fruits
    ? Math.round(
        Object.values(fruits).reduce((sum, fruit) => sum + (fruit.score || 0), 0) / 9
      )
    : 0;

  return {
    fruits,
    isLoading,
    error,
    overallScore,
    refetch: fetchFruits,
  };
};

export default useFruitsStatus;

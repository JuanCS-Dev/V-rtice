import { useState, useCallback } from 'react';
import { searchBreachData } from '../../../../api/worldClassTools';

/**
 * Custom hook for the breach data search logic.
 * Manages state for query, queryType, loading, results, and errors.
 */
export const useBreachDataSearch = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (query, queryType) => {
    // Validate input
    if (!query?.trim()) {
      setError('O campo de busca é obrigatório');
      return;
    }

    // Reset state and start loading
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await searchBreachData(query.trim(), { queryType });
      setResult(response.result);
    } catch (err) {
      setError(err.message || 'Erro ao buscar dados de vazamento');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    result,
    loading,
    error,
    search,
    reset
  };
};

export default useBreachDataSearch;
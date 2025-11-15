import { useState, useCallback } from "react";

/**
 * Custom hook for handling API calls with loading and error states
 *
 * @param {Function} apiFunction - The API function to execute
 * @returns {Object} - { data, loading, error, execute, reset }
 *
 * @example
 * const { data, loading, error, execute } = useApi(searchExploits);
 *
 * const handleSearch = async () => {
 *   try {
 *     const result = await execute('CVE-2021-44228');
 *     logger.debug(result);
 *   } catch (err) {
 *     logger.error(err);
 *   }
 * };
 */
export const useApi = (apiFunction) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);
      setData(null);

      try {
        const result = await apiFunction(...args);
        setData(result);
        return result;
      } catch (err) {
        const errorMessage = err.message || "Erro desconhecido";
        setError(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction],
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
};

export default useApi;

import { useState, useCallback } from "react";
import logger from "@/utils/logger";

/**
 * Hook customizado para chamadas API com retry, timeout e error handling
 *
 * @param {Object} options - Configurações do hook
 * @param {number} options.maxRetries - Número máximo de tentativas (default: 3)
 * @param {number} options.retryDelay - Delay entre retries em ms (default: 1000)
 * @param {number} options.timeout - Timeout da requisição em ms (default: 30000)
 *
 * @returns {Object} - { data, loading, error, execute, reset }
 */
export const useApiCall = (options = {}) => {
  const { maxRetries = 3, retryDelay = 1000, timeout = 30000 } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Executa fetch com timeout
   */
  const fetchWithTimeout = useCallback(
    async (url, options) => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      try {
        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response;
      } catch (err) {
        clearTimeout(timeoutId);
        if (err.name === "AbortError") {
          throw new Error(`Request timeout after ${timeout}ms`);
        }
        throw err;
      }
    },
    [timeout],
  );

  /**
   * Sleep helper para retry delay
   */
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  /**
   * Executa a chamada API com retry logic
   */
  const execute = useCallback(
    async (url, fetchOptions = {}) => {
      setLoading(true);
      setError(null);

      let lastError = null;
      let attempt = 0;

      while (attempt < maxRetries) {
        try {
          logger.debug(
            `[API Call] Attempt ${attempt + 1}/${maxRetries}: ${url}`,
          );

          const response = await fetchWithTimeout(url, fetchOptions);

          if (!response.ok) {
            // Erro HTTP
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

            try {
              const errorData = await response.json();
              errorMessage =
                errorData.detail || errorData.message || errorMessage;
            } catch (e) {
              // Não conseguiu parsear JSON do erro
            }

            throw new Error(errorMessage);
          }

          // Sucesso!
          const result = await response.json();
          setData(result);
          setLoading(false);
          logger.debug(`[API Call] Success: ${url}`);
          return result;
        } catch (err) {
          logger.error(`[API Call] Error on attempt ${attempt + 1}:`, err);
          lastError = err;
          attempt++;

          // Se não é a última tentativa, espera antes de retry
          if (attempt < maxRetries) {
            logger.debug(`[API Call] Retrying in ${retryDelay}ms...`);
            await sleep(retryDelay * attempt); // Exponential backoff
          }
        }
      }

      // Todas as tentativas falharam
      const finalError = {
        message: lastError?.message || "API call failed",
        status: lastError?.status,
        attempts: maxRetries,
        timestamp: new Date().toISOString(),
      };

      setError(finalError);
      setLoading(false);
      logger.error(
        `[API Call] Failed after ${maxRetries} attempts:`,
        finalError,
      );

      throw lastError;
    },
    [maxRetries, retryDelay, fetchWithTimeout],
  );

  /**
   * Reset do estado
   */
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

/**
 * Hook específico para GET requests
 */
export const useApiGet = (url, options = {}) => {
  const apiCall = useApiCall(options);

  const execute = useCallback(() => {
    return apiCall.execute(url, { method: "GET" });
  }, [url, apiCall]);

  return {
    ...apiCall,
    execute,
  };
};

/**
 * Hook específico para POST requests
 */
export const useApiPost = (url, options = {}) => {
  const apiCall = useApiCall(options);

  const execute = useCallback(
    (body) => {
      return apiCall.execute(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
    },
    [url, apiCall],
  );

  return {
    ...apiCall,
    execute,
  };
};

export default useApiCall;

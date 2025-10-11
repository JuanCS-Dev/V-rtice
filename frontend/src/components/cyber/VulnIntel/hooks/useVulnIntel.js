import { useState, useCallback } from 'react';
import logger from '@/utils/logger';
import {
  searchCVE as apiSearchCVE,
  searchVulnerabilities,
  getExploits as apiGetExploits,
  correlateWithScan as apiCorrelate,
} from '../../../../api/offensiveServices';

/**
 * useVulnIntel - Hook para Vulnerability Intelligence
 *
 * Gerencia buscas de CVE, exploits e correlação
 */
export const useVulnIntel = () => {
  const [currentCVE, setCurrentCVE] = useState(null);
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [exploits, setExploits] = useState([]);
  const [correlationResults, setCorrelationResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Busca CVE específica por ID
   */
  const searchCVE = useCallback(async (cveId) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiSearchCVE(cveId);

      if (result.success) {
        setCurrentCVE(result.cve || result.data || result);
        setVulnerabilities([]); // Limpa lista de vulnerabilidades
        return result;
      } else {
        setError(result.error);
        setCurrentCVE(null);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error searching CVE:', err);
      setError(err.message);
      setCurrentCVE(null);
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Busca vulnerabilidades por query
   */
  const searchVulns = useCallback(async (query, filters = {}) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await searchVulnerabilities(query, filters);

      if (result.success) {
        setVulnerabilities(result.vulnerabilities || result.data || []);
        setCurrentCVE(null); // Limpa CVE atual
        return result;
      } else {
        setError(result.error);
        setVulnerabilities([]);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error searching vulnerabilities:', err);
      setError(err.message);
      setVulnerabilities([]);
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Busca exploits disponíveis para CVE
   */
  const getExploits = useCallback(async (cveId) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiGetExploits(cveId);

      if (result.success) {
        setExploits(result.exploits || result.data || []);
        return result;
      } else {
        setError(result.error);
        setExploits([]);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error getting exploits:', err);
      setError(err.message);
      setExploits([]);
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Correlaciona vulnerabilidades com scan
   */
  const correlateWithScan = useCallback(async (scanId) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiCorrelate(scanId);

      if (result.success) {
        setCorrelationResults(result.correlation || result.data || result);
        setVulnerabilities(result.vulnerabilities || []);
        return result;
      } else {
        setError(result.error);
        setCorrelationResults(null);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error correlating with scan:', err);
      setError(err.message);
      setCorrelationResults(null);
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Limpa resultados
   */
  const clearResults = useCallback(() => {
    setCurrentCVE(null);
    setVulnerabilities([]);
    setExploits([]);
    setCorrelationResults(null);
    setError(null);
  }, []);

  return {
    currentCVE,
    vulnerabilities,
    exploits,
    correlationResults,
    isLoading,
    error,
    searchCVE,
    searchVulns,
    getExploits,
    correlateWithScan,
    clearResults,
  };
};

export default useVulnIntel;

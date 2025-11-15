import { useState, useCallback } from 'react';
import logger from '@/utils/logger';
import {
  scanWebTarget,
  runWebTest,
  getWebScanReport,
} from '../../../../api/offensiveServices';

/**
 * useWebAttack - Hook para Web Attack Surface
 *
 * Gerencia scans web, testes individuais e relatórios
 */
export const useWebAttack = () => {
  const [currentScan, setCurrentScan] = useState(null);
  const [scans, setScans] = useState([]);
  const [scanResults, setScanResults] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Inicia scan completo de web attack surface
   */
  const startScan = useCallback(async (url, scanProfile = 'full', authConfig = null) => {
    setIsScanning(true);
    setError(null);

    try {
      const result = await scanWebTarget(url, scanProfile, authConfig);

      if (result.success) {
        setCurrentScan(result);
        setScanResults(result.results || result);

        // Adiciona aos scans
        setScans(prev => [...prev, {
          scan_id: result.scan_id || Date.now(),
          url,
          scan_profile: scanProfile,
          status: 'completed',
          started_at: new Date().toISOString(),
          vulnerabilities_found: result.vulnerabilities?.length || 0,
        }]);

        return { success: true, scanId: result.scan_id };
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error starting web scan:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsScanning(false);
    }
  }, []);

  /**
   * Executa teste específico (SQLi, XSS, etc)
   */
  const runTest = useCallback(async (url, testType, params = {}) => {
    setIsScanning(true);
    setError(null);

    try {
      const result = await runWebTest(url, testType, params);

      if (result.success) {
        return result;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error running web test:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsScanning(false);
    }
  }, []);

  /**
   * Obtém relatório completo de scan
   */
  const getReport = useCallback(async (scanId) => {
    setIsScanning(true);
    setError(null);

    try {
      const result = await getWebScanReport(scanId);

      if (result.success) {
        setScanResults(result.report || result);
        setCurrentScan(result);
        return result;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error getting scan report:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsScanning(false);
    }
  }, []);

  /**
   * Limpa resultados
   */
  const clearResults = useCallback(() => {
    setCurrentScan(null);
    setScanResults(null);
    setError(null);
  }, []);

  return {
    currentScan,
    scans,
    scanResults,
    isScanning,
    error,
    startScan,
    runTest,
    getReport,
    clearResults,
  };
};

export default useWebAttack;

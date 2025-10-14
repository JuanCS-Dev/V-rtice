import { useState, useEffect, useCallback } from 'react';
import logger from '@/utils/logger';
import {
  scanNetwork,
  getScanStatus,
  listScans,
  discoverHosts,
} from '../../../../api/offensiveServices';

/**
 * useNetworkRecon - Hook para Network Reconnaissance
 *
 * Gerencia scans, polling de status, e histórico
 */
export const useNetworkRecon = () => {
  const [scans, setScans] = useState([]);
  const [activeScans, setActiveScans] = useState([]);
  const [currentScan, setCurrentScan] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Carrega lista de scans
   */
  const loadScans = useCallback(async () => {
    try {
      const result = await listScans(50);
      if (result.success) {
        setScans(result.scans || []);

        // Separa scans ativos
        const active = (result.scans || []).filter(
          s => s.status === 'running' || s.status === 'pending'
        );
        setActiveScans(active);
      }
    } catch (err) {
      logger.error('Error loading scans:', err);
      setError(err.message);
    }
  }, []);

  /**
   * Atualiza status de scan específico
   */
  const updateScanStatus = useCallback(async (scanId) => {
    try {
      const result = await getScanStatus(scanId);

      if (result.success) {
        // Atualiza na lista
        setScans(prev =>
          prev.map(s =>
            s.scan_id === scanId
              ? { ...s, ...result }
              : s
          )
        );

        // Remove dos ativos se completou
        if (result.status === 'completed' || result.status === 'failed') {
          setActiveScans(prev =>
            prev.filter(s => s.scan_id !== scanId)
          );
        }

        // Atualiza current scan se for o mesmo
        if (currentScan?.scan_id === scanId) {
          setCurrentScan(prev => ({ ...prev, ...result }));
        }
      }
    } catch (err) {
      logger.error('Error updating scan status:', err);
    }
  }, [currentScan]);

  // Carrega lista de scans ao montar
  useEffect(() => {
    loadScans();
  }, [loadScans]);

  // Polling para scans ativos
  useEffect(() => {
    if (activeScans.length === 0) return;

    const interval = setInterval(() => {
      activeScans.forEach(scan => {
        updateScanStatus(scan.scan_id);
      });
    }, 3000); // Poll a cada 3 segundos

    return () => clearInterval(interval);
  }, [activeScans, updateScanStatus]);

  /**
   * Inicia novo scan
   */
  const startScan = useCallback(async (target, scanType, ports) => {
    setIsScanning(true);
    setError(null);

    try {
      const result = await scanNetwork(target, scanType, ports);

      if (result.success) {
        setCurrentScan(result);

        // Adiciona aos scans ativos
        setActiveScans(prev => [...prev, {
          scan_id: result.scan_id,
          target: result.target,
          status: 'running',
          started_at: new Date().toISOString(),
        }]);

        // Recarrega lista
        await loadScans();

        return { success: true, scanId: result.scan_id };
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error starting scan:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsScanning(false);
    }
  }, [loadScans]);

  /**
   * Obtém detalhes completos de um scan
   */
  const getScanDetails = useCallback(async (scanId) => {
    try {
      const result = await getScanStatus(scanId);
      if (result.success) {
        setCurrentScan(result);
        return result;
      }
    } catch (err) {
      logger.error('Error getting scan details:', err);
      setError(err.message);
    }
  }, []);

  /**
   * Descobre hosts em rede
   */
  const discover = useCallback(async (network) => {
    setIsScanning(true);
    setError(null);

    try {
      const result = await discoverHosts(network);

      if (result.success) {
        return result;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error discovering hosts:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsScanning(false);
    }
  }, []);

  /**
   * Refresh manual
   */
  const refreshScans = useCallback(() => {
    loadScans();
  }, [loadScans]);

  return {
    scans,
    activeScans,
    currentScan,
    isScanning,
    error,
    startScan,
    getScanDetails,
    updateScanStatus,
    discover,
    refreshScans,
  };
};

export default useNetworkRecon;

import { useState, useEffect, useCallback } from 'react';
import logger from '@/utils/logger';

const API_BASE = 'http://localhost:8000';

const ENDPOINTS = [
  { endpoint: '/cyber/port-analysis', key: 'portAnalysis' },
  { endpoint: '/cyber/file-integrity', key: 'fileIntegrity' },
  { endpoint: '/cyber/process-analysis', key: 'processAnalysis' },
  { endpoint: '/cyber/security-config', key: 'securityConfig' },
  { endpoint: '/cyber/security-logs', key: 'securityLogs' }
];

export const useSystemSecurity = () => {
  const [securityData, setSecurityData] = useState({
    portAnalysis: null,
    fileIntegrity: null,
    processAnalysis: null,
    securityConfig: null,
    securityLogs: null
  });

  const [loading, setLoading] = useState({});
  const [lastUpdate, setLastUpdate] = useState(null);

  /**
   * Busca dados de um endpoint específico
   */
  const fetchSecurityData = useCallback(async (endpoint, key) => {
    setLoading(prev => ({ ...prev, [key]: true }));
    try {
      const response = await fetch(`${API_BASE}${endpoint}`);
      const data = await response.json();

      if (data.success) {
        setSecurityData(prev => ({ ...prev, [key]: data.data }));
      } else {
        logger.error(`Erro em ${endpoint}:`, data.errors);
      }
    } catch (error) {
      logger.error(`Erro ao buscar ${endpoint}:`, error);
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  }, []);

  /**
   * Carrega todos os dados de segurança em paralelo
   */
  const loadAllSecurityData = useCallback(async () => {
    setLastUpdate(new Date());

    await Promise.all(
      ENDPOINTS.map(({ endpoint, key }) => fetchSecurityData(endpoint, key))
    );
  }, [fetchSecurityData]);

  // Carrega dados iniciais
  useEffect(() => {
    loadAllSecurityData();
  }, [loadAllSecurityData]);

  return {
    securityData,
    loading,
    lastUpdate,
    refresh: loadAllSecurityData
  };
};

export default useSystemSecurity;

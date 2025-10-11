import { useState, useEffect, useCallback } from 'react';
import logger from '@/utils/logger';
import {
  runAttackSimulation,
  listAttackTechniques,
  validatePurpleTeam as apiValidatePurpleTeam,
  getAttackCoverage,
} from '../../../../api/offensiveServices';

/**
 * useBAS - Hook para Breach & Attack Simulation
 *
 * Gerencia simulações MITRE ATT&CK e validação Purple Team
 */
export const useBAS = () => {
  const [techniques, setTechniques] = useState([]);
  const [simulations, setSimulations] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [error, setError] = useState(null);

  // Carrega técnicas ao montar
  useEffect(() => {
    loadTechniques();
    loadCoverage();
  }, []);

  /**
   * Carrega técnicas MITRE ATT&CK disponíveis
   */
  const loadTechniques = useCallback(async (tactic = null, platform = null) => {
    try {
      const result = await listAttackTechniques(tactic, platform);

      if (result.success) {
        setTechniques(result.techniques || result.data || []);
      }
    } catch (err) {
      logger.error('Error loading techniques:', err);
      setError(err.message);
    }
  }, []);

  /**
   * Carrega coverage ATT&CK
   */
  const loadCoverage = useCallback(async () => {
    try {
      const result = await getAttackCoverage();

      if (result.success) {
        setCoverage(result.coverage || result.data || result);
      }
    } catch (err) {
      logger.error('Error loading coverage:', err);
      setError(err.message);
    }
  }, []);

  /**
   * Executa simulação de ataque
   */
  const runSimulation = useCallback(async (techniqueId, targetHost, platform, params = {}) => {
    setIsSimulating(true);
    setError(null);

    try {
      const result = await runAttackSimulation(techniqueId, targetHost, platform, params);

      if (result.success) {
        // Adiciona simulação à lista
        const newSimulation = {
          simulation_id: result.simulation_id || Date.now(),
          technique_id: techniqueId,
          target_host: targetHost,
          platform,
          status: result.status || 'completed',
          detected: result.detected,
          timestamp: new Date().toISOString(),
          ...result,
        };

        setSimulations(prev => [...prev, newSimulation]);

        // Atualiza coverage
        await loadCoverage();

        return { success: true, simulation: newSimulation };
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error running simulation:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsSimulating(false);
    }
  }, [loadCoverage]);

  /**
   * Valida simulação com Purple Team (correlação com telemetria)
   */
  const validatePurpleTeam = useCallback(async (simulationId, telemetrySources) => {
    setIsSimulating(true);
    setError(null);

    try {
      const result = await apiValidatePurpleTeam(simulationId, telemetrySources);

      if (result.success) {
        // Atualiza simulação com resultados de detecção
        setSimulations(prev =>
          prev.map(s =>
            s.simulation_id === simulationId
              ? {
                  ...s,
                  detected: result.detected,
                  telemetry: result.telemetry,
                  validation_timestamp: new Date().toISOString(),
                }
              : s
          )
        );

        return result;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error validating purple team:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsSimulating(false);
    }
  }, []);

  /**
   * Obtém coverage atualizado
   */
  const getCoverage = useCallback(async (organizationId = null) => {
    setIsSimulating(true);
    setError(null);

    try {
      const result = await getAttackCoverage(organizationId);

      if (result.success) {
        setCoverage(result.coverage || result.data || result);
        return result;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error('Error getting coverage:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsSimulating(false);
    }
  }, []);

  /**
   * Refresh manual
   */
  const refreshTechniques = useCallback(() => {
    loadTechniques();
    loadCoverage();
  }, [loadTechniques, loadCoverage]);

  return {
    techniques,
    simulations,
    coverage,
    isSimulating,
    error,
    runSimulation,
    validatePurpleTeam,
    getCoverage,
    loadTechniques,
    refreshTechniques,
  };
};

export default useBAS;

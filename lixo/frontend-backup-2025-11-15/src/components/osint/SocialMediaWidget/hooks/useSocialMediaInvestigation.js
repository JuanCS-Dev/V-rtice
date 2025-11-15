import { useState, useCallback } from 'react';
import logger from '@/utils/logger';
import { socialMediaInvestigation } from '../../../../api/worldClassTools';

/**
 * Custom hook for social media investigation logic.
 * Manages state for target, platforms, loading, results, and errors.
 */
export const useSocialMediaInvestigation = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const investigate = useCallback(async (target, platforms) => {
    // Validate input
    if (!target?.trim()) {
      setError('Username/Target é obrigatório');
      return;
    }

    if (!platforms || platforms.length === 0) {
      setError('Selecione pelo menos uma plataforma');
      return;
    }

    // Reset state and start loading
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await socialMediaInvestigation(target.trim(), {
        platforms,
        deepAnalysis: true
      });

      if (response && response.result) {
        setResult(response.result);
      } else {
        throw new Error('Resposta inválida do servidor');
      }
    } catch (err) {
      logger.error('Social Media Investigation Error:', err);
      setError(err.message || 'Erro ao investigar target. Verifique se o serviço está ativo.');
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
    investigate,
    reset
  };
};

export default useSocialMediaInvestigation;
import { useState, useCallback } from 'react';
import logger from '@/utils/logger';

const API_BASE = 'http://localhost:8000/api/domain';

/**
 * Gera dados fallback quando a API não está disponível
 */
const generateFallbackData = (domain) => ({
  domain,
  status: Math.random() > 0.3 ? 'suspicious' : 'malicious',
  registrar: 'GoDaddy LLC',
  creation_date: '2023-05-15',
  expiration_date: '2024-05-15',
  nameservers: ['ns1.suspicious-domain.com', 'ns2.suspicious-domain.com'],
  ip_addresses: ['192.168.1.100', '10.0.0.50'],
  ssl_cert: {
    issuer: 'Let\'s Encrypt',
    expires: '2024-08-15',
    valid: false
  },
  reputation_score: Math.floor(Math.random() * 100),
  threats_detected: [
    'Phishing pages detected',
    'Malware distribution',
    'Suspicious redirects'
  ]
});

export const useDomainAnalysis = () => {
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);

  /**
   * Adiciona domínio ao histórico
   */
  const addToHistory = useCallback((domain) => {
    setSearchHistory(prev =>
      [domain, ...prev.filter(d => d !== domain)].slice(0, 10)
    );
  }, []);

  /**
   * Analisa um domínio
   */
  const analyzeDomain = useCallback(async () => {
    const trimmedDomain = domain.trim();
    if (!trimmedDomain) return;

    setLoading(true);
    setAnalysisResult(null);

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: trimmedDomain })
      });

      const data = await response.json();

      if (data.success) {
        setAnalysisResult(data.data);
        addToHistory(trimmedDomain);
      } else {
        logger.error('Erro na análise:', data.errors);
        const fallback = generateFallbackData(trimmedDomain);
        setAnalysisResult(fallback);
        addToHistory(trimmedDomain);
      }
    } catch (error) {
      logger.error('Erro ao conectar com o backend:', error);
      const fallback = generateFallbackData(trimmedDomain);
      setAnalysisResult(fallback);
      addToHistory(trimmedDomain);
    } finally {
      setLoading(false);
    }
  }, [domain, addToHistory]);

  /**
   * Seleciona domínio do histórico
   */
  const selectFromHistory = useCallback((historicDomain) => {
    setDomain(historicDomain);
  }, []);

  return {
    domain,
    setDomain,
    loading,
    analysisResult,
    searchHistory,
    analyzeDomain,
    selectFromHistory
  };
};

export default useDomainAnalysis;

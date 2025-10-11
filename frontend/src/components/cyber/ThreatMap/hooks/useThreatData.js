import { useState, useEffect, useCallback } from 'react';
import logger from '@/utils/logger';
import { checkThreatIntelligence, analyzeIP } from '../../../../api/cyberServices';

/**
 * Custom hook for managing threat data - INTEGRADO COM SERVIÇOS REAIS
 * Combina dados de threat_intel_service + ip_intelligence_service
 */
export const useThreatData = () => {
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    severity: [],
    type: [],
    timeRange: '24h'
  });

  /**
   * Gera lista de IPs suspeitos conhecidos para análise
   * OTIMIZADO: Reduzido para apenas IPs relevantes
   */
  const getKnownThreatsIPs = useCallback(() => {
    // Apenas IPs de threat feeds conhecidos (OTIMIZADO)
    return [
      '185.220.101.23', // Tor exit node
      '45.142.212.61',  // Known botnet
      '89.248.165.201', // Malware C2
      '185.234.218.27', // Phishing
      '104.244.76.61',  // Twitter phishing
      '8.8.8.8',        // Google DNS (teste)
      '1.1.1.1',        // Cloudflare DNS (teste)
      // Reduzido de 20 para 5 IPs aleatórios
      ...Array.from({ length: 5 }, () =>
        `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
      )
    ];
  }, []);

  const fetchThreats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const ipsToAnalyze = getKnownThreatsIPs();
      const threats = [];

      // OTIMIZADO: Reduzido batch size de 10 para 5 e com timeout
      const batchSize = 5;
      const timeout = 8000; // 8 segundos timeout por batch

      for (let i = 0; i < ipsToAnalyze.length; i += batchSize) {
        const batch = ipsToAnalyze.slice(i, i + batchSize);

        const batchResults = await Promise.race([
          Promise.all(
            batch.map(async (ip) => {
              try {
                // OTIMIZADO: Apenas uma chamada (analyzeIP já retorna threat info)
                const ipData = await analyzeIP(ip);

                // Se não tem geolocalização, pula
                if (!ipData.success || !ipData.geolocation) {
                  return null;
                }

                // Determina severidade baseada no reputation score
                const score = ipData.reputation?.score || 50;
                let severity = 'low';
                if (score >= 80) severity = 'critical';
                else if (score >= 60) severity = 'high';
                else if (score >= 40) severity = 'medium';

                // Tipo baseado em heurística simples
                const type = ipData.ptr_record?.includes('tor') ? 'tor' :
                             score < 40 ? 'malicious' : 'unknown';

                return {
                  id: `threat_${ip}`,
                  lat: ipData.geolocation.lat,
                  lng: ipData.geolocation.lon,
                  severity,
                  type,
                  timestamp: new Date().toISOString(),
                  source: ip,
                  description: ipData.reputation?.threat_level || 'Unknown threat',
                  country: ipData.geolocation.country,
                  city: ipData.geolocation.city,
                  isp: ipData.geolocation.isp,
                  asn: ipData.geolocation.asn,
                  threatScore: score,
                  isMalicious: score < 50,
                  confidence: score > 70 ? 'high' : score > 40 ? 'medium' : 'low'
                };
              } catch (error) {
                logger.error(`Failed to analyze ${ip}:`, error);
                return null;
              }
            })
          ),
          // Timeout protection
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Batch timeout')), timeout)
          )
        ]).catch(err => {
          logger.warn('Batch failed:', err.message);
          return [];
        });

        // Filtra nulls e adiciona à lista
        const validThreats = (batchResults || []).filter(t => t !== null);
        threats.push(...validThreats);

        // Atualiza progressivamente para feedback visual
        if (validThreats.length > 0) {
          setThreats([...threats]);
        }
      }

      logger.debug(`Loaded ${threats.length} threats from real services`);

    } catch (err) {
      logger.error('Error fetching threats:', err);
      setError(err.message || 'Erro ao carregar ameaças. Serviços de threat intelligence podem estar offline.');

      // Graceful degradation: retorna lista vazia em vez de mocks
      // UI deve mostrar empty state apropriado baseado em error !== null
      setThreats([]);
    } finally {
      setLoading(false);
    }
  }, [getKnownThreatsIPs]);

  useEffect(() => {
    fetchThreats();
  }, [fetchThreats]);

  const filteredThreats = threats.filter(threat => {
    if (filters.severity.length > 0 && !filters.severity.includes(threat.severity)) {
      return false;
    }
    if (filters.type.length > 0 && !filters.type.includes(threat.type)) {
      return false;
    }
    return true;
  });

  return {
    threats: filteredThreats,
    loading,
    error,
    filters,
    setFilters,
    refresh: fetchThreats
  };
};

export default useThreatData;

import { useState, useEffect, useCallback } from 'react';
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
   * Em produção, isso viria de um feed de threat intelligence
   */
  const getKnownThreatsIPs = useCallback(() => {
    // IPs de threat feeds conhecidos (exemplo)
    // Em produção: buscar de um feed real ou database
    return [
      '185.220.101.23', // Tor exit node
      '45.142.212.61',  // Known botnet
      '89.248.165.201', // Malware C2
      '185.234.218.27', // Phishing
      '104.244.76.61',  // Twitter phishing
      '8.8.8.8',        // Google DNS (teste - clean)
      '1.1.1.1',        // Cloudflare DNS (teste - clean)
      // Adiciona IPs aleatórios para visualização
      ...Array.from({ length: 20 }, () =>
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

      // Analisa cada IP (em paralelo, limitado a 10 por vez para não sobrecarregar)
      const batchSize = 10;
      for (let i = 0; i < ipsToAnalyze.length; i += batchSize) {
        const batch = ipsToAnalyze.slice(i, i + batchSize);

        const batchResults = await Promise.all(
          batch.map(async (ip) => {
            try {
              // Busca dados de geolocalização
              const ipData = await analyzeIP(ip);

              // Busca threat intelligence
              const threatData = await checkThreatIntelligence(ip, 'ip');

              // Se não tem geolocalização, pula
              if (!ipData.success || !ipData.geolocation) {
                return null;
              }

              // Determina severidade baseada no threat score
              let severity = 'low';
              if (threatData.success) {
                const score = threatData.threatScore;
                if (score >= 80) severity = 'critical';
                else if (score >= 60) severity = 'high';
                else if (score >= 40) severity = 'medium';
              }

              // Determina tipo baseado nas categorias
              const categories = threatData.success ? threatData.categories : [];
              const type = categories[0] || 'unknown';

              return {
                id: `threat_${ip}`,
                lat: ipData.geolocation.lat,
                lng: ipData.geolocation.lon,
                severity,
                type,
                timestamp: new Date().toISOString(),
                source: ip,
                description: threatData.success ? threatData.reputation : 'Unknown threat',
                country: ipData.geolocation.country,
                city: ipData.geolocation.city,
                isp: ipData.geolocation.isp,
                asn: ipData.geolocation.asn,
                threatScore: threatData.success ? threatData.threatScore : 0,
                isMalicious: threatData.success ? threatData.isMalicious : false,
                confidence: threatData.success ? threatData.confidence : 'low',
                recommendations: threatData.success ? threatData.recommendations : []
              };
            } catch (error) {
              console.error(`Failed to analyze ${ip}:`, error);
              return null;
            }
          })
        );

        // Filtra nulls e adiciona à lista
        threats.push(...batchResults.filter(t => t !== null));

        // Atualiza progressivamente para feedback visual
        setThreats([...threats]);
      }

      console.log(`Loaded ${threats.length} threats from real services`);

    } catch (err) {
      console.error('Error fetching threats:', err);
      setError(err.message || 'Erro ao carregar ameaças');

      // Fallback: dados mock se serviços estiverem offline
      const mockThreats = Array.from({ length: 30 }, (_, i) => ({
        id: i,
        lat: -23.5505 + (Math.random() - 0.5) * 20,
        lng: -46.6333 + (Math.random() - 0.5) * 20,
        severity: ['critical', 'high', 'medium', 'low'][Math.floor(Math.random() * 4)],
        type: ['malware', 'botnet', 'phishing', 'ddos', 'exploit'][Math.floor(Math.random() * 5)],
        timestamp: new Date().toISOString(),
        source: `IP ${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
        description: 'Simulated threat (services offline)',
        country: 'Unknown',
        city: 'Unknown',
        threatScore: Math.floor(Math.random() * 100),
        isMalicious: Math.random() > 0.5
      }));
      setThreats(mockThreats);
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

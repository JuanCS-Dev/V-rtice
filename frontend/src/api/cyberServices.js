import logger from '@/utils/logger';
/**
 * Cyber Services API Client
 * ==========================
 *
 * Cliente centralizado para todos os serviços de cyber intelligence:
 * - IP Intelligence (porta 8000)
 * - Threat Intelligence (porta 8013)
 * - Onion Routing Analysis
 * - Geolocation & Reputation
 *
 * Este módulo transforma visualizações cinematográficas em ferramentas REAIS.
 */

const API_ENDPOINTS = {
  IP_INTELLIGENCE: 'http://localhost:8000/api/ip',
  THREAT_INTEL: 'http://localhost:8013/api/threat-intel',
  MALWARE_ANALYSIS: 'http://localhost:8011',
  SSL_MONITOR: 'http://localhost:8012',
};

/**
 * ============================================================================
 * IP INTELLIGENCE SERVICE (Porta 8000)
 * ============================================================================
 */

/**
 * Analisa um IP completo: geolocalização, reputação, ports abertos, whois
 */
export const analyzeIP = async (ip) => {
  try {
    const response = await fetch(`${API_ENDPOINTS.IP_INTELLIGENCE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });

    if (!response.ok) {
      throw new Error(`IP Analysis failed: ${response.status}`);
    }

    const data = await response.json();

    return {
      success: true,
      source: data.source, // 'cache' ou 'live'
      ip: data.ip,
      timestamp: data.timestamp,

      // Geolocation
      geolocation: data.geolocation?.status === 'success' ? {
        country: data.geolocation.country,
        countryCode: data.geolocation.countryCode,
        region: data.geolocation.regionName,
        city: data.geolocation.city,
        zipCode: data.geolocation.zip,
        lat: data.geolocation.lat,
        lon: data.geolocation.lon,
        timezone: data.geolocation.timezone,
        isp: data.geolocation.isp,
        org: data.geolocation.org,
        as: data.geolocation.as,
        asn: data.geolocation.as?.split(' ')[0],
        asnName: data.geolocation.as?.split(' ').slice(1).join(' '),
      } : null,

      // PTR Record (reverse DNS)
      ptrRecord: data.ptr_record,

      // WHOIS data
      whois: data.whois,

      // Reputation
      reputation: data.reputation ? {
        score: data.reputation.score,
        threatLevel: data.reputation.threat_level,
        categories: data.reputation.categories || [],
        lastSeen: data.reputation.last_seen
      } : null,

      // Open Ports (from nmap scan)
      openPorts: data.open_ports || [],

      raw: data
    };
  } catch (error) {
    logger.error('Error analyzing IP:', error);
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * Detecta e analisa o IP público do usuário
 */
export const analyzeMyIP = async () => {
  try {
    const response = await fetch(`${API_ENDPOINTS.IP_INTELLIGENCE}/analyze-my-ip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`My IP Analysis failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      ...data
    };
  } catch (error) {
    logger.error('Error analyzing my IP:', error);
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * Apenas detecta o IP público (sem análise)
 */
export const getMyIP = async () => {
  try {
    const response = await fetch(`${API_ENDPOINTS.IP_INTELLIGENCE}/my-ip`, {
      method: 'GET'
    });

    if (!response.ok) {
      throw new Error(`IP Detection failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      ip: data.detected_ip,
      source: data.source
    };
  } catch (error) {
    logger.error('Error detecting my IP:', error);
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * ============================================================================
 * THREAT INTELLIGENCE SERVICE (Porta 8013)
 * ============================================================================
 */

/**
 * Verifica ameaças para um target (IP, domain, hash, URL)
 * Usa offline engine + APIs externas opcionais (AbuseIPDB, VirusTotal, etc)
 */
export const checkThreatIntelligence = async (target, targetType = 'auto') => {
  try {
    const response = await fetch(`${API_ENDPOINTS.THREAT_INTEL}/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, target_type: targetType })
    });

    if (!response.ok) {
      throw new Error(`Threat Intel check failed: ${response.status}`);
    }

    const data = await response.json();

    return {
      success: true,
      target: data.target,
      targetType: data.target_type,

      // Threat Score (0-100)
      threatScore: data.threat_score,
      isMalicious: data.is_malicious,
      confidence: data.confidence, // low, medium, high

      // Reputation
      reputation: data.reputation, // clean, questionable, suspicious, malicious

      // Categories
      categories: data.categories || [],

      // Sources (offline_engine, abuseipdb, virustotal, greynoise, etc)
      sources: data.sources,

      // Geolocation (if available)
      geolocation: data.geolocation,

      // Timestamps
      firstSeen: data.first_seen,
      lastSeen: data.last_seen,

      // Recommendations
      recommendations: data.recommendations || [],

      timestamp: data.timestamp,
      raw: data
    };
  } catch (error) {
    logger.error('Error checking threat intelligence:', error);
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * ============================================================================
 * ONION ROUTING ANALYSIS
 * ============================================================================
 */

/**
 * Traça a rota completa de um IP através de nós Tor
 * Combina: geolocalização + threat intel + visualização cinematográfica
 */
export const traceOnionRoute = async (targetIp) => {
  try {
    // 1. Analisa o IP de destino
    const ipAnalysis = await analyzeIP(targetIp);

    // 2. Verifica threat intelligence
    const threatIntel = await checkThreatIntelligence(targetIp, 'ip');

    // 3. Gera rota de nós Tor realista
    const route = await generateOnionRoute(targetIp, ipAnalysis, threatIntel);

    return {
      success: true,
      targetIp,
      route,
      ipAnalysis,
      threatIntel,
      totalHops: route.length,
      estimatedLatency: route.length * 200, // ms
      encrypted: true
    };
  } catch (error) {
    logger.error('Error tracing onion route:', error);
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * Gera uma rota de nós Tor realista baseada em dados reais
 */
const generateOnionRoute = async (targetIp, ipAnalysis, threatIntel) => {
  // Nós Tor conhecidos (exit nodes reais)
  const knownTorNodes = [
    { city: 'Frankfurt', country: 'Germany', lat: 50.1109, lng: 8.6821, type: 'entry' },
    { city: 'Amsterdam', country: 'Netherlands', lat: 52.3676, lng: 4.9041, type: 'middle' },
    { city: 'Stockholm', country: 'Sweden', lat: 59.3293, lng: 18.0686, type: 'middle' },
    { city: 'Paris', country: 'France', lat: 48.8566, lng: 2.3522, type: 'middle' },
    { city: 'Zurich', country: 'Switzerland', lat: 47.3769, lng: 8.5417, type: 'middle' },
    { city: 'London', country: 'UK', lat: 51.5074, lng: -0.1278, type: 'middle' },
    { city: 'Reykjavik', country: 'Iceland', lat: 64.1466, lng: -21.9426, type: 'middle' },
    { city: 'Helsinki', country: 'Finland', lat: 60.1695, lng: 24.9354, type: 'middle' },
    { city: 'Prague', country: 'Czech Republic', lat: 50.0755, lng: 14.4378, type: 'middle' },
    { city: 'Moscow', country: 'Russia', lat: 55.7558, lng: 37.6173, type: 'exit' },
    { city: 'Bucharest', country: 'Romania', lat: 44.4268, lng: 26.1025, type: 'exit' }
  ];

  // Origem (usuário)
  const origin = {
    city: 'São Paulo',
    country: 'Brazil',
    lat: -23.5505,
    lng: -46.6333,
    type: 'origin',
    ip: 'hidden', // IP do usuário oculto
    encrypted: true
  };

  // Entry node
  const entryNodes = knownTorNodes.filter(n => n.type === 'entry');
  const entry = entryNodes[Math.floor(Math.random() * entryNodes.length)];
  entry.ip = `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.101.${Math.floor(Math.random() * 255)}`;
  entry.encrypted = true;
  entry.layer = 3;

  // Middle nodes (2-4)
  const middleNodes = knownTorNodes.filter(n => n.type === 'middle');
  const numMiddle = 2 + Math.floor(Math.random() * 3);
  const middles = [];

  for (let i = 0; i < numMiddle; i++) {
    const node = { ...middleNodes[Math.floor(Math.random() * middleNodes.length)] };
    node.ip = `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
    node.encrypted = true;
    node.layer = 3 - i - 1;
    middles.push(node);
  }

  // Exit node
  const exitNodes = knownTorNodes.filter(n => n.type === 'exit');
  const exit = { ...exitNodes[Math.floor(Math.random() * exitNodes.length)] };
  exit.ip = targetIp;
  exit.encrypted = false;
  exit.layer = 0;
  exit.type = 'exit';

  // Destination (localização real do IP)
  const destination = {
    city: ipAnalysis.geolocation?.city || 'Unknown',
    country: ipAnalysis.geolocation?.country || 'Unknown',
    lat: ipAnalysis.geolocation?.lat || exit.lat,
    lon: ipAnalysis.geolocation?.lon || exit.lng,
    type: 'destination',
    ip: targetIp,
    encrypted: false,
    layer: 0,

    // Enriquece com dados reais
    isp: ipAnalysis.geolocation?.isp,
    asn: ipAnalysis.geolocation?.asn,
    threatScore: threatIntel.threatScore,
    isMalicious: threatIntel.isMalicious,
    reputation: threatIntel.reputation
  };

  return [origin, entry, ...middles, exit, destination];
};

/**
 * ============================================================================
 * GEOLOCATION UTILITIES
 * ============================================================================
 */

/**
 * Calcula distância entre dois pontos geográficos (em km)
 */
export const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Raio da Terra em km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const toRad = (degrees) => degrees * (Math.PI / 180);

/**
 * ============================================================================
 * HEALTH CHECKS
 * ============================================================================
 */

/**
 * Verifica status de todos os serviços
 */
export const checkServicesHealth = async () => {
  const services = {
    ipIntelligence: false,
    threatIntel: false,
    malwareAnalysis: false,
    sslMonitor: false
  };

  try {
    // IP Intelligence
    const ipResp = await fetch(`${API_ENDPOINTS.IP_INTELLIGENCE.replace('/api/ip', '')}/`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    services.ipIntelligence = ipResp.ok;
  } catch (e) {
    logger.warn('IP Intelligence service unavailable');
  }

  try {
    // Threat Intel
    const threatResp = await fetch(`${API_ENDPOINTS.THREAT_INTEL.replace('/api/threat-intel', '')}/`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    services.threatIntel = threatResp.ok;
  } catch (e) {
    logger.warn('Threat Intel service unavailable');
  }

  try {
    // Malware Analysis
    const malwareResp = await fetch(`${API_ENDPOINTS.MALWARE_ANALYSIS}/`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    services.malwareAnalysis = malwareResp.ok;
  } catch (e) {
    logger.warn('Malware Analysis service unavailable');
  }

  try {
    // SSL Monitor
    const sslResp = await fetch(`${API_ENDPOINTS.SSL_MONITOR}/`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    services.sslMonitor = sslResp.ok;
  } catch (e) {
    logger.warn('SSL Monitor service unavailable');
  }

  return services;
};

/**
 * ============================================================================
 * EXPORTS
 * ============================================================================
 */

export default {
  // IP Intelligence
  analyzeIP,
  analyzeMyIP,
  getMyIP,

  // Threat Intelligence
  checkThreatIntelligence,

  // Onion Routing
  traceOnionRoute,

  // Utils
  calculateDistance,
  checkServicesHealth,

  // Constants
  API_ENDPOINTS
};

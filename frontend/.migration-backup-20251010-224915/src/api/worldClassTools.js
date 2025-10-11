/**
 * World-Class Tools API Client
 *
 * Cliente para integração com as 17 NSA-grade tools do Maximus 2.0
 * Backend: ai_agent_service (porta 8017)
 */

const AI_AGENT_BASE_URL = 'http://localhost:8017';

/**
 * Executa uma World-Class Tool
 *
 * @param {string} toolName - Nome da tool (ex: 'exploit_search')
 * @param {object} toolInput - Parâmetros de entrada
 * @returns {Promise<object>} Resultado com status, confidence, data
 */
export const executeTool = async (toolName, toolInput) => {
  try {
    const response = await fetch(`${AI_AGENT_BASE_URL}/tools/world-class/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tool_name: toolName,
        tool_input: toolInput
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`[WorldClassTools] Error executing ${toolName}:`, error);
    throw error;
  }
};

/**
 * Executa múltiplas World-Class Tools em paralelo
 *
 * @param {Array<{tool_name: string, tool_input: object, priority?: number}>} executions
 * @param {boolean} failFast - Para no primeiro erro
 * @returns {Promise<object>} Resultados + summary + orchestrator stats
 */
export const executeParallel = async (executions, failFast = false) => {
  try {
    const response = await fetch(`${AI_AGENT_BASE_URL}/tools/world-class/execute-parallel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        executions,
        fail_fast: failFast
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[WorldClassTools] Error executing parallel:', error);
    throw error;
  }
};

/**
 * Obtém catálogo completo de World-Class Tools
 *
 * @returns {Promise<object>} Catálogo organizado por categoria
 */
export const getToolCatalog = async () => {
  try {
    const response = await fetch(`${AI_AGENT_BASE_URL}/tools/world-class`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[WorldClassTools] Error fetching catalog:', error);
    throw error;
  }
};

/**
 * Obtém estatísticas do Tool Orchestrator
 *
 * @returns {Promise<object>} Stats (executions, success rate, cache hit rate)
 */
export const getOrchestratorStats = async () => {
  try {
    const response = await fetch(`${AI_AGENT_BASE_URL}/tools/orchestrator/stats`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[WorldClassTools] Error fetching stats:', error);
    throw error;
  }
};

// ============================================
// CYBER SECURITY TOOLS (6)
// ============================================

/**
 * CVE Exploit Search
 * Busca exploits conhecidos para um CVE
 */
export const searchExploits = async (cveId, options = {}) => {
  return executeTool('exploit_search', {
    cve_id: cveId,
    include_poc: options.includePoc ?? true,
    include_metasploit: options.includeMetasploit ?? true
  });
};

/**
 * DNS Enumeration
 * Análise profunda de DNS com security scoring
 */
export const enumerateDNS = async (domain, options = {}) => {
  return executeTool('dns_enumeration', {
    domain,
    check_dnssec: options.checkDnssec ?? true,
    check_blacklists: options.checkBlacklists ?? true
  });
};

/**
 * Subdomain Discovery
 * Descobre subdomínios usando múltiplas técnicas
 */
export const discoverSubdomains = async (domain, options = {}) => {
  return executeTool('subdomain_discovery', {
    domain,
    methods: options.methods ?? ['certificate_transparency', 'brute_force'],
    wordlist_size: options.wordlistSize ?? 'medium'
  });
};

/**
 * Web Crawler
 * Crawling inteligente com tech fingerprinting
 */
export const crawlWebsite = async (url, options = {}) => {
  return executeTool('web_crawler', {
    url,
    max_depth: options.maxDepth ?? 3,
    follow_external: options.followExternal ?? false
  });
};

/**
 * JavaScript Analysis
 * Detecta secrets/API keys em código JS
 */
export const analyzeJavaScript = async (url, options = {}) => {
  return executeTool('javascript_analysis', {
    url,
    scan_type: options.scanType ?? 'deep'
  });
};

/**
 * Container Scan
 * Escaneia containers Docker/K8s
 */
export const scanContainer = async (image, options = {}) => {
  return executeTool('container_scan', {
    image,
    check_compliance: options.checkCompliance ?? ['CIS', 'HIPAA']
  });
};

// ============================================
// OSINT TOOLS (2)
// ============================================

/**
 * Social Media Deep Dive
 * OSINT em 20+ plataformas sociais
 */
export const socialMediaInvestigation = async (target, options = {}) => {
  return executeTool('social_media_deep_dive', {
    target,
    platforms: options.platforms ?? ['twitter', 'linkedin', 'github'],
    deep_analysis: options.deepAnalysis ?? true
  });
};

/**
 * Breach Data Search
 * Busca em 12B+ registros de vazamentos
 */
export const searchBreachData = async (query, options = {}) => {
  return executeTool('breach_data_search', {
    query,
    query_type: options.queryType ?? 'email'
  });
};

// ============================================
// ANALYTICS TOOLS (5)
// ============================================

/**
 * Pattern Recognition
 * Detecta padrões usando ML (clustering)
 */
export const recognizePatterns = async (data, options = {}) => {
  return executeTool('pattern_recognition', {
    data,
    algorithm: options.algorithm ?? 'kmeans',
    n_clusters: options.nClusters ?? 5
  });
};

/**
 * Anomaly Detection
 * Detecta anomalias usando statistical + ML
 */
export const detectAnomalies = async (data, options = {}) => {
  return executeTool('anomaly_detection', {
    data,
    method: options.method ?? 'isolation_forest',
    sensitivity: options.sensitivity ?? 0.05
  });
};

/**
 * Time Series Analysis
 * Forecasting com confidence intervals
 */
export const analyzeTimeSeries = async (data, options = {}) => {
  return executeTool('time_series_analysis', {
    data,
    forecast_horizon: options.forecastHorizon ?? 30,
    confidence_level: options.confidenceLevel ?? 0.95
  });
};

/**
 * Graph Analysis
 * Análise de grafos (redes, relações)
 */
export const analyzeGraph = async (nodes, edges, options = {}) => {
  return executeTool('graph_analysis', {
    nodes,
    edges
  });
};

/**
 * NLP Entity Extraction
 * Named Entity Recognition
 */
export const extractEntities = async (text, options = {}) => {
  return executeTool('nlp_entity_extraction', {
    text,
    language: options.language ?? 'en'
  });
};

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Verifica se um resultado é acionável (confidence >= 70%)
 */
export const isResultActionable = (result) => {
  return result.is_actionable === true || result.confidence >= 70;
};

/**
 * Obtém badge de confidence level
 */
export const getConfidenceBadge = (confidence) => {
  if (confidence >= 90) return { label: 'VERY HIGH', color: '#00ff00', icon: '🟢' };
  if (confidence >= 75) return { label: 'HIGH', color: '#00ffff', icon: '🔵' };
  if (confidence >= 50) return { label: 'MEDIUM', color: '#ffaa00', icon: '🟡' };
  if (confidence >= 25) return { label: 'LOW', color: '#ff4000', icon: '🟠' };
  return { label: 'VERY LOW', color: '#ff0040', icon: '🔴' };
};

/**
 * Formata tempo de execução
 */
export const formatExecutionTime = (ms) => {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
};

/**
 * Parse severity para cor
 */
export const getSeverityColor = (severity) => {
  const colors = {
    'CRITICAL': '#ff0040',
    'HIGH': '#ff4000',
    'MEDIUM': '#ffaa00',
    'LOW': '#00aa00',
    'INFO': '#00aaff'
  };
  return colors[severity] || colors.INFO;
};

export default {
  // Core
  executeTool,
  executeParallel,
  getToolCatalog,
  getOrchestratorStats,

  // Cyber Security
  searchExploits,
  enumerateDNS,
  discoverSubdomains,
  crawlWebsite,
  analyzeJavaScript,
  scanContainer,

  // OSINT
  socialMediaInvestigation,
  searchBreachData,

  // Analytics
  recognizePatterns,
  detectAnomalies,
  analyzeTimeSeries,
  analyzeGraph,
  extractEntities,

  // Utils
  isResultActionable,
  getConfidenceBadge,
  formatExecutionTime,
  getSeverityColor
};
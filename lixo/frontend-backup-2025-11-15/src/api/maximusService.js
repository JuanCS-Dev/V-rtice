import { API_BASE_URL } from "@/config/api";
import logger from "@/utils/logger";
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MAXIMUS API SERVICE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Cliente HTTP para comunicação com MAXIMUS Integration Service (port 8099)
 *
 * Endpoints:
 * - Health check
 * - Oráculo (self-improvement)
 * - Eureka (malware analysis)
 * - Integration workflows
 */

const MAXIMUS_BASE_URL = API_BASE_URL;

/**
 * Generic API request handler
 */
const apiRequest = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `API Error: ${response.status}`);
    }

    return {
      success: true,
      data: data.status === "success" ? data.data : data,
      message: data.message,
    };
  } catch (error) {
    logger.error(`MAXIMUS API Error [${endpoint}]:`, error);
    return {
      success: false,
      error: error.message,
    };
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Check MAXIMUS Integration Service health
 */
export const checkMaximusHealth = async () => {
  return apiRequest("/health");
};

// ═══════════════════════════════════════════════════════════════════════════
// ORÁCULO ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Run Oráculo self-improvement analysis
 *
 * @param {Object} config
 * @param {string|null} config.focusCategory - Category to focus on (security, performance, etc.)
 * @param {number} config.maxSuggestions - Max suggestions to generate (1-20)
 * @param {number} config.minConfidence - Minimum confidence threshold (0.0-1.0)
 * @param {boolean} config.dryRun - If true, only analyze without implementing
 */
export const runOraculoAnalysis = async (config = {}) => {
  return apiRequest("/api/v1/oraculo/analyze", {
    method: "POST",
    body: JSON.stringify({
      focus_category: config.focusCategory || null,
      max_suggestions: config.maxSuggestions || 5,
      min_confidence: config.minConfidence || 0.8,
      dry_run: config.dryRun !== undefined ? config.dryRun : true,
    }),
  });
};

/**
 * Get pending approvals (suggestions waiting for human review)
 */
export const getOraculoPendingApprovals = async () => {
  return apiRequest("/api/v1/oraculo/pending-approvals");
};

/**
 * Approve a pending suggestion
 *
 * @param {string} suggestionId - ID of the suggestion to approve
 */
export const approveOraculoSuggestion = async (suggestionId) => {
  return apiRequest(`/api/v1/oraculo/approve/${suggestionId}`, {
    method: "POST",
  });
};

/**
 * Get Oráculo statistics
 */
export const getOraculoStats = async () => {
  return apiRequest("/api/v1/oraculo/stats");
};

// ═══════════════════════════════════════════════════════════════════════════
// EUREKA ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Analyze file with Eureka
 *
 * @param {Object} config
 * @param {string} config.filePath - Path to the file to analyze
 * @param {boolean} config.generatePlaybook - Generate ADR playbook
 */
export const analyzeFileWithEureka = async (config) => {
  return apiRequest("/api/v1/eureka/analyze", {
    method: "POST",
    body: JSON.stringify({
      file_path: config.filePath,
      generate_playbook:
        config.generatePlaybook !== undefined ? config.generatePlaybook : true,
    }),
  });
};

/**
 * Get Eureka statistics
 */
export const getEurekaStats = async () => {
  return apiRequest("/api/v1/eureka/stats");
};

/**
 * Get available malicious patterns
 */
export const getEurekaPatterns = async () => {
  return apiRequest("/api/v1/eureka/patterns");
};

// ═══════════════════════════════════════════════════════════════════════════
// SUPPLY CHAIN GUARDIAN
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Run Supply Chain Guardian scan
 *
 * @param {Object} config
 * @param {string} config.repositoryPath - Path to repository
 * @param {boolean} config.scanDependencies - Scan dependencies
 * @param {boolean} config.analyzeCode - Analyze code for malicious patterns
 * @param {boolean} config.autoFix - Auto-fix issues
 */
export const runSupplyChainScan = async (config) => {
  return apiRequest("/api/v1/supply-chain/scan", {
    method: "POST",
    body: JSON.stringify({
      repository_path: config.repositoryPath,
      scan_dependencies:
        config.scanDependencies !== undefined ? config.scanDependencies : true,
      analyze_code:
        config.analyzeCode !== undefined ? config.analyzeCode : true,
      auto_fix: config.autoFix !== undefined ? config.autoFix : false,
    }),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// INTEGRATION WORKFLOWS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Execute complete Analyze & Respond workflow
 * (EUREKA → ADR Core → Auto Response)
 *
 * @param {string} filePath - Path to file to analyze
 */
export const analyzeAndRespond = async (filePath) => {
  return apiRequest("/api/v1/integration/analyze-and-respond", {
    method: "POST",
    body: JSON.stringify({ file_path: filePath }),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Check if MAXIMUS services are available
 */
export const isMaximusAvailable = async () => {
  const health = await checkMaximusHealth();
  return health.success && health.data.status === "healthy";
};

/**
 * Get all MAXIMUS services status
 */
export const getMaximusServicesStatus = async () => {
  const health = await checkMaximusHealth();
  if (health.success) {
    return {
      available: true,
      services: health.data.services,
      version: health.data.version,
      uptime: health.data.uptime_seconds,
    };
  }
  return {
    available: false,
    services: {},
  };
};

export default {
  // Health
  checkMaximusHealth,
  isMaximusAvailable,
  getMaximusServicesStatus,

  // Oráculo
  runOraculoAnalysis,
  getOraculoPendingApprovals,
  approveOraculoSuggestion,
  getOraculoStats,

  // Eureka
  analyzeFileWithEureka,
  getEurekaStats,
  getEurekaPatterns,

  // Supply Chain
  runSupplyChainScan,

  // Integration
  analyzeAndRespond,
};

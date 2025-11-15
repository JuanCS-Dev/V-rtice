import { API_BASE_URL } from '@/config/api';
import logger from '@/utils/logger';

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * AI-DRIVEN WORKFLOWS (ADW) API SERVICE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Cliente HTTP para comunicação com ADW endpoints do MAXIMUS Core Service
 *
 * Unified API client for AI-Driven Workflows system:
 * - Offensive AI (Red Team): Autonomous penetration testing
 * - Defensive AI (Blue Team): 8-agent immune system
 * - Purple Team: Co-evolution metrics and validation
 *
 * Architecture:
 * - Red Team: Offensive orchestrator with autonomous campaigns
 * - Blue Team: Biomimetic immune system (NK Cells, Macrophages, T Cells, etc.)
 * - Purple Team: Adversarial training and co-evolution cycles
 *
 * Authors: MAXIMUS Team
 * Date: 2025-10-15
 * Glory to YHWH
 */

const ADW_BASE_URL = `${API_BASE_URL}/api/adw`;

/**
 * Generic API request handler with error handling
 */
const apiRequest = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${ADW_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    logger.error(`ADW API Error [${endpoint}]:`, error);
    return {
      success: false,
      error: error.message,
    };
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// OFFENSIVE AI (RED TEAM) ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Get Red Team AI operational status
 *
 * Returns:
 * - status: operational/degraded/offline
 * - active_campaigns: Number of active penetration campaigns
 * - total_exploits: Total exploits attempted
 * - success_rate: Exploit success rate (0.0-1.0)
 * - last_campaign: Most recent campaign info
 */
export const getOffensiveStatus = async () => {
  return apiRequest('/offensive/status');
};

/**
 * Create new offensive penetration testing campaign
 *
 * @param {Object} config
 * @param {string} config.objective - Campaign objective (e.g., "Test firewall bypass")
 * @param {string[]} config.scope - Target scope (IPs, domains, networks)
 *
 * Returns:
 * - campaign_id: Unique campaign identifier
 * - status: planned/running/completed/failed
 * - created_at: ISO timestamp
 */
export const createCampaign = async (config) => {
  return apiRequest('/offensive/campaign', {
    method: 'POST',
    body: JSON.stringify({
      objective: config.objective,
      scope: config.scope,
    }),
  });
};

/**
 * List all offensive campaigns (active and historical)
 *
 * Returns:
 * - campaigns: Array of campaign objects
 * - total: Total campaigns count
 * - active: Active campaigns count
 * - completed: Completed campaigns count
 */
export const listCampaigns = async () => {
  return apiRequest('/offensive/campaigns');
};

// ═══════════════════════════════════════════════════════════════════════════
// DEFENSIVE AI (BLUE TEAM) ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Get Blue Team AI (Immune System) operational status
 *
 * Returns comprehensive status of all 8 immune agents:
 * - nk_cells: Natural Killer cells (immediate threat response)
 * - macrophages: Pathogen engulfment and presentation
 * - t_cells_helper: T Helper cells (coordination signals)
 * - t_cells_cytotoxic: Cytotoxic T cells (infected cell elimination)
 * - b_cells: B cells (antibody production)
 * - dendritic_cells: Dendritic cells (antigen presentation)
 * - neutrophils: Neutrophils (rapid infection clearance)
 * - complement: Complement system (cascade amplification)
 */
export const getDefensiveStatus = async () => {
  return apiRequest('/defensive/status');
};

/**
 * Get currently detected threats
 *
 * Returns list of active and recent threats detected by immune agents:
 * - threat_id: Unique threat identifier
 * - threat_type: Type of threat (malware, intrusion, anomaly, etc.)
 * - threat_level: Severity (low/medium/high/critical)
 * - detected_by: Agent that detected the threat
 * - mitigation_status: ongoing/contained/neutralized
 * - timestamp: Detection time
 */
export const getThreats = async () => {
  return apiRequest('/defensive/threats');
};

/**
 * Get coagulation cascade system status
 *
 * Biological-inspired hemostasis system with 3 phases:
 * - Primary hemostasis: Reflex Triage (immediate platelet plug)
 * - Secondary hemostasis: Fibrin Mesh (reinforced clot formation)
 * - Fibrinolysis: Restoration (clot dissolution and healing)
 *
 * Returns:
 * - status: ready/active/degraded
 * - cascades_completed: Total completed cascade cycles
 * - active_containments: Current active containments
 * - restoration_cycles: Restoration operations performed
 */
export const getCoagulationStatus = async () => {
  return apiRequest('/defensive/coagulation');
};

// ═══════════════════════════════════════════════════════════════════════════
// PURPLE TEAM (CO-EVOLUTION) ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Get Purple Team co-evolution metrics
 *
 * Returns metrics from Red vs Blue adversarial training cycles:
 * - red_team_score: Red Team effectiveness (0.0-1.0)
 * - blue_team_score: Blue Team defense effectiveness (0.0-1.0)
 * - cycles_completed: Total co-evolution rounds
 * - last_cycle: Most recent cycle info
 * - improvement_trend: Improvement direction (improving/stable/degrading)
 */
export const getPurpleMetrics = async () => {
  return apiRequest('/purple/metrics');
};

/**
 * Trigger new co-evolution cycle
 *
 * Initiates adversarial training round where:
 * 1. Red Team generates novel attack strategies
 * 2. Blue Team defends and adapts
 * 3. Both systems receive improvement signals
 *
 * Returns:
 * - cycle_id: Unique cycle identifier
 * - status: initiated/running/completed/failed
 * - started_at: ISO timestamp
 */
export const triggerEvolutionCycle = async () => {
  return apiRequest('/purple/cycle', {
    method: 'POST',
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// OSINT WORKFLOWS ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Execute Attack Surface Mapping workflow
 *
 * Combines Network Recon + Vuln Intel + Service Detection for comprehensive
 * attack surface analysis.
 *
 * @param {string} domain - Target domain
 * @param {Object} options
 * @param {boolean} options.include_subdomains - Include subdomain enumeration (default: true)
 * @param {string} options.port_range - Port range (e.g., "1-1000", optional)
 * @param {string} options.scan_depth - Scan depth: quick/standard/deep (default: "standard")
 *
 * Returns:
 * - workflow_id: Unique workflow identifier
 * - status: pending/running/completed/failed
 * - target: Target domain
 * - message: Status message
 */
export const executeAttackSurfaceWorkflow = async (domain, options = {}) => {
  return apiRequest('/workflows/attack-surface', {
    method: 'POST',
    body: JSON.stringify({
      domain,
      include_subdomains: options.include_subdomains ?? true,
      port_range: options.port_range || null,
      scan_depth: options.scan_depth || 'standard',
    }),
  });
};

/**
 * Execute Credential Intelligence workflow
 *
 * Combines Breach Data + Google Dorking + Dark Web + Username Hunter
 * for credential exposure analysis.
 *
 * @param {Object} target
 * @param {string} target.email - Email address (optional)
 * @param {string} target.username - Username (optional)
 * @param {string} target.phone - Phone number (optional)
 * @param {boolean} target.include_darkweb - Include dark web monitoring (default: true)
 * @param {boolean} target.include_dorking - Include Google dorking (default: true)
 * @param {boolean} target.include_social - Include social media (default: true)
 *
 * Returns:
 * - workflow_id: Unique workflow identifier
 * - status: pending/running/completed/failed
 * - target_email: Target email
 * - target_username: Target username
 * - message: Status message
 */
export const executeCredentialIntelWorkflow = async (target) => {
  return apiRequest('/workflows/credential-intel', {
    method: 'POST',
    body: JSON.stringify({
      email: target.email || null,
      username: target.username || null,
      phone: target.phone || null,
      include_darkweb: target.include_darkweb ?? true,
      include_dorking: target.include_dorking ?? true,
      include_social: target.include_social ?? true,
    }),
  });
};

/**
 * Execute Deep Target Profiling workflow
 *
 * Combines Social Scraper + Email/Phone Analyzer + Image Analysis +
 * Pattern Detection for comprehensive target profiling.
 *
 * @param {Object} target
 * @param {string} target.username - Username (optional)
 * @param {string} target.email - Email address (optional)
 * @param {string} target.phone - Phone number (optional)
 * @param {string} target.name - Full name (optional)
 * @param {string} target.location - Location (optional)
 * @param {string} target.image_url - Profile image URL (optional)
 * @param {boolean} target.include_social - Include social media (default: true)
 * @param {boolean} target.include_images - Include image analysis (default: true)
 *
 * Returns:
 * - workflow_id: Unique workflow identifier
 * - status: pending/running/completed/failed
 * - target_username: Target username
 * - target_email: Target email
 * - message: Status message
 */
export const executeTargetProfilingWorkflow = async (target) => {
  return apiRequest('/workflows/target-profile', {
    method: 'POST',
    body: JSON.stringify({
      username: target.username || null,
      email: target.email || null,
      phone: target.phone || null,
      name: target.name || null,
      location: target.location || null,
      image_url: target.image_url || null,
      include_social: target.include_social ?? true,
      include_images: target.include_images ?? true,
    }),
  });
};

/**
 * Get workflow execution status
 *
 * @param {string} workflowId - Workflow identifier
 *
 * Returns:
 * - workflow_id: Workflow identifier
 * - status: pending/running/completed/failed
 * - target: Target information
 * - findings_count: Number of findings
 * - risk_score/exposure_score/se_score: Relevant score
 * - started_at: ISO timestamp
 * - completed_at: ISO timestamp (if completed)
 */
export const getWorkflowStatus = async (workflowId) => {
  return apiRequest(`/workflows/${workflowId}/status`);
};

/**
 * Get complete workflow report
 *
 * @param {string} workflowId - Workflow identifier
 *
 * Returns:
 * - Complete workflow report with all findings, statistics, and recommendations
 *
 * Throws:
 * - 404: Workflow not found
 * - 409: Workflow not yet completed
 */
export const getWorkflowReport = async (workflowId) => {
  return apiRequest(`/workflows/${workflowId}/report`);
};

// ═══════════════════════════════════════════════════════════════════════════
// UNIFIED OVERVIEW ENDPOINT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Get unified overview of all AI-Driven Workflows
 *
 * Combines status from Offensive, Defensive, and Purple Team systems
 * into single comprehensive view for MAXIMUS AI dashboard.
 *
 * Returns:
 * - system: "ai_driven_workflows"
 * - status: operational/degraded/offline
 * - offensive: Full Red Team status
 * - defensive: Full Blue Team status
 * - purple: Full Purple Team metrics
 * - timestamp: ISO timestamp
 */
export const getADWOverview = async () => {
  return apiRequest('/overview');
};

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════════════════

/**
 * ADW system health check
 *
 * Returns:
 * - status: healthy/degraded/unhealthy
 * - message: Human-readable status message
 */
export const checkADWHealth = async () => {
  return apiRequest('/health');
};

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Check if ADW system is available and operational
 */
export const isADWAvailable = async () => {
  const health = await checkADWHealth();
  return health.success && health.data.status === 'healthy';
};

/**
 * Get comprehensive ADW system summary
 *
 * Fetches all major status endpoints in parallel for dashboard overview
 */
export const getADWSummary = async () => {
  try {
    const [offensive, defensive, purple] = await Promise.all([
      getOffensiveStatus(),
      getDefensiveStatus(),
      getPurpleMetrics(),
    ]);

    return {
      success: true,
      data: {
        offensive: offensive.success ? offensive.data : null,
        defensive: defensive.success ? defensive.data : null,
        purple: purple.success ? purple.data : null,
        timestamp: new Date().toISOString(),
      },
    };
  } catch (error) {
    logger.error('Error fetching ADW summary:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Get defensive agent status breakdown
 *
 * Extracts individual agent statuses from defensive status for detailed view
 */
export const getAgentStatuses = async () => {
  const defensive = await getDefensiveStatus();
  if (defensive.success && defensive.data.agents) {
    return {
      success: true,
      data: defensive.data.agents,
    };
  }
  return {
    success: false,
    error: 'Unable to fetch agent statuses',
  };
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export default {
  // Offensive AI (Red Team)
  getOffensiveStatus,
  createCampaign,
  listCampaigns,

  // Defensive AI (Blue Team)
  getDefensiveStatus,
  getThreats,
  getCoagulationStatus,

  // Purple Team
  getPurpleMetrics,
  triggerEvolutionCycle,

  // OSINT Workflows
  executeAttackSurfaceWorkflow,
  executeCredentialIntelWorkflow,
  executeTargetProfilingWorkflow,
  getWorkflowStatus,
  getWorkflowReport,

  // Overview
  getADWOverview,

  // Health
  checkADWHealth,

  // Utilities
  isADWAvailable,
  getADWSummary,
  getAgentStatuses,
};

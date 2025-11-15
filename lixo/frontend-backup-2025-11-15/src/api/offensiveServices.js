import logger from "@/utils/logger";
import { ServiceEndpoints } from "../config/endpoints";

/**
 * Offensive Security Arsenal - API Client
 * ========================================
 *
 * Cliente unificado para os 6 serviços do arsenal ofensivo via API Gateway certificado.
 * Todos os requests passam pelo API Gateway (porta 8000) que roteia para:
 * - Network Reconnaissance (8032)
 * - Vulnerability Intelligence (8033)
 * - Web Attack Surface (8034)
 * - C2 Orchestration (8035)
 * - Breach & Attack Simulation (8036)
 * - Offensive Gateway (8037)
 *
 * QUALITY-FIRST: Implementação real, zero mocks, zero placeholders.
 * FIXED 2025-10-27: Air Gap #1 - Now uses API Gateway instead of localhost
 */

// ✅ FIX: Use API Gateway instead of localhost
const API_BASE = ServiceEndpoints.apiGateway;

const ENDPOINTS = {
  NETWORK_RECON: `${API_BASE}/offensive/network-recon`,
  VULN_INTEL: `${API_BASE}/offensive/vuln-intel`,
  WEB_ATTACK: `${API_BASE}/offensive/web-attack`,
  C2_ORCHESTRATION: `${API_BASE}/offensive/c2`,
  BAS: `${API_BASE}/offensive/bas`,
  OFFENSIVE_GATEWAY: `${API_BASE}/offensive/gateway`,
};

/**
 * ============================================================================
 * NETWORK RECONNAISSANCE SERVICE (Port 8032)
 * ============================================================================
 */

/**
 * Executa varredura completa de rede (Masscan + Nmap + Service Detection)
 */
export const scanNetwork = async (
  target,
  scanType = "quick",
  ports = "1-1000",
) => {
  try {
    const response = await fetch(`${ENDPOINTS.NETWORK_RECON}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target,
        scan_type: scanType,
        ports,
      }),
    });

    if (!response.ok)
      throw new Error(`Network scan failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error in network scan:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Obtém status de scan em andamento
 */
export const getScanStatus = async (scanId) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.NETWORK_RECON}/api/scan/${scanId}/status`,
    );
    if (!response.ok)
      throw new Error(`Failed to get scan status: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error getting scan status:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Lista todos os scans recentes
 */
export const listScans = async (limit = 50) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.NETWORK_RECON}/api/scans?limit=${limit}`,
    );
    if (!response.ok)
      throw new Error(`Failed to list scans: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error listing scans:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Descobre hosts ativos em rede (ping sweep)
 */
export const discoverHosts = async (network) => {
  try {
    const response = await fetch(`${ENDPOINTS.NETWORK_RECON}/api/discover`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ network }),
    });

    if (!response.ok)
      throw new Error(`Host discovery failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error in host discovery:", error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * VULNERABILITY INTELLIGENCE SERVICE (Port 8033)
 * ============================================================================
 */

/**
 * Busca vulnerabilidades por CVE ID
 */
export const searchCVE = async (cveId) => {
  try {
    const response = await fetch(`${ENDPOINTS.VULN_INTEL}/api/cve/${cveId}`);
    if (!response.ok) throw new Error(`CVE search failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error searching CVE:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Busca vulnerabilidades por produto/vendor
 */
export const searchVulnerabilities = async (query, filters = {}) => {
  try {
    const params = new URLSearchParams({
      query,
      ...filters,
    });

    const response = await fetch(
      `${ENDPOINTS.VULN_INTEL}/api/search?${params}`,
    );
    if (!response.ok)
      throw new Error(`Vulnerability search failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error searching vulnerabilities:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Obtém exploits disponíveis para CVE
 */
export const getExploits = async (cveId) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.VULN_INTEL}/api/cve/${cveId}/exploits`,
    );
    if (!response.ok)
      throw new Error(`Exploit search failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error getting exploits:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Correlaciona vulnerabilidades com scan de rede
 */
export const correlateWithScan = async (scanId) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.VULN_INTEL}/api/correlate/${scanId}`,
      {
        method: "POST",
      },
    );
    if (!response.ok) throw new Error(`Correlation failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error correlating vulnerabilities:", error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * WEB ATTACK SURFACE SERVICE (Port 8034)
 * ============================================================================
 */

/**
 * Escaneia superfície de ataque web (OWASP Top 10, SQLi, XSS, etc)
 */
export const scanWebTarget = async (
  url,
  scanProfile = "full",
  authConfig = null,
) => {
  try {
    const response = await fetch(`${ENDPOINTS.WEB_ATTACK}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        scan_profile: scanProfile,
        auth_config: authConfig,
      }),
    });

    if (!response.ok) throw new Error(`Web scan failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error in web scan:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Executa teste específico (SQLi, XSS, SSRF, etc)
 */
export const runWebTest = async (url, testType, params = {}) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.WEB_ATTACK}/api/test/${testType}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          ...params,
        }),
      },
    );

    if (!response.ok) throw new Error(`Web test failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error running web test:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Obtém relatório de scan web
 */
export const getWebScanReport = async (scanId) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.WEB_ATTACK}/api/scan/${scanId}/report`,
    );
    if (!response.ok)
      throw new Error(`Failed to get report: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error getting web scan report:", error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * C2 ORCHESTRATION SERVICE (Port 8035)
 * ============================================================================
 */

/**
 * Cria sessão C2 (Cobalt Strike ou Metasploit)
 */
export const createC2Session = async (
  framework,
  targetHost,
  payload,
  config = {},
) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.C2_ORCHESTRATION}/api/session/create`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          framework, // 'cobalt_strike' | 'metasploit'
          target_host: targetHost,
          payload,
          config,
        }),
      },
    );

    if (!response.ok)
      throw new Error(`Session creation failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error creating C2 session:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Lista sessões ativas
 */
export const listC2Sessions = async (framework = null) => {
  try {
    const params = framework ? `?framework=${framework}` : "";
    const response = await fetch(
      `${ENDPOINTS.C2_ORCHESTRATION}/api/sessions${params}`,
    );
    if (!response.ok)
      throw new Error(`Failed to list sessions: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error listing C2 sessions:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Executa comando em sessão C2
 */
export const executeC2Command = async (sessionId, command, args = []) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.C2_ORCHESTRATION}/api/session/${sessionId}/execute`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command,
          args,
        }),
      },
    );

    if (!response.ok)
      throw new Error(`Command execution failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error executing C2 command:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Passa sessão entre frameworks (CS <-> MSF)
 */
export const passSession = async (sessionId, targetFramework) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.C2_ORCHESTRATION}/api/session/${sessionId}/pass`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_framework: targetFramework,
        }),
      },
    );

    if (!response.ok)
      throw new Error(`Session passing failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error passing session:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Executa attack chain completo (kill chain automation)
 */
export const executeAttackChain = async (chainConfig) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.C2_ORCHESTRATION}/api/attack-chain/execute`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chainConfig),
      },
    );

    if (!response.ok)
      throw new Error(`Attack chain execution failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error executing attack chain:", error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * BREACH & ATTACK SIMULATION (BAS) SERVICE (Port 8036)
 * ============================================================================
 */

/**
 * Executa simulação de técnica MITRE ATT&CK
 */
export const runAttackSimulation = async (
  techniqueId,
  targetHost,
  platform,
  params = {},
) => {
  try {
    const response = await fetch(`${ENDPOINTS.BAS}/api/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        technique_id: techniqueId,
        target_host: targetHost,
        platform,
        params,
      }),
    });

    if (!response.ok) throw new Error(`Simulation failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error running attack simulation:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Lista técnicas MITRE ATT&CK disponíveis
 */
export const listAttackTechniques = async (tactic = null, platform = null) => {
  try {
    const params = new URLSearchParams();
    if (tactic) params.append("tactic", tactic);
    if (platform) params.append("platform", platform);

    const response = await fetch(`${ENDPOINTS.BAS}/api/techniques?${params}`);
    if (!response.ok)
      throw new Error(`Failed to list techniques: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error listing attack techniques:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Executa validação Purple Team (correlação com SIEM/EDR)
 */
export const validatePurpleTeam = async (simulationId, telemetrySources) => {
  try {
    const response = await fetch(`${ENDPOINTS.BAS}/api/purple-team/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        simulation_id: simulationId,
        telemetry_sources: telemetrySources,
      }),
    });

    if (!response.ok)
      throw new Error(`Purple team validation failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error in purple team validation:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Gera relatório de coverage ATT&CK
 */
export const getAttackCoverage = async (organizationId = null) => {
  try {
    const params = organizationId ? `?org_id=${organizationId}` : "";
    const response = await fetch(`${ENDPOINTS.BAS}/api/coverage${params}`);
    if (!response.ok)
      throw new Error(`Failed to get coverage: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error getting attack coverage:", error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * OFFENSIVE GATEWAY SERVICE (Port 8037)
 * ============================================================================
 */

/**
 * Cria workflow de ataque multi-serviço
 */
export const createWorkflow = async (workflowConfig) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.OFFENSIVE_GATEWAY}/api/workflow/create`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(workflowConfig),
      },
    );

    if (!response.ok)
      throw new Error(`Workflow creation failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error creating workflow:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Executa workflow
 */
export const executeWorkflow = async (workflowId, context = {}) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.OFFENSIVE_GATEWAY}/api/workflow/${workflowId}/execute`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context }),
      },
    );

    if (!response.ok)
      throw new Error(`Workflow execution failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error executing workflow:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Obtém status de workflow
 */
export const getWorkflowStatus = async (executionId) => {
  try {
    const response = await fetch(
      `${ENDPOINTS.OFFENSIVE_GATEWAY}/api/workflow/execution/${executionId}`,
    );
    if (!response.ok)
      throw new Error(`Failed to get workflow status: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error getting workflow status:", error);
    return { success: false, error: error.message };
  }
};

/**
 * Lista workflows disponíveis
 */
export const listWorkflows = async () => {
  try {
    const response = await fetch(
      `${ENDPOINTS.OFFENSIVE_GATEWAY}/api/workflows`,
    );
    if (!response.ok)
      throw new Error(`Failed to list workflows: ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error("Error listing workflows:", error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * HEALTH CHECKS
 * ============================================================================
 */

/**
 * Verifica status de todos os serviços ofensivos
 */
export const checkOffensiveServicesHealth = async () => {
  const services = {
    networkRecon: false,
    vulnIntel: false,
    webAttack: false,
    c2Orchestration: false,
    bas: false,
    offensiveGateway: false,
  };

  const checkService = async (name, endpoint) => {
    try {
      const response = await fetch(`${endpoint}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(3000),
      });
      services[name] = response.ok;
    } catch (e) {
      logger.warn(`${name} service unavailable`);
      services[name] = false;
    }
  };

  await Promise.all([
    checkService("networkRecon", ENDPOINTS.NETWORK_RECON),
    checkService("vulnIntel", ENDPOINTS.VULN_INTEL),
    checkService("webAttack", ENDPOINTS.WEB_ATTACK),
    checkService("c2Orchestration", ENDPOINTS.C2_ORCHESTRATION),
    checkService("bas", ENDPOINTS.BAS),
    checkService("offensiveGateway", ENDPOINTS.OFFENSIVE_GATEWAY),
  ]);

  return services;
};

/**
 * ============================================================================
 * EXPORTS
 * ============================================================================
 */

export default {
  // Network Reconnaissance
  scanNetwork,
  getScanStatus,
  listScans,
  discoverHosts,

  // Vulnerability Intelligence
  searchCVE,
  searchVulnerabilities,
  getExploits,
  correlateWithScan,

  // Web Attack Surface
  scanWebTarget,
  runWebTest,
  getWebScanReport,

  // C2 Orchestration
  createC2Session,
  listC2Sessions,
  executeC2Command,
  passSession,
  executeAttackChain,

  // Breach & Attack Simulation
  runAttackSimulation,
  listAttackTechniques,
  validatePurpleTeam,
  getAttackCoverage,

  // Offensive Gateway
  createWorkflow,
  executeWorkflow,
  getWorkflowStatus,
  listWorkflows,

  // Health
  checkOffensiveServicesHealth,

  // Constants
  ENDPOINTS,
};

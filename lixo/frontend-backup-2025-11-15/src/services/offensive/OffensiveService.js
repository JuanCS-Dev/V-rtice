/**
 * Offensive Service
 * =================
 *
 * Service layer for Offensive & Defensive Security Arsenal
 * Manages communication with 9 offensive/defensive services:
 * - Network Reconnaissance (8032)
 * - Vulnerability Intelligence (8033)
 * - Web Attack Surface (8034)
 * - C2 Orchestration (8035)
 * - Breach & Attack Simulation (8036)
 * - Behavioral Analyzer (8037) - DEFENSIVE
 * - Traffic Analyzer (8038) - DEFENSIVE
 * - MAV Detection (8039) - DEFENSIVE
 * - Offensive Gateway (8040)
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002 (Service Layer Pattern)
 *
 * Architecture:
 * Component → Hook → Service (THIS LAYER) → API Client
 */

import { BaseService } from "../base/BaseService";
import { ServiceEndpoints } from "@/config/endpoints";
import logger from "@/utils/logger";

export class OffensiveService extends BaseService {
  constructor(client) {
    super(ServiceEndpoints.offensive.gateway, client);

    // Service-specific endpoints
    this.endpoints = {
      networkRecon: ServiceEndpoints.offensive.networkRecon,
      vulnIntel: ServiceEndpoints.offensive.vulnIntel,
      webAttack: ServiceEndpoints.offensive.webAttack,
      c2: ServiceEndpoints.offensive.c2Orchestration,
      bas: ServiceEndpoints.offensive.bas,
      behavioral: "/api/defensive/behavioral",
      traffic: "/api/defensive/traffic",
      mav: "/api/social-defense/mav",
      gateway: ServiceEndpoints.offensive.gateway,
    };
  }

  // ============================================================================
  // NETWORK RECONNAISSANCE
  // ============================================================================

  /**
   * Executes network scan (Masscan + Nmap + Service Detection)
   * @param {string} target - Target IP/CIDR
   * @param {string} scanType - 'quick' | 'full' | 'stealth'
   * @param {string} ports - Port range (e.g., '1-1000')
   * @returns {Promise<Object>} Scan result with scan_id
   */
  async scanNetwork(target, scanType = "quick", ports = "1-1000") {
    this.validateRequest({ target, scanType, ports });

    try {
      const response = await this.client.post(
        `${this.endpoints.networkRecon}/api/scan`,
        {
          target,
          scan_type: scanType,
          ports,
        },
      );

      return this.transformResponse(response);
    } catch (error) {
      return this.handleError(
        error,
        "POST",
        `${this.endpoints.networkRecon}/api/scan`,
      );
    }
  }

  /**
   * Gets scan status
   * @param {string} scanId - Scan identifier
   * @returns {Promise<Object>} Scan status and progress
   */
  async getScanStatus(scanId) {
    if (!scanId) {
      throw new Error("Scan ID is required");
    }

    return await this.client.get(
      `${this.endpoints.networkRecon}/api/scan/${scanId}/status`,
    );
  }

  /**
   * Lists recent scans
   * @param {number} limit - Maximum number of scans to return
   * @returns {Promise<Array>} List of scans
   */
  async listScans(limit = 50) {
    return await this.client.get(`${this.endpoints.networkRecon}/api/scans`, {
      params: { limit },
    });
  }

  /**
   * Discovers active hosts in network (ping sweep)
   * @param {string} network - Network CIDR (e.g., '192.168.1.0/24')
   * @returns {Promise<Object>} Discovered hosts
   */
  async discoverHosts(network) {
    this.validateRequest({ network });

    return await this.client.post(
      `${this.endpoints.networkRecon}/api/discover`,
      {
        network,
      },
    );
  }

  // ============================================================================
  // VULNERABILITY INTELLIGENCE
  // ============================================================================

  /**
   * Searches CVE by ID
   * @param {string} cveId - CVE identifier (e.g., 'CVE-2024-1234')
   * @returns {Promise<Object>} CVE details
   */
  async searchCVE(cveId) {
    if (!cveId || !cveId.startsWith("CVE-")) {
      throw new Error("Invalid CVE ID format");
    }

    return await this.client.get(
      `${this.endpoints.vulnIntel}/api/cve/${cveId}`,
    );
  }

  /**
   * Searches vulnerabilities by query
   * @param {string} query - Search query
   * @param {Object} filters - Additional filters
   * @returns {Promise<Array>} Vulnerability results
   */
  async searchVulnerabilities(query, filters = {}) {
    const params = new URLSearchParams({ query, ...filters });
    return await this.client.get(
      `${this.endpoints.vulnIntel}/api/search?${params}`,
    );
  }

  /**
   * Gets available exploits for CVE
   * @param {string} cveId - CVE identifier
   * @returns {Promise<Array>} Available exploits
   */
  async getExploits(cveId) {
    if (!cveId) {
      throw new Error("CVE ID is required");
    }

    return await this.client.get(
      `${this.endpoints.vulnIntel}/api/cve/${cveId}/exploits`,
    );
  }

  /**
   * Correlates vulnerabilities with network scan
   * @param {string} scanId - Scan identifier
   * @returns {Promise<Object>} Correlation results
   */
  async correlateWithScan(scanId) {
    return await this.client.post(
      `${this.endpoints.vulnIntel}/api/correlate/${scanId}`,
    );
  }

  // ============================================================================
  // WEB ATTACK SURFACE
  // ============================================================================

  /**
   * Scans web target (OWASP Top 10, SQLi, XSS, etc)
   * @param {string} url - Target URL
   * @param {string} scanProfile - 'quick' | 'full' | 'custom'
   * @param {Object} authConfig - Optional authentication configuration
   * @returns {Promise<Object>} Scan results
   */
  async scanWebTarget(url, scanProfile = "full", authConfig = null) {
    this.validateRequest({ url, scanProfile });

    return await this.client.post(`${this.endpoints.webAttack}/api/scan`, {
      url,
      scan_profile: scanProfile,
      auth_config: authConfig,
    });
  }

  /**
   * Runs specific web test (SQLi, XSS, SSRF, etc)
   * @param {string} url - Target URL
   * @param {string} testType - Test type identifier
   * @param {Object} params - Test-specific parameters
   * @returns {Promise<Object>} Test results
   */
  async runWebTest(url, testType, params = {}) {
    this.validateRequest({ url, testType });

    return await this.client.post(
      `${this.endpoints.webAttack}/api/test/${testType}`,
      {
        url,
        ...params,
      },
    );
  }

  /**
   * Gets web scan report
   * @param {string} scanId - Scan identifier
   * @returns {Promise<Object>} Scan report
   */
  async getWebScanReport(scanId) {
    return await this.client.get(
      `${this.endpoints.webAttack}/api/scan/${scanId}/report`,
    );
  }

  // ============================================================================
  // C2 ORCHESTRATION
  // ============================================================================

  /**
   * Creates C2 session (Cobalt Strike or Metasploit)
   * @param {string} framework - 'cobalt_strike' | 'metasploit'
   * @param {string} targetHost - Target host
   * @param {string} payload - Payload configuration
   * @param {Object} config - Additional configuration
   * @returns {Promise<Object>} Session details
   */
  async createC2Session(framework, targetHost, payload, config = {}) {
    this.validateRequest({ framework, targetHost, payload });

    return await this.client.post(`${this.endpoints.c2}/api/session/create`, {
      framework,
      target_host: targetHost,
      payload,
      config,
    });
  }

  /**
   * Lists active C2 sessions
   * @param {string} framework - Optional framework filter
   * @returns {Promise<Array>} Active sessions
   */
  async listC2Sessions(framework = null) {
    const params = framework ? `?framework=${framework}` : "";
    return await this.client.get(`${this.endpoints.c2}/api/sessions${params}`);
  }

  /**
   * Executes command in C2 session
   * @param {string} sessionId - Session identifier
   * @param {string} command - Command to execute
   * @param {Array} args - Command arguments
   * @returns {Promise<Object>} Command output
   */
  async executeC2Command(sessionId, command, args = []) {
    this.validateRequest({ sessionId, command });

    return await this.client.post(
      `${this.endpoints.c2}/api/session/${sessionId}/execute`,
      {
        command,
        args,
      },
    );
  }

  /**
   * Passes session between frameworks (CS <-> MSF)
   * @param {string} sessionId - Session identifier
   * @param {string} targetFramework - Target framework
   * @returns {Promise<Object>} Pass result
   */
  async passSession(sessionId, targetFramework) {
    return await this.client.post(
      `${this.endpoints.c2}/api/session/${sessionId}/pass`,
      {
        target_framework: targetFramework,
      },
    );
  }

  /**
   * Executes complete attack chain (kill chain automation)
   * @param {Object} chainConfig - Attack chain configuration
   * @returns {Promise<Object>} Execution result
   */
  async executeAttackChain(chainConfig) {
    this.validateRequest(chainConfig);

    return await this.client.post(
      `${this.endpoints.c2}/api/attack-chain/execute`,
      chainConfig,
    );
  }

  // ============================================================================
  // BREACH & ATTACK SIMULATION (BAS)
  // ============================================================================

  /**
   * Runs MITRE ATT&CK technique simulation
   * @param {string} techniqueId - MITRE ATT&CK technique ID
   * @param {string} targetHost - Target host
   * @param {string} platform - Target platform
   * @param {Object} params - Technique-specific parameters
   * @returns {Promise<Object>} Simulation result
   */
  async runAttackSimulation(techniqueId, targetHost, platform, params = {}) {
    this.validateRequest({ techniqueId, targetHost, platform });

    return await this.client.post(`${this.endpoints.bas}/api/simulate`, {
      technique_id: techniqueId,
      target_host: targetHost,
      platform,
      params,
    });
  }

  /**
   * Lists available MITRE ATT&CK techniques
   * @param {string} tactic - Optional tactic filter
   * @param {string} platform - Optional platform filter
   * @returns {Promise<Array>} Available techniques
   */
  async listAttackTechniques(tactic = null, platform = null) {
    const params = new URLSearchParams();
    if (tactic) params.append("tactic", tactic);
    if (platform) params.append("platform", platform);

    return await this.client.get(
      `${this.endpoints.bas}/api/techniques?${params}`,
    );
  }

  /**
   * Validates Purple Team simulation (correlates with SIEM/EDR)
   * @param {string} simulationId - Simulation identifier
   * @param {Array} telemetrySources - Telemetry sources to correlate
   * @returns {Promise<Object>} Validation result
   */
  async validatePurpleTeam(simulationId, telemetrySources) {
    return await this.client.post(
      `${this.endpoints.bas}/api/purple-team/validate`,
      {
        simulation_id: simulationId,
        telemetry_sources: telemetrySources,
      },
    );
  }

  /**
   * Gets ATT&CK coverage report
   * @param {string} organizationId - Optional organization filter
   * @returns {Promise<Object>} Coverage report
   */
  async getAttackCoverage(organizationId = null) {
    const params = organizationId ? `?org_id=${organizationId}` : "";
    return await this.client.get(`${this.endpoints.bas}/api/coverage${params}`);
  }

  // ============================================================================
  // BEHAVIORAL ANALYZER (DEFENSIVE - 8037)
  // ============================================================================

  /**
   * Analyzes behavioral event for anomalies
   * @param {Object} eventData - Event data
   * @param {string} eventData.entityId - Entity identifier (user/process/host)
   * @param {string} eventData.eventType - Event type (login/file_access/network/privilege)
   * @param {string} eventData.sourceIp - Source IP address
   * @param {Object} eventData.metadata - Additional metadata
   * @returns {Promise<Object>} Analysis result with anomaly detection
   */
  async analyzeBehavioralEvent(eventData) {
    this.validateRequest(eventData);

    return await this.client.post(`${this.endpoints.behavioral}/analyze`, {
      entity_id: eventData.entityId,
      event_type: eventData.eventType,
      source_ip: eventData.sourceIp,
      timestamp: new Date().toISOString(),
      metadata: eventData.metadata || {},
    });
  }

  /**
   * Analyzes batch of behavioral events
   * @param {Array<Object>} events - Array of event objects
   * @returns {Promise<Object>} Batch analysis results
   */
  async analyzeBatchBehavioralEvents(events) {
    if (!Array.isArray(events) || events.length === 0) {
      throw new Error("Events array is required");
    }

    const formattedEvents = events.map((e) => ({
      entity_id: e.entityId,
      event_type: e.eventType,
      source_ip: e.sourceIp,
      timestamp: e.timestamp || new Date().toISOString(),
      metadata: e.metadata || {},
    }));

    return await this.client.post(
      `${this.endpoints.behavioral}/analyze-batch`,
      {
        events: formattedEvents,
      },
    );
  }

  /**
   * Trains baseline profile for entity
   * @param {string} entityId - Entity identifier
   * @param {Array<Object>} trainingEvents - Historical events for training
   * @returns {Promise<Object>} Training result
   */
  async trainBehavioralBaseline(entityId, trainingEvents) {
    if (!entityId || !Array.isArray(trainingEvents)) {
      throw new Error("Entity ID and training events are required");
    }

    return await this.client.post(
      `${this.endpoints.behavioral}/train-baseline`,
      {
        entity_id: entityId,
        training_events: trainingEvents,
      },
    );
  }

  /**
   * Gets behavioral analysis metrics
   * @returns {Promise<Object>} Behavioral metrics
   */
  async getBehavioralMetrics() {
    return await this.client.get(`${this.endpoints.behavioral}/metrics`);
  }

  // ============================================================================
  // TRAFFIC ANALYZER (DEFENSIVE - 8038)
  // ============================================================================

  /**
   * Analyzes network flow for threats
   * @param {Object} flowData - Network flow data
   * @param {string} flowData.sourceIp - Source IP address
   * @param {string} flowData.destIp - Destination IP address
   * @param {number} flowData.sourcePort - Source port
   * @param {number} flowData.destPort - Destination port
   * @param {string} flowData.protocol - Protocol (tcp/udp/icmp)
   * @param {number} flowData.bytesSent - Bytes sent
   * @param {number} flowData.bytesReceived - Bytes received
   * @param {number} flowData.duration - Flow duration in seconds
   * @returns {Promise<Object>} Threat analysis result
   */
  async analyzeTrafficFlow(flowData) {
    this.validateRequest(flowData);

    return await this.client.post(`${this.endpoints.traffic}/analyze`, {
      source_ip: flowData.sourceIp,
      dest_ip: flowData.destIp,
      source_port: flowData.sourcePort,
      dest_port: flowData.destPort,
      protocol: flowData.protocol || "tcp",
      bytes_sent: flowData.bytesSent || 0,
      bytes_received: flowData.bytesReceived || 0,
      duration_seconds: flowData.duration || 0,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Analyzes batch of network flows
   * @param {Array<Object>} flows - Array of flow objects
   * @returns {Promise<Object>} Batch analysis results
   */
  async analyzeBatchTrafficFlows(flows) {
    if (!Array.isArray(flows) || flows.length === 0) {
      throw new Error("Flows array is required");
    }

    const formattedFlows = flows.map((f) => ({
      source_ip: f.sourceIp,
      dest_ip: f.destIp,
      source_port: f.sourcePort,
      dest_port: f.destPort,
      protocol: f.protocol || "tcp",
      bytes_sent: f.bytesSent || 0,
      bytes_received: f.bytesReceived || 0,
      duration_seconds: f.duration || 0,
      timestamp: f.timestamp || new Date().toISOString(),
    }));

    return await this.client.post(`${this.endpoints.traffic}/analyze-batch`, {
      flows: formattedFlows,
    });
  }

  /**
   * Detects C2 beaconing patterns
   * @param {Array<Object>} flows - Network flows to analyze
   * @returns {Promise<Object>} C2 detection result
   */
  async detectC2Beacons(flows) {
    return await this.analyzeBatchTrafficFlows(flows);
  }

  /**
   * Gets traffic analysis metrics
   * @returns {Promise<Object>} Traffic metrics
   */
  async getTrafficMetrics() {
    return await this.client.get(`${this.endpoints.traffic}/metrics`);
  }

  // ============================================================================
  // MAV DETECTION (DEFENSIVE - 8039) - CRITICAL FOR BRAZIL
  // ============================================================================

  /**
   * Detects Manipulative Amplification & Viralization campaigns
   * @param {Object} campaignData - Campaign data
   * @param {Array<Object>} campaignData.posts - Social media posts
   * @param {Array<Object>} campaignData.accounts - Account profiles
   * @param {string} campaignData.platform - Platform (twitter/instagram/facebook)
   * @param {string} campaignData.timeWindow - Time window (e.g., '24h')
   * @returns {Promise<Object>} MAV detection result
   */
  async detectMAVCampaign(campaignData) {
    this.validateRequest(campaignData);

    if (!Array.isArray(campaignData.posts) || campaignData.posts.length === 0) {
      throw new Error("Posts array is required");
    }

    return await this.client.post(`${this.endpoints.mav}/detect`, {
      posts: campaignData.posts,
      accounts: campaignData.accounts || [],
      platform: campaignData.platform || "twitter",
      time_window: campaignData.timeWindow || "24h",
    });
  }

  /**
   * Analyzes temporal coordination patterns
   * @param {Array<Object>} posts - Social media posts with timestamps
   * @returns {Promise<Object>} Coordination analysis
   */
  async analyzeTemporalCoordination(posts) {
    if (!Array.isArray(posts) || posts.length === 0) {
      throw new Error("Posts array is required");
    }

    return await this.client.post(
      `${this.endpoints.mav}/coordination/temporal`,
      {
        posts,
      },
    );
  }

  /**
   * Analyzes content similarity (embeddings + semantic analysis)
   * @param {Array<Object>} posts - Social media posts
   * @returns {Promise<Object>} Content similarity analysis
   */
  async analyzeContentSimilarity(posts) {
    if (!Array.isArray(posts) || posts.length === 0) {
      throw new Error("Posts array is required");
    }

    return await this.client.post(
      `${this.endpoints.mav}/coordination/content`,
      {
        posts,
      },
    );
  }

  /**
   * Analyzes network coordination (GNN-based)
   * @param {Array<Object>} accounts - Account profiles with connections
   * @returns {Promise<Object>} Network analysis
   */
  async analyzeNetworkCoordination(accounts) {
    if (!Array.isArray(accounts) || accounts.length === 0) {
      throw new Error("Accounts array is required");
    }

    return await this.client.post(
      `${this.endpoints.mav}/coordination/network`,
      {
        accounts,
      },
    );
  }

  /**
   * Gets MAV detection metrics
   * @returns {Promise<Object>} MAV metrics
   */
  async getMAVMetrics() {
    return await this.client.get(`${this.endpoints.mav}/metrics`);
  }

  /**
   * Lists detected MAV campaigns
   * @param {Object} filters - Optional filters
   * @param {string} filters.severity - Severity filter (low/medium/high/critical)
   * @param {string} filters.platform - Platform filter
   * @param {number} filters.limit - Maximum campaigns to return
   * @returns {Promise<Array>} List of detected campaigns
   */
  async listMAVCampaigns(filters = {}) {
    const params = new URLSearchParams();
    if (filters.severity) params.append("severity", filters.severity);
    if (filters.platform) params.append("platform", filters.platform);
    if (filters.limit) params.append("limit", filters.limit);

    return await this.client.get(`${this.endpoints.mav}/campaigns?${params}`);
  }

  // ============================================================================
  // OFFENSIVE GATEWAY (WORKFLOWS)
  // ============================================================================

  /**
   * Creates multi-service attack workflow
   * @param {Object} workflowConfig - Workflow configuration
   * @returns {Promise<Object>} Workflow details
   */
  async createWorkflow(workflowConfig) {
    this.validateRequest(workflowConfig);

    return await this.post("/api/workflow/create", workflowConfig);
  }

  /**
   * Executes workflow
   * @param {string} workflowId - Workflow identifier
   * @param {Object} context - Execution context
   * @returns {Promise<Object>} Execution result
   */
  async executeWorkflow(workflowId, context = {}) {
    return await this.post(`/api/workflow/${workflowId}/execute`, { context });
  }

  /**
   * Gets workflow execution status
   * @param {string} executionId - Execution identifier
   * @returns {Promise<Object>} Execution status
   */
  async getWorkflowStatus(executionId) {
    return await this.get(`/api/workflow/execution/${executionId}`);
  }

  /**
   * Lists available workflows
   * @returns {Promise<Array>} Available workflows
   */
  async listWorkflows() {
    return await this.get("/api/workflows");
  }

  // ============================================================================
  // METRICS & AGGREGATION
  // ============================================================================

  /**
   * Gets aggregated offensive metrics from all services
   * @returns {Promise<Object>} Aggregated metrics
   */
  async getMetrics() {
    const metrics = {
      activeScans: 0,
      exploitsFound: 0,
      targets: 0,
      c2Sessions: 0,
    };

    try {
      // Aggregate from multiple services with timeout
      const results = await Promise.allSettled([
        this.client.get(`${this.endpoints.networkRecon}/api/scans/active`, {
          signal: AbortSignal.timeout(3000),
        }),
        this.client.get(
          `${this.endpoints.vulnIntel}/api/vulnerabilities/count`,
          {
            signal: AbortSignal.timeout(3000),
          },
        ),
        this.client.get(`${this.endpoints.webAttack}/api/targets/count`, {
          signal: AbortSignal.timeout(3000),
        }),
        this.client.get(`${this.endpoints.c2}/api/sessions/active`, {
          signal: AbortSignal.timeout(3000),
        }),
      ]);

      // Extract counts from responses
      if (results[0].status === "fulfilled") {
        metrics.activeScans =
          results[0].value?.count || results[0].value?.total || 0;
      }
      if (results[1].status === "fulfilled") {
        metrics.exploitsFound =
          results[1].value?.count || results[1].value?.total || 0;
      }
      if (results[2].status === "fulfilled") {
        metrics.targets =
          results[2].value?.count || results[2].value?.total || 0;
      }
      if (results[3].status === "fulfilled") {
        metrics.c2Sessions =
          results[3].value?.count || results[3].value?.total || 0;
      }

      return metrics;
    } catch (error) {
      logger.error("[OffensiveService] Failed to aggregate metrics:", error);
      return metrics; // Return zeros on error
    }
  }

  /**
   * Checks health of all offensive/defensive services
   * @returns {Promise<Object>} Service health status
   */
  async checkHealth() {
    const services = {
      networkRecon: false,
      vulnIntel: false,
      webAttack: false,
      c2Orchestration: false,
      bas: false,
      behavioral: false,
      traffic: false,
      mav: false,
      offensiveGateway: false,
    };

    const checkService = async (name, endpoint) => {
      try {
        const response = await this.client.get(`${endpoint}/health`, {
          signal: AbortSignal.timeout(3000),
        });
        services[name] = !!response;
      } catch (error) {
        logger.warn(`[OffensiveService] ${name} service unavailable`);
        services[name] = false;
      }
    };

    await Promise.allSettled([
      checkService("networkRecon", this.endpoints.networkRecon),
      checkService("vulnIntel", this.endpoints.vulnIntel),
      checkService("webAttack", this.endpoints.webAttack),
      checkService("c2Orchestration", this.endpoints.c2),
      checkService("bas", this.endpoints.bas),
      checkService("behavioral", this.endpoints.behavioral),
      checkService("traffic", this.endpoints.traffic),
      checkService("mav", this.endpoints.mav),
      checkService("offensiveGateway", this.endpoints.gateway),
    ]);

    return services;
  }

  // ============================================================================
  // VALIDATION & TRANSFORMATION
  // ============================================================================

  /**
   * Validates request data before sending
   * @param {Object} data - Request data
   * @throws {Error} If validation fails
   * @protected
   */
  validateRequest(data) {
    // Basic validation
    if (!data || typeof data !== "object") {
      throw new Error("Invalid request data");
    }

    // Validate target fields (IP/CIDR/URL)
    if (data.target) {
      // IP/CIDR validation with proper range checking
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/;
      if (!ipRegex.test(data.target)) {
        throw new Error("Invalid target format");
      }

      // Validate each octet is 0-255
      const parts = data.target.split("/")[0].split(".");
      for (const part of parts) {
        const num = parseInt(part, 10);
        if (num < 0 || num > 255) {
          throw new Error("Invalid target format");
        }
      }

      // Validate CIDR suffix if present
      if (data.target.includes("/")) {
        const cidr = parseInt(data.target.split("/")[1], 10);
        if (cidr < 0 || cidr > 32) {
          throw new Error("Invalid target format");
        }
      }
    }

    // Validate URL fields
    if (data.url) {
      try {
        new URL(data.url);
      } catch {
        throw new Error("Invalid URL format");
      }
    }

    // Validate CVE format
    if (data.cveId && !data.cveId.startsWith("CVE-")) {
      throw new Error("Invalid CVE ID format");
    }

    return true;
  }

  /**
   * Transforms API response to domain model
   * @param {Object} response - Raw API response
   * @returns {Object} Transformed data
   * @protected
   */
  transformResponse(response) {
    // Transform common response patterns
    if (response && typeof response === "object") {
      // Ensure success field exists
      if (response.success === undefined) {
        response.success = true;
      }

      // Transform snake_case to camelCase for common fields
      if (response.scan_id) {
        response.scanId = response.scan_id;
      }
      if (response.workflow_id) {
        response.workflowId = response.workflow_id;
      }
      if (response.session_id) {
        response.sessionId = response.session_id;
      }
    }

    return response;
  }
}

// Singleton instance
let offensiveServiceInstance = null;

/**
 * Gets singleton instance of OffensiveService
 * @returns {OffensiveService}
 */
export const getOffensiveService = () => {
  if (!offensiveServiceInstance) {
    offensiveServiceInstance = new OffensiveService();
  }
  return offensiveServiceInstance;
};

export default OffensiveService;

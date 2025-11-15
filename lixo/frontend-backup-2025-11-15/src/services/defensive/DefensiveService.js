/**
 * Defensive Service
 * =================
 *
 * Service layer for Defensive Security Operations
 * Manages communication with defensive tools and systems:
 * - Behavioral Analyzer (anomaly detection)
 * - Encrypted Traffic Analyzer (TLS inspection)
 * - SIEM Integration
 * - EDR/XDR Operations
 * - Threat Intelligence
 * - Alert Management
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002 (Service Layer Pattern)
 *
 * Architecture:
 * Component → Hook → Service (THIS LAYER) → API Client
 */

import { BaseService } from '../base/BaseService';
import { ServiceEndpoints } from '@/config/endpoints';
import logger from '@/utils/logger';

export class DefensiveService extends BaseService {
  constructor(client) {
    // Use RELATIVE PATH for API Gateway routing
    // BaseService will concatenate this with apiClient's API_BASE
    super('/api/defensive', client);

    // Service-specific endpoints (relative paths)
    this.endpoints = {
      core: '/api/defensive',
      immune: '/api/v1/immune/defensive',
    };
  }

  // ============================================================================
  // BEHAVIORAL ANALYZER
  // ============================================================================

  /**
   * Analyzes single behavior event for anomalies
   * @param {Object} eventData - Event data
   * @param {string} eventData.entityId - Entity identifier
   * @param {string} eventData.eventType - Event type
   * @param {string} eventData.timestamp - ISO timestamp
   * @param {Object} eventData.metadata - Additional metadata
   * @returns {Promise<Object>} Analysis result
   */
  async analyzeEvent(eventData) {
    this.validateRequest(eventData);

    return await this.client.post(`${this.endpoints.immune}/behavioral/analyze`, {
      entity_id: eventData.entityId,
      event_type: eventData.eventType,
      timestamp: eventData.timestamp || new Date().toISOString(),
      metadata: eventData.metadata || {},
    });
  }

  /**
   * Analyzes batch of behavior events
   * @param {Array<Object>} events - Array of event objects
   * @returns {Promise<Object>} Batch analysis results
   */
  async analyzeBatchEvents(events) {
    if (!Array.isArray(events) || events.length === 0) {
      throw new Error('Events array is required and must not be empty');
    }

    const formattedEvents = events.map((e) => ({
      entity_id: e.entityId,
      event_type: e.eventType,
      timestamp: e.timestamp || new Date().toISOString(),
      metadata: e.metadata || {},
    }));

    return await this.client.post(`${this.endpoints.immune}/behavioral/analyze-batch`, {
      events: formattedEvents,
    });
  }

  /**
   * Trains baseline for entity
   * @param {string} entityId - Entity identifier
   * @param {Array<Object>} trainingEvents - Training event data
   * @returns {Promise<Object>} Training result
   */
  async trainBaseline(entityId, trainingEvents) {
    if (!entityId) {
      throw new Error('Entity ID is required');
    }

    if (!Array.isArray(trainingEvents) || trainingEvents.length === 0) {
      throw new Error('Training events are required');
    }

    const formattedEvents = trainingEvents.map((e) => ({
      event_type: e.eventType,
      timestamp: e.timestamp || new Date().toISOString(),
      metadata: e.metadata || {},
    }));

    return await this.client.post(`${this.endpoints.immune}/behavioral/train-baseline`, {
      entity_id: entityId,
      training_events: formattedEvents,
    });
  }

  /**
   * Gets baseline status for entity
   * @param {string} entityId - Entity identifier
   * @returns {Promise<Object>} Baseline status
   */
  async getBaselineStatus(entityId) {
    if (!entityId) {
      throw new Error('Entity ID is required');
    }

    return await this.client.get(`${this.endpoints.immune}/behavioral/baseline-status`, {
      params: { entity_id: entityId },
    });
  }

  /**
   * Gets behavioral analysis metrics
   * @returns {Promise<Object>} Behavioral metrics
   */
  async getBehavioralMetrics() {
    return await this.client.get(`${this.endpoints.immune}/behavioral/metrics`);
  }

  // ============================================================================
  // ENCRYPTED TRAFFIC ANALYZER
  // ============================================================================

  /**
   * Analyzes encrypted network flow
   * @param {Object} flowData - Flow data
   * @param {string} flowData.sourceIp - Source IP address
   * @param {string} flowData.destIp - Destination IP address
   * @param {number} flowData.sourcePort - Source port
   * @param {number} flowData.destPort - Destination port
   * @param {string} flowData.protocol - Protocol (tcp/udp)
   * @param {Array<number>} flowData.packetSizes - Packet sizes array
   * @param {Array<number>} flowData.interArrivalTimes - Inter-arrival times
   * @param {string} flowData.tlsVersion - TLS version
   * @param {string} flowData.cipherSuite - Cipher suite
   * @param {string} flowData.sni - Server Name Indication
   * @param {number} flowData.flowDuration - Flow duration in seconds
   * @returns {Promise<Object>} Flow analysis result
   */
  async analyzeFlow(flowData) {
    this.validateRequest(flowData);

    return await this.client.post(`${this.endpoints.immune}/traffic/analyze`, {
      source_ip: flowData.sourceIp,
      dest_ip: flowData.destIp,
      source_port: flowData.sourcePort,
      dest_port: flowData.destPort,
      protocol: flowData.protocol || 'tcp',
      packet_sizes: flowData.packetSizes || [],
      inter_arrival_times: flowData.interArrivalTimes || [],
      tls_version: flowData.tlsVersion,
      cipher_suite: flowData.cipherSuite,
      sni: flowData.sni,
      flow_duration_seconds: flowData.flowDuration || 0,
    });
  }

  /**
   * Analyzes batch of network flows
   * @param {Array<Object>} flows - Array of flow objects
   * @returns {Promise<Object>} Batch analysis results
   */
  async analyzeBatchFlows(flows) {
    if (!Array.isArray(flows) || flows.length === 0) {
      throw new Error('Flows array is required and must not be empty');
    }

    const formattedFlows = flows.map((f) => ({
      source_ip: f.sourceIp,
      dest_ip: f.destIp,
      source_port: f.sourcePort,
      dest_port: f.destPort,
      protocol: f.protocol || 'tcp',
      packet_sizes: f.packetSizes || [],
      inter_arrival_times: f.interArrivalTimes || [],
      tls_version: f.tlsVersion,
      cipher_suite: f.cipherSuite,
      sni: f.sni,
      flow_duration_seconds: f.flowDuration || 0,
    }));

    return await this.client.post(`${this.endpoints.immune}/traffic/analyze-batch`, {
      flows: formattedFlows,
    });
  }

  /**
   * Gets traffic analysis metrics
   * @returns {Promise<Object>} Traffic metrics
   */
  async getTrafficMetrics() {
    return await this.client.get(`${this.endpoints.immune}/traffic/metrics`);
  }

  // ============================================================================
  // DEFENSIVE METRICS & AGGREGATION
  // ============================================================================

  /**
   * Gets aggregated defensive metrics from all services
   * @returns {Promise<Object>} Aggregated defensive metrics
   */
  async getMetrics() {
    try {
      // Fetch from Maximus Core health endpoint
      const healthData = await this.client.get(`${this.endpoints.core}/health`, {
        signal: AbortSignal.timeout(5000),
      });

      // Also fetch behavioral and traffic metrics
      const [behavioralMetrics, trafficMetrics] = await Promise.allSettled([
        this.client.get(`${this.endpoints.immune}/behavioral/metrics`, {
          signal: AbortSignal.timeout(3000),
        }),
        this.client.get(`${this.endpoints.immune}/traffic/metrics`, {
          signal: AbortSignal.timeout(3000),
        }),
      ]);

      // Aggregate metrics
      const metrics = {
        threats: 0,
        suspiciousIPs: 0,
        domains: 0,
        monitored: 0,
      };

      // Extract from health data
      if (healthData) {
        metrics.threats = healthData.memory_system?.episodic_stats?.investigations || 0;
        metrics.monitored = healthData.total_integrated_tools || 57;
      }

      // Extract from behavioral metrics
      if (behavioralMetrics.status === 'fulfilled' && behavioralMetrics.value) {
        metrics.threats += behavioralMetrics.value.anomalies_detected || 0;
      }

      // Extract from traffic metrics
      if (trafficMetrics.status === 'fulfilled' && trafficMetrics.value) {
        metrics.suspiciousIPs = trafficMetrics.value.suspicious_flows || 0;
        metrics.domains = trafficMetrics.value.monitored_domains || 0;
      }

      return metrics;
    } catch (error) {
      logger.error('[DefensiveService] Failed to aggregate metrics:', error);
      // Return zeros on error
      return {
        threats: 0,
        suspiciousIPs: 0,
        domains: 0,
        monitored: 0,
      };
    }
  }

  /**
   * Gets alerts from defensive systems
   * @param {Object} filters - Optional filters
   * @param {string} filters.severity - Severity filter (low/medium/high/critical)
   * @param {number} filters.limit - Maximum alerts to return
   * @param {string} filters.status - Status filter (active/investigating/resolved)
   * @returns {Promise<Array>} List of alerts
   */
  async getAlerts(filters = {}) {
    const params = new URLSearchParams();

    if (filters.severity) params.append('severity', filters.severity);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.status) params.append('status', filters.status);

    return await this.client.get(`${this.endpoints.core}/api/alerts?${params}`);
  }

  /**
   * Gets alert by ID
   * @param {string} alertId - Alert identifier
   * @returns {Promise<Object>} Alert details
   */
  async getAlert(alertId) {
    if (!alertId) {
      throw new Error('Alert ID is required');
    }

    return await this.client.get(`${this.endpoints.core}/api/alerts/${alertId}`);
  }

  /**
   * Updates alert status
   * @param {string} alertId - Alert identifier
   * @param {string} status - New status (investigating/resolved/false_positive)
   * @param {string} notes - Optional notes
   * @returns {Promise<Object>} Updated alert
   */
  async updateAlertStatus(alertId, status, notes = '') {
    if (!alertId) {
      throw new Error('Alert ID is required');
    }

    if (!['investigating', 'resolved', 'false_positive'].includes(status)) {
      throw new Error('Invalid alert status');
    }

    return await this.client.put(`${this.endpoints.core}/api/alerts/${alertId}`, {
      status,
      notes,
    });
  }

  // ============================================================================
  // THREAT INTELLIGENCE
  // ============================================================================

  /**
   * Queries threat intelligence for IP
   * @param {string} ipAddress - IP address to query
   * @returns {Promise<Object>} Threat intelligence data
   */
  async queryIPThreatIntel(ipAddress) {
    this.validateIPAddress(ipAddress);

    return await this.client.get(`${this.endpoints.core}/api/threat-intel/ip/${ipAddress}`);
  }

  /**
   * Queries threat intelligence for domain
   * @param {string} domain - Domain to query
   * @returns {Promise<Object>} Threat intelligence data
   */
  async queryDomainThreatIntel(domain) {
    if (!domain || domain.length === 0) {
      throw new Error('Domain is required');
    }

    return await this.client.get(`${this.endpoints.core}/api/threat-intel/domain/${domain}`);
  }

  /**
   * Queries threat intelligence for file hash
   * @param {string} hash - File hash (MD5/SHA1/SHA256)
   * @returns {Promise<Object>} Threat intelligence data
   */
  async queryHashThreatIntel(hash) {
    if (!hash || hash.length < 32) {
      throw new Error('Valid hash is required');
    }

    return await this.client.get(`${this.endpoints.core}/api/threat-intel/hash/${hash}`);
  }

  // ============================================================================
  // HEALTH CHECK
  // ============================================================================

  /**
   * Checks health of defensive services
   * @returns {Promise<Object>} Service health status
   */
  async checkHealth() {
    try {
      const [coreHealth, immuneHealth] = await Promise.allSettled([
        this.client.get(`${this.endpoints.core}/health`, {
          signal: AbortSignal.timeout(3000),
        }),
        this.client.get(`${this.endpoints.immune}/health`, {
          signal: AbortSignal.timeout(3000),
        }),
      ]);

      return {
        core: coreHealth.status === 'fulfilled' && !!coreHealth.value,
        immune: immuneHealth.status === 'fulfilled' && !!immuneHealth.value,
      };
    } catch (error) {
      logger.warn('[DefensiveService] Health check failed:', error);
      return {
        core: false,
        immune: false,
      };
    }
  }

  // ============================================================================
  // VALIDATION
  // ============================================================================

  /**
   * Validates request data before sending
   * @param {Object} data - Request data
   * @throws {Error} If validation fails
   * @protected
   */
  validateRequest(data) {
    // Basic validation
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid request data');
    }

    // Validate entity ID
    if (data.entityId !== undefined && (!data.entityId || data.entityId.length === 0)) {
      throw new Error('Invalid entity ID');
    }

    // Validate event type
    if (data.eventType !== undefined && (!data.eventType || data.eventType.length === 0)) {
      throw new Error('Invalid event type');
    }

    // Validate IP addresses
    if (data.sourceIp) {
      this.validateIPAddress(data.sourceIp);
    }

    if (data.destIp) {
      this.validateIPAddress(data.destIp);
    }

    // Validate ports
    if (data.sourcePort !== undefined) {
      this.validatePort(data.sourcePort);
    }

    if (data.destPort !== undefined) {
      this.validatePort(data.destPort);
    }

    return true;
  }

  /**
   * Validates IP address format
   * @param {string} ip - IP address
   * @throws {Error} If invalid
   * @private
   */
  validateIPAddress(ip) {
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(ip)) {
      throw new Error('Invalid IP address format');
    }

    // Validate each octet is 0-255
    const parts = ip.split('.');
    for (const part of parts) {
      const num = parseInt(part, 10);
      if (num < 0 || num > 255) {
        throw new Error('Invalid IP address format');
      }
    }
  }

  /**
   * Validates port number
   * @param {number} port - Port number
   * @throws {Error} If invalid
   * @private
   */
  validatePort(port) {
    if (typeof port !== 'number' || port < 0 || port > 65535) {
      throw new Error('Invalid port number');
    }
  }

  /**
   * Transforms API response to domain model
   * @param {Object} response - Raw API response
   * @returns {Object} Transformed data
   * @protected
   */
  transformResponse(response) {
    // Transform common response patterns
    if (response && typeof response === 'object') {
      // Ensure success field exists
      if (response.success === undefined) {
        response.success = true;
      }

      // Transform snake_case to camelCase for common fields
      if (response.entity_id) {
        response.entityId = response.entity_id;
      }
      if (response.event_type) {
        response.eventType = response.event_type;
      }
      if (response.alert_id) {
        response.alertId = response.alert_id;
      }
    }

    return response;
  }
}

// Singleton instance
let defensiveServiceInstance = null;

/**
 * Gets singleton instance of DefensiveService
 * @returns {DefensiveService}
 */
export const getDefensiveService = () => {
  if (!defensiveServiceInstance) {
    defensiveServiceInstance = new DefensiveService();
  }
  return defensiveServiceInstance;
};

export default DefensiveService;

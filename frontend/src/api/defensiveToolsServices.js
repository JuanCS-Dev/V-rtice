import { API_BASE_URL } from '@/config/api';
/**
 * Defensive Tools Services
 * 
 * API integration for defensive tools: Behavioral Analyzer & Encrypted Traffic
 * Connects to Active Immune Core defensive endpoints
 * 
 * Philosophy: Type-safe, async/await, complete error handling
 */

import axios from 'axios';

const DEFENSIVE_BASE = '/api/v1/immune/defensive';

// Create axios instance
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Behavioral Analyzer Services
 */
export const behavioralAnalyzerService = {
  /**
   * Analyze single behavior event for anomalies
   */
  async analyzeEvent(eventData) {
    try {
      const response = await apiClient.post(`${DEFENSIVE_BASE}/behavioral/analyze`, {
        entity_id: eventData.entityId,
        event_type: eventData.eventType,
        timestamp: eventData.timestamp || new Date().toISOString(),
        metadata: eventData.metadata || {}
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  },

  /**
   * Analyze batch of behavior events
   */
  async analyzeBatch(events) {
    try {
      const response = await apiClient.post(`${DEFENSIVE_BASE}/behavioral/analyze-batch`, {
        events: events.map(e => ({
          entity_id: e.entityId,
          event_type: e.eventType,
          timestamp: e.timestamp || new Date().toISOString(),
          metadata: e.metadata || {}
        }))
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  },

  /**
   * Train baseline for entity
   */
  async trainBaseline(entityId, trainingEvents) {
    try {
      const response = await apiClient.post(`${DEFENSIVE_BASE}/behavioral/train-baseline`, {
        entity_id: entityId,
        training_events: trainingEvents.map(e => ({
          event_type: e.eventType,
          timestamp: e.timestamp || new Date().toISOString(),
          metadata: e.metadata || {}
        }))
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  },

  /**
   * Get baseline status
   */
  async getBaselineStatus(entityId) {
    try {
      const response = await apiClient.get(`${DEFENSIVE_BASE}/behavioral/baseline-status`, {
        params: { entity_id: entityId }
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  },

  /**
   * Get behavioral metrics
   */
  async getMetrics() {
    try {
      const response = await apiClient.get(`${DEFENSIVE_BASE}/behavioral/metrics`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  }
};

/**
 * Encrypted Traffic Analyzer Services
 */
export const encryptedTrafficService = {
  /**
   * Analyze encrypted network flow
   */
  async analyzeFlow(flowData) {
    try {
      const response = await apiClient.post(`${DEFENSIVE_BASE}/traffic/analyze`, {
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
        flow_duration_seconds: flowData.flowDuration || 0
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  },

  /**
   * Analyze batch of flows
   */
  async analyzeBatch(flows) {
    try {
      const response = await apiClient.post(`${DEFENSIVE_BASE}/traffic/analyze-batch`, {
        flows: flows.map(f => ({
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
          flow_duration_seconds: f.flowDuration || 0
        }))
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  },

  /**
   * Get traffic analysis metrics
   */
  async getMetrics() {
    try {
      const response = await apiClient.get(`${DEFENSIVE_BASE}/traffic/metrics`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  }
};

/**
 * Health check
 */
export const defensiveToolsHealth = async () => {
  try {
    const response = await apiClient.get(`${DEFENSIVE_BASE}/health`);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message
    };
  }
};

export default {
  behavioral: behavioralAnalyzerService,
  traffic: encryptedTrafficService,
  health: defensiveToolsHealth
};

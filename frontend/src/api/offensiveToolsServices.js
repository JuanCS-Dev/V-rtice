import { API_BASE_URL } from '@/config/api';
/**
 * Offensive Tools Services
 * 
 * API integration for offensive arsenal:
 * - Network Scanner
 * - DNS Enumeration
 * - Payload Generation
 * - Post-Exploitation (Privilege Escalation, Persistence, Lateral Movement, etc)
 * 
 * Philosophy: Ethical boundaries, type-safe, complete error handling
 */

import axios from 'axios';

const OFFENSIVE_BASE = '/api/v1/offensive';

// Create axios instance
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Tool Registry Services
 */
export const toolRegistryService = {
  /**
   * List all available offensive tools
   */
  async listTools(category = null) {
    try {
      const params = category ? { category } : {};
      const response = await apiClient.get(`${OFFENSIVE_BASE}/tools`, { params });
      
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
   * Get specific tool details
   */
  async getTool(toolName) {
    try {
      const response = await apiClient.get(`${OFFENSIVE_BASE}/tools/${toolName}`);
      
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
   * Get registry statistics
   */
  async getStats() {
    try {
      const response = await apiClient.get(`${OFFENSIVE_BASE}/registry/stats`);
      
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
 * Network Scanner Services
 */
export const networkScannerService = {
  /**
   * Scan network target
   */
  async scan(scanData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/scan/network`, {
        target: scanData.target,
        ports: scanData.ports || null,
        timeout: scanData.timeout || 5.0,
        context: {
          operation_mode: scanData.operationMode || 'defensive',
          authorization_token: scanData.authToken || null,
          target_justification: scanData.justification || null
        }
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
  }
};

/**
 * DNS Enumeration Services
 */
export const dnsEnumService = {
  /**
   * Enumerate DNS records
   */
  async enumerate(enumData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/recon/dns-enum`, {
        domain: enumData.domain,
        subdomain_wordlist: enumData.subdomainWordlist || null,
        dns_servers: enumData.dnsServers || null,
        timeout: enumData.timeout || 5.0,
        context: {
          operation_mode: enumData.operationMode || 'defensive',
          authorization_token: enumData.authToken || null,
          target_justification: enumData.justification || null
        }
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
  }
};

/**
 * Payload Generation Services
 */
export const payloadGenService = {
  /**
   * Generate payload
   */
  async generate(payloadData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/exploit/generate-payload`, {
        payload_type: payloadData.payloadType,
        target_platform: payloadData.targetPlatform,
        encoding: payloadData.encoding || 'none',
        obfuscation_level: payloadData.obfuscationLevel || 1,
        callback_config: payloadData.callbackConfig || null,
        context: {
          operation_mode: payloadData.operationMode || 'defensive',
          authorization_token: payloadData.authToken || null,
          target_justification: payloadData.justification || null
        }
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
   * Execute payload
   */
  async execute(executionData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/exploit/execute-payload`, {
        payload: executionData.payload,
        execution_method: executionData.executionMethod || 'direct',
        target_process: executionData.targetProcess || null,
        context: {
          operation_mode: executionData.operationMode || 'defensive',
          authorization_token: executionData.authToken || null,
          target_justification: executionData.justification || null
        }
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
  }
};

/**
 * Post-Exploitation Services
 */
export const postExploitService = {
  /**
   * Privilege escalation
   */
  async privilegeEscalation(escalationData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/post-exploit/privilege-escalation`, {
        target_system: escalationData.targetSystem,
        escalation_method: escalationData.escalationMethod || 'auto',
        target_user: escalationData.targetUser || 'SYSTEM',
        context: {
          operation_mode: escalationData.operationMode || 'defensive',
          authorization_token: escalationData.authToken || null,
          target_justification: escalationData.justification || null
        }
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
   * Establish persistence
   */
  async persistence(persistenceData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/post-exploit/persistence`, {
        target_platform: persistenceData.targetPlatform,
        persistence_type: persistenceData.persistenceType,
        stealth_level: persistenceData.stealthLevel || 2,
        context: {
          operation_mode: persistenceData.operationMode || 'defensive',
          authorization_token: persistenceData.authToken || null,
          target_justification: persistenceData.justification || null
        }
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
   * Lateral movement
   */
  async lateralMovement(movementData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/post-exploit/lateral-movement`, {
        source_host: movementData.sourceHost,
        target_hosts: movementData.targetHosts,
        method: movementData.method || 'smb',
        context: {
          operation_mode: movementData.operationMode || 'defensive',
          authorization_token: movementData.authToken || null,
          target_justification: movementData.justification || null
        }
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
   * Credential harvesting
   */
  async credentialHarvest(harvestData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/post-exploit/credential-harvest`, {
        target_system: harvestData.targetSystem,
        harvest_types: harvestData.harvestTypes || ['memory', 'registry', 'files'],
        context: {
          operation_mode: harvestData.operationMode || 'defensive',
          authorization_token: harvestData.authToken || null,
          target_justification: harvestData.justification || null
        }
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
   * Data exfiltration
   */
  async dataExfiltration(exfilData) {
    try {
      const response = await apiClient.post(`${OFFENSIVE_BASE}/post-exploit/data-exfiltration`, {
        source_path: exfilData.sourcePath,
        exfil_method: exfilData.exfilMethod || 'https',
        encryption: exfilData.encryption !== false,
        context: {
          operation_mode: exfilData.operationMode || 'defensive',
          authorization_token: exfilData.authToken || null,
          target_justification: exfilData.justification || null
        }
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
  }
};

/**
 * Health check
 */
export const offensiveToolsHealth = async () => {
  try {
    const response = await apiClient.get(`${OFFENSIVE_BASE}/health`);
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
  registry: toolRegistryService,
  networkScanner: networkScannerService,
  dnsEnum: dnsEnumService,
  payloadGen: payloadGenService,
  postExploit: postExploitService,
  health: offensiveToolsHealth
};

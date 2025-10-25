/**
 * Service Endpoints Configuration
 * ================================
 *
 * Centralized configuration for all service endpoints.
 * Governed by: Constituição Vértice v2.5 - ADR-001
 *
 * IMPORTANT:
 * - All URLs must come from environment variables
 * - In production, missing required vars will throw ConfigurationError
 * - Use getServiceEndpoint() to access endpoints (with validation)
 */

// ============================================================================
// CONFIGURATION ERROR
// ============================================================================

export class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

// ============================================================================
// ENVIRONMENT VARIABLES
// ============================================================================

const env = import.meta.env;
const isProd = env.PROD;
const isDev = env.DEV;

// ============================================================================
// SERVICE ENDPOINTS
// ============================================================================

export const ServiceEndpoints = {
  // API Gateway (Single Entry Point)
  apiGateway: env.VITE_API_GATEWAY_URL || 'http://localhost:8000',

  // MAXIMUS Core Services (REAL PORTS FROM DOCKER COMPOSE)
  maximus: {
    core: env.VITE_MAXIMUS_CORE_URL || 'http://localhost:8150',
    orchestrator: env.VITE_MAXIMUS_ORCHESTRATOR_URL || 'http://localhost:8125',
    eureka: env.VITE_MAXIMUS_EUREKA_URL || 'http://localhost:9103',
    oraculo: env.VITE_MAXIMUS_ORACULO_URL || 'http://localhost:8152',
    dlqMonitor: env.VITE_MAXIMUS_DLQ_MONITOR_URL || 'http://localhost:8012',
  },

  // Offensive Arsenal
  offensive: {
    gateway: env.VITE_OFFENSIVE_GATEWAY_URL || 'http://localhost:8037',
    networkRecon: env.VITE_OFFENSIVE_NETWORK_RECON_URL || 'http://localhost:8032',
    vulnIntel: env.VITE_OFFENSIVE_VULN_INTEL_URL || 'http://localhost:8033',
    webAttack: env.VITE_OFFENSIVE_WEB_ATTACK_URL || 'http://localhost:8034',
    c2Orchestration: env.VITE_OFFENSIVE_C2_URL || 'http://localhost:8035',
    bas: env.VITE_OFFENSIVE_BAS_URL || 'http://localhost:8036',
  },

  // Defensive Services
  defensive: {
    core: env.VITE_DEFENSIVE_CORE_URL || 'http://localhost:8150', // Maximus Core
  },

  // Cockpit Soberano Services
  cockpit: {
    narrativeFilter: env.VITE_NARRATIVE_FILTER_API || 'http://localhost:8090',
    verdictEngine: env.VITE_VERDICT_ENGINE_API || 'http://localhost:8091',
    commandBus: env.VITE_COMMAND_BUS_API || 'http://localhost:8092',
  },

  // HITL (Human-in-the-Loop) Service
  hitl: {
    api: env.VITE_HITL_API_URL || 'http://localhost:8127',
  },

  // Immunis System
  immunis: {
    api: env.VITE_IMMUNIS_API_URL || 'http://localhost:8300',
  },

  // OSINT Services
  osint: {
    api: env.VITE_OSINT_API_URL || env.VITE_API_GATEWAY_URL || 'http://localhost:8000',
  },

  // Reactive Fabric
  reactiveFabric: {
    api: env.VITE_REACTIVE_FABRIC_API_URL || 'http://localhost:8004',
  },
} as const;

// ============================================================================
// WEBSOCKET ENDPOINTS
// ============================================================================

export const WebSocketEndpoints = {
  maximus: {
    stream: env.VITE_MAXIMUS_WS_URL || 'ws://localhost:8150/ws/stream',
  },

  consciousness: {
    stream: env.VITE_CONSCIOUSNESS_WS_URL || 'ws://localhost:8000/stream/consciousness/ws',
  },

  apv: {
    stream: env.VITE_APV_WS_URL || 'ws://localhost:8000/stream/apv/ws',
  },

  cockpit: {
    verdicts: env.VITE_VERDICT_ENGINE_WS || 'ws://localhost:8091/ws/verdicts',
  },

  hitl: {
    ws: env.VITE_HITL_WS_URL || 'ws://localhost:8127/hitl/ws',
  },

  offensive: {
    executions: env.VITE_OFFENSIVE_WS_URL || 'ws://localhost:8037/ws/executions',
  },

  defensive: {
    alerts: env.VITE_DEFENSIVE_WS_URL || 'ws://localhost:8150/ws/alerts',
  },
} as const;

// ============================================================================
// AUTHENTICATION & SECRETS
// ============================================================================

export const AuthConfig = {
  apiKey: env.VITE_API_KEY || '',

  google: {
    clientId: env.VITE_GOOGLE_CLIENT_ID || '',
  },
} as const;

// ============================================================================
// REQUIRED ENVIRONMENT VARIABLES (PRODUCTION)
// ============================================================================

const REQUIRED_ENV_VARS_PROD = [
  'VITE_API_GATEWAY_URL',
  'VITE_MAXIMUS_CORE_URL',
  'VITE_API_KEY',
] as const;

const REQUIRED_ENV_VARS_DEV = [
  // Development pode usar defaults
] as const;

// ============================================================================
// VALIDATION FUNCTIONS
// ============================================================================

/**
 * Validates that all required environment variables are set
 * @throws {ConfigurationError} if required vars are missing in production
 */
export function validateConfiguration(): void {
  const requiredVars = isProd ? REQUIRED_ENV_VARS_PROD : REQUIRED_ENV_VARS_DEV;
  const missing: string[] = [];

  for (const varName of requiredVars) {
    if (!env[varName]) {
      missing.push(varName);
    }
  }

  if (missing.length > 0) {
    const errorMessage = `
╔═══════════════════════════════════════════════════════════════╗
║                 CONFIGURATION ERROR                           ║
╚═══════════════════════════════════════════════════════════════╝

Missing required environment variables:
${missing.map(v => `  ❌ ${v}`).join('\n')}

Please set these variables in your .env file.
See .env.example for reference.

Production deployment cannot proceed without proper configuration.
    `.trim();

    throw new ConfigurationError(errorMessage);
  }

  if (isDev) {
    console.info('✅ Configuration validated (development mode)');
  }
}

/**
 * Gets a service endpoint by path
 * @param path - Dot-notation path (e.g., 'maximus.core', 'offensive.gateway')
 * @returns The endpoint URL
 * @throws {ConfigurationError} if endpoint not found
 */
export function getServiceEndpoint(path: string): string {
  const parts = path.split('.');
  let current: any = ServiceEndpoints;

  for (const part of parts) {
    if (current[part] === undefined) {
      throw new ConfigurationError(
        `Endpoint not found: ${path}\nAvailable endpoints: ${Object.keys(ServiceEndpoints).join(', ')}`
      );
    }
    current = current[part];
  }

  if (typeof current !== 'string') {
    throw new ConfigurationError(
      `Invalid endpoint path: ${path} does not point to a URL string`
    );
  }

  return current;
}

/**
 * Gets a WebSocket endpoint by path
 * @param path - Dot-notation path (e.g., 'maximus.stream', 'cockpit.verdicts')
 * @returns The WebSocket URL
 * @throws {ConfigurationError} if endpoint not found
 */
export function getWebSocketEndpoint(path: string): string {
  const parts = path.split('.');
  let current: any = WebSocketEndpoints;

  for (const part of parts) {
    if (current[part] === undefined) {
      throw new ConfigurationError(
        `WebSocket endpoint not found: ${path}`
      );
    }
    current = current[part];
  }

  if (typeof current !== 'string') {
    throw new ConfigurationError(
      `Invalid WebSocket endpoint path: ${path} does not point to a URL string`
    );
  }

  return current;
}

/**
 * Converts HTTP(S) URL to WebSocket URL
 * @param httpUrl - HTTP or HTTPS URL
 * @returns WebSocket URL (ws:// or wss://)
 */
export function httpToWs(httpUrl: string): string {
  return httpUrl.replace(/^http/, 'ws');
}

/**
 * Gets WebSocket URL with API key authentication
 * @param endpoint - WebSocket endpoint path
 * @returns WebSocket URL with api_key query parameter
 * @deprecated Use token-based auth instead (ADR-005)
 */
export function getWebSocketUrlWithApiKey(endpoint: string): string {
  const wsUrl = getWebSocketEndpoint(endpoint);
  const apiKey = AuthConfig.apiKey;

  if (!apiKey && isProd) {
    throw new ConfigurationError('API key not configured');
  }

  return `${wsUrl}${wsUrl.includes('?') ? '&' : '?'}api_key=${apiKey}`;
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  ServiceEndpoints,
  WebSocketEndpoints,
  AuthConfig,
  validateConfiguration,
  getServiceEndpoint,
  getWebSocketEndpoint,
  httpToWs,
  getWebSocketUrlWithApiKey,
};

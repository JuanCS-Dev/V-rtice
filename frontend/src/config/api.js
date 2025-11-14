/**
 * API Configuration - Single Source of Truth
 * Governed by: Constituição Vértice v2.5
 *
 * ALL API URLs MUST come from this file.
 * NO hardcoded URLs allowed in components.
 */

// Base URLs
export const API_BASE_URL = import.meta.env.VITE_API_GATEWAY_URL || 'https://api.vertice-maximus.com';

// HTTP Endpoints
export const API_ENDPOINTS = {
  // Core
  health: `${API_BASE_URL}/health`,

  // IP & Domain Intelligence
  ip: `${API_BASE_URL}/api/ip`,
  domain: `${API_BASE_URL}/api/domain`,

  // Threat Intelligence
  threatIntel: `${API_BASE_URL}/api/threat-intel`,

  // Security Tools
  nmap: `${API_BASE_URL}/api/nmap`,
  vulnScanner: `${API_BASE_URL}/api/vuln-scanner`,
  socialEng: `${API_BASE_URL}/api/social-eng`,

  // Monitoring
  network: `${API_BASE_URL}/api/network`,
  cyber: `${API_BASE_URL}/cyber`,

  // HITL
  hitl: `${API_BASE_URL}/hitl`,

  // Dashboards
  offensive: `${API_BASE_URL}/offensive`,
  defensive: `${API_BASE_URL}/defensive`,

  // Cockpit Soberano (Narrative Filter, Verdict Engine, Command Bus)
  narrativeFilter: import.meta.env.VITE_NARRATIVE_FILTER_API || API_BASE_URL,
  verdictEngine: import.meta.env.VITE_VERDICT_ENGINE_API || API_BASE_URL,
  commandBus: import.meta.env.VITE_COMMAND_BUS_API || API_BASE_URL,

  // Aurora AI
  aurora: `${API_BASE_URL}/api/aurora`,

  // Auth
  auth: `${API_BASE_URL}/api/auth`,

  // Oráculo
  oraculo: `${API_BASE_URL}/api/v1/oraculo`,

  // OSINT Investigation
  investigate: `${API_BASE_URL}/api/investigate`,

  // MAXIMUS Core Services
  skills: `${API_BASE_URL}/skills`,
  primitives: `${API_BASE_URL}/primitives`,
  stats: `${API_BASE_URL}/stats`,
  mode: `${API_BASE_URL}/mode`,
  policies: `${API_BASE_URL}/policies`,
  resources: `${API_BASE_URL}/resources`,
  risks: `${API_BASE_URL}/risks`,
  approvals: `${API_BASE_URL}/approvals`,
  plans: `${API_BASE_URL}/plans`,
  history: `${API_BASE_URL}/history`,
  reset: `${API_BASE_URL}/reset`,
  buffer: `${API_BASE_URL}/buffer`,
  consolidate: `${API_BASE_URL}/consolidate`,
  sleep: `${API_BASE_URL}/sleep`,
  wake: `${API_BASE_URL}/wake`,

  // Immune System
  innate: `${API_BASE_URL}/innate`,
  adaptive: `${API_BASE_URL}/adaptive`,
  cytokines: `${API_BASE_URL}/cytokines`,
  antibody: `${API_BASE_URL}/antibody`,
  memory: `${API_BASE_URL}/memory`,

  // MAXIMUS Subordinate Services (New - 2025-10-31)
  // MABA - MAXIMUS Browser Agent (Port 8152)
  maba: `${API_BASE_URL}/api/v1/maba`,
  mabaStats: `${API_BASE_URL}/api/v1/maba/stats`,
  mabaSessions: `${API_BASE_URL}/api/v1/maba/sessions`,
  mabaCognitiveMap: `${API_BASE_URL}/api/v1/maba/cognitive-map`,

  // MVP - MAXIMUS Vision Protocol (Port 8153)
  mvp: `${API_BASE_URL}/api/v1/mvp`,
  mvpNarratives: `${API_BASE_URL}/api/v1/mvp/narratives`,
  mvpMetrics: `${API_BASE_URL}/api/v1/mvp/metrics`,
  mvpAnomalies: `${API_BASE_URL}/api/v1/mvp/anomalies`,
  mvpStatus: `${API_BASE_URL}/api/v1/mvp/status`,

  // PENELOPE - Christian Autonomous Healing (Port 8154)
  penelope: `${API_BASE_URL}/api/v1/penelope`,
  penelopeDiagnose: `${API_BASE_URL}/api/v1/penelope/diagnose`,
  penelopePatches: `${API_BASE_URL}/api/v1/penelope/patches`,
  penelopeWisdom: `${API_BASE_URL}/api/v1/penelope/wisdom`,
  penelopeFruits: `${API_BASE_URL}/api/v1/penelope/fruits/status`,
  penelopeVirtues: `${API_BASE_URL}/api/v1/penelope/virtues/metrics`,
  penelopeHealing: `${API_BASE_URL}/api/v1/penelope/healing/history`,
  penelopeHealth: `${API_BASE_URL}/api/v1/penelope/health`,
};

// WebSocket URLs
const WS_BASE_URL = API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://');

export const WS_ENDPOINTS = {
  // Real-time streams
  executions: `${WS_BASE_URL}/ws/executions`,
  alerts: `${WS_BASE_URL}/ws/alerts`,
  verdicts: `${WS_BASE_URL}/ws/verdicts`,

  // MAXIMUS streams
  maximus: `${WS_BASE_URL}/ws/stream`,
  consciousness: `${WS_BASE_URL}/stream/consciousness/ws`,

  // HITL
  hitl: `${WS_BASE_URL}/hitl/ws`,
  wargaming: `${WS_BASE_URL}/ws/wargaming`,

  // MAXIMUS Subordinate Services (New - 2025-10-31)
  maba: `${WS_BASE_URL}/ws/maba`,
  mvp: `${WS_BASE_URL}/ws/mvp`,
  penelope: `${WS_BASE_URL}/ws/penelope`,
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  WS_ENDPOINTS,
};

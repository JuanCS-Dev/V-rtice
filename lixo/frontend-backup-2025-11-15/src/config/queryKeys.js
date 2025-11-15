/**
 * Centralized Query Key Factory
 * ==============================
 *
 * Boris Cherny Standard - GAP #34 FIX
 *
 * Centralized query key definitions for React Query
 * Prevents duplicate/inconsistent keys across the application
 *
 * Pattern: Hierarchical keys with factory functions
 * Benefits:
 * - Type safety (when using TypeScript)
 * - Autocomplete in IDE
 * - Easier refactoring
 * - Prevents typos and inconsistencies
 * - Clear cache invalidation strategy
 *
 * Usage:
 *   import { queryKeys } from '@/config/queryKeys';
 *   useQuery({ queryKey: queryKeys.defensive.alerts() })
 */

// ============================================================================
// DEFENSIVE
// ============================================================================
export const defensiveKeys = {
  all: ["defensive"],

  // Metrics
  metrics: () => [...defensiveKeys.all, "metrics"],
  health: () => [...defensiveKeys.all, "health"],

  // Alerts
  alerts: (filters) =>
    filters
      ? [...defensiveKeys.all, "alerts", filters]
      : [...defensiveKeys.all, "alerts"],
  alert: (id) => [...defensiveKeys.all, "alerts", id],

  // Behavioral Analyzer
  behavioral: {
    all: () => [...defensiveKeys.all, "behavioral"],
    metrics: () => [...defensiveKeys.all, "behavioral", "metrics"],
    baseline: (entityId) => [
      ...defensiveKeys.all,
      "behavioral",
      "baseline",
      entityId,
    ],
  },

  // Traffic Analyzer
  traffic: {
    all: () => [...defensiveKeys.all, "traffic"],
    metrics: () => [...defensiveKeys.all, "traffic", "metrics"],
  },

  // Threat Intelligence
  threatIntel: {
    ip: (ipAddress) => [...defensiveKeys.all, "threat-intel", "ip", ipAddress],
    domain: (domain) => [
      ...defensiveKeys.all,
      "threat-intel",
      "domain",
      domain,
    ],
    hash: (hash) => [...defensiveKeys.all, "threat-intel", "hash", hash],
  },
};

// ============================================================================
// OFFENSIVE
// ============================================================================
export const offensiveKeys = {
  all: ["offensive"],

  // Metrics
  metrics: () => [...offensiveKeys.all, "metrics"],
  health: () => [...offensiveKeys.all, "health"],

  // Network Reconnaissance
  scans: (limit) =>
    limit
      ? [...offensiveKeys.all, "scans", limit]
      : [...offensiveKeys.all, "scans"],
  scan: (id) => [...offensiveKeys.all, "scans", id],

  // Workflows
  workflows: () => [...offensiveKeys.all, "workflows"],
  workflow: (id) => [...offensiveKeys.all, "workflows", id],

  // C2 Orchestration
  c2Sessions: (framework) =>
    framework
      ? [...offensiveKeys.all, "c2", "sessions", framework]
      : [...offensiveKeys.all, "c2", "sessions"],

  // BAS (Breach & Attack Simulation)
  bas: {
    techniques: (tactic, platform) => {
      const key = [...offensiveKeys.all, "bas", "techniques"];
      if (tactic) key.push(tactic);
      if (platform) key.push(platform);
      return key;
    },
    coverage: (organizationId) => [
      ...offensiveKeys.all,
      "bas",
      "coverage",
      organizationId,
    ],
  },
};

// ============================================================================
// PURPLE TEAM
// ============================================================================
export const purpleKeys = {
  all: ["purple"],
  correlations: () => [...purpleKeys.all, "correlations"],
  gaps: () => [...purpleKeys.all, "gaps"],
};

// ============================================================================
// MAXIMUS AI
// ============================================================================
export const maximusKeys = {
  all: ["maximus"],
  health: () => [...maximusKeys.all, "health"],
  chat: (sessionId) => [...maximusKeys.all, "chat", sessionId],
  tools: () => [...maximusKeys.all, "tools"],
};

// ============================================================================
// HITL (Human-in-the-Loop)
// ============================================================================
export const hitlKeys = {
  all: ["hitl"],

  // Reviews
  reviews: (filters) =>
    filters
      ? [...hitlKeys.all, "reviews", filters]
      : [...hitlKeys.all, "reviews"],
  review: (id) => [...hitlKeys.all, "reviews", id],

  // Stats
  stats: () => [...hitlKeys.all, "stats"],

  // Decisions
  decisions: () => [...hitlKeys.all, "decisions"],
};

// ============================================================================
// OSINT
// ============================================================================
export const osintKeys = {
  all: ["osint"],
  domain: (domain) => [...osintKeys.all, "domain", domain],
  ip: (ip) => [...osintKeys.all, "ip", ip],
};

// ============================================================================
// SERVICES
// ============================================================================
export const serviceKeys = {
  all: ["service"],
  health: (serviceId) => [...serviceKeys.all, "health", serviceId],
  metrics: (serviceId) => [...serviceKeys.all, "metrics", serviceId],
};

// ============================================================================
// MAIN EXPORT
// ============================================================================
export const queryKeys = {
  defensive: defensiveKeys,
  offensive: offensiveKeys,
  purple: purpleKeys,
  maximus: maximusKeys,
  hitl: hitlKeys,
  osint: osintKeys,
  service: serviceKeys,
};

export default queryKeys;

/**
 * Test Fixtures - PropTypes Compliant
 *
 * Provides realistic test data with correct types for PropTypes validation
 * All IDs are strings, timestamps are ISO strings, numbers are numbers
 */

/**
 * Generate unique ID (string format)
 */
let idCounter = 0;
export function generateId(prefix = "test") {
  return `${prefix}-${++idCounter}-${Date.now()}`;
}

/**
 * Generate ISO timestamp string
 */
export function generateTimestamp(offsetMs = 0) {
  return new Date(Date.now() + offsetMs).toISOString();
}

/**
 * Alert fixture (PropTypes compliant)
 */
export function createAlertFixture(overrides = {}) {
  return {
    id: generateId("alert"),
    type: "threat",
    severity: "high",
    title: "Test Alert",
    message: "Test alert message",
    timestamp: generateTimestamp(),
    source: "test-source",
    status: "active",
    ...overrides,
  };
}

/**
 * Verdict fixture (PropTypes compliant)
 */
export function createVerdictFixture(overrides = {}) {
  return {
    id: generateId("verdict"),
    timestamp: generateTimestamp(),
    threat_level: "high",
    confidence: 0.95,
    verdict: "malicious",
    source_ip: "192.168.1.100",
    destination_ip: "10.0.0.50",
    protocol: "TCP",
    port: 443,
    indicators: ["suspicious-pattern", "known-malware"],
    details: {
      description: "Test threat detected",
      recommendation: "Block immediately",
    },
    ...overrides,
  };
}

/**
 * Node fixture for topology (PropTypes compliant)
 */
export function createNodeFixture(overrides = {}) {
  return {
    id: generateId("node"),
    label: "Test Node",
    type: "server",
    status: "active",
    ip: "192.168.1.1",
    position: { x: 0, y: 0 },
    metadata: {
      os: "Linux",
      version: "5.10",
    },
    ...overrides,
  };
}

/**
 * Edge fixture for topology (PropTypes compliant)
 */
export function createEdgeFixture(overrides = {}) {
  return {
    id: generateId("edge"),
    source: generateId("node-src"),
    target: generateId("node-tgt"),
    type: "connection",
    label: "Test Connection",
    weight: 1.0,
    ...overrides,
  };
}

/**
 * Attack fixture (PropTypes compliant)
 */
export function createAttackFixture(overrides = {}) {
  return {
    id: generateId("attack"),
    timestamp: generateTimestamp(),
    type: "brute-force",
    severity: "critical",
    source: "203.0.113.42",
    target: "192.168.1.10",
    status: "detected",
    description: "Brute force attack detected",
    techniques: ["T1110.001", "T1078"],
    mitigation_status: "in-progress",
    ...overrides,
  };
}

/**
 * Metric fixture (PropTypes compliant)
 */
export function createMetricFixture(overrides = {}) {
  return {
    id: generateId("metric"),
    timestamp: generateTimestamp(),
    name: "cpu_usage",
    value: 75.5,
    unit: "percent",
    source: "server-1",
    tags: ["performance", "monitoring"],
    ...overrides,
  };
}

/**
 * User fixture (PropTypes compliant)
 */
export function createUserFixture(overrides = {}) {
  return {
    id: generateId("user"),
    username: "testuser",
    email: "test@example.com",
    role: "analyst",
    status: "active",
    created_at: generateTimestamp(-86400000), // 1 day ago
    last_login: generateTimestamp(-3600000), // 1 hour ago
    permissions: ["read", "write"],
    ...overrides,
  };
}

/**
 * Service fixture (PropTypes compliant)
 */
export function createServiceFixture(overrides = {}) {
  return {
    id: generateId("service"),
    name: "test-service",
    status: "running",
    health: "healthy",
    uptime: 3600,
    version: "1.0.0",
    url: "http://localhost:5000",
    last_check: generateTimestamp(),
    ...overrides,
  };
}

/**
 * Log entry fixture (PropTypes compliant)
 */
export function createLogFixture(overrides = {}) {
  return {
    id: generateId("log"),
    timestamp: generateTimestamp(),
    level: "info",
    message: "Test log message",
    source: "test-component",
    metadata: {
      context: "test",
      details: "additional information",
    },
    ...overrides,
  };
}

/**
 * Notification fixture (PropTypes compliant)
 */
export function createNotificationFixture(overrides = {}) {
  return {
    id: generateId("notification"),
    timestamp: generateTimestamp(),
    type: "info",
    title: "Test Notification",
    message: "This is a test notification",
    read: false,
    action_url: "/dashboard",
    ...overrides,
  };
}

/**
 * Generate array of fixtures
 */
export function createFixtures(factoryFn, count = 5, overrides = {}) {
  return Array.from({ length: count }, (_, i) =>
    factoryFn({ ...overrides, index: i }),
  );
}

/**
 * Batch fixtures for common test scenarios
 */
export const fixtures = {
  // Multiple alerts
  alerts: () => createFixtures(createAlertFixture, 3),

  // Multiple verdicts
  verdicts: () => createFixtures(createVerdictFixture, 5),

  // Network topology
  topology: () => ({
    nodes: createFixtures(createNodeFixture, 10),
    edges: createFixtures(createEdgeFixture, 15),
  }),

  // Attack timeline
  attacks: () => createFixtures(createAttackFixture, 7),

  // Metrics dashboard
  metrics: () => createFixtures(createMetricFixture, 20),

  // User management
  users: () => createFixtures(createUserFixture, 4),

  // Service health
  services: () => createFixtures(createServiceFixture, 6),

  // Logs
  logs: () => createFixtures(createLogFixture, 50),

  // Notifications
  notifications: () => createFixtures(createNotificationFixture, 10),
};

/**
 * Reset ID counter (useful for consistent test snapshots)
 */
export function resetFixtureIds() {
  idCounter = 0;
}

/**
 * CockpitSoberano Component Tests
 * Smoke tests following Padrão Pagani
 * 
 * @version 1.0.0
 */

import { describe, it, expect, vi } from 'vitest';

// Mock hooks to avoid WebSocket and API calls in tests
vi.mock('../hooks/useVerdictStream', () => ({
  useVerdictStream: () => ({
    verdicts: [],
    isConnected: false,
    stats: {},
    dismissVerdict: vi.fn()
  })
}));

vi.mock('../hooks/useCockpitMetrics', () => ({
  useCockpitMetrics: () => ({
    metrics: {
      totalAgents: 0,
      activeAgents: 0,
      totalVerdicts: 0,
      criticalVerdicts: 0,
      alliancesDetected: 0,
      deceptionMarkers: 0,
      avgProcessingLatency: 0,
      systemHealth: 'UNKNOWN'
    },
    loading: false,
    error: null
  })
}));

vi.mock('../hooks/useAllianceGraph', () => ({
  useAllianceGraph: () => ({
    graphData: { nodes: [], edges: [] },
    loading: false,
    error: null
  })
}));

vi.mock('../hooks/useCommandBus', () => ({
  useCommandBus: () => ({
    sendCommand: vi.fn(),
    loading: false,
    error: null,
    lastCommand: null
  })
}));

describe('CockpitSoberano Dashboard', () => {
  it('exports CockpitSoberano component', async () => {
    const module = await import('../CockpitSoberano');
    expect(module.CockpitSoberano).toBeDefined();
    expect(typeof module.CockpitSoberano).toBe('function');
  });

  it('exports default export', async () => {
    const module = await import('../CockpitSoberano');
    expect(module.default).toBeDefined();
  });
});

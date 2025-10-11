/**
 * Maximus AI Integration Tests
 * =============================
 *
 * End-to-end integration tests for Maximus AI features:
 * - FASE 8: Enhanced Cognition (Narrative Analysis, Threat Prediction)
 * - FASE 9: Immune Enhancement (FP Suppression, Memory Consolidation)
 * - FASE 10: Distributed Organism (Edge Agents, Topology)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { waitFor } from '@testing-library/react';
import * as maximusAI from '../../api/maximusAI';

// Mock fetch globally
global.fetch = vi.fn();

describe('Maximus AI Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch.mockClear();
  });

  describe('FASE 8 - Enhanced Cognition Workflow', () => {
    it('should complete narrative analysis workflow', async () => {
      const mockResponse = {
        analysis: {
          manipulation_score: 0.78,
          fallacies: ['ad hominem', 'straw man'],
          credibility: 0.42
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await maximusAI.analyzeNarrative('Test narrative content');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/maximus/narrative-analysis',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('Test narrative content')
        })
      );

      expect(result.analysis.manipulation_score).toBe(0.78);
      expect(result.analysis.fallacies).toHaveLength(2);
    });

    it('should complete threat prediction workflow', async () => {
      const mockResponse = {
        predicted_attacks: [
          { type: 'Ransomware', confidence: 0.85, timeline: '24h' }
        ],
        vuln_forecast: [
          { cve: 'CVE-2024-1234', exploit_probability: 0.91 }
        ],
        hunting_recommendations: [
          'Monitor for PowerShell execution',
          'Check for lateral movement'
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const context = {
        recent_alerts: [],
        historical_events: [],
        current_environment: 'production'
      };

      const result = await maximusAI.predictThreats(context, {
        timeHorizon: 24,
        minConfidence: 0.7
      });

      expect(result.predicted_attacks).toHaveLength(1);
      expect(result.vuln_forecast).toHaveLength(1);
      expect(result.hunting_recommendations).toHaveLength(2);
    });
  });

  describe('FASE 9 - Immune Enhancement Workflow', () => {
    it('should complete false positive suppression workflow', async () => {
      const alerts = [
        { id: 'alert_001', severity: 'high', entity: '192.168.1.10', type: 'port_scan' },
        { id: 'alert_002', severity: 'medium', entity: '10.0.0.5', type: 'brute_force' }
      ];

      const mockResponse = {
        total_alerts: 2,
        suppressed_count: 1,
        suppressed_alerts: ['alert_001'],
        avg_tolerance_score: 0.85,
        details: {
          alert_001: { suppressed: true, tolerance_score: 0.92 },
          alert_002: { suppressed: false, tolerance_score: 0.45 }
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await maximusAI.suppressFalsePositives(alerts, 0.7);

      expect(result.total_alerts).toBe(2);
      expect(result.suppressed_count).toBe(1);
      expect(result.suppressed_alerts).toContain('alert_001');
      expect(result.avg_tolerance_score).toBeGreaterThan(0.7);
    });

    it('should complete memory consolidation workflow', async () => {
      const mockResponse = {
        patterns_count: 15,
        ltm_entries_created: 10,
        duration_ms: 380,
        patterns: [
          { type: 'Attack Chain', frequency: 5, importance: 0.92 },
          { type: 'IOC Pattern', frequency: 8, importance: 0.88 }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await maximusAI.consolidateMemory({
        manual: true,
        threshold: 0.7
      });

      expect(result.patterns_count).toBe(15);
      expect(result.ltm_entries_created).toBe(10);
      expect(result.patterns).toHaveLength(2);
    });

    it('should complete LTM query workflow', async () => {
      const mockResponse = {
        memories: [
          {
            pattern_type: 'Ransomware',
            importance: 0.95,
            description: 'WannaCry-like behavior detected in 5 incidents',
            first_seen: '2024-01-15T10:00:00Z',
            last_seen: '2024-03-20T14:30:00Z',
            frequency: 5
          },
          {
            pattern_type: 'Lateral Movement',
            importance: 0.88,
            description: 'SMB enumeration and exploitation pattern',
            first_seen: '2024-02-10T08:15:00Z',
            last_seen: '2024-03-22T16:45:00Z',
            frequency: 8
          }
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await maximusAI.queryLongTermMemory('ransomware campaigns', {
        limit: 5,
        minImportance: 0.7
      });

      expect(result.memories).toHaveLength(2);
      expect(result.memories[0].pattern_type).toBe('Ransomware');
      expect(result.memories[0].importance).toBeGreaterThan(0.9);
    });
  });

  describe('FASE 10 - Distributed Organism Workflow', () => {
    it('should complete edge agent status workflow', async () => {
      const mockResponse = {
        agent_id: 'edge-us-east-001',
        health: 'healthy',
        metrics: {
          buffer_utilization: 45,
          events_per_second: 250,
          compression_ratio: 0.68,
          uptime_seconds: 86400
        },
        capabilities: ['detection', 'compression', 'local_analysis']
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await maximusAI.getEdgeStatus('edge-us-east-001');

      expect(result.agent_id).toBe('edge-us-east-001');
      expect(result.health).toBe('healthy');
      expect(result.metrics.buffer_utilization).toBeLessThan(50);
      expect(result.capabilities).toContain('detection');
    });

    it('should complete global metrics workflow', async () => {
      const mockResponse = {
        time_window_seconds: 60,
        events_per_second: 2500,
        avg_compression_ratio: 0.72,
        p95_latency_ms: 38,
        total_events: 5000000,
        total_bytes: 104857600,
        active_agents: 12,
        healthy_agents: 11
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await maximusAI.getGlobalMetrics(60);

      expect(result.events_per_second).toBeGreaterThan(2000);
      expect(result.avg_compression_ratio).toBeGreaterThan(0.7);
      expect(result.p95_latency_ms).toBeLessThan(50);
      expect(result.active_agents).toBe(12);
    });

    it('should complete topology discovery workflow', async () => {
      const mockResponse = {
        agent_count: 8,
        healthy_count: 7,
        regions: ['us-east', 'eu-west', 'ap-south'],
        agents: [
          {
            id: 'edge-001',
            health: 'healthy',
            location: 'us-east-1a',
            buffer_utilization: 45,
            events_per_second: 250
          },
          {
            id: 'edge-002',
            health: 'degraded',
            location: 'eu-west-1b',
            buffer_utilization: 78,
            events_per_second: 180
          }
        ],
        network_graph: {
          nodes: 8,
          edges: 12
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await maximusAI.getTopology();

      expect(result.agent_count).toBe(8);
      expect(result.regions).toHaveLength(3);
      expect(result.agents).toHaveLength(2);
      expect(result.network_graph.nodes).toBe(8);
    });
  });

  describe('Cross-FASE Integration Workflows', () => {
    it('should complete AI reasoning + tool orchestration workflow', async () => {
      // Step 1: AI Reasoning
      const reasoningResponse = {
        reasoning_chain: [
          { step: 1, thought: 'Analyzing threat context' },
          { step: 2, thought: 'Identifying best tool' }
        ],
        conclusion: 'Use network_scan tool',
        confidence: 0.92
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => reasoningResponse
      });

      const reasoning = await maximusAI.aiReason('Analyze suspicious network activity');
      expect(reasoning.conclusion).toContain('network_scan');

      // Step 2: Tool Orchestration
      const toolResponse = {
        tool_name: 'network_scan',
        result: {
          scan_id: 'scan_123',
          status: 'completed',
          findings: ['open_port_22', 'open_port_80']
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => toolResponse
      });

      const toolResult = await maximusAI.callTool('network_scan', { target: '192.168.1.0/24' });
      expect(toolResult.result.findings).toHaveLength(2);
    });

    it('should complete multi-phase workflow: prediction → suppression → consolidation', async () => {
      // Phase 1: Threat Prediction
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          predicted_attacks: [{ type: 'Ransomware', confidence: 0.85 }]
        })
      });

      const prediction = await maximusAI.predictThreats({}, { timeHorizon: 24 });
      expect(prediction.predicted_attacks).toHaveLength(1);

      // Phase 2: FP Suppression (after alerts generated)
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_alerts: 10,
          suppressed_count: 3,
          avg_tolerance_score: 0.75
        })
      });

      const suppression = await maximusAI.suppressFalsePositives([], 0.7);
      expect(suppression.suppressed_count).toBeGreaterThan(0);

      // Phase 3: Memory Consolidation
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patterns_count: 5,
          ltm_entries_created: 3
        })
      });

      const consolidation = await maximusAI.consolidateMemory({ manual: true });
      expect(consolidation.ltm_entries_created).toBeGreaterThan(0);
    });

    it('should handle distributed workflow: edge → central → consolidation', async () => {
      // Step 1: Query edge agent status
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          agent_id: 'edge-001',
          health: 'healthy',
          metrics: { events_per_second: 250 }
        })
      });

      const edgeStatus = await maximusAI.getEdgeStatus('edge-001');
      expect(edgeStatus.health).toBe('healthy');

      // Step 2: Get global metrics from central coordinator
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          events_per_second: 2500,
          active_agents: 10
        })
      });

      const globalMetrics = await maximusAI.getGlobalMetrics(60);
      expect(globalMetrics.active_agents).toBeGreaterThan(0);

      // Step 3: Consolidate distributed patterns
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patterns_count: 15,
          distributed_patterns: true
        })
      });

      const consolidation = await maximusAI.consolidateMemory({ manual: true });
      expect(consolidation.patterns_count).toBeGreaterThan(0);
    });
  });

  describe('Error Recovery and Resilience', () => {
    it('should handle API failures gracefully', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable'
      });

      await expect(
        maximusAI.predictThreats({}, {})
      ).rejects.toThrow('Maximus API Error: 503');
    });

    it('should handle network timeouts', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network timeout'));

      await expect(
        maximusAI.getTopology()
      ).rejects.toThrow('Network timeout');
    });

    it('should handle malformed responses', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => { throw new Error('Invalid JSON'); }
      });

      await expect(
        maximusAI.analyzeNarrative('test')
      ).rejects.toThrow();
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle concurrent API calls', async () => {
      const mockResponse = { success: true };
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const promises = [
        maximusAI.getEdgeStatus('edge-001'),
        maximusAI.getGlobalMetrics(60),
        maximusAI.getTopology(),
        maximusAI.predictThreats({}, {}),
        maximusAI.suppressFalsePositives([], 0.7)
      ];

      const results = await Promise.all(promises);
      expect(results).toHaveLength(5);
      expect(global.fetch).toHaveBeenCalledTimes(5);
    });

    it('should handle large payload processing', async () => {
      const largeAlertSet = Array.from({ length: 1000 }, (_, i) => ({
        id: `alert_${i}`,
        severity: 'medium',
        entity: `192.168.1.${i % 255}`,
        type: 'port_scan'
      }));

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_alerts: 1000,
          suppressed_count: 350
        })
      });

      const result = await maximusAI.suppressFalsePositives(largeAlertSet, 0.7);
      expect(result.total_alerts).toBe(1000);
    });
  });
});

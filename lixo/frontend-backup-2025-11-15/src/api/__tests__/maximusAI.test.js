/**
 * Maximus AI API Client Tests
 * ============================
 *
 * Tests for all Maximus AI API functions
 * Coverage target: 100%
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  analyzeWithAI,
  aiReason,
  callTool,
  getToolCatalog,
  orchestrateWorkflow,
  aiFullAssessment,
  aiOSINTInvestigation,
  aiPurpleTeamExercise,
  getAIMemory,
  addToMemory,
  chatWithMaximus,
  synthesizeIntelligence,
  getAISuggestions,
  getMaximusHealth,
  getAIStats,
} from "../maximusAI";

const MAXIMUS_BASE_URL = "http://34.148.161.131:8000";

describe("maximusAI API Client", () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = vi.fn();
  });

  // ==========================================================================
  // AI ANALYSIS & REASONING
  // ==========================================================================

  describe("analyzeWithAI", () => {
    it("should analyze data successfully", async () => {
      const mockResponse = {
        success: true,
        analysis: "Test analysis",
        insights: ["insight1", "insight2"],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await analyzeWithAI(
        { target: "192.168.1.1" },
        { mode: "deep" },
      );

      expect(global.fetch).toHaveBeenCalledWith(
        `${MAXIMUS_BASE_URL}/api/analyze`,
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: expect.stringContaining("target"),
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle API failure", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const result = await analyzeWithAI({ data: "test" });

      expect(result.success).toBe(false);
      expect(result.error).toContain("AI Analysis failed");
    });
  });

  describe("aiReason", () => {
    it("should perform reasoning with chain-of-thought", async () => {
      const mockResponse = {
        success: true,
        reasoning_steps: ["step1", "step2"],
        conclusion: "Final conclusion",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await aiReason(
        "What is the threat level?",
        "chain_of_thought",
      );

      expect(global.fetch).toHaveBeenCalledWith(
        `${MAXIMUS_BASE_URL}/api/reason`,
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("chain_of_thought"),
        }),
      );
      expect(result).toEqual(mockResponse);
    });
  });

  // ==========================================================================
  // TOOL CALLING
  // ==========================================================================

  describe("callTool", () => {
    it("should call a tool successfully", async () => {
      const mockResponse = {
        success: true,
        result: { data: "tool result" },
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await callTool("network_recon_tool", {
        target: "10.0.0.1",
      });

      expect(global.fetch).toHaveBeenCalledWith(
        `${MAXIMUS_BASE_URL}/api/tool-call`,
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("network_recon_tool"),
        }),
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getToolCatalog", () => {
    it("should retrieve tool catalog", async () => {
      const mockCatalog = {
        success: true,
        tools: [
          { name: "network_recon_tool", description: "Scan networks" },
          { name: "vuln_intel_tool", description: "Check vulnerabilities" },
        ],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCatalog,
      });

      const result = await getToolCatalog();

      expect(global.fetch).toHaveBeenCalledWith(
        `${MAXIMUS_BASE_URL}/api/tools`,
      );
      expect(result.tools).toHaveLength(2);
    });
  });

  // ==========================================================================
  // ORCHESTRATION & WORKFLOWS
  // ==========================================================================

  describe("orchestrateWorkflow", () => {
    it("should orchestrate multi-service workflow", async () => {
      const mockResponse = {
        success: true,
        workflow_id: "wf_123",
        status: "running",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const workflow = {
        type: "full_assessment",
        target: "192.168.1.1",
        steps: [],
      };

      const result = await orchestrateWorkflow(workflow);

      expect(result.workflow_id).toBe("wf_123");
    });
  });

  describe("aiFullAssessment", () => {
    it("should create full assessment workflow", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, workflow_id: "wf_456" }),
      });

      const result = await aiFullAssessment("10.0.0.5", { scanType: "deep" });

      expect(global.fetch).toHaveBeenCalledWith(
        `${MAXIMUS_BASE_URL}/api/orchestrate`,
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("full_assessment"),
        }),
      );
      expect(result.success).toBe(true);
    });
  });

  describe("aiOSINTInvestigation", () => {
    it("should create OSINT investigation workflow", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await aiOSINTInvestigation("test@example.com", "email");

      expect(global.fetch).toHaveBeenCalledWith(
        `${MAXIMUS_BASE_URL}/api/orchestrate`,
        expect.objectContaining({
          body: expect.stringContaining("osint_investigation"),
        }),
      );
    });
  });

  describe("aiPurpleTeamExercise", () => {
    it("should create purple team exercise workflow", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await aiPurpleTeamExercise("T1190", "10.0.0.1", ["siem", "edr"]);

      expect(global.fetch).toHaveBeenCalledWith(
        `${MAXIMUS_BASE_URL}/api/orchestrate`,
        expect.objectContaining({
          body: expect.stringContaining("purple_team"),
        }),
      );
    });
  });

  // ==========================================================================
  // MEMORY & CONTEXT
  // ==========================================================================

  describe("getAIMemory", () => {
    it("should retrieve AI memory", async () => {
      const mockMemory = {
        success: true,
        memories: [{ type: "semantic", content: "Memory 1" }],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemory,
      });

      const result = await getAIMemory("session_123", "short_term");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/memory"),
        expect.anything(),
      );
      expect(result.memories).toBeDefined();
    });
  });

  describe("addToMemory", () => {
    it("should add information to memory", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, memory_id: "mem_789" }),
      });

      const result = await addToMemory(
        { event: "threat_detected", details: "Malware found" },
        "episodic",
        "high",
      );

      expect(result.success).toBe(true);
    });
  });

  // ==========================================================================
  // CHAT & STREAMING
  // ==========================================================================

  describe("chatWithMaximus", () => {
    it("should send chat message (non-streaming)", async () => {
      const mockResponse = {
        success: true,
        response: "AI response here",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await chatWithMaximus("What are the current threats?");

      expect(result.success).toBe(true);
      expect(result.response).toBe("AI response here");
    });
  });

  // ==========================================================================
  // FASE 8: ENHANCED COGNITION
  // ==========================================================================

  describe("analyzeNarrative", () => {
    it("should analyze narrative text", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          result: { manipulation_score: 0.8, techniques: ["bandwagon"] },
        }),
      });

      const result = await callTool("analyze_narrative", {
        text: "Test narrative",
        analysis_type: "comprehensive",
      });

      expect(result.success).toBe(true);
    });
  });

  describe("predictThreats", () => {
    it("should predict future threats", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          result: {
            predictions: [{ threat: "ransomware", probability: 0.75 }],
          },
        }),
      });

      const result = await callTool("predict_threats", {
        context: { asset: "server1" },
        time_horizon_hours: 24,
      });

      expect(result.success).toBe(true);
    });
  });

  // ==========================================================================
  // FASE 9: IMMUNE ENHANCEMENT
  // ==========================================================================

  describe("suppressFalsePositives", () => {
    it("should suppress false positive alerts", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          result: { suppressed_count: 2, total_alerts: 5 },
        }),
      });

      const alerts = [
        { id: "a1", severity: "high" },
        { id: "a2", severity: "low" },
      ];

      const result = await callTool("suppress_false_positives", {
        alerts,
        suppression_threshold: 0.7,
      });

      expect(result.success).toBe(true);
    });
  });

  describe("consolidateMemory", () => {
    it("should trigger memory consolidation", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          result: { ltm_entries_created: 10, patterns_count: 5 },
        }),
      });

      const result = await callTool("consolidate_memory", {
        trigger_manual: true,
        importance_threshold: 0.6,
      });

      expect(result.success).toBe(true);
    });
  });

  describe("queryLongTermMemory", () => {
    it("should query long-term memory", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          result: {
            memories: [{ pattern_type: "attack_chain", importance: 0.9 }],
          },
        }),
      });

      const result = await callTool("query_long_term_memory", {
        query: "ransomware patterns",
        limit: 5,
      });

      expect(result.success).toBe(true);
    });
  });

  // ==========================================================================
  // FASE 10: DISTRIBUTED ORGANISM
  // ==========================================================================

  describe("getEdgeStatus", () => {
    it("should get edge agent status", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          result: { agents: [{ id: "edge1", status: "online" }] },
        }),
      });

      const result = await callTool("get_edge_status", { agent_id: null });

      expect(result.success).toBe(true);
    });
  });

  describe("getTopology", () => {
    it("should get distributed organism topology", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          result: { nodes: 5, edges: 8 },
        }),
      });

      const result = await callTool("get_topology", {});

      expect(result.success).toBe(true);
    });
  });

  // ==========================================================================
  // HEALTH & STATUS
  // ==========================================================================

  describe("getMaximusHealth", () => {
    it("should check Maximus health successfully", async () => {
      const mockHealth = {
        status: "healthy",
        version: "1.0.0",
        uptime: 3600,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealth,
      });

      const result = await getMaximusHealth();

      expect(global.fetch).toHaveBeenCalledWith(`${MAXIMUS_BASE_URL}/health`);
      expect(result.status).toBe("healthy");
    });

    it("should handle health check failure", async () => {
      global.fetch.mockRejectedValueOnce(new Error("Network error"));

      const result = await getMaximusHealth();

      expect(result.success).toBe(false);
      expect(result.status).toBe("offline");
    });
  });

  describe("getAIStats", () => {
    it("should retrieve AI statistics", async () => {
      const mockStats = {
        total_requests: 1000,
        avg_response_time_ms: 250,
        tool_calls: 500,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      });

      const result = await getAIStats();

      expect(result.total_requests).toBe(1000);
    });
  });

  // ==========================================================================
  // INTELLIGENCE SYNTHESIS
  // ==========================================================================

  describe("synthesizeIntelligence", () => {
    it("should synthesize intelligence from multiple sources", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          synthesis: "Combined intelligence",
          recommendations: ["rec1", "rec2"],
        }),
      });

      const sources = [
        { type: "threat_intel", data: {} },
        { type: "vuln_scan", data: {} },
      ];

      const result = await synthesizeIntelligence(sources, "Security overview");

      expect(result.synthesis).toBeDefined();
    });
  });

  describe("getAISuggestions", () => {
    it("should get AI-powered suggestions", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          suggestions: [{ action: "patch_server", priority: "high" }],
        }),
      });

      const result = await getAISuggestions(
        { incident_id: "inc_123" },
        "next_action",
      );

      expect(result.suggestions).toBeDefined();
    });
  });
});

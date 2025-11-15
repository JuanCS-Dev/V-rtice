/**
 * OffensiveService Tests
 * ======================
 *
 * Comprehensive test suite for OffensiveService
 * Target: 90%+ coverage
 * Governed by: Constituição Vértice v2.5 - ADR-004 (Testing Strategy)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { OffensiveService, getOffensiveService } from "../OffensiveService";
import { ServiceEndpoints } from "@/config/endpoints";

// Mock dependencies
vi.mock("@/config/endpoints", () => ({
  ServiceEndpoints: {
    apiGateway: "http://34.148.161.131:8000",
    offensive: {
      gateway: "http://34.148.161.131:8000",
      networkRecon: "http://34.148.161.131:8000",
      vulnIntel: "http://34.148.161.131:8000",
      webAttack: "http://34.148.161.131:8000",
      c2Orchestration: "http://34.148.161.131:8000",
      bas: "http://34.148.161.131:8000",
    },
  },
  AuthConfig: {
    apiKey: "test-api-key",
    google: {
      clientId: "test-client-id",
    },
  },
  httpToWs: (url) => url.replace(/^http/, "ws"),
}));

vi.mock("@/utils/logger", () => ({
  default: {
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}));

vi.mock("@/utils/security", () => ({
  getCSRFToken: vi.fn(() => "mock-csrf-token"),
  checkRateLimit: vi.fn(),
  RateLimitError: class RateLimitError extends Error {
    constructor(message, retryAfter) {
      super(message);
      this.retryAfter = retryAfter;
    }
  },
}));

// ============================================================================
// TEST SUITE
// ============================================================================

describe("OffensiveService", () => {
  let service;
  let mockClient;

  beforeEach(() => {
    // Mock API client
    mockClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    };

    service = new OffensiveService(mockClient);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ──────────────────────────────────────────────────────────────────────────
  // CONSTRUCTOR
  // ──────────────────────────────────────────────────────────────────────────

  describe("constructor", () => {
    it("should initialize with correct base endpoint", () => {
      expect(service.baseEndpoint).toBe("http://34.148.161.131:8000");
    });

    it("should store all service endpoints", () => {
      expect(service.endpoints).toHaveProperty("networkRecon");
      expect(service.endpoints).toHaveProperty("vulnIntel");
      expect(service.endpoints).toHaveProperty("webAttack");
      expect(service.endpoints).toHaveProperty("c2");
      expect(service.endpoints).toHaveProperty("bas");
      expect(service.endpoints).toHaveProperty("gateway");
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // NETWORK RECONNAISSANCE
  // ──────────────────────────────────────────────────────────────────────────

  describe("scanNetwork", () => {
    it("should execute network scan with correct parameters", async () => {
      const mockResponse = { success: true, scan_id: "scan-123" };
      mockClient.post.mockResolvedValue(mockResponse);

      const result = await service.scanNetwork(
        "192.168.1.0/24",
        "quick",
        "1-1000",
      );

      expect(mockClient.post).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/scan",
        {
          target: "192.168.1.0/24",
          scan_type: "quick",
          ports: "1-1000",
        },
      );

      expect(result).toHaveProperty("scanId", "scan-123");
    });

    it("should use default scan parameters", async () => {
      mockClient.post.mockResolvedValue({ success: true });

      await service.scanNetwork("192.168.1.1");

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          scan_type: "quick",
          ports: "1-1000",
        }),
      );
    });

    it("should validate target format", async () => {
      await expect(service.scanNetwork("invalid-target")).rejects.toThrow(
        "Invalid target format",
      );
    });
  });

  describe("getScanStatus", () => {
    it("should get scan status by ID", async () => {
      const mockStatus = { status: "running", progress: 50 };
      mockClient.get.mockResolvedValue(mockStatus);

      const result = await service.getScanStatus("scan-123");

      expect(mockClient.get).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/scan/scan-123/status",
      );
      expect(result).toEqual(mockStatus);
    });

    it("should throw error if scan ID is missing", async () => {
      await expect(service.getScanStatus()).rejects.toThrow(
        "Scan ID is required",
      );
    });
  });

  describe("listScans", () => {
    it("should list recent scans with default limit", async () => {
      const mockScans = [{ id: "scan-1" }, { id: "scan-2" }];
      mockClient.get.mockResolvedValue(mockScans);

      const result = await service.listScans();

      expect(mockClient.get).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/scans",
        { params: { limit: 50 } },
      );
      expect(result).toEqual(mockScans);
    });

    it("should list scans with custom limit", async () => {
      mockClient.get.mockResolvedValue([]);

      await service.listScans(100);

      expect(mockClient.get).toHaveBeenCalledWith(expect.any(String), {
        params: { limit: 100 },
      });
    });
  });

  describe("discoverHosts", () => {
    it("should discover hosts in network", async () => {
      const mockHosts = { hosts: ["192.168.1.1", "192.168.1.2"] };
      mockClient.post.mockResolvedValue(mockHosts);

      const result = await service.discoverHosts("192.168.1.0/24");

      expect(mockClient.post).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/discover",
        { network: "192.168.1.0/24" },
      );
      expect(result).toEqual(mockHosts);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // VULNERABILITY INTELLIGENCE
  // ──────────────────────────────────────────────────────────────────────────

  describe("searchCVE", () => {
    it("should search CVE by ID", async () => {
      const mockCVE = { id: "CVE-2024-1234", severity: "HIGH" };
      mockClient.get.mockResolvedValue(mockCVE);

      const result = await service.searchCVE("CVE-2024-1234");

      expect(mockClient.get).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/cve/CVE-2024-1234",
      );
      expect(result).toEqual(mockCVE);
    });

    it("should validate CVE ID format", async () => {
      await expect(service.searchCVE("invalid-cve")).rejects.toThrow(
        "Invalid CVE ID format",
      );
    });

    it("should require CVE ID", async () => {
      await expect(service.searchCVE()).rejects.toThrow(
        "Invalid CVE ID format",
      );
    });
  });

  describe("searchVulnerabilities", () => {
    it("should search vulnerabilities with query", async () => {
      const mockResults = [{ cve: "CVE-2024-1" }];
      mockClient.get.mockResolvedValue(mockResults);

      const result = await service.searchVulnerabilities("apache");

      expect(mockClient.get).toHaveBeenCalled();
      expect(result).toEqual(mockResults);
    });

    it("should include filters in search", async () => {
      mockClient.get.mockResolvedValue([]);

      await service.searchVulnerabilities("nginx", { severity: "high" });

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining("severity=high"),
      );
    });
  });

  describe("getExploits", () => {
    it("should get exploits for CVE", async () => {
      const mockExploits = [{ name: "exploit-1" }];
      mockClient.get.mockResolvedValue(mockExploits);

      const result = await service.getExploits("CVE-2024-1234");

      expect(mockClient.get).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/cve/CVE-2024-1234/exploits",
      );
      expect(result).toEqual(mockExploits);
    });

    it("should require CVE ID", async () => {
      await expect(service.getExploits()).rejects.toThrow("CVE ID is required");
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // WEB ATTACK SURFACE
  // ──────────────────────────────────────────────────────────────────────────

  describe("scanWebTarget", () => {
    it("should scan web target with default profile", async () => {
      const mockResult = { scan_id: "web-scan-123", success: true };
      mockClient.post.mockResolvedValue(mockResult);

      const result = await service.scanWebTarget("https://example.com");

      expect(mockClient.post).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/scan",
        expect.objectContaining({
          url: "https://example.com",
          scan_profile: "full",
          auth_config: null,
        }),
      );
      // After transformation, snake_case should become camelCase
      expect(result.scanId || result.scan_id).toBeDefined();
    });

    it("should validate URL format", async () => {
      await expect(service.scanWebTarget("not-a-url")).rejects.toThrow(
        "Invalid URL format",
      );
    });

    it("should accept custom scan profile", async () => {
      mockClient.post.mockResolvedValue({});

      await service.scanWebTarget("https://example.com", "quick");

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ scan_profile: "quick" }),
      );
    });
  });

  describe("runWebTest", () => {
    it("should run specific web test", async () => {
      const mockResult = { vulnerabilities: [] };
      mockClient.post.mockResolvedValue(mockResult);

      const result = await service.runWebTest("https://example.com", "sqli");

      expect(mockClient.post).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/test/sqli",
        expect.objectContaining({ url: "https://example.com" }),
      );
      expect(result).toEqual(mockResult);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // C2 ORCHESTRATION
  // ──────────────────────────────────────────────────────────────────────────

  describe("createC2Session", () => {
    it("should create C2 session", async () => {
      const mockSession = { session_id: "c2-session-123", success: true };
      mockClient.post.mockResolvedValue(mockSession);

      const result = await service.createC2Session(
        "metasploit",
        "192.168.1.100",
        "reverse_tcp",
      );

      expect(mockClient.post).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/session/create",
        expect.objectContaining({
          framework: "metasploit",
          target_host: "192.168.1.100",
          payload: "reverse_tcp",
        }),
      );
      // After transformation, snake_case should become camelCase
      expect(result.sessionId || result.session_id).toBeDefined();
    });
  });

  describe("listC2Sessions", () => {
    it("should list all C2 sessions", async () => {
      const mockSessions = [{ id: "session-1" }];
      mockClient.get.mockResolvedValue(mockSessions);

      const result = await service.listC2Sessions();

      expect(mockClient.get).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/sessions",
      );
      expect(result).toEqual(mockSessions);
    });

    it("should filter by framework", async () => {
      mockClient.get.mockResolvedValue([]);

      await service.listC2Sessions("cobalt_strike");

      expect(mockClient.get).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/sessions?framework=cobalt_strike",
      );
    });
  });

  describe("executeC2Command", () => {
    it("should execute command in C2 session", async () => {
      const mockOutput = { output: "command result" };
      mockClient.post.mockResolvedValue(mockOutput);

      const result = await service.executeC2Command("session-123", "sysinfo");

      expect(mockClient.post).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/session/session-123/execute",
        expect.objectContaining({
          command: "sysinfo",
          args: [],
        }),
      );
      expect(result).toEqual(mockOutput);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // BAS (BREACH & ATTACK SIMULATION)
  // ──────────────────────────────────────────────────────────────────────────

  describe("runAttackSimulation", () => {
    it("should run MITRE ATT&CK simulation", async () => {
      const mockResult = { success: true, detected: false };
      mockClient.post.mockResolvedValue(mockResult);

      const result = await service.runAttackSimulation(
        "T1078",
        "192.168.1.100",
        "windows",
      );

      expect(mockClient.post).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/simulate",
        expect.objectContaining({
          technique_id: "T1078",
          target_host: "192.168.1.100",
          platform: "windows",
        }),
      );
      expect(result).toEqual(mockResult);
    });
  });

  describe("listAttackTechniques", () => {
    it("should list all techniques", async () => {
      const mockTechniques = [{ id: "T1078" }];
      mockClient.get.mockResolvedValue(mockTechniques);

      const result = await service.listAttackTechniques();

      expect(mockClient.get).toHaveBeenCalled();
      expect(result).toEqual(mockTechniques);
    });

    it("should filter by tactic and platform", async () => {
      mockClient.get.mockResolvedValue([]);

      await service.listAttackTechniques("credential-access", "linux");

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining("tactic=credential-access"),
      );
      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining("platform=linux"),
      );
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // WORKFLOWS
  // ──────────────────────────────────────────────────────────────────────────

  describe("createWorkflow", () => {
    it("should create workflow", async () => {
      const mockWorkflow = { workflow_id: "wf-123" };
      mockClient.post.mockResolvedValue(mockWorkflow);

      const config = { name: "Test Workflow", steps: [] };
      const result = await service.createWorkflow(config);

      expect(result).toHaveProperty("workflowId");
    });
  });

  describe("executeWorkflow", () => {
    it("should execute workflow with context", async () => {
      const mockExecution = { execution_id: "exec-123" };
      mockClient.post.mockResolvedValue(mockExecution);

      const result = await service.executeWorkflow("wf-123", {
        target: "192.168.1.1",
      });

      expect(result).toBeDefined();
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // METRICS & HEALTH
  // ──────────────────────────────────────────────────────────────────────────

  describe("getMetrics", () => {
    it("should aggregate metrics from all services", async () => {
      mockClient.get
        .mockResolvedValueOnce({ count: 5 }) // activeScans
        .mockResolvedValueOnce({ count: 12 }) // exploitsFound
        .mockResolvedValueOnce({ count: 3 }) // targets
        .mockResolvedValueOnce({ count: 2 }); // c2Sessions

      const result = await service.getMetrics();

      expect(result).toEqual({
        activeScans: 5,
        exploitsFound: 12,
        targets: 3,
        c2Sessions: 2,
      });
    });

    it("should return zero metrics on error", async () => {
      mockClient.get.mockRejectedValue(new Error("Network error"));

      const result = await service.getMetrics();

      expect(result).toEqual({
        activeScans: 0,
        exploitsFound: 0,
        targets: 0,
        c2Sessions: 0,
      });
    });

    it("should handle partial failures gracefully", async () => {
      mockClient.get
        .mockResolvedValueOnce({ count: 5 })
        .mockRejectedValueOnce(new Error("Service down"))
        .mockResolvedValueOnce({ count: 3 })
        .mockRejectedValueOnce(new Error("Timeout"));

      const result = await service.getMetrics();

      expect(result.activeScans).toBe(5);
      expect(result.targets).toBe(3);
      expect(result.exploitsFound).toBe(0);
      expect(result.c2Sessions).toBe(0);
    });
  });

  describe("checkHealth", () => {
    it("should check health of all services", async () => {
      mockClient.get.mockResolvedValue({ status: "ok" });

      const result = await service.checkHealth();

      expect(result).toHaveProperty("networkRecon");
      expect(result).toHaveProperty("vulnIntel");
      expect(result).toHaveProperty("webAttack");
      expect(result).toHaveProperty("c2Orchestration");
      expect(result).toHaveProperty("bas");
      expect(result).toHaveProperty("offensiveGateway");
    });

    it("should mark unavailable services as false", async () => {
      mockClient.get
        .mockResolvedValueOnce({ status: "ok" })
        .mockRejectedValueOnce(new Error("Down"))
        .mockResolvedValueOnce({ status: "ok" })
        .mockRejectedValueOnce(new Error("Down"))
        .mockResolvedValueOnce({ status: "ok" })
        .mockResolvedValueOnce({ status: "ok" });

      const result = await service.checkHealth();

      expect(result.networkRecon).toBe(true);
      expect(result.vulnIntel).toBe(false);
      expect(result.c2Orchestration).toBe(false);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // VALIDATION
  // ──────────────────────────────────────────────────────────────────────────

  describe("validateRequest", () => {
    it("should validate IP addresses", () => {
      expect(() =>
        service.validateRequest({ target: "192.168.1.1" }),
      ).not.toThrow();
      expect(() =>
        service.validateRequest({ target: "192.168.1.0/24" }),
      ).not.toThrow();
    });

    it("should reject invalid IP addresses", () => {
      expect(() =>
        service.validateRequest({ target: "999.999.999.999" }),
      ).toThrow();
      expect(() => service.validateRequest({ target: "not-an-ip" })).toThrow();
    });

    it("should validate URLs", () => {
      expect(() =>
        service.validateRequest({ url: "https://example.com" }),
      ).not.toThrow();
      expect(() => service.validateRequest({ url: "not-a-url" })).toThrow();
    });

    it("should validate CVE IDs", () => {
      expect(() =>
        service.validateRequest({ cveId: "CVE-2024-1234" }),
      ).not.toThrow();
      expect(() => service.validateRequest({ cveId: "invalid" })).toThrow();
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // SINGLETON
  // ──────────────────────────────────────────────────────────────────────────

  describe("getOffensiveService", () => {
    it("should return singleton instance", () => {
      const instance1 = getOffensiveService();
      const instance2 = getOffensiveService();

      expect(instance1).toBe(instance2);
    });

    it("should return OffensiveService instance", () => {
      const instance = getOffensiveService();

      expect(instance).toBeInstanceOf(OffensiveService);
    });
  });
});

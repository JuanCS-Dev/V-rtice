/**
 * Offensive Services API Client Tests
 * ====================================
 *
 * Tests for all 6 offensive security services:
 * - Network Reconnaissance (8032)
 * - Vulnerability Intelligence (8033)
 * - Web Attack Surface (8034)
 * - C2 Orchestration (8035)
 * - Breach & Attack Simulation (8036)
 * - Offensive Gateway (8037)
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  scanNetwork,
  getScanStatus,
  listScans,
  discoverHosts,
  searchCVE,
  searchVulnerabilities,
  getExploits,
  correlateWithScan,
  scanWebTarget,
  runWebTest,
  getWebScanReport,
  createC2Session,
  listC2Sessions,
  executeC2Command,
  passSession,
  executeAttackChain,
  runAttackSimulation,
  listAttackTechniques,
  validatePurpleTeam,
  getAttackCoverage,
  createWorkflow,
  executeWorkflow,
  getWorkflowStatus,
  listWorkflows,
  checkOffensiveServicesHealth,
} from "../offensiveServices";

describe("offensiveServices API Client", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  // ==========================================================================
  // NETWORK RECONNAISSANCE (8032)
  // ==========================================================================

  describe("Network Reconnaissance", () => {
    it("should scan network successfully", async () => {
      const mockResponse = {
        success: true,
        scan_id: "scan_123",
        status: "running",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await scanNetwork("192.168.1.0/24", "quick", "1-1000");

      expect(global.fetch).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/scan",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("192.168.1.0/24"),
        }),
      );
      expect(result.scan_id).toBe("scan_123");
    });

    it("should handle scan failure", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const result = await scanNetwork("10.0.0.0/24");

      expect(result.success).toBe(false);
      expect(result.error).toContain("Network scan failed");
    });

    it("should get scan status", async () => {
      const mockStatus = {
        scan_id: "scan_123",
        status: "completed",
        hosts_found: 15,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus,
      });

      const result = await getScanStatus("scan_123");

      expect(result.status).toBe("completed");
      expect(result.hosts_found).toBe(15);
    });

    it("should list recent scans", async () => {
      const mockScans = {
        scans: [
          { scan_id: "scan_1", target: "10.0.0.0/24" },
          { scan_id: "scan_2", target: "192.168.1.0/24" },
        ],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockScans,
      });

      const result = await listScans(50);

      expect(result.scans).toHaveLength(2);
    });

    it("should discover hosts", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ hosts_found: 10, online: 8 }),
      });

      const result = await discoverHosts("172.16.0.0/24");

      expect(result.hosts_found).toBe(10);
    });
  });

  // ==========================================================================
  // VULNERABILITY INTELLIGENCE (8033)
  // ==========================================================================

  describe("Vulnerability Intelligence", () => {
    it("should search CVE by ID", async () => {
      const mockCVE = {
        cve_id: "CVE-2024-1234",
        description: "Remote code execution",
        cvss_score: 9.8,
        severity: "critical",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCVE,
      });

      const result = await searchCVE("CVE-2024-1234");

      expect(result.cve_id).toBe("CVE-2024-1234");
      expect(result.severity).toBe("critical");
    });

    it("should search vulnerabilities by product", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          vulnerabilities: [
            { cve_id: "CVE-2024-1", product: "apache" },
            { cve_id: "CVE-2024-2", product: "apache" },
          ],
        }),
      });

      const result = await searchVulnerabilities("apache", {
        severity: "high",
      });

      expect(result.vulnerabilities).toHaveLength(2);
    });

    it("should get exploits for CVE", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          exploits: [
            { type: "metasploit", module: "exploit/windows/smb/ms17_010" },
          ],
        }),
      });

      const result = await getExploits("CVE-2017-0144");

      expect(result.exploits).toBeDefined();
    });

    it("should correlate vulnerabilities with scan", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          matches: 5,
          critical: 2,
          high: 3,
        }),
      });

      const result = await correlateWithScan("scan_123");

      expect(result.matches).toBe(5);
    });
  });

  // ==========================================================================
  // WEB ATTACK SURFACE (8034)
  // ==========================================================================

  describe("Web Attack Surface", () => {
    it("should scan web target", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          scan_id: "web_scan_1",
          vulnerabilities_found: 12,
        }),
      });

      const result = await scanWebTarget("https://example.com", "full");

      expect(result.scan_id).toBe("web_scan_1");
    });

    it("should run specific web test", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          test_type: "sqli",
          vulnerable: true,
          payloads_tested: 50,
        }),
      });

      const result = await runWebTest("https://example.com/login", "sqli");

      expect(result.test_type).toBe("sqli");
    });

    it("should get web scan report", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          scan_id: "web_scan_1",
          report: { findings: 10, severity_breakdown: {} },
        }),
      });

      const result = await getWebScanReport("web_scan_1");

      expect(result.report).toBeDefined();
    });
  });

  // ==========================================================================
  // C2 ORCHESTRATION (8035)
  // ==========================================================================

  describe("C2 Orchestration", () => {
    it("should create C2 session", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: "c2_session_1",
          framework: "cobalt_strike",
          status: "active",
        }),
      });

      const result = await createC2Session(
        "cobalt_strike",
        "10.0.0.5",
        "windows/x64/meterpreter/reverse_tcp",
      );

      expect(result.session_id).toBe("c2_session_1");
    });

    it("should list C2 sessions", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          sessions: [
            { session_id: "s1", framework: "metasploit" },
            { session_id: "s2", framework: "cobalt_strike" },
          ],
        }),
      });

      const result = await listC2Sessions();

      expect(result.sessions).toHaveLength(2);
    });

    it("should execute C2 command", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          command: "sysinfo",
          output: "Windows Server 2019...",
        }),
      });

      const result = await executeC2Command("session_1", "sysinfo");

      expect(result.output).toContain("Windows");
    });

    it("should pass session between frameworks", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          new_session_id: "session_2",
        }),
      });

      const result = await passSession("session_1", "metasploit");

      expect(result.success).toBe(true);
    });

    it("should execute attack chain", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          chain_id: "chain_1",
          steps_completed: 3,
          status: "running",
        }),
      });

      const chainConfig = {
        target: "10.0.0.5",
        steps: ["recon", "exploit", "persist"],
      };

      const result = await executeAttackChain(chainConfig);

      expect(result.chain_id).toBe("chain_1");
    });
  });

  // ==========================================================================
  // BREACH & ATTACK SIMULATION (8036)
  // ==========================================================================

  describe("Breach & Attack Simulation", () => {
    it("should run attack simulation", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          simulation_id: "sim_1",
          technique_id: "T1190",
          status: "completed",
          detected: false,
        }),
      });

      const result = await runAttackSimulation("T1190", "10.0.0.10", "windows");

      expect(result.technique_id).toBe("T1190");
    });

    it("should list attack techniques", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          techniques: [
            { id: "T1190", name: "Exploit Public-Facing Application" },
            { id: "T1078", name: "Valid Accounts" },
          ],
        }),
      });

      const result = await listAttackTechniques("TA0001", "windows");

      expect(result.techniques).toHaveLength(2);
    });

    it("should validate purple team exercise", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          detected: true,
          detection_time_seconds: 45,
          siem_alerts: 3,
        }),
      });

      const result = await validatePurpleTeam("sim_1", ["siem", "edr"]);

      expect(result.detected).toBe(true);
    });

    it("should get attack coverage", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_techniques: 200,
          simulated: 50,
          coverage_percentage: 25,
        }),
      });

      const result = await getAttackCoverage("org_1");

      expect(result.coverage_percentage).toBe(25);
    });
  });

  // ==========================================================================
  // OFFENSIVE GATEWAY (8037)
  // ==========================================================================

  describe("Offensive Gateway", () => {
    it("should create workflow", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          workflow_id: "wf_1",
          status: "created",
        }),
      });

      const workflowConfig = {
        name: "Full penetration test",
        steps: [],
      };

      const result = await createWorkflow(workflowConfig);

      expect(result.workflow_id).toBe("wf_1");
    });

    it("should execute workflow", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          execution_id: "exec_1",
          status: "running",
        }),
      });

      const result = await executeWorkflow("wf_1", { target: "10.0.0.0/24" });

      expect(result.execution_id).toBe("exec_1");
    });

    it("should get workflow status", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          execution_id: "exec_1",
          progress: 75,
          status: "running",
        }),
      });

      const result = await getWorkflowStatus("exec_1");

      expect(result.progress).toBe(75);
    });

    it("should list workflows", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          workflows: [
            { workflow_id: "wf_1", name: "Pentest" },
            { workflow_id: "wf_2", name: "Red Team" },
          ],
        }),
      });

      const result = await listWorkflows();

      expect(result.workflows).toHaveLength(2);
    });
  });

  // ==========================================================================
  // HEALTH CHECKS
  // ==========================================================================

  describe("checkOffensiveServicesHealth", () => {
    it("should check all services health", async () => {
      // Mock all 6 service health checks
      global.fetch
        .mockResolvedValueOnce({ ok: true }) // networkRecon
        .mockResolvedValueOnce({ ok: true }) // vulnIntel
        .mockResolvedValueOnce({ ok: true }) // webAttack
        .mockResolvedValueOnce({ ok: true }) // c2Orchestration
        .mockResolvedValueOnce({ ok: true }) // bas
        .mockResolvedValueOnce({ ok: true }); // offensiveGateway

      const result = await checkOffensiveServicesHealth();

      expect(result.networkRecon).toBe(true);
      expect(result.vulnIntel).toBe(true);
      expect(result.webAttack).toBe(true);
      expect(result.c2Orchestration).toBe(true);
      expect(result.bas).toBe(true);
      expect(result.offensiveGateway).toBe(true);
    });

    it("should handle service unavailability", async () => {
      // Some services offline
      global.fetch
        .mockResolvedValueOnce({ ok: true }) // networkRecon OK
        .mockRejectedValueOnce(new Error("timeout")) // vulnIntel FAIL
        .mockResolvedValueOnce({ ok: false, status: 500 }) // webAttack FAIL
        .mockResolvedValueOnce({ ok: true }) // c2Orchestration OK
        .mockResolvedValueOnce({ ok: true }) // bas OK
        .mockResolvedValueOnce({ ok: true }); // offensiveGateway OK

      const result = await checkOffensiveServicesHealth();

      expect(result.networkRecon).toBe(true);
      expect(result.vulnIntel).toBe(false);
      expect(result.webAttack).toBe(false);
      expect(result.c2Orchestration).toBe(true);
    });
  });
});

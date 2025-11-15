/**
 * Cyber Services API Client Tests
 * ================================
 *
 * Tests for cyber intelligence services:
 * - IP Intelligence (8000)
 * - Threat Intelligence (8013)
 * - Malware Analysis (8011)
 * - SSL Monitor (8012)
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { analyzeIP, checkThreatIntelligence } from "../cyberServices";

describe("cyberServices API Client", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  // ==========================================================================
  // IP INTELLIGENCE (8000)
  // ==========================================================================

  describe("analyzeIP", () => {
    it("should analyze IP successfully with full data", async () => {
      const mockResponse = {
        success: true,
        source: "live",
        ip: "8.8.8.8",
        timestamp: "2025-10-06T10:00:00Z",
        geolocation: {
          status: "success",
          country: "United States",
          countryCode: "US",
          regionName: "California",
          city: "Mountain View",
          zip: "94035",
          lat: 37.386,
          lon: -122.0838,
          timezone: "America/Los_Angeles",
          isp: "Google LLC",
          org: "Google Public DNS",
          as: "AS15169 Google LLC",
        },
        ptr_record: "dns.google",
        whois: {
          registrar: "ARIN",
          network: "8.8.8.0/24",
        },
        reputation: {
          score: 100,
          threat_level: "clean",
          categories: ["dns", "infrastructure"],
          last_seen: null,
        },
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await analyzeIP("8.8.8.8");

      expect(global.fetch).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/ip/analyze",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: expect.stringContaining("8.8.8.8"),
        }),
      );

      expect(result.success).toBe(true);
      expect(result.ip).toBe("8.8.8.8");
      expect(result.geolocation.country).toBe("United States");
      expect(result.geolocation.lat).toBe(37.386);
      expect(result.geolocation.asn).toBe("AS15169");
      expect(result.geolocation.asnName).toBe("Google LLC");
      expect(result.reputation.score).toBe(100);
      expect(result.reputation.threatLevel).toBe("clean");
    });

    it("should handle malicious IP detection", async () => {
      const mockResponse = {
        success: true,
        ip: "185.220.101.23",
        geolocation: {
          status: "success",
          country: "Unknown",
          lat: 0,
          lon: 0,
        },
        reputation: {
          score: 10,
          threat_level: "malicious",
          categories: ["tor", "proxy"],
          last_seen: "2025-10-05T12:00:00Z",
        },
        ptr_record: "tor-exit-node.example.com",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await analyzeIP("185.220.101.23");

      expect(result.reputation.threatLevel).toBe("malicious");
      expect(result.reputation.categories).toContain("tor");
    });

    it("should handle API failure", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const result = await analyzeIP("192.168.1.1");

      expect(result.success).toBe(false);
      expect(result.error).toContain("IP Analysis failed");
    });

    it("should handle network errors", async () => {
      global.fetch.mockRejectedValueOnce(new Error("Network timeout"));

      const result = await analyzeIP("10.0.0.1");

      expect(result.success).toBe(false);
      expect(result.error).toContain("Network timeout");
    });

    it("should handle missing geolocation", async () => {
      const mockResponse = {
        success: true,
        ip: "192.168.1.1",
        geolocation: {
          status: "fail",
        },
        reputation: null,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await analyzeIP("192.168.1.1");

      expect(result.geolocation).toBeNull();
    });

    it("should parse ASN correctly", async () => {
      const mockResponse = {
        success: true,
        ip: "1.1.1.1",
        geolocation: {
          status: "success",
          as: "AS13335 Cloudflare, Inc.",
          country: "Australia",
          lat: -33.494,
          lon: 143.2104,
        },
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await analyzeIP("1.1.1.1");

      expect(result.geolocation.asn).toBe("AS13335");
      expect(result.geolocation.asnName).toBe("Cloudflare, Inc.");
    });
  });

  // ==========================================================================
  // THREAT INTELLIGENCE (8013)
  // ==========================================================================

  describe("checkThreatIntelligence", () => {
    it("should check threat intelligence for IP", async () => {
      const mockResponse = {
        success: true,
        target: "45.142.212.61",
        target_type: "ip",
        threats_found: 3,
        threat_sources: [
          { source: "AbuseIPDB", score: 100, reports: 50 },
          { source: "VirusTotal", score: 8, positives: 8, total: 90 },
        ],
        reputation: "malicious",
        categories: ["botnet", "spam"],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await checkThreatIntelligence("45.142.212.61", "ip");

      expect(global.fetch).toHaveBeenCalledWith(
        "http://34.148.161.131:8000/api/threat-intel/check",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("45.142.212.61"),
        }),
      );

      expect(result.reputation).toBe("malicious");
      expect(result.threats_found).toBe(3);
    });

    it("should check threat intelligence for domain", async () => {
      const mockResponse = {
        success: true,
        target: "evil.com",
        target_type: "domain",
        reputation: "suspicious",
        categories: ["phishing"],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await checkThreatIntelligence("evil.com", "domain");

      expect(result.target_type).toBe("domain");
      expect(result.categories).toContain("phishing");
    });

    it("should check threat intelligence for hash", async () => {
      const mockResponse = {
        success: true,
        target: "a1b2c3d4e5f6...",
        target_type: "hash",
        malware_family: "WannaCry",
        reputation: "malicious",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await checkThreatIntelligence("a1b2c3d4e5f6...", "hash");

      expect(result.malware_family).toBe("WannaCry");
    });

    it("should handle clean target", async () => {
      const mockResponse = {
        success: true,
        target: "8.8.8.8",
        threats_found: 0,
        reputation: "clean",
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await checkThreatIntelligence("8.8.8.8");

      expect(result.reputation).toBe("clean");
      expect(result.threats_found).toBe(0);
    });

    it("should handle API failure", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
      });

      const result = await checkThreatIntelligence("test.com");

      expect(result.success).toBe(false);
    });
  });

  // ==========================================================================
  // ERROR HANDLING
  // ==========================================================================

  describe("Error Handling", () => {
    it("should handle fetch network errors gracefully", async () => {
      global.fetch.mockRejectedValueOnce(new Error("Failed to fetch"));

      const result = await analyzeIP("10.0.0.1");

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it("should handle invalid JSON responses", async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error("Invalid JSON");
        },
      });

      const result = await analyzeIP("192.168.1.1");

      expect(result.success).toBe(false);
    });

    it("should handle timeout errors", async () => {
      global.fetch.mockImplementationOnce(() =>
        Promise.reject(new Error("Request timeout")),
      );

      const result = await checkThreatIntelligence("test.com");

      expect(result.success).toBe(false);
      expect(result.error).toContain("timeout");
    });
  });
});

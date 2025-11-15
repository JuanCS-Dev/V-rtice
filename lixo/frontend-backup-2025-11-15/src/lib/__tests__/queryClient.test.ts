/**
 * QueryClient Configuration Tests
 *
 * DOUTRINA VÉRTICE - GAP #9 (P1)
 * Tests for QueryClient configuration
 *
 * Following Boris Cherny: "Tests or it didn't happen"
 */

import { describe, it, expect, beforeEach } from "vitest";
import {
  createQueryClient,
  queryKeys,
  mutationKeys,
  invalidateScans,
  invalidateVulnerabilities,
  invalidateMetrics,
} from "../queryClient";

describe("queryClient", () => {
  describe("createQueryClient", () => {
    it("should create QueryClient with correct configuration", () => {
      const queryClient = createQueryClient();

      expect(queryClient).toBeDefined();
      expect(queryClient.getDefaultOptions()).toBeDefined();
    });

    it("should have correct query defaults", () => {
      const queryClient = createQueryClient();
      const defaults = queryClient.getDefaultOptions().queries;

      expect(defaults?.staleTime).toBe(1000 * 60 * 5); // 5 minutes
      expect(defaults?.gcTime).toBe(1000 * 60 * 10); // 10 minutes
      expect(defaults?.refetchOnWindowFocus).toBe(true);
      expect(defaults?.refetchOnReconnect).toBe(true);
      expect(defaults?.refetchOnMount).toBe(true);
      expect(defaults?.throwOnError).toBe(false);
    });

    it("should have correct mutation defaults", () => {
      const queryClient = createQueryClient();
      const defaults = queryClient.getDefaultOptions().mutations;

      expect(defaults?.networkMode).toBe("offlineFirst");
      expect(defaults?.throwOnError).toBe(false);
      expect(typeof defaults?.retry).toBe("function");
      expect(typeof defaults?.retryDelay).toBe("function");
    });

    it("should retry server errors", () => {
      const queryClient = createQueryClient();
      const retry = queryClient.getDefaultOptions().mutations
        ?.retry as Function;

      // Retry 5xx errors
      const serverError = { response: { status: 500 } };
      expect(retry(0, serverError)).toBe(true);
      expect(retry(1, serverError)).toBe(true);
      expect(retry(2, serverError)).toBe(true);
      expect(retry(3, serverError)).toBe(false); // Max retries
    });

    it("should not retry client errors", () => {
      const queryClient = createQueryClient();
      const retry = queryClient.getDefaultOptions().mutations
        ?.retry as Function;

      // Don't retry 4xx errors
      const clientError = { response: { status: 400 } };
      expect(retry(0, clientError)).toBe(false);

      const notFoundError = { response: { status: 404 } };
      expect(retry(0, notFoundError)).toBe(false);
    });

    it("should not retry auth errors", () => {
      const queryClient = createQueryClient();
      const retry = queryClient.getDefaultOptions().mutations
        ?.retry as Function;

      const authError = { error_code: "AUTH_001" };
      expect(retry(0, authError)).toBe(false);

      const authError2 = { errorCode: "AUTH_EXPIRED_TOKEN" };
      expect(retry(0, authError2)).toBe(false);
    });

    it("should not retry validation errors", () => {
      const queryClient = createQueryClient();
      const retry = queryClient.getDefaultOptions().mutations
        ?.retry as Function;

      const valError = { error_code: "VAL_001" };
      expect(retry(0, valError)).toBe(false);

      const valError2 = { errorCode: "VAL_INVALID_INPUT" };
      expect(retry(0, valError2)).toBe(false);
    });

    it("should use exponential backoff for retry delay", () => {
      const queryClient = createQueryClient();
      const retryDelay = queryClient.getDefaultOptions().mutations
        ?.retryDelay as Function;

      expect(retryDelay(0)).toBe(1000); // 1s
      expect(retryDelay(1)).toBe(2000); // 2s
      expect(retryDelay(2)).toBe(4000); // 4s
      expect(retryDelay(3)).toBe(8000); // 8s
      expect(retryDelay(10)).toBe(30000); // Cap at 30s
    });
  });

  describe("queryKeys", () => {
    it("should have health key", () => {
      expect(queryKeys.health).toEqual(["health"]);
    });

    it("should have scan keys", () => {
      expect(queryKeys.scan.all).toEqual(["scans"]);
      expect(queryKeys.scan.lists()).toEqual(["scans", "list"]);
      expect(queryKeys.scan.list({ status: "active" })).toEqual([
        "scans",
        "list",
        { filters: { status: "active" } },
      ]);
      expect(queryKeys.scan.details()).toEqual(["scans", "detail"]);
      expect(queryKeys.scan.detail("123")).toEqual(["scans", "detail", "123"]);
    });

    it("should have vulnerability keys", () => {
      expect(queryKeys.vulnerability.all).toEqual(["vulnerabilities"]);
      expect(queryKeys.vulnerability.lists()).toEqual([
        "vulnerabilities",
        "list",
      ]);
      expect(queryKeys.vulnerability.list({ severity: "high" })).toEqual([
        "vulnerabilities",
        "list",
        { filters: { severity: "high" } },
      ]);
      expect(queryKeys.vulnerability.details()).toEqual([
        "vulnerabilities",
        "detail",
      ]);
      expect(queryKeys.vulnerability.detail("456")).toEqual([
        "vulnerabilities",
        "detail",
        "456",
      ]);
    });

    it("should have metrics keys", () => {
      expect(queryKeys.metrics.all).toEqual(["metrics"]);
      expect(queryKeys.metrics.dashboard()).toEqual(["metrics", "dashboard"]);
      expect(queryKeys.metrics.timeRange("7d")).toEqual([
        "metrics",
        "timeRange",
        "7d",
      ]);
    });

    it("should generate unique keys for different filters", () => {
      const key1 = queryKeys.scan.list({ status: "active" });
      const key2 = queryKeys.scan.list({ status: "completed" });

      expect(key1).not.toEqual(key2);
    });
  });

  describe("mutationKeys", () => {
    it("should have scan mutation keys", () => {
      expect(mutationKeys.scan.start).toEqual(["scan", "start"]);
      expect(mutationKeys.scan.stop("123")).toEqual(["scan", "stop", "123"]);
      expect(mutationKeys.scan.delete("456")).toEqual([
        "scan",
        "delete",
        "456",
      ]);
    });

    it("should have vulnerability mutation keys", () => {
      expect(mutationKeys.vulnerability.acknowledge("123")).toEqual([
        "vulnerability",
        "acknowledge",
        "123",
      ]);
      expect(mutationKeys.vulnerability.ignore("456")).toEqual([
        "vulnerability",
        "ignore",
        "456",
      ]);
    });

    it("should generate unique keys for different IDs", () => {
      const key1 = mutationKeys.scan.stop("123");
      const key2 = mutationKeys.scan.stop("456");

      expect(key1).not.toEqual(key2);
    });
  });

  describe("invalidation helpers", () => {
    let queryClient: ReturnType<typeof createQueryClient>;

    beforeEach(() => {
      queryClient = createQueryClient();
    });

    it("invalidateScans should invalidate scan queries", async () => {
      // Set some scan data
      queryClient.setQueryData(queryKeys.scan.all, { scans: [] });

      // Invalidate
      await invalidateScans(queryClient);

      // Query should be invalidated (stale)
      const state = queryClient.getQueryState(queryKeys.scan.all);
      expect(state?.isInvalidated).toBe(true);
    });

    it("invalidateVulnerabilities should invalidate vulnerability queries", async () => {
      // Set some vulnerability data
      queryClient.setQueryData(queryKeys.vulnerability.all, {
        vulnerabilities: [],
      });

      // Invalidate
      await invalidateVulnerabilities(queryClient);

      // Query should be invalidated
      const state = queryClient.getQueryState(queryKeys.vulnerability.all);
      expect(state?.isInvalidated).toBe(true);
    });

    it("invalidateMetrics should invalidate metrics queries", async () => {
      // Set some metrics data
      queryClient.setQueryData(queryKeys.metrics.all, { metrics: {} });

      // Invalidate
      await invalidateMetrics(queryClient);

      // Query should be invalidated
      const state = queryClient.getQueryState(queryKeys.metrics.all);
      expect(state?.isInvalidated).toBe(true);
    });

    it("should only invalidate matching queries", async () => {
      // Set data for different query types
      queryClient.setQueryData(queryKeys.scan.all, { scans: [] });
      queryClient.setQueryData(queryKeys.vulnerability.all, {
        vulnerabilities: [],
      });

      // Invalidate only scans
      await invalidateScans(queryClient);

      // Scans should be invalidated
      const scanState = queryClient.getQueryState(queryKeys.scan.all);
      expect(scanState?.isInvalidated).toBe(true);

      // Vulnerabilities should NOT be invalidated
      const vulnState = queryClient.getQueryState(queryKeys.vulnerability.all);
      expect(vulnState?.isInvalidated).toBe(false);
    });
  });
});

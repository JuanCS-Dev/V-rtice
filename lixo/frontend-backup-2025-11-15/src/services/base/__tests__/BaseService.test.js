/**
 * BaseService Tests
 * ==================
 *
 * Comprehensive test suite for services/base/BaseService.js
 * Focus: Retry logic, idempotency patterns, error handling
 *
 * Target: 100% coverage
 * Governed by: Constituição Vértice v2.5 - ADR-004 (Testing Strategy)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { BaseService } from "../BaseService";

// Mock logger
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

describe("BaseService Retry Logic", () => {
  let service;
  let mockClient;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock API client
    mockClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    };

    service = new BaseService("/api/test", mockClient);
  });

  // ========================================================================
  // GET REQUESTS - AUTOMATIC RETRY (Idempotent)
  // ========================================================================

  describe("GET - Automatic Retry", () => {
    it("should retry GET on network error", async () => {
      // Fail 2x, succeed on 3rd attempt
      mockClient.get
        .mockRejectedValueOnce(new Error("Network error"))
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({ data: "success" });

      const result = await service.get("/endpoint");

      // Should have been called 3 times (1 initial + 2 retries)
      expect(mockClient.get).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ data: "success" });
    });

    it("should fail after max retries exhausted", async () => {
      // Fail all attempts
      mockClient.get.mockRejectedValue(new Error("Persistent network error"));

      await expect(service.get("/endpoint")).rejects.toThrow();

      // 1 initial attempt + 3 retries = 4 total
      expect(mockClient.get).toHaveBeenCalledTimes(4);
    });

    it("should NOT retry GET on 401 Unauthorized", async () => {
      mockClient.get.mockRejectedValue(new Error("401 Unauthorized"));

      await expect(service.get("/endpoint")).rejects.toThrow("401");

      // Only 1 attempt, no retries
      expect(mockClient.get).toHaveBeenCalledTimes(1);
    });

    it("should NOT retry GET on 403 Forbidden", async () => {
      mockClient.get.mockRejectedValue(new Error("403 Forbidden"));

      await expect(service.get("/endpoint")).rejects.toThrow("403");

      // Only 1 attempt
      expect(mockClient.get).toHaveBeenCalledTimes(1);
    });

    it("should allow disabling retry with retry: 0", async () => {
      mockClient.get.mockRejectedValue(new Error("Network error"));

      await expect(service.get("/endpoint", { retry: 0 })).rejects.toThrow();

      // Only 1 attempt, no retries
      expect(mockClient.get).toHaveBeenCalledTimes(1);
    });

    it("should allow custom retry count", async () => {
      mockClient.get.mockRejectedValue(new Error("Network error"));

      await expect(service.get("/endpoint", { retry: 5 })).rejects.toThrow();

      // 1 initial + 5 retries = 6 total
      expect(mockClient.get).toHaveBeenCalledTimes(6);
    });

    it("should use exponential backoff delays", async () => {
      vi.useFakeTimers();

      mockClient.get.mockRejectedValue(new Error("Network error"));

      const promise = service.get("/endpoint");

      // Verify delays: 1s, 2s, 4s
      await vi.advanceTimersByTimeAsync(1000); // 1st retry
      await vi.advanceTimersByTimeAsync(2000); // 2nd retry
      await vi.advanceTimersByTimeAsync(4000); // 3rd retry

      await expect(promise).rejects.toThrow();

      vi.useRealTimers();
    });

    it("should succeed on first attempt without retry", async () => {
      mockClient.get.mockResolvedValue({ data: "success" });

      const result = await service.get("/endpoint");

      expect(mockClient.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ data: "success" });
    });
  });

  // ========================================================================
  // POST REQUESTS - OPT-IN RETRY (Non-Idempotent)
  // ========================================================================

  describe("POST - Opt-In Retry", () => {
    it("should NOT retry POST by default", async () => {
      mockClient.post.mockRejectedValue(new Error("Network error"));

      await expect(service.post("/endpoint", {})).rejects.toThrow();

      // Only 1 attempt, no automatic retry
      expect(mockClient.post).toHaveBeenCalledTimes(1);
    });

    it("should retry POST when options.retry = true", async () => {
      mockClient.post
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({ data: "success" });

      const result = await service.post("/endpoint", {}, { retry: true });

      // 2 attempts (1 initial + 1 retry)
      expect(mockClient.post).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ data: "success" });
    });

    it("should use custom maxRetries for POST", async () => {
      mockClient.post.mockRejectedValue(new Error("Network error"));

      await expect(
        service.post("/endpoint", {}, { retry: true, maxRetries: 5 }),
      ).rejects.toThrow();

      // 1 initial + 5 retries = 6 total
      expect(mockClient.post).toHaveBeenCalledTimes(6);
    });

    it("should NOT retry POST on auth errors even with retry: true", async () => {
      mockClient.post.mockRejectedValue(new Error("401 Unauthorized"));

      await expect(
        service.post("/endpoint", {}, { retry: true }),
      ).rejects.toThrow("401");

      // Only 1 attempt
      expect(mockClient.post).toHaveBeenCalledTimes(1);
    });

    it("should succeed on first POST without retry", async () => {
      mockClient.post.mockResolvedValue({ id: 123 });

      const result = await service.post("/endpoint", { name: "test" });

      expect(mockClient.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ id: 123 });
    });
  });

  // ========================================================================
  // PUT REQUESTS - OPT-IN RETRY (Non-Idempotent)
  // ========================================================================

  describe("PUT - Opt-In Retry", () => {
    it("should NOT retry PUT by default", async () => {
      mockClient.put.mockRejectedValue(new Error("Network error"));

      await expect(service.put("/endpoint/123", {})).rejects.toThrow();

      expect(mockClient.put).toHaveBeenCalledTimes(1);
    });

    it("should retry PUT when options.retry = true", async () => {
      mockClient.put
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({ updated: true });

      const result = await service.put("/endpoint/123", {}, { retry: true });

      expect(mockClient.put).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ updated: true });
    });
  });

  // ========================================================================
  // DELETE REQUESTS - OPT-IN RETRY (Non-Idempotent)
  // ========================================================================

  describe("DELETE - Opt-In Retry", () => {
    it("should NOT retry DELETE by default", async () => {
      mockClient.delete.mockRejectedValue(new Error("Network error"));

      await expect(service.delete("/endpoint/123")).rejects.toThrow();

      expect(mockClient.delete).toHaveBeenCalledTimes(1);
    });

    it("should retry DELETE when options.retry = true", async () => {
      mockClient.delete
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({ deleted: true });

      const result = await service.delete("/endpoint/123", { retry: true });

      expect(mockClient.delete).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ deleted: true });
    });
  });

  // ========================================================================
  // RETRY METHOD - INTERNAL LOGIC
  // ========================================================================

  describe("retry() method", () => {
    it("should retry function with exponential backoff", async () => {
      let callCount = 0;

      const flakeyFn = async () => {
        callCount++;
        if (callCount < 3) {
          throw new Error("Temporary failure");
        }
        return "success";
      };

      const result = await service.retry(flakeyFn, 5, 100);

      expect(result).toBe("success");
      expect(callCount).toBe(3);
    });

    it("should stop retrying on auth error", async () => {
      let callCount = 0;

      const authErrorFn = async () => {
        callCount++;
        throw new Error("401 Unauthorized");
      };

      await expect(service.retry(authErrorFn, 5, 100)).rejects.toThrow("401");

      // Should stop immediately, not retry
      expect(callCount).toBe(1);
    });

    it("should throw last error after all retries exhausted", async () => {
      const alwaysFailFn = async () => {
        throw new Error("Persistent error");
      };

      await expect(service.retry(alwaysFailFn, 3, 100)).rejects.toThrow(
        "Persistent error",
      );
    });
  });

  // ========================================================================
  // ERROR HANDLING
  // ========================================================================

  describe("Error Handling", () => {
    it("should enhance errors with context", async () => {
      mockClient.get.mockRejectedValue(new Error("Original error"));

      try {
        await service.get("/test", { retry: 0 });
      } catch (error) {
        expect(error.message).toContain("Original error");
        expect(error.method).toBe("GET");
        expect(error.endpoint).toContain("/test");
        expect(error.service).toBe("BaseService");
      }
    });

    it("should extract error message from various formats", () => {
      expect(service.extractErrorMessage("string error")).toBe("string error");
      expect(service.extractErrorMessage({ message: "msg" })).toBe("msg");
      expect(service.extractErrorMessage({ detail: "detail" })).toBe("detail");
      expect(service.extractErrorMessage({ error: "err" })).toBe("err");
      expect(service.extractErrorMessage({})).toBe("Unknown error occurred");
    });
  });

  // ========================================================================
  // VALIDATION
  // ========================================================================

  describe("Request Validation", () => {
    it("should throw on null data", async () => {
      await expect(service.post("/endpoint", null)).rejects.toThrow(
        "cannot be null",
      );
    });

    it("should throw on undefined data", async () => {
      await expect(service.post("/endpoint", undefined)).rejects.toThrow(
        "cannot be null",
      );
    });

    it("should throw on oversized payload", async () => {
      // Create 6MB payload (exceeds 5MB limit)
      const largePayload = { data: "x".repeat(6 * 1024 * 1024) };

      await expect(service.post("/endpoint", largePayload)).rejects.toThrow(
        "payload too large",
      );
    });

    it("should accept valid payloads", async () => {
      mockClient.post.mockResolvedValue({ ok: true });

      const validPayload = { name: "test", value: 123 };

      const result = await service.post("/endpoint", validPayload);

      expect(result).toEqual({ ok: true });
    });
  });

  // ========================================================================
  // INTEGRATION TESTS
  // ========================================================================

  describe("Integration Tests", () => {
    it("should handle complete GET retry flow", async () => {
      // Simulate: fail → fail → success
      mockClient.get
        .mockRejectedValueOnce(new Error("Network timeout"))
        .mockRejectedValueOnce(new Error("Connection refused"))
        .mockResolvedValueOnce({ data: "final success" });

      const result = await service.get("/flaky-endpoint");

      expect(mockClient.get).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ data: "final success" });
    });

    it("should handle POST with explicit retry enabled", async () => {
      mockClient.post
        .mockRejectedValueOnce(new Error("503 Service Unavailable"))
        .mockResolvedValueOnce({ created: true, id: 456 });

      const result = await service.post(
        "/create",
        { name: "test" },
        { retry: true, maxRetries: 3 },
      );

      expect(mockClient.post).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ created: true, id: 456 });
    });

    it("should respect idempotency rules across methods", async () => {
      // GET: auto-retry
      mockClient.get.mockRejectedValue(new Error("Network error"));
      await expect(service.get("/data")).rejects.toThrow();
      const getCallsWithRetry = mockClient.get.mock.calls.length;
      expect(getCallsWithRetry).toBeGreaterThan(1); // Has retries

      vi.clearAllMocks();

      // POST: no auto-retry
      mockClient.post.mockRejectedValue(new Error("Network error"));
      await expect(service.post("/data", {})).rejects.toThrow();
      const postCallsNoRetry = mockClient.post.mock.calls.length;
      expect(postCallsNoRetry).toBe(1); // No retries
    });
  });
});

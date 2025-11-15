/**
 * useApiCall Hook Tests
 * =====================
 *
 * Tests for the unified API call hook with:
 * - Loading states
 * - Error handling
 * - Retry logic
 * - Request cancellation
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useApiCall } from "../useApiCall";

describe("useApiCall Hook", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("should initialize with default state", () => {
    const { result } = renderHook(() => useApiCall());

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBeNull();
  });

  it("should execute API call successfully", async () => {
    const mockData = { success: true, result: "test data" };
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const { result } = renderHook(() => useApiCall());

    const callPromise = result.current.execute("http://api.test/endpoint", {
      method: "POST",
      body: JSON.stringify({ test: "data" }),
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const data = await callPromise;
    expect(data).toEqual(mockData);
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it("should handle API errors", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    const { result } = renderHook(() => useApiCall());

    await result.current.execute("http://api.test/error");

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.data).toBeNull();
  });

  it("should handle network errors", async () => {
    global.fetch.mockRejectedValueOnce(new Error("Network failure"));

    const { result } = renderHook(() => useApiCall());

    await result.current.execute("http://api.test/network-error");

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain("Network failure");
  });

  it("should retry on failure when retry enabled", async () => {
    global.fetch
      .mockRejectedValueOnce(new Error("Fail 1"))
      .mockRejectedValueOnce(new Error("Fail 2"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

    const { result } = renderHook(() =>
      useApiCall({ retry: 3, retryDelay: 10 }),
    );

    await result.current.execute("http://api.test/retry");

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual({ success: true });
    expect(global.fetch).toHaveBeenCalledTimes(3);
  });

  it("should cancel request on abort", async () => {
    global.fetch.mockImplementationOnce(
      () => new Promise((resolve) => setTimeout(resolve, 1000)),
    );

    const { result } = renderHook(() => useApiCall());

    result.current.execute("http://api.test/slow");
    result.current.cancel();

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain("cancelled");
  });

  it("should reset state", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: "test" }),
    });

    const { result } = renderHook(() => useApiCall());

    await result.current.execute("http://api.test/data");

    await waitFor(() => {
      expect(result.current.data).toBeTruthy();
    });

    result.current.reset();

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBeNull();
  });

  it("should handle POST with body", async () => {
    const mockResponse = { id: 123, created: true };
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useApiCall());

    const body = { name: "Test", value: 42 };
    await result.current.execute("http://api.test/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockResponse);
    });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.test/create",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(body),
      }),
    );
  });

  it("should handle custom headers", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { result } = renderHook(() => useApiCall());

    await result.current.execute("http://api.test/auth", {
      headers: {
        Authorization: "Bearer token123",
        "X-Custom-Header": "value",
      },
    });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.test/auth",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer token123",
          "X-Custom-Header": "value",
        }),
      }),
    );
  });
});

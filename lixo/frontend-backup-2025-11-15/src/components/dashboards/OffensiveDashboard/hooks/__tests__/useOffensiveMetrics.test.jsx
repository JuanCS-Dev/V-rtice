/**
 * useOffensiveMetrics Hook Tests
 * ===============================
 *
 * Tests for offensive dashboard metrics hook
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useOffensiveMetrics } from "../useOffensiveMetrics";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("useOffensiveMetrics Hook", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("should fetch offensive metrics successfully", async () => {
    const mockHealthData = {
      offensive_stats: {
        active_scans: 5,
        active_sessions: 3,
        simulations_today: 12,
        vulnerabilities_found: 48,
      },
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthData,
    });

    const { result } = renderHook(() => useOffensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metrics).toEqual({
      activeScans: 5,
      activeSessions: 3,
      simulationsToday: 12,
      vulnerabilitiesFound: 48,
    });
  });

  it("should return default values when no stats available", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { result } = renderHook(() => useOffensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metrics).toEqual({
      activeScans: 0,
      activeSessions: 0,
      simulationsToday: 0,
      vulnerabilitiesFound: 0,
    });
  });

  it("should handle API errors", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
    });

    const { result } = renderHook(() => useOffensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });

  it("should refetch on interval", async () => {
    vi.useFakeTimers();

    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        offensive_stats: { active_scans: 5 },
      }),
    });

    renderHook(() => useOffensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    vi.useRealTimers();
  });
});

/**
 * useDefensiveMetrics Hook Tests
 * ===============================
 *
 * Tests for defensive dashboard metrics hook
 * Uses React Query for data fetching
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDefensiveMetrics } from '../useDefensiveMetrics';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries for tests
        cacheTime: 0,
      },
    },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useDefensiveMetrics Hook', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it('should fetch defensive metrics successfully', async () => {
    const mockHealthData = {
      status: 'healthy',
      memory_system: {
        episodic_stats: {
          investigations: 15,
        },
      },
      security_stats: {
        suspicious_ips: 23,
        monitored_domains: 145,
      },
      total_integrated_tools: 57,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthData,
    });

    const { result } = renderHook(() => useDefensiveMetrics(), {
      wrapper: createWrapper(),
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metrics).toEqual({
      threats: 15,
      suspiciousIPs: 23,
      domains: 145,
      monitored: 57,
    });
    expect(result.current.error).toBeNull();
  });

  it('should return default values when health endpoint has no stats', async () => {
    const mockHealthData = {
      status: 'healthy',
      total_integrated_tools: 50,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthData,
    });

    const { result } = renderHook(() => useDefensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metrics).toEqual({
      threats: 0,
      suspiciousIPs: 0,
      domains: 0,
      monitored: 50,
    });
  });

  it('should handle API errors gracefully', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    const { result } = renderHook(() => useDefensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.metrics).toEqual({
      threats: 0,
      suspiciousIPs: 0,
      domains: 0,
      monitored: 0,
    });
  });

  it('should handle network errors', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useDefensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('should refetch data on interval', async () => {
    vi.useFakeTimers();

    const mockHealthData = {
      memory_system: { episodic_stats: { investigations: 10 } },
      security_stats: { suspicious_ips: 5, monitored_domains: 100 },
      total_integrated_tools: 57,
    };

    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => mockHealthData,
    });

    const { result } = renderHook(() => useDefensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Advance time by 30 seconds (refetch interval)
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    vi.useRealTimers();
  });

  it('should call correct API endpoint', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total_integrated_tools: 57,
      }),
    });

    renderHook(() => useDefensiveMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('http://34.148.161.131:8000/health');
    });
  });
});

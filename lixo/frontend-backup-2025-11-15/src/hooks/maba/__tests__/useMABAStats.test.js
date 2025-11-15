/**
 * useMABAStats Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useMABAStats } from "../useMABAStats";
import { mabaService } from "../../../services/maba/mabaService";

vi.mock("../../../services/maba/mabaService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useMABAStats", () => {
  const mockStats = {
    cognitive_map: {
      total_pages: 127,
      total_domains: 15,
      total_elements: 845,
    },
    browser: {
      active_sessions: 3,
      total_navigations: 358,
    },
    uptime_seconds: 7200,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar stats no mount", async () => {
    mabaService.getStats = vi.fn().mockResolvedValue(mockStats);

    const { result } = renderHook(() => useMABAStats());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mabaService.getStats).toHaveBeenCalledTimes(1);
    expect(result.current.stats).toEqual(mockStats);
  });

  it("deve extrair cognitiveMap e browser separadamente", async () => {
    mabaService.getStats = vi.fn().mockResolvedValue(mockStats);

    const { result } = renderHook(() => useMABAStats());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.cognitiveMap).toEqual(mockStats.cognitive_map);
    expect(result.current.browser).toEqual(mockStats.browser);
    expect(result.current.uptime).toBe(7200);
  });

  it("deve fazer polling a cada 30 segundos", async () => {
    mabaService.getStats = vi.fn().mockResolvedValue(mockStats);

    renderHook(() => useMABAStats());

    await waitFor(() => {
      expect(mabaService.getStats).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(mabaService.getStats).toHaveBeenCalledTimes(2);
    });
  });

  it("deve suportar pollingInterval customizado", async () => {
    mabaService.getStats = vi.fn().mockResolvedValue(mockStats);

    renderHook(() => useMABAStats({ pollingInterval: 15000 }));

    await waitFor(() => {
      expect(mabaService.getStats).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(15000);

    await waitFor(() => {
      expect(mabaService.getStats).toHaveBeenCalledTimes(2);
    });
  });

  it("deve suportar enabled=false", async () => {
    mabaService.getStats = vi.fn().mockResolvedValue(mockStats);

    renderHook(() => useMABAStats({ enabled: false }));

    expect(mabaService.getStats).not.toHaveBeenCalled();
  });

  it("deve tratar erro", async () => {
    const mockError = new Error("Service unavailable");
    mabaService.getStats = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useMABAStats());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Service unavailable");
    expect(result.current.stats).toBeNull();
  });

  it("deve retornar null quando stats não tem cognitive_map", async () => {
    mabaService.getStats = vi.fn().mockResolvedValue({ uptime_seconds: 100 });

    const { result } = renderHook(() => useMABAStats());

    await waitFor(() => {
      expect(result.current.cognitiveMap).toBeNull();
      expect(result.current.browser).toBeNull();
    });
  });

  it("deve expor função refetch", async () => {
    mabaService.getStats = vi.fn().mockResolvedValue(mockStats);

    const { result } = renderHook(() => useMABAStats());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mabaService.getStats).toHaveBeenCalledTimes(1);

    result.current.refetch();

    await waitFor(() => {
      expect(mabaService.getStats).toHaveBeenCalledTimes(2);
    });
  });

  it("deve retornar uptime 0 por default", () => {
    mabaService.getStats = vi
      .fn()
      .mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useMABAStats());

    expect(result.current.uptime).toBe(0);
  });
});

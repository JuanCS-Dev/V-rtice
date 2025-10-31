/**
 * useAnomalies Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAnomalies } from "../useAnomalies";
import { mvpService } from "../../../services/mvp/mvpService";

vi.mock("../../../services/mvp/mvpService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useAnomalies", () => {
  const mockAnomalies = [
    {
      anomaly_id: "anom-001",
      severity: "critical",
      detected_at: new Date().toISOString(),
    },
    {
      anomaly_id: "anom-002",
      severity: "high",
      detected_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2h ago
    },
    {
      anomaly_id: "anom-003",
      severity: "medium",
      detected_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30min ago
    },
    {
      anomaly_id: "anom-004",
      severity: "low",
      detected_at: new Date().toISOString(),
    },
  ];

  const mockTimeline = [
    { date: "2025-10-31", count: 2 },
    { date: "2025-10-30", count: 1 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar anomalias e timeline no mount", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    const { result } = renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mvpService.detectAnomalies).toHaveBeenCalledWith({});
    expect(mvpService.getAnomalyTimeline).toHaveBeenCalledWith(30);
    expect(result.current.anomalies).toEqual(mockAnomalies);
    expect(result.current.timeline).toEqual(mockTimeline);
  });

  it("deve calcular stats por severity", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    const { result } = renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    expect(result.current.stats.total).toBe(4);
    expect(result.current.stats.bySeverity.critical).toBe(1);
    expect(result.current.stats.bySeverity.high).toBe(1);
    expect(result.current.stats.bySeverity.medium).toBe(1);
    expect(result.current.stats.bySeverity.low).toBe(1);
  });

  it("deve calcular recentCount (última hora)", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    const { result } = renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    // anom-001 (now), anom-003 (30min ago), anom-004 (now) = 3
    expect(result.current.stats.recentCount).toBe(3);
  });

  it("deve suportar filtros", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    const filters = { severity: "critical", time_range: "24h" };
    renderHook(() => useAnomalies(filters));

    await waitFor(() => {
      expect(mvpService.detectAnomalies).toHaveBeenCalledWith(filters);
    });
  });

  it("deve fazer polling a cada 30 segundos", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(mvpService.detectAnomalies).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(mvpService.detectAnomalies).toHaveBeenCalledTimes(2);
    });
  });

  it("não deve fazer polling do timeline", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(mvpService.getAnomalyTimeline).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(30000);

    // Timeline não deve ser chamado novamente (só no mount)
    await waitFor(() => {
      expect(mvpService.getAnomalyTimeline).toHaveBeenCalledTimes(1);
    });
  });

  it("deve expor refetchTimeline", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    const { result } = renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(mvpService.getAnomalyTimeline).toHaveBeenCalledTimes(1);
    });

    result.current.refetchTimeline(7);

    await waitFor(() => {
      expect(mvpService.getAnomalyTimeline).toHaveBeenCalledWith(7);
      expect(mvpService.getAnomalyTimeline).toHaveBeenCalledTimes(2);
    });
  });

  it("deve suportar enabled=false", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    renderHook(() => useAnomalies({}, { enabled: false }));

    expect(mvpService.detectAnomalies).not.toHaveBeenCalled();
    expect(mvpService.getAnomalyTimeline).not.toHaveBeenCalled();
  });

  it("deve retornar stats null quando anomalies vazio", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue([]);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue([]);

    const { result } = renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.stats).toBeNull();
  });

  it("deve tratar erro em detectAnomalies", async () => {
    const mockError = new Error("Detection failed");
    mvpService.detectAnomalies = vi.fn().mockRejectedValue(mockError);
    mvpService.getAnomalyTimeline = vi.fn().mockResolvedValue(mockTimeline);

    const { result } = renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Detection failed");
    expect(result.current.anomalies).toEqual([]);
  });

  it("deve continuar mesmo se getAnomalyTimeline falhar", async () => {
    mvpService.detectAnomalies = vi.fn().mockResolvedValue(mockAnomalies);
    mvpService.getAnomalyTimeline = vi
      .fn()
      .mockRejectedValue(new Error("Timeline error"));

    const { result } = renderHook(() => useAnomalies());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Deve ter anomalies mesmo sem timeline
    expect(result.current.anomalies).toEqual(mockAnomalies);
    expect(result.current.timeline).toEqual([]);
  });
});

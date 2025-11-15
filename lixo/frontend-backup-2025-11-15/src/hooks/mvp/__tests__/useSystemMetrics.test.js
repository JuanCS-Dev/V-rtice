/**
 * useSystemMetrics Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useSystemMetrics } from "../useSystemMetrics";
import { mvpService } from "../../../services/mvp/mvpService";

vi.mock("../../../services/mvp/mvpService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useSystemMetrics", () => {
  const mockMetrics = {
    cpu_usage: 0.65,
    memory_usage: 0.72,
    request_rate: 125.5,
    error_rate: 0.02,
  };

  const mockPulse = {
    health: 0.85,
    status_messages: [
      { timestamp: "2025-10-31T10:00:00Z", message: "System healthy" },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar metrics e pulse no mount", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    const { result } = renderHook(() => useSystemMetrics());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mvpService.queryMetrics).toHaveBeenCalledWith({
      time_range_minutes: 60,
    });
    expect(mvpService.getSystemPulse).toHaveBeenCalled();
    expect(result.current.metrics).toEqual(mockMetrics);
    expect(result.current.pulse).toEqual(mockPulse);
  });

  it("deve extrair métricas individuais", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    const { result } = renderHook(() => useSystemMetrics());

    await waitFor(() => {
      expect(result.current.cpuUsage).toBe(0.65);
      expect(result.current.memoryUsage).toBe(0.72);
      expect(result.current.requestRate).toBe(125.5);
      expect(result.current.errorRate).toBe(0.02);
    });
  });

  it("deve suportar query parameters", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    const query = { time_range_minutes: 30, metric_name: "cpu_usage" };
    renderHook(() => useSystemMetrics(query));

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalledWith({
        time_range_minutes: 30,
        metric_name: "cpu_usage",
      });
    });
  });

  it("deve suportar includePulse=false", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    renderHook(() => useSystemMetrics({}, { includePulse: false }));

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalled();
    });

    expect(mvpService.getSystemPulse).not.toHaveBeenCalled();
  });

  it("deve fazer polling a cada 15 segundos", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    renderHook(() => useSystemMetrics());

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(15000);

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalledTimes(2);
    });
  });

  it("deve chamar pulse a cada polling quando includePulse=true", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    renderHook(() => useSystemMetrics());

    await waitFor(() => {
      expect(mvpService.getSystemPulse).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(15000);

    await waitFor(() => {
      expect(mvpService.getSystemPulse).toHaveBeenCalledTimes(2);
    });
  });

  it("deve suportar pollingInterval customizado", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    renderHook(() => useSystemMetrics({}, { pollingInterval: 10000 }));

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalledTimes(2);
    });
  });

  it("deve suportar enabled=false", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    renderHook(() => useSystemMetrics({}, { enabled: false }));

    expect(mvpService.queryMetrics).not.toHaveBeenCalled();
    expect(mvpService.getSystemPulse).not.toHaveBeenCalled();
  });

  it("deve tratar erro", async () => {
    const mockError = new Error("Metrics unavailable");
    mvpService.queryMetrics = vi.fn().mockRejectedValue(mockError);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    const { result } = renderHook(() => useSystemMetrics());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Metrics unavailable");
    expect(result.current.metrics).toBeNull();
  });

  it("deve retornar null para métricas individuais quando metrics é null", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(null);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    const { result } = renderHook(() => useSystemMetrics());

    await waitFor(() => {
      expect(result.current.cpuUsage).toBeNull();
      expect(result.current.memoryUsage).toBeNull();
      expect(result.current.requestRate).toBeNull();
      expect(result.current.errorRate).toBeNull();
    });
  });

  it("deve expor função refetch", async () => {
    mvpService.queryMetrics = vi.fn().mockResolvedValue(mockMetrics);
    mvpService.getSystemPulse = vi.fn().mockResolvedValue(mockPulse);

    const { result } = renderHook(() => useSystemMetrics());

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalledTimes(1);
    });

    result.current.refetch();

    await waitFor(() => {
      expect(mvpService.queryMetrics).toHaveBeenCalledTimes(2);
    });
  });

  it("deve iniciar com null", () => {
    mvpService.queryMetrics = vi
      .fn()
      .mockImplementation(() => new Promise(() => {}));
    mvpService.getSystemPulse = vi
      .fn()
      .mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useSystemMetrics());

    expect(result.current.metrics).toBeNull();
    expect(result.current.pulse).toBeNull();
    expect(result.current.cpuUsage).toBeNull();
  });
});

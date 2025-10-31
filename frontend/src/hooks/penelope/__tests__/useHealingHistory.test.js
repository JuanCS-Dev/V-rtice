/**
 * useHealingHistory Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useHealingHistory } from "../useHealingHistory";
import { penelopeService } from "../../../services/penelope/penelopeService";

vi.mock("../../../services/penelope/penelopeService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useHealingHistory", () => {
  const mockHistory = [
    {
      event_id: "heal-001",
      outcome: "success",
      patch_size_lines: 15,
      mansidao_score: 0.92,
    },
    {
      event_id: "heal-002",
      outcome: "success",
      patch_size_lines: 8,
      mansidao_score: 0.95,
    },
    {
      event_id: "heal-003",
      outcome: "failed",
      patch_size_lines: 20,
      mansidao_score: 0.7,
    },
    {
      event_id: "heal-004",
      outcome: "escalated",
      patch_size_lines: 50,
      mansidao_score: 0.4,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar healing history no mount", async () => {
    penelopeService.getHealingHistory = vi.fn().mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useHealingHistory());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(penelopeService.getHealingHistory).toHaveBeenCalledWith(50); // default limit
    expect(result.current.history).toEqual(mockHistory);
  });

  it("deve calcular estatísticas corretamente", async () => {
    penelopeService.getHealingHistory = vi.fn().mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useHealingHistory());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    expect(result.current.stats.total).toBe(4);
    expect(result.current.stats.successful).toBe(2);
    expect(result.current.stats.failed).toBe(1);
    expect(result.current.stats.escalated).toBe(1);
    expect(result.current.stats.successRate).toBe(50); // 2/4 = 50%
  });

  it("deve calcular avgPatchSize", async () => {
    penelopeService.getHealingHistory = vi.fn().mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useHealingHistory());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    // (15 + 8 + 20 + 50) / 4 = 23.25 → 23
    expect(result.current.stats.avgPatchSize).toBe(23);
  });

  it("deve calcular avgMansidao", async () => {
    penelopeService.getHealingHistory = vi.fn().mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useHealingHistory());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    // (0.92 + 0.95 + 0.70 + 0.40) / 4 = 0.7425
    expect(result.current.stats.avgMansidao).toBe("0.74");
  });

  it("deve suportar limit customizado", async () => {
    penelopeService.getHealingHistory = vi
      .fn()
      .mockResolvedValue(mockHistory.slice(0, 2));

    renderHook(() => useHealingHistory({ limit: 10 }));

    await waitFor(() => {
      expect(penelopeService.getHealingHistory).toHaveBeenCalledWith(10);
    });
  });

  it("deve fazer polling a cada 60 segundos", async () => {
    penelopeService.getHealingHistory = vi.fn().mockResolvedValue(mockHistory);

    renderHook(() => useHealingHistory());

    await waitFor(() => {
      expect(penelopeService.getHealingHistory).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(60000);

    await waitFor(() => {
      expect(penelopeService.getHealingHistory).toHaveBeenCalledTimes(2);
    });
  });

  it("deve retornar stats null quando history vazio", async () => {
    penelopeService.getHealingHistory = vi.fn().mockResolvedValue([]);

    const { result } = renderHook(() => useHealingHistory());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.stats).toBeNull();
  });

  it("deve tratar erro", async () => {
    const mockError = new Error("Database error");
    penelopeService.getHealingHistory = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useHealingHistory());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Database error");
    expect(result.current.history).toEqual([]);
  });

  it("deve suportar enabled=false", async () => {
    penelopeService.getHealingHistory = vi.fn().mockResolvedValue(mockHistory);

    renderHook(() => useHealingHistory({ enabled: false }));

    expect(penelopeService.getHealingHistory).not.toHaveBeenCalled();
  });
});

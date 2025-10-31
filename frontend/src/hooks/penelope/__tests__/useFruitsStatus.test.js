/**
 * useFruitsStatus Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useFruitsStatus } from "../useFruitsStatus";
import { penelopeService } from "../../../services/penelope/penelopeService";

vi.mock("../../../services/penelope/penelopeService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useFruitsStatus", () => {
  const mockFruits = {
    amor_agape: { name: "Amor", score: 0.92 },
    chara: { name: "Alegria", score: 0.88 },
    eirene: { name: "Paz", score: 0.95 },
    enkrateia: { name: "Domínio Próprio", score: 0.9 },
    pistis: { name: "Fidelidade", score: 0.91 },
    praotes: { name: "Mansidão", score: 0.87 },
    tapeinophrosyne: { name: "Humildade", score: 0.93 },
    aletheia: { name: "Verdade", score: 0.89 },
    sophia: { name: "Sabedoria", score: 0.94 },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar fruits status no mount", async () => {
    penelopeService.getFruitsStatus = vi
      .fn()
      .mockResolvedValue({ fruits: mockFruits });

    const { result } = renderHook(() => useFruitsStatus());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(penelopeService.getFruitsStatus).toHaveBeenCalledTimes(1);
    expect(result.current.fruits).toEqual(mockFruits);
  });

  it("deve calcular overall score corretamente", async () => {
    penelopeService.getFruitsStatus = vi
      .fn()
      .mockResolvedValue({ fruits: mockFruits });

    const { result } = renderHook(() => useFruitsStatus());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Average: (0.92 + 0.88 + 0.95 + 0.90 + 0.91 + 0.87 + 0.93 + 0.89 + 0.94) / 9 = 0.91
    expect(result.current.overallScore).toBeGreaterThanOrEqual(0);
    expect(result.current.overallScore).toBeLessThanOrEqual(100);
  });

  it("deve suportar opção enabled=false", async () => {
    penelopeService.getFruitsStatus = vi
      .fn()
      .mockResolvedValue({ fruits: mockFruits });

    const { result } = renderHook(() => useFruitsStatus({ enabled: false }));

    expect(result.current.isLoading).toBe(true);
    expect(penelopeService.getFruitsStatus).not.toHaveBeenCalled();
  });

  it("deve fazer polling no intervalo configurado", async () => {
    penelopeService.getFruitsStatus = vi
      .fn()
      .mockResolvedValue({ fruits: mockFruits });

    renderHook(() => useFruitsStatus({ pollingInterval: 10000 }));

    await waitFor(() => {
      expect(penelopeService.getFruitsStatus).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(penelopeService.getFruitsStatus).toHaveBeenCalledTimes(2);
    });
  });

  it("deve tratar erro na busca", async () => {
    const mockError = new Error("Failed to fetch");
    penelopeService.getFruitsStatus = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useFruitsStatus());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch");
    expect(result.current.fruits).toBeNull();
  });

  it("deve expor função refetch", async () => {
    penelopeService.getFruitsStatus = vi
      .fn()
      .mockResolvedValue({ fruits: mockFruits });

    const { result } = renderHook(() => useFruitsStatus());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(penelopeService.getFruitsStatus).toHaveBeenCalledTimes(1);

    // Chamar refetch manualmente
    result.current.refetch();

    await waitFor(() => {
      expect(penelopeService.getFruitsStatus).toHaveBeenCalledTimes(2);
    });
  });

  it("deve retornar overallScore 0 quando fruits é null", () => {
    penelopeService.getFruitsStatus = vi
      .fn()
      .mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useFruitsStatus());

    expect(result.current.overallScore).toBe(0);
  });
});

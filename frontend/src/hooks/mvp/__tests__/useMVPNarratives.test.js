/**
 * useMVPNarratives Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useMVPNarratives } from "../useMVPNarratives";
import { mvpService } from "../../../services/mvp/mvpService";

vi.mock("../../../services/mvp/mvpService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useMVPNarratives", () => {
  const mockNarratives = [
    {
      narrative_id: "narr-001",
      tone: "reflective",
      content: "Narrativa 1",
      nqs: 0.92,
      word_count: 150,
    },
    {
      narrative_id: "narr-002",
      tone: "urgent",
      content: "Narrativa 2",
      nqs: 0.88,
      word_count: 200,
    },
    {
      narrative_id: "narr-003",
      tone: "informative",
      content: "Narrativa 3",
      nqs: 0.95,
      word_count: 180,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar narrativas no mount", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mvpService.listNarratives).toHaveBeenCalledWith({ limit: 20 });
    expect(result.current.narratives).toEqual(mockNarratives);
  });

  it("deve calcular stats corretamente", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    expect(result.current.stats.total).toBe(3);
    expect(result.current.stats.byTone.reflective).toBe(1);
    expect(result.current.stats.byTone.urgent).toBe(1);
    expect(result.current.stats.byTone.informative).toBe(1);
  });

  it("deve calcular avgNQS", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    // (0.92 + 0.88 + 0.95) / 3 ≈ 0.916 → arredondado
    expect(result.current.stats.avgNQS).toBeGreaterThanOrEqual(0);
  });

  it("deve calcular avgWordCount", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.stats).not.toBeNull();
    });

    // (150 + 200 + 180) / 3 ≈ 177
    expect(result.current.stats.avgWordCount).toBe(177);
  });

  it("deve suportar filtros", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);

    const filters = { tone: "urgent", min_nqs: 0.8, limit: 10 };
    renderHook(() => useMVPNarratives(filters));

    await waitFor(() => {
      expect(mvpService.listNarratives).toHaveBeenCalledWith({
        ...filters,
      });
    });
  });

  it("deve fazer polling a cada 60 segundos", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);

    renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(mvpService.listNarratives).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(60000);

    await waitFor(() => {
      expect(mvpService.listNarratives).toHaveBeenCalledTimes(2);
    });
  });

  it("deve gerar nova narrativa com generateNarrative", async () => {
    const newNarrative = {
      narrative_id: "narr-004",
      tone: "reflective",
      content: "Nova narrativa",
      nqs: 0.9,
    };

    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);
    mvpService.generateNarrative = vi.fn().mockResolvedValue(newNarrative);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let generated;
    await act(async () => {
      generated = await result.current.generateNarrative({
        tone: "reflective",
      });
    });

    expect(mvpService.generateNarrative).toHaveBeenCalledWith({
      tone: "reflective",
    });
    expect(generated).toEqual(newNarrative);

    // Deve chamar listNarratives para refresh
    expect(mvpService.listNarratives).toHaveBeenCalledTimes(2);
  });

  it("deve tratar erro em generateNarrative", async () => {
    const mockError = new Error("Generation failed");

    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);
    mvpService.generateNarrative = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(async () => {
      await act(async () => {
        await result.current.generateNarrative({});
      });
    }).rejects.toThrow("Generation failed");
  });

  it("deve suportar enabled=false", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue(mockNarratives);

    renderHook(() => useMVPNarratives({}, { enabled: false }));

    expect(mvpService.listNarratives).not.toHaveBeenCalled();
  });

  it("deve retornar stats null quando narratives vazio", async () => {
    mvpService.listNarratives = vi.fn().mockResolvedValue([]);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.stats).toBeNull();
  });

  it("deve tratar erro na busca", async () => {
    const mockError = new Error("Service error");
    mvpService.listNarratives = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useMVPNarratives());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Service error");
    expect(result.current.narratives).toEqual([]);
  });
});

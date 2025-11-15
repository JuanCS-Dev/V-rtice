/**
 * usePenelopeHealth Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { usePenelopeHealth } from "../usePenelopeHealth";
import { penelopeService } from "../../../services/penelope/penelopeService";

vi.mock("../../../services/penelope/penelopeService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe("usePenelopeHealth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve iniciar com loading true", () => {
    penelopeService.getHealth = vi
      .fn()
      .mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => usePenelopeHealth());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.health).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("deve buscar health check no mount", async () => {
    const mockHealth = {
      status: "healthy",
      uptime_seconds: 3600,
      sabbath_mode: false,
    };

    penelopeService.getHealth = vi.fn().mockResolvedValue(mockHealth);

    const { result } = renderHook(() => usePenelopeHealth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(penelopeService.getHealth).toHaveBeenCalledTimes(1);
    expect(result.current.health).toEqual(mockHealth);
    expect(result.current.isHealthy).toBe(true);
    expect(result.current.uptime).toBe(3600);
  });

  it("deve detectar Sabbath mode do servidor", async () => {
    const mockHealth = {
      status: "healthy",
      sabbath_mode: true,
    };

    penelopeService.getHealth = vi.fn().mockResolvedValue(mockHealth);

    const { result } = renderHook(() => usePenelopeHealth());

    await waitFor(() => {
      expect(result.current.isSabbath).toBe(true);
    });
  });

  it("deve detectar Sabbath mode por dia da semana (domingo)", async () => {
    const mockHealth = {
      status: "healthy",
      sabbath_mode: false,
    };

    // Mock domingo (day 0)
    const sunday = new Date("2025-11-02T10:00:00Z"); // Sunday
    vi.setSystemTime(sunday);

    penelopeService.getHealth = vi.fn().mockResolvedValue(mockHealth);

    const { result } = renderHook(() => usePenelopeHealth());

    await waitFor(() => {
      expect(result.current.isSabbath).toBe(true);
    });
  });

  it("deve tratar erro no health check", async () => {
    const mockError = new Error("Network error");
    penelopeService.getHealth = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => usePenelopeHealth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.health).toBeNull();
  });

  it("deve fazer polling a cada 30 segundos", async () => {
    penelopeService.getHealth = vi
      .fn()
      .mockResolvedValue({ status: "healthy" });

    renderHook(() => usePenelopeHealth());

    await waitFor(() => {
      expect(penelopeService.getHealth).toHaveBeenCalledTimes(1);
    });

    // Avançar 30s
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(penelopeService.getHealth).toHaveBeenCalledTimes(2);
    });

    // Avançar mais 30s
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(penelopeService.getHealth).toHaveBeenCalledTimes(3);
    });
  });

  it("deve limpar interval no unmount", async () => {
    penelopeService.getHealth = vi
      .fn()
      .mockResolvedValue({ status: "healthy" });

    const { unmount } = renderHook(() => usePenelopeHealth());

    await waitFor(() => {
      expect(penelopeService.getHealth).toHaveBeenCalledTimes(1);
    });

    unmount();

    // Avançar 30s após unmount
    vi.advanceTimersByTime(30000);

    // Não deve chamar novamente
    expect(penelopeService.getHealth).toHaveBeenCalledTimes(1);
  });
});

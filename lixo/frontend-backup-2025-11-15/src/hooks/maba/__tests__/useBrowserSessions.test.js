/**
 * useBrowserSessions Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useBrowserSessions } from "../useBrowserSessions";
import { mabaService } from "../../../services/maba/mabaService";

vi.mock("../../../services/maba/mabaService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useBrowserSessions", () => {
  const mockSessions = [
    {
      session_id: "sess-001",
      status: "active",
      current_url: "https://example.com",
    },
    {
      session_id: "sess-002",
      status: "idle",
      current_url: "https://test.com",
    },
    {
      session_id: "sess-003",
      status: "active",
      current_url: "https://demo.com",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar sessions no mount", async () => {
    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);

    const { result } = renderHook(() => useBrowserSessions());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mabaService.listSessions).toHaveBeenCalledTimes(1);
    expect(result.current.sessions).toEqual(mockSessions);
    expect(result.current.sessionCount).toBe(3);
  });

  it("deve filtrar activeSessions", async () => {
    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);

    const { result } = renderHook(() => useBrowserSessions());

    await waitFor(() => {
      expect(result.current.activeSessions.length).toBe(2);
    });

    expect(result.current.activeSessions[0].session_id).toBe("sess-001");
    expect(result.current.activeSessions[1].session_id).toBe("sess-003");
  });

  it("deve fazer polling a cada 10 segundos", async () => {
    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);

    renderHook(() => useBrowserSessions());

    await waitFor(() => {
      expect(mabaService.listSessions).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(mabaService.listSessions).toHaveBeenCalledTimes(2);
    });
  });

  it("deve criar nova sessão com createSession", async () => {
    const newSession = {
      session_id: "sess-004",
      status: "active",
      current_url: "https://new.com",
    };

    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);
    mabaService.createSession = vi.fn().mockResolvedValue(newSession);

    const { result } = renderHook(() => useBrowserSessions());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let createdSession;
    await act(async () => {
      createdSession = await result.current.createSession({
        url: "https://new.com",
      });
    });

    expect(mabaService.createSession).toHaveBeenCalledWith({
      url: "https://new.com",
    });
    expect(createdSession).toEqual(newSession);

    // Deve chamar listSessions novamente para refresh
    expect(mabaService.listSessions).toHaveBeenCalledTimes(2);
  });

  it("deve fechar sessão com closeSession", async () => {
    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);
    mabaService.closeSession = vi.fn().mockResolvedValue({});

    const { result } = renderHook(() => useBrowserSessions());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.closeSession("sess-001");
    });

    expect(mabaService.closeSession).toHaveBeenCalledWith("sess-001");

    // Deve chamar listSessions novamente para refresh
    expect(mabaService.listSessions).toHaveBeenCalledTimes(2);
  });

  it("deve tratar erro em createSession", async () => {
    const mockError = new Error("Failed to create session");

    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);
    mabaService.createSession = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useBrowserSessions());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(async () => {
      await act(async () => {
        await result.current.createSession({});
      });
    }).rejects.toThrow("Failed to create session");
  });

  it("deve tratar erro em closeSession", async () => {
    const mockError = new Error("Session not found");

    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);
    mabaService.closeSession = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useBrowserSessions());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(async () => {
      await act(async () => {
        await result.current.closeSession("invalid-id");
      });
    }).rejects.toThrow("Session not found");
  });

  it("deve suportar enabled=false", async () => {
    mabaService.listSessions = vi.fn().mockResolvedValue(mockSessions);

    renderHook(() => useBrowserSessions({ enabled: false }));

    expect(mabaService.listSessions).not.toHaveBeenCalled();
  });

  it("deve iniciar com array vazio", () => {
    mabaService.listSessions = vi
      .fn()
      .mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useBrowserSessions());

    expect(result.current.sessions).toEqual([]);
    expect(result.current.sessionCount).toBe(0);
    expect(result.current.activeSessions).toEqual([]);
  });
});

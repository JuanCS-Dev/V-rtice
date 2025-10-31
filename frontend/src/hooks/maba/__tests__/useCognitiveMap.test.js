/**
 * useCognitiveMap Hook Tests
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useCognitiveMap } from "../useCognitiveMap";
import { mabaService } from "../../../services/maba/mabaService";

vi.mock("../../../services/maba/mabaService");
vi.mock("../../../utils/logger", () => ({
  default: {
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useCognitiveMap", () => {
  const mockGraph = {
    nodes: [
      { id: "node-1", url: "https://example.com", domain: "example.com" },
      { id: "node-2", url: "https://test.com", domain: "test.com" },
    ],
    edges: [{ source: "node-1", target: "node-2" }],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("deve buscar cognitive map no mount", async () => {
    mabaService.queryCognitiveMap = vi.fn().mockResolvedValue(mockGraph);

    const { result } = renderHook(() => useCognitiveMap());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mabaService.queryCognitiveMap).toHaveBeenCalledWith({});
    expect(result.current.graph).toEqual(mockGraph);
    expect(result.current.nodes).toEqual(mockGraph.nodes);
    expect(result.current.edges).toEqual(mockGraph.edges);
  });

  it("deve calcular nodeCount e edgeCount", async () => {
    mabaService.queryCognitiveMap = vi.fn().mockResolvedValue(mockGraph);

    const { result } = renderHook(() => useCognitiveMap());

    await waitFor(() => {
      expect(result.current.nodeCount).toBe(2);
      expect(result.current.edgeCount).toBe(1);
    });
  });

  it("deve suportar query parameters", async () => {
    const query = { domain: "example.com", limit: 50 };
    mabaService.queryCognitiveMap = vi.fn().mockResolvedValue(mockGraph);

    renderHook(() => useCognitiveMap(query));

    await waitFor(() => {
      expect(mabaService.queryCognitiveMap).toHaveBeenCalledWith(query);
    });
  });

  it("deve transformar response alternativo (pages/links)", async () => {
    const altResponse = {
      pages: mockGraph.nodes,
      links: mockGraph.edges,
    };

    mabaService.queryCognitiveMap = vi.fn().mockResolvedValue(altResponse);

    const { result } = renderHook(() => useCognitiveMap());

    await waitFor(() => {
      expect(result.current.nodes).toEqual(mockGraph.nodes);
      expect(result.current.edges).toEqual(mockGraph.edges);
    });
  });

  it("deve fazer polling a cada 60 segundos", async () => {
    mabaService.queryCognitiveMap = vi.fn().mockResolvedValue(mockGraph);

    renderHook(() => useCognitiveMap());

    await waitFor(() => {
      expect(mabaService.queryCognitiveMap).toHaveBeenCalledTimes(1);
    });

    vi.advanceTimersByTime(60000);

    await waitFor(() => {
      expect(mabaService.queryCognitiveMap).toHaveBeenCalledTimes(2);
    });
  });

  it("deve suportar enabled=false", async () => {
    mabaService.queryCognitiveMap = vi.fn().mockResolvedValue(mockGraph);

    renderHook(() => useCognitiveMap({}, { enabled: false }));

    expect(mabaService.queryCognitiveMap).not.toHaveBeenCalled();
  });

  it("deve tratar erro", async () => {
    const mockError = new Error("Neo4j connection failed");
    mabaService.queryCognitiveMap = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useCognitiveMap());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Neo4j connection failed");
    expect(result.current.graph).toEqual({ nodes: [], edges: [] });
  });

  it("deve iniciar com graph vazio", () => {
    mabaService.queryCognitiveMap = vi
      .fn()
      .mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useCognitiveMap());

    expect(result.current.graph).toEqual({ nodes: [], edges: [] });
    expect(result.current.nodeCount).toBe(0);
    expect(result.current.edgeCount).toBe(0);
  });

  it("deve expor função refetch", async () => {
    mabaService.queryCognitiveMap = vi.fn().mockResolvedValue(mockGraph);

    const { result } = renderHook(() => useCognitiveMap());

    await waitFor(() => {
      expect(mabaService.queryCognitiveMap).toHaveBeenCalledTimes(1);
    });

    result.current.refetch();

    await waitFor(() => {
      expect(mabaService.queryCognitiveMap).toHaveBeenCalledTimes(2);
    });
  });
});

/**
 * Query Persister Tests
 *
 * DOUTRINA VÉRTICE - GAP #9 (P1)
 * Tests for IndexedDB persistence layer
 *
 * Following Boris Cherny: "Tests or it didn't happen"
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { get, set, del, clear } from "idb-keyval";
import type { PersistedClient } from "@tanstack/react-query-persist-client";
import {
  createIDBPersister,
  isIndexedDBSupported,
  clearPersistedQueries,
} from "../queryPersister";

// Mock idb-keyval
vi.mock("idb-keyval", () => ({
  get: vi.fn(),
  set: vi.fn(),
  del: vi.fn(),
  clear: vi.fn(),
}));

describe("queryPersister", () => {
  const mockClient: PersistedClient = {
    clientState: {
      queries: [],
      mutations: [],
    },
    timestamp: Date.now(),
    buster: "",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, "info").mockImplementation(() => {});
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("createIDBPersister", () => {
    it("should create persister with persistClient method", () => {
      const persister = createIDBPersister();

      expect(persister).toHaveProperty("persistClient");
      expect(persister).toHaveProperty("restoreClient");
      expect(persister).toHaveProperty("removeClient");
    });

    describe("persistClient", () => {
      it("should persist client to IndexedDB", async () => {
        const persister = createIDBPersister();

        await persister.persistClient(mockClient);

        expect(set).toHaveBeenCalledWith(
          "VERTICE_REACT_QUERY_OFFLINE_CACHE",
          mockClient,
        );
        expect(console.info).toHaveBeenCalledWith(
          "[QueryPersister] State persisted to IndexedDB",
        );
      });

      it("should handle persistence errors gracefully", async () => {
        const persister = createIDBPersister();
        const error = new Error("IndexedDB error");
        vi.mocked(set).mockRejectedValueOnce(error);

        await persister.persistClient(mockClient);

        expect(console.error).toHaveBeenCalledWith(
          "[QueryPersister] Failed to persist state:",
          error,
        );
      });
    });

    describe("restoreClient", () => {
      it("should restore client from IndexedDB", async () => {
        vi.mocked(get).mockResolvedValueOnce(mockClient);
        const persister = createIDBPersister();

        const result = await persister.restoreClient();

        expect(get).toHaveBeenCalledWith("VERTICE_REACT_QUERY_OFFLINE_CACHE");
        expect(result).toEqual(mockClient);
        expect(console.info).toHaveBeenCalledWith(
          "[QueryPersister] Restored state from IndexedDB",
        );
      });

      it("should return undefined when no persisted state found", async () => {
        vi.mocked(get).mockResolvedValueOnce(undefined);
        const persister = createIDBPersister();

        const result = await persister.restoreClient();

        expect(result).toBeUndefined();
        expect(console.info).toHaveBeenCalledWith(
          "[QueryPersister] No persisted state found",
        );
      });

      it("should handle restore errors gracefully", async () => {
        const error = new Error("IndexedDB error");
        vi.mocked(get).mockRejectedValueOnce(error);
        const persister = createIDBPersister();

        const result = await persister.restoreClient();

        expect(result).toBeUndefined();
        expect(console.error).toHaveBeenCalledWith(
          "[QueryPersister] Failed to restore state:",
          error,
        );
      });
    });

    describe("removeClient", () => {
      it("should remove client from IndexedDB", async () => {
        const persister = createIDBPersister();

        await persister.removeClient();

        expect(del).toHaveBeenCalledWith("VERTICE_REACT_QUERY_OFFLINE_CACHE");
        expect(console.info).toHaveBeenCalledWith(
          "[QueryPersister] Cleared persisted state",
        );
      });

      it("should handle removal errors gracefully", async () => {
        const error = new Error("IndexedDB error");
        vi.mocked(del).mockRejectedValueOnce(error);
        const persister = createIDBPersister();

        await persister.removeClient();

        expect(console.error).toHaveBeenCalledWith(
          "[QueryPersister] Failed to clear state:",
          error,
        );
      });
    });
  });

  describe("isIndexedDBSupported", () => {
    it("should return true when IndexedDB is available", () => {
      // IndexedDB is available in vitest environment (jsdom)
      const result = isIndexedDBSupported();

      expect(result).toBe(true);
    });

    it("should return false when window is undefined", () => {
      const originalWindow = global.window;
      // @ts-ignore
      delete global.window;

      const result = isIndexedDBSupported();

      expect(result).toBe(false);

      // Restore
      global.window = originalWindow;
    });

    it("should return false when indexedDB is undefined", () => {
      const originalIndexedDB = global.indexedDB;
      // @ts-ignore
      delete global.indexedDB;

      const result = isIndexedDBSupported();

      expect(result).toBe(false);

      // Restore
      global.indexedDB = originalIndexedDB;
    });
  });

  describe("clearPersistedQueries", () => {
    it("should clear all persisted queries", async () => {
      await clearPersistedQueries();

      expect(del).toHaveBeenCalledWith("VERTICE_REACT_QUERY_OFFLINE_CACHE");
      expect(console.info).toHaveBeenCalledWith(
        "[QueryPersister] Cleared all persisted queries",
      );
    });

    it("should handle errors when clearing", async () => {
      const error = new Error("IndexedDB error");
      vi.mocked(del).mockRejectedValueOnce(error);

      await clearPersistedQueries();

      expect(console.error).toHaveBeenCalledWith(
        "[QueryPersister] Failed to clear queries:",
        error,
      );
    });
  });
});

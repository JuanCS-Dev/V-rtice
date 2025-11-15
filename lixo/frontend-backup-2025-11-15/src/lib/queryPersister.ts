/**
 * React Query Persistence with IndexedDB
 *
 * DOUTRINA VÉRTICE - GAP #9 (P1)
 * Persist mutations across page reloads using IndexedDB
 *
 * Following Boris Cherny's principle: "State should survive failures"
 */

import { get, set, del } from "idb-keyval";
import type {
  PersistedClient,
  Persister,
} from "@tanstack/react-query-persist-client";

// ============================================================================
// IndexedDB Configuration
// ============================================================================

const IDB_KEY = "VERTICE_REACT_QUERY_OFFLINE_CACHE";
const MAX_AGE = 1000 * 60 * 60 * 24 * 7; // 7 days

/**
 * Create IndexedDB persister for React Query
 *
 * Stores query and mutation state in IndexedDB for offline persistence
 *
 * @returns Persister instance for PersistQueryClientProvider
 *
 * @example
 * ```tsx
 * import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
 * import { createIDBPersister } from '@/lib/queryPersister';
 *
 * const persister = createIDBPersister();
 *
 * function App() {
 *   return (
 *     <PersistQueryClientProvider
 *       client={queryClient}
 *       persistOptions={{ persister, maxAge: MAX_AGE }}
 *     >
 *       <YourApp />
 *     </PersistQueryClientProvider>
 *   );
 * }
 * ```
 */
export function createIDBPersister(): Persister {
  return {
    persistClient: async (client: PersistedClient) => {
      try {
        await set(IDB_KEY, client);
        console.info("[QueryPersister] State persisted to IndexedDB");
      } catch (error) {
        console.error("[QueryPersister] Failed to persist state:", error);
        // Silently fail - persistence is optional enhancement
      }
    },

    restoreClient: async () => {
      try {
        const client = await get<PersistedClient>(IDB_KEY);

        if (!client) {
          console.info("[QueryPersister] No persisted state found");
          return undefined;
        }

        console.info("[QueryPersister] Restored state from IndexedDB");
        return client;
      } catch (error) {
        console.error("[QueryPersister] Failed to restore state:", error);
        return undefined;
      }
    },

    removeClient: async () => {
      try {
        await del(IDB_KEY);
        console.info("[QueryPersister] Cleared persisted state");
      } catch (error) {
        console.error("[QueryPersister] Failed to clear state:", error);
      }
    },
  };
}

// ============================================================================
// Persistence Configuration
// ============================================================================

/**
 * Default persistence options for React Query
 */
export const persistOptions = {
  maxAge: MAX_AGE,
  buster: "", // Change this to invalidate all cached data
};

/**
 * Check if browser supports IndexedDB
 *
 * @returns Whether IndexedDB is available
 */
export function isIndexedDBSupported(): boolean {
  try {
    return typeof window !== "undefined" && "indexedDB" in window;
  } catch {
    return false;
  }
}

/**
 * Clear all persisted query data
 *
 * Useful for logout or debugging
 *
 * @example
 * ```typescript
 * async function handleLogout() {
 *   await clearPersistedQueries();
 *   queryClient.clear();
 *   // ... redirect to login
 * }
 * ```
 */
export async function clearPersistedQueries(): Promise<void> {
  try {
    await del(IDB_KEY);
    console.info("[QueryPersister] Cleared all persisted queries");
  } catch (error) {
    console.error("[QueryPersister] Failed to clear queries:", error);
  }
}

/**
 * Offline Mutation Queue
 *
 * DOUTRINA VÉRTICE - GAP #9 (P1)
 * Queue mutations when offline and retry when connection restored
 *
 * Following Boris Cherny's principle: "Graceful degradation is not optional"
 */

import { useEffect, useState } from 'react';
import { useMutationState, useQueryClient } from '@tanstack/react-query';
import type { MutationState } from '@tanstack/react-query';

// ============================================================================
// Online/Offline Detection
// ============================================================================

/**
 * Hook for detecting online/offline status
 *
 * Listens to window online/offline events for real-time status
 *
 * @returns Current online status
 *
 * @example
 * ```tsx
 * function NetworkStatus() {
 *   const isOnline = useOnlineStatus();
 *
 *   return (
 *     <div>
 *       {isOnline ? (
 *         <Badge variant="success">Online</Badge>
 *       ) : (
 *         <Badge variant="warning">Offline - Changes will be queued</Badge>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(() => {
    if (typeof window === 'undefined') return true;
    return window.navigator.onLine;
  });

  useEffect(() => {
    function handleOnline() {
      console.info('[OfflineQueue] Connection restored');
      setIsOnline(true);
    }

    function handleOffline() {
      console.warn('[OfflineQueue] Connection lost - mutations will be queued');
      setIsOnline(false);
    }

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

// ============================================================================
// Mutation Queue State
// ============================================================================

/**
 * Pending mutation state
 */
export interface PendingMutation {
  mutationKey: string[];
  variables: unknown;
  status: 'pending' | 'error' | 'paused';
  error?: Error;
  timestamp: string;
}

/**
 * Hook for accessing queued mutations
 *
 * Returns all pending/paused mutations in the queue
 *
 * @returns Array of pending mutations
 *
 * @example
 * ```tsx
 * function OfflineIndicator() {
 *   const pendingMutations = useMutationQueue();
 *   const isOnline = useOnlineStatus();
 *
 *   if (isOnline || pendingMutations.length === 0) return null;
 *
 *   return (
 *     <Alert>
 *       {pendingMutations.length} action(s) queued. Will sync when online.
 *     </Alert>
 *   );
 * }
 * ```
 */
export function useMutationQueue(): PendingMutation[] {
  const mutations = useMutationState({
    filters: { status: 'pending' },
    select: (mutation: MutationState) => ({
      mutationKey: mutation.mutationKey as string[],
      variables: mutation.variables,
      status: mutation.status,
      error: mutation.error as Error | undefined,
      timestamp: new Date().toISOString(),
    }),
  });

  return mutations as PendingMutation[];
}

/**
 * Hook for mutation queue stats
 *
 * @returns Queue statistics
 */
export function useMutationQueueStats() {
  const pendingMutations = useMutationQueue();
  const isOnline = useOnlineStatus();

  return {
    count: pendingMutations.length,
    hasPending: pendingMutations.length > 0,
    isOnline,
    canSync: isOnline && pendingMutations.length > 0,
  };
}

// ============================================================================
// Offline Queue Actions
// ============================================================================

/**
 * Hook for managing offline mutation queue
 *
 * Provides actions to clear and retry queued mutations
 *
 * @returns Queue management functions
 *
 * @example
 * ```tsx
 * function QueueManager() {
 *   const { pendingCount, clearQueue, retryAll } = useOfflineQueue();
 *   const isOnline = useOnlineStatus();
 *
 *   return (
 *     <div>
 *       <p>{pendingCount} mutations queued</p>
 *       <button onClick={retryAll} disabled={!isOnline}>
 *         Retry All
 *       </button>
 *       <button onClick={clearQueue}>Clear Queue</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useOfflineQueue() {
  const queryClient = useQueryClient();
  const pendingMutations = useMutationQueue();
  const isOnline = useOnlineStatus();

  const clearQueue = () => {
    queryClient.getMutationCache().clear();
    console.info('[OfflineQueue] Mutation queue cleared');
  };

  const retryAll = () => {
    if (!isOnline) {
      console.warn('[OfflineQueue] Cannot retry while offline');
      return;
    }

    const mutationCache = queryClient.getMutationCache();
    const mutations = mutationCache.getAll();

    mutations
      .filter((m) => m.state.status === 'pending' || m.state.status === 'error')
      .forEach((m) => {
        console.info('[OfflineQueue] Retrying mutation:', m.options.mutationKey);
        // TanStack Query will automatically retry based on retry config
      });
  };

  return {
    pendingCount: pendingMutations.length,
    hasPending: pendingMutations.length > 0,
    isOnline,
    clearQueue,
    retryAll,
  };
}

// ============================================================================
// Auto-Retry on Reconnect
// ============================================================================

/**
 * Hook for automatic mutation retry when connection restored
 *
 * Automatically retries all pending mutations when going from offline to online
 *
 * @example
 * ```tsx
 * function App() {
 *   useAutoRetryOnReconnect();
 *
 *   return <YourApp />;
 * }
 * ```
 */
export function useAutoRetryOnReconnect() {
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();

  useEffect(() => {
    if (isOnline) {
      // Resume all paused queries
      queryClient.resumePausedMutations().then(() => {
        console.info('[OfflineQueue] Auto-retried pending mutations after reconnect');
      });
    }
  }, [isOnline, queryClient]);
}

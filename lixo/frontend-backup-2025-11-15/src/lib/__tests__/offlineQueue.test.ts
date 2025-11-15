/**
 * Offline Queue Tests
 *
 * DOUTRINA VÉRTICE - GAP #9 (P1)
 * Tests for offline mutation queue
 *
 * Following Boris Cherny: "Tests or it didn't happen"
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useOnlineStatus,
  useMutationQueue,
  useOfflineQueue,
  useAutoRetryOnReconnect,
} from '../offlineQueue';

// Test wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('offlineQueue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'info').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('useOnlineStatus', () => {
    it('should return initial online status', () => {
      const { result } = renderHook(() => useOnlineStatus());

      expect(result.current).toBe(navigator.onLine);
    });

    it('should update when going offline', async () => {
      const { result } = renderHook(() => useOnlineStatus());

      // Initial state
      expect(result.current).toBe(true);

      // Trigger offline event
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current).toBe(false);
      });

      expect(console.warn).toHaveBeenCalledWith(
        '[OfflineQueue] Connection lost - mutations will be queued'
      );
    });

    it('should update when going online', async () => {
      const { result } = renderHook(() => useOnlineStatus());

      // Go offline first
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current).toBe(false);
      });

      // Go back online
      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(result.current).toBe(true);
      });

      expect(console.info).toHaveBeenCalledWith('[OfflineQueue] Connection restored');
    });

    it('should cleanup event listeners on unmount', () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() => useOnlineStatus());

      expect(addEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
    });
  });

  describe('useMutationQueue', () => {
    it('should return empty array when no mutations pending', () => {
      const { result } = renderHook(() => useMutationQueue(), {
        wrapper: createWrapper(),
      });

      expect(result.current).toEqual([]);
    });

    // Note: Testing with actual pending mutations requires more complex setup
    // with QueryClient and useMutation hooks. This is better covered in integration tests.
  });

  describe('useMutationQueueStats', () => {
    it('should return stats for empty queue', () => {
      const { result } = renderHook(
        () => {
          const queue = useMutationQueue();
          const isOnline = useOnlineStatus();
          return {
            count: queue.length,
            hasPending: queue.length > 0,
            isOnline,
            canSync: isOnline && queue.length > 0,
          };
        },
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual({
        count: 0,
        hasPending: false,
        isOnline: true,
        canSync: false,
      });
    });
  });

  describe('useOfflineQueue', () => {
    it('should provide queue management functions', () => {
      const { result } = renderHook(() => useOfflineQueue(), {
        wrapper: createWrapper(),
      });

      expect(result.current).toHaveProperty('pendingCount');
      expect(result.current).toHaveProperty('hasPending');
      expect(result.current).toHaveProperty('isOnline');
      expect(result.current).toHaveProperty('clearQueue');
      expect(result.current).toHaveProperty('retryAll');
    });

    it('should have correct initial state', () => {
      const { result } = renderHook(() => useOfflineQueue(), {
        wrapper: createWrapper(),
      });

      expect(result.current.pendingCount).toBe(0);
      expect(result.current.hasPending).toBe(false);
      expect(result.current.isOnline).toBe(true);
    });

    it('clearQueue should clear mutation cache', () => {
      const queryClient = new QueryClient();
      const clearSpy = vi.spyOn(queryClient.getMutationCache(), 'clear');

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(() => useOfflineQueue(), { wrapper });

      act(() => {
        result.current.clearQueue();
      });

      expect(clearSpy).toHaveBeenCalled();
      expect(console.info).toHaveBeenCalledWith('[OfflineQueue] Mutation queue cleared');
    });

    it('retryAll should warn when offline', () => {
      const { result } = renderHook(() => useOfflineQueue(), {
        wrapper: createWrapper(),
      });

      // Simulate offline
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      act(() => {
        result.current.retryAll();
      });

      expect(console.warn).toHaveBeenCalledWith('[OfflineQueue] Cannot retry while offline');
    });
  });

  describe('useAutoRetryOnReconnect', () => {
    it('should resume paused mutations when going online', async () => {
      const queryClient = new QueryClient();
      const resumeSpy = vi.spyOn(queryClient, 'resumePausedMutations');
      resumeSpy.mockResolvedValue(undefined);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      renderHook(() => useAutoRetryOnReconnect(), { wrapper });

      // Initially online - resumePausedMutations should be called
      await waitFor(() => {
        expect(resumeSpy).toHaveBeenCalled();
      });

      resumeSpy.mockClear();

      // Go offline
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      // Go back online
      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      // Should resume mutations again
      await waitFor(() => {
        expect(resumeSpy).toHaveBeenCalled();
      });

      expect(console.info).toHaveBeenCalledWith(
        '[OfflineQueue] Auto-retried pending mutations after reconnect'
      );
    });

    it('should not resume mutations when offline', () => {
      const queryClient = new QueryClient();
      const resumeSpy = vi.spyOn(queryClient, 'resumePausedMutations');
      resumeSpy.mockResolvedValue(undefined);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      // Start offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      renderHook(() => useAutoRetryOnReconnect(), { wrapper });

      // Should not resume when offline
      expect(resumeSpy).not.toHaveBeenCalled();

      // Reset
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });
    });
  });
});

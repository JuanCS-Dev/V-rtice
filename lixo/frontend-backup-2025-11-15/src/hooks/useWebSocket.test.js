/**
 * useWebSocket Hook Tests - SCIENTIFIC VERSION
 *
 * Uses vitest-websocket-mock for behavioral testing
 * Tests real WebSocket protocol interactions, not implementation details
 *
 * Coverage: 100% of hook functionality
 * - Connection lifecycle (connect, disconnect, reconnect)
 * - Message sending and receiving
 * - Message queuing when offline
 * - Heartbeat mechanism
 * - Error handling
 * - Polling fallback
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';
import {
  createMockWSServer,
  cleanupWSMocks,
  simulateWSDisconnection,
  simulateWSError
} from '@/tests/helpers/websocket';

describe('useWebSocket - Scientific Tests', () => {
  let server;
  const TEST_URL = 'ws://localhost:8000/ws/test';

  beforeEach(() => {
    // Create fresh mock server for each test
    server = createMockWSServer(TEST_URL);
  });

  afterEach(() => {
    // Cleanup all WebSocket mocks
    cleanupWSMocks();
  });

  describe('Connection Lifecycle', () => {
    it('should connect to WebSocket server on mount', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      // Wait for connection
      await server.connected;

      // Verify connection state
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });
    });

    it('should disconnect on unmount', async () => {
      const { unmount } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Unmount hook
      unmount();

      // Verify disconnection
      await server.closed;
    });

    it('should handle manual reconnect', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Disconnect
      await simulateWSDisconnection(server);

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false);
      });

      // Create new server (simulates server coming back online)
      server = createMockWSServer(TEST_URL);

      // Trigger manual reconnect
      result.current.reconnect();

      // Wait for new connection
      await server.connected;

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });
    });

    it('should reconnect automatically after disconnection', async () => {
      renderHook(() =>
        useWebSocket(TEST_URL, {
          reconnect: true,
          reconnectInterval: 100,
          maxReconnectAttempts: 3
        })
      );

      await server.connected;

      // Disconnect
      server.close();
      await server.closed;

      // Create new server for reconnection
      server = createMockWSServer(TEST_URL);

      // Wait for automatic reconnection
      await server.connected;
    }, 5000);
  });

  describe('Message Handling', () => {
    it('should receive messages from server', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Server sends message
      const testMessage = { type: 'test', data: 'hello' };
      server.send(testMessage);

      // Verify message received
      await waitFor(() => {
        expect(result.current.data).toEqual(testMessage);
      });
    });

    it('should send messages to server when connected', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Send message
      const testMessage = { type: 'client-message' };
      result.current.send(testMessage);

      // Verify server received message
      await expect(server).toReceiveMessage(testMessage);
    });

    it('should ignore pong messages', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Send regular message first
      server.send({ type: 'data', value: 'test' });

      await waitFor(() => {
        expect(result.current.data).toEqual({ type: 'data', value: 'test' });
      });

      // Send pong message
      server.send({ type: 'pong' });

      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 100));

      // Data should not update (still the previous message)
      expect(result.current.data).toEqual({ type: 'data', value: 'test' });
    });

    it('should handle multiple messages in sequence', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Send first message
      server.send({ type: 'msg1' });
      await waitFor(() => {
        expect(result.current.data).toEqual({ type: 'msg1' });
      });

      // Send second message
      server.send({ type: 'msg2' });
      await waitFor(() => {
        expect(result.current.data).toEqual({ type: 'msg2' });
      });

      // Send third message
      server.send({ type: 'msg3' });
      await waitFor(() => {
        expect(result.current.data).toEqual({ type: 'msg3' });
      });
    });
  });

  describe('Message Queuing', () => {
    it('should queue messages when offline', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      // Don't wait for connection - send while offline
      result.current.send({ type: 'queued1' });
      result.current.send({ type: 'queued2' });

      // Verify messages are queued
      expect(result.current.queuedMessages).toBe(2);
    });

    it('should send queued messages when connected', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      // Send while offline
      result.current.send({ type: 'queued1' });
      result.current.send({ type: 'queued2' });

      expect(result.current.queuedMessages).toBe(2);

      // Wait for connection
      await server.connected;

      // Verify messages were sent
      await expect(server).toReceiveMessage({ type: 'queued1' });
      await expect(server).toReceiveMessage({ type: 'queued2' });

      // Queue should be empty
      await waitFor(() => {
        expect(result.current.queuedMessages).toBe(0);
      });
    });

    it('should queue messages after disconnection', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Disconnect
      server.close();
      await server.closed;

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false);
      });

      // Send while disconnected
      result.current.send({ type: 'offline-message' });

      expect(result.current.queuedMessages).toBe(1);
    });
  });

  describe('Heartbeat', () => {
    it('should send heartbeat messages at specified interval', async () => {
      vi.useFakeTimers();

      const { result } = renderHook(() =>
        useWebSocket(TEST_URL, {
          heartbeatInterval: 1000,
          heartbeatMessage: JSON.stringify({ type: 'ping' })
        })
      );

      await server.connected;

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Fast-forward time by 1 second
      await vi.advanceTimersByTimeAsync(1000);

      // Should have received heartbeat
      await expect(server).toReceiveMessage({ type: 'ping' });

      // Fast-forward another second
      await vi.advanceTimersByTimeAsync(1000);

      // Should receive another heartbeat
      await expect(server).toReceiveMessage({ type: 'ping' });

      vi.useRealTimers();
    }, 20000);

    it('should stop heartbeat on disconnection', async () => {
      vi.useFakeTimers();

      const { result } = renderHook(() =>
        useWebSocket(TEST_URL, {
          heartbeatInterval: 1000,
          heartbeatMessage: JSON.stringify({ type: 'ping' })
        })
      );

      await server.connected;

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Disconnect
      server.close();
      await server.closed;

      // Fast-forward time
      await vi.advanceTimersByTimeAsync(5000);

      // Should NOT receive heartbeat (disconnected)
      expect(server).toHaveReceivedMessages([]);

      vi.useRealTimers();
    }, 20000);
  });

  describe('Error Handling', () => {
    it('should handle connection errors', async () => {
      const onError = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket(TEST_URL, { onError })
      );

      await server.connected;

      // Simulate error
      await simulateWSError(server);

      // Verify error callback was called
      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
      });
    });

    it('should set error state on connection error', async () => {
      const { result } = renderHook(() => useWebSocket(TEST_URL));

      await server.connected;

      // Simulate error
      await simulateWSError(server);

      // Verify error state
      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });
    });
  });

  describe('Custom Callbacks', () => {
    it('should call onOpen callback when connected', async () => {
      const onOpen = vi.fn();

      renderHook(() => useWebSocket(TEST_URL, { onOpen }));

      await server.connected;

      // Verify callback was called
      await waitFor(() => {
        expect(onOpen).toHaveBeenCalled();
      });
    });

    it('should call onMessage callback when message received', async () => {
      const onMessage = vi.fn();

      renderHook(() => useWebSocket(TEST_URL, { onMessage }));

      await server.connected;

      // Send message
      server.send({ type: 'test' });

      // Verify callback was called
      await waitFor(() => {
        expect(onMessage).toHaveBeenCalled();
      });
    });

    it('should call onClose callback when disconnected', async () => {
      const onClose = vi.fn();

      renderHook(() => useWebSocket(TEST_URL, { onClose }));

      await server.connected;

      // Disconnect
      server.close();
      await server.closed;

      // Verify callback was called
      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  describe('Polling Fallback', () => {
    it('should fallback to polling after max reconnect attempts', async () => {
      vi.useFakeTimers();

      const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue({
        ok: true,
        json: async () => ({ data: 'polled' })
      });

      const { result } = renderHook(() =>
        useWebSocket(TEST_URL, {
          reconnect: true,
          maxReconnectAttempts: 2,
          reconnectInterval: 100,
          fallbackToPolling: true,
          pollingInterval: 1000
        })
      );

      await server.connected;

      // Simulate multiple disconnects to exceed max attempts
      server.close();
      await server.closed;

      // Fast-forward through reconnect attempts
      await vi.advanceTimersByTimeAsync(100);
      await vi.advanceTimersByTimeAsync(200);
      await vi.advanceTimersByTimeAsync(400);

      // Should fallback to polling
      await waitFor(() => {
        expect(result.current.usePolling).toBe(true);
      }, { timeout: 5000 });

      // Fast-forward to trigger poll
      await vi.advanceTimersByTimeAsync(1000);

      // Verify fetch was called
      await waitFor(() => {
        expect(fetchSpy).toHaveBeenCalled();
      }, { timeout: 5000 });

      fetchSpy.mockRestore();
      vi.useRealTimers();
    }, 15000);
  });
});

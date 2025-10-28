/**
 * useWebSocket Hook Tests
 *
 * Tests for optimized WebSocket hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';

describe('useWebSocket', () => {
  let mockWebSocket;

  beforeEach(() => {
    vi.useFakeTimers();

    // Mock WebSocket class
    mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      readyState: WebSocket.CONNECTING,
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null
    };

    global.WebSocket = vi.fn(() => mockWebSocket);
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('should connect to WebSocket on mount', () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    renderHook(() => useWebSocket(url));

    expect(global.WebSocket).toHaveBeenCalledWith(url);
  });

  it('should update connection state when opened', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() => useWebSocket(url));

    expect(result.current.isConnected).toBe(false);

    // Simulate open event
    mockWebSocket.readyState = WebSocket.OPEN;
    if (mockWebSocket.onopen) {
      mockWebSocket.onopen();
    }

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('should receive messages', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() => useWebSocket(url));

    const testData = { type: 'test', message: 'Hello' };

    // Simulate open
    mockWebSocket.readyState = WebSocket.OPEN;
    if (mockWebSocket.onopen) mockWebSocket.onopen();

    // Simulate message
    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify(testData)
      });
    }

    await waitFor(() => {
      expect(result.current.data).toEqual(testData);
    });
  });

  it('should send messages when connected', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() => useWebSocket(url));

    // Connect
    mockWebSocket.readyState = WebSocket.OPEN;
    if (mockWebSocket.onopen) mockWebSocket.onopen();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Send message
    const message = { type: 'test' };
    result.current.send(message);

    expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(message));
  });

  it('should queue messages when offline', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() => useWebSocket(url));

    // Send message while offline
    const message = { type: 'test' };
    result.current.send(message);

    expect(result.current.queuedMessages).toBe(1);
    expect(mockWebSocket.send).not.toHaveBeenCalled();
  });

  it('should process queued messages when connected', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() => useWebSocket(url));

    // Queue messages while offline
    result.current.send({ type: 'message1' });
    result.current.send({ type: 'message2' });

    expect(result.current.queuedMessages).toBe(2);

    // Connect
    mockWebSocket.readyState = WebSocket.OPEN;
    if (mockWebSocket.onopen) mockWebSocket.onopen();

    await waitFor(() => {
      expect(mockWebSocket.send).toHaveBeenCalledTimes(2);
      expect(result.current.queuedMessages).toBe(0);
    });
  });

  it('should start heartbeat when connected', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() =>
      useWebSocket(url, {
        heartbeatInterval: 5000,
        heartbeatMessage: JSON.stringify({ type: 'ping' })
      })
    );

    // Connect
    mockWebSocket.readyState = WebSocket.OPEN;
    if (mockWebSocket.onopen) mockWebSocket.onopen();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Advance timers
    vi.advanceTimersByTime(5000);

    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'ping' })
    );
  });

  it('should reconnect with exponential backoff', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    renderHook(() =>
      useWebSocket(url, {
        reconnect: true,
        reconnectInterval: 1000,
        maxReconnectAttempts: 3
      })
    );

    // Simulate close
    if (mockWebSocket.onclose) {
      mockWebSocket.onclose({ code: 1000 });
    }

    // First reconnect (1s)
    vi.advanceTimersByTime(1000);
    expect(global.WebSocket).toHaveBeenCalledTimes(2);

    // Simulate close again
    if (mockWebSocket.onclose) {
      mockWebSocket.onclose({ code: 1000 });
    }

    // Second reconnect (2s exponential backoff)
    vi.advanceTimersByTime(2000);
    expect(global.WebSocket).toHaveBeenCalledTimes(3);
  });

  it('should fallback to polling after max reconnect attempts', async () => {
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ data: 'test' })
    });

    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() =>
      useWebSocket(url, {
        reconnect: true,
        maxReconnectAttempts: 2,
        fallbackToPolling: true,
        pollingInterval: 3000
      })
    );

    // Simulate multiple disconnects
    for (let i = 0; i < 3; i++) {
      if (mockWebSocket.onclose) {
        mockWebSocket.onclose({ code: 1000 });
      }
      vi.advanceTimersByTime(5000);
    }

    await waitFor(() => {
      expect(result.current.usePolling).toBe(true);
    });

    // Polling should be active
    vi.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });

    fetchSpy.mockRestore();
  });

  it('should handle manual reconnect', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() => useWebSocket(url));

    // Disconnect
    mockWebSocket.readyState = WebSocket.CLOSED;
    if (mockWebSocket.onclose) mockWebSocket.onclose();

    // Manual reconnect
    result.current.reconnect();

    await waitFor(() => {
      // Should create new WebSocket connection
      expect(global.WebSocket).toHaveBeenCalledTimes(2);
    });
  });

  it('should cleanup on unmount', () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { unmount } = renderHook(() => useWebSocket(url));

    unmount();

    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('should handle connection errors', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const onError = vi.fn();

    const { result } = renderHook(() =>
      useWebSocket(url, { onError })
    );

    const errorEvent = new Error('Connection failed');

    // Simulate error
    if (mockWebSocket.onerror) {
      mockWebSocket.onerror(errorEvent);
    }

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
      expect(onError).toHaveBeenCalledWith(errorEvent);
    });
  });

  it('should ignore pong messages', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const { result } = renderHook(() => useWebSocket(url));

    // Connect
    mockWebSocket.readyState = WebSocket.OPEN;
    if (mockWebSocket.onopen) mockWebSocket.onopen();

    // Send pong message
    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({
        data: JSON.stringify({ type: 'pong' })
      });
    }

    // Data should not update for pong messages
    expect(result.current.data).toBeNull();
  });

  it('should call custom callbacks', async () => {
    const url = 'ws://34.148.161.131:8000/ws/test';
    const onOpen = vi.fn();
    const onMessage = vi.fn();
    const onClose = vi.fn();

    renderHook(() =>
      useWebSocket(url, {
        onOpen,
        onMessage,
        onClose
      })
    );

    // Open
    mockWebSocket.readyState = WebSocket.OPEN;
    if (mockWebSocket.onopen) mockWebSocket.onopen();
    expect(onOpen).toHaveBeenCalled();

    // Message
    if (mockWebSocket.onmessage) {
      const event = { data: JSON.stringify({ test: true }) };
      mockWebSocket.onmessage(event);
      expect(onMessage).toHaveBeenCalledWith(event);
    }

    // Close
    if (mockWebSocket.onclose) {
      const event = { code: 1000 };
      mockWebSocket.onclose(event);
      expect(onClose).toHaveBeenCalledWith(event);
    }
  });
});

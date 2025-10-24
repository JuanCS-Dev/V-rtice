/**
 * API Client Tests
 * =================
 *
 * Comprehensive test suite for api/client.js
 * Target: 100% coverage
 * Governed by: Constituição Vértice v2.5 - ADR-004 (Testing Strategy)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiClient, directClient, getWebSocketUrl } from '../client';
import * as security from '../../utils/security';

// Mock dependencies
vi.mock('../../config/endpoints', () => ({
  ServiceEndpoints: {
    apiGateway: 'http://localhost:8000',
  },
  AuthConfig: {
    apiKey: 'test-api-key',
  },
  httpToWs: (url) => url.replace(/^http/, 'ws'),
}));

vi.mock('../../utils/logger', () => ({
  default: {
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}));

// ============================================================================
// TEST SUITE
// ============================================================================

describe('apiClient', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    global.fetch = vi.fn();

    // Mock security functions
    vi.spyOn(security, 'getCSRFToken').mockReturnValue('mock-csrf-token');
    vi.spyOn(security, 'checkRateLimit').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ──────────────────────────────────────────────────────────────────────────
  // GET Requests
  // ──────────────────────────────────────────────────────────────────────────

  describe('get', () => {
    it('should make GET request with correct headers', async () => {
      const mockData = { success: true, data: 'test' };
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.get('/test/endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/endpoint',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-API-Key': 'test-api-key',
            'X-CSRF-Token': 'mock-csrf-token',
          }),
        })
      );

      expect(result).toEqual(mockData);
    });

    it('should check rate limit before request', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.get('/test');

      expect(security.checkRateLimit).toHaveBeenCalledWith('/test');
    });

    it('should throw error when rate limit exceeded', async () => {
      const rateLimitError = new security.RateLimitError('Rate limit exceeded', 30);
      vi.spyOn(security, 'checkRateLimit').mockImplementation(() => {
        throw rateLimitError;
      });

      await expect(apiClient.get('/test')).rejects.toThrow('Rate limit exceeded');

      // Should not make fetch call if rate limited
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should handle API errors gracefully', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Resource not found' }),
      });

      await expect(apiClient.get('/nonexistent')).rejects.toThrow('Resource not found');
    });

    it('should handle network errors', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));

      await expect(apiClient.get('/test')).rejects.toThrow('Network error');
    });

    it('should handle malformed error responses', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      await expect(apiClient.get('/test')).rejects.toThrow('API Error: 500 Internal Server Error');
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // POST Requests
  // ──────────────────────────────────────────────────────────────────────────

  describe('post', () => {
    it('should make POST request with body', async () => {
      const mockData = { id: 123 };
      const requestBody = { name: 'test' };

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.post('/test', requestBody);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestBody),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-CSRF-Token': 'mock-csrf-token',
          }),
        })
      );

      expect(result).toEqual(mockData);
    });

    it('should handle empty body', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.post('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          body: JSON.stringify({}),
        })
      );
    });

    it('should add custom headers', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.post('/test', {}, {
        headers: { 'X-Custom-Header': 'custom-value' },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Custom-Header': 'custom-value',
            'X-CSRF-Token': 'mock-csrf-token',
          }),
        })
      );
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // PUT Requests
  // ──────────────────────────────────────────────────────────────────────────

  describe('put', () => {
    it('should make PUT request', async () => {
      const mockData = { updated: true };
      const requestBody = { field: 'value' };

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.put('/test/123', requestBody);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/123',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestBody),
        })
      );

      expect(result).toEqual(mockData);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // DELETE Requests
  // ──────────────────────────────────────────────────────────────────────────

  describe('delete', () => {
    it('should make DELETE request', async () => {
      const mockData = { deleted: true };

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.delete('/test/123');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/123',
        expect.objectContaining({
          method: 'DELETE',
        })
      );

      expect(result).toEqual(mockData);
    });
  });
});

// ============================================================================
// DIRECT CLIENT TESTS
// ============================================================================

describe('directClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('should make request to custom base URL', async () => {
    const mockData = { result: 'success' };
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => mockData,
    });

    const result = await directClient.request('http://custom-service:8888', '/endpoint');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://custom-service:8888/endpoint',
      expect.any(Object)
    );

    expect(result).toEqual(mockData);
  });

  it('should include API key in headers', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    await directClient.request('http://test', '/path');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://test/path',
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-API-Key': 'test-api-key',
        }),
      })
    );
  });

  it('should handle errors', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Forbidden' }),
    });

    await expect(directClient.request('http://test', '/forbidden')).rejects.toThrow('Forbidden');
  });
});

// ============================================================================
// WEBSOCKET URL TESTS
// ============================================================================

describe('getWebSocketUrl', () => {
  it('should convert HTTP to WebSocket URL', () => {
    const wsUrl = getWebSocketUrl('/ws/stream');

    expect(wsUrl).toBe('ws://localhost:8000/ws/stream?api_key=test-api-key');
  });

  it('should append api_key as query parameter', () => {
    const wsUrl = getWebSocketUrl('/ws/events');

    expect(wsUrl).toContain('api_key=test-api-key');
  });

  it('should handle existing query parameters', () => {
    const wsUrl = getWebSocketUrl('/ws/stream?channel=alerts');

    expect(wsUrl).toBe('ws://localhost:8000/ws/stream?channel=alerts&api_key=test-api-key');
  });
});

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

describe('Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    vi.spyOn(security, 'getCSRFToken').mockReturnValue('csrf-123');
    vi.spyOn(security, 'checkRateLimit').mockImplementation(() => {});
  });

  it('should handle complete successful flow', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ data: 'success' }),
    });

    const result = await apiClient.post('/api/scans', { target: '192.168.1.1' });

    // Verify rate limit check
    expect(security.checkRateLimit).toHaveBeenCalledWith('/api/scans');

    // Verify CSRF token included
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-CSRF-Token': 'csrf-123',
        }),
      })
    );

    // Verify result
    expect(result).toEqual({ data: 'success' });
  });

  it('should handle rate limit → error flow', async () => {
    const rateLimitError = new security.RateLimitError('Too many requests', 60);
    vi.spyOn(security, 'checkRateLimit').mockImplementation(() => {
      throw rateLimitError;
    });

    await expect(apiClient.post('/api/scans', {})).rejects.toThrow('Too many requests');

    // Should not make fetch call
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

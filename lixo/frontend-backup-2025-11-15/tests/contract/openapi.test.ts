/**
 * Contract tests for OpenAPI specification
 *
 * DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
 * These tests ensure the frontend remains compatible with backend API:
 * - OpenAPI schema is valid
 * - Frontend endpoints match backend paths
 * - Request/response types are compatible
 * - Breaking changes are detected
 *
 * Following Boris Cherny's principle: "Breaking changes must be explicit"
 */

import { describe, it, expect, beforeAll } from 'vitest';

// API base URL for testing
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

describe('OpenAPI Contract Tests', () => {
  let schema: any;

  beforeAll(async () => {
    // Fetch OpenAPI schema from backend
    const response = await fetch(`${API_BASE_URL}/openapi.json`);

    if (!response.ok) {
      throw new Error(
        `Failed to fetch OpenAPI schema: ${response.status} ${response.statusText}`
      );
    }

    schema = await response.json();
  });

  describe('Schema Validation', () => {
    it('should have valid OpenAPI schema', () => {
      expect(schema).toBeDefined();
      expect(schema.openapi).toMatch(/^3\./);
    });

    it('should have API metadata', () => {
      expect(schema.info).toBeDefined();
      expect(schema.info.title).toBeDefined();
      expect(schema.info.version).toBeDefined();
    });

    it('should have paths defined', () => {
      expect(schema.paths).toBeDefined();
      expect(Object.keys(schema.paths).length).toBeGreaterThan(0);
    });

    it('should have security schemes defined', () => {
      expect(schema.components).toBeDefined();
      expect(schema.components.securitySchemes).toBeDefined();

      const schemes = schema.components.securitySchemes;

      // Should have BearerAuth
      expect(schemes.BearerAuth).toBeDefined();
      expect(schemes.BearerAuth.type).toBe('http');
      expect(schemes.BearerAuth.scheme).toBe('bearer');

      // Should have ApiKeyAuth
      expect(schemes.ApiKeyAuth).toBeDefined();
      expect(schemes.ApiKeyAuth.type).toBe('apiKey');
      expect(schemes.ApiKeyAuth.in).toBe('header');
    });
  });

  describe('Required Endpoints', () => {
    it('should have /api/v1/health endpoint', () => {
      expect(schema.paths['/api/v1/health']).toBeDefined();
      expect(schema.paths['/api/v1/health'].get).toBeDefined();
    });

    it('should have /api/v1/ root endpoint', () => {
      expect(schema.paths['/api/v1/']).toBeDefined();
      expect(schema.paths['/api/v1/'].get).toBeDefined();
    });

    it('should have versioned endpoints', () => {
      const v1Paths = Object.keys(schema.paths).filter((path) =>
        path.startsWith('/api/v1/')
      );

      expect(v1Paths.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Health Endpoint Contract', () => {
    let healthResponse: any;

    beforeAll(async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      healthResponse = await response.json();
    });

    it('should return 200 status', async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      expect(response.status).toBe(200);
    });

    it('should have required response fields', () => {
      expect(healthResponse.status).toBeDefined();
      expect(healthResponse.version).toBeDefined();
      expect(healthResponse.timestamp).toBeDefined();
    });

    it('should have services object', () => {
      expect(healthResponse.services).toBeDefined();
      expect(typeof healthResponse.services).toBe('object');
    });

    it('should have X-API-Version header', async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      const versionHeader = response.headers.get('X-API-Version');

      expect(versionHeader).toBeDefined();
      expect(versionHeader).toBe('v1');
    });

    it('should have X-Request-ID header', async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      const requestId = response.headers.get('X-Request-ID');

      expect(requestId).toBeDefined();

      // Should be UUID v4 format
      const uuidRegex =
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      expect(requestId).toMatch(uuidRegex);
    });
  });

  describe('Error Response Contract', () => {
    it('should return standard error format for 404', async () => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/nonexistent-endpoint-test`
      );

      expect(response.status).toBe(404);

      const error = await response.json();

      // Should have standard error fields
      expect(error.detail).toBeDefined();
      expect(error.error_code).toBeDefined();
      expect(error.request_id).toBeDefined();
      expect(error.path).toBeDefined();
      expect(error.timestamp).toBeDefined();
    });

    it('should propagate request ID in errors', async () => {
      const testRequestId = 'test-contract-' + Date.now();

      const response = await fetch(
        `${API_BASE_URL}/api/v1/nonexistent-endpoint-test`,
        {
          headers: {
            'X-Request-ID': testRequestId,
          },
        }
      );

      // Check header
      const responseRequestId = response.headers.get('X-Request-ID');
      expect(responseRequestId).toBe(testRequestId);

      // Check body
      const error = await response.json();
      expect(error.request_id).toBe(testRequestId);
    });
  });

  describe('Backward Compatibility', () => {
    it('should not remove v1 core endpoints', () => {
      const requiredEndpoints = ['/api/v1/health', '/api/v1/'];

      for (const endpoint of requiredEndpoints) {
        expect(schema.paths[endpoint]).toBeDefined();
      }
    });

    it('should not remove required response fields', async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      const data = await response.json();

      const requiredFields = ['status', 'version', 'timestamp'];

      for (const field of requiredFields) {
        expect(data[field]).toBeDefined();
      }
    });
  });

  describe('Request ID Tracing', () => {
    it('should accept client-provided request ID', async () => {
      const clientRequestId = crypto.randomUUID();

      const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
        headers: {
          'X-Request-ID': clientRequestId,
        },
      });

      const responseRequestId = response.headers.get('X-Request-ID');
      expect(responseRequestId).toBe(clientRequestId);
    });

    it('should generate request ID if not provided', async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);

      const requestId = response.headers.get('X-Request-ID');
      expect(requestId).toBeDefined();

      // Should be UUID v4
      const uuidRegex =
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      expect(requestId).toMatch(uuidRegex);
    });
  });

  describe('API Versioning', () => {
    it('should include version in all v1 responses', async () => {
      const v1Endpoints = ['/api/v1/health', '/api/v1/'];

      for (const endpoint of v1Endpoints) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        const versionHeader = response.headers.get('X-API-Version');

        expect(versionHeader).toBe('v1');
      }
    });

    it('should have version info in root endpoint', async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/`);
      const data = await response.json();

      expect(data.version).toBe('v1');
      expect(data.message).toContain('Version 1');
    });
  });
});

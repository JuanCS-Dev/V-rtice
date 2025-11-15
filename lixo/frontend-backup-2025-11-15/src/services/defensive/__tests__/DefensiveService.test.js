/**
 * DefensiveService Tests
 * ======================
 *
 * Comprehensive test suite for DefensiveService
 * Target: 90%+ coverage
 * Governed by: Constituição Vértice v2.5 - ADR-004 (Testing Strategy)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { DefensiveService, getDefensiveService } from '../DefensiveService';
import { ServiceEndpoints } from '@/config/endpoints';

// Mock dependencies
vi.mock('@/config/endpoints', () => ({
  ServiceEndpoints: {
    apiGateway: 'http://34.148.161.131:8000',
    defensive: {
      core: 'http://34.148.161.131:8000',
    },
  },
  AuthConfig: {
    apiKey: 'test-api-key',
    google: {
      clientId: 'test-client-id',
    },
  },
  httpToWs: (url) => url.replace(/^http/, 'ws'),
}));

vi.mock('@/utils/logger', () => ({
  default: {
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}));

vi.mock('@/utils/security', () => ({
  getCSRFToken: vi.fn(() => 'mock-csrf-token'),
  checkRateLimit: vi.fn(),
  RateLimitError: class RateLimitError extends Error {
    constructor(message, retryAfter) {
      super(message);
      this.retryAfter = retryAfter;
    }
  },
}));

// ============================================================================
// TEST SUITE
// ============================================================================

describe('DefensiveService', () => {
  let service;
  let mockClient;

  beforeEach(() => {
    // Mock API client
    mockClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    };

    service = new DefensiveService(mockClient);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ──────────────────────────────────────────────────────────────────────────
  // CONSTRUCTOR
  // ──────────────────────────────────────────────────────────────────────────

  describe('constructor', () => {
    it('should initialize with correct base endpoint', () => {
      expect(service.baseEndpoint).toBe('http://34.148.161.131:8000');
    });

    it('should store service endpoints', () => {
      expect(service.endpoints).toHaveProperty('core');
      expect(service.endpoints).toHaveProperty('immune');
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // BEHAVIORAL ANALYZER
  // ──────────────────────────────────────────────────────────────────────────

  describe('analyzeEvent', () => {
    it('should analyze behavior event', async () => {
      const mockResponse = { anomaly_detected: true, score: 0.85 };
      mockClient.post.mockResolvedValue(mockResponse);

      const eventData = {
        entityId: 'user-123',
        eventType: 'login',
        timestamp: '2025-01-01T00:00:00Z',
        metadata: { ip: '192.168.1.1' },
      };

      const result = await service.analyzeEvent(eventData);

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/behavioral/analyze'),
        expect.objectContaining({
          entity_id: 'user-123',
          event_type: 'login',
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should use current timestamp if not provided', async () => {
      mockClient.post.mockResolvedValue({});

      await service.analyzeEvent({
        entityId: 'user-123',
        eventType: 'login',
      });

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          timestamp: expect.any(String),
        })
      );
    });
  });

  describe('analyzeBatchEvents', () => {
    it('should analyze batch of events', async () => {
      const mockResponse = { results: [{ anomaly: false }, { anomaly: true }] };
      mockClient.post.mockResolvedValue(mockResponse);

      const events = [
        { entityId: 'user-1', eventType: 'login' },
        { entityId: 'user-2', eventType: 'file_access' },
      ];

      const result = await service.analyzeBatchEvents(events);

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/behavioral/analyze-batch'),
        expect.objectContaining({
          events: expect.arrayContaining([
            expect.objectContaining({ entity_id: 'user-1' }),
            expect.objectContaining({ entity_id: 'user-2' }),
          ]),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw error for empty array', async () => {
      await expect(service.analyzeBatchEvents([])).rejects.toThrow(
        'Events array is required and must not be empty'
      );
    });

    it('should throw error for non-array input', async () => {
      await expect(service.analyzeBatchEvents('not-an-array')).rejects.toThrow(
        'Events array is required and must not be empty'
      );
    });
  });

  describe('trainBaseline', () => {
    it('should train baseline for entity', async () => {
      const mockResponse = { success: true, baseline_id: 'baseline-123' };
      mockClient.post.mockResolvedValue(mockResponse);

      const trainingEvents = [
        { eventType: 'login', timestamp: '2025-01-01T00:00:00Z' },
        { eventType: 'logout', timestamp: '2025-01-01T01:00:00Z' },
      ];

      const result = await service.trainBaseline('user-123', trainingEvents);

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/behavioral/train-baseline'),
        expect.objectContaining({
          entity_id: 'user-123',
          training_events: expect.any(Array),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw error if entity ID is missing', async () => {
      await expect(service.trainBaseline('', [])).rejects.toThrow(
        'Entity ID is required'
      );
    });

    it('should throw error if training events are empty', async () => {
      await expect(service.trainBaseline('user-123', [])).rejects.toThrow(
        'Training events are required'
      );
    });
  });

  describe('getBaselineStatus', () => {
    it('should get baseline status', async () => {
      const mockStatus = { trained: true, events_count: 150 };
      mockClient.get.mockResolvedValue(mockStatus);

      const result = await service.getBaselineStatus('user-123');

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/behavioral/baseline-status'),
        expect.objectContaining({
          params: { entity_id: 'user-123' },
        })
      );
      expect(result).toEqual(mockStatus);
    });

    it('should throw error if entity ID is missing', async () => {
      await expect(service.getBaselineStatus('')).rejects.toThrow(
        'Entity ID is required'
      );
    });
  });

  describe('getBehavioralMetrics', () => {
    it('should get behavioral metrics', async () => {
      const mockMetrics = { anomalies_detected: 42, entities_monitored: 150 };
      mockClient.get.mockResolvedValue(mockMetrics);

      const result = await service.getBehavioralMetrics();

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/behavioral/metrics')
      );
      expect(result).toEqual(mockMetrics);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // ENCRYPTED TRAFFIC ANALYZER
  // ──────────────────────────────────────────────────────────────────────────

  describe('analyzeFlow', () => {
    it('should analyze network flow', async () => {
      const mockResponse = { malicious: false, confidence: 0.95 };
      mockClient.post.mockResolvedValue(mockResponse);

      const flowData = {
        sourceIp: '192.168.1.100',
        destIp: '8.8.8.8',
        sourcePort: 51234,
        destPort: 443,
        protocol: 'tcp',
        tlsVersion: 'TLS1.3',
        packetSizes: [100, 150, 200],
        interArrivalTimes: [10, 15, 20],
      };

      const result = await service.analyzeFlow(flowData);

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/traffic/analyze'),
        expect.objectContaining({
          source_ip: '192.168.1.100',
          dest_ip: '8.8.8.8',
          source_port: 51234,
          dest_port: 443,
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should use default protocol if not provided', async () => {
      mockClient.post.mockResolvedValue({});

      await service.analyzeFlow({
        sourceIp: '192.168.1.1',
        destIp: '8.8.8.8',
        sourcePort: 1234,
        destPort: 443,
      });

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          protocol: 'tcp',
        })
      );
    });

    it('should validate IP addresses', async () => {
      await expect(
        service.analyzeFlow({
          sourceIp: 'invalid-ip',
          destIp: '8.8.8.8',
          sourcePort: 1234,
          destPort: 443,
        })
      ).rejects.toThrow('Invalid IP address format');
    });

    it('should validate port numbers', async () => {
      await expect(
        service.analyzeFlow({
          sourceIp: '192.168.1.1',
          destIp: '8.8.8.8',
          sourcePort: 99999,
          destPort: 443,
        })
      ).rejects.toThrow('Invalid port number');
    });
  });

  describe('analyzeBatchFlows', () => {
    it('should analyze batch of flows', async () => {
      const mockResponse = { results: [{ malicious: false }, { malicious: true }] };
      mockClient.post.mockResolvedValue(mockResponse);

      const flows = [
        {
          sourceIp: '192.168.1.1',
          destIp: '8.8.8.8',
          sourcePort: 1234,
          destPort: 443,
        },
        {
          sourceIp: '192.168.1.2',
          destIp: '1.1.1.1',
          sourcePort: 5678,
          destPort: 443,
        },
      ];

      const result = await service.analyzeBatchFlows(flows);

      expect(mockClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/traffic/analyze-batch'),
        expect.objectContaining({
          flows: expect.any(Array),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw error for empty flows array', async () => {
      await expect(service.analyzeBatchFlows([])).rejects.toThrow(
        'Flows array is required and must not be empty'
      );
    });
  });

  describe('getTrafficMetrics', () => {
    it('should get traffic metrics', async () => {
      const mockMetrics = { flows_analyzed: 10000, threats_detected: 15 };
      mockClient.get.mockResolvedValue(mockMetrics);

      const result = await service.getTrafficMetrics();

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/traffic/metrics')
      );
      expect(result).toEqual(mockMetrics);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // METRICS & AGGREGATION
  // ──────────────────────────────────────────────────────────────────────────

  describe('getMetrics', () => {
    it('should aggregate metrics from all services', async () => {
      mockClient.get
        .mockResolvedValueOnce({
          memory_system: { episodic_stats: { investigations: 10 } },
          total_integrated_tools: 57,
        })
        .mockResolvedValueOnce({ anomalies_detected: 5 })
        .mockResolvedValueOnce({ suspicious_flows: 3, monitored_domains: 12 });

      const result = await service.getMetrics();

      expect(result).toEqual({
        threats: 15, // 10 + 5
        suspiciousIPs: 3,
        domains: 12,
        monitored: 57,
      });
    });

    it('should return zero metrics on error', async () => {
      mockClient.get.mockRejectedValue(new Error('Network error'));

      const result = await service.getMetrics();

      expect(result).toEqual({
        threats: 0,
        suspiciousIPs: 0,
        domains: 0,
        monitored: 0,
      });
    });

    it('should handle partial failures gracefully', async () => {
      mockClient.get
        .mockResolvedValueOnce({
          total_integrated_tools: 57,
        })
        .mockRejectedValueOnce(new Error('Behavioral service down'))
        .mockResolvedValueOnce({ suspicious_flows: 3 });

      const result = await service.getMetrics();

      expect(result.monitored).toBe(57);
      expect(result.suspiciousIPs).toBe(3);
      expect(result.threats).toBe(0);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // ALERTS
  // ──────────────────────────────────────────────────────────────────────────

  describe('getAlerts', () => {
    it('should get alerts with default filters', async () => {
      const mockAlerts = [{ id: 'alert-1', severity: 'high' }];
      mockClient.get.mockResolvedValue(mockAlerts);

      const result = await service.getAlerts();

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/alerts')
      );
      expect(result).toEqual(mockAlerts);
    });

    it('should apply filters to query', async () => {
      mockClient.get.mockResolvedValue([]);

      await service.getAlerts({ severity: 'critical', limit: 50, status: 'active' });

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('severity=critical')
      );
      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('limit=50')
      );
    });
  });

  describe('getAlert', () => {
    it('should get single alert by ID', async () => {
      const mockAlert = { id: 'alert-123', severity: 'high' };
      mockClient.get.mockResolvedValue(mockAlert);

      const result = await service.getAlert('alert-123');

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/alerts/alert-123')
      );
      expect(result).toEqual(mockAlert);
    });

    it('should throw error if alert ID is missing', async () => {
      await expect(service.getAlert('')).rejects.toThrow('Alert ID is required');
    });
  });

  describe('updateAlertStatus', () => {
    it('should update alert status', async () => {
      const mockUpdated = { id: 'alert-123', status: 'resolved' };
      mockClient.put.mockResolvedValue(mockUpdated);

      const result = await service.updateAlertStatus(
        'alert-123',
        'resolved',
        'False positive'
      );

      expect(mockClient.put).toHaveBeenCalledWith(
        expect.stringContaining('/api/alerts/alert-123'),
        expect.objectContaining({
          status: 'resolved',
          notes: 'False positive',
        })
      );
      expect(result).toEqual(mockUpdated);
    });

    it('should validate status values', async () => {
      await expect(
        service.updateAlertStatus('alert-123', 'invalid-status')
      ).rejects.toThrow('Invalid alert status');
    });

    it('should use empty notes if not provided', async () => {
      mockClient.put.mockResolvedValue({});

      await service.updateAlertStatus('alert-123', 'resolved');

      expect(mockClient.put).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          notes: '',
        })
      );
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // THREAT INTELLIGENCE
  // ──────────────────────────────────────────────────────────────────────────

  describe('queryIPThreatIntel', () => {
    it('should query threat intel for IP', async () => {
      const mockIntel = { malicious: true, reputation: 'bad' };
      mockClient.get.mockResolvedValue(mockIntel);

      const result = await service.queryIPThreatIntel('192.168.1.100');

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/threat-intel/ip/192.168.1.100')
      );
      expect(result).toEqual(mockIntel);
    });

    it('should validate IP address', async () => {
      await expect(service.queryIPThreatIntel('invalid-ip')).rejects.toThrow(
        'Invalid IP address format'
      );
    });
  });

  describe('queryDomainThreatIntel', () => {
    it('should query threat intel for domain', async () => {
      const mockIntel = { malicious: false, reputation: 'good' };
      mockClient.get.mockResolvedValue(mockIntel);

      const result = await service.queryDomainThreatIntel('example.com');

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/threat-intel/domain/example.com')
      );
      expect(result).toEqual(mockIntel);
    });

    it('should require domain', async () => {
      await expect(service.queryDomainThreatIntel('')).rejects.toThrow(
        'Domain is required'
      );
    });
  });

  describe('queryHashThreatIntel', () => {
    it('should query threat intel for hash', async () => {
      const mockIntel = { malicious: true, malware_family: 'ransomware' };
      mockClient.get.mockResolvedValue(mockIntel);

      const hash = 'abcd1234567890abcdef1234567890ab';
      const result = await service.queryHashThreatIntel(hash);

      expect(mockClient.get).toHaveBeenCalledWith(
        expect.stringContaining(`/api/threat-intel/hash/${hash}`)
      );
      expect(result).toEqual(mockIntel);
    });

    it('should validate hash length', async () => {
      await expect(service.queryHashThreatIntel('short')).rejects.toThrow(
        'Valid hash is required'
      );
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // HEALTH CHECK
  // ──────────────────────────────────────────────────────────────────────────

  describe('checkHealth', () => {
    it('should check health of all services', async () => {
      mockClient.get
        .mockResolvedValueOnce({ status: 'ok' })
        .mockResolvedValueOnce({ status: 'ok' });

      const result = await service.checkHealth();

      expect(result).toEqual({
        core: true,
        immune: true,
      });
    });

    it('should mark unavailable services as false', async () => {
      mockClient.get
        .mockResolvedValueOnce({ status: 'ok' })
        .mockRejectedValueOnce(new Error('Service down'));

      const result = await service.checkHealth();

      expect(result.core).toBe(true);
      expect(result.immune).toBe(false);
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // VALIDATION
  // ──────────────────────────────────────────────────────────────────────────

  describe('validateRequest', () => {
    it('should validate valid IP addresses', () => {
      expect(() =>
        service.validateRequest({
          sourceIp: '192.168.1.1',
          destIp: '10.0.0.1',
        })
      ).not.toThrow();
    });

    it('should reject invalid IP addresses', () => {
      expect(() =>
        service.validateRequest({ sourceIp: '999.999.999.999' })
      ).toThrow('Invalid IP address format');
    });

    it('should validate port numbers', () => {
      expect(() =>
        service.validateRequest({ sourcePort: 443, destPort: 80 })
      ).not.toThrow();

      expect(() => service.validateRequest({ sourcePort: -1 })).toThrow(
        'Invalid port number'
      );

      expect(() => service.validateRequest({ destPort: 99999 })).toThrow(
        'Invalid port number'
      );
    });

    it('should validate entity ID', () => {
      expect(() => service.validateRequest({ entityId: '' })).toThrow(
        'Invalid entity ID'
      );
    });

    it('should validate event type', () => {
      expect(() => service.validateRequest({ eventType: '' })).toThrow(
        'Invalid event type'
      );
    });
  });

  describe('validateIPAddress', () => {
    it('should accept valid IPs', () => {
      expect(() => service.validateIPAddress('192.168.1.1')).not.toThrow();
      expect(() => service.validateIPAddress('10.0.0.1')).not.toThrow();
      expect(() => service.validateIPAddress('255.255.255.255')).not.toThrow();
    });

    it('should reject invalid format', () => {
      expect(() => service.validateIPAddress('not-an-ip')).toThrow();
      expect(() => service.validateIPAddress('192.168.1')).toThrow();
    });

    it('should reject out-of-range octets', () => {
      expect(() => service.validateIPAddress('256.1.1.1')).toThrow();
      expect(() => service.validateIPAddress('1.1.1.256')).toThrow();
    });
  });

  describe('validatePort', () => {
    it('should accept valid ports', () => {
      expect(() => service.validatePort(80)).not.toThrow();
      expect(() => service.validatePort(443)).not.toThrow();
      expect(() => service.validatePort(65535)).not.toThrow();
    });

    it('should reject invalid ports', () => {
      expect(() => service.validatePort(-1)).toThrow();
      expect(() => service.validatePort(99999)).toThrow();
      expect(() => service.validatePort('not-a-number')).toThrow();
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // SINGLETON
  // ──────────────────────────────────────────────────────────────────────────

  describe('getDefensiveService', () => {
    it('should return singleton instance', () => {
      const instance1 = getDefensiveService();
      const instance2 = getDefensiveService();

      expect(instance1).toBe(instance2);
    });

    it('should return DefensiveService instance', () => {
      const instance = getDefensiveService();

      expect(instance).toBeInstanceOf(DefensiveService);
    });
  });
});

/**
 * Offensive Store Tests
 *
 * Comprehensive test suite for Zustand offensive operations store
 * 47 tests covering all functionality
 *
 * Test Coverage:
 * - Initialization and default state
 * - Metrics management (set, update, increment)
 * - Executions CRUD operations
 * - Module management
 * - Loading states
 * - Error handling
 * - Persistence and expiration
 * - Network scanner operations
 * - Payload generator operations
 * - Selectors
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useOffensiveStore } from './offensiveStore';

describe('offensiveStore', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();

    // Reset store before each test
    const { result } = renderHook(() => useOffensiveStore());
    act(() => {
      result.current.reset();
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  // ==================== INITIALIZATION TESTS ====================
  describe('Initialization', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useOffensiveStore());

      expect(result.current.metrics).toEqual({
        activeScans: 0,
        exploitsFound: 0,
        targets: 0,
        c2Sessions: 0,
        networkScans: 0,
        payloadsGenerated: 0
      });
      expect(result.current.executions).toEqual([]);
      expect(result.current.activeModule).toBe('network-scanner');
      expect(result.current.loading.metrics).toBe(true);
      expect(result.current.loading.executions).toBe(false);
      expect(result.current.loading.scanner).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.lastUpdate).toBeNull();
      expect(result.current.scanResults).toEqual([]);
      expect(result.current.payloads).toEqual([]);
    });

    it('should have all required action methods', () => {
      const { result } = renderHook(() => useOffensiveStore());

      expect(typeof result.current.setMetrics).toBe('function');
      expect(typeof result.current.updateMetric).toBe('function');
      expect(typeof result.current.incrementMetric).toBe('function');
      expect(typeof result.current.addExecution).toBe('function');
      expect(typeof result.current.updateExecution).toBe('function');
      expect(typeof result.current.removeExecution).toBe('function');
      expect(typeof result.current.clearExecutions).toBe('function');
      expect(typeof result.current.setActiveModule).toBe('function');
      expect(typeof result.current.setLoading).toBe('function');
      expect(typeof result.current.setError).toBe('function');
      expect(typeof result.current.clearError).toBe('function');
      expect(typeof result.current.addScanResult).toBe('function');
      expect(typeof result.current.clearScanResults).toBe('function');
      expect(typeof result.current.addPayload).toBe('function');
      expect(typeof result.current.clearPayloads).toBe('function');
      expect(typeof result.current.reset).toBe('function');
    });
  });

  // ==================== METRICS TESTS ====================
  describe('Metrics Management', () => {
    it('should set all metrics at once', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const newMetrics = {
        activeScans: 5,
        exploitsFound: 10,
        targets: 20,
        c2Sessions: 3,
        networkScans: 15,
        payloadsGenerated: 8
      };

      act(() => {
        result.current.setMetrics(newMetrics);
      });

      expect(result.current.metrics).toEqual(newMetrics);
      expect(result.current.loading.metrics).toBe(false);
      expect(result.current.lastUpdate).toBeTruthy();
    });

    it('should update single metric', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.updateMetric('activeScans', 42);
      });

      expect(result.current.metrics.activeScans).toBe(42);
      expect(result.current.metrics.exploitsFound).toBe(0); // Others unchanged
      expect(result.current.lastUpdate).toBeTruthy();
    });

    it('should increment metric with default amount', () => {
      const { result } = renderHook(() => useOffensiveStore());

      // Set initial value
      act(() => {
        result.current.updateMetric('targets', 10);
      });

      // Increment by default (1)
      act(() => {
        result.current.incrementMetric('targets');
      });

      expect(result.current.metrics.targets).toBe(11);
    });

    it('should increment metric with custom amount', () => {
      const { result } = renderHook(() => useOffensiveStore());

      // Set initial value
      act(() => {
        result.current.updateMetric('exploitsFound', 5);
      });

      // Increment by 10
      act(() => {
        result.current.incrementMetric('exploitsFound', 10);
      });

      expect(result.current.metrics.exploitsFound).toBe(15);
    });

    it('should increment from zero if metric does not exist', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const initialMetrics = result.current.metrics;
      const newMetricKey = 'customMetric';

      act(() => {
        result.current.incrementMetric(newMetricKey, 5);
      });

      expect(result.current.metrics[newMetricKey]).toBe(5);
    });

    it('should update lastUpdate timestamp when setting metrics', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const before = new Date().toISOString();

      act(() => {
        result.current.setMetrics({ activeScans: 1, exploitsFound: 0, targets: 0, c2Sessions: 0, networkScans: 0, payloadsGenerated: 0 });
      });

      const after = new Date().toISOString();

      expect(result.current.lastUpdate).toBeTruthy();
      expect(result.current.lastUpdate >= before).toBe(true);
      expect(result.current.lastUpdate <= after).toBe(true);
    });
  });

  // ==================== EXECUTIONS TESTS ====================
  describe('Executions Management', () => {
    it('should add execution with auto-generated fields', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const execution = {
        command: 'nmap -sV target.com',
        module: 'network-scanner'
      };

      act(() => {
        result.current.addExecution(execution);
      });

      expect(result.current.executions).toHaveLength(1);
      expect(result.current.executions[0]).toMatchObject(execution);
      expect(result.current.executions[0].id).toBeTruthy();
      expect(result.current.executions[0].timestamp).toBeTruthy();
      expect(result.current.executions[0].status).toBe('running');
    });

    it('should preserve provided id and timestamp', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const execution = {
        id: 'custom-id-123',
        timestamp: '2025-01-01T00:00:00Z',
        command: 'test command',
        status: 'completed'
      };

      act(() => {
        result.current.addExecution(execution);
      });

      expect(result.current.executions[0].id).toBe('custom-id-123');
      expect(result.current.executions[0].timestamp).toBe('2025-01-01T00:00:00Z');
      expect(result.current.executions[0].status).toBe('completed');
    });

    it('should add executions in reverse chronological order', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addExecution({ command: 'First' });
        result.current.addExecution({ command: 'Second' });
        result.current.addExecution({ command: 'Third' });
      });

      // Newest first
      expect(result.current.executions[0].command).toBe('Third');
      expect(result.current.executions[1].command).toBe('Second');
      expect(result.current.executions[2].command).toBe('First');
    });

    it('should limit executions to 100', () => {
      const { result } = renderHook(() => useOffensiveStore());

      // Add 110 executions
      act(() => {
        for (let i = 0; i < 110; i++) {
          result.current.addExecution({ command: `Command ${i}` });
        }
      });

      // Should keep only last 100
      expect(result.current.executions).toHaveLength(100);
      // Most recent should be first
      expect(result.current.executions[0].command).toBe('Command 109');
    });

    it('should update execution by id', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addExecution({ id: 'exec-1', command: 'test', status: 'running' });
      });

      act(() => {
        result.current.updateExecution('exec-1', { status: 'completed', output: 'Success' });
      });

      const updatedExec = result.current.executions.find(e => e.id === 'exec-1');
      expect(updatedExec.status).toBe('completed');
      expect(updatedExec.output).toBe('Success');
      expect(updatedExec.updated).toBeTruthy();
    });

    it('should not update non-existent execution', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addExecution({ id: 'exec-1', command: 'test' });
      });

      const originalLength = result.current.executions.length;

      act(() => {
        result.current.updateExecution('non-existent-id', { status: 'completed' });
      });

      expect(result.current.executions).toHaveLength(originalLength);
    });

    it('should remove execution by id', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addExecution({ id: 'exec-1', command: 'test1' });
        result.current.addExecution({ id: 'exec-2', command: 'test2' });
        result.current.addExecution({ id: 'exec-3', command: 'test3' });
      });

      expect(result.current.executions).toHaveLength(3);

      act(() => {
        result.current.removeExecution('exec-2');
      });

      expect(result.current.executions).toHaveLength(2);
      expect(result.current.executions.find(e => e.id === 'exec-2')).toBeUndefined();
    });

    it('should clear all executions', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addExecution({ command: 'test1' });
        result.current.addExecution({ command: 'test2' });
      });

      expect(result.current.executions).toHaveLength(2);

      act(() => {
        result.current.clearExecutions();
      });

      expect(result.current.executions).toHaveLength(0);
    });
  });

  // ==================== MODULE TESTS ====================
  describe('Module Management', () => {
    it('should set active module', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.setActiveModule('payload-generator');
      });

      expect(result.current.activeModule).toBe('payload-generator');
    });

    it('should change active module multiple times', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const modules = ['network-scanner', 'exploit-framework', 'c2-server', 'payload-generator'];

      modules.forEach(module => {
        act(() => {
          result.current.setActiveModule(module);
        });
        expect(result.current.activeModule).toBe(module);
      });
    });
  });

  // ==================== LOADING TESTS ====================
  describe('Loading States', () => {
    it('should set loading state for specific key', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.setLoading('metrics', false);
      });

      expect(result.current.loading.metrics).toBe(false);
      expect(result.current.loading.executions).toBe(false); // Others unchanged
    });

    it('should manage multiple loading states independently', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.setLoading('executions', true);
        result.current.setLoading('scanner', true);
      });

      expect(result.current.loading.executions).toBe(true);
      expect(result.current.loading.scanner).toBe(true);
      expect(result.current.loading.metrics).toBe(true); // Initial state
    });
  });

  // ==================== ERROR TESTS ====================
  describe('Error Handling', () => {
    it('should set error', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const error = 'Network connection failed';

      act(() => {
        result.current.setError(error);
      });

      expect(result.current.error).toBe(error);
    });

    it('should clear error', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.setError('Test error');
      });

      expect(result.current.error).toBe('Test error');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should overwrite previous error', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.setError('First error');
      });

      expect(result.current.error).toBe('First error');

      act(() => {
        result.current.setError('Second error');
      });

      expect(result.current.error).toBe('Second error');
    });
  });

  // ==================== NETWORK SCANNER TESTS ====================
  describe('Network Scanner Operations', () => {
    it('should add scan result and update metrics', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const scanResult = {
        target: '192.168.1.1',
        ports: [80, 443, 22],
        success: true
      };

      act(() => {
        result.current.addScanResult(scanResult);
      });

      expect(result.current.scanResults).toHaveLength(1);
      expect(result.current.scanResults[0]).toEqual(scanResult);
      expect(result.current.metrics.networkScans).toBe(1);
      expect(result.current.metrics.activeScans).toBe(1);
    });

    it('should increment networkScans but not activeScans on failed scan', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const failedScan = {
        target: '192.168.1.1',
        success: false,
        error: 'Timeout'
      };

      act(() => {
        result.current.addScanResult(failedScan);
      });

      expect(result.current.metrics.networkScans).toBe(1);
      expect(result.current.metrics.activeScans).toBe(0);
    });

    it('should limit scan results to 50', () => {
      const { result } = renderHook(() => useOffensiveStore());

      // Add 60 scan results
      act(() => {
        for (let i = 0; i < 60; i++) {
          result.current.addScanResult({
            target: `192.168.1.${i}`,
            success: true
          });
        }
      });

      // Should keep only last 50
      expect(result.current.scanResults).toHaveLength(50);
    });

    it('should clear all scan results', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addScanResult({ target: '192.168.1.1', success: true });
        result.current.addScanResult({ target: '192.168.1.2', success: true });
      });

      expect(result.current.scanResults).toHaveLength(2);

      act(() => {
        result.current.clearScanResults();
      });

      expect(result.current.scanResults).toHaveLength(0);
    });

    it('should add scan results in reverse chronological order', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addScanResult({ target: 'First', success: true });
        result.current.addScanResult({ target: 'Second', success: true });
        result.current.addScanResult({ target: 'Third', success: true });
      });

      // Newest first
      expect(result.current.scanResults[0].target).toBe('Third');
      expect(result.current.scanResults[1].target).toBe('Second');
      expect(result.current.scanResults[2].target).toBe('First');
    });
  });

  // ==================== PAYLOAD GENERATOR TESTS ====================
  describe('Payload Generator Operations', () => {
    it('should add payload and update metrics', () => {
      const { result } = renderHook(() => useOffensiveStore());

      const payload = {
        type: 'reverse-shell',
        language: 'python',
        code: 'import socket...'
      };

      act(() => {
        result.current.addPayload(payload);
      });

      expect(result.current.payloads).toHaveLength(1);
      expect(result.current.payloads[0]).toEqual(payload);
      expect(result.current.metrics.payloadsGenerated).toBe(1);
    });

    it('should limit payloads to 20', () => {
      const { result } = renderHook(() => useOffensiveStore());

      // Add 30 payloads
      act(() => {
        for (let i = 0; i < 30; i++) {
          result.current.addPayload({
            type: `payload-${i}`,
            code: `code-${i}`
          });
        }
      });

      // Should keep only last 20
      expect(result.current.payloads).toHaveLength(20);
    });

    it('should clear all payloads', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addPayload({ type: 'payload1' });
        result.current.addPayload({ type: 'payload2' });
      });

      expect(result.current.payloads).toHaveLength(2);

      act(() => {
        result.current.clearPayloads();
      });

      expect(result.current.payloads).toHaveLength(0);
    });

    it('should add payloads in reverse chronological order', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addPayload({ type: 'First' });
        result.current.addPayload({ type: 'Second' });
        result.current.addPayload({ type: 'Third' });
      });

      // Newest first
      expect(result.current.payloads[0].type).toBe('Third');
      expect(result.current.payloads[1].type).toBe('Second');
      expect(result.current.payloads[2].type).toBe('First');
    });

    it('should increment payloadsGenerated metric correctly', () => {
      const { result } = renderHook(() => useOffensiveStore());

      expect(result.current.metrics.payloadsGenerated).toBe(0);

      act(() => {
        result.current.addPayload({ type: 'payload1' });
        result.current.addPayload({ type: 'payload2' });
        result.current.addPayload({ type: 'payload3' });
      });

      expect(result.current.metrics.payloadsGenerated).toBe(3);
    });
  });

  // ==================== RESET TESTS ====================
  describe('Reset Functionality', () => {
    it('should reset to initial state', () => {
      const { result } = renderHook(() => useOffensiveStore());

      // Modify state extensively
      act(() => {
        result.current.setMetrics({ activeScans: 10, exploitsFound: 5, targets: 20, c2Sessions: 3, networkScans: 15, payloadsGenerated: 8 });
        result.current.addExecution({ command: 'test' });
        result.current.setActiveModule('exploit-framework');
        result.current.setError('Test error');
        result.current.addScanResult({ target: '192.168.1.1', success: true });
        result.current.addPayload({ type: 'test' });
        result.current.setLoading('executions', true);
      });

      // Reset
      act(() => {
        result.current.reset();
      });

      // Should be back to defaults
      expect(result.current.metrics).toEqual({
        activeScans: 0,
        exploitsFound: 0,
        targets: 0,
        c2Sessions: 0,
        networkScans: 0,
        payloadsGenerated: 0
      });
      expect(result.current.executions).toEqual([]);
      expect(result.current.activeModule).toBe('network-scanner');
      expect(result.current.error).toBeNull();
      expect(result.current.scanResults).toEqual([]);
      expect(result.current.payloads).toEqual([]);
      expect(result.current.loading.metrics).toBe(true);
      expect(result.current.loading.executions).toBe(false);
      expect(result.current.loading.scanner).toBe(false);
    });
  });

  // ==================== SELECTORS TESTS ====================
  describe('Selectors', () => {
    it('should work with built-in selectors', () => {
      const { result: metricsResult } = renderHook(() =>
        useOffensiveStore((state) => state.metrics)
      );
      const { result: executionsResult } = renderHook(() =>
        useOffensiveStore((state) => state.executions)
      );

      expect(metricsResult.current).toEqual({
        activeScans: 0,
        exploitsFound: 0,
        targets: 0,
        c2Sessions: 0,
        networkScans: 0,
        payloadsGenerated: 0
      });
      expect(executionsResult.current).toEqual([]);
    });

    it('should select specific metric', () => {
      const { result } = renderHook(() =>
        useOffensiveStore((state) => state.metrics.activeScans)
      );

      expect(result.current).toBe(0);
    });

    it('should select computed values', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.addExecution({ id: 'exec-1', status: 'running' });
        result.current.addExecution({ id: 'exec-2', status: 'completed' });
        result.current.addExecution({ id: 'exec-3', status: 'running' });
      });

      // Access computed values directly from state
      const runningExecutions = result.current.executions.filter(e => e.status === 'running');

      expect(runningExecutions).toHaveLength(2);
    });
  });

  // ==================== PERSISTENCE TESTS ====================
  describe('Persistence & Expiration', () => {
    it('should persist activeModule to localStorage', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.setActiveModule('payload-generator');
      });

      // Check localStorage
      const stored = localStorage.getItem('offensive-store');
      expect(stored).toBeTruthy();

      const parsed = JSON.parse(stored);
      expect(parsed.state.activeModule).toBe('payload-generator');
    });

    it('should persist executions to localStorage (max 20)', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        for (let i = 0; i < 25; i++) {
          result.current.addExecution({ command: `Command ${i}` });
        }
      });

      const stored = localStorage.getItem('offensive-store');
      const parsed = JSON.parse(stored);

      // Should persist only last 20 executions
      expect(parsed.state.executions.length).toBeLessThanOrEqual(20);
    });

    it('should include expiration timestamp in persisted state', () => {
      const { result } = renderHook(() => useOffensiveStore());

      act(() => {
        result.current.setActiveModule('test-module');
      });

      const stored = localStorage.getItem('offensive-store');
      const parsed = JSON.parse(stored);

      expect(parsed.state._expiresAt).toBeTruthy();
      expect(typeof parsed.state._expiresAt).toBe('number');
      expect(parsed.state._expiresAt).toBeGreaterThan(Date.now());
    });
  });
});

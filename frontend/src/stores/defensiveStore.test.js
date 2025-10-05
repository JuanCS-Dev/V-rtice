/**
 * Defensive Store Tests
 *
 * Tests for Zustand defensive operations store
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDefensiveStore } from './defensiveStore';

describe('defensiveStore', () => {
  beforeEach(() => {
    // Reset store before each test
    const { result } = renderHook(() => useDefensiveStore());
    act(() => {
      result.current.reset();
    });
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useDefensiveStore());

    expect(result.current.metrics).toEqual({
      threats: 0,
      suspiciousIPs: 0,
      domains: 0,
      monitored: 0
    });
    expect(result.current.alerts).toEqual([]);
    expect(result.current.activeModule).toBe('threat-map');
    expect(result.current.loading.metrics).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should update metrics', () => {
    const { result } = renderHook(() => useDefensiveStore());

    const newMetrics = {
      threats: 10,
      suspiciousIPs: 5,
      domains: 3,
      monitored: 100
    };

    act(() => {
      result.current.setMetrics(newMetrics);
    });

    expect(result.current.metrics).toEqual(newMetrics);
    expect(result.current.loading.metrics).toBe(false);
    expect(result.current.lastUpdate).toBeTruthy();
  });

  it('should update single metric', () => {
    const { result } = renderHook(() => useDefensiveStore());

    act(() => {
      result.current.updateMetric('threats', 42);
    });

    expect(result.current.metrics.threats).toBe(42);
    expect(result.current.metrics.suspiciousIPs).toBe(0); // Others unchanged
  });

  it('should add alert', () => {
    const { result } = renderHook(() => useDefensiveStore());

    const alert = {
      type: 'THREAT_DETECTED',
      message: 'Suspicious activity detected',
      severity: 'high'
    };

    act(() => {
      result.current.addAlert(alert);
    });

    expect(result.current.alerts).toHaveLength(1);
    expect(result.current.alerts[0]).toMatchObject(alert);
    expect(result.current.alerts[0].id).toBeTruthy();
    expect(result.current.alerts[0].timestamp).toBeTruthy();
  });

  it('should limit alerts to 50', () => {
    const { result } = renderHook(() => useDefensiveStore());

    // Add 60 alerts
    act(() => {
      for (let i = 0; i < 60; i++) {
        result.current.addAlert({
          type: 'TEST',
          message: `Alert ${i}`,
          severity: 'info'
        });
      }
    });

    // Should keep only last 50
    expect(result.current.alerts).toHaveLength(50);
  });

  it('should add alerts in reverse chronological order', () => {
    const { result } = renderHook(() => useDefensiveStore());

    act(() => {
      result.current.addAlert({ message: 'First' });
      result.current.addAlert({ message: 'Second' });
      result.current.addAlert({ message: 'Third' });
    });

    // Newest first
    expect(result.current.alerts[0].message).toBe('Third');
    expect(result.current.alerts[1].message).toBe('Second');
    expect(result.current.alerts[2].message).toBe('First');
  });

  it('should clear all alerts', () => {
    const { result } = renderHook(() => useDefensiveStore());

    act(() => {
      result.current.addAlert({ message: 'Test 1' });
      result.current.addAlert({ message: 'Test 2' });
    });

    expect(result.current.alerts).toHaveLength(2);

    act(() => {
      result.current.clearAlerts();
    });

    expect(result.current.alerts).toHaveLength(0);
  });

  it('should remove specific alert', () => {
    const { result } = renderHook(() => useDefensiveStore());

    act(() => {
      result.current.addAlert({ message: 'Alert 1' });
      result.current.addAlert({ message: 'Alert 2' });
      result.current.addAlert({ message: 'Alert 3' });
    });

    const alertToRemove = result.current.alerts[1].id;

    act(() => {
      result.current.removeAlert(alertToRemove);
    });

    expect(result.current.alerts).toHaveLength(2);
    expect(result.current.alerts.find(a => a.id === alertToRemove)).toBeUndefined();
  });

  it('should set active module', () => {
    const { result } = renderHook(() => useDefensiveStore());

    act(() => {
      result.current.setActiveModule('network-monitor');
    });

    expect(result.current.activeModule).toBe('network-monitor');
  });

  it('should set loading state', () => {
    const { result } = renderHook(() => useDefensiveStore());

    act(() => {
      result.current.setLoading('metrics', false);
    });

    expect(result.current.loading.metrics).toBe(false);

    act(() => {
      result.current.setLoading('alerts', true);
    });

    expect(result.current.loading.alerts).toBe(true);
    expect(result.current.loading.metrics).toBe(false); // Other unchanged
  });

  it('should set error', () => {
    const { result } = renderHook(() => useDefensiveStore());

    const error = 'Network error occurred';

    act(() => {
      result.current.setError(error);
    });

    expect(result.current.error).toBe(error);
  });

  it('should clear error', () => {
    const { result } = renderHook(() => useDefensiveStore());

    act(() => {
      result.current.setError('Test error');
    });

    expect(result.current.error).toBe('Test error');

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('should reset to initial state', () => {
    const { result } = renderHook(() => useDefensiveStore());

    // Modify state
    act(() => {
      result.current.setMetrics({ threats: 10, suspiciousIPs: 5, domains: 3, monitored: 100 });
      result.current.addAlert({ message: 'Test' });
      result.current.setActiveModule('malware-analysis');
      result.current.setError('Test error');
    });

    // Reset
    act(() => {
      result.current.reset();
    });

    // Should be back to defaults
    expect(result.current.metrics).toEqual({
      threats: 0,
      suspiciousIPs: 0,
      domains: 0,
      monitored: 0
    });
    expect(result.current.alerts).toEqual([]);
    expect(result.current.activeModule).toBe('threat-map');
    expect(result.current.error).toBeNull();
  });

  it('should update lastUpdate timestamp when setting metrics', () => {
    const { result } = renderHook(() => useDefensiveStore());

    const before = new Date().toISOString();

    act(() => {
      result.current.setMetrics({ threats: 10, suspiciousIPs: 5, domains: 3, monitored: 100 });
    });

    const after = new Date().toISOString();

    expect(result.current.lastUpdate).toBeTruthy();
    expect(result.current.lastUpdate >= before).toBe(true);
    expect(result.current.lastUpdate <= after).toBe(true);
  });

  it('should work with selectors', () => {
    const { result: metricsResult } = renderHook(() =>
      useDefensiveStore((state) => state.metrics)
    );
    const { result: alertsResult } = renderHook(() =>
      useDefensiveStore((state) => state.alerts)
    );

    expect(metricsResult.current).toEqual({
      threats: 0,
      suspiciousIPs: 0,
      domains: 0,
      monitored: 0
    });
    expect(alertsResult.current).toEqual([]);
  });
});

/**
 * useLocalStorage Hook Tests
 * ===========================
 *
 * Tests for localStorage hook with:
 * - State persistence
 * - JSON serialization
 * - Default values
 * - Error handling
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from '../useLocalStorage';

describe('useLocalStorage Hook', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    global.localStorage.clear();
    vi.clearAllMocks();
  });

  it('should initialize with default value when localStorage is empty', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    expect(result.current[0]).toBe('default');
  });

  it('should initialize with value from localStorage', () => {
    localStorage.setItem('test-key', JSON.stringify('stored-value'));

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    expect(result.current[0]).toBe('stored-value');
  });

  it('should update localStorage when value changes', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'initial'));

    act(() => {
      result.current[1]('updated');
    });

    expect(result.current[0]).toBe('updated');
    expect(localStorage.getItem('test-key')).toBe(JSON.stringify('updated'));
  });

  it('should handle objects', () => {
    const { result } = renderHook(() =>
      useLocalStorage('obj-key', { count: 0 })
    );

    act(() => {
      result.current[1]({ count: 5, name: 'test' });
    });

    expect(result.current[0]).toEqual({ count: 5, name: 'test' });
    expect(JSON.parse(localStorage.getItem('obj-key'))).toEqual({
      count: 5,
      name: 'test',
    });
  });

  it('should handle arrays', () => {
    const { result } = renderHook(() => useLocalStorage('arr-key', []));

    act(() => {
      result.current[1]([1, 2, 3]);
    });

    expect(result.current[0]).toEqual([1, 2, 3]);
    expect(JSON.parse(localStorage.getItem('arr-key'))).toEqual([1, 2, 3]);
  });

  it('should handle function updates', () => {
    const { result } = renderHook(() => useLocalStorage('counter', 0));

    act(() => {
      result.current[1]((prev) => prev + 1);
    });

    expect(result.current[0]).toBe(1);

    act(() => {
      result.current[1]((prev) => prev + 1);
    });

    expect(result.current[0]).toBe(2);
  });

  it('should remove item when set to undefined', () => {
    localStorage.setItem('test-key', JSON.stringify('value'));

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    act(() => {
      result.current[1](undefined);
    });

    expect(localStorage.getItem('test-key')).toBeNull();
    expect(result.current[0]).toBe('default');
  });

  it('should handle invalid JSON gracefully', () => {
    localStorage.setItem('bad-key', 'invalid-json{');

    const { result } = renderHook(() => useLocalStorage('bad-key', 'fallback'));

    expect(result.current[0]).toBe('fallback');
  });

  it('should sync across multiple instances', () => {
    const { result: result1 } = renderHook(() =>
      useLocalStorage('shared-key', 'initial')
    );

    const { result: result2 } = renderHook(() =>
      useLocalStorage('shared-key', 'initial')
    );

    act(() => {
      result1.current[1]('updated');
    });

    // Both should reflect the change
    expect(result1.current[0]).toBe('updated');
    expect(result2.current[0]).toBe('updated');
  });

  it('should handle boolean values', () => {
    const { result } = renderHook(() => useLocalStorage('bool-key', false));

    act(() => {
      result.current[1](true);
    });

    expect(result.current[0]).toBe(true);
    expect(JSON.parse(localStorage.getItem('bool-key'))).toBe(true);
  });

  it('should handle null values', () => {
    const { result } = renderHook(() => useLocalStorage('null-key', null));

    expect(result.current[0]).toBeNull();

    act(() => {
      result.current[1]('not-null');
    });

    expect(result.current[0]).toBe('not-null');
  });
});

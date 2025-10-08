/**
 * useDebounce Hook Tests
 * ======================
 *
 * Tests for debouncing hook
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from '../useDebounce';

describe('useDebounce Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500));

    expect(result.current).toBe('initial');
  });

  it('should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'first', delay: 500 } }
    );

    expect(result.current).toBe('first');

    // Change value
    rerender({ value: 'second', delay: 500 });

    // Value should not change immediately
    expect(result.current).toBe('first');

    // Advance time by 499ms (not enough)
    act(() => {
      vi.advanceTimersByTime(499);
    });
    expect(result.current).toBe('first');

    // Advance time by 1ms more (total 500ms)
    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current).toBe('second');
  });

  it('should reset timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'first' } }
    );

    // Rapid changes
    rerender({ value: 'second' });
    act(() => vi.advanceTimersByTime(300));

    rerender({ value: 'third' });
    act(() => vi.advanceTimersByTime(300));

    rerender({ value: 'fourth' });
    act(() => vi.advanceTimersByTime(300));

    // Still showing first value
    expect(result.current).toBe('first');

    // Wait full delay after last change
    act(() => vi.advanceTimersByTime(200));

    expect(result.current).toBe('fourth');
  });

  it('should handle different delay values', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'test', delay: 1000 } }
    );

    rerender({ value: 'changed', delay: 1000 });

    act(() => vi.advanceTimersByTime(999));
    expect(result.current).toBe('test');

    act(() => vi.advanceTimersByTime(1));
    expect(result.current).toBe('changed');
  });

  it('should handle object values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: { count: 0 } } }
    );

    expect(result.current).toEqual({ count: 0 });

    rerender({ value: { count: 1 } });

    act(() => vi.advanceTimersByTime(300));

    expect(result.current).toEqual({ count: 1 });
  });

  it('should cleanup timeout on unmount', () => {
    const { unmount, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'first' } }
    );

    rerender({ value: 'second' });

    // Unmount before timeout
    unmount();

    // No error should occur
    act(() => vi.advanceTimersByTime(500));
  });

  it('should handle zero delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 0),
      { initialProps: { value: 'first' } }
    );

    rerender({ value: 'second' });

    act(() => vi.advanceTimersByTime(0));

    expect(result.current).toBe('second');
  });
});

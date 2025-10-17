/**
 * useTheme Hook Tests
 * ===================
 *
 * Tests for theme management hook
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from '../useTheme';

describe('useTheme Hook', () => {
  beforeEach(() => {
    global.localStorage.clear();
    vi.clearAllMocks();
    // Reset document attributes
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.removeAttribute('data-mode');
  });

  it('should initialize with default theme', () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('default');
    expect(result.current.availableThemes).toHaveLength(7);
  });

  it('should initialize with theme from localStorage', () => {
    localStorage.setItem('vertice-theme', 'cyber-blue');

    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('cyber-blue');
  });

  it('should cycle through themes', () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('default');

    act(() => {
      result.current.cycleTheme();
    });

    expect(result.current.theme).toBe('cyber-blue');

    act(() => {
      result.current.cycleTheme();
    });

    expect(result.current.theme).toBe('purple-haze');
  });

  it('should set specific theme', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.setTheme('windows11');
    });

    expect(result.current.theme).toBe('windows11');

    act(() => {
      result.current.setTheme('red-alert');
    });

    expect(result.current.theme).toBe('red-alert');
  });

  it('should persist theme to localStorage', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.setTheme('amber-alert');
    });

    expect(localStorage.getItem('vertice-theme')).toBe('amber-alert');
  });

  it('should apply theme attribute to document', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.setTheme('stealth-mode');
    });

    expect(document.documentElement.getAttribute('data-theme')).toBe('stealth-mode');

    act(() => {
      result.current.setTheme('purple-haze');
    });

    expect(document.documentElement.getAttribute('data-theme')).toBe('purple-haze');
  });

  it('should return current theme info', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.setTheme('cyber-blue');
    });

    expect(result.current.currentThemeInfo.id).toBe('cyber-blue');
    expect(result.current.currentThemeInfo.name).toBe('Cyber Blue');
    expect(result.current.currentThemeInfo.preview).toBeDefined();
  });

  it('should not set invalid theme', () => {
    const { result } = renderHook(() => useTheme());

    const initialTheme = result.current.theme;

    act(() => {
      result.current.setTheme('invalid-theme');
    });

    // Theme should not change
    expect(result.current.theme).toBe(initialTheme);
  });

  it('should handle mode for windows11 theme', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.setTheme('windows11');
      result.current.setMode('dark');
    });

    expect(result.current.mode).toBe('dark');
    expect(document.documentElement.getAttribute('data-mode')).toBe('dark');
  });

  it('should toggle mode', () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.mode).toBe('light');

    act(() => {
      result.current.toggleMode();
    });

    expect(result.current.mode).toBe('dark');

    act(() => {
      result.current.toggleMode();
    });

    expect(result.current.mode).toBe('light');
  });
});

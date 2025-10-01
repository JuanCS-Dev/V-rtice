/**
 * useTheme Hook - Gerenciamento de temas
 * ======================================
 *
 * Hook para gerenciar tema da aplicação (cyberpunk, windows11, etc)
 */

import { useState, useEffect, useCallback } from 'react';

const THEME_KEY = 'vertice-theme';
const MODE_KEY = 'vertice-theme-mode';

const AVAILABLE_THEMES = [
  {
    id: 'cyberpunk',
    name: 'Cyberpunk',
    description: 'Visual moderno com neon e high-tech',
    preview: {
      primary: '#00d9ff',
      secondary: '#ff00aa',
      background: '#0a0e1a'
    }
  },
  {
    id: 'windows11',
    name: 'Windows 11',
    description: 'Clean, sóbrio e profissional',
    preview: {
      primary: '#0078d4',
      secondary: '#8764b8',
      background: '#f3f3f3'
    }
  }
];

export const useTheme = () => {
  // Estado do tema atual
  const [theme, setThemeState] = useState(() => {
    if (typeof window === 'undefined') return 'cyberpunk';
    return localStorage.getItem(THEME_KEY) || 'cyberpunk';
  });

  // Estado do modo (light/dark) - apenas para windows11
  const [mode, setModeState] = useState(() => {
    if (typeof window === 'undefined') return 'light';
    return localStorage.getItem(MODE_KEY) || 'light';
  });

  /**
   * Aplica tema no DOM
   */
  const applyTheme = useCallback((newTheme, newMode) => {
    if (typeof document === 'undefined') return;

    const root = document.documentElement;

    // Set theme
    root.setAttribute('data-theme', newTheme);

    // Set mode (only for themes that support it)
    if (newTheme === 'windows11') {
      root.setAttribute('data-mode', newMode);
    } else {
      root.removeAttribute('data-mode');
    }

    // Salva no localStorage
    localStorage.setItem(THEME_KEY, newTheme);
    localStorage.setItem(MODE_KEY, newMode);

    console.log(`[Theme] Applied: ${newTheme}${newTheme === 'windows11' ? ` (${newMode})` : ''}`);
  }, []);

  /**
   * Muda tema
   */
  const setTheme = useCallback((newTheme) => {
    if (!AVAILABLE_THEMES.find(t => t.id === newTheme)) {
      console.warn(`[Theme] Invalid theme: ${newTheme}`);
      return;
    }

    setThemeState(newTheme);
    applyTheme(newTheme, mode);
  }, [mode, applyTheme]);

  /**
   * Muda modo (light/dark)
   */
  const setMode = useCallback((newMode) => {
    if (newMode !== 'light' && newMode !== 'dark') {
      console.warn(`[Theme] Invalid mode: ${newMode}`);
      return;
    }

    setModeState(newMode);
    applyTheme(theme, newMode);
  }, [theme, applyTheme]);

  /**
   * Toggle entre light/dark (apenas windows11)
   */
  const toggleMode = useCallback(() => {
    if (theme !== 'windows11') {
      console.warn('[Theme] Mode toggle only available for windows11 theme');
      return;
    }

    const newMode = mode === 'light' ? 'dark' : 'light';
    setMode(newMode);
  }, [theme, mode, setMode]);

  /**
   * Cicla entre temas
   */
  const cycleTheme = useCallback(() => {
    const currentIndex = AVAILABLE_THEMES.findIndex(t => t.id === theme);
    const nextIndex = (currentIndex + 1) % AVAILABLE_THEMES.length;
    setTheme(AVAILABLE_THEMES[nextIndex].id);
  }, [theme, setTheme]);

  /**
   * Get tema info
   */
  const getCurrentThemeInfo = useCallback(() => {
    return AVAILABLE_THEMES.find(t => t.id === theme) || AVAILABLE_THEMES[0];
  }, [theme]);

  // Aplica tema inicial no mount
  useEffect(() => {
    applyTheme(theme, mode);
  }, []); // Empty deps - só roda uma vez no mount

  return {
    theme,
    mode,
    setTheme,
    setMode,
    toggleMode,
    cycleTheme,
    availableThemes: AVAILABLE_THEMES,
    currentThemeInfo: getCurrentThemeInfo(),
    supportsMode: theme === 'windows11'
  };
};

export default useTheme;

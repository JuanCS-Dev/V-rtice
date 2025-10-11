/**
import logger from '@/utils/logger';
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
    id: 'default',
    name: 'Matrix Green',
    description: 'Tema clássico inspirado em Matrix',
    preview: {
      primary: '#00ff41',
      secondary: '#00cc33',
      background: '#000000'
    }
  },
  {
    id: 'cyber-blue',
    name: 'Cyber Blue',
    description: 'Azul cibernético futurista',
    preview: {
      primary: '#00d4ff',
      secondary: '#00a8cc',
      background: '#000511'
    }
  },
  {
    id: 'purple-haze',
    name: 'Purple Haze',
    description: 'Roxo neon vibrante',
    preview: {
      primary: '#c77dff',
      secondary: '#9d4edd',
      background: '#10002b'
    }
  },
  {
    id: 'amber-alert',
    name: 'Amber Alert',
    description: 'Âmbar de alerta operacional',
    preview: {
      primary: '#ffb703',
      secondary: '#fb8500',
      background: '#1a0f00'
    }
  },
  {
    id: 'red-alert',
    name: 'Red Alert',
    description: 'Vermelho de alerta crítico',
    preview: {
      primary: '#ff0a54',
      secondary: '#cc0844',
      background: '#1a0000'
    }
  },
  {
    id: 'stealth-mode',
    name: 'Stealth Mode',
    description: 'Modo furtivo discreto',
    preview: {
      primary: '#8b8b8b',
      secondary: '#5a5a5a',
      background: '#0a0a0a'
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
    if (typeof window === 'undefined') return 'default';
    return localStorage.getItem(THEME_KEY) || 'default';
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

    logger.debug(`[Theme] Applied: ${newTheme}${newTheme === 'windows11' ? ` (${newMode})` : ''}`);
  }, []);

  /**
   * Muda tema
   */
  const setTheme = useCallback((newTheme) => {
    if (!AVAILABLE_THEMES.find(t => t.id === newTheme)) {
      logger.warn(`[Theme] Invalid theme: ${newTheme}`);
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
      logger.warn(`[Theme] Invalid mode: ${newMode}`);
      return;
    }

    setModeState(newMode);
    applyTheme(theme, newMode);
  }, [theme, applyTheme]);

  /**
   * Toggle entre light/dark (não usado nos novos temas)
   */
  const toggleMode = useCallback(() => {
    const newMode = mode === 'light' ? 'dark' : 'light';
    setMode(newMode);
  }, [mode, setMode]);

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
    supportsMode: false // Removido suporte a modo claro/escuro
  };
};

export default useTheme;

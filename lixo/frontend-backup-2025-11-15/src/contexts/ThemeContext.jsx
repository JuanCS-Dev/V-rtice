/* eslint-disable react-refresh/only-export-components */
// frontend/src/contexts/ThemeContext.jsx
/**
 * SECURITY (Boris Cherny Standard):
 * - GAP #3 FIXED: Context value memoized to prevent unnecessary re-renders
 */
import React, { createContext, useContext, useMemo } from 'react';

const ThemeContext = createContext(undefined);

/**
 * ThemeProvider - Mantém compatibilidade mas não faz nada
 *
 * Tema único fixo: Preto + Vermelho
 */
export const ThemeProvider = ({ children }) => {
  // GAP #3 FIX: Memoize value to prevent 100+ components re-rendering
  const value = useMemo(() => ({
    currentTheme: 'core',
    availableThemes: [],
    categories: {},
    changeTheme: () => {}, // No-op
    getThemeData: () => ({ id: 'core', name: 'Core Theme' }),
    getThemesByCategory: () => ({})
  }), []); // Empty deps - value never changes

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * Hook para acessar contexto de temas (compatibilidade)
 */
export const useTheme = () => {
  const context = useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useTheme deve ser usado dentro de ThemeProvider');
  }

  return context;
};

/* eslint-disable react-refresh/only-export-components */
// frontend/src/contexts/ThemeContext.jsx
import React, { createContext, useContext } from 'react';

const ThemeContext = createContext(undefined);

/**
 * ThemeProvider - Mantém compatibilidade mas não faz nada
 *
 * Tema único fixo: Preto + Vermelho
 */
export const ThemeProvider = ({ children }) => {
  // Tema fixo - não há mais troca de temas
  const value = {
    currentTheme: 'core',
    availableThemes: [],
    categories: {},
    changeTheme: () => {}, // No-op
    getThemeData: () => ({ id: 'core', name: 'Core Theme' }),
    getThemesByCategory: () => ({})
  };

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

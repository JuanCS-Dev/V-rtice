/* eslint-disable react-refresh/only-export-components */
// frontend/src/contexts/ThemeContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { themes, applyTheme, getCurrentTheme } from '../themes';

const ThemeContext = createContext(undefined);

/**
 * ThemeProvider - Gerencia estado global de temas
 * 
 * Permite troca de temas em tempo real mantendo persistência via localStorage.
 * Fornece lista completa de temas disponíveis e tema atual.
 */
export const ThemeProvider = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState(getCurrentTheme());
  const [availableThemes] = useState(themes);

  // Aplica tema inicial na montagem
  useEffect(() => {
    applyTheme(currentTheme);
  }, [currentTheme]);

  /**
   * Troca o tema ativo
   * @param {string} themeId - ID do tema a ser aplicado
   */
  const changeTheme = (themeId) => {
    if (themes.find(t => t.id === themeId)) {
      applyTheme(themeId);
      setCurrentTheme(themeId);
    } else {
      console.warn(`[ThemeContext] Tema inválido: ${themeId}`);
    }
  };

  /**
   * Obtém metadados do tema atual
   * @returns {Object} Objeto com dados do tema
   */
  const getThemeData = () => {
    return themes.find(t => t.id === currentTheme) || themes[0];
  };

  const value = {
    currentTheme,
    availableThemes,
    changeTheme,
    getThemeData
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * Hook para acessar contexto de temas
 * @returns {Object} Contexto de temas
 * @throws {Error} Se usado fora do ThemeProvider
 */
export const useTheme = () => {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    throw new Error('useTheme deve ser usado dentro de ThemeProvider');
  }
  
  return context;
};

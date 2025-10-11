// frontend/src/components/ThemeSelector/ThemeSelector.jsx
import React, { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import './ThemeSelector.css';

/**
 * ThemeSelector - Componente para troca de temas
 * 
 * Interface elegante tipo dropdown que permite usuário escolher entre
 * todos os temas disponíveis. Visual adaptável ao tema atual.
 */
const ThemeSelector = ({ position = 'top-right' }) => {
  const { currentTheme, availableThemes, changeTheme, getThemeData } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const currentThemeData = getThemeData();

  const handleThemeChange = (themeId) => {
    changeTheme(themeId);
    setIsOpen(false);
  };

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className={`theme-selector theme-selector--${position}`}>
      <button
        className="theme-selector__trigger"
        onClick={toggleDropdown}
        aria-label="Selecionar tema"
        aria-expanded={isOpen}
        title="Trocar tema"
      >
        <span className="theme-selector__icon">{currentThemeData.icon}</span>
        <span className="theme-selector__label">{currentThemeData.name}</span>
        <svg 
          className={`theme-selector__arrow ${isOpen ? 'theme-selector__arrow--open' : ''}`}
          width="12" 
          height="12" 
          viewBox="0 0 12 12"
        >
          <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="2" fill="none"/>
        </svg>
      </button>

      {isOpen && (
        <>
          <div 
            className="theme-selector__backdrop" 
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          <div className="theme-selector__dropdown">
            <div className="theme-selector__header">
              <span className="theme-selector__title">Temas Disponíveis</span>
            </div>
            <div className="theme-selector__list">
              {availableThemes.map((theme) => (
                <button
                  key={theme.id}
                  className={`theme-selector__option ${
                    theme.id === currentTheme ? 'theme-selector__option--active' : ''
                  }`}
                  onClick={() => handleThemeChange(theme.id)}
                  aria-current={theme.id === currentTheme}
                >
                  <span className="theme-selector__option-icon">{theme.icon}</span>
                  <div className="theme-selector__option-content">
                    <span className="theme-selector__option-name">{theme.name}</span>
                    <span className="theme-selector__option-description">{theme.description}</span>
                  </div>
                  <div 
                    className="theme-selector__option-preview" 
                    style={{ backgroundColor: theme.primary }}
                    aria-hidden="true"
                  />
                  {theme.id === currentTheme && (
                    <svg 
                      className="theme-selector__check" 
                      width="16" 
                      height="16" 
                      viewBox="0 0 16 16"
                    >
                      <path d="M3 8l3 3 7-7" stroke="currentColor" strokeWidth="2" fill="none"/>
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ThemeSelector;

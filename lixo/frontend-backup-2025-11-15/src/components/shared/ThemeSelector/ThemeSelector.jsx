/**
 * ThemeSelector Component - Seletor de Temas
 * ===========================================
 *
 * Componente para trocar entre temas (Cyberpunk, Windows 11, etc)
 */

import React, { useState } from 'react';
import { useTheme } from '../../../hooks/useTheme';
import styles from './ThemeSelector.module.css';

export const ThemeSelector = ({ compact = false, showInHeader: _showInHeader = false }) => {
  const {
    theme,
    mode,
    setTheme,
    toggleMode,
    availableThemes,
    currentThemeInfo,
    supportsMode
  } = useTheme();

  const [isOpen, setIsOpen] = useState(false);

  const handleThemeChange = (themeId) => {
    setTheme(themeId);
    setIsOpen(false);
  };

  if (compact) {
    // Versão compacta para header
    return (
      <div className={styles.compact}>
        <button
          className={styles.compactButton}
          onClick={() => setIsOpen(!isOpen)}
          title="Mudar tema"
        >
          <span className={styles.themeIcon}>
            {theme === 'default' && '🟢'}
            {theme === 'cyber-blue' && '🔵'}
            {theme === 'purple-haze' && '🟣'}
            {theme === 'amber-alert' && '🟠'}
            {theme === 'red-alert' && '🔴'}
            {theme === 'stealth-mode' && '⚫'}
            {theme === 'windows11' && '🪟'}
          </span>
        </button>

        {isOpen && (
          <div className={styles.dropdown}>
            {availableThemes.map((t) => (
              <button
                key={t.id}
                className={`${styles.dropdownItem} ${theme === t.id ? styles.active : ''}`}
                onClick={() => handleThemeChange(t.id)}
                style={{
                  '--preview-primary': t.preview.primary,
                  '--preview-secondary': t.preview.secondary
                }}
              >
                <span className={styles.themePreview}>
                  <span className={styles.previewDot} style={{ backgroundColor: 'var(--preview-primary)' }} />
                  <span className={styles.previewDot} style={{ backgroundColor: 'var(--preview-secondary)' }} />
                </span>
                <span className={styles.themeName}>{t.name}</span>
                {theme === t.id && <span className={styles.checkmark}>✓</span>}
              </button>
            ))}

            {supportsMode && (
              <>
                <div className={styles.divider} />
                <button
                  className={styles.dropdownItem}
                  onClick={() => {
                    toggleMode();
                    setIsOpen(false);
                  }}
                >
                  <span className={styles.modeIcon}>
                    {mode === 'light' ? '☀️' : '🌙'}
                  </span>
                  <span className={styles.themeName}>
                    {mode === 'light' ? 'Modo Escuro' : 'Modo Claro'}
                  </span>
                </button>
              </>
            )}
          </div>
        )}
      </div>
    );
  }

  // Versão completa para settings
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Tema da Interface</h3>
        <p className={styles.subtitle}>
          Personalize a aparência da plataforma
        </p>
      </div>

      <div className={styles.themesGrid}>
        {availableThemes.map((t) => (
          <button
            key={t.id}
            className={`${styles.themeCard} ${theme === t.id ? styles.selected : ''}`}
            onClick={() => handleThemeChange(t.id)}
          >
            <div className={styles.cardHeader}>
              <div
                className={styles.themePreviewLarge}
                style={{
                  '--preview-bg': t.preview.background,
                  '--preview-primary': t.preview.primary,
                  '--preview-secondary': t.preview.secondary
                }}
              >
                <div className={styles.previewSquare} style={{ backgroundColor: 'var(--preview-bg)' }}>
                  <div
                    className={styles.previewAccent}
                    style={{
                      borderColor: 'var(--preview-primary)',
                      boxShadow: t.id === 'cyberpunk'
                        ? `0 0 10px var(--preview-primary)`
                        : 'none'
                    }}
                  />
                  <div className={styles.previewContent}>
                    <span className={styles.previewLine} style={{ backgroundColor: 'var(--preview-primary)' }} />
                    <span className={styles.previewLine} style={{ backgroundColor: 'var(--preview-secondary)' }} />
                  </div>
                </div>
              </div>

              {theme === t.id && (
                <div className={styles.selectedBadge}>
                  <span className={styles.checkmarkLarge}>✓</span>
                </div>
              )}
            </div>

            <div className={styles.cardBody}>
              <h4 className={styles.cardTitle}>{t.name}</h4>
              <p className={styles.cardDescription}>{t.description}</p>
            </div>
          </button>
        ))}
      </div>

      {supportsMode && (
        <div className={styles.modeToggle}>
          <span className={styles.modeLabel}>Modo:</span>
          <button
            className={styles.modeButton}
            onClick={toggleMode}
          >
            <span className={`${styles.modeOption} ${mode === 'light' ? styles.modeActive : ''}`}>
              ☀️ Claro
            </span>
            <span className={`${styles.modeOption} ${mode === 'dark' ? styles.modeActive : ''}`}>
              🌙 Escuro
            </span>
          </button>
        </div>
      )}

      <div className={styles.footer}>
        <span className={styles.currentTheme}>
          Tema atual: <strong>{currentThemeInfo.name}</strong>
          {supportsMode && ` (${mode === 'light' ? 'Claro' : 'Escuro'})`}
        </span>
      </div>
    </div>
  );
};

export default ThemeSelector;

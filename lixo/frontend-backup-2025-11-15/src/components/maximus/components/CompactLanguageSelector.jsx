/**
 * CompactLanguageSelector - Minimal Language Switcher for Maximus Header
 *
 * 🎯 ZERO INLINE STYLES - 100% CSS Module
 * ✅ Theme-agnostic (Matrix + Enterprise)
 * ✅ Matches MaximusHeader design
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './CompactLanguageSelector.module.css';

const LANGUAGES = [
  { code: 'pt-BR', flag: '🇧🇷', name: 'Português' },
  { code: 'en-US', flag: '🇺🇸', name: 'English' },
  { code: 'es-ES', flag: '🇪🇸', name: 'Español' }
];

export const CompactLanguageSelector = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const currentLang = LANGUAGES.find(l => l.code === i18n.language) || LANGUAGES[0];

  const handleChange = (langCode) => {
    i18n.changeLanguage(langCode);
    setIsOpen(false);
  };

  return (
    <div className={styles.container}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={styles.toggle}
        title={`Language: ${currentLang.name}`}
        aria-label="Language selector"
        aria-expanded={isOpen}
      >
        {currentLang.flag}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          role="menu"
          aria-label="Language selection menu"
          tabIndex={-1}
          className={styles.dropdown}
          onMouseLeave={() => setIsOpen(false)}
        >
          {/* Header */}
          <div className={styles.dropdownHeader}>
            🌐 Language
          </div>

          {/* Language Options */}
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              onClick={() => handleChange(lang.code)}
              className={`${styles.langButton} ${currentLang.code === lang.code ? styles.active : ''}`}
              role="menuitem"
              aria-current={currentLang.code === lang.code ? 'true' : undefined}
            >
              <span className={styles.flag}>{lang.flag}</span>
              <span className={styles.langName}>{lang.name}</span>
              {currentLang.code === lang.code && (
                <span className={styles.checkmark}>✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default CompactLanguageSelector;

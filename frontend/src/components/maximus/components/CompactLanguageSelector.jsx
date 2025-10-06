/**
 * CompactLanguageSelector - Minimal Language Switcher for Maximus Header
 *
 * Ultra-compact language selector with dropdown
 * Positioned discretely in the header
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

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
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '42px',
          height: '32px',
          background: 'rgba(139, 92, 246, 0.15)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '6px',
          color: '#E2E8F0',
          fontSize: '1.2rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s ease',
          padding: 0
        }}
        onMouseEnter={(e) => {
          e.target.style.background = 'rgba(139, 92, 246, 0.25)';
          e.target.style.borderColor = '#8B5CF6';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = 'rgba(139, 92, 246, 0.15)';
          e.target.style.borderColor = 'rgba(139, 92, 246, 0.3)';
        }}
        title={`Language: ${currentLang.name}`}
      >
        {currentLang.flag}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '40px',
            right: 0,
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 27, 75, 0.98))',
            border: '1px solid rgba(139, 92, 246, 0.4)',
            borderRadius: '8px',
            padding: '0.5rem',
            backdropFilter: 'blur(15px)',
            boxShadow: '0 8px 24px rgba(139, 92, 246, 0.3)',
            zIndex: 10000,
            minWidth: '150px'
          }}
          onMouseLeave={() => setIsOpen(false)}
        >
          {/* Header */}
          <div style={{
            fontSize: '0.6rem',
            color: '#94A3B8',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            marginBottom: '0.5rem',
            paddingBottom: '0.5rem',
            borderBottom: '1px solid rgba(139, 92, 246, 0.2)',
            fontFamily: 'monospace'
          }}>
            🌐 Language
          </div>

          {/* Language Options */}
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              onClick={() => handleChange(lang.code)}
              style={{
                width: '100%',
                padding: '0.6rem',
                background: currentLang.code === lang.code
                  ? 'rgba(139, 92, 246, 0.3)'
                  : 'transparent',
                border: 'none',
                borderRadius: '4px',
                color: currentLang.code === lang.code ? '#E2E8F0' : '#94A3B8',
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                marginBottom: '0.25rem',
                transition: 'all 0.2s ease',
                fontFamily: 'monospace',
                textAlign: 'left'
              }}
              onMouseEnter={(e) => {
                if (currentLang.code !== lang.code) {
                  e.target.style.background = 'rgba(139, 92, 246, 0.15)';
                  e.target.style.color = '#E2E8F0';
                }
              }}
              onMouseLeave={(e) => {
                if (currentLang.code !== lang.code) {
                  e.target.style.background = 'transparent';
                  e.target.style.color = '#94A3B8';
                }
              }}
            >
              <span style={{ fontSize: '1.25rem' }}>{lang.flag}</span>
              <span style={{ flex: 1 }}>{lang.name}</span>
              {currentLang.code === lang.code && (
                <span style={{ color: '#10B981', fontSize: '0.9rem' }}>✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default CompactLanguageSelector;

/**
 * CompactEffectSelector - Discrete Visual Effect Selector for Header
 *
 * Ultra-compact selector for background effects (Matrix, Scanline, etc.)
 * Positioned discretely in the header next to clock.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';

const EFFECTS = [
  { id: 'matrix', icon: '⋮', title: 'Matrix Rain' },
  { id: 'scanline', icon: '━', title: 'Scanline' },
  { id: 'particles', icon: '∴', title: 'Particles' },
  { id: 'none', icon: '○', title: 'None' }
];

export const CompactEffectSelector = ({ currentEffect, onEffectChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {/* Toggle Button - Discreto */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '32px',
          height: '32px',
          background: 'rgba(139, 92, 246, 0.15)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '6px',
          color: '#8B5CF6',
          fontSize: '0.9rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s ease',
          fontFamily: 'monospace'
        }}
        onMouseEnter={(e) => {
          e.target.style.background = 'rgba(139, 92, 246, 0.25)';
          e.target.style.borderColor = '#8B5CF6';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = 'rgba(139, 92, 246, 0.15)';
          e.target.style.borderColor = 'rgba(139, 92, 246, 0.3)';
        }}
        title="Visual Effects"
      >
        {EFFECTS.find(e => e.id === currentEffect)?.icon || '⋮'}
      </button>

      {/* Dropdown Menu */}
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
            minWidth: '140px'
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
            🎨 Visual FX
          </div>

          {/* Effect Options */}
          {EFFECTS.map(effect => (
            <button
              key={effect.id}
              onClick={() => {
                onEffectChange(effect.id);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                padding: '0.5rem',
                background: currentEffect === effect.id
                  ? 'rgba(139, 92, 246, 0.3)'
                  : 'transparent',
                border: 'none',
                borderRadius: '4px',
                color: currentEffect === effect.id ? '#E2E8F0' : '#94A3B8',
                fontSize: '0.75rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.25rem',
                transition: 'all 0.2s ease',
                fontFamily: 'monospace',
                textAlign: 'left'
              }}
              onMouseEnter={(e) => {
                if (currentEffect !== effect.id) {
                  e.target.style.background = 'rgba(139, 92, 246, 0.15)';
                  e.target.style.color = '#E2E8F0';
                }
              }}
              onMouseLeave={(e) => {
                if (currentEffect !== effect.id) {
                  e.target.style.background = 'transparent';
                  e.target.style.color = '#94A3B8';
                }
              }}
            >
              <span style={{ fontSize: '1rem' }}>{effect.icon}</span>
              <span>{effect.title}</span>
              {currentEffect === effect.id && (
                <span style={{ marginLeft: 'auto', color: '#10B981' }}>✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

CompactEffectSelector.propTypes = {
  currentEffect: PropTypes.string.isRequired,
  onEffectChange: PropTypes.func.isRequired
};

export default CompactEffectSelector;

/**
 * CompactEffectSelector - Discrete Visual Effect Selector for Header
 *
 * 🎯 ZERO INLINE STYLES - 100% CSS Module
 * ✅ Theme-agnostic (Matrix + Enterprise)
 * ✅ Matches MaximusHeader design
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import styles from './CompactEffectSelector.module.css';

const EFFECTS = [
  { id: 'matrix', icon: '⋮', title: 'Matrix Rain' },
  { id: 'scanline', icon: '━', title: 'Scanline' },
  { id: 'particles', icon: '∴', title: 'Particles' },
  { id: 'none', icon: '○', title: 'None' }
];

export const CompactEffectSelector = ({ currentEffect, onEffectChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={styles.container}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={styles.toggle}
        title="Visual Effects"
        aria-label="Visual effects selector"
        aria-expanded={isOpen}
      >
        {EFFECTS.find(e => e.id === currentEffect)?.icon || '⋮'}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          role="menu"
          tabIndex={-1}
          aria-label="Effect selection menu"
          className={styles.dropdown}
          onMouseLeave={() => setIsOpen(false)}
        >
          {/* Header */}
          <div className={styles.dropdownHeader}>
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
              className={`${styles.effectButton} ${currentEffect === effect.id ? styles.active : ''}`}
              role="menuitem"
              aria-current={currentEffect === effect.id ? 'true' : undefined}
            >
              <span className={styles.effectIcon}>{effect.icon}</span>
              <span>{effect.title}</span>
              {currentEffect === effect.id && (
                <span className={styles.checkmark}>✓</span>
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

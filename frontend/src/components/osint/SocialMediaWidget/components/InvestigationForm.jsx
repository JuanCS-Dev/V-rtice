import React, { useState } from 'react';
import { Button, Input } from '../../../shared';
import { validateUsername } from '../../../../utils/validation';
import { sanitizePlainText } from '../../../../utils/sanitization';
import styles from './InvestigationForm.module.css';

const PLATFORM_ICONS = {
  twitter: 'fab fa-twitter',
  linkedin: 'fab fa-linkedin',
  github: 'fab fa-github',
  instagram: 'fab fa-instagram',
  reddit: 'fab fa-reddit',
  facebook: 'fab fa-facebook',
  youtube: 'fab fa-youtube',
  tiktok: 'fab fa-tiktok'
};

/**
 * Form for submitting a social media investigation.
 * Handles target input and platform selection.
 *
 * SECURITY (Boris Cherny Standard):
 * - GAP #45 FIXED: Username validation
 * - maxLength on all inputs
 * - Sanitization of user input
 *
 * @version 2.0.0 (Security Hardened)
 */
const InvestigationForm = ({ onInvestigate, loading, error }) => {
  const [target, setTarget] = useState('');
  const [platforms, setPlatforms] = useState(['twitter', 'linkedin', 'github']);
  const [targetError, setTargetError] = useState(null);

  const availablePlatforms = ['twitter', 'linkedin', 'github', 'instagram', 'reddit', 'facebook'];

  // Secure target input handler
  const handleTargetChange = (e) => {
    const sanitized = sanitizePlainText(e.target.value);
    setTarget(sanitized);
    if (targetError) setTargetError(null);
  };

  // Validate target on blur
  const handleTargetBlur = () => {
    if (!target.trim()) {
      return;
    }

    const result = validateUsername(target);
    if (!result.valid) {
      setTargetError(result.error);
    } else {
      setTargetError(null);
    }
  };

  const togglePlatform = (platform) => {
    setPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate before submission
    if (!target.trim()) {
      setTargetError('Username is required');
      return;
    }

    const result = validateUsername(target);
    if (!result.valid) {
      setTargetError(result.error);
      return;
    }

    if (platforms.length === 0) {
      return;
    }

    // Only proceed if no errors
    if (!targetError && !loading) {
      onInvestigate(target, platforms);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
        handleSubmit(e);
    }
  }

  return (
    <div className={styles.form}>
      <form onSubmit={handleSubmit} className={styles.searchForm}>
        <div className={styles.inputWrapper}>
          <label htmlFor="target-input" className={styles.visuallyHidden}>Username ou Target</label>
          <input
            id="target-input"
            type="text"
            placeholder="@ssimone"
            value={target}
            onChange={handleTargetChange}
            onBlur={handleTargetBlur}
            onKeyPress={handleKeyPress}
            disabled={loading}
            className={styles.input}
            maxLength={200}
            aria-invalid={!!targetError}
            aria-describedby={targetError ? "target-error" : undefined}
          />
          {targetError && (
            <div
              id="target-error"
              className={styles.error}
              role="alert"
              aria-live="polite"
            >
              {targetError}
            </div>
          )}
        </div>

        <Button
          type="submit"
          variant="osint"
          size="lg"
          loading={loading}
          disabled={!target.trim() || platforms.length === 0}
          icon={loading ? null : <i className="fas fa-search"></i>}
        >
          {loading ? 'INVESTIGANDO...' : 'INVESTIGAR'}
        </Button>
      </form>

      {/* Platform Selection */}
      <div className={styles.platformSelection}>
        <div id="platform-label" className={styles.platformLabel}>
          Plataformas ({platforms.length} selecionadas):
        </div>
        <div className={styles.platformGrid} role="group" aria-labelledby="platform-label">
          {availablePlatforms.map(platform => (
            <button
              key={platform}
              type="button"
              aria-pressed={platforms.includes(platform)}
              className={`${styles.platformButton} ${
                platforms.includes(platform) ? styles.active : ''
              }`}
              onClick={() => togglePlatform(platform)}
              disabled={loading}
            >
              <i className={PLATFORM_ICONS[platform] || 'fas fa-globe'}></i>
              <span>{platform}</span>
            </button>
          ))}
        </div>
      </div>

      <p className={styles.hint}>
        <i className="fas fa-info-circle"></i>
        Busca em 20+ redes sociais e plataformas públicas
      </p>
    </div>
  );
};

export default React.memo(InvestigationForm);

import React, { useState } from 'react';
import { Button, Input } from '../../../shared';
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
 */
const InvestigationForm = ({ onInvestigate, loading, error }) => {
  const [target, setTarget] = useState('');
  const [platforms, setPlatforms] = useState(['twitter', 'linkedin', 'github']);

  const availablePlatforms = ['twitter', 'linkedin', 'github', 'instagram', 'reddit', 'facebook'];

  const togglePlatform = (platform) => {
    setPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onInvestigate(target, platforms);
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
            onChange={(e) => setTarget(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            className={styles.input}
          />
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

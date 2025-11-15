/**
 * TARGET INPUT - Investigation Target Input with Type Selection
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - Semantic input structure with explicit labels
 * - role="radiogroup" for investigation type buttons
 * - role="radio" + aria-checked for custom radio buttons
 * - aria-live for loading status
 * - Clear labels and descriptions
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Radio group with proper ARIA
 * - Loading status announced
 * - Keyboard accessible
 * - Required field indicated
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';
import { Button } from '../../../shared/Button/Button';
import { Input } from '../../../shared/Input/Input';
import { INVESTIGATION_TYPES } from '../utils/investigationUtils';
import styles from './TargetInput.module.css';

export const TargetInput = ({
  targetInput,
  setTargetInput,
  investigationType,
  setInvestigationType,
  isAnalyzing,
  onStart
}) => {
  return (
    <div className={styles.container}>
      {/* Input de Target */}
      <div className={styles.section}>
        <label htmlFor="target-input" className={styles.label}>
          Target
        </label>
        <Input
          id="target-input"
          type="text"
          value={targetInput}
          onChange={(e) => setTargetInput(e.target.value)}
          placeholder="IP, Domain or URL..."
          disabled={isAnalyzing}
          variant="cyber"
          aria-required="true"
          aria-describedby="target-hint"
        />
        <p id="target-hint" className="sr-only">
          Enter an IP address, domain name, or URL to investigate
        </p>
      </div>

      {/* Tipo de Investigação */}
      <fieldset className={styles.section}>
        <legend className={styles.label}>Investigation Type</legend>
        <div
          role="radiogroup"
          aria-label="Select investigation type"
          className={styles.types}>
          {INVESTIGATION_TYPES.map(type => (
            <button
              key={type.id}
              type="button"
              role="radio"
              aria-checked={investigationType === type.id}
              aria-label={`${type.name}: ${type.description}`}
              onClick={() => setInvestigationType(type.id)}
              disabled={isAnalyzing}
              className={`${styles.typeButton} ${investigationType === type.id ? styles.active : ''}`}
            >
              <div className={styles.typeName}>{type.name}</div>
              <div className={styles.typeDescription}>{type.description}</div>
            </button>
          ))}
        </div>
      </fieldset>

      {/* Botão Start */}
      <Button
        onClick={onStart}
        disabled={isAnalyzing || !targetInput.trim()}
        variant="success"
        fullWidth
        aria-label={isAnalyzing ? "Investigation in progress" : "Initialize investigation"}
      >
        {isAnalyzing ? (
          <>
            <div className={styles.spinner} aria-hidden="true"></div>
            <span>Analyzing...</span>
          </>
        ) : (
          <span>Initialize Investigation</span>
        )}
      </Button>

      {isAnalyzing && (
        <div className="sr-only" role="status" aria-live="polite">
          Investigation in progress...
        </div>
      )}
    </div>
  );
};

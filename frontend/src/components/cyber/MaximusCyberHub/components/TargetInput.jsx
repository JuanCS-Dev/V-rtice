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
        <label htmlFor="target-input" className={styles.label}>Target</label>
        <Input
          id="target-input"
          type="text"
          value={targetInput}
          onChange={(e) => setTargetInput(e.target.value)}
          placeholder="IP, Domain or URL..."
          disabled={isAnalyzing}
          variant="cyber"
        />
      </div>

      {/* Tipo de Investigação */}
      <div className={styles.section}>
        <label htmlFor="investigation-type" className={styles.label}>Investigation Type</label>
        <div className={styles.types}>
          {INVESTIGATION_TYPES.map(type => (
            <button
              key={type.id}
              onClick={() => setInvestigationType(type.id)}
              disabled={isAnalyzing}
              className={`${styles.typeButton} ${investigationType === type.id ? styles.active : ''}`}
            >
              <div className={styles.typeName}>{type.name}</div>
              <div className={styles.typeDescription}>{type.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Botão Start */}
      <Button
        onClick={onStart}
        disabled={isAnalyzing || !targetInput.trim()}
        variant="success"
        fullWidth
      >
        {isAnalyzing ? (
          <>
            <div className={styles.spinner}></div>
            <span>Analyzing...</span>
          </>
        ) : (
          <span>Initialize Investigation</span>
        )}
      </Button>
    </div>
  );
};

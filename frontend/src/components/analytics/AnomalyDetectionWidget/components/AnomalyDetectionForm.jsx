import React from "react";
import { Button } from "../../../shared";
import styles from "./AnomalyDetectionForm.module.css";

const METHODS = [
  { value: "zscore", label: "Z-Score (Statistical)" },
  { value: "iqr", label: "IQR (Interquartile Range)" },
  { value: "isolation_forest", label: "Isolation Forest (ML)" },
  { value: "lstm", label: "LSTM Autoencoder (Deep Learning)" },
];

/**
 * Form for submitting anomaly detection jobs.
 */
const AnomalyDetectionForm = ({
  dataInput,
  setDataInput,
  method,
  setMethod,
  sensitivity,
  setSensitivity,
  loading,
  onDetect,
  onGenerateSample,
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onDetect();
  };

  return (
    <form onSubmit={handleSubmit} className={styles.formContainer}>
      <div className={styles.formGroup}>
        <label htmlFor="data-input">Dados (separados por vírgula):</label>
        <textarea
          id="data-input"
          className={styles.textarea}
          placeholder="1.2, 1.3, 1.1, 15.7, 1.4, 1.3, 1.2, ..."
          value={dataInput}
          onChange={(e) => setDataInput(e.target.value)}
          rows={4}
          disabled={loading}
        />
        <button
          type="button"
          className={styles.sampleButton}
          onClick={onGenerateSample}
          disabled={loading}
        >
          <i className="fas fa-magic"></i> Gerar Dados de Exemplo
        </button>
      </div>

      <div className={styles.formGroup}>
        <label htmlFor="method-select">Método de Detecção:</label>
        <select
          id="method-select"
          className={styles.select}
          value={method}
          onChange={(e) => setMethod(e.target.value)}
          disabled={loading}
        >
          {METHODS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.formGroup}>
        <label htmlFor="sensitivity-slider">
          Sensibilidade: {(sensitivity * 100).toFixed(0)}%
        </label>
        <input
          id="sensitivity-slider"
          type="range"
          className={styles.slider}
          min="0.01"
          max="0.2"
          step="0.01"
          value={sensitivity}
          onChange={(e) => {
            const val = parseFloat(e.target.value);
            if (!isNaN(val) && val >= 0.01 && val <= 0.2) {
              setSensitivity(val);
            }
          }}
          disabled={loading}
        />
        <div className={styles.sliderLabels}>
          <span>Baixa (1%)</span>
          <span>Alta (20%)</span>
        </div>
      </div>

      <Button
        type="submit"
        variant="analytics"
        size="lg"
        loading={loading}
        disabled={!dataInput.trim()}
        icon={<i className="fas fa-brain"></i>}
      >
        {loading ? "ANALISANDO..." : "DETECTAR ANOMALIAS"}
      </Button>
    </form>
  );
};

export default React.memo(AnomalyDetectionForm);

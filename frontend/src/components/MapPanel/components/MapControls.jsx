import React from 'react';
import { Button } from '../../../shared';
import styles from './MapControls.module.css';

/**
 * Renders the entire map control panel, including stats, filters, and AI controls.
 */
const MapControls = ({
  // Data props
  statistics,
  timeFilter, setTimeFilter,
  crimeTypeFilter, setCrimeTypeFilter,
  isLoading,
  isPredicting,
  predictionError,
  successMessage,
  occurrenceData,
  handlePredictiveAnalysis,

  // Control props
  heatmapVisible, setHeatmapVisible,
  showOccurrenceMarkers, setShowOccurrenceMarkers,
  showPredictiveHotspots, setShowPredictiveHotspots,
  analysisRadius, setAnalysisRadius,
  minSamples, setMinSamples
}) => {
  return (
    <div className={styles.controlsOverlay}>
      {/* Statistics Card */}
      <div className={styles.card}>
        <div className={styles.header}>
          <i className="fas fa-chart-bar"></i>
          <span>ESTATÍSTICAS</span>
        </div>
        <div className={styles.statsRow}>
          <div className={styles.statCompact}>
            <span className={styles.statValue}>{statistics.totalOccurrences}</span>
            <span className={styles.statLabel}>Ocorrências</span>
          </div>
          <div className={styles.statCompact}>
            <span className={`${styles.statValue} ${styles.critical}`}>{statistics.criticalZones}</span>
            <span className={styles.statLabel}>Críticas</span>
          </div>
          <div className={styles.statCompact}>
            <span className={`${styles.statValue} ${styles.success}`}>{statistics.activePredictions}</span>
            <span className={styles.statLabel}>Predições</span>
          </div>
        </div>
      </div>

      {/* Controls Card */}
      <div className={styles.card}>
        <div className={styles.header}>
          <i className="fas fa-cogs"></i>
          <span>CONTROLES</span>
        </div>

        <div className={styles.filtersRow}>
          <select
            className={styles.filterSelect}
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
          >
            <option value="all">Todos</option>
            <option value="24h">24H</option>
            <option value="7d">7D</option>
            <option value="30d">30D</option>
          </select>

          <select
            className={styles.filterSelect}
            value={crimeTypeFilter}
            onChange={(e) => setCrimeTypeFilter(e.target.value)}
          >
            <option value="todos">Todos Tipos</option>
            <option value="roubo">Roubo</option>
            <option value="furto">Furto</option>
            <option value="trafico">Tráfico</option>
          </select>
        </div>

        <div className={styles.layerToggles}>
          <label className={styles.toggleLabel}>
            <input type="checkbox" className={styles.toggleCheckbox} checked={heatmapVisible} onChange={() => setHeatmapVisible(!heatmapVisible)} />
            <span><i className="fas fa-fire"></i> Heatmap</span>
          </label>
          <label className={styles.toggleLabel}>
            <input type="checkbox" className={styles.toggleCheckbox} checked={showOccurrenceMarkers} onChange={() => setShowOccurrenceMarkers(!showOccurrenceMarkers)} />
            <span><i className="fas fa-map-marker-alt"></i> Marcadores</span>
          </label>
          <label className={styles.toggleLabel}>
            <input type="checkbox" className={styles.toggleCheckbox} checked={showPredictiveHotspots} onChange={() => setShowPredictiveHotspots(!showPredictiveHotspots)} />
            <span><i className="fas fa-brain"></i> IA</span>
          </label>
        </div>

        <div className={styles.aiControls}>
          <div className={styles.sliderControl}>
            <label>Raio: {analysisRadius.toFixed(1)}km</label>
            <input
              type="range"
              min="0.5"
              max="10"
              step="0.1"
              value={analysisRadius}
              onChange={(e) => setAnalysisRadius(parseFloat(e.target.value))}
              className={styles.slider}
            />
          </div>
          <div className={styles.sliderControl}>
            <label>Min: {minSamples}</label>
            <input
              type="range"
              min="2"
              max="20"
              step="1"
              value={minSamples}
              onChange={(e) => setMinSamples(parseInt(e.target.value, 10))}
              className={styles.slider}
            />
          </div>
        </div>

        <Button
          onClick={() => handlePredictiveAnalysis(analysisRadius, minSamples)}
          disabled={isLoading || isPredicting || occurrenceData.length < minSamples}
          variant="cyber"
          className={styles.aiButton}
          icon={isPredicting ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-brain"></i>}
        >
          {isPredicting ? 'PROCESSANDO...' : 'ANALISAR IA'}
        </Button>
      </div>

      {/* Feedback Messages */}
      {predictionError && (
        <div className={`${styles.alert} ${styles.error}`}>
          <i className="fas fa-exclamation-circle"></i>
          <span>{predictionError}</span>
        </div>
      )}

      {successMessage && (
        <div className={`${styles.alert} ${styles.success}`}>
          <i className="fas fa-check-circle"></i>
          <span>{successMessage}</span>
        </div>
      )}
    </div>
  );
};

export default React.memo(MapControls);

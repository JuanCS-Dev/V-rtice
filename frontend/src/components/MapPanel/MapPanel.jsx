import React, { useMemo } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useMapData } from './hooks/useMapData';
import { useMapControls } from './hooks/useMapControls';
import { MapControls } from './components/MapControls';
import { MapLayers } from './components/MapLayers';
import styles from './MapPanel.module.css';

/**
 * MapPanel - REFATORADO
 * Orquestra a exibição do mapa, controles e camadas de dados.
 */
const MapPanel = ({ dossierData }) => {
  const {
    occurrenceData,
    timeFilter, setTimeFilter,
    crimeTypeFilter, setCrimeTypeFilter,
    isLoading,
    isPredicting,
    predictionError,
    successMessage,
    predictedHotspots,
    statistics,
    handlePredictiveAnalysis
  } = useMapData();

  const {
    heatmapVisible, setHeatmapVisible,
    showOccurrenceMarkers, setShowOccurrenceMarkers,
    showPredictiveHotspots, setShowPredictiveHotspots,
    analysisRadius, setAnalysisRadius,
    minSamples, setMinSamples
  } = useMapControls();

  const initialCenter = useMemo(() => [-16.328, -48.953], []);
  const initialZoom = 12;

  return (
    <div className={styles.mapPanelContainer}>
      {(isLoading || isPredicting) && (
        <div className={styles.loadingOverlay}>
          <div className={styles.loadingContent}>
            <div className={styles.loadingSpinner}><i className="fas fa-spinner"></i></div>
            <span className={styles.loadingText}>
              {isLoading ? 'CARREGANDO DADOS...' : 'AURORA AI PROCESSANDO...'}
            </span>
          </div>
        </div>
      )}

      <MapControls
        statistics={statistics}
        timeFilter={timeFilter}
        setTimeFilter={setTimeFilter}
        crimeTypeFilter={crimeTypeFilter}
        setCrimeTypeFilter={setCrimeTypeFilter}
        isLoading={isLoading}
        isPredicting={isPredicting}
        predictionError={predictionError}
        successMessage={successMessage}
        occurrenceData={occurrenceData}
        handlePredictiveAnalysis={handlePredictiveAnalysis}
        heatmapVisible={heatmapVisible}
        setHeatmapVisible={setHeatmapVisible}
        showOccurrenceMarkers={showOccurrenceMarkers}
        setShowOccurrenceMarkers={setShowOccurrenceMarkers}
        showPredictiveHotspots={showPredictiveHotspots}
        setShowPredictiveHotspots={setShowPredictiveHotspots}
        analysisRadius={analysisRadius}
        setAnalysisRadius={setAnalysisRadius}
        minSamples={minSamples}
        setMinSamples={setMinSamples}
      />

      <MapContainer
        center={initialCenter}
        zoom={initialZoom}
        scrollWheelZoom={true}
        className={styles.leafletContainer}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        <MapLayers 
            heatmapVisible={heatmapVisible}
            occurrenceData={occurrenceData}
            showOccurrenceMarkers={showOccurrenceMarkers}
            showPredictiveHotspots={showPredictiveHotspots}
            predictedHotspots={predictedHotspots}
            dossierData={dossierData}
        />
      </MapContainer>
    </div>
  );
};

export default MapPanel;

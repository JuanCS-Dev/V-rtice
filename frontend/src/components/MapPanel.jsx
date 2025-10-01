import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import HeatmapLayer from './HeatmapLayer';
import axios from 'axios';

// Importações para clustering
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster';

// --- Funções Auxiliares e Ícones ---
const getRiskColor = (riskLevel) => {
  const colors = {
    'Crítico': '#ff0040',
    'Alto': '#ff4000',
    'Médio': '#ffaa00',
    'Baixo': '#00aa00',
    'Mínimo': '#00aaff'
  };
  return colors[riskLevel] || '#00aaff';
};

const createIcon = (color, pulse = false, opacity = 1, size = 16) => {
  const pulseHtml = pulse ? `<div class="pulse-ring" style="border-color: ${color};"></div>` : '';
  return L.divIcon({
    html: `
      <div class="cyber-marker" style="opacity: ${opacity};">
        <div class="marker-core" style="background-color: ${color}; width: ${size-4}px; height: ${size-4}px;"></div>
        ${pulseHtml}
      </div>
    `,
    className: 'custom-cyber-marker',
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -size/2]
  });
};

const createHotspotIcon = (riskLevel) => createIcon(getRiskColor(riskLevel), true, 1, 20);

// --- Componente de Marcadores Clusterizados Otimizado ---
const ClusteredOccurrenceMarkers = React.memo(({ data }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || data.length === 0) return;

    const markerClusterGroup = L.markerClusterGroup({
      chunkedLoading: true,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      maxClusterRadius: 50,
      disableClusteringAtZoom: 16,
      iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        let size = count < 10 ? 'small' : count < 100 ? 'medium' : 'large';
        let color = count < 10 ? '#00aaff' : count < 100 ? '#ffaa00' : '#ff4000';

        return new L.DivIcon({
          html: `
            <div class="cluster-inner cyber-cluster-${size}" style="background: radial-gradient(circle, ${color}, transparent);">
              <span class="cluster-count">${count}</span>
            </div>
          `,
          className: `marker-cluster marker-cluster-${size}`,
          iconSize: new L.Point(40, 40)
        });
      }
    });

    const occurrenceIcon = createIcon('rgba(255, 0, 0, 0.8)', false, 1);

    // Processar dados em batch para melhor performance
    const batchSize = 100;
    for (let i = 0; i < data.length; i += batchSize) {
      const batch = data.slice(i, i + batchSize);

      batch.forEach((point) => {
        if (typeof point.lat === 'number' && typeof point.lng === 'number') {
          const marker = L.marker([point.lat, point.lng], { icon: occurrenceIcon });

          marker.bindPopup(`
            <div class="cyber-popup">
              <div class="popup-header">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>OCORRÊNCIA</strong>
              </div>
              <div class="popup-content">
                <div class="coord-line">
                  <span class="label">TIPO:</span>
                  <span class="value">${point.tipo || 'N/A'}</span>
                </div>
                <div class="coord-line">
                  <span class="label">DATA:</span>
                  <span class="value">${point.timestamp ? new Date(point.timestamp).toLocaleDateString('pt-BR') : 'N/A'}</span>
                </div>
                <div class="coord-line">
                  <span class="label">INTENSIDADE:</span>
                  <span class="value">${(point.intensity * 100).toFixed(0)}%</span>
                </div>
                <div class="coord-line">
                  <span class="label">LAT:</span>
                  <span class="value">${point.lat.toFixed(6)}°</span>
                </div>
                <div class="coord-line">
                  <span class="label">LNG:</span>
                  <span class="value">${point.lng.toFixed(6)}°</span>
                </div>
              </div>
            </div>
          `, { maxWidth: 250, className: 'cyber-popup-container' });

          markerClusterGroup.addLayer(marker);
        }
      });
    }

    map.addLayer(markerClusterGroup);

    return () => map.removeLayer(markerClusterGroup);
  }, [map, data]);

  return null;
});

// --- Componente de Hotspots Preditivos com Animação ---
const PredictiveHotspots = React.memo(({ hotspots, visible }) => {
  const map = useMap();

  useEffect(() => {
    // Limpar hotspots anteriores
    map.eachLayer(layer => {
      if (layer.options && layer.options.isHotspot) {
        map.removeLayer(layer);
      }
    });

    if (!map || !visible || !hotspots || hotspots.length === 0) return;

    const hotspotsGroup = L.layerGroup();

    hotspots.forEach((hotspot, index) => {
      const { center_lat: lat, center_lng: lng } = hotspot;
      if (typeof lat === 'number' && typeof lng === 'number') {
        const icon = createHotspotIcon(hotspot.risk_level);
        const marker = L.marker([lat, lng], { icon, isHotspot: true });

        // Adicionar círculo de área de influência
        const circle = L.circle([lat, lng], {
          radius: (hotspot.radius || 500) * (hotspot.risk_score / 100),
          color: getRiskColor(hotspot.risk_level),
          fillColor: getRiskColor(hotspot.risk_level),
          fillOpacity: 0.1,
          weight: 1,
          dashArray: '5, 10'
        });

        marker.bindPopup(`
          <div class="cyber-popup predictive-popup">
            <div class="popup-header" style="background: linear-gradient(90deg, ${getRiskColor(hotspot.risk_level)}, #0066cc);">
              <i class="fas fa-brain"></i>
              <strong>HOTSPOT PREDITIVO #${index + 1}</strong>
            </div>
            <div class="popup-content">
              <div class="coord-line">
                <span class="label">RISCO:</span>
                <span class="value" style="color: ${getRiskColor(hotspot.risk_level)}; font-weight: bold;">
                  ${hotspot.risk_level}
                </span>
              </div>
              <div class="coord-line">
                <span class="label">SCORE IA:</span>
                <div class="risk-bar">
                  <div class="risk-bar-fill" style="width: ${hotspot.risk_score}%; background: ${getRiskColor(hotspot.risk_level)};"></div>
                </div>
                <span class="value">${hotspot.risk_score}%</span>
              </div>
              <div class="coord-line">
                <span class="label">OCORRÊNCIAS:</span>
                <span class="value">${hotspot.num_points}</span>
              </div>
              <div class="coord-line">
                <span class="label">CONFIANÇA:</span>
                <span class="value">${hotspot.confidence || 85}%</span>
              </div>
            </div>
          </div>
        `, { maxWidth: 300, className: 'cyber-popup-container' });

        hotspotsGroup.addLayer(marker);
        hotspotsGroup.addLayer(circle);
      }
    });

    map.addLayer(hotspotsGroup);

    return () => map.removeLayer(hotspotsGroup);
  }, [map, hotspots, visible]);

  return null;
});

// Componente para centralizar mapa quando dossierData mudar
const MapUpdater = ({ dossierData }) => {
  const map = useMap();

  useEffect(() => {
    if (dossierData && dossierData.lastKnownLocation) {
      const { lat, lng } = dossierData.lastKnownLocation;
      map.flyTo([lat, lng], 15, { duration: 1.5 });
    }
  }, [dossierData, map]);

  return null;
};

// Componente para marcador do veículo
const VehicleMarker = ({ dossierData }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || !dossierData || !dossierData.lastKnownLocation) return;

    const { lat, lng } = dossierData.lastKnownLocation;
    const riskColor = dossierData.riskLevel === 'HIGH' ? '#ff0040' :
                     dossierData.riskLevel === 'MEDIUM' ? '#ffaa00' : '#00aa00';

    const vehicleIcon = L.divIcon({
      html: `
        <div class="vehicle-marker" style="position: relative;">
          <div class="pulse-ring" style="border-color: ${riskColor};"></div>
          <div style="
            width: 24px;
            height: 24px;
            background: ${riskColor};
            border: 3px solid white;
            border-radius: 50%;
            box-shadow: 0 0 20px ${riskColor};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
          ">🚗</div>
        </div>
      `,
      className: 'custom-vehicle-marker',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15]
    });

    const marker = L.marker([lat, lng], { icon: vehicleIcon });

    marker.bindPopup(`
      <div class="cyber-popup vehicle-popup">
        <div class="popup-header" style="background: linear-gradient(90deg, ${riskColor}, #0066cc);">
          <strong>🚗 VEÍCULO LOCALIZADO</strong>
        </div>
        <div class="popup-content">
          <div class="coord-line">
            <span class="label">PLACA:</span>
            <span class="value" style="color: ${riskColor}; font-weight: bold;">${dossierData.placa}</span>
          </div>
          <div class="coord-line">
            <span class="label">VEÍCULO:</span>
            <span class="value">${dossierData.marca} ${dossierData.modelo}</span>
          </div>
          <div class="coord-line">
            <span class="label">ANO:</span>
            <span class="value">${dossierData.ano}</span>
          </div>
          <div class="coord-line">
            <span class="label">COR:</span>
            <span class="value">${dossierData.cor}</span>
          </div>
          <div class="coord-line">
            <span class="label">SITUAÇÃO:</span>
            <span class="value" style="color: ${riskColor};">${dossierData.situacao}</span>
          </div>
          <div class="coord-line">
            <span class="label">RISCO:</span>
            <span class="value" style="color: ${riskColor};">${dossierData.riskLevel}</span>
          </div>
          <div class="coord-line">
            <span class="label">LOCALIZAÇÃO:</span>
            <span class="value">${dossierData.municipio} - ${dossierData.uf}</span>
          </div>
          <div class="coord-line">
            <span class="label">LAT:</span>
            <span class="value">${lat.toFixed(6)}°</span>
          </div>
          <div class="coord-line">
            <span class="label">LNG:</span>
            <span class="value">${lng.toFixed(6)}°</span>
          </div>
        </div>
      </div>
    `, { maxWidth: 300, className: 'cyber-popup-container' });

    marker.addTo(map);

    // Adicionar marcadores do histórico de localização se existir
    if (dossierData.locationHistory && dossierData.locationHistory.length > 0) {
      const historyGroup = L.layerGroup();

      dossierData.locationHistory.forEach((location, index) => {
        const historyIcon = createIcon('#ffaa00', false, 0.6, 12);
        const historyMarker = L.marker([location.lat, location.lng], { icon: historyIcon });

        historyMarker.bindPopup(`
          <div class="cyber-popup history-popup">
            <div class="popup-header" style="background: linear-gradient(90deg, #ffaa00, #0066cc);">
              <strong>📍 HISTÓRICO DE LOCALIZAÇÃO #${index + 1}</strong>
            </div>
            <div class="popup-content">
              <div class="coord-line">
                <span class="label">DATA:</span>
                <span class="value">${new Date(location.timestamp).toLocaleString('pt-BR')}</span>
              </div>
              <div class="coord-line">
                <span class="label">LOCAL:</span>
                <span class="value">${location.description}</span>
              </div>
              <div class="coord-line">
                <span class="label">COORDENADAS:</span>
                <span class="value">${location.lat.toFixed(6)}°, ${location.lng.toFixed(6)}°</span>
              </div>
            </div>
          </div>
        `, { maxWidth: 300, className: 'cyber-popup-container' });

        historyGroup.addLayer(historyMarker);
      });

      historyGroup.addTo(map);
    }

    return () => {
      map.removeLayer(marker);
    };
  }, [map, dossierData]);

  return null;
};

// === Componente Principal: MapPanel ===
const MapPanel = ({ dossierData }) => {
  // Estados de dados e filtros
  const [occurrenceData, setOccurrenceData] = useState([]);
  const [timeFilter, setTimeFilter] = useState('all');
  const [crimeTypeFilter, setCrimeTypeFilter] = useState('todos');

  // Estados de visualização do mapa
  const [heatmapVisible, setHeatmapVisible] = useState(true);
  const [showOccurrenceMarkers, setShowOccurrenceMarkers] = useState(true);

  // Estados de controle de UI e carga
  const [isLoading, setIsLoading] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionError, setPredictionError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Estados dos resultados da IA
  const [predictedHotspots, setPredictedHotspots] = useState([]);
  const [showPredictiveHotspots, setShowPredictiveHotspots] = useState(true);
  const [aiMetrics, setAiMetrics] = useState(null);

  // Estados para parâmetros da IA
  const [analysisRadius, setAnalysisRadius] = useState(2.5);
  const [minSamples, setMinSamples] = useState(5);

  // Estados para estatísticas
  const [statistics, setStatistics] = useState({
    totalOccurrences: 0,
    criticalZones: 0,
    activePredictions: 0
  });

  // Efeito para buscar dados de ocorrências
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setPredictedHotspots([]);
      setPredictionError(null);

      const params = new URLSearchParams({
        periodo: timeFilter,
        tipo: crimeTypeFilter
      });

      try {
        const response = await axios.get(`http://localhost:8000/ocorrencias/heatmap?${params.toString()}`);
        const data = response.data || [];
        setOccurrenceData(data);

        // Atualizar estatísticas
        setStatistics(prev => ({
          ...prev,
          totalOccurrences: data.length,
          criticalZones: data.filter(d => d.intensity > 0.7).length || 0
        }));

      } catch (error) {
        console.error("Falha ao buscar dados de ocorrências:", error);
        setOccurrenceData([]);
        setPredictionError("Erro ao carregar dados. Verifique a conexão.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [timeFilter, crimeTypeFilter]);

  // Função de análise preditiva
  const handlePredictiveAnalysis = useCallback(async () => {
    if (occurrenceData.length < minSamples) {
      setPredictionError(`Dados insuficientes. Mínimo necessário: ${minSamples} ocorrências.`);
      return;
    }

    setIsPredicting(true);
    setPredictionError(null);
    setSuccessMessage(null);
    setPredictedHotspots([]);

    try {
      const payload = {
        occurrences: occurrenceData,
        eps_km: analysisRadius,
        min_samples: minSamples
      };

      const response = await axios.post('http://localhost:8000/predict/crime-hotspots', payload, {
        timeout: 90000,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const { hotspots, metrics } = response.data;

      setPredictedHotspots(hotspots || []);
      setAiMetrics(metrics);

      // Atualizar estatísticas com dados da IA
      setStatistics(prev => ({
        ...prev,
        activePredictions: hotspots?.length || 0
      }));

      setSuccessMessage(`Análise concluída: ${hotspots?.length || 0} hotspots identificados.`);

      // Limpar mensagem de sucesso após 5 segundos
      setTimeout(() => setSuccessMessage(null), 5000);

    } catch (error) {
      console.error("Erro na análise preditiva:", error);
      const detail = error.response?.data?.detail || "Serviço de IA indisponível ou timeout.";
      setPredictionError(`Falha na análise: ${detail}`);
    } finally {
      setIsPredicting(false);
    }
  }, [occurrenceData, analysisRadius, minSamples]);

  const initialCenter = useMemo(() => [-16.328, -48.953], []);
  const initialZoom = 12;

  return (
    <div className="flex-1 relative h-full w-full">
      <div className="h-full w-full bg-black/20 overflow-hidden relative">

        {/* Overlay de Carregamento */}
        {(isLoading || isPredicting) && (
          <div className="loading-overlay">
            <div className="loading-content">
              <div className="spinner-container">
                <i className="fas fa-spinner fa-spin"></i>
              </div>
              <span className="loading-text">
                {isLoading ? 'CARREGANDO DADOS...' : 'AURORA AI PROCESSANDO...'}
              </span>
            </div>
          </div>
        )}

        {/* Container do Mapa */}
        <MapContainer
          center={initialCenter}
          zoom={initialZoom}
          scrollWheelZoom={true}
          className="h-full w-full"
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />

          {heatmapVisible && <HeatmapLayer points={occurrenceData} />}
          {showOccurrenceMarkers && <ClusteredOccurrenceMarkers data={occurrenceData} />}
          {showPredictiveHotspots && <PredictiveHotspots hotspots={predictedHotspots} visible={showPredictiveHotspots} />}

          {/* Componentes para visualização do veículo pesquisado */}
          <MapUpdater dossierData={dossierData} />
          <VehicleMarker dossierData={dossierData} />
        </MapContainer>

        {/* Painel de Controle Compacto */}
        <div className="absolute top-4 left-4 z-[1000] w-72 flex flex-col gap-3">
          {/* Card de Estatísticas Compacto */}
          <div className="stats-card-compact cyber-glass">
            <div className="stats-header">
              <i className="fas fa-chart-bar"></i>
              <span>ESTATÍSTICAS</span>
            </div>
            <div className="stats-row">
              <div className="stat-compact">
                <span className="stat-value">{statistics.totalOccurrences}</span>
                <span className="stat-label">Ocorrências</span>
              </div>
              <div className="stat-compact">
                <span className="stat-value critical">{statistics.criticalZones}</span>
                <span className="stat-label">Críticas</span>
              </div>
              <div className="stat-compact">
                <span className="stat-value success">{statistics.activePredictions}</span>
                <span className="stat-label">Predições</span>
              </div>
            </div>
          </div>

          {/* Controles Compactos */}
          <div className="controls-compact cyber-glass">
            <div className="control-header">
              <i className="fas fa-cogs"></i>
              <span>CONTROLES</span>
            </div>

            {/* Filtros em linha */}
            <div className="filters-row">
              <select
                className="filter-select compact"
                value={timeFilter}
                onChange={(e) => setTimeFilter(e.target.value)}
              >
                <option value="all">Todos</option>
                <option value="24h">24H</option>
                <option value="7d">7D</option>
                <option value="30d">30D</option>
              </select>

              <select
                className="filter-select compact"
                value={crimeTypeFilter}
                onChange={(e) => setCrimeTypeFilter(e.target.value)}
              >
                <option value="todos">Todos Tipos</option>
                <option value="roubo">Roubo</option>
                <option value="furto">Furto</option>
                <option value="trafico">Tráfico</option>
              </select>
            </div>

            {/* Toggles de Camadas em linha */}
            <div className="layer-toggles-compact">
              <label className="toggle-compact">
                <input type="checkbox" checked={heatmapVisible} onChange={() => setHeatmapVisible(!heatmapVisible)} />
                <span><i className="fas fa-fire"></i> Heatmap</span>
              </label>
              <label className="toggle-compact">
                <input type="checkbox" checked={showOccurrenceMarkers} onChange={() => setShowOccurrenceMarkers(!showOccurrenceMarkers)} />
                <span><i className="fas fa-map-marker-alt"></i> Marcadores</span>
              </label>
              <label className="toggle-compact">
                <input type="checkbox" checked={showPredictiveHotspots} onChange={() => setShowPredictiveHotspots(!showPredictiveHotspots)} />
                <span><i className="fas fa-brain"></i> IA</span>
              </label>
            </div>

            {/* Controles IA Compactos */}
            <div className="ai-controls-compact">
              <div className="slider-compact">
                <label>Raio: {analysisRadius.toFixed(1)}km</label>
                <input
                  type="range"
                  min="0.5"
                  max="10"
                  step="0.1"
                  value={analysisRadius}
                  onChange={(e) => setAnalysisRadius(parseFloat(e.target.value))}
                  className="slider-compact"
                />
              </div>
              <div className="slider-compact">
                <label>Min: {minSamples}</label>
                <input
                  type="range"
                  min="2"
                  max="20"
                  step="1"
                  value={minSamples}
                  onChange={(e) => setMinSamples(parseInt(e.target.value, 10))}
                  className="slider-compact"
                />
              </div>
            </div>

            {/* Botão de Análise */}
            <button
              onClick={handlePredictiveAnalysis}
              disabled={isLoading || isPredicting || occurrenceData.length < minSamples}
              className="ai-button-compact"
            >
              <i className={`fas ${isPredicting ? 'fa-spinner fa-spin' : 'fa-brain'}`}></i>
              <span>{isPredicting ? 'PROCESSANDO...' : 'ANALISAR IA'}</span>
            </button>
          </div>

          {/* Mensagens de Feedback Compactas */}
          {predictionError && (
            <div className="alert-compact error">
              <i className="fas fa-exclamation-circle"></i>
              <span>{predictionError}</span>
            </div>
          )}

          {successMessage && (
            <div className="alert-compact success">
              <i className="fas fa-check-circle"></i>
              <span>{successMessage}</span>
            </div>
          )}
        </div>

        {/* Métricas IA (lado direito) - Somente quando há dados */}
        {aiMetrics && (
          <div className="absolute top-4 right-4 z-[1000] w-64">
            <div className="ai-metrics-compact cyber-glass">
              <div className="metrics-header">
                <i className="fas fa-chart-line"></i>
                <span>MÉTRICAS IA</span>
              </div>
              <div className="metrics-grid-compact">
                <div className="metric-compact">
                  <span className="metric-label">Precisão</span>
                  <span className="metric-value">{aiMetrics.accuracy || 0}%</span>
                </div>
                <div className="metric-compact">
                  <span className="metric-label">Padrões</span>
                  <span className="metric-value">{aiMetrics.patterns || 0}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Estilos CSS Compactos */}
      <style>{`
        /* Variáveis CSS */
        :root {
          --cyber-primary: #00ffff;
          --cyber-secondary: #ff00ff;
          --cyber-danger: #ff0040;
          --cyber-warning: #ffaa00;
          --cyber-success: #00ff00;
          --cyber-dark: #0a0e1a;
          --cyber-glass: rgba(10, 14, 26, 0.9);
        }

        /* Loading Overlay */
        .loading-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: radial-gradient(circle, rgba(0, 255, 255, 0.1), rgba(5, 8, 16, 0.95));
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2000;
          backdrop-filter: blur(10px);
        }

        .loading-content {
          text-align: center;
        }

        .spinner-container {
          font-size: 2rem;
          color: var(--cyber-primary);
          margin-bottom: 15px;
        }

        .loading-text {
          color: var(--cyber-primary);
          font-size: 1rem;
          font-weight: 600;
          letter-spacing: 1px;
        }

        /* Stats Card Compact */
        .stats-card-compact {
          padding: 12px;
          border-radius: 6px;
          border: 1px solid rgba(0, 255, 255, 0.3);
          background: var(--cyber-glass);
          backdrop-filter: blur(10px);
        }

        .stats-header {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--cyber-primary);
          font-weight: 600;
          font-size: 0.8rem;
          margin-bottom: 8px;
          letter-spacing: 1px;
        }

        .stats-row {
          display: flex;
          justify-content: space-between;
        }

        .stat-compact {
          display: flex;
          flex-direction: column;
          align-items: center;
          flex: 1;
        }

        .stat-compact .stat-value {
          font-size: 1.2rem;
          font-weight: bold;
          color: var(--cyber-primary);
        }

        .stat-compact .stat-value.critical {
          color: var(--cyber-danger);
        }

        .stat-compact .stat-value.success {
          color: var(--cyber-success);
        }

        .stat-compact .stat-label {
          font-size: 0.65rem;
          color: #8a99c0;
          text-transform: uppercase;
        }

        /* Controls Compact */
        .controls-compact {
          padding: 12px;
          border-radius: 6px;
          border: 1px solid rgba(0, 255, 255, 0.3);
          background: var(--cyber-glass);
          backdrop-filter: blur(10px);
        }

        .control-header {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--cyber-primary);
          font-weight: 600;
          font-size: 0.8rem;
          margin-bottom: 10px;
          letter-spacing: 1px;
        }

        .filters-row {
          display: flex;
          gap: 6px;
          margin-bottom: 10px;
        }

        .filter-select.compact {
          flex: 1;
          background: rgba(0, 255, 255, 0.05);
          border: 1px solid rgba(0, 255, 255, 0.2);
          color: #d0d8f0;
          padding: 6px 8px;
          border-radius: 4px;
          font-size: 0.75rem;
          cursor: pointer;
        }

        .layer-toggles-compact {
          display: flex;
          gap: 8px;
          margin-bottom: 10px;
          flex-wrap: wrap;
        }

        .toggle-compact {
          display: flex;
          align-items: center;
          cursor: pointer;
          font-size: 0.7rem;
          color: #d0d8f0;
        }

        .toggle-compact input[type="checkbox"] {
          margin-right: 4px;
          width: 12px;
          height: 12px;
          accent-color: var(--cyber-primary);
        }

        .toggle-compact span {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .ai-controls-compact {
          display: flex;
          gap: 10px;
          margin-bottom: 10px;
        }

        .slider-compact {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .slider-compact label {
          font-size: 0.7rem;
          color: #8a99c0;
        }

        .slider-compact input[type="range"] {
          width: 100%;
          height: 4px;
          border-radius: 2px;
          background: rgba(0, 255, 255, 0.1);
          outline: none;
          -webkit-appearance: none;
        }

        .slider-compact input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: var(--cyber-primary);
          cursor: pointer;
        }

        .ai-button-compact {
          width: 100%;
          background: linear-gradient(135deg, var(--cyber-primary), var(--cyber-secondary));
          color: var(--cyber-dark);
          border: none;
          padding: 8px 12px;
          font-size: 0.75rem;
          font-weight: bold;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          text-transform: uppercase;
          letter-spacing: 1px;
          transition: all 0.3s ease;
        }

        .ai-button-compact:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 5px 15px rgba(0, 255, 255, 0.3);
        }

        .ai-button-compact:disabled {
          background: rgba(128, 128, 128, 0.3);
          color: #4a5a8a;
          cursor: not-allowed;
          opacity: 0.6;
        }

        /* Alert Compact */
        .alert-compact {
          padding: 8px 12px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 8px;
          backdrop-filter: blur(10px);
          font-size: 0.75rem;
        }

        .alert-compact.error {
          background: rgba(255, 0, 64, 0.1);
          border: 1px solid rgba(255, 0, 64, 0.3);
          color: #ff8888;
        }

        .alert-compact.success {
          background: rgba(0, 255, 0, 0.1);
          border: 1px solid rgba(0, 255, 0, 0.3);
          color: var(--cyber-success);
        }

        /* AI Metrics Compact */
        .ai-metrics-compact {
          background: var(--cyber-glass);
          border: 1px solid rgba(0, 255, 255, 0.3);
          border-radius: 6px;
          padding: 12px;
          backdrop-filter: blur(10px);
        }

        .metrics-header {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--cyber-primary);
          font-weight: 600;
          font-size: 0.8rem;
          margin-bottom: 10px;
        }

        .metrics-grid-compact {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .metric-compact {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .metric-compact .metric-label {
          font-size: 0.65rem;
          color: #8a99c0;
          text-transform: uppercase;
        }

        .metric-compact .metric-value {
          font-size: 1rem;
          font-weight: bold;
          color: var(--cyber-primary);
        }

        /* Cyber Glass Effect */
        .cyber-glass {
          background: linear-gradient(135deg, rgba(10, 14, 26, 0.95), rgba(0, 255, 255, 0.05));
          backdrop-filter: blur(15px);
          border: 1px solid rgba(0, 255, 255, 0.2);
          box-shadow: 0 4px 16px rgba(0, 255, 255, 0.1);
        }

        /* Popups */
        .cyber-popup .popup-header {
          padding: 8px;
          color: white;
          font-weight: bold;
          border-radius: 4px 4px 0 0;
          display: flex;
          align-items: center;
          gap: 8px;
          background: linear-gradient(90deg, #ff0040, #0066cc);
        }

        .cyber-popup .popup-content {
          padding: 10px;
          background: rgba(5, 8, 16, 0.95);
        }

        .cyber-popup .coord-line {
          display: flex;
          justify-content: space-between;
          padding: 3px 0;
          border-bottom: 1px solid rgba(0, 255, 255, 0.1);
        }

        .cyber-popup .coord-line:last-child {
          border-bottom: none;
        }

        .cyber-popup .label {
          color: #8a99c0;
          font-size: 0.75rem;
        }

        .cyber-popup .value {
          color: var(--cyber-primary);
          font-weight: 600;
          font-size: 0.75rem;
        }

        .risk-bar {
          flex: 1;
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          margin: 0 8px;
          overflow: hidden;
        }

        .risk-bar-fill {
          height: 100%;
          transition: width 1s ease;
        }

        /* Marcador do Veículo */
        .vehicle-marker {
          position: relative;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .pulse-ring {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 30px;
          height: 30px;
          border: 2px solid;
          border-radius: 50%;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% {
            transform: translate(-50%, -50%) scale(1);
            opacity: 1;
          }
          100% {
            transform: translate(-50%, -50%) scale(2.5);
            opacity: 0;
          }
        }

        /* Responsividade */
        @media (max-width: 768px) {
          .absolute.left-4.w-72 {
            width: calc(100% - 32px);
          }

          .filters-row {
            flex-direction: column;
          }

          .layer-toggles-compact {
            flex-direction: column;
            align-items: flex-start;
          }
        }
      `}</style>
    </div>
  );
};

export default MapPanel;
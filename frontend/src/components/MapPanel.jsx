// Path: frontend/src/components/MapPanel.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import HeatmapLayer from './HeatmapLayer';

// Importações para clustering
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster';

// === FUNÇÕES AUXILIARES ===
const getIntensityLevel = (intensity) => {
  if (intensity >= 0.8) return 'high';
  if (intensity >= 0.5) return 'medium';
  return 'low';
};

const getRiskColor = (riskLevel) => {
  switch (riskLevel) {
    case 'Crítico': return '#ff0040';
    case 'Alto': return '#ff4000';
    case 'Médio': return '#ffaa00';
    case 'Baixo': return '#00aa00';
    default: return '#00aaff';
  }
};

const createIcon = (color, pulse = false, opacity = 1, size = 16) => {
  const pulseHtml = pulse ? `<div class="pulse-ring" style="border-color: ${color};"></div>` : '';
  
  return L.divIcon({
    html: `<div class="cyber-marker" style="opacity: ${opacity};">
             <div class="marker-core" style="background-color: ${color}; width: ${size-4}px; height: ${size-4}px;"></div>
             ${pulseHtml}
           </div>`,
    className: 'custom-cyber-marker',
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -size/2]
  });
};

// Ícones específicos
const lastLocationIcon = createIcon('#ff0040', true);
const historyIcon = createIcon('#00ff88');
const createHotspotIcon = (riskLevel) => createIcon(getRiskColor(riskLevel), true, 1, 20);

// === COMPONENTES ===

const ClusteredOccurrenceMarkers = ({ data }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || data.length === 0) return;

    const markerClusterGroup = L.markerClusterGroup({
      chunkedLoading: true,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      maxClusterRadius: 50,
      iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        let size = count < 10 ? 'small' : count < 100 ? 'medium' : 'large';
        return new L.DivIcon({
          html: `<div class="cluster-inner cyber-cluster-${size}"><span class="cluster-count">${count}</span></div>`,
          className: `marker-cluster marker-cluster-${size}`,
          iconSize: new L.Point(40, 40)
        });
      }
    });

    const occurrenceIcon = createIcon('rgba(255, 0, 0, 0.8)', false, 1);

    data.forEach((point) => {
      // Suporte para formato array [lat, lng, intensity] ou objeto
      let lat, lng, intensity, tipo;
      
      if (Array.isArray(point)) {
        [lat, lng, intensity] = point;
        tipo = 'ocorrência';
      } else {
        lat = point.lat;
        lng = point.lng;
        intensity = point.intensity || 1.0;
        tipo = point.tipo || 'ocorrência';
      }

      if (typeof lat === 'number' && typeof lng === 'number') {
        const marker = L.marker([lat, lng], { icon: occurrenceIcon });
        marker.bindPopup(
          `<div class="cyber-popup">
             <div class="popup-header">
               <i class="fas fa-exclamation-triangle"></i>
               <strong>OCORRÊNCIA DETECTADA</strong>
             </div>
             <div class="popup-content">
               <div class="coord-line">
                 <span class="label">TIPO:</span>
                 <span class="value">${tipo}</span>
               </div>
               <div class="coord-line">
                 <span class="label">LAT:</span>
                 <span class="value">${lat.toFixed(6)}°</span>
               </div>
               <div class="coord-line">
                 <span class="label">LNG:</span>
                 <span class="value">${lng.toFixed(6)}°</span>
               </div>
               <div class="coord-line">
                 <span class="label">INTENSIDADE:</span>
                 <span class="value intensity-${getIntensityLevel(intensity)}">${intensity.toFixed(2)}</span>
               </div>
             </div>
           </div>`,
          { maxWidth: 250, className: 'cyber-popup-container' }
        );
        markerClusterGroup.addLayer(marker);
      }
    });

    map.addLayer(markerClusterGroup);
    return () => map.removeLayer(markerClusterGroup);
  }, [map, data]);

  return null;
};

const PredictiveHotspots = ({ hotspots, visible }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || !visible || !hotspots || hotspots.length === 0) return;

    const hotspotsGroup = L.layerGroup();

    hotspots.forEach((hotspot, index) => {
      try {
        // Verificar se o hotspot tem as propriedades necessárias
        const lat = hotspot.lat || hotspot.center_lat;
        const lng = hotspot.lng || hotspot.center_lng;
        
        if (typeof lat !== 'number' || typeof lng !== 'number') {
          console.warn('Hotspot com coordenadas inválidas:', hotspot);
          return;
        }

        const icon = createHotspotIcon(hotspot.risk_level || 'Baixo');
        const marker = L.marker([lat, lng], { icon });
        
        marker.bindPopup(
          `<div class="cyber-popup">
             <div class="popup-header" style="background: linear-gradient(90deg, ${getRiskColor(hotspot.risk_level || 'Baixo')}, #0066cc);">
               <i class="fas fa-brain"></i>
               <strong>HOTSPOT PREDITIVO #${index + 1}</strong>
             </div>
             <div class="popup-content">
               <div class="coord-line">
                 <span class="label">NÍVEL DE RISCO:</span>
                 <span class="value" style="color: ${getRiskColor(hotspot.risk_level || 'Baixo')}; font-weight: bold;">${hotspot.risk_level || 'Baixo'}</span>
               </div>
               <div class="coord-line">
                 <span class="label">OCORRÊNCIAS:</span>
                 <span class="value">${hotspot.num_points || 0}</span>
               </div>
               <div class="coord-line">
                 <span class="label">NÚCLEO:</span>
                 <span class="value">${hotspot.core_samples || 0}</span>
               </div>
               <div class="coord-line">
                 <span class="label">RAIO:</span>
                 <span class="value">${hotspot.radius_km || 'N/A'} km</span>
               </div>
               <div class="coord-line">
                 <span class="label">CENTROIDE:</span>
                 <span class="value">${lat.toFixed(5)}°, ${lng.toFixed(5)}°</span>
               </div>
             </div>
           </div>`,
          { maxWidth: 280, className: 'cyber-popup-container' }
        );

        hotspotsGroup.addLayer(marker);
      } catch (error) {
        console.error('Erro ao renderizar hotspot:', error, hotspot);
      }
    });

    map.addLayer(hotspotsGroup);
    return () => map.removeLayer(hotspotsGroup);
  }, [map, hotspots, visible]);

  return null;
};

const TimeFilterButtons = ({ timeFilter, setTimeFilter }) => {
  const filters = [
    { id: 'all', label: 'Todos', icon: '🌐' },
    { id: '24h', label: '24h', icon: '⚡' },
    { id: '7d', label: '7d', icon: '📅' },
    { id: '30d', label: '30d', icon: '📊' },
  ];
  
  return (
    <div className="cyber-filter-group">
      <div className="filter-title">
        <i className="fas fa-clock"></i>
        <span>PERÍODO TEMPORAL</span>
      </div>
      <div className="filter-buttons">
        {filters.map(filter => (
          <button
            key={filter.id}
            onClick={() => setTimeFilter(filter.id)}
            className={`cyber-filter-btn ${timeFilter === filter.id ? 'active' : ''}`}
            title={`Filtrar por ${filter.label}`}
          >
            <span className="btn-icon">{filter.icon}</span>
            <span className="btn-text">{filter.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

const TypeFilterDropdown = ({ typeFilter, setTypeFilter, occurrenceTypes }) => {
  return (
    <div className="cyber-filter-group">
      <div className="filter-title">
        <i className="fas fa-tags"></i>
        <span>CLASSIFICAÇÃO</span>
      </div>
      <div className="custom-select-wrapper">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="cyber-select"
        >
          <option value="todos">🔍 Todos os Tipos</option>
          {occurrenceTypes.map(type => (
            <option key={type} value={type}>
              📋 {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
            </option>
          ))}
        </select>
        <i className="fas fa-chevron-down select-arrow"></i>
      </div>
    </div>
  );
};

const ChangeView = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [map, center, zoom]);
  return null;
};

// === COMPONENTE PRINCIPAL ===
const MapPanel = ({ dossierData }) => {
  const [heatmapData, setHeatmapData] = useState([]);
  const [heatmapVisible, setHeatmapVisible] = useState(true);
  const [timeFilter, setTimeFilter] = useState('all');
  const [occurrenceTypes, setOccurrenceTypes] = useState([]);
  const [typeFilter, setTypeFilter] = useState('todos');
  const [showOccurrenceMarkers, setShowOccurrenceMarkers] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Estados para análise preditiva
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictedHotspots, setPredictedHotspots] = useState([]);
  const [showPredictiveHotspots, setShowPredictiveHotspots] = useState(true);
  const [predictionError, setPredictionError] = useState(null);

  // Buscar tipos de ocorrências
  useEffect(() => {
    const fetchOccurrenceTypes = async () => {
      try {
        const response = await fetch('http://localhost:8000/ocorrencias/tipos');
        if (!response.ok) throw new Error('Falha ao buscar tipos de ocorrência');
        const types = await response.json();
        setOccurrenceTypes(types);
      } catch (error) {
        console.error('Erro ao buscar tipos:', error);
      }
    };
    fetchOccurrenceTypes();
  }, []);

  // Buscar dados do heatmap
  useEffect(() => {
    const fetchHeatmapData = async () => {
      setIsLoading(true);
      setPredictedHotspots([]); // Limpar hotspots anteriores
      setPredictionError(null);
      
      const params = new URLSearchParams();
      if (timeFilter !== 'all') params.append('periodo', timeFilter);
      if (typeFilter !== 'todos') params.append('tipo', typeFilter);
      
      const queryString = params.toString();
      const url = `http://localhost:8000/ocorrencias/heatmap${queryString ? `?${queryString}` : ''}`;
      
      try {
        setHeatmapData([]);
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        setHeatmapData(data || []);
      } catch (error) {
        console.error("Falha ao buscar dados do heatmap:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHeatmapData();
  }, [timeFilter, typeFilter]);

  // Função para análise preditiva
  const handlePredictiveAnalysis = useCallback(async () => {
    if (heatmapData.length < 5) {
      alert("Dados insuficientes para análise preditiva (mínimo 5 ocorrências)");
      return;
    }

    setIsPredicting(true);
    setPredictionError(null);

    try {
      // Preparar dados para o Aurora
      const occurrences = heatmapData.map(point => {
        // Suporte para formato array [lat, lng, intensity] ou objeto
        if (Array.isArray(point)) {
          return {
            lat: point[0],
            lng: point[1],
            intensity: point[2] || 1.0,
            timestamp: new Date().toISOString(),
            tipo: 'ocorrencia'
          };
        } else {
          return {
            lat: point.lat,
            lng: point.lng,
            intensity: point.intensity || 1.0,
            timestamp: point.timestamp || new Date().toISOString(),
            tipo: point.tipo || 'ocorrencia'
          };
        }
      });

      console.log('Enviando para Aurora:', { occurrences: occurrences.slice(0, 3) }); // Log de debug

      const response = await fetch('http://localhost:8000/predict/crime-hotspots', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ occurrences }),
        timeout: 60000
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      console.log('Resposta do Aurora:', result); // Log de debug

      setPredictedHotspots(result.hotspots || []);
      
      // Log para debug
      console.log('Hotspots recebidos:', result.hotspots?.length || 0);
      
      if (result.hotspots && result.hotspots.length > 0) {
        alert(`Análise concluída! ${result.hotspots.length} hotspots identificados.`);
      } else {
        // Verificar se há dados na resposta mesmo sem hotspots
        const totalAnalyzed = result.total_occurrences_analyzed || 0;
        alert(`Análise concluída. ${totalAnalyzed} ocorrências analisadas, mas nenhum hotspot identificado com os critérios atuais.`);
      }

    } catch (error) {
      console.error("Erro na análise preditiva:", error);
      setPredictionError(`Erro na análise preditiva: ${error.message}`);
    } finally {
      setIsPredicting(false);
    }
  }, [heatmapData]);

  const { lastKnownLocation, locationHistory } = dossierData || {};
  const trailPositions = (locationHistory && lastKnownLocation) 
    ? [...locationHistory.map(p => [p.lat, p.lng]), [lastKnownLocation.lat, lastKnownLocation.lng]].reverse() 
    : [];
  const initialCenter = dossierData ? [lastKnownLocation.lat, lastKnownLocation.lng] : [-16.328, -48.953];
  const initialZoom = dossierData ? 12 : 11;

  return (
    <div className="flex-1 relative p-4 pl-0 pb-0">
      {/* CSS Customizado */}
      <style>{`
        .cyber-popup {
          background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
          border: 1px solid #00ff88;
          border-radius: 8px;
          color: #00ff88;
          font-family: 'Courier New', monospace;
          font-size: 11px;
          line-height: 1.4;
          box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        
        .popup-header {
          background: linear-gradient(90deg, #ff0040, #ff4000);
          color: white;
          padding: 6px 10px;
          margin: -8px -8px 8px -8px;
          border-radius: 6px 6px 0 0;
          display: flex;
          align-items: center;
          gap: 6px;
          font-weight: bold;
          font-size: 10px;
        }
        
        .popup-content {
          padding: 0 8px 8px 8px;
        }
        
        .coord-line {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
          padding: 2px 0;
          border-bottom: 1px solid rgba(0, 255, 136, 0.2);
        }
        
        .coord-line:last-child {
          border-bottom: none;
        }
        
        .label {
          font-weight: bold;
          color: #00ff88;
        }
        
        .value {
          color: #ffffff;
          font-weight: normal;
        }
        
        .intensity-high { color: #ff0040; font-weight: bold; }
        .intensity-medium { color: #ffaa00; font-weight: bold; }
        .intensity-low { color: #00ff88; font-weight: bold; }
        
        .cyber-marker {
          position: relative;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .marker-core {
          width: 12px;
          height: 12px;
          border: 2px solid #ffffff;
          border-radius: 50%;
          z-index: 10;
          box-shadow: 0 0 8px rgba(0, 0, 0, 0.8);
        }
        
        .pulse-ring {
          position: absolute;
          width: 20px;
          height: 20px;
          border: 2px solid #ff0040;
          border-radius: 50%;
          animation: cyber-pulse 2s infinite;
        }
        
        @keyframes cyber-pulse {
          0% { transform: scale(0.95); opacity: 1; }
          70% { transform: scale(1.3); opacity: 0; }
          100% { transform: scale(0.95); opacity: 0; }
        }
        
        .cyber-cluster-small .cluster-inner {
          background: linear-gradient(135deg, #00ff88, #00cc66);
          border: 2px solid #ffffff;
          border-radius: 50%;
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #000;
          font-weight: bold;
          font-size: 12px;
          box-shadow: 0 0 15px rgba(0, 255, 136, 0.6);
        }
        
        .cyber-cluster-medium .cluster-inner {
          background: linear-gradient(135deg, #ffaa00, #ff8800);
          border: 2px solid #ffffff;
          border-radius: 50%;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #000;
          font-weight: bold;
          font-size: 13px;
          box-shadow: 0 0 20px rgba(255, 170, 0, 0.6);
        }
        
        .cyber-cluster-large .cluster-inner {
          background: linear-gradient(135deg, #ff0040, #cc0030);
          border: 2px solid #ffffff;
          border-radius: 50%;
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-weight: bold;
          font-size: 14px;
          box-shadow: 0 0 25px rgba(255, 0, 64, 0.8);
        }
        
        .cyber-filter-group {
          margin-bottom: 16px;
          padding: 12px;
          background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(26, 26, 26, 0.9));
          border: 1px solid rgba(0, 255, 136, 0.3);
          border-radius: 8px;
          backdrop-filter: blur(10px);
        }
        
        .filter-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #00ff88;
          font-size: 10px;
          font-weight: bold;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        
        .filter-buttons {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4px;
        }
        
        .cyber-filter-btn {
          background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 255, 136, 0.05));
          border: 1px solid rgba(0, 255, 136, 0.3);
          border-radius: 6px;
          color: #00ff88;
          padding: 6px 8px;
          font-size: 10px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          text-transform: uppercase;
        }
        
        .cyber-filter-btn:hover {
          background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 255, 136, 0.1));
          border-color: #00ff88;
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0, 255, 136, 0.3);
        }
        
        .cyber-filter-btn.active {
          background: linear-gradient(135deg, #00ff88, #00cc66);
          color: #000;
          border-color: #00ff88;
          box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
        }
        
        .btn-icon {
          font-size: 12px;
        }
        
        .btn-text {
          font-size: 9px;
          font-weight: bold;
        }
        
        .custom-select-wrapper {
          position: relative;
        }
        
        .cyber-select {
          width: 100%;
          background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(26, 26, 26, 0.8));
          border: 1px solid rgba(0, 255, 136, 0.3);
          border-radius: 6px;
          color: #00ff88;
          padding: 8px 30px 8px 12px;
          font-size: 10px;
          font-weight: 500;
          cursor: pointer;
          appearance: none;
          outline: none;
          transition: all 0.3s ease;
        }
        
        .cyber-select:hover,
        .cyber-select:focus {
          border-color: #00ff88;
          background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 255, 136, 0.05));
          box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        
        .select-arrow {
          position: absolute;
          right: 10px;
          top: 50%;
          transform: translateY(-50%);
          color: #00ff88;
          font-size: 10px;
          pointer-events: none;
        }
        
        .layer-control {
          background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(26, 26, 26, 0.9));
          border: 1px solid rgba(0, 255, 136, 0.3);
          border-radius: 8px;
          padding: 12px;
          backdrop-filter: blur(10px);
        }
        
        .layer-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #00ff88;
          font-size: 10px;
          font-weight: bold;
          margin-bottom: 12px;
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        
        .layer-item {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          padding: 6px;
          border-radius: 4px;
          transition: background 0.3s ease;
        }
        
        .layer-item:hover {
          background: rgba(0, 255, 136, 0.1);
        }
        
        .layer-checkbox {
          appearance: none;
          width: 16px;
          height: 16px;
          border: 2px solid rgba(0, 255, 136, 0.5);
          border-radius: 3px;
          background: transparent;
          cursor: pointer;
          position: relative;
          transition: all 0.3s ease;
        }
        
        .layer-checkbox:checked {
          background: linear-gradient(135deg, #00ff88, #00cc66);
          border-color: #00ff88;
        }
        
        .layer-checkbox:checked::after {
          content: '✓';
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          color: #000;
          font-size: 10px;
          font-weight: bold;
        }
        
        .layer-label {
          color: #ffffff;
          font-size: 11px;
          cursor: pointer;
          user-select: none;
        }
        
        .coordinates-display {
          background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(26, 26, 26, 0.9));
          border: 1px solid rgba(255, 0, 64, 0.3);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 16px;
          backdrop-filter: blur(10px);
        }
        
        .coord-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #ff0040;
          font-size: 10px;
          font-weight: bold;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        
        .coord-value {
          color: #ffffff;
          font-family: 'Courier New', monospace;
          font-size: 11px;
          line-height: 1.6;
        }
        
        .loading-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          z-index: 1500;
          backdrop-filter: blur(5px);
        }
        
        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 3px solid rgba(0, 255, 136, 0.3);
          border-top: 3px solid #00ff88;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .prediction-control {
          background: linear-gradient(135deg, rgba(0, 170, 255, 0.1), rgba(0, 100, 200, 0.1));
          border: 1px solid rgba(0, 170, 255, 0.3);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 16px;
          backdrop-filter: blur(10px);
        }
        
        .prediction-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #00aaff;
          font-size: 10px;
          font-weight: bold;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        
        .prediction-btn {
          width: 100%;
          background: linear-gradient(135deg, #00aaff, #0088cc);
          border: 1px solid #00aaff;
          border-radius: 6px;
          color: #fff;
          padding: 8px 12px;
          font-size: 11px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        
        .prediction-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #0088cc, #0066aa);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 170, 255, 0.4);
        }
        
        .prediction-btn:disabled {
          background: rgba(100, 100, 100, 0.5);
          border-color: rgba(100, 100, 100, 0.5);
          cursor: not-allowed;
          opacity: 0.6;
        }
        
        .error-message {
          color: #ff4d4d;
          font-size: 10px;
          margin-top: 8px;
          padding: 4px 8px;
          background: rgba(255, 77, 77, 0.1);
          border: 1px solid rgba(255, 77, 77, 0.3);
          border-radius: 4px;
        }
      `}</style>
      
      <div className="h-full w-full border border-green-400/30 rounded-lg bg-black/20 backdrop-blur-sm overflow-hidden relative">
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <span style={{color: '#00ff88', marginTop: '10px', fontFamily: 'Courier New, monospace'}}>
              CARREGANDO DADOS DE CAMPO...
            </span>
          </div>
        )}
        
        {isPredicting && (
          <div className="loading-overlay">
            <div className="loading-spinner" style={{borderTopColor: '#00aaff'}}></div>
            <span style={{color: '#00aaff', marginTop: '10px', fontFamily: 'Courier New, monospace'}}>
              PROCESSANDO ANÁLISE PREDITIVA...
            </span>
          </div>
        )}
        
        <MapContainer 
          center={initialCenter} 
          zoom={initialZoom} 
          scrollWheelZoom={true} 
          className="h-full w-full"
        >
          {dossierData && (
            <ChangeView center={[lastKnownLocation.lat, lastKnownLocation.lng]} zoom={12} />
          )}
          
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          
          {heatmapVisible && heatmapData.length > 0 && (
            <HeatmapLayer points={heatmapData} />
          )}

          {showOccurrenceMarkers && heatmapData.length > 0 && (
            <ClusteredOccurrenceMarkers data={heatmapData} />
          )}

          {showPredictiveHotspots && (
            <PredictiveHotspots hotspots={predictedHotspots} visible={showPredictiveHotspots} />
          )}

          {dossierData && (
            <>
              {trailPositions.length > 0 && (
                <Polyline
                  pathOptions={{ 
                    color: 'rgba(255, 0, 64, 0.8)', 
                    weight: 3,
                    dashArray: '10, 5',
                    shadowColor: 'rgba(255, 0, 64, 0.3)',
                    shadowWeight: 6
                  }}
                  positions={trailPositions}
                />
              )}
              
              {locationHistory && locationHistory.map((point, index) => (
                <Marker key={index} position={[point.lat, point.lng]} icon={historyIcon}>
                  <Popup className="cyber-popup-container">
                    <div className="cyber-popup">
                      <div className="popup-header">
                        <i className="fas fa-map-marker-alt"></i>
                        <strong>PONTO HISTÓRICO #{index + 1}</strong>
                      </div>
                      <div className="popup-content">
                        <div className="coord-line">
                          <span className="label">TIMESTAMP:</span>
                          <span className="value">{new Date(point.timestamp).toLocaleString('pt-BR')}</span>
                        </div>
                        <div className="coord-line">
                          <span className="label">DESCRIÇÃO:</span>
                          <span className="value">{point.description}</span>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
              
              <Marker position={[lastKnownLocation.lat, lastKnownLocation.lng]} icon={lastLocationIcon}>
                <Popup className="cyber-popup-container">
                  <div className="cyber-popup">
                    <div className="popup-header">
                      <i className="fas fa-crosshairs"></i>
                      <strong>ÚLTIMA LOCALIZAÇÃO</strong>
                    </div>
                    <div className="popup-content">
                      <div className="coord-line">
                        <span className="label">MUNICÍPIO:</span>
                        <span className="value">{dossierData.municipio}</span>
                      </div>
                      <div className="coord-line">
                        <span className="label">UF:</span>
                        <span className="value">{dossierData.uf}</span>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </>
          )}
        </MapContainer>
        
        {/* Painel de Controle */}
        <div className="absolute top-4 left-4 z-[1000] w-64">
          {/* Coordenadas do Alvo */}
          {dossierData && (
            <div className="coordinates-display">
              <div className="coord-title">
                <i className="fas fa-crosshairs"></i>
                <span>COORDENADAS DO ALVO</span>
              </div>
              <div className="coord-value">
                <strong>LAT:</strong> {lastKnownLocation?.lat.toFixed(6)}°<br/>
                <strong>LNG:</strong> {lastKnownLocation?.lng.toFixed(6)}°
              </div>
            </div>
          )}
          
          {/* Filtros Temporais */}
          <TimeFilterButtons timeFilter={timeFilter} setTimeFilter={setTimeFilter} />
          
          {/* Filtros de Tipo */}
          <TypeFilterDropdown 
            typeFilter={typeFilter} 
            setTypeFilter={setTypeFilter} 
            occurrenceTypes={occurrenceTypes} 
          />
          
          {/* Controle de Análise Preditiva */}
          <div className="prediction-control">
            <div className="prediction-title">
              <i className="fas fa-brain"></i>
              <span>ANÁLISE PREDITIVA</span>
            </div>
            
            <button
              onClick={handlePredictiveAnalysis}
              disabled={isLoading || isPredicting || heatmapData.length < 5}
              className="prediction-btn"
            >
              <i className="fas fa-brain"></i>
              <span>
                {isPredicting ? 'CALCULANDO...' : 'GERAR HOTSPOTS'}
              </span>
            </button>
            
            {predictionError && (
              <div className="error-message">
                {predictionError}
              </div>
            )}
          </div>
          
          {/* Controles de Camadas */}
          <div className="layer-control">
            <div className="layer-title">
              <i className="fas fa-layer-group"></i>
              <span>CAMADAS DE VISUALIZAÇÃO</span>
            </div>
            
            <div className="layer-item">
              <input
                type="checkbox"
                id="heatmap-toggle"
                checked={heatmapVisible}
                onChange={() => setHeatmapVisible(!heatmapVisible)}
                className="layer-checkbox"
              />
              <label htmlFor="heatmap-toggle" className="layer-label">
                🔥 Mapa de Densidade Térmica
              </label>
            </div>
            
            <div className="layer-item">
              <input
                type="checkbox"
                id="markers-toggle"
                checked={showOccurrenceMarkers}
                onChange={() => setShowOccurrenceMarkers(!showOccurrenceMarkers)}
                className="layer-checkbox"
              />
              <label htmlFor="markers-toggle" className="layer-label">
                📍 Marcadores de Ocorrências
              </label>
            </div>
            
            <div className="layer-item">
              <input
                type="checkbox"
                id="predictive-toggle"
                checked={showPredictiveHotspots}
                onChange={() => setShowPredictiveHotspots(!showPredictiveHotspots)}
                className="layer-checkbox"
              />
              <label htmlFor="predictive-toggle" className="layer-label">
                🧠 Hotspots Preditivos
              </label>
            </div>
          </div>
          
          {/* Status de Dados */}
          <div className="cyber-filter-group">
            <div className="filter-title">
              <i className="fas fa-database"></i>
              <span>STATUS DOS DADOS</span>
            </div>
            <div style={{ color: '#ffffff', fontSize: '10px', fontFamily: 'Courier New, monospace' }}>
              📊 Ocorrências: <strong style={{ color: '#00ff88' }}>{heatmapData.length}</strong><br/>
              🧠 Hotspots: <strong style={{ color: '#00aaff' }}>{predictedHotspots.length}</strong><br/>
              🔄 Última Atualização: <strong style={{ color: '#00ff88' }}>{new Date().toLocaleTimeString('pt-BR')}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapPanel;

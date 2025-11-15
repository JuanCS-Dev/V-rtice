// Path: frontend/src/components/HeatmapLayer.jsx

import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import 'leaflet.heat';
import L from 'leaflet';
import PropTypes from 'prop-types';

/**
 * Camada de heatmap adaptada para receber um array de objetos.
 * @param {object} props
 * @param {Array<object>} props.points - Array de objetos, cada um com `lat`, `lng`, e `intensity`.
 */
const HeatmapLayer = ({ points }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || !points || points.length === 0) {
      return;
    }

    // --- CORREÇÃO: Transforma os dados do formato de objeto para o formato de array que o L.heatLayer espera ---
    const formattedPoints = points
      .filter(p => typeof p.lat === 'number' && typeof p.lng === 'number') // Filtra pontos com dados inválidos
      .map(p => [p.lat, p.lng, p.intensity || 0.5]); // Usa intensidade do objeto ou um padrão

    // Se após a filtragem não sobrarem pontos, não adiciona a camada.
    if (formattedPoints.length === 0) {
      return;
    }

    const heatLayerOptions = {
      radius: 25,
      blur: 15,
      maxZoom: 18,
      gradient: { 0.4: '#1A237E', 0.65: '#F9A825', 1: '#B71C1C' }
    };

    const heatLayer = L.heatLayer(formattedPoints, heatLayerOptions).addTo(map);

    return () => {
      map.removeLayer(heatLayer);
    };
  }, [map, points]);

  return null;
};

// --- CORREÇÃO: Atualiza os propTypes para o novo formato de dados ---
HeatmapLayer.propTypes = {
  points: PropTypes.arrayOf(
    PropTypes.shape({
      lat: PropTypes.number.isRequired,
      lng: PropTypes.number.isRequired,
      intensity: PropTypes.number // A intensidade pode ser opcional
    }).isRequired
  ).isRequired
};

export default HeatmapLayer;

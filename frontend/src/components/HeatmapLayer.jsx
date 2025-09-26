// Path: frontend/src/components/HeatmapLayer.jsx

import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import 'leaflet.heat';
import L from 'leaflet';
import PropTypes from 'prop-types';

/**
 * Uma camada de mapa de calor (heatmap) para o React-Leaflet.
 * Este componente é um wrapper para a biblioteca Leaflet.heat, 
 * garantindo a integração correta com o ciclo de vida do React.
 * @param {object} props
 * @param {Array<[number, number, number?]>} props.points - Array de pontos para o heatmap. 
 * Cada ponto é um array no formato [latitude, longitude, intensidade(opcional)].
 */
const HeatmapLayer = ({ points }) => {
  const map = useMap();

  useEffect(() => {
    // Não faz nada se o mapa não estiver pronto ou se não houver pontos para renderizar.
    if (!map || !points || points.length === 0) {
      return;
    }

    // Configurações para a camada de heatmap. Ajusta estes valores para otimizar a visualização.
    const heatLayerOptions = {
      radius: 25,
      blur: 15,
      maxZoom: 18,
      gradient: { 0.4: '#1A237E', 0.65: '#F9A825', 1: '#B71C1C' } // Gradiente: Azul escuro -> Amarelo -> Vermelho
    };

    const heatLayer = L.heatLayer(points, heatLayerOptions).addTo(map);

    // Função de cleanup: essencial para evitar camadas duplicadas em re-renderizações.
    // O React executa esta função quando o componente é desmontado ou quando as dependências do useEffect mudam.
    return () => {
      map.removeLayer(heatLayer);
    };
  }, [map, points]); // O efeito é re-executado se a instância do mapa ou os dados dos pontos mudarem.

  return null; // Este componente não renderiza elementos no DOM, apenas manipula o mapa do Leaflet.
};

HeatmapLayer.propTypes = {
  points: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.number).isRequired
  ).isRequired
};

export default HeatmapLayer;

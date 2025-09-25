// src/components/Map.jsx

import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Correção do ícone
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// O COMPONENTE AGORA RECEBE 'location' COMO PARÂMETRO (PROP)
const MapComponent = ({ location }) => {

  const positronUrl = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
  const positronAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

  // Se não recebermos uma localização, podemos mostrar uma mensagem ou um mapa padrão
  if (!location) {
    return <div>Carregando mapa...</div>;
  }

  return (
    <div style={{ height: '100%', width: '100%' }}>
      {/* O MAPA E O MARCADOR AGORA USAM A 'location' RECEBIDA */}
      <MapContainer center={location} zoom={13} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution={positronAttribution}
          url={positronUrl}
        />
        <Marker position={location}>
          <Popup>
            Última localização conhecida.
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

export default MapComponent;

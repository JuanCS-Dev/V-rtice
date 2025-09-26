import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css'; // Importa o CSS do Leaflet

const ChangeView = ({ center, zoom }) => { const map = useMap(); map.setView(center, zoom); return null; };
const createIcon = (color, pulse = false) => { const pulseHtml = pulse ? `<div style="width:100%;height:100%;border-radius:50%;background-color:${color};animation:pulse-anim 2s infinite;"></div><style>@keyframes pulse-anim{0%{transform:scale(.95);box-shadow:0 0 0 0 rgba(255,0,0,.7)}70%{transform:scale(1);box-shadow:0 0 0 10px rgba(255,0,0,0)}100%{transform:scale(.95);box-shadow:0 0 0 0 rgba(255,0,0,0)}}</style>`:''; return L.divIcon({ html: `<div style="width:16px;height:16px;position:relative;"><div style="position:absolute;top:50%;left:50%;width:12px;height:12px;background-color:${color};border:2px solid #fff;border-radius:50%;transform:translate(-50%,-50%);z-index:10;"></div>${pulse?pulseHtml:''}</div>`, className: 'custom-marker-icon', iconSize: [16, 16], iconAnchor: [8, 8], popupAnchor: [0, -8] });};
const lastLocationIcon = createIcon('#f00', true);
const historyIcon = createIcon('#ff0');

const MapPanel = ({ dossierData }) => {
  if (!dossierData) {
    return (
      <div className="flex-1 bg-gradient-to-br from-green-900/10 to-blue-900/10 relative">
        <div className="absolute inset-4 border border-green-400/30 rounded-lg bg-black/20 backdrop-blur-sm flex items-center justify-center h-full text-green-400/50">
          <div className="text-center"><div className="text-6xl mb-4">🗺️</div><p>MAPA SERÁ EXIBIDO APÓS CONSULTA</p></div>
        </div>
      </div>
    );
  }

  const { lastKnownLocation, locationHistory } = dossierData;
  const trailPositions = locationHistory ? [...locationHistory.map(p => [p.lat, p.lng]), [lastKnownLocation.lat, lastKnownLocation.lng]].reverse() : [];

  return (
    // Estrutura simplificada para garantir que o mapa preencha o espaço
    <div className="flex-1 relative p-4 pl-0 pb-0">
      <div className="h-full w-full border border-green-400/30 rounded-lg bg-black/20 backdrop-blur-sm overflow-hidden">
        <MapContainer 
          center={[lastKnownLocation.lat, lastKnownLocation.lng]} 
          zoom={12} 
          scrollWheelZoom={true}
          className="h-full w-full" // Garante que o container do mapa ocupe 100%
        >
          <ChangeView center={[lastKnownLocation.lat, lastKnownLocation.lng]} zoom={12} />
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>' />
          {trailPositions.length > 0 && <Polyline pathOptions={{ color: 'rgba(255, 0, 0, 0.5)', weight: 2 }} positions={trailPositions} />}
          {locationHistory && locationHistory.map((point, index) => (
            <Marker key={index} position={[point.lat, point.lng]} icon={historyIcon}>
              <Popup><div className="bg-black text-white p-1 font-mono text-xs"><strong>Ponto Histórico {index + 1}</strong><br/>{new Date(point.timestamp).toLocaleString('pt-BR')}<br/>{point.description}</div></Popup>
            </Marker>
          ))}
          <Marker position={[lastKnownLocation.lat, lastKnownLocation.lng]} icon={lastLocationIcon}>
            <Popup><div className="bg-black text-white p-1 font-mono text-xs"><strong>Última Localização</strong><br/>{dossierData.municipio} - {dossierData.uf}</div></Popup>
          </Marker>
          <div className="absolute top-4 left-4 bg-black/70 text-green-400 text-xs p-2 rounded z-[1000]">LAT: {lastKnownLocation?.lat.toFixed(3)}° <br/>LNG: {lastKnownLocation?.lng.toFixed(3)}°</div>
        </MapContainer>
      </div>
    </div>
  );
};
export default MapPanel;

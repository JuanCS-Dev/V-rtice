// Path: frontend/src/components/MapPanel.jsx

import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import HeatmapLayer from './HeatmapLayer'; 

// --- Componentes Internos e Ícones (sem alterações) ---
const ChangeView = ({ center, zoom }) => { const map = useMap(); map.setView(center, zoom); return null; };
const createIcon = (color, pulse = false) => { const pulseHtml = pulse ? `<div style="width:100%;height:100%;border-radius:50%;background-color:${color};animation:pulse-anim 2s infinite;"></div><style>@keyframes pulse-anim{0%{transform:scale(.95);box-shadow:0 0 0 0 rgba(255,0,0,.7)}70%{transform:scale(1);box-shadow:0 0 0 10px rgba(255,0,0,0)}100%{transform:scale(.95);box-shadow:0 0 0 0 rgba(255,0,0,0)}}</style>`:''; return L.divIcon({ html: `<div style="width:16px;height:16px;position:relative;"><div style="position:absolute;top:50%;left:50%;width:12px;height:12px;background-color:${color};border:2px solid #fff;border-radius:50%;transform:translate(-50%,-50%);z-index:10;"></div>${pulse?pulseHtml:''}</div>`, className: 'custom-marker-icon', iconSize: [16, 16], iconAnchor: [8, 8], popupAnchor: [0, -8] });};
const lastLocationIcon = createIcon('#f00', true);
const historyIcon = createIcon('#ff0');

const MapPanel = ({ dossierData }) => {
  const [heatmapData, setHeatmapData] = useState([]);
  const [heatmapVisible, setHeatmapVisible] = useState(true);

  useEffect(() => {
    const fetchHeatmapData = async () => {
      try {
        const response = await fetch('http://localhost:8000/ocorrencias/heatmap');
        const data = await response.json();
        
        // --- A CORREÇÃO ESTÁ AQUI ---
        // A API envia um array diretamente, então usamos 'data' em vez de 'data.points'.
        setHeatmapData(data || []); 
      } catch (error) {
        console.error("Falha ao buscar dados do heatmap:", error);
      }
    };
    fetchHeatmapData();
  }, []);

  const { lastKnownLocation, locationHistory } = dossierData || {};
  const trailPositions = (locationHistory && lastKnownLocation) ? [...locationHistory.map(p => [p.lat, p.lng]), [lastKnownLocation.lat, lastKnownLocation.lng]].reverse() : [];

  const initialCenter = dossierData ? [lastKnownLocation.lat, lastKnownLocation.lng] : [-16.328, -48.953];
  const initialZoom = dossierData ? 12 : 11;

  // O console.log pode ser removido agora que encontrámos o problema, mas vou mantê-lo por enquanto.
  // console.log('Estado do heatmapData:', heatmapData);

  return (
    <div className="flex-1 relative p-4 pl-0 pb-0">
      <div className="h-full w-full border border-green-400/30 rounded-lg bg-black/20 backdrop-blur-sm overflow-hidden relative">
        <MapContainer 
          center={initialCenter} 
          zoom={initialZoom} 
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          {dossierData && <ChangeView center={[lastKnownLocation.lat, lastKnownLocation.lng]} zoom={12} />}
          
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>' />

          {heatmapVisible && heatmapData.length > 0 && (
            <HeatmapLayer points={heatmapData} />
          )}

          {dossierData && (
            <>
              {trailPositions.length > 0 && <Polyline pathOptions={{ color: 'rgba(255, 0, 0, 0.5)', weight: 2 }} positions={trailPositions} />}
              {locationHistory && locationHistory.map((point, index) => (
                <Marker key={index} position={[point.lat, point.lng]} icon={historyIcon}>
                  <Popup><div className="bg-black text-white p-1 font-mono text-xs"><strong>Ponto Histórico {index + 1}</strong><br/>{new Date(point.timestamp).toLocaleString('pt-BR')}<br/>{point.description}</div></Popup>
                </Marker>
              ))}
              <Marker position={[lastKnownLocation.lat, lastKnownLocation.lng]} icon={lastLocationIcon}>
                <Popup><div className="bg-black text-white p-1 font-mono text-xs"><strong>Última Localização</strong><br/>{dossierData.municipio} - {dossierData.uf}</div></Popup>
              </Marker>
            </>
          )}
        </MapContainer>
        
        <div className="absolute top-4 left-4 bg-black/70 text-green-400 text-xs p-2 rounded z-[1000] flex flex-col space-y-2">
            {dossierData && (
                <div>
                    <strong>LAT:</strong> {lastKnownLocation?.lat.toFixed(3)}° <br/>
                    <strong>LNG:</strong> {lastKnownLocation?.lng.toFixed(3)}°
                </div>
            )}
            <div className={dossierData ? "border-t border-green-400/30 pt-2" : ""}>
                <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="checkbox" checked={heatmapVisible} onChange={() => setHeatmapVisible(!heatmapVisible)} className="form-checkbox bg-gray-800 border-green-400 text-green-500 focus:ring-green-500" />
                    <span>Mostrar Heatmap</span>
                </label>
            </div>
        </div>
      </div>
    </div>
  );
};

export default MapPanel;

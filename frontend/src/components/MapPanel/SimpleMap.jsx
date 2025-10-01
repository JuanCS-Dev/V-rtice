/**
 * SimpleMap - REESCRITO DO ZERO
 * Mapa funcional SEM complicação
 */

import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix do ícone padrão do Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export const SimpleMap = ({ dossierData }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);
  const [isReady, setIsReady] = useState(false);

  // Inicializar mapa UMA VEZ
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    console.log('[SIMPLE MAP] Initializing...');

    // Criar mapa
    const map = L.map(mapRef.current, {
      center: [-15.7801, -47.9292], // Brasília
      zoom: 4,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    // Adicionar tiles - MÉTODO MAIS SIMPLES POSSÍVEL
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);

    // Aguardar carregamento
    map.whenReady(() => {
      console.log('[SIMPLE MAP] Ready!');
      setTimeout(() => {
        map.invalidateSize();
        setIsReady(true);
      }, 100);
    });

    mapInstanceRef.current = map;

    // Cleanup
    return () => {
      console.log('[SIMPLE MAP] Cleanup');
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Atualizar posição quando dossierData mudar
  useEffect(() => {
    if (!mapInstanceRef.current || !isReady || !dossierData?.lastKnownLocation) return;

    const { lat, lng } = dossierData.lastKnownLocation;
    console.log('[SIMPLE MAP] Moving to:', lat, lng);

    // Remover marcador anterior
    if (markerRef.current) {
      markerRef.current.remove();
    }

    // Adicionar novo marcador
    const marker = L.marker([lat, lng]).addTo(mapInstanceRef.current);
    marker.bindPopup(`
      <div style="padding: 10px;">
        <h3 style="margin: 0 0 10px 0; color: #333;">🚗 Veículo Localizado</h3>
        <p style="margin: 5px 0;"><strong>Placa:</strong> ${dossierData.placa || 'N/A'}</p>
        <p style="margin: 5px 0;"><strong>Modelo:</strong> ${dossierData.modelo || 'N/A'}</p>
        <p style="margin: 5px 0;"><strong>Coordenadas:</strong> ${lat.toFixed(4)}, ${lng.toFixed(4)}</p>
      </div>
    `).openPopup();

    markerRef.current = marker;

    // Mover mapa suavemente
    mapInstanceRef.current.flyTo([lat, lng], 15, {
      duration: 1.5,
    });
  }, [dossierData, isReady]);

  return (
    <div className="w-full h-full relative">
      <div
        ref={mapRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '600px',
          backgroundColor: '#f0f0f0',
          position: 'relative',
          zIndex: 0,
        }}
      />

      {!isReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-10">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-green-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-green-400 font-bold">Carregando mapa...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleMap;

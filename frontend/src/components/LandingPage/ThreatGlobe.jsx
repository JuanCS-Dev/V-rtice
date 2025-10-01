/**
 * ThreatGlobe - Mapa Global Interativo de Ameaças
 */

import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export const ThreatGlobe = () => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [threats, setThreats] = useState([]);

  // Gerar ameaças aleatórias em locais mais realistas
  const generateThreat = () => {
    const types = ['DDoS', 'Malware', 'Phishing', 'Ransomware', 'Exploit'];
    const severities = ['critical', 'high', 'medium', 'low'];

    const regions = [
      { name: 'Brazil', latRange: [-34, 5], lngRange: [-74, -34] },
      { name: 'USA', latRange: [25, 49], lngRange: [-122, -67] },
      { name: 'Russia', latRange: [41, 78], lngRange: [20, 180] },
      { name: 'Europe', latRange: [36, 70], lngRange: [-10, 40] },
      { name: 'Australia', latRange: [-38, -18], lngRange: [120, 148] },
      { name: 'Japan', latRange: [30, 46], lngRange: [129, 146] },
      { name: 'China', latRange: [20, 54], lngRange: [73, 135] },
    ];

    const region = regions[Math.floor(Math.random() * regions.length)];
    
    const lat = Math.random() * (region.latRange[1] - region.latRange[0]) + region.latRange[0];
    const lng = Math.random() * (region.lngRange[1] - region.lngRange[0]) + region.lngRange[0];

    return {
      id: Math.random(),
      type: types[Math.floor(Math.random() * types.length)],
      severity: severities[Math.floor(Math.random() * severities.length)],
      lat: lat,
      lng: lng,
    };
  };

  // Inicializar mapa
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [20, 0],
      zoom: 2,
      minZoom: 2,
      maxZoom: 5,
      zoomControl: false,
      attributionControl: false,
      scrollWheelZoom: false,
      dragging: true,
      preferCanvas: true,
    });

    const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
      attribution: '',
      maxZoom: 5,
      minZoom: 2,
      subdomains: 'abcd',
    });

    tileLayer.on('tileerror', (error, tile) => console.error('Tile error:', error));
    tileLayer.on('load', () => console.log('Tiles loaded successfully'));
    tileLayer.addTo(map);

    mapInstanceRef.current = map;

    // --- ROBUST FIX --- 
    // Observa o container do mapa e força a atualização do Leaflet quando o tamanho muda.
    // Isso corrige o bug dos tiles desalinhados de forma confiável.
    const resizeObserver = new ResizeObserver(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    });

    resizeObserver.observe(mapRef.current);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
      if (mapRef.current) {
        // eslint-disable-next-line react-hooks/exhaustive-deps
        resizeObserver.unobserve(mapRef.current);
      }
    };
  }, []);

  // Adicionar ameaças periodicamente
  useEffect(() => {
    const interval = setInterval(() => {
      setThreats(prev => {
        const newThreats = [...prev, generateThreat()].slice(-50); // Máx 50
        return newThreats;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Renderizar ameaças no mapa
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    const map = mapInstanceRef.current;

    // Limpar marcadores antigos
    map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    // Adicionar novos marcadores
    threats.forEach((threat) => {
      const color = {
        critical: '#ff0040',
        high: '#ff6600',
        medium: '#ffaa00',
        low: '#00ff88'
      }[threat.severity];

      const circle = L.circleMarker([threat.lat, threat.lng], {
        radius: threat.severity === 'critical' ? 8 : 5,
        fillColor: color,
        color: color,
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.6,
      }).addTo(map);

      circle.bindPopup(`
        <div style="font-family: monospace; min-width: 150px;">
          <div style="color: ${color}; font-weight: bold; margin-bottom: 5px;">
            ⚠️ ${threat.type.toUpperCase()}
          </div>
          <div style="font-size: 11px; color: #666;">
            Severidade: ${threat.severity}<br>
            Lat: ${threat.lat.toFixed(2)}<br>
            Lng: ${threat.lng.toFixed(2)}
          </div>
        </div>
      `);

      // Animação de pulso
      setTimeout(() => {
        circle.setRadius(circle.getRadius() * 1.5);
        setTimeout(() => circle.remove(), 500);
      }, 8000);
    });
  }, [threats]);

  return (
    <div className="threat-globe">
      <div
        ref={mapRef}
        style={{
          width: '100%',
          height: '100%',
          background: '#0a0e1a',
          position: 'relative',
          zIndex: 1
        }}
      />

      <div className="globe-overlay">
        <div className="threat-counter">
          <span className="counter-value">{threats.length}</span>
          <span className="counter-label">Ameaças Ativas</span>
        </div>
      </div>
    </div>
  );
};

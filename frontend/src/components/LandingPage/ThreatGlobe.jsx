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

  // Gerar ameaças aleatórias
  const generateThreat = () => {
    const types = ['DDoS', 'Malware', 'Phishing', 'Ransomware', 'Exploit'];
    const severities = ['critical', 'high', 'medium', 'low'];

    return {
      id: Math.random(),
      type: types[Math.floor(Math.random() * types.length)],
      severity: severities[Math.floor(Math.random() * severities.length)],
      lat: (Math.random() * 180) - 90,
      lng: (Math.random() * 360) - 180,
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

    // Tiles escuros - CartoDB Dark Matter (versão alternativa)
    const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
      attribution: '',
      maxZoom: 5,
      minZoom: 2,
      subdomains: 'abcd',
    });

    tileLayer.on('tileerror', function(error, tile) {
      console.error('Tile error:', error);
    });

    tileLayer.on('load', function() {
      console.log('Tiles loaded successfully');
    });

    tileLayer.addTo(map);

    mapInstanceRef.current = map;

    // Force invalidate after mount
    setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 100);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
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

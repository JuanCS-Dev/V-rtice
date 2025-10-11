/**
import logger from '@/utils/logger';
 * ThreatGlobe - Mapa Global Interativo de Ameaças
 * =================================================
 * VERSÃO IMPRESSIONANTE com animação OnionTracer integrada
 *
 * Features:
 * - Ameaças REAIS plotadas no mapa
 * - Animação de trace estilo Hollywood
 * - Paths animados entre nós
 * - Cores por severidade
 * - Interativo e cinematográfico
 */

import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export const ThreatGlobe = ({ realThreats = [] }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const pathsRef = useRef([]);

  const [activeTrace, setActiveTrace] = useState(null);
  const [threatCount, setThreatCount] = useState(0);

  // Cores por severidade/reputation
  const getSeverityColor = (severity) => {
    const colors = {
      malicious: '#ff0040',
      suspicious: '#ff6600',
      questionable: '#ffaa00',
      clean: '#00ff88',
      critical: '#ff0040',
      high: '#ff6600',
      medium: '#ffaa00',
      low: '#00ff88'
    };
    return colors[severity] || '#00d9ff';
  };

  // Inicializar mapa
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [20, 0],
      zoom: 2,
      minZoom: 2,
      maxZoom: 6,
      zoomControl: false,
      attributionControl: false,
      scrollWheelZoom: true,
      dragging: true,
      preferCanvas: true,
    });

    // Tema dark estilo cyber
    const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
      attribution: '',
      maxZoom: 6,
      minZoom: 2,
      subdomains: 'abcd',
    });

    tileLayer.on('tileerror', (error) => logger.error('Tile error:', error));
    tileLayer.addTo(map);

    mapInstanceRef.current = map;

    // ResizeObserver para fix de tiles
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
        resizeObserver.unobserve(mapRef.current);
      }
    };
  }, []);

  // Plotar ameaças REAIS no mapa
  useEffect(() => {
    if (!mapInstanceRef.current || realThreats.length === 0) return;

    const map = mapInstanceRef.current;

    // Limpar marcadores antigos
    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    // Atualizar contador
    setThreatCount(realThreats.length);

    // Adicionar ameaças reais
    realThreats.forEach((threat, index) => {
      // Usar geolocalização REAL do backend (prioridade absoluta)
      let lat, lng;

      if (threat.geolocation && threat.geolocation.lat && (threat.geolocation.lng || threat.geolocation.lon)) {
        // DADOS REAIS DO BACKEND - usar sempre que disponível
        lat = threat.geolocation.lat;
        lng = threat.geolocation.lng || threat.geolocation.lon;

        logger.debug(`[ThreatGlobe] Using REAL geolocation for ${threat.ip}: ${lat}, ${lng} (${threat.geolocation.country})`);
      } else {
        // Fallback: posições em CIDADES REAIS conhecidas (sem oceanos!)
        logger.warn(`[ThreatGlobe] No geolocation for ${threat.ip}, using fallback city`);
        const fallbackCity = getRandomRealCity();
        lat = fallbackCity.lat;
        lng = fallbackCity.lng;
      }

      const color = getSeverityColor(threat.severity);

      // Criar marcador com animação
      const circle = L.circleMarker([lat, lng], {
        radius: threat.isMalicious ? 10 : 6,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.7,
        className: 'threat-marker'
      }).addTo(map);

      // Popup com dados REAIS
      const popupContent = `
        <div style="font-family: 'Courier New', monospace; min-width: 200px; background: #0a0e1a; color: #00ff88; padding: 10px;">
          <div style="color: ${color}; font-weight: bold; font-size: 14px; margin-bottom: 8px; border-bottom: 1px solid ${color}; padding-bottom: 5px;">
            ⚠️ ${threat.type.toUpperCase() || 'THREAT'}
          </div>
          <div style="font-size: 11px; line-height: 1.6;">
            <div><strong style="color: #00d9ff;">IP:</strong> ${threat.ip}</div>
            <div><strong style="color: #00d9ff;">Threat Score:</strong> ${threat.threatScore}/100</div>
            <div><strong style="color: #00d9ff;">Reputation:</strong> ${threat.severity}</div>
            ${threat.geolocation ? `
              <div style="margin-top: 5px; padding-top: 5px; border-top: 1px solid #333;">
                <div><strong style="color: #00d9ff;">Country:</strong> ${threat.geolocation.country}</div>
                ${threat.geolocation.isp ? `<div><strong style="color: #00d9ff;">ISP:</strong> ${threat.geolocation.isp}</div>` : ''}
              </div>
            ` : ''}
            <div style="margin-top: 5px; color: #666; font-size: 10px;">
              Detected: ${threat.timestamp}
            </div>
          </div>
        </div>
      `;

      circle.bindPopup(popupContent);

      // Animação de pulso para ameaças maliciosas
      if (threat.isMalicious) {
        let pulseCount = 0;
        const pulseInterval = setInterval(() => {
          if (pulseCount >= 3) {
            clearInterval(pulseInterval);
            return;
          }
          circle.setRadius(circle.getRadius() * 1.3);
          setTimeout(() => circle.setRadius(threat.isMalicious ? 10 : 6), 300);
          pulseCount++;
        }, 1000);
      }

      markersRef.current.push(circle);

      // Efeito de trace/path animado para primeiras ameaças
      if (index < 3 && threat.geolocation) {
        setTimeout(() => {
          animateTracePath(map, lat, lng, color);
        }, index * 2000);
      }
    });

  }, [realThreats]);

  // Animar trace path estilo OnionTracer
  const animateTracePath = (map, targetLat, targetLng, color) => {
    // Origem: São Paulo (você)
    const origin = [-23.5505, -46.6333];

    // Nó intermediário aleatório (simula relay)
    const relayLat = (origin[0] + targetLat) / 2 + (Math.random() - 0.5) * 20;
    const relayLng = (origin[1] + targetLng) / 2 + (Math.random() - 0.5) * 40;

    // Path 1: Origin -> Relay
    const path1 = L.polyline([origin, [relayLat, relayLng]], {
      color: '#00d9ff',
      weight: 2,
      opacity: 0,
      dashArray: '10, 10',
      className: 'trace-path'
    }).addTo(map);

    // Path 2: Relay -> Target
    const path2 = L.polyline([[relayLat, relayLng], [targetLat, targetLng]], {
      color: color,
      weight: 2,
      opacity: 0,
      dashArray: '5, 5',
      className: 'trace-path'
    }).addTo(map);

    // Animação: fade in
    let opacity = 0;
    const fadeIn = setInterval(() => {
      opacity += 0.1;
      path1.setStyle({ opacity: Math.min(opacity, 0.6) });
      path2.setStyle({ opacity: Math.min(opacity, 0.8) });

      if (opacity >= 0.8) {
        clearInterval(fadeIn);

        // Fade out depois de 5s
        setTimeout(() => {
          let fadeOpacity = opacity;
          const fadeOut = setInterval(() => {
            fadeOpacity -= 0.1;
            path1.setStyle({ opacity: Math.max(fadeOpacity, 0) });
            path2.setStyle({ opacity: Math.max(fadeOpacity, 0) });

            if (fadeOpacity <= 0) {
              clearInterval(fadeOut);
              map.removeLayer(path1);
              map.removeLayer(path2);
            }
          }, 100);
        }, 5000);
      }
    }, 100);

    pathsRef.current.push(path1, path2);
  };

  // Helpers: CIDADES REAIS conhecidas (sem oceanos, sem Aquiles no Mar Egeu!)
  const getRandomRealCity = () => {
    // Lista de cidades REAIS onde ameaças cyber acontecem frequentemente
    const realCities = [
      // América do Sul
      { name: 'São Paulo', country: 'Brazil', lat: -23.5505, lng: -46.6333 },
      { name: 'Rio de Janeiro', country: 'Brazil', lat: -22.9068, lng: -43.1729 },
      { name: 'Buenos Aires', country: 'Argentina', lat: -34.6037, lng: -58.3816 },
      { name: 'Bogotá', country: 'Colombia', lat: 4.7110, lng: -74.0721 },

      // América do Norte
      { name: 'New York', country: 'USA', lat: 40.7128, lng: -74.0060 },
      { name: 'Los Angeles', country: 'USA', lat: 34.0522, lng: -118.2437 },
      { name: 'Chicago', country: 'USA', lat: 41.8781, lng: -87.6298 },
      { name: 'Miami', country: 'USA', lat: 25.7617, lng: -80.1918 },
      { name: 'Toronto', country: 'Canada', lat: 43.6532, lng: -79.3832 },

      // Europa (cidades em terra firme, longe do Mar Egeu!)
      { name: 'London', country: 'UK', lat: 51.5074, lng: -0.1278 },
      { name: 'Paris', country: 'France', lat: 48.8566, lng: 2.3522 },
      { name: 'Berlin', country: 'Germany', lat: 52.5200, lng: 13.4050 },
      { name: 'Frankfurt', country: 'Germany', lat: 50.1109, lng: 8.6821 },
      { name: 'Amsterdam', country: 'Netherlands', lat: 52.3676, lng: 4.9041 },
      { name: 'Stockholm', country: 'Sweden', lat: 59.3293, lng: 18.0686 },
      { name: 'Prague', country: 'Czech Republic', lat: 50.0755, lng: 14.4378 },
      { name: 'Warsaw', country: 'Poland', lat: 52.2297, lng: 21.0122 },
      { name: 'Vienna', country: 'Austria', lat: 48.2082, lng: 16.3738 },

      // Ásia
      { name: 'Tokyo', country: 'Japan', lat: 35.6762, lng: 139.6503 },
      { name: 'Seoul', country: 'South Korea', lat: 37.5665, lng: 126.9780 },
      { name: 'Beijing', country: 'China', lat: 39.9042, lng: 116.4074 },
      { name: 'Shanghai', country: 'China', lat: 31.2304, lng: 121.4737 },
      { name: 'Singapore', country: 'Singapore', lat: 1.3521, lng: 103.8198 },
      { name: 'Hong Kong', country: 'China', lat: 22.3193, lng: 114.1694 },
      { name: 'Mumbai', country: 'India', lat: 19.0760, lng: 72.8777 },
      { name: 'Delhi', country: 'India', lat: 28.7041, lng: 77.1025 },

      // Rússia e Leste Europeu
      { name: 'Moscow', country: 'Russia', lat: 55.7558, lng: 37.6173 },
      { name: 'St. Petersburg', country: 'Russia', lat: 59.9343, lng: 30.3351 },
      { name: 'Bucharest', country: 'Romania', lat: 44.4268, lng: 26.1025 },
      { name: 'Sofia', country: 'Bulgaria', lat: 42.6977, lng: 23.3219 },
      { name: 'Kiev', country: 'Ukraine', lat: 50.4501, lng: 30.5234 },

      // Oceania
      { name: 'Sydney', country: 'Australia', lat: -33.8688, lng: 151.2093 },
      { name: 'Melbourne', country: 'Australia', lat: -37.8136, lng: 144.9631 },

      // África
      { name: 'Johannesburg', country: 'South Africa', lat: -26.2041, lng: 28.0473 },
      { name: 'Cairo', country: 'Egypt', lat: 30.0444, lng: 31.2357 },
      { name: 'Lagos', country: 'Nigeria', lat: 6.5244, lng: 3.3792 }
    ];

    return realCities[Math.floor(Math.random() * realCities.length)];
  };

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

      {/* Overlay com contador */}
      <div className="globe-overlay">
        <div className="threat-counter">
          <span className="counter-value">{threatCount}</span>
          <span className="counter-label">Ameaças Detectadas</span>
        </div>

        {/* Status indicator */}
        <div className="globe-status">
          <span className="status-pulse"></span>
          <span className="status-text">SCANNING GLOBAL THREATS</span>
        </div>
      </div>

      {/* Legend */}
      <div className="globe-legend">
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#ff0040' }}></span>
          <span>Malicious</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#ff6600' }}></span>
          <span>Suspicious</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#ffaa00' }}></span>
          <span>Questionable</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#00ff88' }}></span>
          <span>Clean</span>
        </div>
      </div>

      <style jsx>{`
        .threat-marker {
          animation: pulse-marker 2s infinite;
        }

        @keyframes pulse-marker {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.2); }
        }

        .trace-path {
          animation: dash 20s linear infinite;
        }

        @keyframes dash {
          to {
            stroke-dashoffset: -1000;
          }
        }
      `}</style>
    </div>
  );
};

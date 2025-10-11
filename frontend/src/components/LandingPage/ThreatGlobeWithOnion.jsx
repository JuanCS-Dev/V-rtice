/**
import logger from '@/utils/logger';
 * ThreatGlobe + OnionTracer - VERSÃO COMPLETA
 * ============================================
 * Mapa global COM animação OnionTracer integrada de verdade!
 *
 * Features:
 * - Ameaças REAIS do backend
 * - Animação OnionTracer COMPLETA (origin → entry → middle → exit → target)
 * - Packets animados voando entre nós
 * - Camera follow cinematográfico
 * - Status em tempo real
 */

import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { traceOnionRoute } from '../../api/cyberServices';

export const ThreatGlobeWithOnion = ({ realThreats = [] }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const pathsRef = useRef([]);
  const traceIntervalRef = useRef(null);

  const [threatCount, setThreatCount] = useState(0);
  const [isTracing, setIsTracing] = useState(false);
  const [traceStatus, setTraceStatus] = useState('READY');
  const [traceProgress, setTraceProgress] = useState(0);
  const [currentRoute, setCurrentRoute] = useState([]);
  const [currentHop, setCurrentHop] = useState(0);

  // Cores por severidade
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

  // Cores por tipo de nó
  const getNodeColor = (type) => {
    const colors = {
      origin: '#00ff88',
      entry: '#00d9ff',
      middle: '#ffaa00',
      exit: '#ff00aa',
      destination: '#ff3366'
    };
    return colors[type] || '#00d9ff';
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

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
      attribution: '',
      maxZoom: 6,
      minZoom: 2,
      subdomains: 'abcd',
    }).addTo(map);

    mapInstanceRef.current = map;

    const resizeObserver = new ResizeObserver(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    });

    resizeObserver.observe(mapRef.current);

    return () => {
      if (traceIntervalRef.current) clearInterval(traceIntervalRef.current);
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
      if (mapRef.current) {
        resizeObserver.unobserve(mapRef.current);
      }
    };
  }, []);

  // Iniciar trace automático quando aparecer ameaça maliciosa
  useEffect(() => {
    if (!mapInstanceRef.current || realThreats.length === 0 || isTracing) return;

    // Pegar a primeira ameaça maliciosa
    const maliciousThreat = realThreats.find(t => t.isMalicious);
    if (!maliciousThreat) return;

    // Iniciar trace automaticamente a cada 30s
    const autoTraceInterval = setInterval(() => {
      if (!isTracing) {
        startOnionTrace(maliciousThreat.ip);
      }
    }, 30000); // 30s

    // Trace inicial após 3s
    setTimeout(() => {
      if (!isTracing) {
        startOnionTrace(maliciousThreat.ip);
      }
    }, 3000);

    return () => clearInterval(autoTraceInterval);
  }, [realThreats, isTracing]);

  // Função para iniciar trace OnionRouter
  const startOnionTrace = async (targetIp) => {
    if (isTracing || !mapInstanceRef.current) return;

    setIsTracing(true);
    setTraceStatus('INITIALIZING');
    setTraceProgress(0);
    setCurrentHop(0);

    logger.debug('[OnionTracer] Starting trace for:', targetIp);

    try {
      // Buscar rota completa do backend
      setTraceStatus('ANALYZING');
      const result = await traceOnionRoute(targetIp);

      if (!result.success || !result.route) {
        throw new Error('Failed to trace route');
      }

      const route = result.route;
      setCurrentRoute(route);

      logger.debug('[OnionTracer] Route generated:', route.length, 'hops');

      // Limpar marcadores e paths antigos
      clearMap();

      // Animar trace hop por hop
      let hop = 0;
      const map = mapInstanceRef.current;

      traceIntervalRef.current = setInterval(() => {
        if (hop >= route.length - 1) {
          // Trace completo!
          clearInterval(traceIntervalRef.current);
          setTraceStatus('COMPLETE');
          setTraceProgress(100);
          setIsTracing(false);

          const destination = route[route.length - 1];
          logger.debug('[OnionTracer] Trace complete:', destination);

          // Zoom out após 5s
          setTimeout(() => {
            map.setView([20, 0], 2, { animate: true, duration: 2 });
          }, 5000);

          return;
        }

        const fromNode = route[hop];
        const toNode = route[hop + 1];

        // Update status
        if (toNode.type === 'entry') {
          setTraceStatus('CONNECTING TO ENTRY NODE');
        } else if (toNode.type === 'middle') {
          setTraceStatus(`RELAYING THROUGH ${toNode.city.toUpperCase()}`);
        } else if (toNode.type === 'exit') {
          setTraceStatus('EXIT NODE REACHED');
        } else if (toNode.type === 'destination') {
          setTraceStatus('TRIANGULATING LOCATION');
        }

        // Adicionar nós no mapa
        addNodeMarker(fromNode);
        if (hop === route.length - 2) {
          addNodeMarker(toNode);
        }

        // Adicionar path animado
        addAnimatedPath(fromNode, toNode);

        // Flyto para o próximo nó
        const lat = toNode.lat;
        const lng = toNode.lng || toNode.lon;
        map.flyTo([lat, lng], 5, {
          duration: 1.5,
          easeLinearity: 0.25
        });

        setCurrentHop(hop + 1);
        setTraceProgress(((hop + 1) / (route.length - 1)) * 100);

        hop++;
      }, 2500); // 2.5s por hop

    } catch (error) {
      logger.error('[OnionTracer] Error:', error);
      setTraceStatus('ERROR');
      setIsTracing(false);
    }
  };

  // Adicionar marcador de nó
  const addNodeMarker = (node) => {
    if (!mapInstanceRef.current) return;

    const map = mapInstanceRef.current;
    const color = getNodeColor(node.type);
    const lat = node.lat;
    const lng = node.lng || node.lon;

    const circle = L.circleMarker([lat, lng], {
      radius: node.type === 'destination' ? 15 : 10,
      fillColor: color,
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.8,
    }).addTo(map);

    // Popup
    const popupContent = `
      <div style="font-family: monospace; background: #0a0e1a; color: ${color}; padding: 8px; min-width: 180px;">
        <div style="font-weight: bold; font-size: 12px; margin-bottom: 5px; border-bottom: 1px solid ${color}; padding-bottom: 3px;">
          ${node.type.toUpperCase()} NODE
        </div>
        <div style="font-size: 10px; line-height: 1.5; color: #a8b2c1;">
          <div><strong>City:</strong> ${node.city}, ${node.country}</div>
          <div><strong>IP:</strong> ${node.ip || 'hidden'}</div>
          ${node.layer !== undefined ? `<div><strong>Layer:</strong> ${node.layer}</div>` : ''}
          ${node.encrypted !== undefined ? `<div><strong>Encrypted:</strong> ${node.encrypted ? '✓ YES' : '✗ NO'}</div>` : ''}
        </div>
      </div>
    `;

    circle.bindPopup(popupContent);

    // Animação de pulso
    let pulseCount = 0;
    const pulseInterval = setInterval(() => {
      if (pulseCount >= 3) {
        clearInterval(pulseInterval);
        return;
      }
      circle.setRadius(circle.getRadius() * 1.3);
      setTimeout(() => circle.setRadius(node.type === 'destination' ? 15 : 10), 300);
      pulseCount++;
    }, 800);

    markersRef.current.push(circle);
  };

  // Adicionar path animado
  const addAnimatedPath = (fromNode, toNode) => {
    if (!mapInstanceRef.current) return;

    const map = mapInstanceRef.current;
    const fromLat = fromNode.lat;
    const fromLng = fromNode.lng || fromNode.lon;
    const toLat = toNode.lat;
    const toLng = toNode.lng || toNode.lon;

    const color = fromNode.encrypted ? '#00d9ff' : '#ff3366';

    const path = L.polyline([[fromLat, fromLng], [toLat, toLng]], {
      color: color,
      weight: 3,
      opacity: 0,
      dashArray: fromNode.encrypted ? '10, 10' : '5, 5',
    }).addTo(map);

    // Fade in
    let opacity = 0;
    const fadeIn = setInterval(() => {
      opacity += 0.1;
      path.setStyle({ opacity: Math.min(opacity, 0.8) });
      if (opacity >= 0.8) {
        clearInterval(fadeIn);
      }
    }, 50);

    pathsRef.current.push(path);
  };

  // Limpar mapa
  const clearMap = () => {
    if (!mapInstanceRef.current) return;

    const map = mapInstanceRef.current;

    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    pathsRef.current.forEach(path => map.removeLayer(path));
    pathsRef.current = [];
  };

  // Plotar ameaças reais (estáticas)
  useEffect(() => {
    if (!mapInstanceRef.current || realThreats.length === 0 || isTracing) return;

    setThreatCount(realThreats.length);

    // Plotar apenas as últimas 10 ameaças para não poluir
    const latestThreats = realThreats.slice(0, 10);

    latestThreats.forEach((threat) => {
      if (!threat.geolocation) return;

      const lat = threat.geolocation.lat;
      const lng = threat.geolocation.lng || threat.geolocation.lon;
      if (!lat || !lng) return;

      const color = getSeverityColor(threat.severity);

      const circle = L.circleMarker([lat, lng], {
        radius: 5,
        fillColor: color,
        color: '#fff',
        weight: 1,
        opacity: 0.6,
        fillOpacity: 0.4,
      }).addTo(mapInstanceRef.current);

      const popupContent = `
        <div style="font-family: monospace; min-width: 180px;">
          <div style="color: ${color}; font-weight: bold; font-size: 11px; margin-bottom: 5px;">
            ⚠️ ${threat.type || 'THREAT'}
          </div>
          <div style="font-size: 10px; color: #a8b2c1;">
            <div><strong>IP:</strong> ${threat.ip}</div>
            <div><strong>Score:</strong> ${threat.threatScore}/100</div>
            <div><strong>Status:</strong> ${threat.severity}</div>
          </div>
        </div>
      `;

      circle.bindPopup(popupContent);
    });

  }, [realThreats, isTracing]);

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

        {/* OnionTracer Status */}
        {isTracing && (
          <div className="onion-status">
            <div className="onion-header">
              <span className="onion-icon">🧅</span>
              <span className="onion-title">ONION TRACER</span>
            </div>
            <div className="onion-progress-bar">
              <div className="onion-progress-fill" style={{ width: `${traceProgress}%` }}></div>
            </div>
            <div className="onion-message">{traceStatus}</div>
            <div className="onion-hop">HOP {currentHop}/{currentRoute.length - 1}</div>
          </div>
        )}

        {/* Status indicator */}
        <div className="globe-status">
          <span className="status-pulse"></span>
          <span className="status-text">
            {isTracing ? 'TRACING ONION ROUTE' : 'SCANNING GLOBAL THREATS'}
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="globe-legend">
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#00ff88' }}></span>
          <span>Origin</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#00d9ff' }}></span>
          <span>Entry Node</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#ffaa00' }}></span>
          <span>Middle Relay</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#ff00aa' }}></span>
          <span>Exit Node</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#ff3366' }}></span>
          <span>Target</span>
        </div>
      </div>
    </div>
  );
};

export default ThreatGlobeWithOnion;

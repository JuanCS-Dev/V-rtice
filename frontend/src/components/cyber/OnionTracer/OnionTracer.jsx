/**
 * OnionTracer Component - Hollywood-Style Onion Routing Animation
 * ================================================================
 *
 * A animação ÉPICA de trace de Onion routing como nos filmes!
 * - Visualiza saltos entre nós Tor
 * - Animação de packets voando pelo mapa
 * - Efeitos visuais cinematográficos
 * - "TRACING... BYPASSING NODE... DECRYPTING LAYER..."
 *
 * Inspired by: Mr. Robot, CSI Cyber, Hackers (1995), The Matrix
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { traceOnionRoute } from '../../../api/cyberServices';
import styles from './OnionTracer.module.css';

/**
 * Component que anima a câmera para seguir o trace
 */
const CameraFollower = ({ currentNode }) => {
  const map = useMap();

  useEffect(() => {
    if (currentNode && currentNode.lat && currentNode.lng) {
      map.flyTo([currentNode.lat, currentNode.lng], 6, {
        duration: 1.5,
        easeLinearity: 0.25
      });
    }
  }, [currentNode, map]);

  return null;
};

/**
 * Componente principal
 */
export const OnionTracer = ({
  targetIp = "185.220.101.23",
  onTraceComplete = () => {},
  autoStart = false
}) => {
  const [isTracing, setIsTracing] = useState(false);
  const [currentHop, setCurrentHop] = useState(0);
  const [nodes, setNodes] = useState([]);
  const [paths, setPaths] = useState([]);
  const [status, setStatus] = useState('READY');
  const [statusMessage, setStatusMessage] = useState('Ready to trace...');
  const [progress, setProgress] = useState(0);
  const [packets, setPackets] = useState([]);
  const [realIp, setRealIp] = useState(null);

  const traceIntervalRef = useRef(null);
  const packetIntervalRef = useRef(null);

  /**
   * Gera rota de nós Tor fake (mas realista)
   */
  const generateOnionRoute = useCallback(() => {
    // Localizações reais de exit nodes Tor conhecidos
    const possibleNodes = [
      { city: 'Frankfurt', country: 'Germany', lat: 50.1109, lng: 8.6821, type: 'entry' },
      { city: 'Amsterdam', country: 'Netherlands', lat: 52.3676, lng: 4.9041, type: 'middle' },
      { city: 'Stockholm', country: 'Sweden', lat: 59.3293, lng: 18.0686, type: 'middle' },
      { city: 'Paris', country: 'France', lat: 48.8566, lng: 2.3522, type: 'middle' },
      { city: 'Zurich', country: 'Switzerland', lat: 47.3769, lng: 8.5417, type: 'middle' },
      { city: 'London', country: 'UK', lat: 51.5074, lng: -0.1278, type: 'middle' },
      { city: 'Reykjavik', country: 'Iceland', lat: 64.1466, lng: -21.9426, type: 'middle' },
      { city: 'Helsinki', country: 'Finland', lat: 60.1695, lng: 24.9354, type: 'middle' },
      { city: 'Prague', country: 'Czech Republic', lat: 50.0755, lng: 14.4378, type: 'middle' },
      { city: 'Warsaw', country: 'Poland', lat: 52.2297, lng: 21.0122, type: 'middle' },
      { city: 'Vienna', country: 'Austria', lat: 48.2082, lng: 16.3738, type: 'middle' },
      { city: 'Moscow', country: 'Russia', lat: 55.7558, lng: 37.6173, type: 'exit' },
      { city: 'Bucharest', country: 'Romania', lat: 44.4268, lng: 26.1025, type: 'exit' },
      { city: 'Sofia', country: 'Bulgaria', lat: 42.6977, lng: 23.3219, type: 'exit' }
    ];

    // User location (Brazil)
    const origin = {
      city: 'São Paulo',
      country: 'Brazil',
      lat: -23.5505,
      lng: -46.6333,
      type: 'origin',
      ip: '201.x.x.x',
      encrypted: true
    };

    // Seleciona 1 entry node
    const entryNodes = possibleNodes.filter(n => n.type === 'entry');
    const entry = entryNodes[Math.floor(Math.random() * entryNodes.length)];
    entry.ip = `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.101.${Math.floor(Math.random() * 255)}`;
    entry.encrypted = true;
    entry.layer = 3;

    // Seleciona 2-4 middle nodes
    const middleNodes = possibleNodes.filter(n => n.type === 'middle');
    const numMiddle = 2 + Math.floor(Math.random() * 3); // 2-4 nodes
    const middles = [];
    for (let i = 0; i < numMiddle; i++) {
      const node = middleNodes[Math.floor(Math.random() * middleNodes.length)];
      middles.push({
        ...node,
        ip: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
        encrypted: true,
        layer: 3 - i - 1
      });
    }

    // Seleciona 1 exit node
    const exitNodes = possibleNodes.filter(n => n.type === 'exit');
    const exit = exitNodes[Math.floor(Math.random() * exitNodes.length)];
    exit.ip = targetIp;
    exit.encrypted = false;
    exit.layer = 0;
    exit.type = 'exit';

    // Final destination (real IP location)
    const destination = {
      city: 'Unknown Location',
      country: '???',
      lat: exit.lat + (Math.random() - 0.5) * 0.5,
      lng: exit.lng + (Math.random() - 0.5) * 0.5,
      type: 'destination',
      ip: targetIp,
      encrypted: false,
      layer: 0
    };

    return [origin, entry, ...middles, exit, destination];
  }, [targetIp]);

  /**
   * Inicia trace - VERSÃO COM DADOS REAIS
   */
  const startTrace = useCallback(async () => {
    setIsTracing(true);
    setCurrentHop(0);
    setProgress(0);
    setStatus('INITIALIZING');
    setStatusMessage('Initializing Onion Router trace...');
    setRealIp(null);
    setPaths([]);
    setPackets([]);

    try {
      // ====================================
      // FASE 1: ANÁLISE REAL DO IP TARGET
      // ====================================
      setStatus('ANALYZING');
      setStatusMessage(`Analyzing target IP ${targetIp}... Querying real services...`);

      const traceResult = await traceOnionRoute(targetIp);

      if (!traceResult.success) {
        throw new Error(traceResult.error || 'Trace failed');
      }

      const route = traceResult.route;
      setNodes(route);

      // ====================================
      // FASE 2: ANIMAÇÃO CINEMATOGRÁFICA
      // ====================================
      let hop = 0;
      traceIntervalRef.current = setInterval(() => {
        if (hop >= route.length - 1) {
          // Trace completo!
          clearInterval(traceIntervalRef.current);
          clearInterval(packetIntervalRef.current);

          const destination = route[route.length - 1];
          setStatus('COMPLETE');

          // Mensagem com dados REAIS
          const threatInfo = destination.isMalicious ? '⚠️ MALICIOUS' : '✓ CLEAN';
          setStatusMessage(
            `✓ Trace complete! Real IP: ${targetIp} | ${destination.city}, ${destination.country} | Threat: ${threatInfo}`
          );

          setProgress(100);
          setIsTracing(false);
          setRealIp(destination);

          // Passa dados REAIS para callback
          onTraceComplete({
            ...destination,
            ipAnalysis: traceResult.ipAnalysis,
            threatIntel: traceResult.threatIntel,
            route: route
          });
          return;
        }

        const fromNode = route[hop];
        const toNode = route[hop + 1];

        // Update status com informações REAIS
        if (toNode.type === 'entry') {
          setStatus('CONNECTING');
          setStatusMessage(`Connecting to entry node... ${toNode.city}, ${toNode.country}`);
        } else if (toNode.type === 'middle') {
          setStatus('RELAYING');
          setStatusMessage(`Relaying through ${toNode.city}... Decrypting layer ${toNode.layer}...`);
        } else if (toNode.type === 'exit') {
          setStatus('DECRYPTING');
          setStatusMessage(`Exit node reached! Bypassing final encryption... ${toNode.city}`);
        } else if (toNode.type === 'destination') {
          setStatus('LOCATING');
          const isp = toNode.isp ? `ISP: ${toNode.isp}` : '';
          setStatusMessage(`Triangulating real location... ${toNode.city}, ${toNode.country} ${isp}`);
        }

        // Adiciona path
        setPaths(prev => [...prev, {
          from: [fromNode.lat, fromNode.lng || fromNode.lon],
          to: [toNode.lat, toNode.lng || toNode.lon],
          encrypted: fromNode.encrypted
        }]);

        // Adiciona packet animado
        const packetId = `packet_${hop}_${Date.now()}`;
        setPackets(prev => [...prev, {
          id: packetId,
          from: [fromNode.lat, fromNode.lng || fromNode.lon],
          to: [toNode.lat, toNode.lng || toNode.lon]
        }]);

        // Remove packet depois da animação
        setTimeout(() => {
          setPackets(prev => prev.filter(p => p.id !== packetId));
        }, 2000);

        setCurrentHop(hop + 1);
        setProgress(((hop + 1) / (route.length - 1)) * 100);

        hop++;
      }, 2500); // 2.5s por hop para efeito cinematográfico

    } catch (error) {
      console.error('Trace error:', error);
      setStatus('ERROR');
      setStatusMessage(`❌ Trace failed: ${error.message}`);
      setIsTracing(false);

      // Fallback para rota fake se serviços estiverem offline
      console.warn('Falling back to simulated route...');
      const route = generateOnionRoute();
      setNodes(route);
      // Continua com animação fake...
    }

  }, [targetIp, onTraceComplete, generateOnionRoute]);

  /**
   * Para trace
   */
  const stopTrace = useCallback(() => {
    if (traceIntervalRef.current) {
      clearInterval(traceIntervalRef.current);
    }
    if (packetIntervalRef.current) {
      clearInterval(packetIntervalRef.current);
    }
    setIsTracing(false);
    setStatus('STOPPED');
    setStatusMessage('Trace aborted by user');
  }, []);

  /**
   * Auto-start se configurado
   */
  useEffect(() => {
    if (autoStart) {
      startTrace();
    }

    return () => {
      if (traceIntervalRef.current) clearInterval(traceIntervalRef.current);
      if (packetIntervalRef.current) clearInterval(packetIntervalRef.current);
    };
  }, [autoStart, startTrace]);

  return (
    <div className={styles.container}>
      {/* Control Panel */}
      <div className={styles.controlPanel}>
        <div className={styles.header}>
          <div className={styles.titleSection}>
            <h2 className={styles.title}>
              <span className={styles.icon}>🧅</span>
              ONION ROUTER TRACER
            </h2>
            <p className={styles.subtitle}>Real-time Tor Network Visualization</p>
          </div>

          <div className={styles.controls}>
            <button
              className={`${styles.button} ${styles.buttonPrimary}`}
              onClick={startTrace}
              disabled={isTracing}
            >
              {isTracing ? '⏳ TRACING...' : '▶ START TRACE'}
            </button>

            {isTracing && (
              <button
                className={`${styles.button} ${styles.buttonDanger}`}
                onClick={stopTrace}
              >
                ⏹ ABORT
              </button>
            )}
          </div>
        </div>

        {/* Status Display */}
        <div className={styles.statusBar}>
          <div className={styles.statusIndicator}>
            <span className={`${styles.statusLight} ${isTracing ? styles.statusActive : ''}`} />
            <span className={styles.statusLabel}>STATUS:</span>
            <span className={styles.statusValue}>{status}</span>
          </div>

          <div className={styles.statusMessage}>
            <span className={styles.messageIcon}>→</span>
            {statusMessage}
          </div>
        </div>

        {/* Progress Bar */}
        {isTracing && (
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${progress}%` }} />
            <span className={styles.progressText}>{Math.round(progress)}%</span>
          </div>
        )}

        {/* Hop Info */}
        {nodes.length > 0 && (
          <div className={styles.hopInfo}>
            <span className={styles.hopLabel}>HOP:</span>
            <span className={styles.hopValue}>{currentHop}/{nodes.length - 1}</span>
            <span className={styles.hopSeparator}>|</span>
            <span className={styles.hopLabel}>NODES:</span>
            <span className={styles.hopValue}>{nodes.length}</span>
            <span className={styles.hopSeparator}>|</span>
            <span className={styles.hopLabel}>TARGET:</span>
            <span className={styles.hopValue}>{targetIp}</span>
          </div>
        )}
      </div>

      {/* Map Visualization */}
      <div className={styles.mapContainer}>
        <MapContainer
          center={[50, 10]}
          zoom={4}
          style={{ height: '100%', width: '100%' }}
          className={styles.map}
          zoomControl={true}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />

          {/* Camera Follower */}
          {nodes[currentHop] && <CameraFollower currentNode={nodes[currentHop]} />}

          {/* Draw Paths */}
          {paths.map((path, idx) => (
            <Polyline
              key={`path_${idx}`}
              positions={[path.from, path.to]}
              color={path.encrypted ? '#00d9ff' : '#ff3366'}
              weight={3}
              opacity={0.8}
              dashArray={path.encrypted ? '10, 10' : '0'}
              className={styles.pathLine}
            />
          ))}

          {/* Draw Nodes */}
          {nodes.slice(0, currentHop + 1).map((node, idx) => (
            <CircleMarker
              key={`node_${idx}`}
              center={[node.lat, node.lng]}
              radius={node.type === 'destination' ? 15 : 8}
              fillColor={
                node.type === 'origin' ? '#00ff88' :
                node.type === 'entry' ? '#00d9ff' :
                node.type === 'middle' ? '#ffaa00' :
                node.type === 'exit' ? '#ff00aa' :
                '#ff3366'
              }
              color="#ffffff"
              weight={2}
              opacity={1}
              fillOpacity={node.type === 'destination' ? 1 : 0.8}
              className={idx === currentHop ? styles.pulseNode : ''}
            >
              <Popup>
                <div className={styles.popup}>
                  <strong>{node.city}, {node.country}</strong>
                  <br />
                  <small>Type: {node.type.toUpperCase()}</small>
                  <br />
                  <small>IP: {node.ip}</small>

                  {/* Dados REAIS do IP Intelligence */}
                  {node.isp && (
                    <>
                      <br />
                      <small>ISP: {node.isp}</small>
                    </>
                  )}
                  {node.asn && (
                    <>
                      <br />
                      <small>ASN: {node.asn}</small>
                    </>
                  )}

                  {node.encrypted !== undefined && (
                    <>
                      <br />
                      <small>Encrypted: {node.encrypted ? '✓ YES' : '✗ NO'}</small>
                    </>
                  )}
                  {node.layer !== undefined && node.layer > 0 && (
                    <>
                      <br />
                      <small>Encryption Layer: {node.layer}</small>
                    </>
                  )}

                  {/* Dados REAIS do Threat Intelligence */}
                  {node.threatScore !== undefined && (
                    <>
                      <br />
                      <small>Threat Score: {node.threatScore}/100</small>
                    </>
                  )}
                  {node.reputation && (
                    <>
                      <br />
                      <small>Reputation: {node.reputation.toUpperCase()}</small>
                    </>
                  )}
                  {node.isMalicious !== undefined && (
                    <>
                      <br />
                      <small style={{ color: node.isMalicious ? '#ff3366' : '#00ff88' }}>
                        {node.isMalicious ? '⚠️ MALICIOUS' : '✓ CLEAN'}
                      </small>
                    </>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        <h4 className={styles.legendTitle}>LEGEND</h4>
        <div className={styles.legendItems}>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ backgroundColor: '#00ff88' }} />
            <span className={styles.legendLabel}>Origin (You)</span>
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ backgroundColor: '#00d9ff' }} />
            <span className={styles.legendLabel}>Entry Node</span>
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ backgroundColor: '#ffaa00' }} />
            <span className={styles.legendLabel}>Middle Relay</span>
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ backgroundColor: '#ff00aa' }} />
            <span className={styles.legendLabel}>Exit Node</span>
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ backgroundColor: '#ff3366' }} />
            <span className={styles.legendLabel}>Real Location</span>
          </div>
        </div>
      </div>

      {/* Result Panel - COM DADOS REAIS */}
      {realIp && (
        <div className={styles.resultPanel}>
          <h3 className={styles.resultTitle}>✓ TRACE COMPLETE</h3>
          <div className={styles.resultInfo}>
            <div className={styles.resultItem}>
              <span className={styles.resultLabel}>Real IP:</span>
              <span className={styles.resultValue}>{realIp.ip}</span>
            </div>
            <div className={styles.resultItem}>
              <span className={styles.resultLabel}>Location:</span>
              <span className={styles.resultValue}>{realIp.city}, {realIp.country}</span>
            </div>
            <div className={styles.resultItem}>
              <span className={styles.resultLabel}>Coordinates:</span>
              <span className={styles.resultValue}>
                {realIp.lat?.toFixed(4) || 'N/A'}, {(realIp.lng || realIp.lon)?.toFixed(4) || 'N/A'}
              </span>
            </div>
            {realIp.isp && (
              <div className={styles.resultItem}>
                <span className={styles.resultLabel}>ISP:</span>
                <span className={styles.resultValue}>{realIp.isp}</span>
              </div>
            )}
            {realIp.asn && (
              <div className={styles.resultItem}>
                <span className={styles.resultLabel}>ASN:</span>
                <span className={styles.resultValue}>{realIp.asn}</span>
              </div>
            )}
            <div className={styles.resultItem}>
              <span className={styles.resultLabel}>Hops:</span>
              <span className={styles.resultValue}>{nodes.length - 1}</span>
            </div>
            {realIp.threatScore !== undefined && (
              <div className={styles.resultItem}>
                <span className={styles.resultLabel}>Threat Score:</span>
                <span
                  className={styles.resultValue}
                  style={{ color: realIp.threatScore > 60 ? '#ff3366' : '#00ff88' }}
                >
                  {realIp.threatScore}/100
                </span>
              </div>
            )}
            {realIp.reputation && (
              <div className={styles.resultItem}>
                <span className={styles.resultLabel}>Reputation:</span>
                <span
                  className={styles.resultValue}
                  style={{
                    color:
                      realIp.reputation === 'malicious' ? '#ff3366' :
                      realIp.reputation === 'suspicious' ? '#ffaa00' :
                      '#00ff88'
                  }}
                >
                  {realIp.reputation.toUpperCase()}
                </span>
              </div>
            )}
            {realIp.isMalicious !== undefined && (
              <div className={styles.resultItem}>
                <span className={styles.resultLabel}>Status:</span>
                <span
                  className={styles.resultValue}
                  style={{ color: realIp.isMalicious ? '#ff3366' : '#00ff88', fontWeight: 'bold' }}
                >
                  {realIp.isMalicious ? '⚠️ MALICIOUS DETECTED' : '✓ CLEAN'}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OnionTracer;

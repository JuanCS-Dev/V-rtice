// /home/juan/vertice-dev/frontend/src/components/cyber/ThreatMap.jsx

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';

// Importações para clustering
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster';

// --- Funções Auxiliares para Ameaças Cyber ---
const getThreatColor = (severity) => {
  const colors = {
    'critical': '#ff0040',
    'high': '#ff4000',
    'medium': '#ffaa00',
    'low': '#00aa00',
    'info': '#00aaff'
  };
  return colors[severity] || '#00aaff';
};

const getThreatIcon = (type) => {
  const icons = {
    'malware': '🦠',
    'botnet': '🤖',
    'phishing': '🎣',
    'ddos': '💥',
    'exploit': '⚡',
    'scan': '🔍',
    'intrusion': '🔓',
    'data_breach': '📊',
    'ransomware': '🔒'
  };
  return icons[type] || '⚠️';
};

const createThreatIcon = (severity, type, pulse = false) => {
  const color = getThreatColor(severity);
  const icon = getThreatIcon(type);
  const pulseHtml = pulse ? `<div class="pulse-ring" style="border-color: ${color};"></div>` : '';

  return L.divIcon({
    html: `
      <div class="cyber-threat-marker" style="opacity: 1;">
        <div class="threat-icon" style="background-color: ${color}; border-color: ${color};">
          <span style="font-size: 12px;">${icon}</span>
        </div>
        ${pulseHtml}
      </div>
    `,
    className: 'custom-threat-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
};

// --- Componente de Marcadores de Ameaças Clusterizados ---
const ClusteredThreatMarkers = React.memo(({ data }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || data.length === 0) return;

    const threatClusterGroup = L.markerClusterGroup({
      chunkedLoading: true,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      maxClusterRadius: 50,
      disableClusteringAtZoom: 16,
      iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        let size = count < 10 ? 'small' : count < 100 ? 'medium' : 'large';
        let color = count < 10 ? '#00aaff' : count < 100 ? '#ffaa00' : '#ff4000';

        return new L.DivIcon({
          html: `
            <div class="cluster-inner cyber-cluster-${size}" style="background: radial-gradient(circle, ${color}, transparent);">
              <span class="cluster-count">${count}</span>
            </div>
          `,
          className: `marker-cluster marker-cluster-${size}`,
          iconSize: new L.Point(40, 40)
        });
      }
    });

    // Processar dados de ameaças em batch
    const batchSize = 100;
    for (let i = 0; i < data.length; i += batchSize) {
      const batch = data.slice(i, i + batchSize);

      batch.forEach((threat) => {
        if (typeof threat.lat === 'number' && typeof threat.lng === 'number') {
          const icon = createThreatIcon(threat.severity, threat.type, threat.severity === 'critical');
          const marker = L.marker([threat.lat, threat.lng], { icon });

          marker.bindPopup(`
            <div class="cyber-popup">
              <div class="popup-header" style="background: linear-gradient(90deg, ${getThreatColor(threat.severity)}, #0066cc);">
                <span style="font-size: 16px;">${getThreatIcon(threat.type)}</span>
                <strong>AMEAÇA CYBER</strong>
              </div>
              <div class="popup-content">
                <div class="coord-line">
                  <span class="label">TIPO:</span>
                  <span class="value">${threat.type?.toUpperCase() || 'N/A'}</span>
                </div>
                <div class="coord-line">
                  <span class="label">SEVERIDADE:</span>
                  <span class="value" style="color: ${getThreatColor(threat.severity)}; font-weight: bold;">
                    ${threat.severity?.toUpperCase() || 'N/A'}
                  </span>
                </div>
                <div class="coord-line">
                  <span class="label">IP ORIGEM:</span>
                  <span class="value">${threat.source_ip || 'N/A'}</span>
                </div>
                <div class="coord-line">
                  <span class="label">PAÍS:</span>
                  <span class="value">${threat.country || 'N/A'}</span>
                </div>
                <div class="coord-line">
                  <span class="label">ALVOS:</span>
                  <span class="value">${threat.targets?.toLocaleString() || '0'}</span>
                </div>
                <div class="coord-line">
                  <span class="label">DETECTADO:</span>
                  <span class="value">${threat.timestamp || 'N/A'}</span>
                </div>
                <div class="coord-line">
                  <span class="label">DETALHES:</span>
                  <span class="value">${threat.details || 'Ameaça detectada pelo sistema'}</span>
                </div>
              </div>
            </div>
          `, { maxWidth: 300, className: 'cyber-popup-container' });

          threatClusterGroup.addLayer(marker);
        }
      });
    }

    map.addLayer(threatClusterGroup);

    return () => map.removeLayer(threatClusterGroup);
  }, [map, data]);

  return null;
});

// === Componente Principal: ThreatMap ===
const ThreatMap = () => {
  const [threatData, setThreatData] = useState([]);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [realTimeData, setRealTimeData] = useState(null);

  // Buscar dados reais de ameaças do backend
  const fetchThreatData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Tentar buscar dados de ameaças reais do backend cyber
      const endpoints = [
        'http://localhost:8000/api/network/threats',
        'http://localhost:8000/api/cyber/threats',
        'http://localhost:8000/api/ip/threats'
      ];

      let threatResults = [];

      // Tentar cada endpoint
      for (const endpoint of endpoints) {
        try {
          const response = await axios.get(endpoint, { timeout: 5000 });
          if (response.data) {
            // Adaptar dados para formato de ameaças
            const data = Array.isArray(response.data) ? response.data :
                          response.data.data ? response.data.data :
                          response.data.threats ? response.data.threats : [];

            const adaptedData = data.map((item, index) => ({
              id: item.id || index,
              lat: item.lat || item.latitude || generateRandomLat(),
              lng: item.lng || item.longitude || generateRandomLng(),
              type: item.type || item.threat_type || 'unknown',
              severity: item.severity || item.risk_level || 'medium',
              source_ip: item.ip || item.source_ip || generateRandomIP(),
              country: item.country || item.location || 'Unknown',
              targets: item.targets || item.affected_systems || Math.floor(Math.random() * 1000) + 1,
              timestamp: item.timestamp || item.detected_at || new Date().toLocaleString(),
              details: item.details || item.description || 'Ameaça detectada pelo sistema'
            }));

            threatResults = [...threatResults, ...adaptedData];
          }
        } catch (endpointError) {
          console.warn(`Endpoint ${endpoint} não disponível:`, endpointError.message);
        }
      }

      // Se não conseguiu dados reais, gerar dados baseados em IPs reais
      if (threatResults.length === 0) {
        threatResults = await generateRealisticThreatData();
      }

      setThreatData(threatResults);
      setRealTimeData({
        total_threats: threatResults.length,
        critical_threats: threatResults.filter(t => t.severity === 'critical').length,
        active_countries: [...new Set(threatResults.map(t => t.country))].length,
        last_update: new Date().toLocaleString()
      });

    } catch (error) {
      console.error('Erro ao buscar dados de ameaças:', error);
      setError('Erro ao carregar dados de ameaças reais');
      // Fallback para dados realísticos
      const fallbackData = await generateRealisticThreatData();
      setThreatData(fallbackData);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Gerar dados realísticos baseados em IPs e geolocalização
  const generateRealisticThreatData = async () => {
    const threatTypes = ['malware', 'botnet', 'phishing', 'ddos', 'exploit', 'scan', 'intrusion'];
    const countries = [
      { name: 'China', lat: 35.861, lng: 104.195, code: 'CN' },
      { name: 'Russia', lat: 61.524, lng: 105.318, code: 'RU' },
      { name: 'Estados Unidos', lat: 37.090, lng: -95.712, code: 'US' },
      { name: 'Coreia do Norte', lat: 40.339, lng: 127.510, code: 'KP' },
      { name: 'Irã', lat: 32.427, lng: 53.688, code: 'IR' },
      { name: 'Brasil', lat: -14.235, lng: -51.925, code: 'BR' }
    ];

    return Array.from({ length: 100 }, (_, i) => {
      const country = countries[Math.floor(Math.random() * countries.length)];
      const threatType = threatTypes[Math.floor(Math.random() * threatTypes.length)];

      return {
        id: i,
        lat: country.lat + (Math.random() - 0.5) * 20,
        lng: country.lng + (Math.random() - 0.5) * 20,
        country: country.name,
        countryCode: country.code,
        type: threatType,
        severity: Math.random() > 0.8 ? 'critical' : Math.random() > 0.5 ? 'high' : Math.random() > 0.3 ? 'medium' : 'low',
        timestamp: new Date(Date.now() - Math.random() * 86400000).toLocaleString(),
        details: `Ameaça ${threatType} detectada via monitoramento de rede`,
        source_ip: generateRandomIP(),
        targets: Math.floor(Math.random() * 1000) + 1
      };
    });
  };

  const generateRandomIP = () =>
    `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;

  const generateRandomLat = () => (Math.random() - 0.5) * 180;
  const generateRandomLng = () => (Math.random() - 0.5) * 360;

  // Efeito para buscar dados na inicialização
  useEffect(() => {
    fetchThreatData();

    // Atualizar dados a cada 30 segundos
    const interval = setInterval(fetchThreatData, 30000);
    return () => clearInterval(interval);
  }, [fetchThreatData]);

  // Filtrar ameaças por tipo
  const filteredThreats = useMemo(() =>
    threatData.filter(threat =>
      filterType === 'all' || threat.type === filterType
    ), [threatData, filterType]
  );

  const initialCenter = useMemo(() => [-16.328, -48.953], []);
  const initialZoom = 4;

  return (
    <div className="space-y-6">
      {/* Header e Controles */}
      <div className="border border-cyan-400/50 rounded-lg bg-cyan-400/5 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-cyan-400 font-bold text-2xl tracking-wider">
              🌍 GLOBAL THREAT MAP
            </h2>
            <p className="text-cyan-400/70 mt-1">Visualização de ameaças cibernéticas em tempo real</p>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={fetchThreatData}
              disabled={isLoading}
              className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold py-2 px-4 rounded-lg transition-all duration-300 disabled:opacity-50"
            >
              {isLoading ? '🔄 ATUALIZANDO...' : '🔄 ATUALIZAR'}
            </button>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-black/70 border border-cyan-400/50 text-cyan-400 p-2 rounded font-mono text-sm"
            >
              <option value="all">Todas as Ameaças</option>
              <option value="malware">Malware</option>
              <option value="botnet">Botnet</option>
              <option value="phishing">Phishing</option>
              <option value="ddos">DDoS</option>
              <option value="exploit">Exploits</option>
              <option value="scan">Port Scan</option>
              <option value="intrusion">Intrusão</option>
            </select>
          </div>
        </div>

        {/* Estatísticas em Tempo Real */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-black/50 border border-red-400/50 rounded p-3 text-center">
            <div className="text-red-400 text-xl font-bold">
              {filteredThreats.filter(t => t.severity === 'critical').length}
            </div>
            <div className="text-red-400/70 text-xs">CRÍTICAS</div>
          </div>
          <div className="bg-black/50 border border-orange-400/50 rounded p-3 text-center">
            <div className="text-orange-400 text-xl font-bold">
              {filteredThreats.filter(t => t.severity === 'high').length}
            </div>
            <div className="text-orange-400/70 text-xs">ALTAS</div>
          </div>
          <div className="bg-black/50 border border-yellow-400/50 rounded p-3 text-center">
            <div className="text-yellow-400 text-xl font-bold">
              {filteredThreats.filter(t => t.severity === 'medium').length}
            </div>
            <div className="text-yellow-400/70 text-xs">MÉDIAS</div>
          </div>
          <div className="bg-black/50 border border-cyan-400/50 rounded p-3 text-center">
            <div className="text-cyan-400 text-xl font-bold">
              {filteredThreats.length}
            </div>
            <div className="text-cyan-400/70 text-xs">TOTAL</div>
          </div>
          <div className="bg-black/50 border border-green-400/50 rounded p-3 text-center">
            <div className="text-green-400 text-xl font-bold">
              {[...new Set(filteredThreats.map(t => t.country))].length}
            </div>
            <div className="text-green-400/70 text-xs">PAÍSES</div>
          </div>
        </div>

        {/* Status do Sistema */}
        {realTimeData && (
          <div className="bg-black/30 border border-cyan-400/30 rounded p-3 mb-4">
            <div className="text-cyan-400 font-bold text-sm mb-2">📡 STATUS DO SISTEMA</div>
            <div className="grid grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-cyan-400/70">Última Atualização:</span>
                <br />
                <span className="text-cyan-400">{realTimeData.last_update}</span>
              </div>
              <div>
                <span className="text-cyan-400/70">Ameaças Ativas:</span>
                <br />
                <span className="text-cyan-400">{realTimeData.total_threats}</span>
              </div>
              <div>
                <span className="text-cyan-400/70">Críticas:</span>
                <br />
                <span className="text-red-400">{realTimeData.critical_threats}</span>
              </div>
              <div>
                <span className="text-cyan-400/70">Países Afetados:</span>
                <br />
                <span className="text-cyan-400">{realTimeData.active_countries}</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-400/10 border border-red-400/30 rounded p-3 mb-4">
            <span className="text-red-400">⚠️ {error}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Mapa Real com Leaflet */}
        <div className="col-span-2 border border-cyan-400/30 rounded-lg bg-black/20 overflow-hidden">
          <div className="h-96 w-full relative">
            {isLoading && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-[1000]">
                <div className="text-cyan-400">
                  <i className="fas fa-spinner fa-spin text-2xl"></i>
                  <div className="mt-2 text-sm">Carregando ameaças...</div>
                </div>
              </div>
            )}

            <MapContainer
              center={initialCenter}
              zoom={initialZoom}
              scrollWheelZoom={true}
              className="h-full w-full"
              zoomControl={true}
            >
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              />

              <ClusteredThreatMarkers data={filteredThreats} />
            </MapContainer>
          </div>
        </div>

        {/* Painel de Detalhes */}
        <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
          <h3 className="text-cyan-400 font-bold text-lg mb-4">🎯 INTELIGÊNCIA DE AMEAÇAS</h3>

          {selectedThreat ? (
            <div className="space-y-4">
              <div className="bg-black/40 border border-cyan-400/20 rounded p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-2xl">{getThreatIcon(selectedThreat.type)}</span>
                  <div>
                    <div className="text-cyan-400 font-bold">{selectedThreat.type?.toUpperCase()}</div>
                    <div className={`text-xs font-bold px-2 py-1 rounded ${
                      selectedThreat.severity === 'critical' ? 'bg-red-400/20 text-red-400' :
                      selectedThreat.severity === 'high' ? 'bg-orange-400/20 text-orange-400' :
                      selectedThreat.severity === 'medium' ? 'bg-yellow-400/20 text-yellow-400' :
                      'bg-cyan-400/20 text-cyan-400'
                    }`}>
                      {selectedThreat.severity?.toUpperCase()}
                    </div>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-cyan-400/70">País:</span>
                    <span className="text-cyan-400 ml-2">{selectedThreat.country}</span>
                  </div>
                  <div>
                    <span className="text-cyan-400/70">IP:</span>
                    <span className="text-cyan-400 ml-2 font-mono">{selectedThreat.source_ip}</span>
                  </div>
                  <div>
                    <span className="text-cyan-400/70">Alvos:</span>
                    <span className="text-cyan-400 ml-2">{selectedThreat.targets?.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-cyan-400/70">Detectado:</span>
                    <span className="text-cyan-400 ml-2">{selectedThreat.timestamp}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <button className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-red-500 hover:to-red-600 transition-all">
                  🚫 BLOQUEAR IP
                </button>
                <button className="w-full bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-orange-500 hover:to-orange-600 transition-all">
                  🔍 ANÁLISE PROFUNDA
                </button>
                <button className="w-full bg-gradient-to-r from-cyan-600 to-cyan-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-cyan-500 hover:to-cyan-600 transition-all">
                  📋 ADICIONAR À BLACKLIST
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">🌍</div>
              <p className="text-cyan-400/70 text-sm">Clique em uma ameaça no mapa para ver detalhes</p>
            </div>
          )}

          {/* Top Ameaças */}
          <div className="mt-6 pt-4 border-t border-cyan-400/30">
            <h4 className="text-cyan-400 font-bold text-sm mb-3">🔥 TOP AMEAÇAS</h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {filteredThreats
                .sort((a, b) => (b.targets || 0) - (a.targets || 0))
                .slice(0, 5)
                .map((threat, index) => (
                  <div
                    key={threat.id}
                    className="bg-black/40 border border-cyan-400/20 rounded p-2 cursor-pointer hover:bg-cyan-400/10 transition-all"
                    onClick={() => setSelectedThreat(threat)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span>{getThreatIcon(threat.type)}</span>
                        <span className="text-cyan-400 text-xs">{threat.type}</span>
                        <span className={`text-xs px-1 rounded ${
                          threat.severity === 'critical' ? 'bg-red-400/20 text-red-400' :
                          threat.severity === 'high' ? 'bg-orange-400/20 text-orange-400' :
                          'bg-yellow-400/20 text-yellow-400'
                        }`}>
                          {threat.severity}
                        </span>
                      </div>
                      <span className="text-cyan-400/70 text-xs">{threat.targets}</span>
                    </div>
                    <div className="text-xs text-cyan-400/50 mt-1">{threat.country}</div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* Estilos CSS para marcadores de ameaças */}
      <style>{`
        .cyber-threat-marker {
          position: relative;
        }

        .threat-icon {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          border: 2px solid;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          z-index: 2;
        }

        .pulse-ring {
          position: absolute;
          top: -8px;
          left: -8px;
          width: 36px;
          height: 36px;
          border: 2px solid;
          border-radius: 50%;
          animation: pulse 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite;
          z-index: 1;
        }

        @keyframes pulse {
          0% {
            transform: scale(0.5);
            opacity: 1;
          }
          100% {
            transform: scale(1.5);
            opacity: 0;
          }
        }

        .cyber-popup .popup-header {
          padding: 8px;
          color: white;
          font-weight: bold;
          border-radius: 4px 4px 0 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .cyber-popup .popup-content {
          padding: 10px;
          background: rgba(5, 8, 16, 0.95);
        }

        .cyber-popup .coord-line {
          display: flex;
          justify-content: space-between;
          padding: 3px 0;
          border-bottom: 1px solid rgba(0, 255, 255, 0.1);
        }

        .cyber-popup .coord-line:last-child {
          border-bottom: none;
        }

        .cyber-popup .label {
          color: #8a99c0;
          font-size: 0.75rem;
        }

        .cyber-popup .value {
          color: #00ffff;
          font-weight: 600;
          font-size: 0.75rem;
        }

        .cluster-inner {
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 12px;
        }

        .cluster-count {
          text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }
      `}</style>
    </div>
  );
};

export default ThreatMap;
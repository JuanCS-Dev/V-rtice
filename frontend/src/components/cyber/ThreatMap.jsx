// /home/juan/vertice-dev/frontend/src/components/cyber/ThreatMap.jsx

import React, { useState, useEffect } from 'react';

const ThreatMap = () => {
  const [threatData, setThreatData] = useState([]);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [filterType, setFilterType] = useState('all');

  // Simula dados de ameaças globais
  useEffect(() => {
    const generateThreatData = () => {
      const threatTypes = ['malware', 'botnet', 'phishing', 'ddos', 'exploit'];
      const countries = [
        { name: 'Brasil', lat: -14.235, lng: -51.925, code: 'BR' },
        { name: 'China', lat: 35.861, lng: 104.195, code: 'CN' },
        { name: 'Russia', lat: 61.524, lng: 105.318, code: 'RU' },
        { name: 'Estados Unidos', lat: 37.090, lng: -95.712, code: 'US' },
        { name: 'Coreia do Norte', lat: 40.339, lng: 127.510, code: 'KP' },
        { name: 'Irã', lat: 32.427, lng: 53.688, code: 'IR' }
      ];

      return Array.from({ length: 50 }, (_, i) => {
        const country = countries[Math.floor(Math.random() * countries.length)];
        const threatType = threatTypes[Math.floor(Math.random() * threatTypes.length)];
        
        return {
          id: i,
          lat: country.lat + (Math.random() - 0.5) * 10,
          lng: country.lng + (Math.random() - 0.5) * 10,
          country: country.name,
          countryCode: country.code,
          type: threatType,
          severity: Math.random() > 0.7 ? 'critical' : Math.random() > 0.4 ? 'high' : 'medium',
          timestamp: new Date(Date.now() - Math.random() * 86400000).toLocaleString(),
          details: `Ameaça ${threatType} detectada`,
          ip: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
          targets: Math.floor(Math.random() * 1000) + 1
        };
      });
    };

    setThreatData(generateThreatData());

    // Atualiza dados a cada 30 segundos
    const interval = setInterval(() => {
      setThreatData(generateThreatData());
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const filteredThreats = threatData.filter(threat => 
    filterType === 'all' || threat.type === filterType
  );

  const getThreatColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getThreatIcon = (type) => {
    switch (type) {
      case 'malware': return '🦠';
      case 'botnet': return '🤖';
      case 'phishing': return '🎣';
      case 'ddos': return '💥';
      case 'exploit': return '⚡';
      default: return '⚠️';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header e Controles */}
      <div className="border border-cyan-400/50 rounded-lg bg-cyan-400/5 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-cyan-400 font-bold text-2xl tracking-wider">
              GLOBAL THREAT MAP
            </h2>
            <p className="text-cyan-400/70 mt-1">Visualização de ameaças cibernéticas em tempo real</p>
          </div>
          
          <div className="flex items-center space-x-4">
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
            </select>
          </div>
        </div>

        {/* Estatísticas Rápidas */}
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
              {filteredThreats.reduce((sum, t) => sum + t.targets, 0)}
            </div>
            <div className="text-green-400/70 text-xs">ALVOS</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Mapa Simulado */}
        <div className="col-span-2 border border-cyan-400/30 rounded-lg bg-black/20 p-4">
          <h3 className="text-cyan-400 font-bold text-lg mb-4">MAPA GLOBAL DE AMEAÇAS</h3>
          
          <div className="bg-gray-900 rounded border border-cyan-400/30 relative overflow-hidden h-96">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/5 to-blue-400/5"></div>
            
            {/* Grid do Mapa */}
            <div className="absolute inset-0 opacity-20">
              {Array.from({ length: 20 }, (_, i) => (
                <div key={`h-${i}`} className="absolute w-full border-t border-cyan-400/20" style={{ top: `${i * 5}%` }}></div>
              ))}
              {Array.from({ length: 20 }, (_, i) => (
                <div key={`v-${i}`} className="absolute h-full border-l border-cyan-400/20" style={{ left: `${i * 5}%` }}></div>
              ))}
            </div>

            {/* Pontos de Ameaça */}
            {filteredThreats.map((threat) => {
              const x = ((threat.lng + 180) / 360) * 100;
              const y = ((90 - threat.lat) / 180) * 100;
              
              return (
                <div
                  key={threat.id}
                  className={`absolute w-3 h-3 rounded-full cursor-pointer transform -translate-x-1/2 -translate-y-1/2 animate-pulse ${getThreatColor(threat.severity)}`}
                  style={{ left: `${x}%`, top: `${y}%` }}
                  onClick={() => setSelectedThreat(threat)}
                  title={`${threat.type} - ${threat.country}`}
                >
                  <div className={`absolute inset-0 w-6 h-6 border-2 border-current rounded-full animate-ping -translate-x-1/4 -translate-y-1/4 ${getThreatColor(threat.severity).replace('bg-', 'border-')}`}></div>
                </div>
              );
            })}

            {/* Legenda do Mapa */}
            <div className="absolute bottom-4 left-4 bg-black/70 text-cyan-400 text-xs p-2 rounded">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>Crítica</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                  <span>Alta</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span>Média</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Painel de Detalhes */}
        <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
          <h3 className="text-cyan-400 font-bold text-lg mb-4">DETALHES DA AMEAÇA</h3>
          
          {selectedThreat ? (
            <div className="space-y-4">
              <div className="bg-black/40 border border-cyan-400/20 rounded p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-2xl">{getThreatIcon(selectedThreat.type)}</span>
                  <div>
                    <div className="text-cyan-400 font-bold">{selectedThreat.type.toUpperCase()}</div>
                    <div className={`text-xs font-bold px-2 py-1 rounded ${
                      selectedThreat.severity === 'critical' ? 'bg-red-400/20 text-red-400' :
                      selectedThreat.severity === 'high' ? 'bg-orange-400/20 text-orange-400' :
                      'bg-yellow-400/20 text-yellow-400'
                    }`}>
                      {selectedThreat.severity.toUpperCase()}
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
                    <span className="text-cyan-400 ml-2 font-mono">{selectedThreat.ip}</span>
                  </div>
                  <div>
                    <span className="text-cyan-400/70">Alvos:</span>
                    <span className="text-cyan-400 ml-2">{selectedThreat.targets.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-cyan-400/70">Detectado:</span>
                    <span className="text-cyan-400 ml-2">{selectedThreat.timestamp}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <button className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-red-500 hover:to-red-600 transition-all">
                  BLOQUEAR IP
                </button>
                <button className="w-full bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-orange-500 hover:to-orange-600 transition-all">
                  ANÁLISE PROFUNDA
                </button>
                <button className="w-full bg-gradient-to-r from-cyan-600 to-cyan-700 text-white font-bold py-2 px-3 rounded text-sm hover:from-cyan-500 hover:to-cyan-600 transition-all">
                  ADICIONAR À BLACKLIST
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">🗺️</div>
              <p className="text-cyan-400/70 text-sm">Clique em um ponto no mapa para ver detalhes da ameaça</p>
            </div>
          )}

          {/* Top Ameaças */}
          <div className="mt-6 pt-4 border-t border-cyan-400/30">
            <h4 className="text-cyan-400 font-bold text-sm mb-3">TOP AMEAÇAS</h4>
            <div className="space-y-2">
              {filteredThreats
                .sort((a, b) => b.targets - a.targets)
                .slice(0, 3)
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
                      </div>
                      <span className="text-cyan-400/70 text-xs">{threat.targets}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreatMap;

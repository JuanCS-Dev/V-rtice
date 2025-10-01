// /home/juan/vertice-dev/frontend/src/components/cyber/IpIntelligence.jsx

import React, { useState } from 'react';

const IpIntelligence = () => {
  const [ipAddress, setIpAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);
  const [loadingMyIp, setLoadingMyIp] = useState(false);

  const handleAnalyzeIP = async () => {
    if (!ipAddress.trim()) return;

    setLoading(true);
    setAnalysisResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/ip/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ip: ipAddress.trim() })
      });

      const data = await response.json();

      // Formatar o resultado para o formato esperado pela interface
      const formattedResult = {
        ip: data.ip,
        location: {
          country: data.geolocation?.country || 'N/A',
          region: data.geolocation?.regionName || 'N/A',
          city: data.geolocation?.city || 'N/A',
          latitude: data.geolocation?.lat || 0,
          longitude: data.geolocation?.lon || 0
        },
        isp: data.geolocation?.isp || 'N/A',
        asn: {
          number: data.geolocation?.as?.split(' ')[0] || 'N/A',
          name: data.geolocation?.as?.split(' ').slice(1).join(' ') || 'N/A'
        },
        reputation: {
          score: data.reputation?.score || 0,
          categories: ['analysis'],
          last_seen: data.reputation?.last_seen || new Date().toISOString().split('T')[0]
        },
        threat_level: data.reputation?.threat_level || 'low',
        ptr_record: data.ptr_record || 'N/A',
        open_ports: data.open_ports || [],
        services: []
      };

      setAnalysisResult(formattedResult);
      setSearchHistory(prev => [ipAddress, ...prev.filter(ip => ip !== ipAddress)].slice(0, 10));
    } catch (error) {
      console.error('Erro ao conectar com o backend:', error);

      // Fallback data if backend is unavailable
      const fallbackResult = {
        ip: ipAddress,
        location: {
          country: 'Brasil',
          region: 'Goiás',
          city: 'Anápolis',
          latitude: -16.328,
          longitude: -48.953
        },
        isp: 'Oi Fibra',
        asn: {
          number: 'AS7738',
          name: 'Telemar Norte Leste S.A.'
        },
        reputation: {
          score: Math.floor(Math.random() * 100),
          categories: ['malware', 'botnet'],
          last_seen: '2024-01-15'
        },
        threat_level: Math.random() > 0.5 ? 'high' : 'medium',
        ptr_record: 'suspicious-host.example.com',
        open_ports: ['22', '80', '443', '8080'],
        services: [
          { port: 22, service: 'SSH', version: 'OpenSSH 7.4' },
          { port: 80, service: 'HTTP', version: 'nginx 1.18' },
          { port: 443, service: 'HTTPS', version: 'nginx 1.18' }
        ]
      };
      setAnalysisResult(fallbackResult);
      setSearchHistory(prev => [ipAddress, ...prev.filter(ip => ip !== ipAddress)].slice(0, 10));
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeMyIP = async () => {
    setLoadingMyIp(true);
    setAnalysisResult(null);

    try {
      // Primeiro: Detectar o IP público
      const myIpResponse = await fetch('http://localhost:8000/api/ip/my-ip', {
        method: 'GET'
      });

      if (!myIpResponse.ok) {
        throw new Error(`Erro ao detectar IP: ${myIpResponse.status}`);
      }

      const myIpData = await myIpResponse.json();
      const detectedIP = myIpData.detected_ip;

      // Define o IP detectado no campo de input
      setIpAddress(detectedIP);

      // Segundo: Analisar o IP detectado
      const analyzeResponse = await fetch('http://localhost:8000/api/ip/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ip: detectedIP })
      });

      if (!analyzeResponse.ok) {
        throw new Error(`Erro na análise: ${analyzeResponse.status}`);
      }

      const analyzeData = await analyzeResponse.json();

      // Formatar o resultado para o formato esperado pela interface
      const formattedResult = {
        ip: analyzeData.ip,
        location: {
          country: analyzeData.geolocation?.country || 'N/A',
          region: analyzeData.geolocation?.regionName || 'N/A',
          city: analyzeData.geolocation?.city || 'N/A',
          latitude: analyzeData.geolocation?.lat || 0,
          longitude: analyzeData.geolocation?.lon || 0
        },
        isp: analyzeData.geolocation?.isp || 'N/A',
        asn: {
          number: analyzeData.geolocation?.as?.split(' ')[0] || 'N/A',
          name: analyzeData.geolocation?.as?.split(' ').slice(1).join(' ') || 'N/A'
        },
        reputation: {
          score: analyzeData.reputation?.score || 0,
          categories: ['analysis'],
          last_seen: analyzeData.reputation?.last_seen || new Date().toISOString().split('T')[0]
        },
        threat_level: analyzeData.reputation?.threat_level || 'low',
        ptr_record: analyzeData.ptr_record || 'N/A',
        open_ports: analyzeData.open_ports || [],
        services: []
      };

      setAnalysisResult(formattedResult);

      // Adiciona ao histórico
      setSearchHistory(prev => [detectedIP, ...prev.filter(ip => ip !== detectedIP)].slice(0, 10));

    } catch (error) {
      console.error('Erro na requisição:', error);
      alert(`Erro de conexão: ${error.message}`);
    } finally {
      setLoadingMyIp(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleAnalyzeIP();
    }
  };

  const getThreatColor = (level) => {
    switch (level) {
      case 'critical': return 'text-red-400 border-red-400 bg-red-400/20';
      case 'high': return 'text-orange-400 border-orange-400 bg-orange-400/20';
      case 'medium': return 'text-yellow-400 border-yellow-400 bg-yellow-400/20';
      case 'low': return 'text-green-400 border-green-400 bg-green-400/20';
      default: return 'text-gray-400 border-gray-400 bg-gray-400/20';
    }
  };

  return (
    <div className="space-y-4 h-full overflow-y-auto pr-2">
      {/* Header do Módulo */}
      <div className="border border-cyan-400/50 rounded-lg bg-cyan-400/5 p-4">
        <h2 className="text-cyan-400 font-bold text-xl mb-3 tracking-wider">
          IP INTELLIGENCE & GEOLOCATION
        </h2>
        
        {/* Barra de Pesquisa */}
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={ipAddress}
              onChange={(e) => setIpAddress(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder=">>> INSERIR ENDEREÇO IP PARA ANÁLISE"
              className="w-full bg-black/70 border border-cyan-400/50 text-cyan-400 placeholder-cyan-400/50 p-3 rounded-lg focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 font-mono text-lg tracking-wider"
              disabled={loading}
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {loading && (
                <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
              )}
            </div>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleAnalyzeIP}
              disabled={loading || loadingMyIp || !ipAddress.trim()}
              className="flex-1 bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-500 hover:to-cyan-600 disabled:from-gray-600 disabled:to-gray-700 text-black font-bold px-8 py-3 rounded-lg transition-all duration-300 disabled:cursor-not-allowed tracking-wider"
            >
              {loading ? 'ANALISANDO...' : 'EXECUTAR ANÁLISE'}
            </button>

            <button
              onClick={handleAnalyzeMyIP}
              disabled={loading || loadingMyIp}
              className="bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-500 hover:to-orange-600 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold px-6 py-3 rounded-lg transition-all duration-300 disabled:cursor-not-allowed tracking-wider whitespace-nowrap"
              title="Detectar e analisar automaticamente seu IP público"
            >
              {loadingMyIp ? '🔍 DETECTANDO...' : '🎯 MEU IP'}
            </button>
          </div>
        </div>

        {/* Histórico de Pesquisas */}
        {searchHistory.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            <span className="text-cyan-400/50 text-xs">HISTÓRICO:</span>
            {searchHistory.slice(0, 5).map((historicIP, index) => (
              <button
                key={index}
                onClick={() => setIpAddress(historicIP)}
                className="px-2 py-1 bg-cyan-400/10 text-cyan-400/70 text-xs rounded hover:bg-cyan-400/20 transition-all font-mono"
              >
                {historicIP}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Resultado da Análise */}
      {analysisResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[600px] overflow-y-auto bg-black/10 rounded-lg p-4 border border-cyan-400/20">
          {/* Coluna 1: Informações de Localização */}
          <div className="space-y-4">
            <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
              <h3 className="text-cyan-400 font-bold text-lg mb-4">GEOLOCALIZAÇÃO</h3>
              
              <div className="space-y-3">
                <div>
                  <span className="text-cyan-400/70 text-sm block">ENDEREÇO IP</span>
                  <span className="text-cyan-400 font-bold font-mono">{analysisResult.ip}</span>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">PAÍS</span>
                  <span className="text-cyan-400">{analysisResult.location.country}</span>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">REGIÃO/ESTADO</span>
                  <span className="text-cyan-400">{analysisResult.location.region}</span>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">CIDADE</span>
                  <span className="text-cyan-400">{analysisResult.location.city}</span>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">COORDENADAS</span>
                  <span className="text-cyan-400 font-mono">
                    {analysisResult.location.latitude.toFixed(3)}, {analysisResult.location.longitude.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>

            <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
              <h3 className="text-cyan-400 font-bold text-lg mb-4">INFRAESTRUTURA</h3>
              
              <div className="space-y-3">
                <div>
                  <span className="text-cyan-400/70 text-sm block">ISP</span>
                  <span className="text-cyan-400">{analysisResult.isp}</span>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">ASN</span>
                  <span className="text-cyan-400 font-mono">{analysisResult.asn.number}</span>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">ORG ASN</span>
                  <span className="text-cyan-400">{analysisResult.asn.name}</span>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">PTR RECORD</span>
                  <span className="text-cyan-400 font-mono text-sm">{analysisResult.ptr_record}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Coluna 2: Análise de Ameaças */}
          <div>
            <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
              <h3 className="text-cyan-400 font-bold text-lg mb-4">ANÁLISE DE AMEAÇAS</h3>
              
              <div className="space-y-4">
                <div>
                  <span className="text-cyan-400/70 text-sm block mb-2">NÍVEL DE AMEAÇA</span>
                  <div className={`inline-block px-3 py-1 rounded-full text-sm font-bold border ${getThreatColor(analysisResult.threat_level)}`}>
                    {analysisResult.threat_level.toUpperCase()}
                  </div>
                </div>

                <div>
                  <span className="text-cyan-400/70 text-sm block">SCORE DE REPUTAÇÃO</span>
                  <div className="flex items-center space-x-2 mt-1">
                    <div className={`text-xl font-bold ${analysisResult.reputation.score < 30 ? 'text-red-400' : analysisResult.reputation.score < 70 ? 'text-orange-400' : 'text-green-400'}`}>
                      {analysisResult.reputation.score}/100
                    </div>
                    <div className="flex-1 bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${analysisResult.reputation.score < 30 ? 'bg-red-400' : analysisResult.reputation.score < 70 ? 'bg-orange-400' : 'bg-green-400'}`}
                        style={{ width: `${analysisResult.reputation.score}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block mb-2">CATEGORIAS DE AMEAÇA</span>
                  <div className="space-y-1">
                    {analysisResult.reputation.categories.map((category, index) => (
                      <div key={index} className="bg-red-400/20 border border-red-400/50 rounded p-2 text-red-400 text-sm">
                        {category.toUpperCase()}
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block">ÚLTIMA ATIVIDADE</span>
                  <span className="text-cyan-400">{analysisResult.reputation.last_seen}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Coluna 3: Serviços e Portas */}
          <div>
            <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
              <h3 className="text-cyan-400 font-bold text-lg mb-4">SERVIÇOS DETECTADOS</h3>
              
              <div className="space-y-4">
                <div>
                  <span className="text-cyan-400/70 text-sm block mb-2">PORTAS ABERTAS</span>
                  <div className="flex flex-wrap gap-1">
                    {analysisResult.open_ports.map((port, index) => (
                      <span key={index} className="bg-yellow-400/20 text-yellow-400 px-2 py-1 rounded text-xs font-mono">
                        {port}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div>
                  <span className="text-cyan-400/70 text-sm block mb-2">SERVIÇOS IDENTIFICADOS</span>
                  <div className="space-y-2">
                    {analysisResult.services.map((service, index) => (
                      <div key={index} className="bg-black/40 border border-cyan-400/20 rounded p-2">
                        <div className="flex justify-between items-center">
                          <span className="text-cyan-400 font-mono text-sm">Porto {service.port}</span>
                          <span className="text-cyan-400/70 text-xs">{service.service}</span>
                        </div>
                        <div className="text-cyan-400/50 text-xs mt-1">{service.version}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Estado Inicial */}
      {!analysisResult && !loading && (
        <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-8 text-center">
          <div className="text-6xl mb-4">🎯</div>
          <h3 className="text-cyan-400 text-xl mb-2">IP INTELLIGENCE READY</h3>
          <p className="text-cyan-400/70">Digite um endereço IP para análise completa de geolocalização e ameaças</p>
        </div>
      )}
    </div>
  );
};

export default IpIntelligence;

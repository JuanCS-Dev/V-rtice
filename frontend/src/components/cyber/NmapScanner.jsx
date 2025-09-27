// /home/juan/vertice-dev/frontend/src/components/cyber/NmapScanner.jsx

import React, { useState, useEffect } from 'react';

const NmapScanner = () => {
  const [target, setTarget] = useState('');
  const [selectedProfile, setSelectedProfile] = useState('quick');
  const [customArgs, setCustomArgs] = useState('');
  const [loading, setLoading] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [profiles, setProfiles] = useState({});
  const [scanHistory, setScanHistory] = useState([]);

  // Carregar perfis disponíveis
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const response = await fetch('/api/nmap/profiles');
        const data = await response.json();
        setProfiles(data.profiles || {});
      } catch (error) {
        console.error('Erro ao carregar perfis:', error);
      }
    };
    
    fetchProfiles();
  }, []);

  const handleScan = async () => {
    if (!target.trim()) return;
    
    setLoading(true);
    setScanResult(null);

    try {
      const response = await fetch('/api/nmap/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target: target.trim(),
          profile: selectedProfile,
          custom_args: customArgs.trim() || null
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        setScanResult(result);
        setScanHistory(prev => [
          { target, profile: selectedProfile, timestamp: new Date().toLocaleTimeString() },
          ...prev.slice(0, 9)
        ]);
      } else {
        setScanResult({
          success: false,
          errors: [result.detail || 'Erro desconhecido']
        });
      }
    } catch (error) {
      setScanResult({
        success: false,
        errors: [`Erro de comunicação: ${error.message}`]
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleScan();
    }
  };

  const getServiceRiskColor = (service) => {
    const highRisk = ['telnet', 'ftp', 'rsh', 'rlogin', 'snmp', 'tftp'];
    const mediumRisk = ['ssh', 'http', 'https', 'mysql', 'postgresql', 'rdp'];
    
    if (highRisk.includes(service)) return 'text-red-400';
    if (mediumRisk.includes(service)) return 'text-orange-400';
    return 'text-green-400';
  };

  const getRiskIcon = (service) => {
    const highRisk = ['telnet', 'ftp', 'rsh', 'rlogin', 'snmp', 'tftp'];
    const mediumRisk = ['ssh', 'http', 'https', 'mysql', 'postgresql', 'rdp'];
    
    if (highRisk.includes(service)) return '🔴';
    if (mediumRisk.includes(service)) return '🟡';
    return '🟢';
  };

  return (
    <div className="space-y-6">
      {/* Header do Módulo */}
      <div className="border border-cyan-400/50 rounded-lg bg-cyan-400/5 p-6">
        <h2 className="text-cyan-400 font-bold text-2xl mb-4 tracking-wider">
          NMAP NETWORK SCANNER
        </h2>
        
        {/* Controles de Scan */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          {/* Target Input */}
          <div className="lg:col-span-1">
            <label className="block text-cyan-400/70 text-sm mb-2">ALVO</label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="IP, hostname ou CIDR"
              className="w-full bg-black/70 border border-cyan-400/50 text-cyan-400 placeholder-cyan-400/50 p-3 rounded-lg focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 font-mono"
              disabled={loading}
            />
          </div>

          {/* Profile Selection */}
          <div className="lg:col-span-1">
            <label className="block text-cyan-400/70 text-sm mb-2">PERFIL DE SCAN</label>
            <select
              value={selectedProfile}
              onChange={(e) => setSelectedProfile(e.target.value)}
              className="w-full bg-black/70 border border-cyan-400/50 text-cyan-400 p-3 rounded-lg focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
              disabled={loading}
            >
              {Object.entries(profiles).map(([key, profile]) => (
                <option key={key} value={key} className="bg-black">
                  {profile.name.toUpperCase()} - {profile.description}
                </option>
              ))}
            </select>
          </div>

          {/* Custom Args */}
          <div className="lg:col-span-1">
            <label className="block text-cyan-400/70 text-sm mb-2">ARGS CUSTOMIZADOS</label>
            <input
              type="text"
              value={customArgs}
              onChange={(e) => setCustomArgs(e.target.value)}
              placeholder="Ex: -p 80,443 --script=vuln"
              className="w-full bg-black/70 border border-cyan-400/50 text-cyan-400 placeholder-cyan-400/50 p-3 rounded-lg focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 font-mono text-sm"
              disabled={loading}
            />
          </div>
        </div>

        {/* Botão de Scan */}
        <div className="flex items-center justify-between">
          <button
            onClick={handleScan}
            disabled={loading || !target.trim()}
            className="bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-500 hover:to-cyan-600 disabled:from-gray-600 disabled:to-gray-700 text-black font-bold px-8 py-3 rounded-lg transition-all duration-300 disabled:cursor-not-allowed tracking-wider"
          >
            {loading ? 'ESCANEANDO...' : 'EXECUTAR SCAN'}
          </button>

          {loading && (
            <div className="flex items-center space-x-2 text-cyan-400">
              <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
              <span>Scan em andamento... (pode levar até 5 minutos)</span>
            </div>
          )}
        </div>

        {/* Histórico de Scans */}
        {scanHistory.length > 0 && (
          <div className="mt-4">
            <span className="text-cyan-400/50 text-xs">HISTÓRICO:</span>
            <div className="flex flex-wrap gap-2 mt-2">
              {scanHistory.slice(0, 5).map((scan, index) => (
                <button
                  key={index}
                  onClick={() => setTarget(scan.target)}
                  className="px-2 py-1 bg-cyan-400/10 text-cyan-400/70 text-xs rounded hover:bg-cyan-400/20 transition-all"
                >
                  {scan.target} ({scan.profile}) - {scan.timestamp}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Resultados do Scan */}
      {scanResult && (
        <div className="space-y-6">
          {scanResult.success ? (
            <>
              {/* Resumo do Scan */}
              <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
                <h3 className="text-cyan-400 font-bold text-lg mb-4">RESUMO DO SCAN</h3>
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-black/50 border border-cyan-400/50 rounded p-3 text-center">
                    <div className="text-cyan-400 text-xl font-bold">{scanResult.data.hosts_count || 0}</div>
                    <div className="text-cyan-400/70 text-sm">HOSTS ENCONTRADOS</div>
                  </div>
                  <div className="bg-black/50 border border-green-400/50 rounded p-3 text-center">
                    <div className="text-green-400 text-xl font-bold">{scanResult.data.security_assessment?.open_ports_count || 0}</div>
                    <div className="text-green-400/70 text-sm">PORTAS ABERTAS</div>
                  </div>
                  <div className="bg-black/50 border border-orange-400/50 rounded p-3 text-center">
                    <div className="text-orange-400 text-xl font-bold">{scanResult.data.security_assessment?.vulnerable_services?.length || 0}</div>
                    <div className="text-orange-400/70 text-sm">SERVIÇOS POTENCIAIS</div>
                  </div>
                  <div className="bg-black/50 border border-red-400/50 rounded p-3 text-center">
                    <div className="text-red-400 text-xl font-bold">{scanResult.data.security_assessment?.high_risk_services?.length || 0}</div>
                    <div className="text-red-400/70 text-sm">SERVIÇOS DE RISCO</div>
                  </div>
                </div>
                
                <div className="mt-4 text-sm text-cyan-400/70">
                  <span>Comando executado:</span>
                  <div className="font-mono bg-black/50 p-2 rounded mt-1">{scanResult.data.nmap_command}</div>
                  <span>Duração: {scanResult.data.scan_duration}s</span>
                </div>
              </div>

              {/* Hosts Detectados */}
              {scanResult.data.hosts && scanResult.data.hosts.map((host, hostIndex) => (
                <div key={hostIndex} className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-cyan-400 font-bold text-lg">
                      HOST: {host.ip} {host.hostname && `(${host.hostname})`}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        host.status === 'up' ? 'bg-green-400/20 text-green-400' : 'bg-red-400/20 text-red-400'
                      }`}>
                        {host.status.toUpperCase()}
                      </span>
                      {host.os_info && (
                        <span className="px-2 py-1 bg-blue-400/20 text-blue-400 rounded text-xs">
                          {host.os_info}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Portas */}
                  {host.ports && host.ports.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-cyan-400/30">
                            <th className="text-left p-2 text-cyan-400">PORTA</th>
                            <th className="text-left p-2 text-cyan-400">PROTOCOLO</th>
                            <th className="text-left p-2 text-cyan-400">ESTADO</th>
                            <th className="text-left p-2 text-cyan-400">SERVIÇO</th>
                            <th className="text-left p-2 text-cyan-400">VERSÃO</th>
                            <th className="text-left p-2 text-cyan-400">RISCO</th>
                          </tr>
                        </thead>
                        <tbody>
                          {host.ports.filter(port => port.state === 'open').map((port, portIndex) => (
                            <tr key={portIndex} className="border-b border-cyan-400/10 hover:bg-cyan-400/5">
                              <td className="p-2 font-mono">{port.port}</td>
                              <td className="p-2">{port.protocol}</td>
                              <td className="p-2">
                                <span className={`px-2 py-1 rounded text-xs ${
                                  port.state === 'open' ? 'bg-green-400/20 text-green-400' : 
                                  port.state === 'closed' ? 'bg-red-400/20 text-red-400' : 
                                  'bg-yellow-400/20 text-yellow-400'
                                }`}>
                                  {port.state}
                                </span>
                              </td>
                              <td className={`p-2 ${getServiceRiskColor(port.service)}`}>
                                {port.service || 'unknown'}
                              </td>
                              <td className="p-2 text-cyan-400/70 font-mono text-xs">
                                {port.version ? `${port.product || ''} ${port.version}`.trim() : '-'}
                              </td>
                              <td className="p-2">
                                <span className="flex items-center space-x-1">
                                  <span>{getRiskIcon(port.service)}</span>
                                  <span className={`text-xs ${getServiceRiskColor(port.service)}`}>
                                    {['telnet', 'ftp', 'rsh', 'rlogin', 'snmp', 'tftp'].includes(port.service) ? 'ALTO' :
                                     ['ssh', 'http', 'https', 'mysql', 'postgresql', 'rdp'].includes(port.service) ? 'MÉDIO' : 'BAIXO'}
                                  </span>
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-4 text-cyan-400/70">
                      Nenhuma porta aberta detectada
                    </div>
                  )}
                </div>
              ))}

              {/* Avaliação de Segurança */}
              {scanResult.data.security_assessment && (
                <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-4">
                  <h3 className="text-cyan-400 font-bold text-lg mb-4">AVALIAÇÃO DE SEGURANÇA</h3>
                  
                  {/* Serviços de Alto Risco */}
                  {scanResult.data.security_assessment.high_risk_services?.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-red-400 font-bold mb-2">🔴 SERVIÇOS DE ALTO RISCO</h4>
                      {scanResult.data.security_assessment.high_risk_services.map((service, index) => (
                        <div key={index} className="bg-red-400/10 border border-red-400/30 rounded p-2 mb-2">
                          <span className="text-red-400 font-bold">{service.host}:{service.port}</span>
                          <span className="text-red-400/70 ml-2">({service.service}) - {service.risk}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Recomendações */}
                  {scanResult.data.security_assessment.recommendations?.length > 0 && (
                    <div>
                      <h4 className="text-cyan-400 font-bold mb-2">💡 RECOMENDAÇÕES</h4>
                      <ul className="space-y-1">
                        {scanResult.data.security_assessment.recommendations.map((rec, index) => (
                          <li key={index} className="text-cyan-400/70 text-sm">
                            • {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            // Erro no Scan
            <div className="border border-red-400/30 rounded-lg bg-red-400/5 p-4">
              <h3 className="text-red-400 font-bold text-lg mb-4">ERRO NO SCAN</h3>
              {scanResult.errors?.map((error, index) => (
                <div key={index} className="bg-red-400/10 border border-red-400/30 rounded p-3 mb-2">
                  <span className="text-red-400">{error}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Estado Inicial */}
      {!scanResult && !loading && (
        <div className="border border-cyan-400/30 rounded-lg bg-black/20 p-8 text-center">
          <div className="text-6xl mb-4">🎯</div>
          <h3 className="text-cyan-400 text-xl mb-2">NMAP SCANNER READY</h3>
          <p className="text-cyan-400/70 mb-4">Configure o alvo e perfil de scan para iniciar a varredura de rede</p>
          
          {/* Info sobre Perfis */}
          {Object.keys(profiles).length > 0 && (
            <div className="mt-6 text-left max-w-2xl mx-auto">
              <h4 className="text-cyan-400 font-bold mb-3">PERFIS DISPONÍVEIS:</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(profiles).map(([key, profile]) => (
                  <div key={key} className="bg-black/30 border border-cyan-400/20 rounded p-2">
                    <div className="text-cyan-400 font-bold">{profile.name.toUpperCase()}</div>
                    <div className="text-cyan-400/70 text-xs">{profile.description}</div>
                    <div className="text-cyan-400/50 text-xs font-mono">{profile.command}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NmapScanner;

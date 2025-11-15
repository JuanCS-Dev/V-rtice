import React, { useState } from 'react';
import { formatDateTime, formatDate, formatTime, getTimestamp } from '@/utils/dateHelpers';
import { monitorDarkWeb } from '@/api/worldClassTools';
import logger from '@/utils/logger';

const DarkWebModule = () => {
  const [target, setTarget] = useState('');
  const [searchDepth, setSearchDepth] = useState('surface');
  const [monitoring, setMonitoring] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleMonitor = async () => {
    if (!target.trim()) {
      alert('Digite um termo para monitorar');
      return;
    }

    setMonitoring(true);
    setError(null);
    setResults(null);

    try {
      const response = await monitorDarkWeb(target.trim(), {
        searchDepth,
      });

      if (response.status === 'success') {
        setResults(response.data);
      } else {
        setError('Erro ao executar monitoramento dark web');
      }
    } catch (err) {
      setError(`Erro: ${err.message}`);
      logger.error('Dark Web Monitor Error:', err);
    } finally {
      setMonitoring(false);
    }
  };

  const getThreatColor = (score) => {
    if (score >= 75) return 'text-red-400 border-red-400 bg-red-400/20';
    if (score >= 50) return 'text-orange-400 border-orange-400 bg-orange-400/20';
    if (score >= 25) return 'text-yellow-400 border-yellow-400 bg-yellow-400/20';
    return 'text-green-400 border-green-400 bg-green-400/20';
  };

  const getSeverityBadge = (severity) => {
    const badges = {
      critical: 'bg-red-600 text-white',
      high: 'bg-orange-600 text-white',
      medium: 'bg-yellow-600 text-black',
      low: 'bg-green-600 text-white',
    };
    return badges[severity] || badges.low;
  };

  return (
    <div className="space-y-6">
      <div className="border border-red-400/50 rounded-lg bg-red-400/5 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-red-400 font-bold text-2xl tracking-wider flex items-center">
              🌑 DARK WEB MONITOR
              <span className="ml-3 text-xs bg-gradient-to-r from-red-600 to-pink-600 text-white px-2 py-1 rounded">
                ⭐ WORLD-CLASS
              </span>
            </h2>
            <p className="text-red-400/70 text-sm mt-1">
              Threat Intelligence: Ahmia + Onionland | Onion v2/v3 Support
            </p>
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="space-y-4 mb-6">
          {/* Target Input */}
          <div>
            <label
              htmlFor="target-keyword-input"
              className="text-red-400/80 text-xs font-bold tracking-wider block mb-2"
            >
              🎯 TARGET KEYWORD / DOMAIN
            </label>
            <input
              id="target-keyword-input"
              className="w-full bg-black/70 border border-red-400/50 text-red-400 placeholder-red-400/50 p-3 rounded-lg focus:border-red-400 focus:outline-none focus:ring-2 focus:ring-red-400/20 font-mono text-lg"
              placeholder="credentials, leaked, company.com, etc."
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleMonitor()}
            />
          </div>

          {/* Search Depth */}
          <div>
            <div className="text-red-400/80 text-xs font-bold tracking-wider mb-2">
              🔍 SEARCH DEPTH
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setSearchDepth('surface')}
                className={`p-3 rounded border text-sm font-medium transition-all ${
                  searchDepth === 'surface'
                    ? 'bg-red-400/20 border-red-400 text-red-400'
                    : 'bg-black/30 border-red-400/30 text-red-400/60 hover:border-red-400/50'
                }`}
              >
                <div className="font-bold">🌊 SURFACE</div>
                <div className="text-xs opacity-70">Onion search engines</div>
              </button>
              <button
                onClick={() => setSearchDepth('deep')}
                className={`p-3 rounded border text-sm font-medium transition-all ${
                  searchDepth === 'deep'
                    ? 'bg-orange-400/20 border-orange-400 text-orange-400'
                    : 'bg-black/30 border-red-400/30 text-red-400/60 hover:border-orange-400/50'
                }`}
              >
                <div className="font-bold">🕳️ DEEP</div>
                <div className="text-xs opacity-70">Marketplace crawling</div>
              </button>
            </div>
          </div>

          {/* Monitor Button */}
          <button
            className="w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleMonitor}
            disabled={monitoring}
          >
            {monitoring ? (
              <>
                <span className="animate-pulse">🌑 MONITORING...</span>
              </>
            ) : (
              '🚀 START DARK WEB MONITORING'
            )}
          </button>
        </div>

        {/* Warning Banner */}
        <div className="mb-6 p-4 border-l-4 border-red-600 bg-red-400/10 rounded">
          <div className="flex items-start">
            <span className="text-2xl mr-3">⚠️</span>
            <div>
              <h4 className="text-red-400 font-bold mb-1">DISCLAIMER</h4>
              <p className="text-red-300 text-xs leading-relaxed">
                Esta ferramenta é destinada exclusivamente para propósitos de segurança defensiva e inteligência de ameaças.
                O uso para atividades ilegais é estritamente proibido e pode resultar em consequências legais.
                Todos os acessos são registrados e monitorados.
              </p>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 border border-red-400/50 rounded-lg bg-red-400/10">
            <p className="text-red-400">❌ {error}</p>
          </div>
        )}

        {/* Results Display */}
        {results && !monitoring && (
          <div className="bg-black/50 border border-red-400/30 rounded-lg p-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-black/40 border border-red-400/30 rounded-lg p-3 text-center">
                <div className="text-red-400 text-2xl font-bold">{results.total_findings || 0}</div>
                <div className="text-red-400/70 text-xs">Findings</div>
              </div>
              <div className="bg-black/40 border border-orange-400/30 rounded-lg p-3 text-center">
                <div className="text-orange-400 text-2xl font-bold">{results.onion_sites_found || 0}</div>
                <div className="text-orange-400/70 text-xs">Onion Sites</div>
              </div>
              <div className="bg-black/40 border border-yellow-400/30 rounded-lg p-3 text-center">
                <div className="text-yellow-400 text-2xl font-bold">{results.threat_keywords_matched || 0}</div>
                <div className="text-yellow-400/70 text-xs">Threats</div>
              </div>
              <div className={`rounded-lg p-3 text-center border ${getThreatColor(results.threat_score || 0)}`}>
                <div className="text-2xl font-bold">{results.threat_score?.toFixed(1) || 0}</div>
                <div className="text-xs opacity-70">Threat Score</div>
              </div>
            </div>

            {/* Threat Assessment */}
            {results.threat_score > 0 && (
              <div className={`mb-6 p-4 rounded-lg border ${getThreatColor(results.threat_score)}`}>
                <h4 className="font-bold mb-2">🚨 THREAT ASSESSMENT</h4>
                <p className="text-sm opacity-90">
                  {results.threat_score >= 75 && 'CRITICAL: Ameaças ativas detectadas! Investigação imediata necessária.'}
                  {results.threat_score >= 50 && results.threat_score < 75 && 'HIGH: Múltiplas ameaças potenciais encontradas.'}
                  {results.threat_score >= 25 && results.threat_score < 50 && 'MEDIUM: Algumas menções encontradas. Monitorar.'}
                  {results.threat_score < 25 && 'LOW: Poucas ou nenhuma ameaça detectada.'}
                </p>
              </div>
            )}

            {/* Findings */}
            {results.findings && results.findings.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-red-400 font-bold text-lg mb-3">🔍 DARK WEB FINDINGS</h3>
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {results.findings.map((finding, idx) => (
                    <div
                      key={idx}
                      className="bg-red-400/10 border border-red-400/30 rounded-lg p-4 hover:border-red-400/50 transition-all"
                    >
                      {/* Finding Header */}
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-red-400 font-mono text-sm break-all">
                              {finding.url}
                            </span>
                          </div>
                          <div className="text-xs text-red-400/60">
                            Source: {finding.source} | Discovered: {formatDateTime(finding.discovered_at)}
                          </div>
                        </div>
                        {finding.severity && (
                          <span className={`px-2 py-1 rounded text-xs font-bold ${getSeverityBadge(finding.severity)}`}>
                            {finding.severity.toUpperCase()}
                          </span>
                        )}
                      </div>

                      {/* Matched Keywords */}
                      {finding.matched_keywords && finding.matched_keywords.length > 0 && (
                        <div className="mb-2">
                          <div className="text-xs text-red-400/70 mb-1">Matched Threats:</div>
                          <div className="flex flex-wrap gap-1">
                            {finding.matched_keywords.map((keyword, kidx) => (
                              <span
                                key={kidx}
                                className="px-2 py-0.5 bg-red-600/30 text-red-300 rounded text-xs font-mono"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Context Snippet */}
                      {finding.context_snippet && (
                        <div className="bg-black/40 border border-red-400/20 rounded p-2 mt-2">
                          <div className="text-xs text-red-400/70 mb-1">Context:</div>
                          <p className="text-red-300 text-xs font-mono leading-relaxed">
                            {finding.context_snippet}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center p-8 text-red-400/60">
                <div className="text-4xl mb-2">✅</div>
                <p>Nenhuma ameaça encontrada na dark web.</p>
                <p className="text-xs mt-2">O termo buscado não foi encontrado em marketplaces ou fóruns monitorados.</p>
              </div>
            )}

            {/* Recommendations */}
            {results.recommendations && results.recommendations.length > 0 && (
              <div className="mt-6 bg-yellow-400/10 border border-yellow-400/30 rounded-lg p-4">
                <h4 className="text-yellow-400 font-bold mb-3">💡 RECOMMENDATIONS</h4>
                <ul className="space-y-2 text-xs">
                  {results.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-yellow-300 flex items-start">
                      <span className="mr-2">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Execution Time */}
            {results.execution_time && (
              <div className="mt-6 text-center text-red-400/60 text-xs">
                ⏱️ Execution Time: {results.execution_time}s
              </div>
            )}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-6 bg-red-400/10 border border-red-400/30 rounded-lg p-4">
          <h4 className="text-red-400 font-bold mb-3">🧰 SUPERIOR CAPABILITIES</h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">✅ Multi-Source</span>
              <p className="text-red-300">Ahmia + Onionland search engines</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">✅ Onion v2/v3</span>
              <p className="text-red-300">16-char + 56-char address support</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">✅ Threat Scoring</span>
              <p className="text-red-300">Intelligent keyword-based analysis</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-red-400 font-bold">✅ Context Extraction</span>
              <p className="text-red-300">Snippet extraction for evidence</p>
            </div>
          </div>
        </div>

        {/* Legal Notice */}
        <div className="mt-4 bg-black/40 border border-red-400/20 rounded p-3 text-center">
          <p className="text-red-400/60 text-xs">
            🔒 Este serviço utiliza apenas fontes públicas da clearnet (Ahmia.fi, Onionland).
            Nenhuma conexão direta à rede Tor é estabelecida.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DarkWebModule;

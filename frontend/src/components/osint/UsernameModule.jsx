import React, { useState } from 'react';
import { apiClient } from '@/api/client';
import logger from '@/utils/logger';

const UsernameModule = () => {
  const [username, setUsername] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);

  const handleSearch = async () => {
    if (!username.trim()) {
      alert('Digite um username para buscar');
      return;
    }

    setSearching(true);
    setResults(null);

    try {
      const data = await apiClient.post('/api/username/search', {
        username: username,
        platforms: 'all',
        deep_search: true,
        include_archived: false
      });

      if (data.status === 'success' && data.data) {
        // Adaptar os dados reais do backend para o formato esperado
        const profilesFound = data.data.profiles_found || [];
        const adaptedProfiles = profilesFound.map(profile => ({
          platform: profile.platform,
          url: profile.url,
          status: profile.exists ? 'found' : 'not_found',
          last_activity: profile.timestamp ? new Date(profile.timestamp).toLocaleDateString() : null
        }));

        const adaptedResults = {
          username: username,
          platforms_found: adaptedProfiles,
          total_found: profilesFound.filter(p => p.exists).length,
          confidence_score: data.data.ai_analysis?.confidence_score || 75,
          ai_analysis: data.data.ai_analysis,
          execution_time: data.data.execution_time,
          total_platforms_checked: data.data.total_platforms_checked,
          statistics: data.data.statistics
        };
        setResults(adaptedResults);
      } else {
        throw new Error('Dados inválidos recebidos');
      }
    } catch (error) {
      logger.error('Erro na busca:', error);

      // REGRA DE OURO: No mock fallback in production
      // Return empty results with error indicator
      setResults({
        username: username,
        platforms_found: [],
        total_found: 0,
        confidence_score: 0,
        error: 'Service unavailable. Please try again later.',
        error_mode: true
      });
    } finally {
      setSearching(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'found': return 'text-green-400 border-green-400';
      case 'possible': return 'text-yellow-400 border-yellow-400';
      case 'not_found': return 'text-red-400 border-red-400';
      default: return 'text-gray-400 border-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'found': return '✅';
      case 'possible': return '❓';
      case 'not_found': return '❌';
      default: return '⚪';
    }
  };

  return (
    <div className="space-y-6">
      <div className="border border-red-400/50 rounded-lg bg-red-400/5 p-6">
        <h2 className="text-red-400 font-bold text-2xl mb-4 tracking-wider">
          👤 USERNAME HUNTER
        </h2>
        <p className="text-red-400/70 text-sm mb-6">
          Busca avançada de usernames em múltiplas plataformas sociais e profissionais
        </p>

        {/* Search Input */}
        <div className="space-y-4 mb-6">
          <div className="space-y-2">
            <label htmlFor="input-username-alvo-fibyx" className="text-red-400/80 text-xs font-bold tracking-wider">USERNAME ALVO</label>
<input id="input-username-alvo-fibyx"
              className="w-full bg-black/70 border border-red-400/50 text-red-400 placeholder-red-400/50 p-3 rounded-lg focus:border-red-400 focus:outline-none focus:ring-2 focus:ring-red-400/20 font-mono text-lg"
              placeholder="Digite o username..."
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>

          <button
            className="w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleSearch}
            disabled={searching}
          >
            {searching ? '🔍 BUSCANDO...' : '🚀 INICIAR BUSCA'}
          </button>
        </div>

        {/* Results */}
        {results && (
          <div className="bg-black/50 border border-red-400/30 rounded-lg p-6 max-h-[600px] overflow-y-auto" style={{
            scrollbarWidth: 'thin',
            scrollbarColor: '#ef4444 rgba(0,0,0,0.3)'
          }}>
            <style jsx>{`
              div::-webkit-scrollbar {
                width: 8px;
              }
              div::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
              }
              div::-webkit-scrollbar-thumb {
                background: #ef4444;
                border-radius: 4px;
              }
              div::-webkit-scrollbar-thumb:hover {
                background: #f87171;
              }
            `}</style>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-red-400 font-bold text-lg">RESULTADOS DA BUSCA</h3>
              <div className="text-red-400/60 text-sm">
                Encontrado em {results.total_found} plataforma(s) | Confiança: {results.confidence_score}%
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.platforms_found.map((platform, idx) => (
                <div
                  key={idx}
                  className={`bg-black/30 border rounded-lg p-4 ${getStatusColor(platform.status)}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center space-x-2">
                      <span>{getStatusIcon(platform.status)}</span>
                      <span className="font-bold">{platform.platform}</span>
                    </div>
                    <span className="text-xs uppercase font-bold">{platform.status.replace('_', ' ')}</span>
                  </div>

                  {platform.url && (
                    <div className="text-xs mb-2 font-mono break-all">
                      🔗 {platform.url}
                    </div>
                  )}

                  {platform.last_activity && (
                    <div className="text-xs opacity-70">
                      📅 Última atividade: {platform.last_activity}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2 mt-6">
              <button className="flex-1 bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-2 px-4 rounded text-sm hover:from-orange-500 hover:to-orange-600 transition-all">
                📊 ANÁLISE DETALHADA
              </button>
              <button className="flex-1 bg-gradient-to-r from-green-600 to-green-700 text-white font-bold py-2 px-4 rounded text-sm hover:from-green-500 hover:to-green-600 transition-all">
                💾 SALVAR RELATÓRIO
              </button>
              <button className="flex-1 bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-2 px-4 rounded text-sm hover:from-orange-500 hover:to-orange-600 transition-all">
                🔄 MONITORAR
              </button>
            </div>
          </div>
        )}

        {/* Popular Platforms Info */}
        <div className="mt-6 bg-red-400/10 border border-red-400/30 rounded-lg p-4">
          <h4 className="text-red-400 font-bold mb-3">PLATAFORMAS MONITORADAS</h4>
          <div className="grid grid-cols-4 gap-2 text-xs">
            {['Twitter/X', 'Instagram', 'Facebook', 'LinkedIn', 'GitHub', 'Reddit', 'Discord', 'TikTok', 'YouTube', 'Telegram', 'WhatsApp', 'Snapchat'].map((platform, idx) => (
              <div key={idx} className="bg-black/30 p-2 rounded text-center text-red-400/70">
                {platform}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsernameModule;
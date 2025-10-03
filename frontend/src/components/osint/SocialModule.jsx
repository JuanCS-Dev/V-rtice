import React, { useState } from 'react';

const SocialModule = () => {
  const [platform, setPlatform] = useState('instagram');
  const [identifier, setIdentifier] = useState('');
  const [scraping, setScraping] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleScrape = async () => {
    if (!identifier.trim()) {
      alert('Digite um identificador para extrair');
      return;
    }

    setScraping(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/social/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          platform: platform,
          identifier: identifier.trim()
        }),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setResult(data.data);
      } else {
        setError(data.detail || 'Erro ao analisar perfil social');
      }
    } catch (err) {
      setError('Erro de conexão com o serviço OSINT');
      console.error('Erro:', err);
    } finally {
      setScraping(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          🌐 SOCIAL MEDIA SCRAPER
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Coleta de dados em redes sociais com análise comportamental
        </p>

        <div className="space-y-4">
          <select
            className="w-full bg-black/70 border border-purple-400/50 text-purple-400 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
          >
            <option value="twitter">Twitter/X</option>
            <option value="instagram">Instagram</option>
            <option value="linkedin">LinkedIn</option>
            <option value="facebook">Facebook</option>
            <option value="discord">Discord</option>
            <option value="telegram">Telegram</option>
          </select>

          <input
            className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
            placeholder="Username ou ID do perfil"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />

          <button
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleScrape}
            disabled={scraping}
          >
            {scraping ? '🌐 COLETANDO...' : '🚀 INICIAR SCRAPING'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-4 border border-red-400/50 rounded-lg bg-red-400/5">
            <p className="text-red-400">❌ {error}</p>
          </div>
        )}

        {/* Results Display */}
        {result && (
          <div className="mt-6 space-y-4 max-h-[600px] overflow-y-auto" style={{scrollbarWidth:'thin',scrollbarColor:'#a855f7 rgba(0,0,0,0.3)'}}>
            <style jsx>{`div::-webkit-scrollbar{width:8px}div::-webkit-scrollbar-track{background:rgba(0,0,0,0.3);border-radius:4px}div::-webkit-scrollbar-thumb{background:#a855f7;border-radius:4px}div::-webkit-scrollbar-thumb:hover{background:#c084fc}`}</style>
            <h3 className="text-purple-400 font-bold text-lg">📊 Perfil Analisado - {result.platform}</h3>

            {/* Profile Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">👤 Informações do Perfil</h4>
                <div className="space-y-1 text-sm">
                  <p className="text-purple-300">Username: <span className="text-white">{result.profile_data?.username}</span></p>
                  {result.profile_data?.full_name && (
                    <p className="text-purple-300">Nome: <span className="text-white">{result.profile_data.full_name}</span></p>
                  )}
                  {result.profile_data?.bio && (
                    <p className="text-purple-300">Bio: <span className="text-white text-xs">{result.profile_data.bio}</span></p>
                  )}
                  <p className="text-purple-300">Verificado: <span className={`font-bold ${result.profile_data?.is_verified ? 'text-green-400' : 'text-gray-400'}`}>
                    {result.profile_data?.is_verified ? '✅ Sim' : '❌ Não'}
                  </span></p>
                  <p className="text-purple-300">Privado: <span className={`font-bold ${result.profile_data?.is_private ? 'text-yellow-400' : 'text-green-400'}`}>
                    {result.profile_data?.is_private ? '🔒 Sim' : '🔓 Não'}
                  </span></p>
                  {result.profile_data?.is_business && (
                    <p className="text-purple-300">Tipo: <span className="text-white">🏢 Negócio</span></p>
                  )}
                </div>
              </div>

              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">📈 Estatísticas</h4>
                <div className="space-y-1 text-sm">
                  {result.statistics?.posts !== undefined && (
                    <p className="text-purple-300">Posts: <span className="text-white font-bold">{result.statistics.posts}</span></p>
                  )}
                  {result.statistics?.followers !== undefined && (
                    <p className="text-purple-300">Seguidores: <span className="text-white font-bold">{result.statistics.followers}</span></p>
                  )}
                  {result.statistics?.following !== undefined && (
                    <p className="text-purple-300">Seguindo: <span className="text-white font-bold">{result.statistics.following}</span></p>
                  )}
                  {result.statistics?.engagement_rate !== undefined && (
                    <p className="text-purple-300">Engajamento: <span className="text-white font-bold">{result.statistics.engagement_rate.toFixed(1)}%</span></p>
                  )}
                </div>
              </div>
            </div>

            {/* Profile Picture */}
            {result.profile_data?.profile_pic_url && (
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">🖼️ Foto do Perfil</h4>
                <div className="flex items-center space-x-4">
                  <img
                    src={result.profile_data.profile_pic_url}
                    alt="Profile"
                    className="w-20 h-20 rounded-full border border-purple-400/30"
                    onError={(e) => {e.target.style.display = 'none'}}
                  />
                  <div className="text-xs text-purple-300 break-all">
                    {result.profile_data.profile_pic_url}
                  </div>
                </div>
              </div>
            )}

            {/* Behavioral Analysis */}
            {result.behavioral_analysis && (
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">🧠 Análise Comportamental</h4>
                <div className="space-y-2 text-sm">
                  <p className="text-purple-300">Tipo de Usuário: <span className="text-white capitalize">{result.behavioral_analysis.behavior_type?.replace('_', ' ')}</span></p>
                  <p className="text-purple-300">Nível de Engajamento: <span className="text-white capitalize">{result.behavioral_analysis.engagement_level}</span></p>
                  <p className="text-purple-300">Score de Influência: <span className="text-white font-bold">{result.behavioral_analysis.influence_score}/100</span></p>

                  {result.behavioral_analysis.content_themes && result.behavioral_analysis.content_themes.length > 0 && (
                    <div>
                      <p className="text-purple-300">Temas de Conteúdo:</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {result.behavioral_analysis.content_themes.map((theme, index) => (
                          <span key={index} className="bg-purple-400/20 text-purple-300 px-2 py-1 rounded text-xs">
                            {theme}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.behavioral_analysis.anomalies && result.behavioral_analysis.anomalies.length > 0 && (
                    <div>
                      <p className="text-red-300">⚠️ Anomalias Detectadas:</p>
                      <ul className="text-red-200 text-xs space-y-1 ml-4">
                        {result.behavioral_analysis.anomalies.map((anomaly, index) => (
                          <li key={index}>• {anomaly}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Posts Preview */}
            {result.posts && result.posts.length > 0 && (
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">📝 Posts Recentes ({result.posts.length})</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {result.posts.slice(0, 5).map((post, index) => (
                    <div key={index} className="bg-purple-400/10 border border-purple-400/20 rounded p-2 text-xs">
                      <div className="text-purple-200 mb-1">{post.content || post.caption || 'Conteúdo não disponível'}</div>
                      {post.timestamp && (
                        <div className="text-purple-300 text-xs">📅 {post.timestamp}</div>
                      )}
                      {post.likes && (
                        <div className="text-purple-300 text-xs">❤️ {post.likes} likes</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
              <h4 className="text-purple-400 font-medium mb-2">🔍 Metadados da Coleta</h4>
              <div className="text-xs text-purple-300 space-y-1">
                <p>Timestamp: {result.scrape_timestamp}</p>
                <p>Nível de Profundidade: {result.depth_level}</p>
                <p>Plataforma: {result.platform}</p>
                <p>Identificador: {result.identifier}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SocialModule;
import React, { useState } from 'react';

const GoogleModule = () => {
  const [searchType, setSearchType] = useState('person');
  const [query, setQuery] = useState('');
  const [advanced, setAdvanced] = useState(false);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const searchTypes = {
    person: { label: 'Pessoa', icon: '👤' },
    email: { label: 'Email', icon: '📧' },
    phone: { label: 'Telefone', icon: '📱' },
    domain: { label: 'Domínio', icon: '🌐' },
    document: { label: 'Documentos', icon: '📄' },
    social: { label: 'Redes Sociais', icon: '📱' },
    vulnerability: { label: 'Vulnerabilidades', icon: '🔴' }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      alert('Digite algo para buscar');
      return;
    }

    setSearching(true);
    setError(null);
    setResults(null);

    try {
      const endpoint = advanced ? '/api/google/search/advanced' : '/api/google/search/basic';
      const payload = advanced ? {
        target: query.trim(),
        search_types: [searchType],
        deep_search: true,
        include_social_media: true,
        max_results_per_type: 30
      } : {
        query: query.trim(),
        search_type: searchType,
        max_results: 50,
        language: 'pt',
        region: 'BR',
        include_documents: true,
        safe_search: true
      };

      const response = await fetch(`http://localhost:8013${endpoint.replace('/api/google', '/api')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setResults(data.data);
      } else {
        setError(data.detail || 'Erro ao executar busca Google');
      }
    } catch (err) {
      setError('Erro de conexão com o serviço Google OSINT');
      console.error('Erro:', err);
    } finally {
      setSearching(false);
    }
  };

  const getResultTypeColor = (url) => {
    if (url.includes('linkedin.com')) return 'border-blue-400 bg-blue-400/10';
    if (url.includes('facebook.com')) return 'border-blue-600 bg-blue-600/10';
    if (url.includes('twitter.com') || url.includes('x.com')) return 'border-cyan-400 bg-cyan-400/10';
    if (url.includes('instagram.com')) return 'border-pink-400 bg-pink-400/10';
    if (url.includes('.pdf')) return 'border-red-400 bg-red-400/10';
    if (url.includes('.doc')) return 'border-yellow-400 bg-yellow-400/10';
    return 'border-purple-400 bg-purple-400/10';
  };

  const formatDomain = (url) => {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
    }
  };

  const renderBasicResults = () => {
    if (!results || !results.results) return null;

    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-purple-400 font-bold text-lg">🔍 Resultados Google OSINT</h3>
          <div className="text-purple-400/60 text-sm">
            {results.total_results} resultado(s) encontrado(s)
          </div>
        </div>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          {results.results.map((result, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border transition-all hover:scale-[1.01] ${getResultTypeColor(result.url)}`}
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-purple-300 font-medium text-sm leading-tight">
                  {result.title}
                </h4>
                <span className="text-xs text-purple-400/60 ml-2">#{result.position}</span>
              </div>

              <p className="text-purple-200 text-xs mb-2 line-clamp-2">
                {result.snippet}
              </p>

              <div className="flex justify-between items-center text-xs">
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300 underline break-all flex-1 mr-2"
                >
                  {formatDomain(result.url)}
                </a>
                <span className="text-purple-400/50 whitespace-nowrap">
                  {new Date(result.found_timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderAdvancedResults = () => {
    if (!results || !results.results_by_type) return null;

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h3 className="text-purple-400 font-bold text-lg">🎯 Busca Avançada</h3>
          <div className="text-purple-400/60 text-sm">
            {results.summary?.total_results} resultado(s) | {results.execution_time}s
          </div>
        </div>

        {/* Estatísticas */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-black/40 border border-purple-400/30 rounded-lg p-3 text-center">
            <div className="text-purple-400 text-xl font-bold">{results.summary?.total_results || 0}</div>
            <div className="text-purple-400/70 text-xs">Total Resultados</div>
          </div>
          <div className="bg-black/40 border border-purple-400/30 rounded-lg p-3 text-center">
            <div className="text-purple-400 text-xl font-bold">{results.summary?.domains_found?.length || 0}</div>
            <div className="text-purple-400/70 text-xs">Domínios</div>
          </div>
          <div className="bg-black/40 border border-purple-400/30 rounded-lg p-3 text-center">
            <div className="text-purple-400 text-xl font-bold">{results.summary?.file_types_found?.length || 0}</div>
            <div className="text-purple-400/70 text-xs">Tipos de Arquivo</div>
          </div>
        </div>

        {/* Resultados por tipo */}
        {Object.entries(results.results_by_type).map(([type, typeResults]) => (
          <div key={type} className="bg-black/30 border border-purple-400/30 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-purple-400 font-medium capitalize">
                {searchTypes[type]?.icon} {searchTypes[type]?.label || type}
              </span>
              <span className="text-purple-400/60 text-sm">({typeResults.length} resultados)</span>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {typeResults.slice(0, 10).map((result, index) => (
                <div key={index} className="bg-purple-400/10 border border-purple-400/20 rounded p-3">
                  <div className="flex justify-between items-start mb-1">
                    <h5 className="text-purple-300 font-medium text-sm">{result.title}</h5>
                    <span className="text-xs text-purple-400/60">#{result.position}</span>
                  </div>

                  <p className="text-purple-200 text-xs mb-2">{result.snippet}</p>

                  <div className="flex justify-between items-center text-xs">
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300 underline"
                    >
                      {formatDomain(result.url)}
                    </a>
                    {result.dork_pattern && (
                      <span className="text-purple-400/50 font-mono text-xs">
                        {result.dork_pattern.replace(result.target || query, '***')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          🔍 GOOGLE OSINT INVESTIGATOR
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Investigação avançada através do Google com Google Dorks e técnicas OSINT
        </p>

        {/* Configurações de busca */}
        <div className="space-y-4 mb-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-purple-400/80 text-xs font-bold tracking-wider block mb-2">
                TIPO DE INVESTIGAÇÃO
              </label>
              <select
                className="w-full bg-black/70 border border-purple-400/50 text-purple-400 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
              >
                {Object.entries(searchTypes).map(([key, type]) => (
                  <option key={key} value={key}>
                    {type.icon} {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-purple-400/80 text-xs font-bold tracking-wider block mb-2">
                MODO DE BUSCA
              </label>
              <div className="flex space-x-2">
                <button
                  className={`flex-1 py-3 px-4 rounded-lg font-bold text-sm transition-all ${
                    !advanced
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                      : 'bg-black/50 border border-purple-400/30 text-purple-400 hover:bg-purple-400/10'
                  }`}
                  onClick={() => setAdvanced(false)}
                >
                  📊 BÁSICO
                </button>
                <button
                  className={`flex-1 py-3 px-4 rounded-lg font-bold text-sm transition-all ${
                    advanced
                      ? 'bg-gradient-to-r from-red-600 to-orange-600 text-white'
                      : 'bg-black/50 border border-purple-400/30 text-purple-400 hover:bg-purple-400/10'
                  }`}
                  onClick={() => setAdvanced(true)}
                >
                  🎯 AVANÇADO
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="text-purple-400/80 text-xs font-bold tracking-wider block mb-2">
              ALVO DA INVESTIGAÇÃO
            </label>
            <input
              className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono text-lg"
              placeholder={
                advanced
                  ? 'Digite o alvo para investigação profunda...'
                  : 'Digite sua query de busca...'
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>

          <button
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleSearch}
            disabled={searching}
          >
            {searching ? (
              advanced ? '🎯 INVESTIGANDO...' : '🔍 BUSCANDO...'
            ) : (
              advanced ? '🚀 INICIAR INVESTIGAÇÃO' : '🔍 EXECUTAR BUSCA'
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 border border-red-400/50 rounded-lg bg-red-400/5">
            <p className="text-red-400">❌ {error}</p>
          </div>
        )}

        {/* Results Display */}
        {results && (
          <div className="bg-black/50 border border-purple-400/30 rounded-lg p-6">
            {advanced ? renderAdvancedResults() : renderBasicResults()}
          </div>
        )}

        {/* Dork Examples */}
        <div className="mt-6 bg-purple-400/10 border border-purple-400/30 rounded-lg p-4">
          <h4 className="text-purple-400 font-bold mb-3">🧰 GOOGLE DORKS DISPONÍVEIS</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
            <div className="bg-black/30 p-2 rounded">
              <span className="text-purple-400 font-mono">site:linkedin.com</span>
              <p className="text-purple-300">Busca em LinkedIn</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-purple-400 font-mono">filetype:pdf</span>
              <p className="text-purple-300">Arquivos PDF</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-purple-400 font-mono">intext:"email"</span>
              <p className="text-purple-300">Texto específico</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-purple-400 font-mono">cache:site.com</span>
              <p className="text-purple-300">Cache do Google</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-purple-400 font-mono">"index of"</span>
              <p className="text-purple-300">Diretórios abertos</p>
            </div>
            <div className="bg-black/30 p-2 rounded">
              <span className="text-purple-400 font-mono">intitle:"login"</span>
              <p className="text-purple-300">Páginas de login</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoogleModule;
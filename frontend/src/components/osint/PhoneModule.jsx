import React, { useState } from 'react';

const PhoneModule = () => {
  const [phone, setPhone] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!phone.trim()) {
      alert('Digite um número de telefone para analisar');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/phone/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone: phone.trim() }),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setResult(data.data);
      } else {
        setError(data.detail || 'Erro ao analisar telefone');
      }
    } catch (err) {
      setError('Erro de conexão com o serviço OSINT');
      console.error('Erro:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          📱 PHONE INTELLIGENCE
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Análise de números telefônicos, operadoras e aplicativos de mensagem
        </p>

        <div className="space-y-4">
          <input
            className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
            placeholder="+5562999999999"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? '📱 RASTREANDO...' : '🔍 RASTREAR TELEFONE'}
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
          <div className="mt-6 space-y-4">
            <h3 className="text-purple-400 font-bold text-lg">📊 Resultados da Análise</h3>

            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">📱 Informações Básicas</h4>
                <div className="space-y-1 text-sm">
                  <p className="text-purple-300">Número: <span className="text-white">{result.normalized}</span></p>
                  <p className="text-purple-300">Válido: <span className={`font-bold ${result.valid ? 'text-green-400' : 'text-red-400'}`}>
                    {result.valid ? '✅ Sim' : '❌ Não'}
                  </span></p>
                  <p className="text-purple-300">País: <span className="text-white">{result.location?.country}</span></p>
                  <p className="text-purple-300">Região: <span className="text-white">{result.location?.region}</span></p>
                </div>
              </div>

              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">📡 Operadora</h4>
                <div className="space-y-1 text-sm">
                  <p className="text-purple-300">Nome: <span className="text-white">{result.carrier?.name}</span></p>
                  <p className="text-purple-300">Tipo: <span className="text-white">{result.carrier?.type}</span></p>
                  {result.brazil_info && (
                    <>
                      <p className="text-purple-300">DDD: <span className="text-white">{result.brazil_info.ddd}</span></p>
                      <p className="text-purple-300">Estado: <span className="text-white">{result.brazil_info.state}</span></p>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Risk Analysis */}
            {result.risk_analysis && (
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">⚠️ Análise de Risco</h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-purple-300">Nível:</span>
                    <span className={`font-bold px-2 py-1 rounded text-xs ${
                      result.risk_analysis.level === 'LOW' ? 'bg-green-400/20 text-green-400' :
                      result.risk_analysis.level === 'MEDIUM' ? 'bg-yellow-400/20 text-yellow-400' :
                      'bg-red-400/20 text-red-400'
                    }`}>
                      {result.risk_analysis.level}
                    </span>
                    <span className="text-white">({result.risk_analysis.score}/100)</span>
                  </div>
                  {result.risk_analysis.factors && result.risk_analysis.factors.length > 0 && (
                    <div>
                      <p className="text-purple-300 text-sm">Fatores:</p>
                      <ul className="text-purple-200 text-xs space-y-1 ml-4">
                        {result.risk_analysis.factors.map((factor, index) => (
                          <li key={index}>• {factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Messaging Apps */}
            {result.messaging_apps && (
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">💬 Apps de Mensagem</h4>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  {Object.entries(result.messaging_apps).map(([app, info]) => (
                    <div key={app} className="flex items-center space-x-2">
                      <span className="text-purple-300 capitalize">{app}:</span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        info.available === 'yes' ? 'bg-green-400/20 text-green-400' :
                        info.available === 'no' ? 'bg-red-400/20 text-red-400' :
                        'bg-gray-400/20 text-gray-400'
                      }`}>
                        {info.available === 'yes' ? '✅' : info.available === 'no' ? '❌' : '❓'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Brasil Specific Info */}
            {result.brazil_info?.operator_hints && (
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-4">
                <h4 className="text-purple-400 font-medium mb-2">🇧🇷 Informações Brasil</h4>
                <div className="text-sm space-y-1">
                  <p className="text-purple-300">Região: <span className="text-white">{result.brazil_info.region}</span></p>
                  <div>
                    <p className="text-purple-300">Dicas da Operadora:</p>
                    <ul className="text-purple-200 text-xs space-y-1 ml-4">
                      {result.brazil_info.operator_hints.map((hint, index) => (
                        <li key={index}>• {hint}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PhoneModule;
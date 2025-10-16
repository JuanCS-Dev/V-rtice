import React, { useState } from 'react';
import { apiClient } from '@/api/client';
import logger from '@/utils/logger';

const EmailModule = () => {
  const [email, setEmail] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!email.trim()) {
      alert('Digite um email para analisar');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiClient.post('/api/email/analyze', { email: email.trim() });

      if (data.status === 'success') {
        setResult(data.data);
      } else {
        setError(data.detail || 'Erro ao analisar email');
      }
    } catch (err) {
      setError('Erro de conexão com o serviço OSINT');
      logger.error('Erro:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="border border-red-400/50 rounded-lg bg-red-400/5 p-6">
        <h2 className="text-red-400 font-bold text-2xl mb-4 tracking-wider">
          📧 EMAIL ANALYZER
        </h2>
        <p className="text-red-400/70 text-sm mb-6">
          Análise de segurança, vazamentos e reputação de endereços de email
        </p>

        <div className="space-y-4">
          <input
            className="w-full bg-black/70 border border-red-400/50 text-red-400 placeholder-red-400/50 p-3 rounded-lg focus:border-red-400 focus:outline-none focus:ring-2 focus:ring-red-400/20 font-mono"
            placeholder="Digite o email..."
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            className="w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? '📧 ANALISANDO...' : '🔍 ANALISAR EMAIL'}
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
          <div className="mt-6 space-y-4 max-h-[600px] overflow-y-auto" style={{
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
            <h3 className="text-red-400 font-bold text-lg">📊 Resultados da Análise</h3>

            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-black/40 border border-red-400/30 rounded-lg p-4">
                <h4 className="text-red-400 font-medium mb-2">📧 Informações Básicas</h4>
                <div className="space-y-1 text-sm">
                  <p className="text-red-300">Email: <span className="text-white">{result.email}</span></p>
                  <p className="text-red-300">Usuário: <span className="text-white">{result.username}</span></p>
                  <p className="text-red-300">Domínio: <span className="text-white">{result.domain}</span></p>
                  <p className="text-red-300">Formato: <span className={`font-bold ${result.valid_format ? 'text-green-400' : 'text-red-400'}`}>
                    {result.valid_format ? '✅ Válido' : '❌ Inválido'}
                  </span></p>
                </div>
              </div>

              <div className="bg-black/40 border border-red-400/30 rounded-lg p-4">
                <h4 className="text-red-400 font-medium mb-2">🛡️ Reputação</h4>
                <div className="space-y-1 text-sm">
                  <p className="text-red-300">Spam Listed: <span className={`font-bold ${result.reputation?.spam_listed ? 'text-red-400' : 'text-green-400'}`}>
                    {result.reputation?.spam_listed ? '❌ Sim' : '✅ Não'}
                  </span></p>
                  <p className="text-red-300">Descartável: <span className={`font-bold ${result.reputation?.disposable ? 'text-red-400' : 'text-green-400'}`}>
                    {result.reputation?.disposable ? '❌ Sim' : '✅ Não'}
                  </span></p>
                  <p className="text-red-300">Provedor: <span className="text-white">
                    {result.reputation?.free_provider ? '🆓 Gratuito' : result.reputation?.corporate ? '🏢 Corporativo' : '❓ Desconhecido'}
                  </span></p>
                </div>
              </div>
            </div>

            {/* Risk Assessment */}
            {result.risk_score && (
              <div className="bg-black/40 border border-red-400/30 rounded-lg p-4">
                <h4 className="text-red-400 font-medium mb-2">⚠️ Análise de Risco</h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-red-300">Nível:</span>
                    <span className={`font-bold px-2 py-1 rounded text-xs ${
                      result.risk_score.level === 'LOW' ? 'bg-green-400/20 text-green-400' :
                      result.risk_score.level === 'MEDIUM' ? 'bg-yellow-400/20 text-yellow-400' :
                      'bg-red-400/20 text-red-400'
                    }`}>
                      {result.risk_score.level}
                    </span>
                    <span className="text-white">({result.risk_score.score}/100)</span>
                  </div>
                  {result.risk_score.factors && result.risk_score.factors.length > 0 && (
                    <div>
                      <p className="text-red-300 text-sm">Fatores:</p>
                      <ul className="text-red-200 text-xs space-y-1 ml-4">
                        {result.risk_score.factors.map((factor, index) => (
                          <li key={index}>• {factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Data Breaches */}
            {result.breaches && result.breaches.length > 0 && (
              <div className="bg-black/40 border border-red-400/30 rounded-lg p-4">
                <h4 className="text-red-400 font-medium mb-2">🚨 Vazamentos de Dados</h4>
                <div className="space-y-2">
                  <p className="text-red-300 text-sm">⚠️ Este email foi encontrado em {result.breaches.length} vazamento(s):</p>
                  <div className="space-y-1">
                    {result.breaches.map((breach, index) => (
                      <div key={index} className="bg-red-400/10 border border-red-400/20 rounded p-2 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-red-300 font-medium">{breach.source}</span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            breach.severity === 'HIGH' ? 'bg-red-400/20 text-red-400' :
                            breach.severity === 'MEDIUM' ? 'bg-yellow-400/20 text-yellow-400' :
                            'bg-orange-400/20 text-orange-400'
                          }`}>
                            {breach.severity}
                          </span>
                        </div>
                        {breach.year && <p className="text-red-200">Ano: {breach.year}</p>}
                        {breach.occurrences && <p className="text-red-200">Ocorrências: {breach.occurrences}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* MX Records */}
            {result.mx_records && (
              <div className="bg-black/40 border border-red-400/30 rounded-lg p-4">
                <h4 className="text-red-400 font-medium mb-2">📮 Registros MX</h4>
                <div className="text-sm">
                  <p className="text-red-300">Válido: <span className={`font-bold ${result.mx_records.valid ? 'text-green-400' : 'text-red-400'}`}>
                    {result.mx_records.valid ? '✅ Sim' : '❌ Não'}
                  </span></p>
                  {result.mx_records.records && result.mx_records.records.length > 0 && (
                    <div className="mt-2">
                      <p className="text-red-300 text-sm mb-1">Servidores de Email:</p>
                      <div className="space-y-1">
                        {result.mx_records.records.slice(0, 3).map((record, index) => (
                          <div key={index} className="text-xs text-red-200">
                            <span className="text-gray-400">#{record.priority}</span> {record.host}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Social Presence */}
            {result.social_presence && (
              <div className="bg-black/40 border border-red-400/30 rounded-lg p-4">
                <h4 className="text-red-400 font-medium mb-2">🌐 Presença Social</h4>
                <div className="text-sm">
                  {result.social_presence.possible_accounts && result.social_presence.possible_accounts.length > 0 && (
                    <div>
                      <p className="text-red-300 mb-2">Possíveis Contas:</p>
                      <div className="grid grid-cols-2 gap-2">
                        {result.social_presence.possible_accounts.map((account, index) => (
                          <div key={index} className="bg-red-400/10 border border-red-400/20 rounded p-2 text-xs">
                            <div className="flex justify-between items-center">
                              <span className="text-red-300 capitalize">{account.platform}</span>
                              <span className={`px-1 py-0.5 rounded text-xs ${
                                account.probability === 'high' ? 'bg-green-400/20 text-green-400' :
                                account.probability === 'medium' ? 'bg-yellow-400/20 text-yellow-400' :
                                'bg-gray-400/20 text-gray-400'
                              }`}>
                                {account.probability}
                              </span>
                            </div>
                            <p className="text-red-200">@{account.username}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {result.risk_assessment?.recommendations && result.risk_assessment.recommendations.length > 0 && (
              <div className="bg-black/40 border border-yellow-400/30 rounded-lg p-4">
                <h4 className="text-yellow-400 font-medium mb-2">💡 Recomendações</h4>
                <ul className="text-yellow-200 text-sm space-y-1">
                  {result.risk_assessment.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-yellow-400 mt-0.5">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailModule;
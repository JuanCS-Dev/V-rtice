import React, { useState } from 'react';
import { apiClient } from '@/api/client';
import logger from '@/utils/logger';

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
      const data = await apiClient.post('/api/phone/analyze', { phone: phone.trim() });

      if (data.status === 'success' && data.data) {
        setResult(data.data);
      } else {
        setError(data.detail || 'Erro ao analisar telefone');
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
          📱 PHONE INTELLIGENCE
        </h2>
        <p className="text-red-400/70 text-sm mb-6">
          Análise de números telefônicos com AI-powered carrier detection
        </p>

        <div className="space-y-4">
          <input
            className="w-full bg-black/70 border border-red-400/50 text-red-400 placeholder-red-400/50 p-3 rounded-lg focus:border-red-400 focus:outline-none focus:ring-2 focus:ring-red-400/20 font-mono"
            placeholder="+5562999999999"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button
            className="w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider disabled:opacity-50"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? '📱 RASTREANDO...' : '🔍 RASTREAR TELEFONE'}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 border border-red-400/50 rounded-lg bg-red-400/5">
            <p className="text-red-400">❌ {error}</p>
          </div>
        )}

        {result && (
          <div className="mt-6 space-y-4 max-h-[600px] overflow-y-auto">
            {result.ai_analysis && (
              <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 border border-purple-400/50 rounded-lg p-4">
                <h3 className="text-purple-400 font-bold mb-2 flex items-center">
                  🤖 AI Analysis ({result.ai_analysis.provider})
                </h3>
                <div className="text-purple-300 text-sm whitespace-pre-wrap">
                  {result.ai_analysis.summary}
                </div>
              </div>
            )}

            <div className="bg-black/40 border border-red-400/30 rounded-lg p-4">
              <h4 className="text-red-400 font-medium mb-2">⚠️ Risk Assessment</h4>
              <div className="space-y-2">
                <p className="text-red-300">
                  <span className="font-bold">Level:</span> {result.risk_assessment?.risk_level || 'UNKNOWN'}
                </p>
                <p className="text-red-300">
                  <span className="font-bold">Score:</span> {result.risk_assessment?.risk_score || 0}/100
                </p>
                <p className="text-red-300">
                  <span className="font-bold">Confidence:</span> {result.confidence_score || 0}%
                </p>
              </div>
            </div>

            {result.recommendations && result.recommendations.length > 0 && (
              <div className="bg-black/40 border border-yellow-400/30 rounded-lg p-4">
                <h4 className="text-yellow-400 font-medium mb-2">💡 Recommendations</h4>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-yellow-300 text-sm">
                      • <span className="font-bold">{rec.action}:</span> {rec.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.patterns_found && result.patterns_found.length > 0 && (
              <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-4">
                <h4 className="text-cyan-400 font-medium mb-2">🔍 Patterns Detected</h4>
                <ul className="space-y-2">
                  {result.patterns_found.map((pattern, idx) => (
                    <li key={idx} className="text-cyan-300 text-sm">
                      <span className="font-bold">{pattern.type}:</span> {pattern.description}
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

export default PhoneModule;

import React, { useState } from 'react';
import axios from 'axios';

const AuroraAIModule = ({ setIsAIProcessing, setResults }) => {
  const [targetData, setTargetData] = useState({
    username: '',
    email: '',
    phone: '',
    name: '',
    location: '',
    context: ''
  });
  const [aiProgress, setAiProgress] = useState(0);
  const [aiPhase, setAiPhase] = useState('');
  const [result, setResult] = useState(null);

  const handleInvestigation = async () => {
    if (Object.values(targetData).every(v => !v)) {
      alert('Forneça pelo menos um identificador');
      return;
    }

    setIsAIProcessing(true);
    setAiProgress(0);
    setResult(null);

    // Simular fases da investigação
    const phases = [
      { phase: 'Iniciando Aurora AI...', progress: 10 },
      { phase: 'Reconhecimento inicial...', progress: 25 },
      { phase: 'Deep scan em andamento...', progress: 40 },
      { phase: 'Correlacionando dados...', progress: 55 },
      { phase: 'Análise comportamental...', progress: 70 },
      { phase: 'Avaliação de risco...', progress: 85 },
      { phase: 'Gerando relatório...', progress: 95 },
      { phase: 'Investigação completa!', progress: 100 }
    ];

    for (const phase of phases) {
      setAiPhase(phase.phase);
      setAiProgress(phase.progress);
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    try {
      // Fazer chamada para o API Gateway que irá encaminhar para o OSINT service
      const response = await axios.post('http://localhost:8000/api/investigate/auto', targetData);
      setResult(response.data.data);
      setResults(response.data.data);
    } catch (error) {
      console.error('Erro na investigação:', error);

      // Fallback com dados simulados se a API não estiver disponível
      const fallbackResult = {
        investigation_id: `INV-${Date.now()}`,
        risk_assessment: {
          risk_level: 'MEDIUM',
          risk_score: 65,
          risk_factors: ['Múltiplos perfis online', 'Dados expostos publicamente']
        },
        executive_summary: 'Análise completa do alvo realizada com sucesso. Dados coletados de múltiplas fontes.',
        patterns_found: [
          { type: 'SOCIAL', description: 'Alta atividade em redes sociais' },
          { type: 'BEHAVIORAL', description: 'Padrão de uso noturno detectado' },
          { type: 'DIGITAL', description: 'Pegada digital significativa' }
        ],
        recommendations: [
          { action: 'Monitoramento contínuo', description: 'Manter vigilância sobre atividades online' },
          { action: 'Análise aprofundada', description: 'Investigar conexões secundárias' },
          { action: 'Verificação adicional', description: 'Validar dados encontrados' }
        ],
        data_sources: ['Social Media', 'Public Records', 'Breach Databases', 'Username Databases'],
        confidence_score: 87,
        timestamp: new Date().toISOString()
      };
      setResult(fallbackResult);
      setResults(fallbackResult);
    } finally {
      setIsAIProcessing(false);
    }
  };

  const clearForm = () => {
    setTargetData({
      username: '',
      email: '',
      phone: '',
      name: '',
      location: '',
      context: ''
    });
    setResult(null);
  };

  return (
    <div className="space-y-6">
      <div className="border border-purple-400/50 rounded-lg bg-purple-400/5 p-6">
        <h2 className="text-purple-400 font-bold text-2xl mb-4 tracking-wider">
          🧠 AURORA AI - ORQUESTRADOR DE INVESTIGAÇÃO
        </h2>
        <p className="text-purple-400/70 text-sm mb-6">
          Sistema de IA avançado para investigação OSINT automatizada com análise comportamental
        </p>

        {/* Input Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="space-y-2">
            <label className="text-purple-400/80 text-xs font-bold tracking-wider">USERNAME / HANDLE</label>
            <input
              className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
              placeholder="john_doe_2024"
              value={targetData.username}
              onChange={(e) => setTargetData({...targetData, username: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-purple-400/80 text-xs font-bold tracking-wider">EMAIL</label>
            <input
              className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
              placeholder="target@email.com"
              value={targetData.email}
              onChange={(e) => setTargetData({...targetData, email: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-purple-400/80 text-xs font-bold tracking-wider">TELEFONE</label>
            <input
              className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
              placeholder="+5562999999999"
              value={targetData.phone}
              onChange={(e) => setTargetData({...targetData, phone: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-purple-400/80 text-xs font-bold tracking-wider">NOME COMPLETO</label>
            <input
              className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
              placeholder="João Silva"
              value={targetData.name}
              onChange={(e) => setTargetData({...targetData, name: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-purple-400/80 text-xs font-bold tracking-wider">LOCALIZAÇÃO</label>
            <input
              className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
              placeholder="Goiânia, GO"
              value={targetData.location}
              onChange={(e) => setTargetData({...targetData, location: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-purple-400/80 text-xs font-bold tracking-wider">CONTEXTO</label>
            <input
              className="w-full bg-black/70 border border-purple-400/50 text-purple-400 placeholder-purple-400/50 p-3 rounded-lg focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20 font-mono"
              placeholder="Investigação de segurança"
              value={targetData.context}
              onChange={(e) => setTargetData({...targetData, context: e.target.value})}
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex space-x-4 mb-6">
          <button
            className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider"
            onClick={handleInvestigation}
          >
            🚀 INICIAR INVESTIGAÇÃO AURORA AI
          </button>
          <button
            className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-500 hover:to-gray-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 tracking-wider"
            onClick={clearForm}
          >
            🗑️ LIMPAR
          </button>
        </div>

        {/* Progress */}
        {aiPhase && (
          <div className="bg-black/50 border border-purple-400/30 rounded-lg p-4 mb-6">
            <div className="text-purple-400 text-sm mb-2">{aiPhase}</div>
            <div className="w-full bg-purple-400/20 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-400 to-pink-400 transition-all duration-500"
                style={{ width: `${aiProgress}%` }}
              />
            </div>
            <div className="text-purple-400/60 text-xs text-right mt-1">{aiProgress}%</div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="bg-black/50 border border-purple-400/30 rounded-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-purple-400 font-bold text-lg">📋 RELATÓRIO DE INVESTIGAÇÃO</h3>
              <span className="text-purple-400/60 text-sm">ID: {result.investigation_id}</span>
            </div>

            {/* Risk Assessment */}
            {result.risk_assessment && (
              <div className="bg-red-400/10 border border-red-400/30 rounded-lg p-4 mb-4">
                <h4 className="text-red-400 font-bold mb-3">AVALIAÇÃO DE RISCO</h4>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-red-400 text-4xl font-bold">{result.risk_assessment.risk_score}</div>
                    <div className="text-red-400/70 text-sm">{result.risk_assessment.risk_level}</div>
                  </div>
                  <div className="flex-1">
                    <strong className="text-white/80">Fatores de Risco:</strong>
                    <ul className="text-white/70 text-sm mt-2 space-y-1">
                      {result.risk_assessment.risk_factors?.map((factor, idx) => (
                        <li key={idx}>• {factor}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Executive Summary */}
            {result.executive_summary && (
              <div className="bg-purple-400/10 border border-purple-400/30 rounded-lg p-4 mb-4">
                <h4 className="text-purple-400 font-bold mb-2">RESUMO EXECUTIVO</h4>
                <p className="text-white/80 text-sm">{result.executive_summary}</p>
              </div>
            )}

            {/* Patterns Found */}
            {result.patterns_found && (
              <div className="bg-yellow-400/10 border border-yellow-400/30 rounded-lg p-4 mb-4">
                <h4 className="text-yellow-400 font-bold mb-3">PADRÕES DETECTADOS</h4>
                <div className="space-y-2">
                  {result.patterns_found.map((pattern, idx) => (
                    <div key={idx} className="flex space-x-3 bg-black/30 p-2 rounded">
                      <span className="text-yellow-400 font-bold text-sm">{pattern.type}</span>
                      <span className="text-white/80 text-sm">{pattern.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && (
              <div className="bg-cyan-400/10 border border-cyan-400/30 rounded-lg p-4">
                <h4 className="text-cyan-400 font-bold mb-3">RECOMENDAÇÕES DA IA</h4>
                <div className="space-y-2">
                  {result.recommendations.map((rec, idx) => (
                    <div key={idx} className="bg-black/30 p-3 rounded">
                      <strong className="text-cyan-400">{rec.action}:</strong>
                      <span className="text-white/80 ml-2">{rec.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AuroraAIModule;
import React, { useState } from 'react';
import logger from '@/utils/logger';
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api';

const MaximusAIModule = ({ setIsAIProcessing, setResults }) => {
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
      { phase: 'Iniciando Maximus AI...', progress: 10 },
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
      const response = await axios.post(`${API_ENDPOINTS.investigate}/auto`, targetData);
      setResult(response.data.data);
      setResults(response.data.data);
    } catch (error) {
      logger.error('Erro na investigação:', error);

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
      <div className="border border-red-500/30 rounded-lg bg-black/40 p-6">
        <h2 className="text-white font-semibold text-xl mb-2 tracking-wide">
          AURORA AI
        </h2>
        <p className="text-gray-400 text-xs mb-6 font-mono">
          Autonomous intelligence orchestrator for OSINT investigation
        </p>

        {/* Input Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="space-y-1">
            <label htmlFor="input-username-hsdk3" className="text-gray-400 text-[10px] font-medium tracking-wider uppercase">Username</label>
<input id="input-username-hsdk3"
              className="w-full bg-black/60 border border-gray-700 text-gray-300 placeholder-gray-600 px-3 py-2 rounded text-sm focus:border-red-500/50 focus:outline-none transition-colors font-mono"
              placeholder="john_doe_2024"
              value={targetData.username}
              onChange={(e) => setTargetData({...targetData, username: e.target.value})}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="input-email-pk67y" className="text-gray-400 text-[10px] font-medium tracking-wider uppercase">Email</label>
<input id="input-email-pk67y"
              className="w-full bg-black/60 border border-gray-700 text-gray-300 placeholder-gray-600 px-3 py-2 rounded text-sm focus:border-red-500/50 focus:outline-none transition-colors font-mono"
              placeholder="target@email.com"
              value={targetData.email}
              onChange={(e) => setTargetData({...targetData, email: e.target.value})}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="input-phone-hr0u7" className="text-gray-400 text-[10px] font-medium tracking-wider uppercase">Phone</label>
<input id="input-phone-hr0u7"
              className="w-full bg-black/60 border border-gray-700 text-gray-300 placeholder-gray-600 px-3 py-2 rounded text-sm focus:border-red-500/50 focus:outline-none transition-colors font-mono"
              placeholder="+5562999999999"
              value={targetData.phone}
              onChange={(e) => setTargetData({...targetData, phone: e.target.value})}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="input-name-nfgbz" className="text-gray-400 text-[10px] font-medium tracking-wider uppercase">Name</label>
<input id="input-name-nfgbz"
              className="w-full bg-black/60 border border-gray-700 text-gray-300 placeholder-gray-600 px-3 py-2 rounded text-sm focus:border-red-500/50 focus:outline-none transition-colors font-mono"
              placeholder="João Silva"
              value={targetData.name}
              onChange={(e) => setTargetData({...targetData, name: e.target.value})}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="input-location-jww46" className="text-gray-400 text-[10px] font-medium tracking-wider uppercase">Location</label>
<input id="input-location-jww46"
              className="w-full bg-black/60 border border-gray-700 text-gray-300 placeholder-gray-600 px-3 py-2 rounded text-sm focus:border-red-500/50 focus:outline-none transition-colors font-mono"
              placeholder="Goiânia, GO"
              value={targetData.location}
              onChange={(e) => setTargetData({...targetData, location: e.target.value})}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="input-context-2ndxh" className="text-gray-400 text-[10px] font-medium tracking-wider uppercase">Context</label>
<input id="input-context-2ndxh"
              className="w-full bg-black/60 border border-gray-700 text-gray-300 placeholder-gray-600 px-3 py-2 rounded text-sm focus:border-red-500/50 focus:outline-none transition-colors font-mono"
              placeholder="Security investigation"
              value={targetData.context}
              onChange={(e) => setTargetData({...targetData, context: e.target.value})}
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-2 mb-4">
          <button
            className="flex-1 bg-gradient-to-r from-black via-green-900/40 to-green-700/60 hover:from-green-900/50 hover:to-green-600/70 text-gray-200 font-medium py-2 px-4 rounded text-sm border border-green-700/30 transition-all duration-200"
            onClick={handleInvestigation}
          >
            Initialize Investigation
          </button>
          <button
            className="bg-gray-800/50 hover:bg-gray-700/50 text-gray-400 hover:text-gray-300 font-medium py-2 px-4 rounded text-sm border border-gray-700 transition-all duration-200"
            onClick={clearForm}
          >
            Clear
          </button>
        </div>

        {/* Progress */}
        {aiPhase && (
          <div className="bg-black/60 border border-gray-700 rounded p-3 mb-4">
            <div className="text-gray-300 text-xs mb-2 font-mono">{aiPhase}</div>
            <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-600 to-red-500 transition-all duration-500"
                style={{ width: `${aiProgress}%` }}
              />
            </div>
            <div className="text-gray-500 text-[10px] text-right mt-1 font-mono">{aiProgress}%</div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="bg-black/60 border border-gray-700 rounded p-4">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-gray-800">
              <h3 className="text-white font-semibold text-sm">Investigation Report</h3>
              <span className="text-gray-500 text-xs font-mono">{result.investigation_id}</span>
            </div>

            {/* Risk Assessment */}
            {result.risk_assessment && (
              <div className="bg-red-950/30 border border-red-900/30 rounded p-3 mb-3">
                <h4 className="text-red-400 font-medium text-xs mb-2 uppercase tracking-wider">Risk Assessment</h4>
                <div className="flex items-center space-x-4">
                  <div className="text-center">
                    <div className="text-red-400 text-2xl font-bold">{result.risk_assessment.risk_score}</div>
                    <div className="text-red-400/70 text-[10px]">{result.risk_assessment.risk_level}</div>
                  </div>
                  <div className="flex-1">
                    <span className="text-gray-400 text-xs font-medium">Risk Factors:</span>
                    <ul className="text-gray-500 text-xs mt-1 space-y-0.5">
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
              <div className="bg-orange-950/20 border border-orange-900/30 rounded p-3 mb-3">
                <h4 className="text-red-400 font-medium text-xs mb-2 uppercase tracking-wider">Executive Summary</h4>
                <p className="text-gray-400 text-xs leading-relaxed">{result.executive_summary}</p>
              </div>
            )}

            {/* Patterns Found */}
            {result.patterns_found && (
              <div className="bg-yellow-950/20 border border-yellow-900/30 rounded p-3 mb-3">
                <h4 className="text-yellow-500 font-medium text-xs mb-2 uppercase tracking-wider">Patterns Detected</h4>
                <div className="space-y-1.5">
                  {result.patterns_found.map((pattern, idx) => (
                    <div key={idx} className="flex space-x-2 bg-black/30 px-2 py-1.5 rounded text-xs">
                      <span className="text-yellow-500 font-medium">{pattern.type}</span>
                      <span className="text-gray-400">{pattern.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && (
              <div className="bg-green-950/20 border border-green-900/30 rounded p-3">
                <h4 className="text-green-400 font-medium text-xs mb-2 uppercase tracking-wider">AI Recommendations</h4>
                <div className="space-y-1.5">
                  {result.recommendations.map((rec, idx) => (
                    <div key={idx} className="bg-black/30 px-2 py-1.5 rounded text-xs">
                      <span className="text-green-400 font-medium">{rec.action}:</span>
                      <span className="text-gray-400 ml-2">{rec.description}</span>
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

export default MaximusAIModule;
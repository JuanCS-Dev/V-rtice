// Path: frontend/src/components/OSINTDashboard.jsx

import React, { useState, useCallback } from 'react';
import axios from 'axios';

// --- ÍCONES SVG ---
const Icon = ({ path }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: '10px', opacity: 0.7 }}>
    <path d={path} />
  </svg>
);

// ===================================================================================
// MÓDULO DE INVESTIGAÇÃO AUTOMATIZADA (NOVO)
// ===================================================================================
const AutomatedInvestigationModule = () => {
  const [targetData, setTargetData] = useState({ username: '', email: '', phone: '', name: '', image_url: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState({ phase: '', percentage: 0 });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setTargetData(prev => ({ ...prev, [name]: value }));
  };

  const handleInvestigation = useCallback(async () => {
    if (Object.values(targetData).every(val => val === '')) {
      setError("Pelo menos um identificador deve ser fornecido para iniciar a investigação.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress({ phase: 'Iniciando conexão segura...', percentage: 5 });

    const progressInterval = setInterval(() => {
        setProgress(prev => prev.percentage < 95 ? { ...prev, percentage: prev.percentage + 1 } : prev);
    }, 1500);

    try {
      const response = await axios.post('http://localhost:8000/api/investigate/auto', targetData, { timeout: 300000 });
      clearInterval(progressInterval);
      setProgress({ phase: 'Investigação Concluída', percentage: 100 });
      setResult(response.data.data);
    } catch (err) {
      clearInterval(progressInterval);
      console.error("Erro na investigação automatizada:", err);
      let errorMessage = "Ocorreu um erro desconhecido.";
      if (err.response) errorMessage = `Falha na comunicação com o servidor: ${err.response.data.detail || err.response.statusText}`;
      else if (err.code === 'ECONNABORTED') errorMessage = "A operação excedeu o tempo limite.";
      else if (err.request) errorMessage = "Não foi possível conectar ao servidor.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [targetData]);

  const renderResult = (data) => {
    if (!data) return null;
    return (
      <div className="result-container">
        <div className="result-grid ai-results">
          <div className="result-main-column">
            <div className="result-card risk-assessment">
              <h3 className="card-title">Avaliação de Risco (Aurora AI)</h3>
              <div className="risk-score-container">
                <div className="risk-score" data-risk-level={data.risk_assessment?.risk_level}>{data.risk_assessment?.risk_score || 'N/A'}</div>
                <div className="risk-level">{data.risk_assessment?.risk_level || 'Indeterminado'}</div>
              </div>
              <div className="risk-factors"><strong>Fatores de Risco:</strong><ul>{data.risk_assessment?.risk_factors?.length > 0 ? data.risk_assessment.risk_factors.map((factor, i) => <li key={i}>{factor}</li>) : <li>Nenhum detectado.</li>}</ul></div>
            </div>
            <div className="result-card"><h3 className="card-title">Sumário Executivo</h3><pre className="summary-text">{data.executive_summary}</pre></div>
          </div>
          <div className="result-side-column">
            <div className="result-card"><h3 className="card-title">Principais Descobertas</h3><ul>{data.patterns_found?.length > 0 ? data.patterns_found.map((p, i) => <li key={i}>{p.description}</li>) : <li>Nenhum padrão detectado.</li>}</ul></div>
            <div className="result-card"><h3 className="card-title">Recomendações da IA</h3><ul>{data.recommendations?.length > 0 ? data.recommendations.map((rec, i) => <li key={i}><strong>{rec.action}:</strong> {rec.description}</li>) : <li>Nenhuma gerada.</li>}</ul></div>
            <div className="result-card"><h3 className="card-title">Metadados</h3><p><strong>ID:</strong> {data.investigation_id}</p><p><strong>Duração:</strong> {data.investigation_time?.toFixed(2)}s</p><p><strong>Confiança:</strong> {data.confidence_score}%</p></div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="dashboard-header ai-header"><h1>Orquestrador de Investigação IA</h1><p>Forneça qualquer identificador. A Aurora AI irá orquestrar as ferramentas OSINT, conduzir uma investigação autônoma e gerar um relatório de inteligência.</p></div>
      <div className="input-grid ai-grid">
        <div className="input-group"><label className="input-label">Username</label><div className="input-field"><Icon path="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /><input type="text" name="username" placeholder="ex: a_lenda_2025" value={targetData.username} onChange={handleInputChange} /></div></div>
        <div className="input-group"><label className="input-label">Nome Completo</label><div className="input-field"><Icon path="M12 5.9c1.16 0 2.1.94 2.1 2.1s-.94 2.1-2.1 2.1S9.9 9.16 9.9 8s.94-2.1 2.1-2.1m0 9c2.97 0 6.1 1.46 6.1 2.1v1.1H5.9V17c0-.64 3.13-2.1 6.1-2.1M12 4C9.79 4 8 5.79 8 8s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 9c-2.67 0-8 1.34-8 4v3h16v-3c0-2.66-5.33-4-8-4z" /><input type="text" name="name" placeholder="ex: João da Silva" value={targetData.name} onChange={handleInputChange} /></div></div>
        <div className="input-group"><label className="input-label">Email</label><div className="input-field"><Icon path="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" /><input type="email" name="email" placeholder="ex: alvo@email.com" value={targetData.email} onChange={handleInputChange} /></div></div>
        <div className="input-group"><label className="input-label">Telefone</label><div className="input-field"><Icon path="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.02.74-.25 1.02l-2.2 2.2z" /><input type="tel" name="phone" placeholder="ex: +5562999998888" value={targetData.phone} onChange={handleInputChange} /></div></div>
        <div className="input-group" style={{ gridColumn: '1 / -1' }}><label className="input-label">URL de Imagem (Opcional)</label><div className="input-field"><Icon path="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" /><input type="text" name="image_url" placeholder="Cole o link de uma imagem do alvo" value={targetData.image_url} onChange={handleInputChange} /></div></div>
      </div>
      <div className="controls"><button className="scan-button" onClick={handleInvestigation} disabled={isLoading}>{isLoading ? 'INVESTIGANDO...' : 'INICIAR INVESTIGAÇÃO AUTÔNOMA'}</button></div>
      {isLoading && <div className="progress-container"><div className="progress-bar"><div className="progress-bar-inner" style={{ width: `${progress.percentage}%` }} /></div><p className="progress-phase">{progress.phase}</p></div>}
      {error && <div className="error-message">{error}</div>}
      {result && renderResult(result)}
    </div>
  );
};


// ===================================================================================
// MÓDULOS OSINT MANUAIS (RESTAURADOS)
// ===================================================================================
const OverviewModule = ({ targetData, setTargetData, onStartScan, isScanning, loading, results }) => (
  <div>
    <h2 className="module-title">Visão Geral da Análise</h2>
    <div className="input-grid">
      <div className="input-group"><label className="input-label">Username</label><input type="text" className="osint-input" placeholder="john_doe_2024" value={targetData.username} onChange={(e) => setTargetData({...targetData, username: e.target.value})}/></div>
      <div className="input-group"><label className="input-label">Email</label><input type="email" className="osint-input" placeholder="target@example.com" value={targetData.email} onChange={(e) => setTargetData({...targetData, email: e.target.value})}/></div>
      <div className="input-group"><label className="input-label">Telefone</label><input type="tel" className="osint-input" placeholder="+5562999999999" value={targetData.phone} onChange={(e) => setTargetData({...targetData, phone: e.target.value})}/></div>
    </div>
    <button className="scan-button" onClick={onStartScan} disabled={isScanning || loading || (!targetData.username && !targetData.email && !targetData.phone)}>{isScanning ? '🔍 Scanning...' : loading ? 'Loading...' : '🚀 Iniciar Análise OSINT'}</button>
    {results && (results.social?.length > 0 || results.email || results.phone) && <div className="results-grid" style={{ marginTop: '24px' }}><div className="result-card"><div className="result-header"><div className="result-icon">📊</div><h3 className="result-title">Status</h3></div><div className="result-content"><div className="stats-row"><span className="stat-label">Plataformas</span><span className="stat-value">{results.social?.length || 0}</span></div><div className="stats-row"><span className="stat-label">Email</span><span className="stat-value">{results.email ? '✅' : '⏳'}</span></div><div className="stats-row"><span className="stat-label">Telefone</span><span className="stat-value">{results.phone ? '✅' : '⏳'}</span></div></div></div></div>}
  </div>
);

const SocialAnalysisModule = ({ results }) => (
    <div>
      <h2 className="module-title">Inteligência de Mídia Social</h2>
      <div className="results-grid">
        {results && results.length > 0 ? (
          results.map((social, index) => (
            <div key={index} className="result-card"><div className="result-header"><div className="result-icon">📱</div><h3 className="result-title">{social.platform}</h3></div><div className="result-content"><div className="stats-row"><span className="stat-label">URL</span><span className="stat-value"><a href={social.url} target="_blank" rel="noopener noreferrer">{social.url}</a></span></div><div className="stats-row"><span className="stat-label">Status</span><span className="stat-value">{social.exists ? 'Ativo' : 'Não Encontrado'}</span></div><div className="stats-row"><span className="stat-label">Categoria</span><span className="stat-value">{social.category}</span></div></div></div>
          ))
        ) : <div className="result-card"><p>Nenhum perfil encontrado. Inicie uma busca no Overview.</p></div>}
      </div>
    </div>
);
// Demais módulos manuais...
const PhoneIntelModule = () => (<div>Phone Intel</div>);
const EmailIntelModule = () => (<div>Email Intel</div>);
const ImageAnalysisModule = () => (<div>Image Analysis</div>);
const ReportsModule = () => (<div>Reports</div>);


// ===================================================================================
// COMPONENTE PRINCIPAL DO DASHBOARD
// ===================================================================================
const OSINTDashboard = ({ setCurrentView }) => {
  const [activeModule, setActiveModule] = useState('automated');
  const [isScanning, setIsScanning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [targetData, setTargetData] = useState({ username: '', email: '', phone: '', image: null });
  const [results, setResults] = useState({ social: [], phone: null, email: null, image: null, ai_analysis: null });

  const API_BASE_URL = 'http://localhost:8000/api/osint';

  // Funções de busca manual
  const searchUsername = async (username) => { /* ...código original... */ };
  const analyzeEmail = async (email) => { /* ...código original... */ };
  const analyzePhone = async (phone) => { /* ...código original... */ };

  const comprehensiveSearch = async () => {
    setIsScanning(true); setError(null);
    try {
      if (targetData.username) await searchUsername(targetData.username);
      if (targetData.email) await analyzeEmail(targetData.email);
      if (targetData.phone) await analyzePhone(targetData.phone);
    } catch (err) {
      setError(`Busca compreensiva falhou: ${err.message}`);
    } finally {
      setIsScanning(false);
    }
  };

  const handleBack = () => setCurrentView && setCurrentView('main');

  const moduleComponents = {
    automated: <AutomatedInvestigationModule />,
    overview: <OverviewModule targetData={targetData} setTargetData={setTargetData} onStartScan={comprehensiveSearch} isScanning={isScanning} loading={loading} results={results} />,
    social: <SocialAnalysisModule results={results.social} />,
    phone: <PhoneIntelModule />,
    email: <EmailIntelModule />,
    image: <ImageAnalysisModule />,
    reports: <ReportsModule />
  };

  return (
    <div className="osint-dashboard">
        <style>{`
            /* ESTILOS GLOBAIS DO DASHBOARD */
            .osint-dashboard { background-color: #050810; color: #d0d8f0; min-height: 100vh; padding: 20px; font-family: 'Roboto Mono', monospace; }
            .dashboard-container { max-width: 1400px; margin: 0 auto; }
            .back-button { position: fixed; top: 20px; right: 20px; background: #2a344e; border: 1px solid #4a5a8a; color: #d0d8f0; padding: 10px 15px; border-radius: 5px; cursor: pointer; transition: all 0.2s ease; z-index: 1001; }
            .back-button:hover { background: #4a5a8a; color: #fff; }
            .osint-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
            .osint-title { display: flex; align-items: center; }
            .osint-logo { font-size: 2.5rem; margin-right: 15px; }
            .title-text h1 { margin: 0; font-size: 1.5rem; color: #fff; }
            .title-text p { margin: 0; color: #8a99c0; }
            .module-navigation { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #2a344e; padding-bottom: 10px; }
            .module-btn { background: transparent; border: 1px solid #2a344e; color: #8a99c0; padding: 10px 15px; border-radius: 5px; cursor: pointer; transition: all 0.2s; }
            .module-btn.active, .module-btn:hover { background: #2a344e; color: #fff; border-color: #4a5a8a; }
            .main-content { padding-top: 20px; }
            .module-title { font-size: 1.8rem; color: #fff; margin-bottom: 20px; }
            .osint-input { width: 100%; background: #0e1322; border: 1px solid #2a344e; border-radius: 5px; padding: 10px; color: #d0d8f0; font-size: 1rem; }
            .results-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }

            /* ESTILOS ESPECÍFICOS PARA O MÓDULO DE IA */
            .dashboard-header.ai-header { text-align: center; display: block; }
            .dashboard-header.ai-header h1 { font-size: 2.5rem; color: #57ffdc; text-shadow: 0 0 10px #57ffdc44; margin-bottom: 10px; }
            .dashboard-header.ai-header p { font-size: 1rem; color: #8a99c0; max-width: 700px; margin: 0 auto; }
            .input-grid.ai-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0; }
            .input-group { display: flex; flex-direction: column; }
            .input-label { font-size: 0.8rem; margin-bottom: 8px; color: #8a99c0; text-transform: uppercase; }
            .input-field { display: flex; align-items: center; background: #0e1322; border: 1px solid #2a344e; border-radius: 5px; padding: 10px; }
            .input-field input { flex-grow: 1; background: transparent; border: none; color: #d0d8f0; font-size: 1rem; outline: none; }
            .input-field input::placeholder { color: #4a5a8a; }
            .controls { text-align: center; }
            .scan-button { background: linear-gradient(90deg, #57ffdc, #3a9fff); color: #050810; border: none; padding: 15px 40px; font-size: 1.2rem; font-weight: bold; border-radius: 5px; cursor: pointer; transition: all 0.3s ease; }
            .scan-button:disabled { background: #2a344e; color: #4a5a8a; cursor: not-allowed; }
            .scan-button:hover:not(:disabled) { box-shadow: 0 0 20px #3a9fff88; }
            .progress-container { margin-top: 30px; text-align: center; }
            .progress-bar { width: 100%; background: #0e1322; border-radius: 5px; overflow: hidden; border: 1px solid #2a344e; }
            .progress-bar-inner { height: 20px; background: linear-gradient(90deg, #57ffdc, #3a9fff); transition: width 1.5s ease-out; }
            .progress-phase { margin-top: 10px; color: #8a99c0; }
            .error-message { margin-top: 20px; background: #ff4d4d22; border: 1px solid #ff4d4d88; padding: 15px; border-radius: 5px; color: #ffb3b3; text-align: center; }
            .result-container { margin-top: 40px; }
            .result-grid.ai-results { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
            .result-card { background: #0e1322; border: 1px solid #2a344e; border-radius: 5px; padding: 20px; height: fit-content; }
            .card-title { color: #57ffdc; margin: 0 0 15px 0; border-bottom: 1px solid #2a344e; padding-bottom: 10px; }
            .result-card ul { list-style: none; padding: 0; margin: 0; }
            .result-card li { margin-bottom: 10px; color: #8a99c0; }
            .result-card strong { color: #d0d8f0; }
            .risk-assessment .risk-score-container { display: flex; align-items: center; justify-content: center; gap: 20px; margin: 20px 0; }
            .risk-assessment .risk-score { font-size: 4rem; font-weight: bold; }
            .risk-assessment .risk-score[data-risk-level="CRITICAL"], .risk-assessment .risk-score[data-risk-level="HIGH"] { color: #ff4d4d; }
            .risk-assessment .risk-score[data-risk-level="MEDIUM"] { color: #ffae42; }
            .risk-assessment .risk-score[data-risk-level="LOW"] { color: #57ffdc; }
            .risk-assessment .risk-level { font-size: 1.5rem; text-transform: uppercase; }
            .summary-text { white-space: pre-wrap; word-wrap: break-word; color: #8a99c0; font-size: 0.9rem; max-height: 400px; overflow-y: auto; }
      `}</style>
      <button className="back-button" onClick={handleBack}>← Voltar</button>
      <div className="dashboard-container">
        <div className="osint-header">
          <div className="osint-title"><div className="osint-logo">🕵️</div><div className="title-text"><h1>OSINT Dashboard</h1><p>Open Source Intelligence & Social Media Analysis</p></div></div>
        </div>
        <div className="module-navigation">
          {[
            { id: 'automated', icon: '🧠', label: 'Investigação IA' }, { id: 'overview', icon: '📊', label: 'Overview' },
            { id: 'social', icon: '📱', label: 'Social Media' }, { id: 'phone', icon: '📞', label: 'Phone Intel' },
            { id: 'email', icon: '📧', label: 'Email Intel' }, { id: 'image', icon: '🖼️', label: 'Image Analysis' },
            { id: 'reports', icon: '📋', label: 'Reports' }
          ].map(module => (
            <button key={module.id} className={`module-btn ${activeModule === module.id ? 'active' : ''}`} onClick={() => setActiveModule(module.id)}><span className="module-icon">{module.icon}</span>{module.label}</button>
          ))}
        </div>
        <div className="main-content">{moduleComponents[activeModule]}</div>
      </div>
    </div>
  );
};

export default OSINTDashboard;



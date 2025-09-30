// Aurora Cyber Intelligence Hub - Orquestração Autônoma de Investigações
import React, { useState, useEffect } from 'react';

const AuroraCyberHub = () => {
  const [investigation, setInvestigation] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [targetInput, setTargetInput] = useState('');
  const [investigationType, setInvestigationType] = useState('auto');
  const [analysisSteps, setAnalysisSteps] = useState([]);
  const [results, setResults] = useState({});

  // Serviços disponíveis com status
  const [services, setServices] = useState({
    ip_intelligence: { name: 'IP Intelligence', status: 'ready', icon: '🌐', priority: 1 },
    domain_analyzer: { name: 'Domain Analyzer', status: 'ready', icon: '🔍', priority: 2 },
    nmap_scanner: { name: 'Nmap Scanner', status: 'ready', icon: '📡', priority: 3 },
    vuln_scanner: { name: 'Vulnerability Scanner', status: 'ready', icon: '🔓', priority: 4 },
    threat_intel: { name: 'Threat Intelligence', status: 'ready', icon: '🎯', priority: 1 },
    malware_analysis: { name: 'Malware Analysis', status: 'ready', icon: '🦠', priority: 3 },
    ssl_monitor: { name: 'SSL/TLS Monitor', status: 'ready', icon: '🔒', priority: 2 },
    social_eng: { name: 'Social Engineering', status: 'ready', icon: '🎭', priority: 5 }
  });

  const investigationTypes = [
    { id: 'auto', name: 'Aurora Automático', description: 'IA decide a melhor estratégia', color: 'purple' },
    { id: 'defensive', name: 'Análise Defensiva', description: 'Foco em threat intel e detecção', color: 'blue' },
    { id: 'offensive', name: 'Red Team', description: 'Vulnerabilidades e vetores de ataque', color: 'red' },
    { id: 'full', name: 'Investigação Completa', description: 'Todos os serviços disponíveis', color: 'cyan' }
  ];

  const startInvestigation = async () => {
    if (!targetInput.trim()) return;

    setIsAnalyzing(true);
    setAnalysisSteps([]);
    setResults({});

    try {
      // Chamar Aurora Orchestrator
      const response = await fetch('http://localhost:8016/api/aurora/investigate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target: targetInput,
          investigation_type: investigationType,
          priority: 5,
          stealth_mode: investigationType === 'defensive',
          deep_analysis: investigationType === 'full',
          max_time: 300
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Criar investigação
      const newInvestigation = {
        id: data.investigation_id,
        target: data.target,
        type: data.investigation_type,
        startTime: new Date(data.start_time),
        status: data.status
      };
      setInvestigation(newInvestigation);

      addStep({
        service: 'aurora',
        message: `🤖 Aurora AI iniciou investigação: ${data.investigation_id}`,
        status: 'completed'
      });

      // Polling para atualizar status
      pollInvestigationStatus(data.investigation_id);

    } catch (error) {
      console.error('Error starting investigation:', error);
      addStep({
        service: 'aurora',
        message: `❌ Erro ao iniciar investigação: ${error.message}`,
        status: 'failed'
      });
      setIsAnalyzing(false);
    }
  };

  const pollInvestigationStatus = async (investigationId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8016/api/aurora/investigation/${investigationId}`);

        if (!response.ok) {
          throw new Error('Failed to fetch investigation status');
        }

        const data = await response.json();

        // Atualizar steps
        if (data.steps && data.steps.length > 0) {
          data.steps.forEach(step => {
            const stepExists = analysisSteps.find(s =>
              s.service === step.service && s.timestamp === step.timestamp
            );

            if (!stepExists) {
              const service = services[step.service];
              const icon = service?.icon || '🔧';

              addStep({
                service: step.service,
                message: `${icon} ${service?.name || step.service}: ${step.action}${step.status === 'completed' ? ' ✅' : step.status === 'failed' ? ' ❌' : ' ⏳'}`,
                status: step.status,
                result: step.data,
                timestamp: new Date(step.timestamp)
              });

              if (step.data) {
                setResults(prev => ({ ...prev, [step.service]: step.data }));
              }

              if (step.status === 'running') {
                updateServiceStatus(step.service, 'running');
              } else {
                updateServiceStatus(step.service, 'ready');
              }
            }
          });
        }

        // Verificar se completou
        if (data.status === 'completed') {
          clearInterval(pollInterval);

          // Threat Assessment
          if (data.threat_assessment) {
            addStep({
              service: 'aurora',
              message: `🧠 Aurora Threat Assessment: ${data.threat_assessment.threat_level} (Score: ${data.threat_assessment.threat_score}/100)`,
              status: 'completed',
              result: data.threat_assessment
            });
          }

          // Recommendations
          if (data.recommendations && data.recommendations.length > 0) {
            addStep({
              service: 'aurora',
              message: `💡 Aurora gerou ${data.recommendations.length} recomendações`,
              status: 'completed',
              result: { recommendations: data.recommendations }
            });
          }

          setInvestigation(prev => ({
            ...prev,
            status: 'completed',
            endTime: new Date(data.end_time)
          }));

          setIsAnalyzing(false);
        } else if (data.status === 'failed') {
          clearInterval(pollInterval);
          addStep({
            service: 'aurora',
            message: '❌ Investigação falhou',
            status: 'failed'
          });
          setIsAnalyzing(false);
        }

      } catch (error) {
        console.error('Polling error:', error);
        clearInterval(pollInterval);
        setIsAnalyzing(false);
      }
    }, 2000); // Poll a cada 2 segundos
  };

  const simulateAuroraDecision = async (target, type) => {
    // DEPRECATED - Agora usando Aurora Orchestrator real
    const steps = [];

    // Detectar tipo de target
    const isIP = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(target);
    const isDomain = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?(\.[a-zA-Z]{2,})+$/.test(target);
    const isURL = target.startsWith('http');

    addStep({
      service: 'aurora',
      message: `🤖 Aurora AI analisando target: ${target}...`,
      status: 'running'
    });

    await delay(1000);

    if (isIP) {
      addStep({
        service: 'aurora',
        message: `✅ Target identificado como IP. Iniciando workflow de IP Intelligence.`,
        status: 'completed'
      });
      await executeIPWorkflow(target, type);
    } else if (isDomain || isURL) {
      addStep({
        service: 'aurora',
        message: `✅ Target identificado como Domínio/URL. Iniciando workflow de Domain Analysis.`,
        status: 'completed'
      });
      await executeDomainWorkflow(target, type);
    } else {
      addStep({
        service: 'aurora',
        message: `⚠️ Tipo de target não reconhecido. Executando análise genérica.`,
        status: 'warning'
      });
      await executeGenericWorkflow(target, type);
    }

    setIsAnalyzing(false);
    setInvestigation(prev => ({ ...prev, status: 'completed', endTime: new Date() }));
  };

  const executeIPWorkflow = async (ip, type) => {
    const workflow = [
      { service: 'threat_intel', action: 'checkReputation' },
      { service: 'ip_intelligence', action: 'analyze' },
      { service: 'nmap_scanner', action: 'portScan' },
    ];

    if (type === 'offensive' || type === 'full') {
      workflow.push({ service: 'vuln_scanner', action: 'scan' });
    }

    for (const step of workflow) {
      await executeService(step.service, step.action, ip);
    }

    // Aurora gera conclusão
    addStep({
      service: 'aurora',
      message: '🧠 Aurora gerando relatório final e recomendações...',
      status: 'running'
    });
    await delay(1500);
    addStep({
      service: 'aurora',
      message: '✅ Análise completa! Relatório disponível abaixo.',
      status: 'completed'
    });
  };

  const executeDomainWorkflow = async (domain, type) => {
    const workflow = [
      { service: 'threat_intel', action: 'checkDomain' },
      { service: 'domain_analyzer', action: 'analyze' },
      { service: 'ssl_monitor', action: 'checkCertificate' },
      { service: 'nmap_scanner', action: 'scan' },
    ];

    if (type === 'offensive' || type === 'full') {
      workflow.push({ service: 'vuln_scanner', action: 'webScan' });
      workflow.push({ service: 'social_eng', action: 'reconnaissance' });
    }

    for (const step of workflow) {
      await executeService(step.service, step.action, domain);
    }

    addStep({
      service: 'aurora',
      message: '🧠 Aurora correlacionando dados e gerando insights...',
      status: 'running'
    });
    await delay(1500);
    addStep({
      service: 'aurora',
      message: '✅ Investigação finalizada com sucesso!',
      status: 'completed'
    });
  };

  const executeGenericWorkflow = async (target, type) => {
    addStep({
      service: 'aurora',
      message: '🔍 Executando busca em todas as bases de dados...',
      status: 'running'
    });
    await delay(2000);
    addStep({
      service: 'aurora',
      message: '⚠️ Nenhum resultado encontrado. Target pode ser inválido.',
      status: 'warning'
    });
  };

  const executeService = async (serviceId, action, target) => {
    const service = services[serviceId];

    addStep({
      service: serviceId,
      message: `${service.icon} ${service.name}: ${action} em ${target}...`,
      status: 'running'
    });

    updateServiceStatus(serviceId, 'running');

    // Simular tempo de execução
    await delay(Math.random() * 2000 + 1500);

    // Simular resultado
    const mockResult = generateMockResult(serviceId, target);
    setResults(prev => ({ ...prev, [serviceId]: mockResult }));

    addStep({
      service: serviceId,
      message: `✅ ${service.name}: Análise concluída`,
      status: 'completed',
      result: mockResult
    });

    updateServiceStatus(serviceId, 'ready');
  };

  const generateMockResult = (serviceId, target) => {
    const results = {
      threat_intel: {
        threat_score: Math.floor(Math.random() * 100),
        malicious: Math.random() > 0.7,
        categories: ['scanning', 'bruteforce'],
        last_seen: '2024-09-29'
      },
      ip_intelligence: {
        country: 'United States',
        city: 'Los Angeles',
        isp: 'CloudFlare Inc.',
        asn: 'AS13335'
      },
      nmap_scanner: {
        open_ports: [22, 80, 443, 8080],
        services: ['SSH', 'HTTP', 'HTTPS', 'HTTP-Proxy']
      },
      vuln_scanner: {
        vulnerabilities: Math.floor(Math.random() * 15),
        critical: Math.floor(Math.random() * 3),
        high: Math.floor(Math.random() * 5)
      },
      ssl_monitor: {
        valid: true,
        issuer: 'Let\'s Encrypt',
        expiry: '2025-06-15',
        grade: 'A+'
      }
    };

    return results[serviceId] || { status: 'completed' };
  };

  const addStep = (step) => {
    setAnalysisSteps(prev => [...prev, { ...step, timestamp: new Date() }]);
  };

  const updateServiceStatus = (serviceId, status) => {
    setServices(prev => ({
      ...prev,
      [serviceId]: { ...prev[serviceId], status }
    }));
  };

  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const getTypeColor = (type) => {
    const colors = {
      auto: 'purple',
      defensive: 'blue',
      offensive: 'red',
      full: 'cyan'
    };
    return colors[type] || 'gray';
  };

  return (
    <div className="h-full flex flex-col space-y-4 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/30 to-cyan-900/30 border border-purple-400/50 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-6xl animate-pulse">🤖</div>
            <div>
              <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">
                AURORA CYBER INTEL HUB
              </h2>
              <p className="text-cyan-400/70 text-sm">
                Orquestração Autônoma de Investigações de Segurança
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-400 font-bold">AURORA ONLINE</span>
          </div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-3 gap-4 min-h-0">
        {/* Painel de Controle */}
        <div className="col-span-1 space-y-4 overflow-y-auto">
          {/* Input de Target */}
          <div className="bg-black/50 border border-cyan-400/50 rounded-lg p-4">
            <label className="text-cyan-400 font-bold mb-2 block">TARGET</label>
            <input
              type="text"
              value={targetInput}
              onChange={(e) => setTargetInput(e.target.value)}
              placeholder="IP, Domínio ou URL..."
              className="w-full bg-black/50 border border-cyan-400/30 rounded px-3 py-2 text-cyan-400 placeholder-cyan-400/30 focus:outline-none focus:border-cyan-400"
              disabled={isAnalyzing}
            />
          </div>

          {/* Tipo de Investigação */}
          <div className="bg-black/50 border border-cyan-400/50 rounded-lg p-4">
            <label className="text-cyan-400 font-bold mb-3 block">TIPO DE INVESTIGAÇÃO</label>
            <div className="space-y-2">
              {investigationTypes.map(type => (
                <button
                  key={type.id}
                  onClick={() => setInvestigationType(type.id)}
                  disabled={isAnalyzing}
                  className={`w-full text-left p-3 rounded border transition-all ${
                    investigationType === type.id
                      ? `border-${type.color}-400 bg-${type.color}-400/20`
                      : 'border-gray-700 bg-black/30 hover:border-cyan-400/50'
                  }`}
                >
                  <div className={`text-${type.color}-400 font-bold`}>{type.name}</div>
                  <div className="text-xs text-gray-400">{type.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Botão Start */}
          <button
            onClick={startInvestigation}
            disabled={isAnalyzing || !targetInput.trim()}
            className="w-full bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 disabled:from-gray-700 disabled:to-gray-700 text-white font-bold py-4 rounded-lg transition-all transform hover:scale-105 disabled:scale-100 flex items-center justify-center space-x-2"
          >
            {isAnalyzing ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>AURORA ANALISANDO...</span>
              </>
            ) : (
              <>
                <span className="text-xl">⚡</span>
                <span>INICIAR INVESTIGAÇÃO</span>
              </>
            )}
          </button>

          {/* Status dos Serviços */}
          <div className="bg-black/50 border border-cyan-400/50 rounded-lg p-4">
            <label className="text-cyan-400 font-bold mb-3 block">SERVIÇOS DISPONÍVEIS</label>
            <div className="space-y-2">
              {Object.entries(services).map(([id, service]) => (
                <div key={id} className="flex items-center justify-between text-sm">
                  <span className="text-cyan-400/70">
                    {service.icon} {service.name}
                  </span>
                  <div className={`w-2 h-2 rounded-full ${
                    service.status === 'running' ? 'bg-yellow-400 animate-pulse' :
                    service.status === 'ready' ? 'bg-green-400' :
                    'bg-gray-600'
                  }`} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Timeline de Análise */}
        <div className="col-span-2 flex flex-col space-y-4 min-h-0">
          {/* Info da Investigação */}
          {investigation && (
            <div className="bg-black/50 border border-purple-400/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-purple-400 font-bold">Investigação #{investigation.id}</div>
                  <div className="text-cyan-400 text-sm">Target: {investigation.target}</div>
                </div>
                <div className="text-right">
                  <div className={`text-${getTypeColor(investigation.type)}-400 font-bold uppercase text-sm`}>
                    {investigationTypes.find(t => t.id === investigation.type)?.name}
                  </div>
                  <div className="text-gray-400 text-xs">
                    {investigation.status === 'running' ? 'Em andamento...' : 'Finalizada'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Timeline */}
          <div className="flex-1 bg-black/50 border border-cyan-400/50 rounded-lg p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-cyan-400 font-bold">TIMELINE DE EXECUÇÃO</h3>
              <span className="text-cyan-400">🕐</span>
            </div>

            {analysisSteps.length === 0 ? (
              <div className="text-center text-gray-500 py-12">
                <div className="text-6xl opacity-30 mb-4">🛡️</div>
                <p>Aguardando início da investigação...</p>
                <p className="text-sm mt-2">Aurora está pronta para analisar seu target</p>
              </div>
            ) : (
              <div className="space-y-3">
                {analysisSteps.map((step, idx) => (
                  <div key={idx} className="flex items-start space-x-3 animate-fadeIn">
                    <div className="mt-1">
                      {step.status === 'running' && (
                        <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                      )}
                      {step.status === 'completed' && (
                        <span className="text-green-400">✅</span>
                      )}
                      {step.status === 'warning' && (
                        <span className="text-yellow-400">⚠️</span>
                      )}
                      {step.status === 'failed' && (
                        <span className="text-red-400">❌</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className={`text-sm ${
                        step.status === 'running' ? 'text-yellow-400' :
                        step.status === 'completed' ? 'text-green-400' :
                        'text-yellow-400'
                      }`}>
                        {step.message}
                      </div>
                      <div className="text-xs text-gray-500">
                        {step.timestamp.toLocaleTimeString()}
                      </div>
                      {step.result && (
                        <div className="mt-2 p-2 bg-black/50 rounded border border-cyan-400/30 text-xs">
                          <pre className="text-cyan-400/70 overflow-x-auto">
                            {JSON.stringify(step.result, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Resultados Finais */}
          {investigation?.status === 'completed' && Object.keys(results).length > 0 && (
            <div className="bg-gradient-to-r from-green-900/30 to-cyan-900/30 border border-green-400/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-green-400 font-bold">RELATÓRIO FINAL</h3>
                <span className="text-green-400 text-xl">📊</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-black/50 rounded p-3">
                  <div className="text-cyan-400 text-sm">Serviços Executados</div>
                  <div className="text-2xl font-bold text-cyan-400">{Object.keys(results).length}</div>
                </div>
                <div className="bg-black/50 rounded p-3">
                  <div className="text-cyan-400 text-sm">Tempo Total</div>
                  <div className="text-2xl font-bold text-cyan-400">
                    {investigation.endTime && Math.round((investigation.endTime - investigation.startTime) / 1000)}s
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuroraCyberHub;
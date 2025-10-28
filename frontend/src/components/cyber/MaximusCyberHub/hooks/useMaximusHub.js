import { useState } from 'react';
import logger from '@/utils/logger';
import { API_ENDPOINTS } from '@/config/api';

const INITIAL_SERVICES = {
  ip_intelligence: { name: 'IP Intelligence', status: 'ready', icon: '🌐', priority: 1 },
  domain_analyzer: { name: 'Domain Analyzer', status: 'ready', icon: '🔍', priority: 2 },
  nmap_scanner: { name: 'Nmap Scanner', status: 'ready', icon: '📡', priority: 3 },
  vuln_scanner: { name: 'Vulnerability Scanner', status: 'ready', icon: '🔓', priority: 4 },
  threat_intel: { name: 'Threat Intelligence', status: 'ready', icon: '🎯', priority: 1 },
  malware_analysis: { name: 'Malware Analysis', status: 'ready', icon: '🦠', priority: 3 },
  ssl_monitor: { name: 'SSL/TLS Monitor', status: 'ready', icon: '🔒', priority: 2 },
  social_eng: { name: 'Social Engineering', status: 'ready', icon: '🎭', priority: 5 }
};

export const useMaximusHub = () => {
  const [investigation, setInvestigation] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [targetInput, setTargetInput] = useState('');
  const [investigationType, setInvestigationType] = useState('auto');
  const [analysisSteps, setAnalysisSteps] = useState([]);
  const [results, setResults] = useState({});
  const [services, setServices] = useState(INITIAL_SERVICES);

  const addStep = (step) => {
    setAnalysisSteps(prev => [...prev, { ...step, timestamp: new Date() }]);
  };

  const updateServiceStatus = (serviceId, status) => {
    setServices(prev => ({
      ...prev,
      [serviceId]: { ...prev[serviceId], status }
    }));
  };

  const pollInvestigationStatus = async (investigationId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.aurora}/investigation/${investigationId}`);

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
              message: `🧠 Maximus Threat Assessment: ${data.threat_assessment.threat_level} (Score: ${data.threat_assessment.threat_score}/100)`,
              status: 'completed',
              result: data.threat_assessment
            });
          }

          // Recommendations
          if (data.recommendations && data.recommendations.length > 0) {
            addStep({
              service: 'aurora',
              message: `💡 Maximus gerou ${data.recommendations.length} recomendações`,
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
        logger.error('Polling error:', error);
        clearInterval(pollInterval);
        setIsAnalyzing(false);
      }
    }, 2000); // Poll a cada 2 segundos
  };

  const startInvestigation = async () => {
    if (!targetInput.trim()) return;

    setIsAnalyzing(true);
    setAnalysisSteps([]);
    setResults({});

    try {
      const response = await fetch(`${API_ENDPOINTS.aurora}/investigate`, {
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
        message: `🤖 Maximus AI iniciou investigação: ${data.investigation_id}`,
        status: 'completed'
      });

      pollInvestigationStatus(data.investigation_id);

    } catch (error) {
      logger.error('Error starting investigation:', error);
      addStep({
        service: 'aurora',
        message: `❌ Erro ao iniciar investigação: ${error.message}`,
        status: 'failed'
      });
      setIsAnalyzing(false);
    }
  };

  return {
    investigation,
    isAnalyzing,
    targetInput,
    setTargetInput,
    investigationType,
    setInvestigationType,
    analysisSteps,
    results,
    services,
    startInvestigation
  };
};

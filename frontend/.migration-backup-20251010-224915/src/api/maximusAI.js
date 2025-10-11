/**
 * Maximus AI Core - API Client
 * =============================
 *
 * Cliente para o CORE de inteligência artificial do sistema.
 * O Maximus AI é o maestro que orquestra TODOS os serviços com AI real.
 *
 * Features:
 * - AI Analysis & Reasoning
 * - Tool Calling (Function Calling)
 * - Multi-Service Orchestration
 * - Memory & Context Management
 * - Real-time Streaming
 *
 * Port: 8001 (maximus_core_service)
 */

const MAXIMUS_BASE_URL = 'http://localhost:8001';

/**
 * ============================================================================
 * AI ANALYSIS & REASONING
 * ============================================================================
 */

/**
 * Analisa qualquer dado com inteligência artificial
 */
export const analyzeWithAI = async (data, context = {}) => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data,
        context,
        mode: 'deep_analysis',
      }),
    });

    if (!response.ok) throw new Error(`AI Analysis failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error in AI analysis:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Reasoning Engine - Processamento com Chain-of-Thought
 */
export const aiReason = async (query, reasoningType = 'chain_of_thought') => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/reason`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        reasoning_type: reasoningType, // 'chain_of_thought' | 'step_by_step' | 'tree_of_thoughts'
      }),
    });

    if (!response.ok) throw new Error(`Reasoning failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error in AI reasoning:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * TOOL CALLING (FUNCTION CALLING)
 * ============================================================================
 */

/**
 * Executa tool call - AI chama funções/ferramentas
 */
export const callTool = async (toolName, params = {}, context = {}) => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/tool-call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tool_name: toolName,
        params,
        context,
      }),
    });

    if (!response.ok) throw new Error(`Tool call failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error calling tool:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Lista todas as ferramentas disponíveis
 */
export const getToolCatalog = async () => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/tools`);
    if (!response.ok) throw new Error(`Failed to get tools: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error getting tool catalog:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * ORCHESTRATION & WORKFLOWS
 * ============================================================================
 */

/**
 * Orquestra workflow multi-serviço com AI
 */
export const orchestrateWorkflow = async (workflowConfig) => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/orchestrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflowConfig),
    });

    if (!response.ok) throw new Error(`Orchestration failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error in orchestration:', error);
    return { success: false, error: error.message };
  }
};

/**
 * AI-driven workflow: Full Assessment
 */
export const aiFullAssessment = async (target, options = {}) => {
  const workflow = {
    type: 'full_assessment',
    target,
    steps: [
      { action: 'network_recon', params: { target, scan_type: options.scanType || 'quick' } },
      { action: 'vuln_intel', params: { correlate: true } },
      { action: 'web_attack', params: { profile: 'owasp' }, condition: 'if_http_found' },
      { action: 'threat_intel', params: { aggregate: true } },
      { action: 'ai_synthesis', params: { generate_report: true } },
    ],
    ai_guided: true,
  };

  return await orchestrateWorkflow(workflow);
};

/**
 * AI-driven workflow: OSINT Investigation
 */
export const aiOSINTInvestigation = async (target, type = 'email') => {
  const workflow = {
    type: 'osint_investigation',
    target,
    target_type: type,
    steps: [
      { action: 'breach_data_search', params: { target } },
      { action: 'social_media_profiling', params: { target } },
      { action: 'domain_correlation', params: { target } },
      { action: 'threat_intel_check', params: { target } },
      { action: 'ai_dossier_generation', params: { format: 'executive' } },
    ],
    ai_guided: true,
  };

  return await orchestrateWorkflow(workflow);
};

/**
 * AI-driven workflow: Purple Team Exercise
 */
export const aiPurpleTeamExercise = async (techniqueId, target, telemetrySources = []) => {
  const workflow = {
    type: 'purple_team',
    technique: techniqueId,
    target,
    steps: [
      { action: 'bas_simulation', params: { technique_id: techniqueId, target } },
      { action: 'siem_correlation', params: { sources: telemetrySources } },
      { action: 'coverage_analysis', params: {} },
      { action: 'gap_identification', params: {} },
      { action: 'ai_recommendations', params: { include_mitigations: true } },
    ],
    ai_guided: true,
  };

  return await orchestrateWorkflow(workflow);
};

/**
 * ============================================================================
 * MEMORY & CONTEXT
 * ============================================================================
 */

/**
 * Obtém memória/contexto da AI
 */
export const getAIMemory = async (sessionId = null, type = 'all') => {
  try {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    if (type !== 'all') params.append('type', type); // 'short_term' | 'long_term' | 'semantic'

    const response = await fetch(`${MAXIMUS_BASE_URL}/api/memory?${params}`);
    if (!response.ok) throw new Error(`Failed to get memory: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error getting AI memory:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Adiciona informação à memória da AI
 */
export const addToMemory = async (data, type = 'semantic', importance = 'medium') => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/memory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data,
        memory_type: type,
        importance,
      }),
    });

    if (!response.ok) throw new Error(`Failed to add to memory: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error adding to memory:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * CHAT & STREAMING
 * ============================================================================
 */

/**
 * Chat com Maximus AI (streaming)
 */
export const chatWithMaximus = async (message, context = {}, onChunk = null) => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        context,
        stream: !!onChunk,
      }),
    });

    if (!response.ok) throw new Error(`Chat failed: ${response.status}`);

    // Streaming response
    if (onChunk && response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        fullResponse += chunk;
        onChunk(chunk, fullResponse);
      }

      return { success: true, response: fullResponse };
    }

    // Non-streaming
    const data = await response.json();
    return { success: true, ...data };
  } catch (error) {
    console.error('Error in chat:', error);
    return { success: false, error: error.message };
  }
};

/**
 * WebSocket connection para streaming real-time
 */
export const connectMaximusStream = (onMessage, onError = null) => {
  const ws = new WebSocket(`ws://localhost:8001/ws/stream`);

  ws.onopen = () => {
    console.log('🤖 Maximus AI Stream connected');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };

  ws.onclose = () => {
    console.log('🤖 Maximus AI Stream disconnected');
  };

  return ws;
};

/**
 * ============================================================================
 * OFFENSIVE ARSENAL INTEGRATION
 * ============================================================================
 */

/**
 * AI-powered Network Reconnaissance
 */
export const aiNetworkRecon = async (target, options = {}) => {
  return await callTool('network_recon_tool', {
    target,
    scan_type: options.scanType || 'quick',
    ports: options.ports || '1-1000',
  });
};

/**
 * AI-powered Vulnerability Intelligence
 */
export const aiVulnIntel = async (identifier, type = 'cve') => {
  return await callTool('vuln_intel_tool', {
    identifier,
    type, // 'cve' | 'product' | 'vendor'
  });
};

/**
 * AI-powered Web Attack Analysis
 */
export const aiWebAttack = async (url, profile = 'full') => {
  return await callTool('web_attack_tool', {
    url,
    profile,
  });
};

/**
 * AI-powered C2 Orchestration
 */
export const aiC2Orchestration = async (action, params = {}) => {
  return await callTool('c2_orchestration_tool', {
    action, // 'create_session' | 'execute_command' | 'pass_session' | 'attack_chain'
    ...params,
  });
};

/**
 * AI-powered BAS Simulation
 */
export const aiBASSimulation = async (techniqueId, target, platform = 'windows') => {
  return await callTool('bas_simulation_tool', {
    technique_id: techniqueId,
    target,
    platform,
  });
};

/**
 * ============================================================================
 * INTELLIGENCE SYNTHESIS
 * ============================================================================
 */

/**
 * Síntese inteligente de múltiplas fontes
 */
export const synthesizeIntelligence = async (sources, query = null) => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sources, // Array de dados de diferentes serviços
        query,
        include_recommendations: true,
      }),
    });

    if (!response.ok) throw new Error(`Synthesis failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error synthesizing intelligence:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Auto-suggest baseado em contexto
 */
export const getAISuggestions = async (context, type = 'next_action') => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        context,
        suggestion_type: type, // 'next_action' | 'targets' | 'techniques' | 'mitigations'
      }),
    });

    if (!response.ok) throw new Error(`Suggestions failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error getting suggestions:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * FASE 8: ENHANCED COGNITION
 * ============================================================================
 */

/**
 * Análise de narrativas (social engineering, propaganda, bots)
 */
export const analyzeNarrative = async (text, analysisType = 'comprehensive', options = {}) => {
  return await callTool('analyze_narrative', {
    text,
    analysis_type: analysisType,
    detect_bots: options.detectBots !== false,
    track_memes: options.trackMemes !== false,
  });
};

/**
 * Predição de ameaças futuras (time-series, Bayesian inference)
 */
export const predictThreats = async (context, options = {}) => {
  return await callTool('predict_threats', {
    context,
    time_horizon_hours: options.timeHorizon || 24,
    min_confidence: options.minConfidence || 0.6,
    include_vuln_forecast: options.includeVulnForecast !== false,
  });
};

/**
 * Hunting proativo - recomendações
 */
export const huntProactively = async (assetInventory = null, threatIntel = null) => {
  return await callTool('hunt_proactively', {
    asset_inventory: assetInventory || [],
    threat_intel: threatIntel || {},
  });
};

/**
 * Investigação autônoma com playbooks
 */
export const investigateIncident = async (incidentId, options = {}) => {
  return await callTool('investigate_incident', {
    incident_id: incidentId,
    playbook: options.playbook || 'standard',
    enable_actor_profiling: options.actorProfiling !== false,
    enable_campaign_correlation: options.campaignCorrelation !== false,
  });
};

/**
 * Correlação de campanhas de ataque
 */
export const correlateCampaigns = async (incidents, options = {}) => {
  return await callTool('correlate_campaigns', {
    incidents,
    time_window_days: options.timeWindow || 30,
    correlation_threshold: options.threshold || 0.6,
  });
};

/**
 * ============================================================================
 * FASE 9: IMMUNE ENHANCEMENT
 * ============================================================================
 */

/**
 * Supressão de falsos positivos (Regulatory T-Cells)
 */
export const suppressFalsePositives = async (alerts, suppressionThreshold = 0.6) => {
  return await callTool('suppress_false_positives', {
    alerts,
    suppression_threshold: suppressionThreshold,
  });
};

/**
 * Obtém perfil de tolerância imune para entidade
 */
export const getToleranceProfile = async (entityId, entityType = 'ip') => {
  return await callTool('get_tolerance_profile', {
    entity_id: entityId,
    entity_type: entityType,
  });
};

/**
 * Trigger consolidação de memória (STM → LTM)
 */
export const consolidateMemory = async (options = {}) => {
  return await callTool('consolidate_memory', {
    trigger_manual: options.manual || false,
    importance_threshold: options.threshold || 0.6,
  });
};

/**
 * Query memória imunológica de longo prazo
 */
export const queryLongTermMemory = async (query, options = {}) => {
  return await callTool('query_long_term_memory', {
    query,
    limit: options.limit || 10,
    min_importance: options.minImportance || 0.5,
  });
};

/**
 * Diversificação de anticorpos (V(D)J recombination)
 */
export const diversifyAntibodies = async (threatSamples, repertoireSize = 100) => {
  return await callTool('diversify_antibodies', {
    threat_samples: threatSamples,
    repertoire_size: repertoireSize,
  });
};

/**
 * Affinity maturation (somatic hypermutation)
 */
export const runAffinityMaturation = async (feedbackData) => {
  return await callTool('run_affinity_maturation', feedbackData);
};

/**
 * ============================================================================
 * FASE 10: DISTRIBUTED ORGANISM
 * ============================================================================
 */

/**
 * Status de edge agents
 */
export const getEdgeStatus = async (agentId = null) => {
  return await callTool('get_edge_status', {
    agent_id: agentId,
  });
};

/**
 * Coordenação de scan multi-edge
 */
export const coordinateMultiEdgeScan = async (targets, options = {}) => {
  return await callTool('coordinate_multi_edge_scan', {
    targets,
    scan_type: options.scanType || 'comprehensive',
    distribute_load: options.distributeLoad !== false,
  });
};

/**
 * Métricas globais agregadas
 */
export const getGlobalMetrics = async (timeRangeMinutes = 60) => {
  return await callTool('get_global_metrics', {
    time_range_minutes: timeRangeMinutes,
  });
};

/**
 * Topologia do organismo distribuído
 */
export const getTopology = async () => {
  return await callTool('get_topology', {});
};

/**
 * ============================================================================
 * HEALTH & STATUS
 * ============================================================================
 */

/**
 * Verifica status do Maximus AI Core
 */
export const getMaximusHealth = async () => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/health`);
    if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Maximus health check failed:', error);
    return { success: false, error: error.message, status: 'offline' };
  }
};

/**
 * Obtém estatísticas da AI
 */
export const getAIStats = async () => {
  try {
    const response = await fetch(`${MAXIMUS_BASE_URL}/api/stats`);
    if (!response.ok) throw new Error(`Stats failed: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error getting AI stats:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * EXPORTS
 * ============================================================================
 */

export default {
  // Analysis & Reasoning
  analyzeWithAI,
  aiReason,

  // Tool Calling
  callTool,
  getToolCatalog,

  // Orchestration
  orchestrateWorkflow,
  aiFullAssessment,
  aiOSINTInvestigation,
  aiPurpleTeamExercise,

  // Memory
  getAIMemory,
  addToMemory,

  // Chat & Streaming
  chatWithMaximus,
  connectMaximusStream,

  // Offensive Arsenal AI Integration
  aiNetworkRecon,
  aiVulnIntel,
  aiWebAttack,
  aiC2Orchestration,
  aiBASSimulation,

  // Intelligence
  synthesizeIntelligence,
  getAISuggestions,

  // FASE 8: Enhanced Cognition
  analyzeNarrative,
  predictThreats,
  huntProactively,
  investigateIncident,
  correlateCampaigns,

  // FASE 9: Immune Enhancement
  suppressFalsePositives,
  getToleranceProfile,
  consolidateMemory,
  queryLongTermMemory,
  diversifyAntibodies,
  runAffinityMaturation,

  // FASE 10: Distributed Organism
  getEdgeStatus,
  coordinateMultiEdgeScan,
  getGlobalMetrics,
  getTopology,

  // Health
  getMaximusHealth,
  getAIStats,
};

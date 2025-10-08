/**
 * Consciousness System - API Client
 * ===================================
 *
 * Cliente para o sistema de consciência artificial.
 * Monitora estado em tempo real: ESGT, Arousal, TIG Fabric.
 *
 * Features:
 * - Real-time consciousness state
 * - ESGT event streaming
 * - Arousal level monitoring
 * - Manual consciousness control
 * - WebSocket real-time updates
 *
 * Port: 8001 (maximus_core_service)
 * REGRA: NO MOCK, NO PLACEHOLDER - Dados REAIS via API
 */

const CONSCIOUSNESS_BASE_URL = 'http://localhost:8001/api/consciousness';

/**
 * ============================================================================
 * CONSCIOUSNESS STATE
 * ============================================================================
 */

/**
 * Obtém estado completo do sistema de consciência
 */
export const getConsciousnessState = async () => {
  try {
    const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/state`);

    if (!response.ok) {
      throw new Error(`Failed to get consciousness state: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Error getting consciousness state:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * ESGT EVENTS
 * ============================================================================
 */

/**
 * Obtém eventos ESGT recentes
 * @param {number} limit - Número máximo de eventos (1-100)
 */
export const getESGTEvents = async (limit = 20) => {
  try {
    const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/esgt/events?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Failed to get ESGT events: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Error getting ESGT events:', error);
    return [];
  }
};

/**
 * Trigger manual de ignição ESGT
 * @param {Object} salience - {novelty, relevance, urgency, context}
 */
export const triggerESGT = async (salience) => {
  try {
    const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/esgt/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(salience),
    });

    if (!response.ok) {
      throw new Error(`Failed to trigger ESGT: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Error triggering ESGT:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * AROUSAL STATE
 * ============================================================================
 */

/**
 * Obtém estado atual de arousal (excitabilidade global)
 */
export const getArousalState = async () => {
  try {
    const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/arousal`);

    if (!response.ok) {
      throw new Error(`Failed to get arousal state: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Error getting arousal state:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Ajusta nível de arousal
 * @param {number} delta - Mudança no arousal (-0.5 a +0.5)
 * @param {number} duration - Duração em segundos (0.1 a 60)
 * @param {string} source - Identificador da fonte
 */
export const adjustArousal = async (delta, duration = 5.0, source = 'manual') => {
  try {
    const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/arousal/adjust`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta, duration_seconds: duration, source }),
    });

    if (!response.ok) {
      throw new Error(`Failed to adjust arousal: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Error adjusting arousal:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * SYSTEM METRICS
 * ============================================================================
 */

/**
 * Obtém métricas do sistema (TIG + ESGT)
 */
export const getConsciousnessMetrics = async () => {
  try {
    const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/metrics`);

    if (!response.ok) {
      throw new Error(`Failed to get metrics: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Error getting consciousness metrics:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * WEBSOCKET REAL-TIME STREAMING
 * ============================================================================
 */

/**
 * Conecta ao WebSocket de consciência para updates em tempo real
 * @param {Function} onMessage - Callback para mensagens (message) => {}
 * @param {Function} onError - Callback para erros (error) => {}
 * @returns {WebSocket} Conexão WebSocket
 */
export const connectConsciousnessWebSocket = (onMessage, onError = null) => {
  const wsUrl = 'ws://localhost:8001/api/consciousness/ws';

  try {
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('🧠 Consciousness WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        onMessage(message);
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      if (onError) onError(error);
    };

    ws.onclose = () => {
      console.log('🔌 Consciousness WebSocket disconnected');
    };

    // Heartbeat/ping para manter conexão viva
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      } else {
        clearInterval(pingInterval);
      }
    }, 25000); // 25s (antes do timeout de 30s do servidor)

    return ws;
  } catch (error) {
    console.error('❌ Error creating WebSocket:', error);
    if (onError) onError(error);
    return null;
  }
};

/**
 * ============================================================================
 * HELPER FUNCTIONS
 * ============================================================================
 */

/**
 * Formata classificação de arousal para display
 * @param {string} level - SLEEPY, CALM, RELAXED, ALERT, EXCITED
 */
export const formatArousalLevel = (level) => {
  const levels = {
    'SLEEPY': { emoji: '😴', color: '#64748B', label: 'Sleepy' },
    'CALM': { emoji: '😌', color: '#06B6D4', label: 'Calm' },
    'RELAXED': { emoji: '😊', color: '#10B981', label: 'Relaxed' },
    'ALERT': { emoji: '😃', color: '#F59E0B', label: 'Alert' },
    'EXCITED': { emoji: '🤩', color: '#EF4444', label: 'Excited' }
  };

  return levels[level] || { emoji: '❓', color: '#6B7280', label: 'Unknown' };
};

/**
 * Formata tempo relativo para eventos
 * @param {string} timestamp - ISO timestamp
 */
export const formatEventTime = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);

  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  return date.toLocaleTimeString();
};

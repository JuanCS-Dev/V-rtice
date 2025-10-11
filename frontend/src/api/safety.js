import logger from '@/utils/logger';
/**
 * Safety Protocol - API Client
 * ===============================
 *
 * Cliente para o protocolo de segurança do sistema de consciência.
 * Monitora violações, thresholds e kill switch em tempo real.
 *
 * Features:
 * - Real-time safety status
 * - Safety violations streaming
 * - Kill switch control (HITL only)
 * - WebSocket real-time updates
 *
 * Port: 8001 (maximus_core_service)
 * REGRA: NO MOCK, NO PLACEHOLDER - Dados REAIS via API
 *
 * Authors: Juan & Claude Code
 * Version: 1.0.0 - FASE VII Week 9-10
 */

const SAFETY_BASE_URL = 'http://localhost:8001/api/consciousness/safety';
const WS_BASE_URL = 'ws://localhost:8001/api/consciousness';

/**
 * ============================================================================
 * SAFETY STATUS
 * ============================================================================
 */

/**
 * Obtém status completo do protocolo de segurança
 */
export const getSafetyStatus = async () => {
  try {
    const response = await fetch(`${SAFETY_BASE_URL}/status`);

    if (!response.ok) {
      throw new Error(`Failed to get safety status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    logger.error('❌ Error getting safety status:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * SAFETY VIOLATIONS
 * ============================================================================
 */

/**
 * Obtém violações de segurança recentes
 * @param {number} limit - Número máximo de violações (1-1000)
 */
export const getSafetyViolations = async (limit = 100) => {
  try {
    const response = await fetch(`${SAFETY_BASE_URL}/violations?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Failed to get safety violations: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    logger.error('❌ Error getting safety violations:', error);
    return [];
  }
};

/**
 * ============================================================================
 * EMERGENCY SHUTDOWN (HITL ONLY)
 * ============================================================================
 */

/**
 * Executa shutdown de emergência via kill switch
 * @param {string} reason - Motivo do shutdown (mínimo 10 caracteres)
 * @param {boolean} allowOverride - Permitir override HITL (default: true)
 */
export const executeEmergencyShutdown = async (reason, allowOverride = true) => {
  try {
    const response = await fetch(`${SAFETY_BASE_URL}/emergency-shutdown`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reason: reason,
        allow_override: allowOverride
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Failed to execute shutdown: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    logger.error('❌ Error executing emergency shutdown:', error);
    return { success: false, error: error.message };
  }
};

/**
 * ============================================================================
 * WEBSOCKET CONNECTION
 * ============================================================================
 */

/**
 * Conecta ao WebSocket de consciência para receber atualizações de segurança
 * @param {function} onMessage - Callback para mensagens recebidas
 * @param {function} onError - Callback para erros
 */
export const connectSafetyWebSocket = (onMessage, onError) => {
  try {
    const ws = new WebSocket(`${WS_BASE_URL}/ws`);

    ws.onopen = () => {
      logger.debug('🔌 Safety WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        logger.error('❌ Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      logger.error('❌ WebSocket error:', error);
      if (onError) onError(error);
    };

    ws.onclose = () => {
      logger.debug('🔌 Safety WebSocket disconnected');
      // Auto-reconnect after 5 seconds
      setTimeout(() => {
        logger.debug('🔄 Reconnecting Safety WebSocket...');
        connectSafetyWebSocket(onMessage, onError);
      }, 5000);
    };

    return ws;
  } catch (error) {
    logger.error('❌ Error creating WebSocket connection:', error);
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
 * Formata severity level com cores
 * @param {string} severity - Severity level (normal, warning, critical, emergency)
 */
export const formatSeverity = (severity) => {
  const severityMap = {
    normal: { label: 'Normal', color: '#4ade80', className: 'text-success', borderClass: 'border-success' },
    warning: { label: 'Warning', color: '#fbbf24', className: 'text-warning', borderClass: 'border-warning' },
    critical: { label: 'Critical', color: '#f97316', className: 'text-high', borderClass: 'border-high' },
    emergency: { label: 'EMERGENCY', color: '#ef4444', className: 'text-critical', borderClass: 'border-critical' }
  };

  return severityMap[severity.toLowerCase()] || { label: severity, color: '#6b7280', className: 'text-muted', borderClass: 'border-low' };
};

/**
 * Formata violation type
 * @param {string} violationType - Type of violation
 */
export const formatViolationType = (violationType) => {
  const typeMap = {
    esgt_frequency_exceeded: 'ESGT Frequency Exceeded',
    arousal_sustained_high: 'Arousal Sustained High',
    unexpected_goals: 'Unexpected Goals',
    self_modification: 'SELF-MODIFICATION ATTEMPT',
    memory_usage_exceeded: 'Memory Usage Exceeded',
    cpu_usage_exceeded: 'CPU Usage Exceeded',
    ethical_violation: 'Ethical Violation'
  };

  return typeMap[violationType] || violationType.replace(/_/g, ' ').toUpperCase();
};

/**
 * Formata timestamp para exibição
 * @param {string} timestamp - ISO timestamp
 */
export const formatTimestamp = (timestamp) => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (error) {
    return timestamp;
  }
};

/**
 * Formata timestamp relativo (ex: "5 min ago")
 * @param {string} timestamp - ISO timestamp
 */
export const formatRelativeTime = (timestamp) => {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffMin < 60) return `${diffMin}min ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    return `${diffDay}d ago`;
  } catch (error) {
    return 'unknown';
  }
};

/**
 * Calcula porcentagem de threshold
 * @param {number} value - Valor observado
 * @param {number} threshold - Threshold violado
 */
export const calculateThresholdPercentage = (value, threshold) => {
  if (threshold === 0) return 100;
  return Math.min(Math.round((value / threshold) * 100), 999);
};

/**
 * Verifica se sistema está em estado crítico
 * @param {object} status - Safety status object
 */
export const isCriticalState = (status) => {
  if (!status || !status.violations_by_severity) return false;

  const critical = status.violations_by_severity.critical || 0;
  const emergency = status.violations_by_severity.emergency || 0;

  return critical > 0 || emergency > 0;
};

/**
 * Verifica se kill switch está ativo
 * @param {object} status - Safety status object
 */
export const isKillSwitchActive = (status) => {
  return status && status.kill_switch_active === true;
};

/**
 * Obtém última violação formatada
 * @param {array} violations - Array de violations
 */
export const getLastViolation = (violations) => {
  if (!violations || violations.length === 0) return null;

  const latest = violations[violations.length - 1];
  return {
    ...latest,
    formattedType: formatViolationType(latest.violation_type),
    formattedSeverity: formatSeverity(latest.severity),
    formattedTimestamp: formatTimestamp(latest.timestamp),
    relativeTime: formatRelativeTime(latest.timestamp)
  };
};

/**
 * Calcula uptime formatado
 * @param {number} uptimeSeconds - Uptime em segundos
 */
export const formatUptime = (uptimeSeconds) => {
  const days = Math.floor(uptimeSeconds / 86400);
  const hours = Math.floor((uptimeSeconds % 86400) / 3600);
  const minutes = Math.floor((uptimeSeconds % 3600) / 60);
  const seconds = Math.floor(uptimeSeconds % 60);

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);

  return parts.join(' ');
};

/**
 * ============================================================================
 * VALIDATION FUNCTIONS
 * ============================================================================
 */

/**
 * Valida razão de shutdown
 * @param {string} reason - Razão do shutdown
 */
export const validateShutdownReason = (reason) => {
  if (!reason || typeof reason !== 'string') {
    return { valid: false, error: 'Reason is required' };
  }

  if (reason.length < 10) {
    return { valid: false, error: 'Reason must be at least 10 characters' };
  }

  if (reason.length > 500) {
    return { valid: false, error: 'Reason must be less than 500 characters' };
  }

  return { valid: true };
};

/**
 * ============================================================================
 * EXPORTS
 * ============================================================================
 */

export default {
  // Main API functions
  getSafetyStatus,
  getSafetyViolations,
  executeEmergencyShutdown,
  connectSafetyWebSocket,

  // Helper functions
  formatSeverity,
  formatViolationType,
  formatTimestamp,
  formatRelativeTime,
  calculateThresholdPercentage,
  isCriticalState,
  isKillSwitchActive,
  getLastViolation,
  formatUptime,

  // Validation
  validateShutdownReason
};

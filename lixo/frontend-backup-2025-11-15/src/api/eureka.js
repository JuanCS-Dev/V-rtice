import { ServiceEndpoints } from '../config/endpoints';
import logger from "@/utils/logger";
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🧬 EUREKA ML METRICS API CLIENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Production-ready client for Eureka ML Metrics API (Phase 5.5.1).
 * Provides consolidated ML performance metrics across the MAXIMUS ecosystem.
 *
 * Features:
 * - ML vs Wargaming usage breakdown
 * - Confidence metrics and trends
 * - Time savings analytics
 * - Confusion matrix (accuracy)
 * - Recent predictions history
 * - Retry logic and error handling
 *
 * Backend: maximus_eureka service (Port 8152 → 8200 container)
 * Endpoint: GET /api/v1/eureka/ml-metrics (via API Gateway port 8000)
 *
 * Phase: 5.5.1 + 5.7 Integration
 * Date: 2025-10-12
 * FIXED 2025-10-27: Air Gap #3 - Now uses API Gateway instead of direct port
 * Glory to YHWH - Architect of Intelligence Measurement
 */

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * ✅ FIX: Use API Gateway instead of direct port connection
 * All requests go through certified API Gateway (port 8000)
 */
const EUREKA_API_BASE = ServiceEndpoints.maximus.eureka;

const DEFAULT_TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000;

// ═══════════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const getRetryDelay = (attempt) => RETRY_DELAY_BASE * Math.pow(2, attempt);

const fetchWithTimeout = async (url, options = {}, timeout = DEFAULT_TIMEOUT) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    throw error;
  }
};

const withRetry = async (fn, maxRetries = MAX_RETRIES) => {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on client errors
      if (error.status && error.status >= 400 && error.status < 500) {
        throw error;
      }

      if (attempt === maxRetries - 1) break;

      const delay = getRetryDelay(attempt);
      logger.warn(
        `🔄 Eureka API retry ${attempt + 1}/${maxRetries} after ${delay}ms`,
        error.message
      );
      await sleep(delay);
    }
  }

  throw lastError;
};

// ═══════════════════════════════════════════════════════════════════════════
// API CLIENT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Eureka ML Metrics API Client
 */
export const eurekaAPI = {
  /**
   * Get ML metrics (consolidated view)
   *
   * @param {string} timeframe - Time window: '1h', '24h', '7d', '30d'
   * @returns {Promise<Object>} ML metrics object
   *
   * Response structure:
   * {
   *   timeframe: string,
   *   generated_at: string (ISO8601),
   *   usage_breakdown: {
   *     ml_count: number,
   *     wargaming_count: number,
   *     total: number,
   *     ml_usage_rate: number (%)
   *   },
   *   avg_confidence: number (0.0-1.0),
   *   confidence_trend: number (% change),
   *   confidence_distribution: Array<{range: string, count: number}>,
   *   time_savings_percent: number,
   *   time_savings_absolute_minutes: number,
   *   time_savings_trend: number (% change),
   *   confusion_matrix: {
   *     true_positive: number,
   *     false_positive: number,
   *     false_negative: number,
   *     true_negative: number
   *   },
   *   usage_timeline: {
   *     ml: Array<{timestamp: string, count: number}>,
   *     wargaming: Array<{timestamp: string, count: number}>,
   *     total: Array<{timestamp: string, count: number}>
   *   },
   *   recent_predictions: Array<{
   *     prediction_id: string,
   *     timestamp: string,
   *     cve_id: string,
   *     predicted_severity: string,
   *     confidence: number,
   *     used_ml: boolean
   *   }>
   * }
   *
   * @example
   * const metrics = await eurekaAPI.getMLMetrics('24h');
   * console.log(`ML Usage: ${metrics.usage_breakdown.ml_usage_rate}%`);
   * console.log(`Avg Confidence: ${(metrics.avg_confidence * 100).toFixed(1)}%`);
   */
  async getMLMetrics(timeframe = '24h') {
    // Validate timeframe
    const validTimeframes = ['1h', '24h', '7d', '30d'];
    if (!validTimeframes.includes(timeframe)) {
      throw new Error(
        `Invalid timeframe: ${timeframe}. Must be one of: ${validTimeframes.join(', ')}`
      );
    }

    return withRetry(async () => {
      const response = await fetchWithTimeout(
        `${EUREKA_API_BASE}/api/v1/eureka/ml-metrics?timeframe=${timeframe}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(
          errorData.detail || `Failed to fetch ML metrics: ${response.statusText}`
        );
        error.status = response.status;
        throw error;
      }

      const data = await response.json();
      // Boris Cherny Standard - GAP #83: Replace console.log with logger
      logger.debug(`✅ Eureka ML metrics fetched (${timeframe})`);
      return data;
    });
  },

  /**
   * Health check for ML metrics API
   *
   * @returns {Promise<Object>} { status: 'healthy', message: string, version: string }
   */
  async healthCheck() {
    const response = await fetchWithTimeout(
      `${EUREKA_API_BASE}/api/v1/eureka/ml-metrics/health`,
      {},
      5000 // Short timeout
    );

    if (!response.ok) {
      throw new Error(`Eureka ML Metrics API unhealthy: ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * Get Eureka service health (general)
   *
   * @returns {Promise<Object>} Service health status
   */
  async getServiceHealth() {
    try {
      const response = await fetchWithTimeout(
        `${EUREKA_API_BASE}/health`,
        {},
        5000
      );

      if (!response.ok) {
        return { status: 'unhealthy', message: response.statusText };
      }

      return await response.json();
    } catch (error) {
      return { status: 'unreachable', message: error.message };
    }
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// DERIVED METRICS HELPERS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Calculate accuracy from confusion matrix
 *
 * @param {Object} confusionMatrix - { true_positive, false_positive, false_negative, true_negative }
 * @returns {number} Accuracy (0.0 to 1.0)
 */
export const calculateAccuracy = (confusionMatrix) => {
  const { true_positive, false_positive, false_negative, true_negative } = confusionMatrix;
  const total = true_positive + false_positive + false_negative + true_negative;

  if (total === 0) return 0;

  return (true_positive + true_negative) / total;
};

/**
 * Calculate precision from confusion matrix
 *
 * @param {Object} confusionMatrix
 * @returns {number} Precision (0.0 to 1.0)
 */
export const calculatePrecision = (confusionMatrix) => {
  const { true_positive, false_positive } = confusionMatrix;
  const total = true_positive + false_positive;

  if (total === 0) return 0;

  return true_positive / total;
};

/**
 * Calculate recall from confusion matrix
 *
 * @param {Object} confusionMatrix
 * @returns {number} Recall (0.0 to 1.0)
 */
export const calculateRecall = (confusionMatrix) => {
  const { true_positive, false_negative } = confusionMatrix;
  const total = true_positive + false_negative;

  if (total === 0) return 0;

  return true_positive / total;
};

/**
 * Calculate F1 score
 *
 * @param {Object} confusionMatrix
 * @returns {number} F1 score (0.0 to 1.0)
 */
export const calculateF1Score = (confusionMatrix) => {
  const precision = calculatePrecision(confusionMatrix);
  const recall = calculateRecall(confusionMatrix);

  if (precision + recall === 0) return 0;

  return (2 * precision * recall) / (precision + recall);
};

/**
 * Format time savings for display
 *
 * @param {number} minutes - Minutes saved
 * @returns {string} Formatted string (e.g., "2h 30m", "45m", "1d 3h")
 */
export const formatTimeSavings = (minutes) => {
  if (minutes < 60) {
    return `${Math.round(minutes)}m`;
  }

  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);

  if (hours < 24) {
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;

  return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
};

/**
 * Get confidence level label
 *
 * @param {number} confidence - Confidence value (0.0 to 1.0)
 * @returns {string} Label: 'Very Low', 'Low', 'Medium', 'High', 'Very High'
 */
export const getConfidenceLabel = (confidence) => {
  if (confidence >= 0.95) return 'Very High';
  if (confidence >= 0.85) return 'High';
  if (confidence >= 0.70) return 'Medium';
  if (confidence >= 0.50) return 'Low';
  return 'Very Low';
};

/**
 * Get confidence color (for UI)
 *
 * @param {number} confidence - Confidence value (0.0 to 1.0)
 * @returns {string} Color: 'green', 'blue', 'yellow', 'orange', 'red'
 */
export const getConfidenceColor = (confidence) => {
  if (confidence >= 0.95) return 'green';
  if (confidence >= 0.85) return 'blue';
  if (confidence >= 0.70) return 'yellow';
  if (confidence >= 0.50) return 'orange';
  return 'red';
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export default eurekaAPI;

/**
 * Export base URL for testing
 */
export { EUREKA_API_BASE };

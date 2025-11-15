/**
 * MVP Service
 * ===========
 *
 * Service layer for MVP (MAXIMUS Vision Protocol).
 * Handles communication with MVP backend service.
 *
 * Governed by: Constituição Vértice v3.0
 *
 * Features:
 * - Narrative generation (Claude 3.5 Sonnet)
 * - System observability and consciousness monitoring
 * - Anomaly detection
 * - Metrics analysis and insights
 *
 * Port: 8153
 * Created: 2025-10-31
 */

import { BaseService } from '../base/BaseService';
import { API_ENDPOINTS } from '../../config/api';
import logger from '../../utils/logger';

export class MVPService extends BaseService {
  constructor() {
    super(API_ENDPOINTS.mvp);
    this.serviceName = 'MVP';
  }

  // ────────────────────────────────────────────────────────────────────────────
  // HEALTH & STATUS
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Get MVP service status
   * @returns {Promise<Object>} Service status
   */
  async getStatus() {
    try {
      const response = await this.get('/status');
      logger.debug('[MVP] Status:', response);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get status:', error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // NARRATIVES
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Generate a narrative from system metrics
   * @param {Object} params - Narrative params (time_range, tone, focus_areas)
   * @returns {Promise<Object>} Generated narrative
   */
  async generateNarrative(params = {}) {
    try {
      const response = await this.post('/narratives', params);
      logger.info('[MVP] Narrative generated:', response.narrative_id);
      return response;
    } catch (error) {
      logger.error('[MVP] Narrative generation failed:', error);
      throw error;
    }
  }

  /**
   * Get narrative by ID
   * @param {string} narrativeId - Narrative UUID
   * @returns {Promise<Object>} Narrative details
   */
  async getNarrative(narrativeId) {
    try {
      const response = await this.get(`/narratives/${narrativeId}`);
      logger.debug('[MVP] Narrative retrieved:', narrativeId);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get narrative:', error);
      throw error;
    }
  }

  /**
   * List narratives with pagination
   * @param {Object} params - Query params (limit, offset, tone, min_nqs)
   * @returns {Promise<Array>} List of narratives
   */
  async listNarratives(params = {}) {
    try {
      const queryParams = new URLSearchParams(params).toString();
      const endpoint = queryParams ? `/narratives?${queryParams}` : '/narratives';
      const response = await this.get(endpoint);
      logger.debug(`[MVP] Retrieved ${response.length} narratives`);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to list narratives:', error);
      throw error;
    }
  }

  /**
   * Delete narrative by ID
   * @param {string} narrativeId - Narrative UUID
   * @returns {Promise<Object>} Deletion confirmation
   */
  async deleteNarrative(narrativeId) {
    try {
      const response = await this.delete(`/narratives/${narrativeId}`);
      logger.info('[MVP] Narrative deleted:', narrativeId);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to delete narrative:', error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // METRICS & OBSERVABILITY
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Query system metrics
   * @param {Object} query - Query params (metric_name, time_range, aggregation)
   * @returns {Promise<Object>} Metrics data
   */
  async queryMetrics(query = {}) {
    try {
      const response = await this.post('/metrics', query);
      logger.debug('[MVP] Metrics queried:', response);
      return response;
    } catch (error) {
      logger.error('[MVP] Metrics query failed:', error);
      throw error;
    }
  }

  /**
   * Get aggregated system metrics
   * @param {number} timeRangeMinutes - Time range in minutes (default: 60)
   * @returns {Promise<Object>} Aggregated metrics
   */
  async getAggregatedMetrics(timeRangeMinutes = 60) {
    try {
      const response = await this.post('/metrics', {
        time_range_minutes: timeRangeMinutes,
        aggregation: 'avg',
      });
      logger.debug('[MVP] Aggregated metrics:', response);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get aggregated metrics:', error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // ANOMALIES
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Detect anomalies in metrics
   * @param {Object} params - Detection params (time_range, sensitivity)
   * @returns {Promise<Array>} Detected anomalies
   */
  async detectAnomalies(params = {}) {
    try {
      const queryParams = new URLSearchParams(params).toString();
      const endpoint = queryParams ? `/anomalies?${queryParams}` : '/anomalies';
      const response = await this.get(endpoint);
      logger.info(`[MVP] Detected ${response.length} anomalies`);
      return response;
    } catch (error) {
      logger.error('[MVP] Anomaly detection failed:', error);
      throw error;
    }
  }

  /**
   * Get anomalies by severity
   * @param {string} severity - Severity level (low, medium, high, critical)
   * @param {number} limit - Max results (default: 50)
   * @returns {Promise<Array>} Filtered anomalies
   */
  async getAnomaliesBySeverity(severity, limit = 50) {
    try {
      const response = await this.get(`/anomalies?severity=${severity}&limit=${limit}`);
      logger.debug(`[MVP] Retrieved ${response.length} ${severity} anomalies`);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get anomalies by severity:', error);
      throw error;
    }
  }

  /**
   * Get anomaly timeline (for calendar heatmap)
   * @param {number} days - Number of days to fetch (default: 30)
   * @returns {Promise<Array>} Daily anomaly counts
   */
  async getAnomalyTimeline(days = 30) {
    try {
      const response = await this.get(`/anomalies/timeline?days=${days}`);
      logger.debug(`[MVP] Anomaly timeline for ${days} days`);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get anomaly timeline:', error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // NARRATIVE QUALITY
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Get Narrative Quality Score (NQS) trend
   * @param {number} limit - Number of data points (default: 30)
   * @returns {Promise<Array>} NQS trend data
   */
  async getNQSTrend(limit = 30) {
    try {
      const response = await this.get(`/narratives/nqs-trend?limit=${limit}`);
      logger.debug('[MVP] NQS trend retrieved');
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get NQS trend:', error);
      throw error;
    }
  }

  /**
   * Get average NQS by tone
   * @returns {Promise<Object>} Average NQS per tone
   */
  async getNQSByTone() {
    try {
      const response = await this.get('/narratives/nqs-by-tone');
      logger.debug('[MVP] NQS by tone:', response);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get NQS by tone:', error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // SYSTEM PULSE (Real-time visualization)
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Get current system pulse (live metrics snapshot)
   * @returns {Promise<Object>} Current pulse data
   */
  async getSystemPulse() {
    try {
      const response = await this.post('/metrics', {
        time_range_minutes: 1, // Last minute
        aggregation: 'current',
      });
      logger.debug('[MVP] System pulse:', response);
      return response;
    } catch (error) {
      logger.error('[MVP] Failed to get system pulse:', error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // VALIDATION & TRANSFORMATION
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Validates request data
   * @param {Object} data - Request data
   * @throws {Error} If validation fails
   * @protected
   */
  validateRequest(data) {
    if (!data || typeof data !== 'object') {
      throw new Error('[MVP] Invalid request data: must be an object');
    }

    // Validate tone
    if (data.tone) {
      const validTones = ['reflective', 'urgent', 'informative'];
      if (!validTones.includes(data.tone)) {
        throw new Error(`[MVP] Invalid tone. Must be one of: ${validTones.join(', ')}`);
      }
    }

    // Validate time_range_minutes
    if (data.time_range_minutes && (data.time_range_minutes < 1 || data.time_range_minutes > 10080)) {
      throw new Error('[MVP] time_range_minutes must be between 1 and 10080 (1 week)');
    }

    return true;
  }

  /**
   * Transforms API response
   * @param {Object} response - Raw response
   * @returns {Object} Transformed response
   * @protected
   */
  transformResponse(response) {
    // Ensure timestamp exists
    if (response && !response.timestamp) {
      response.timestamp = new Date().toISOString();
    }

    // Transform NQS to 0-100 scale if needed
    if (response && response.nqs && response.nqs > 1) {
      // Already 0-100
    } else if (response && response.nqs) {
      response.nqs = Math.round(response.nqs * 100);
    }

    return response;
  }
}

// Singleton instance
export const mvpService = new MVPService();

export default mvpService;

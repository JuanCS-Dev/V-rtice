/**
 * PENELOPE Service
 * ================
 *
 * Service layer for PENELOPE (Christian Autonomous Healing System).
 * Handles communication with PENELOPE backend service.
 *
 * Governed by: Constituição Vértice v3.0
 *
 * Features:
 * - 9 Frutos do Espírito (Gálatas 5:22-23)
 * - Autonomous healing and patch generation
 * - Wisdom base precedents
 * - Sabbath mode (Sunday read-only)
 * - Real-time healing events via WebSocket
 *
 * Port: 8154
 * Created: 2025-10-31
 */

import { BaseService } from "../base/BaseService";
import { API_ENDPOINTS } from "../../config/api";
import logger from "../../utils/logger";

export class PenelopeService extends BaseService {
  constructor() {
    super(API_ENDPOINTS.penelope);
    this.serviceName = "PENELOPE";
  }

  // ────────────────────────────────────────────────────────────────────────────
  // HEALTH & STATUS
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Check PENELOPE service health (includes Sabbath mode status)
   * @returns {Promise<Object>} Health status
   */
  async getHealth() {
    try {
      const response = await this.get("/health");
      logger.info("[PENELOPE] Health check:", response);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Health check failed:", error);
      throw error;
    }
  }

  /**
   * Get status of 9 Frutos do Espírito
   * @returns {Promise<Object>} Fruits status with scores
   */
  async getFruitsStatus() {
    try {
      const response = await this.get("/fruits/status");
      logger.debug("[PENELOPE] Fruits status:", response);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Failed to get fruits status:", error);
      throw error;
    }
  }

  /**
   * Get virtue metrics (detailed metrics for each fruit)
   * @returns {Promise<Object>} Virtue metrics
   */
  async getVirtueMetrics() {
    try {
      const response = await this.get("/virtues/metrics");
      logger.debug("[PENELOPE] Virtue metrics:", response);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Failed to get virtue metrics:", error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // HEALING OPERATIONS
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Get healing history
   * @param {number} limit - Number of events to fetch (default: 50)
   * @returns {Promise<Array>} Healing events
   */
  async getHealingHistory(limit = 50) {
    try {
      const response = await this.get(`/healing/history?limit=${limit}`);
      logger.debug(`[PENELOPE] Fetched ${response.length} healing events`);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Failed to get healing history:", error);
      throw error;
    }
  }

  /**
   * Diagnose an anomaly
   * @param {Object} anomalyData - Anomaly data to diagnose
   * @returns {Promise<Object>} Diagnosis result
   */
  async diagnoseAnomaly(anomalyData) {
    try {
      this.validateRequest(anomalyData);
      const response = await this.post("/diagnose", anomalyData);
      logger.info("[PENELOPE] Diagnosis completed:", response);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Diagnosis failed:", error);
      throw error;
    }
  }

  /**
   * Get patch by ID
   * @param {string} patchId - Patch UUID
   * @returns {Promise<Object>} Patch details
   */
  async getPatch(patchId) {
    try {
      const response = await this.get(`/patches/${patchId}`);
      logger.debug("[PENELOPE] Patch retrieved:", patchId);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Failed to get patch:", error);
      throw error;
    }
  }

  /**
   * List all patches
   * @param {Object} filters - Optional filters (status, limit, offset)
   * @returns {Promise<Array>} List of patches
   */
  async listPatches(filters = {}) {
    try {
      const queryParams = new URLSearchParams(filters).toString();
      const endpoint = queryParams ? `/patches?${queryParams}` : "/patches";
      const response = await this.get(endpoint);
      logger.debug(`[PENELOPE] Retrieved ${response.length} patches`);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Failed to list patches:", error);
      throw error;
    }
  }

  /**
   * Validate patch in Digital Twin
   * @param {string} patchId - Patch UUID
   * @returns {Promise<Object>} Validation result
   */
  async validatePatch(patchId) {
    try {
      const response = await this.post(`/patches/${patchId}/validate`);
      logger.info("[PENELOPE] Patch validation:", response);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Patch validation failed:", error);
      throw error;
    }
  }

  /**
   * Deploy patch to production
   * @param {string} patchId - Patch UUID
   * @returns {Promise<Object>} Deployment result
   */
  async deployPatch(patchId) {
    try {
      const response = await this.post(`/patches/${patchId}/deploy`);
      logger.info("[PENELOPE] Patch deployed:", response);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Patch deployment failed:", error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // WISDOM BASE
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Query wisdom base for similar cases
   * @param {Object} query - Query parameters (anomaly_type, similarity_threshold)
   * @returns {Promise<Array>} Similar precedents
   */
  async queryWisdomBase(query = {}) {
    try {
      const queryParams = new URLSearchParams(query).toString();
      const endpoint = queryParams ? `/wisdom?${queryParams}` : "/wisdom";
      const response = await this.get(endpoint);
      logger.debug(
        `[PENELOPE] Wisdom base query returned ${response.length} precedents`,
      );
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Wisdom base query failed:", error);
      throw error;
    }
  }

  /**
   * Get wisdom base statistics
   * @returns {Promise<Object>} Statistics (total cases, success rate, etc.)
   */
  async getWisdomBaseStats() {
    try {
      const response = await this.get("/wisdom/stats");
      logger.debug("[PENELOPE] Wisdom base stats:", response);
      return response;
    } catch (error) {
      logger.error("[PENELOPE] Failed to get wisdom base stats:", error);
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
    if (!data || typeof data !== "object") {
      throw new Error("[PENELOPE] Invalid request data: must be an object");
    }

    // Specific validations for diagnose endpoint
    if (
      data.anomaly_description &&
      typeof data.anomaly_description !== "string"
    ) {
      throw new Error("[PENELOPE] anomaly_description must be a string");
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
    // Add sabbath mode indicator if missing
    if (response && !("sabbath_mode" in response)) {
      const now = new Date();
      response.sabbath_mode = now.getDay() === 0; // Sunday = 0
    }

    return response;
  }
}

// Singleton instance
export const penelopeService = new PenelopeService();

export default penelopeService;

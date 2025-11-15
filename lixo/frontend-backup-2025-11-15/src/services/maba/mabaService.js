/**
 * MABA Service
 * =============
 *
 * Service layer for MABA (MAXIMUS Browser Agent).
 * Handles communication with MABA backend service.
 *
 * Governed by: Constituição Vértice v3.0
 *
 * Features:
 * - Autonomous browser automation (Playwright)
 * - Cognitive map (Neo4j graph of learned pages)
 * - Session management
 * - Page navigation and data extraction
 *
 * Port: 8155 (adjusted from 8152 to avoid conflict with Oráculo)
 * Created: 2025-10-31
 */

import { BaseService } from "../base/BaseService";
import { API_ENDPOINTS } from "../../config/api";
import logger from "../../utils/logger";

export class MABAService extends BaseService {
  constructor() {
    super(API_ENDPOINTS.maba);
    this.serviceName = "MABA";
  }

  // ────────────────────────────────────────────────────────────────────────────
  // HEALTH & STATS
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Get MABA service statistics
   * @returns {Promise<Object>} Stats (cognitive_map, browser, uptime)
   */
  async getStats() {
    try {
      const response = await this.get("/stats");
      logger.debug("[MABA] Stats:", response);
      return response;
    } catch (error) {
      logger.error("[MABA] Failed to get stats:", error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // BROWSER SESSION MANAGEMENT
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Create a new browser session
   * @param {Object} options - Session options (viewport, user_agent, browser_type)
   * @returns {Promise<Object>} Session details with session_id
   */
  async createSession(options = {}) {
    try {
      const response = await this.post("/sessions", options);
      logger.info("[MABA] Session created:", response.session_id);
      return response;
    } catch (error) {
      logger.error("[MABA] Failed to create session:", error);
      throw error;
    }
  }

  /**
   * Get session details
   * @param {string} sessionId - Session UUID
   * @returns {Promise<Object>} Session details
   */
  async getSession(sessionId) {
    try {
      const response = await this.get(`/sessions/${sessionId}`);
      logger.debug("[MABA] Session retrieved:", sessionId);
      return response;
    } catch (error) {
      logger.error("[MABA] Failed to get session:", error);
      throw error;
    }
  }

  /**
   * List all active sessions
   * @returns {Promise<Array>} List of sessions
   */
  async listSessions() {
    try {
      const response = await this.get("/sessions");
      logger.debug(`[MABA] Retrieved ${response.length} sessions`);
      return response;
    } catch (error) {
      logger.error("[MABA] Failed to list sessions:", error);
      throw error;
    }
  }

  /**
   * Close browser session
   * @param {string} sessionId - Session UUID
   * @returns {Promise<Object>} Closure confirmation
   */
  async closeSession(sessionId) {
    try {
      const response = await this.delete(`/sessions/${sessionId}`);
      logger.info("[MABA] Session closed:", sessionId);
      return response;
    } catch (error) {
      logger.error("[MABA] Failed to close session:", error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // BROWSER ACTIONS
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Navigate to URL
   * @param {string} sessionId - Session UUID
   * @param {string} url - Target URL
   * @param {Object} options - Navigation options (wait_until, timeout)
   * @returns {Promise<Object>} Navigation result
   */
  async navigate(sessionId, url, options = {}) {
    try {
      const response = await this.post("/navigate", {
        session_id: sessionId,
        url,
        ...options,
      });
      logger.info(`[MABA] Navigated to ${url}`);
      return response;
    } catch (error) {
      logger.error("[MABA] Navigation failed:", error);
      throw error;
    }
  }

  /**
   * Click element on page
   * @param {string} sessionId - Session UUID
   * @param {string} selector - CSS selector
   * @returns {Promise<Object>} Click result
   */
  async clickElement(sessionId, selector) {
    try {
      const response = await this.post("/click", {
        session_id: sessionId,
        selector,
      });
      logger.debug(`[MABA] Clicked element: ${selector}`);
      return response;
    } catch (error) {
      logger.error("[MABA] Click failed:", error);
      throw error;
    }
  }

  /**
   * Type text into element
   * @param {string} sessionId - Session UUID
   * @param {string} selector - CSS selector
   * @param {string} text - Text to type
   * @returns {Promise<Object>} Type result
   */
  async typeText(sessionId, selector, text) {
    try {
      const response = await this.post("/type", {
        session_id: sessionId,
        selector,
        text,
      });
      logger.debug(`[MABA] Typed into ${selector}`);
      return response;
    } catch (error) {
      logger.error("[MABA] Type failed:", error);
      throw error;
    }
  }

  /**
   * Take screenshot
   * @param {string} sessionId - Session UUID
   * @param {Object} options - Screenshot options (full_page, quality)
   * @returns {Promise<Object>} Screenshot data (base64 or URL)
   */
  async takeScreenshot(sessionId, options = {}) {
    try {
      const response = await this.post("/screenshot", {
        session_id: sessionId,
        ...options,
      });
      logger.info("[MABA] Screenshot captured");
      return response;
    } catch (error) {
      logger.error("[MABA] Screenshot failed:", error);
      throw error;
    }
  }

  /**
   * Extract data from page
   * @param {string} sessionId - Session UUID
   * @param {Object} extractors - Data extractors (selectors, regex, etc.)
   * @returns {Promise<Object>} Extracted data
   */
  async extractData(sessionId, extractors) {
    try {
      const response = await this.post("/extract", {
        session_id: sessionId,
        extractors,
      });
      logger.info("[MABA] Data extracted");
      return response;
    } catch (error) {
      logger.error("[MABA] Extraction failed:", error);
      throw error;
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // COGNITIVE MAP
  // ────────────────────────────────────────────────────────────────────────────

  /**
   * Query cognitive map (Neo4j graph)
   * @param {Object} query - Query parameters (domain, url_pattern, limit)
   * @returns {Promise<Object>} Graph data (nodes, edges)
   */
  async queryCognitiveMap(query = {}) {
    try {
      const response = await this.post("/cognitive-map/query", query);
      logger.debug("[MABA] Cognitive map query:", response);
      return response;
    } catch (error) {
      logger.error("[MABA] Cognitive map query failed:", error);
      throw error;
    }
  }

  /**
   * Get cognitive map statistics
   * @returns {Promise<Object>} Stats (pages_learned, elements, domains)
   */
  async getCognitiveMapStats() {
    try {
      const response = await this.get("/cognitive-map/stats");
      logger.debug("[MABA] Cognitive map stats:", response);
      return response;
    } catch (error) {
      logger.error("[MABA] Failed to get cognitive map stats:", error);
      throw error;
    }
  }

  /**
   * Get learned page details
   * @param {string} pageId - Page node ID
   * @returns {Promise<Object>} Page details
   */
  async getLearnedPage(pageId) {
    try {
      const response = await this.get(`/cognitive-map/pages/${pageId}`);
      logger.debug("[MABA] Learned page retrieved:", pageId);
      return response;
    } catch (error) {
      logger.error("[MABA] Failed to get learned page:", error);
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
      throw new Error("[MABA] Invalid request data: must be an object");
    }

    // Validate session_id for browser actions
    if (data.session_id && typeof data.session_id !== "string") {
      throw new Error("[MABA] session_id must be a string");
    }

    // Validate URL format
    if (data.url) {
      try {
        new URL(data.url);
      } catch (e) {
        throw new Error("[MABA] Invalid URL format");
      }
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
    // Add timestamp if missing
    if (response && !response.timestamp) {
      response.timestamp = new Date().toISOString();
    }

    return response;
  }
}

// Singleton instance
export const mabaService = new MABAService();

export default mabaService;

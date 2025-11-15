/**
 * Base Service Class
 * ===================
 *
 * Foundation for all service layer classes.
 * Provides common functionality for API communication, error handling, and data transformation.
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002 (Service Layer Pattern)
 *
 * Architecture:
 * ┌─────────────────┐
 * │   Component     │  ← UI logic only
 * └────────┬────────┘
 *          │ uses
 * ┌────────▼────────┐
 * │  Custom Hook    │  ← React Query integration
 * └────────┬────────┘
 *          │ calls
 * ┌────────▼────────┐
 * │  Service Class  │  ← Business logic (THIS LAYER)
 * └────────┬────────┘
 *          │ uses
 * ┌────────▼────────┐
 * │   API Client    │  ← HTTP, auth, retry
 * └─────────────────┘
 */

import { apiClient } from "../../api/client";
import logger from "../../utils/logger";

export class BaseService {
  /**
   * @param {string} baseEndpoint - Base API endpoint (e.g., '/offensive')
   * @param {Object} client - API client instance (default: apiClient)
   */
  constructor(baseEndpoint, client = apiClient) {
    this.baseEndpoint = baseEndpoint;
    this.client = client;
  }

  /**
   * Makes a GET request
   * Boris Cherny Pattern: GET is idempotent → automatic retry
   *
   * @param {string} path - Endpoint path relative to baseEndpoint
   * @param {Object} options - Request options
   * @param {number} options.retry - Max retries (default: 3). Set to 0 to disable retry.
   * @param {number} options.retryDelay - Base retry delay in ms (default: 1000)
   * @returns {Promise<any>} Response data
   */
  async get(path = "", options = {}) {
    const endpoint = this.buildEndpoint(path);

    // Wrapper for retry
    const fetchFn = async () => {
      logger.debug(`[${this.constructor.name}] GET ${endpoint}`);
      const response = await this.client.get(endpoint, options);
      return this.transformResponse(response);
    };

    try {
      // GET is idempotent → retry automatically (unless explicitly disabled)
      const maxRetries = options.retry !== undefined ? options.retry : 3;
      const baseDelay = options.retryDelay || 1000;

      if (maxRetries > 0) {
        return await this.retry(fetchFn, maxRetries, baseDelay);
      } else {
        return await fetchFn();
      }
    } catch (error) {
      return this.handleError(error, "GET", endpoint);
    }
  }

  /**
   * Makes a POST request
   * Boris Cherny Pattern: POST is NOT idempotent → no retry by default
   *
   * @param {string} path - Endpoint path
   * @param {Object} data - Request body
   * @param {Object} options - Request options
   * @param {boolean} options.retry - Enable retry (default: false)
   * @param {number} options.maxRetries - Max retries when enabled (default: 2)
   * @param {number} options.retryDelay - Base retry delay in ms (default: 1000)
   * @returns {Promise<any>} Response data
   */
  async post(path = "", data = {}, options = {}) {
    const endpoint = this.buildEndpoint(path);

    try {
      // Validate data before sending (override in subclasses)
      this.validateRequest(data);

      const fetchFn = async () => {
        logger.debug(`[${this.constructor.name}] POST ${endpoint}`, data);
        const response = await this.client.post(endpoint, data, options);
        return this.transformResponse(response);
      };

      // POST/PUT/DELETE are NOT idempotent by default
      // Retry only if explicitly requested
      if (options.retry === true) {
        const maxRetries = options.maxRetries || 2; // More conservative
        const baseDelay = options.retryDelay || 1000;

        logger.debug(
          `[${this.constructor.name}] POST with retry enabled (max: ${maxRetries})`,
        );
        return await this.retry(fetchFn, maxRetries, baseDelay);
      } else {
        return await fetchFn();
      }
    } catch (error) {
      return this.handleError(error, "POST", endpoint);
    }
  }

  /**
   * Makes a PUT request
   * Boris Cherny Pattern: PUT is NOT idempotent → no retry by default
   *
   * @param {string} path - Endpoint path
   * @param {Object} data - Request body
   * @param {Object} options - Request options
   * @param {boolean} options.retry - Enable retry (default: false)
   * @param {number} options.maxRetries - Max retries when enabled (default: 2)
   * @param {number} options.retryDelay - Base retry delay in ms (default: 1000)
   * @returns {Promise<any>} Response data
   */
  async put(path = "", data = {}, options = {}) {
    const endpoint = this.buildEndpoint(path);

    try {
      this.validateRequest(data);

      const fetchFn = async () => {
        logger.debug(`[${this.constructor.name}] PUT ${endpoint}`, data);
        const response = await this.client.put(endpoint, data, options);
        return this.transformResponse(response);
      };

      // PUT is NOT idempotent by default - retry only if explicit
      if (options.retry === true) {
        const maxRetries = options.maxRetries || 2;
        const baseDelay = options.retryDelay || 1000;

        logger.debug(
          `[${this.constructor.name}] PUT with retry enabled (max: ${maxRetries})`,
        );
        return await this.retry(fetchFn, maxRetries, baseDelay);
      } else {
        return await fetchFn();
      }
    } catch (error) {
      return this.handleError(error, "PUT", endpoint);
    }
  }

  /**
   * Makes a DELETE request
   * Boris Cherny Pattern: DELETE is NOT idempotent → no retry by default
   *
   * @param {string} path - Endpoint path
   * @param {Object} options - Request options
   * @param {boolean} options.retry - Enable retry (default: false)
   * @param {number} options.maxRetries - Max retries when enabled (default: 2)
   * @param {number} options.retryDelay - Base retry delay in ms (default: 1000)
   * @returns {Promise<any>} Response data
   */
  async delete(path = "", options = {}) {
    const endpoint = this.buildEndpoint(path);

    try {
      const fetchFn = async () => {
        logger.debug(`[${this.constructor.name}] DELETE ${endpoint}`);
        const response = await this.client.delete(endpoint, options);
        return this.transformResponse(response);
      };

      // DELETE is NOT idempotent by default - retry only if explicit
      if (options.retry === true) {
        const maxRetries = options.maxRetries || 2;
        const baseDelay = options.retryDelay || 1000;

        logger.debug(
          `[${this.constructor.name}] DELETE with retry enabled (max: ${maxRetries})`,
        );
        return await this.retry(fetchFn, maxRetries, baseDelay);
      } else {
        return await fetchFn();
      }
    } catch (error) {
      return this.handleError(error, "DELETE", endpoint);
    }
  }

  /**
   * Builds full endpoint from base + path
   * @param {string} path - Relative path
   * @returns {string} Full endpoint
   * @protected
   */
  buildEndpoint(path) {
    if (!path) return this.baseEndpoint;
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    return `${this.baseEndpoint}${cleanPath}`;
  }

  /**
   * Validates request data before sending
   * Override in subclasses for specific validation
   *
   * Boris Cherny Pattern: Fail fast with clear error messages
   *
   * @param {Object} data - Request data
   * @throws {Error} If validation fails
   * @protected
   */
  validateRequest(data) {
    // Phase 1.4: Add basic validation enforcement
    if (data === null || data === undefined) {
      throw new Error("Request data cannot be null or undefined");
    }

    // Enforce non-empty objects for POST/PUT requests
    if (typeof data === "object" && !Array.isArray(data)) {
      const keys = Object.keys(data);
      if (keys.length === 0) {
        logger.warn(
          `${this.constructor.name}: Sending empty object. Consider if this is intentional.`,
        );
      }
    }

    // Check payload size (prevent accidental large payloads)
    const payloadSize = JSON.stringify(data).length;
    const MAX_PAYLOAD_SIZE = 5 * 1024 * 1024; // 5MB

    if (payloadSize > MAX_PAYLOAD_SIZE) {
      throw new Error(
        `Request payload too large: ${(payloadSize / 1024 / 1024).toFixed(2)}MB (max: 5MB)`,
      );
    }

    // Subclasses should override for specific validation
    return true;
  }

  /**
   * Transforms API response to domain model
   * Override in subclasses for custom transformations
   * @param {Object} response - Raw API response
   * @returns {Object} Transformed data
   * @protected
   */
  transformResponse(response) {
    // Base implementation: return as-is
    // Subclasses should override this
    return response;
  }

  /**
   * Handles errors consistently
   * @param {Error} error - Error object
   * @param {string} method - HTTP method
   * @param {string} endpoint - Endpoint that failed
   * @throws {Error} Processed error
   * @protected
   */
  handleError(error, method, endpoint) {
    logger.error(
      `[${this.constructor.name}] ${method} ${endpoint} failed:`,
      error,
    );

    // Enhanced error with context
    const enhancedError = new Error(
      error.message || `${method} request to ${endpoint} failed`,
    );
    enhancedError.originalError = error;
    enhancedError.method = method;
    enhancedError.endpoint = endpoint;
    enhancedError.service = this.constructor.name;

    throw enhancedError;
  }

  /**
   * Extracts error message from various error formats
   * @param {Error|Object} error - Error object
   * @returns {string} Error message
   * @protected
   */
  extractErrorMessage(error) {
    if (typeof error === "string") return error;
    if (error.message) return error.message;
    if (error.detail) return error.detail;
    if (error.error) return error.error;
    return "Unknown error occurred";
  }

  /**
   * Retries a function with exponential backoff
   * Boris Cherny Pattern: Smart retry with auth error detection
   *
   * @param {Function} fn - Function to retry
   * @param {number} maxRetries - Maximum retry attempts
   * @param {number} baseDelay - Base delay in ms
   * @returns {Promise<any>} Function result
   * @protected
   */
  async retry(fn, maxRetries = 3, baseDelay = 1000) {
    let lastError;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const result = await fn();

        // Log success after retry
        if (attempt > 0) {
          logger.info(
            `[${this.constructor.name}] Success after ${attempt} retry attempt(s)`,
          );
        }

        return result;
      } catch (error) {
        lastError = error;

        // Don't retry on auth errors (401/403)
        const errorMsg = this.extractErrorMessage(error);
        if (
          errorMsg.includes("401") ||
          errorMsg.includes("403") ||
          errorMsg.includes("Unauthorized") ||
          errorMsg.includes("Forbidden")
        ) {
          logger.warn(
            `[${this.constructor.name}] Auth error detected, skipping retry`,
          );
          throw error;
        }

        if (attempt < maxRetries - 1) {
          const delay = baseDelay * Math.pow(2, attempt); // Exponential: 1s, 2s, 4s

          logger.warn(
            `[${this.constructor.name}] Attempt ${attempt + 1}/${maxRetries} failed. ` +
              `Retrying in ${delay}ms...`,
            { error: errorMsg },
          );

          await new Promise((resolve) => setTimeout(resolve, delay));
        } else {
          logger.error(
            `[${this.constructor.name}] All ${maxRetries} retry attempts exhausted`,
            { error: errorMsg },
          );
        }
      }
    }

    throw lastError;
  }

  /**
   * Checks if service is healthy
   * @returns {Promise<boolean>} Health status
   */
  async healthCheck() {
    try {
      await this.get("/health");
      return true;
    } catch (error) {
      logger.error(`[${this.constructor.name}] Health check failed:`, error);
      return false;
    }
  }
}

export default BaseService;

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

import { apiClient } from '../../api/client';
import logger from '../../utils/logger';

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
   * @param {string} path - Endpoint path relative to baseEndpoint
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async get(path = '', options = {}) {
    const endpoint = this.buildEndpoint(path);

    try {
      logger.debug(`[${this.constructor.name}] GET ${endpoint}`);
      const response = await this.client.get(endpoint, options);
      return this.transformResponse(response);
    } catch (error) {
      return this.handleError(error, 'GET', endpoint);
    }
  }

  /**
   * Makes a POST request
   * @param {string} path - Endpoint path
   * @param {Object} data - Request body
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async post(path = '', data = {}, options = {}) {
    const endpoint = this.buildEndpoint(path);

    try {
      // Validate data before sending (override in subclasses)
      this.validateRequest(data);

      logger.debug(`[${this.constructor.name}] POST ${endpoint}`, data);
      const response = await this.client.post(endpoint, data, options);
      return this.transformResponse(response);
    } catch (error) {
      return this.handleError(error, 'POST', endpoint);
    }
  }

  /**
   * Makes a PUT request
   * @param {string} path - Endpoint path
   * @param {Object} data - Request body
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async put(path = '', data = {}, options = {}) {
    const endpoint = this.buildEndpoint(path);

    try {
      this.validateRequest(data);

      logger.debug(`[${this.constructor.name}] PUT ${endpoint}`, data);
      const response = await this.client.put(endpoint, data, options);
      return this.transformResponse(response);
    } catch (error) {
      return this.handleError(error, 'PUT', endpoint);
    }
  }

  /**
   * Makes a DELETE request
   * @param {string} path - Endpoint path
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async delete(path = '', options = {}) {
    const endpoint = this.buildEndpoint(path);

    try {
      logger.debug(`[${this.constructor.name}] DELETE ${endpoint}`);
      const response = await this.client.delete(endpoint, options);
      return this.transformResponse(response);
    } catch (error) {
      return this.handleError(error, 'DELETE', endpoint);
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
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${this.baseEndpoint}${cleanPath}`;
  }

  /**
   * Validates request data before sending
   * Override in subclasses for specific validation
   * @param {Object} data - Request data
   * @throws {Error} If validation fails
   * @protected
   */
  validateRequest(data) {
    // Base implementation: no validation
    // Subclasses should override this
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
    logger.error(`[${this.constructor.name}] ${method} ${endpoint} failed:`, error);

    // Enhanced error with context
    const enhancedError = new Error(
      error.message || `${method} request to ${endpoint} failed`
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
    if (typeof error === 'string') return error;
    if (error.message) return error.message;
    if (error.detail) return error.detail;
    if (error.error) return error.error;
    return 'Unknown error occurred';
  }

  /**
   * Retries a function with exponential backoff
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
        return await fn();
      } catch (error) {
        lastError = error;

        if (attempt < maxRetries - 1) {
          const delay = baseDelay * Math.pow(2, attempt);
          logger.warn(
            `[${this.constructor.name}] Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`
          );
          await new Promise(resolve => setTimeout(resolve, delay));
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
      await this.get('/health');
      return true;
    } catch (error) {
      logger.error(`[${this.constructor.name}] Health check failed:`, error);
      return false;
    }
  }
}

export default BaseService;

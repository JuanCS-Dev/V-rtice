/**
 * Centralized API Client
 * Uses API Gateway (8000) as single entry point
 * Governed by: Constituição Vértice v2.7, ADR-001, ADR-002
 *
 * Boris Cherny Pattern: Type-safe error handling with auth interceptor
 */

import { ServiceEndpoints, AuthConfig, httpToWs } from "../config/endpoints";
import {
  getCSRFToken,
  checkRateLimit,
  RateLimitError,
} from "../utils/security";
import logger from "../utils/logger";

const API_BASE = ServiceEndpoints.apiGateway;
const API_KEY = AuthConfig.apiKey;

/**
 * Timeout configuration
 * Boris Cherny Pattern: Explicit constants over magic numbers
 */
export const DEFAULT_TIMEOUT = 30000; // 30s - production-safe default
export const HEALTH_CHECK_TIMEOUT = 3000; // 3s - fast health checks

/**
 * Custom error classes for typed error handling
 */
export class UnauthorizedError extends Error {
  constructor(message = "Session expired") {
    super(message);
    this.name = "UnauthorizedError";
    this.status = 401;
  }
}

export class ForbiddenError extends Error {
  constructor(message = "Insufficient permissions") {
    super(message);
    this.name = "ForbiddenError";
    this.status = 403;
  }
}

/**
 * Token refresh function - will be set by AuthContext
 * This allows loose coupling between API client and Auth system
 */
let tokenRefreshHandler = null;

export const setTokenRefreshHandler = (handler) => {
  tokenRefreshHandler = handler;
};

/**
 * CORS Preflight cache (to avoid redundant OPTIONS requests)
 * Boris Cherny Pattern: Performance optimization with safety
 */
const corsPreflightCache = new Map();
const PREFLIGHT_CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const PREFLIGHT_TIMEOUT = 3000; // 3s timeout for preflight
const CORS_STRICT_MODE = false; // Set true to block on CORS failures

/**
 * Check CORS preflight (OPTIONS) for an endpoint
 *
 * Boris Cherny Pattern: Fail fast on CORS issues
 *
 * Features:
 * - Cache preflight results (5 min TTL)
 * - Timeout protection (3s)
 * - Retry on network errors (1 retry)
 * - Strict mode option (block on failure)
 *
 * @param {string} endpoint - Endpoint to check
 * @returns {Promise<boolean>} Whether CORS is allowed
 * @throws {Error} In strict mode, throws on CORS failure
 */
const checkCORSPreflight = async (endpoint) => {
  // Check cache first
  const cached = corsPreflightCache.get(endpoint);
  if (cached && Date.now() - cached.timestamp < PREFLIGHT_CACHE_TTL) {
    logger.debug(`CORS preflight cache hit for ${endpoint}`);
    return cached.allowed;
  }

  const url = `${API_BASE}${endpoint}`;
  let lastError = null;

  // Try up to 2 times (1 retry) for network resilience
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      // Create AbortController for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), PREFLIGHT_TIMEOUT);

      const response = await fetch(url, {
        method: "OPTIONS",
        signal: controller.signal,
        headers: {
          "Access-Control-Request-Method": "POST",
          "Access-Control-Request-Headers": "content-type,x-api-key,x-csrf-token",
        },
      });

      clearTimeout(timeoutId);

      // Check if CORS is allowed
      const allowed = response.ok || response.status === 204;

      // Cache result (even failures - avoid hammering)
      corsPreflightCache.set(endpoint, {
        allowed,
        timestamp: Date.now(),
      });

      if (!allowed) {
        logger.warn(
          `CORS preflight failed for ${endpoint}`,
          {
            status: response.status,
            statusText: response.statusText,
            attempt: attempt + 1,
          }
        );

        if (CORS_STRICT_MODE) {
          throw new Error(
            `CORS preflight failed: ${response.status} ${response.statusText}`
          );
        }
      } else {
        if (attempt > 0) {
          logger.info(`CORS preflight succeeded on retry for ${endpoint}`);
        }
      }

      return allowed;

    } catch (error) {
      lastError = error;

      // Timeout error
      if (error.name === 'AbortError') {
        logger.warn(`CORS preflight timeout for ${endpoint} (attempt ${attempt + 1}/2)`);

        if (attempt === 0) {
          // Retry once on timeout
          await new Promise(resolve => setTimeout(resolve, 500));
          continue;
        }

        if (CORS_STRICT_MODE) {
          throw new Error(`CORS preflight timeout after ${PREFLIGHT_TIMEOUT}ms`);
        }
      }

      // Network error
      logger.warn(
        `CORS preflight network error for ${endpoint} (attempt ${attempt + 1}/2)`,
        { error: error.message }
      );

      if (attempt === 0) {
        // Retry once on network error
        await new Promise(resolve => setTimeout(resolve, 500));
        continue;
      }
    }
  }

  // All attempts failed
  logger.error(
    `CORS preflight failed after all attempts for ${endpoint}`,
    { error: lastError?.message }
  );

  if (CORS_STRICT_MODE) {
    throw new Error(
      `CORS preflight failed: ${lastError?.message || 'Unknown error'}`
    );
  }

  // Permissive mode: allow request to proceed (it will fail naturally if CORS is really broken)
  // Cache negative result to avoid repeated failed checks
  corsPreflightCache.set(endpoint, {
    allowed: true, // Permissive: let request try
    timestamp: Date.now(),
  });

  return true;
};

/**
 * Internal request function with auth interceptor
 * Boris Cherny Pattern: Single Responsibility - handles HTTP only
 *
 * Features:
 * - Automatic timeout with AbortController
 * - Configurable timeout via options.timeout
 * - Proper cleanup (clearTimeout)
 * - Clear error messages
 */
const makeRequest = async (url, options) => {
  // Create AbortController for timeout
  const controller = new AbortController();
  const timeout = options.timeout !== undefined ? options.timeout : DEFAULT_TIMEOUT;

  // Set timeout - abort request if it takes too long
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
        "X-CSRF-Token": getCSRFToken(),
        ...options.headers,
      },
    });

    // Clear timeout on success
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    // Always clear timeout
    clearTimeout(timeoutId);

    // Differentiate timeout from other errors
    if (error.name === "AbortError") {
      const seconds = timeout / 1000;
      logger.warn(`Request timeout after ${seconds}s: ${url}`);
      throw new Error(`Request timeout after ${seconds}s`);
    }

    // Re-throw other errors
    throw error;
  }
};

/**
 * Main request function with 401/403 auth interceptor
 * Implements automatic token refresh and graceful degradation
 */
const request = async (endpoint, options = {}, isRetry = false) => {
  const url = `${API_BASE}${endpoint}`;

  try {
    // Check rate limit before making request
    try {
      checkRateLimit(endpoint);
    } catch (error) {
      if (error instanceof RateLimitError) {
        logger.warn(
          `Rate limit exceeded for ${endpoint}. Retry after ${error.retryAfter}s`,
        );
        throw error;
      }
      throw error;
    }

    // Phase 1.5: Check CORS preflight (non-blocking)
    // This helps identify CORS issues proactively but won't block requests
    if (!isRetry && options.method === "POST") {
      await checkCORSPreflight(endpoint);
    }

    const response = await makeRequest(url, options);

    // Handle authentication errors BEFORE checking response.ok
    if (response.status === 401) {
      // Unauthorized - token expired or invalid
      if (!isRetry && tokenRefreshHandler) {
        logger.info("Access token expired, attempting refresh...");

        try {
          const refreshed = await tokenRefreshHandler();

          if (refreshed) {
            logger.info("Token refreshed successfully, retrying request");
            // Retry the request with new token (prevent infinite loop with isRetry flag)
            return request(endpoint, options, true);
          }
        } catch (refreshError) {
          logger.error("Token refresh failed:", refreshError);
        }
      }

      // Clear auth data and redirect to login
      logger.warn("Session expired, redirecting to login");
      localStorage.removeItem("vertice_auth_token");
      localStorage.removeItem("vertice_user");
      localStorage.removeItem("vertice_token_expiry");

      // Redirect to login page (if not already there)
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }

      throw new UnauthorizedError("Session expired. Please log in again.");
    }

    if (response.status === 403) {
      // Forbidden - user lacks permissions
      logger.warn(`Access forbidden for ${endpoint}`);
      throw new ForbiddenError(
        "You do not have permission to perform this action.",
      );
    }

    if (!response.ok) {
      const error = await response.json().catch((parseError) => {
        logger.warn("Failed to parse error response:", parseError);
        return {};
      });
      throw new Error(
        error.detail || `API Error: ${response.status} ${response.statusText}`,
      );
    }

    return await response.json();
  } catch (error) {
    // Re-throw custom errors as-is
    if (
      error instanceof UnauthorizedError ||
      error instanceof ForbiddenError ||
      error instanceof RateLimitError
    ) {
      throw error;
    }

    // Wrap generic errors
    if (error.message.includes("API Error")) {
      throw error;
    }

    throw new Error(`Network error: ${error.message}`);
  }
};

export const apiClient = {
  get: (endpoint, options = {}) =>
    request(endpoint, { ...options, method: "GET" }),

  post: (endpoint, data = {}, options = {}) =>
    request(endpoint, {
      ...options,
      method: "POST",
      body: JSON.stringify(data),
    }),

  put: (endpoint, data = {}, options = {}) =>
    request(endpoint, {
      ...options,
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (endpoint, options = {}) =>
    request(endpoint, { ...options, method: "DELETE" }),

  request,
};

export const directClient = {
  async request(baseUrl, path, options = {}) {
    const url = `${baseUrl}${path}`;

    // Create AbortController for timeout (same pattern as makeRequest)
    const controller = new AbortController();
    const timeout = options.timeout !== undefined ? options.timeout : DEFAULT_TIMEOUT;

    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": API_KEY,
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      // Apply same auth error handling as main client
      if (response.status === 401) {
        logger.warn("Direct API call received 401 Unauthorized");
        throw new UnauthorizedError("Unauthorized access to direct API");
      }

      if (response.status === 403) {
        logger.warn("Direct API call received 403 Forbidden");
        throw new ForbiddenError("Forbidden access to direct API");
      }

      if (!response.ok) {
        const error = await response.json().catch((parseError) => {
          logger.warn("Failed to parse direct API error response:", parseError);
          return {};
        });
        throw new Error(error.detail || `API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Always clear timeout
      clearTimeout(timeoutId);

      // Handle timeout errors
      if (error.name === "AbortError") {
        const seconds = timeout / 1000;
        logger.warn(`Direct API request timeout after ${seconds}s: ${url}`);
        throw new Error(`Request timeout after ${seconds}s`);
      }

      // Re-throw custom errors
      if (
        error instanceof UnauthorizedError ||
        error instanceof ForbiddenError
      ) {
        throw error;
      }

      if (error.message.includes("API Error")) {
        throw error;
      }
      throw new Error(`Network error: ${error.message}`);
    }
  },
};

export const getWebSocketUrl = (endpoint) => {
  const wsBase = httpToWs(API_BASE);
  return `${wsBase}${endpoint}${endpoint.includes("?") ? "&" : "?"}api_key=${API_KEY}`;
};

export default apiClient;

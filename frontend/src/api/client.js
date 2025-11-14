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

/**
 * Check CORS preflight (OPTIONS) for an endpoint
 * Phase 1.5: Detect CORS issues before actual requests fail
 */
const checkCORSPreflight = async (endpoint) => {
  // Check cache first
  const cached = corsPreflightCache.get(endpoint);
  if (cached && Date.now() - cached.timestamp < PREFLIGHT_CACHE_TTL) {
    return cached.allowed;
  }

  try {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      method: "OPTIONS",
      headers: {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-api-key,x-csrf-token",
      },
    });

    const allowed = response.ok || response.status === 204;

    // Cache result
    corsPreflightCache.set(endpoint, {
      allowed,
      timestamp: Date.now(),
    });

    if (!allowed) {
      logger.warn(`CORS preflight failed for ${endpoint}: ${response.status}`);
    }

    return allowed;
  } catch (error) {
    logger.warn(`CORS preflight check failed for ${endpoint}:`, error);
    // Don't block the request - let it proceed and fail naturally if CORS is really broken
    return true;
  }
};

/**
 * Internal request function with auth interceptor
 * Boris Cherny Pattern: Single Responsibility - handles HTTP only
 */
const makeRequest = async (url, options) => {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      "X-CSRF-Token": getCSRFToken(),
      ...options.headers,
    },
  });

  return response;
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

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": API_KEY,
          ...options.headers,
        },
      });

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

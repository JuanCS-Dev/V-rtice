/**
 * Type-safe API client using openapi-fetch
 *
 * DOUTRINA VÉRTICE - GAP #5 (P1)
 * End-to-end type safety from OpenAPI schema
 *
 * Following Boris Cherny's principle: "Types flow from the source of truth"
 *
 * Usage:
 * ```typescript
 * import { apiClient } from '@/api/typedClient';
 *
 * // Fully type-safe!
 * const { data, error } = await apiClient.GET('/api/v1/health');
 *
 * if (error) {
 *   console.error(error); // TypeScript knows error shape
 * } else {
 *   console.log(data.status); // TypeScript knows data.status exists
 * }
 * ```
 */

import createClient from "openapi-fetch";
import type { paths } from "@/types/api";

// API base URL from environment
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Type-safe API client
 *
 * All methods (GET, POST, PUT, DELETE, etc.) are fully typed based on OpenAPI schema.
 * TypeScript will:
 * - Autocomplete available endpoints
 * - Validate request bodies
 * - Validate query parameters
 * - Provide typed responses
 * - Show errors for invalid requests
 */
export const typedApiClient = createClient<paths>({
  baseUrl: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Add authentication token to requests
 *
 * Call this after user logs in to set auth token
 */
export function setAuthToken(token: string) {
  typedApiClient.use({
    async onRequest({ request }) {
      request.headers.set("Authorization", `Bearer ${token}`);
      return request;
    },
  });
}

/**
 * Add request ID to all requests
 *
 * For distributed tracing (P0-4)
 */
typedApiClient.use({
  async onRequest({ request }) {
    // Generate request ID if not present
    if (!request.headers.has("X-Request-ID")) {
      const requestId = crypto.randomUUID();
      request.headers.set("X-Request-ID", requestId);
    }
    return request;
  },
});

/**
 * Handle global errors
 *
 * Add request ID to error context
 */
typedApiClient.use({
  async onResponse({ response }) {
    if (!response.ok) {
      const requestId = response.headers.get("X-Request-ID");
      console.error(`API Error [Request ID: ${requestId}]:`, {
        status: response.status,
        url: response.url,
      });
    }
    return response;
  },
});

// Re-export for convenience
export default typedApiClient;

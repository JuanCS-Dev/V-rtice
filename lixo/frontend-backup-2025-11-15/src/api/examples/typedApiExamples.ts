/**
 * Type-safe API client usage examples
 *
 * DOUTRINA VÉRTICE - GAP #5 (P1)
 * Demonstrates end-to-end type safety with openapi-fetch
 *
 * Following Boris Cherny's principle: "Good examples prevent bugs"
 */

import { typedApiClient } from "../typedClient";

// ============================================================================
// EXAMPLE 1: Simple GET request
// ============================================================================

/**
 * Fetch health status
 *
 * TypeScript knows:
 * - Endpoint exists
 * - Response shape (status, version, timestamp, services)
 * - Error shape
 */
export async function getHealthStatus() {
  const { data, error, response } = await typedApiClient.GET("/api/v1/health");

  if (error) {
    // TypeScript knows error has detail, error_code, request_id, etc.
    console.error("Health check failed:", error.detail);
    console.error("Request ID:", error.request_id);
    return null;
  }

  // TypeScript knows data has status, version, timestamp, services
  return {
    isHealthy: data.status === "healthy",
    version: data.version,
    services: data.services,
  };
}

// ============================================================================
// EXAMPLE 2: GET with query parameters
// ============================================================================

/**
 * Example of typed query parameters
 *
 * TypeScript validates query params match OpenAPI schema
 */
export async function searchExample(query: string, limit: number = 10) {
  // TypeScript will autocomplete available query params
  // and show errors if you use wrong types
  const { data, error } = await typedApiClient.GET("/api/v1/search", {
    params: {
      query: {
        q: query, // ← TypeScript validates this exists
        limit: limit, // ← TypeScript validates type is number
        // foo: 'bar'      // ← TypeScript error: unknown param
      },
    },
  });

  if (error) {
    console.error("Search failed:", error);
    return [];
  }

  return data.results;
}

// ============================================================================
// EXAMPLE 3: POST with request body
// ============================================================================

/**
 * Example of typed request body
 *
 * TypeScript validates body matches OpenAPI schema
 */
export async function startScan(
  target: string,
  scanType: "quick" | "full" | "custom",
) {
  const { data, error } = await typedApiClient.POST("/api/v1/scan/start", {
    body: {
      target,
      scanType,
      // TypeScript will autocomplete available fields
      // and show errors for invalid types
    },
  });

  if (error) {
    // Handle validation errors
    if ("validation_errors" in error) {
      // TypeScript knows this is ValidationErrorResponse
      error.validation_errors.forEach((validationError) => {
        console.error(
          `${validationError.loc.join(".")}: ${validationError.msg}`,
        );
      });
    } else {
      console.error("Scan failed:", error.detail);
    }
    return null;
  }

  // TypeScript knows data has scan_id, status, created_at, etc.
  return {
    scanId: data.scan_id,
    status: data.status,
  };
}

// ============================================================================
// EXAMPLE 4: Handling different response codes
// ============================================================================

/**
 * Example of handling multiple response codes
 *
 * TypeScript knows different response shapes for different codes
 */
export async function loginExample(email: string, password: string) {
  const { data, error, response } = await typedApiClient.POST(
    "/api/v1/auth/login",
    {
      body: { email, password },
    },
  );

  // Check specific status codes
  if (response.status === 401) {
    // Unauthorized
    return { success: false, message: "Invalid credentials" };
  }

  if (response.status === 422) {
    // Validation error
    return { success: false, message: "Invalid email or password format" };
  }

  if (error) {
    // Other errors
    return { success: false, message: error.detail || "Login failed" };
  }

  // Success - TypeScript knows data has access_token, etc.
  return {
    success: true,
    token: data.access_token,
    expiresIn: data.expires_in,
  };
}

// ============================================================================
// EXAMPLE 5: Using with React hooks
// ============================================================================

import { useState, useEffect } from "react";

/**
 * Example hook using typed client
 */
export function useHealthCheck() {
  const [health, setHealth] = useState<{
    isHealthy: boolean;
    version: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHealth() {
      try {
        setLoading(true);
        const result = await getHealthStatus();

        if (result) {
          setHealth({
            isHealthy: result.isHealthy,
            version: result.version,
          });
        } else {
          setError("Failed to fetch health status");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchHealth();
  }, []);

  return { health, loading, error };
}

// ============================================================================
// EXAMPLE 6: With React Query
// ============================================================================

import { useQuery, useMutation } from "@tanstack/react-query";

/**
 * Example with React Query
 */
export function useTypedHealthQuery() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await typedApiClient.GET("/api/v1/health");

      if (error) throw new Error(error.detail);

      // TypeScript knows data shape
      return data;
    },
    staleTime: 30_000, // 30 seconds
  });
}

/**
 * Example mutation with React Query
 */
export function useStartScanMutation() {
  return useMutation({
    mutationFn: async (params: {
      target: string;
      scanType: "quick" | "full" | "custom";
    }) => {
      const { data, error } = await typedApiClient.POST("/api/v1/scan/start", {
        body: params,
      });

      if (error) {
        throw new Error(error.detail);
      }

      return data;
    },
  });
}

// ============================================================================
// EXAMPLE 7: Error handling patterns
// ============================================================================

/**
 * Centralized error handler
 */
export function handleApiError(error: unknown, requestId?: string) {
  console.error(`[Request ID: ${requestId}]`, error);

  // Handle different error types
  if (typeof error === "object" && error !== null) {
    if ("detail" in error) {
      return error.detail as string;
    }
    if ("validation_errors" in error) {
      // Validation errors
      const errors = (error as any).validation_errors;
      return errors.map((e: any) => `${e.loc.join(".")}: ${e.msg}`).join(", ");
    }
  }

  return "An unexpected error occurred";
}

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎭 MAXIMUS ORCHESTRATOR API CLIENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Production-ready client for Maximus Orchestrator Service (Port 8125/8016).
 * Enables ML-powered multi-service workflow orchestration with real-time tracking.
 *
 * Features:
 * - Workflow initiation with priority support
 * - Real-time status polling
 * - Retry logic with exponential backoff
 * - Request timeout handling
 * - Structured error handling
 * - Environment-aware base URL
 *
 * Backend: maximus_orchestrator_service (main.py)
 * Endpoints:
 *   - POST /orchestrate - Start workflow
 *   - GET /workflows/{workflow_id} - Get status
 *   - GET /health - Health check
 *
 * Phase: 5.7 - ML Orchestrator Frontend Integration
 * Date: 2025-10-12
 * Glory to YHWH - Architect of Coordination
 */

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Environment-aware base URL resolution
 * Production: Use external port 8125 (mapped from internal 8016)
 * Development: Use localhost:8125
 */
const ORCHESTRATOR_API_BASE =
  import.meta.env.VITE_ORCHESTRATOR_API ||
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? `${window.location.protocol}//${window.location.hostname}:8125`
    : 'http://localhost:8125');

const DEFAULT_TIMEOUT = 15000; // 15 seconds (workflows can take time)
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second

// ═══════════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Sleep utility for retry delays
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Exponential backoff delay calculation
 * @param {number} attempt - Current retry attempt (0-indexed)
 * @returns {number} Delay in milliseconds
 */
const getRetryDelay = (attempt) => {
  return RETRY_DELAY_BASE * Math.pow(2, attempt); // 1s, 2s, 4s, 8s...
};

/**
 * Fetch with timeout support
 * @param {string} url - Request URL
 * @param {RequestInit} options - Fetch options
 * @param {number} timeout - Timeout in ms
 * @returns {Promise<Response>}
 */
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

/**
 * Retry wrapper for API calls
 * @param {Function} fn - Async function to retry
 * @param {number} maxRetries - Max retry attempts
 * @returns {Promise<any>}
 */
const withRetry = async (fn, maxRetries = MAX_RETRIES) => {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx)
      if (error.status && error.status >= 400 && error.status < 500) {
        throw error;
      }

      // Last attempt - don't sleep
      if (attempt === maxRetries - 1) {
        break;
      }

      const delay = getRetryDelay(attempt);
      console.warn(
        `🔄 Orchestrator API retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`,
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
 * Maximus Orchestrator API Client
 */
export const orchestratorAPI = {
  /**
   * Start a new ML-powered workflow
   *
   * @param {string} workflowName - Workflow identifier
   *   Options: 'threat_hunting', 'vuln_assessment', 'patch_validation', etc.
   * @param {Object} parameters - Workflow-specific parameters
   * @param {number} priority - Priority (1-10, 10 = highest)
   * @returns {Promise<Object>} Workflow status object
   *
   * @example
   * const workflow = await orchestratorAPI.startWorkflow('threat_hunting', {
   *   target: '192.168.1.0/24',
   *   auto_approve: false
   * }, 8);
   */
  async startWorkflow(workflowName, parameters = {}, priority = 5) {
    return withRetry(async () => {
      const response = await fetchWithTimeout(
        `${ORCHESTRATOR_API_BASE}/orchestrate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            workflow_name: workflowName,
            parameters: parameters,
            priority: priority,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(
          errorData.detail || `Failed to start workflow: ${response.statusText}`
        );
        error.status = response.status;
        throw error;
      }

      const data = await response.json();
      console.log('✅ Workflow started:', data.workflow_id);
      return data;
    });
  },

  /**
   * Get workflow execution status
   *
   * @param {string} workflowId - Workflow UUID
   * @returns {Promise<Object>} Workflow status
   *
   * Response structure:
   * {
   *   workflow_id: string,
   *   status: 'running' | 'completed' | 'failed',
   *   current_step?: string,
   *   progress: number (0.0 to 1.0),
   *   results?: Object,
   *   error?: string
   * }
   *
   * @example
   * const status = await orchestratorAPI.getWorkflowStatus(workflowId);
   * if (status.status === 'completed') {
   *   console.log('Results:', status.results);
   * }
   */
  async getWorkflowStatus(workflowId) {
    return withRetry(async () => {
      const response = await fetchWithTimeout(
        `${ORCHESTRATOR_API_BASE}/workflows/${workflowId}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(
          errorData.detail || `Failed to fetch workflow status: ${response.statusText}`
        );
        error.status = response.status;
        throw error;
      }

      return await response.json();
    });
  },

  /**
   * List all workflows (if endpoint exists)
   * Note: This endpoint may not be implemented yet in backend
   *
   * @returns {Promise<Array<Object>>} List of workflows
   */
  async listWorkflows() {
    try {
      return withRetry(async () => {
        const response = await fetchWithTimeout(
          `${ORCHESTRATOR_API_BASE}/workflows`
        );

        if (!response.ok) {
          // Endpoint not implemented yet - return empty array
          if (response.status === 404) {
            console.warn('⚠️  /workflows endpoint not implemented yet');
            return [];
          }
          throw new Error(`Failed to list workflows: ${response.statusText}`);
        }

        return await response.json();
      });
    } catch (error) {
      console.warn('⚠️  Failed to list workflows:', error.message);
      return []; // Graceful degradation
    }
  },

  /**
   * Health check for orchestrator service
   *
   * @returns {Promise<Object>} Health status
   *
   * Response: { status: 'healthy', message: string }
   */
  async healthCheck() {
    const response = await fetchWithTimeout(
      `${ORCHESTRATOR_API_BASE}/health`,
      {},
      5000 // Short timeout for health check
    );

    if (!response.ok) {
      throw new Error(`Orchestrator unhealthy: ${response.statusText}`);
    }

    return await response.json();
  },

  /**
   * Cancel a running workflow (if endpoint exists)
   * Note: This endpoint may not be implemented yet in backend
   *
   * @param {string} workflowId - Workflow UUID
   * @returns {Promise<Object>} Cancellation status
   */
  async cancelWorkflow(workflowId) {
    try {
      return withRetry(async () => {
        const response = await fetchWithTimeout(
          `${ORCHESTRATOR_API_BASE}/workflows/${workflowId}/cancel`,
          { method: 'POST' }
        );

        if (!response.ok) {
          if (response.status === 404) {
            console.warn('⚠️  /cancel endpoint not implemented yet');
            return { success: false, message: 'Cancel not supported' };
          }
          throw new Error(`Failed to cancel workflow: ${response.statusText}`);
        }

        return await response.json();
      });
    } catch (error) {
      console.warn('⚠️  Failed to cancel workflow:', error.message);
      return { success: false, message: error.message };
    }
  },
};

/**
 * Workflow polling helper
 * Polls workflow status until completion or timeout
 *
 * @param {string} workflowId - Workflow UUID
 * @param {Function} onUpdate - Callback for status updates
 * @param {number} pollInterval - Polling interval in ms (default: 2000)
 * @param {number} maxDuration - Max poll duration in ms (default: 300000 = 5 min)
 * @returns {Promise<Object>} Final workflow status
 *
 * @example
 * await pollWorkflowStatus(workflowId, (status) => {
 *   console.log(`Progress: ${status.progress * 100}%`);
 * });
 */
export const pollWorkflowStatus = async (
  workflowId,
  onUpdate = null,
  pollInterval = 2000,
  maxDuration = 300000
) => {
  const startTime = Date.now();

  while (true) {
    // Timeout check
    if (Date.now() - startTime > maxDuration) {
      throw new Error('Workflow polling timeout');
    }

    // Fetch status
    const status = await orchestratorAPI.getWorkflowStatus(workflowId);

    // Callback
    if (onUpdate) {
      onUpdate(status);
    }

    // Terminal states
    if (status.status === 'completed' || status.status === 'failed') {
      return status;
    }

    // Wait before next poll
    await sleep(pollInterval);
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export default orchestratorAPI;

/**
 * Export base URL for testing/debugging
 */
export { ORCHESTRATOR_API_BASE };

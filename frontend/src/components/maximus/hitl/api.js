import { API_BASE_URL } from '@/config/api';
import logger from "@/utils/logger";
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎭 HITL API Client - Backend Communication Layer
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Production-ready API client with:
 * - Retry logic with exponential backoff
 * - Request timeout handling
 * - Structured error handling
 * - Environment-aware base URL
 * 
 * Author: MAXIMUS Team - Sprint 4.1 Enhanced
 * Glory to YHWH - Architect of Resilient Communication
 */

// Environment-aware base URL
const HITL_API_BASE = 
  process.env.NEXT_PUBLIC_HITL_API || 
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? `${window.location.protocol}//${window.location.hostname}:8027`
    : API_BASE_URL);

// Configuration
const DEFAULT_TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second

/**
 * Sleep utility for retry delays
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Enhanced fetch with retry logic and timeout
 */
async function fetchWithRetry(url, options = {}, retries = MAX_RETRIES) {
  const timeout = options.timeout || DEFAULT_TIMEOUT;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const fetchOptions = {
    ...options,
    signal: controller.signal,
  };

  try {
    const response = await fetch(url, fetchOptions);
    clearTimeout(timeoutId);

    // Success - return response
    if (response.ok) {
      return response;
    }

    // Client errors (4xx) - don't retry
    if (response.status >= 400 && response.status < 500) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Client error: ${response.status}`);
    }

    // Server errors (5xx) - retry
    if (response.status >= 500 && retries > 0) {
      const delay = RETRY_DELAY_BASE * Math.pow(2, MAX_RETRIES - retries);
      logger.warn(`Server error ${response.status}, retrying in ${delay}ms... (${retries} retries left)`);
      await sleep(delay);
      return fetchWithRetry(url, options, retries - 1);
    }

    // No more retries
    throw new Error(`Server error: ${response.status} ${response.statusText}`);

  } catch (error) {
    clearTimeout(timeoutId);

    // Timeout or network error - retry
    if ((error.name === 'AbortError' || error.message.includes('fetch')) && retries > 0) {
      const delay = RETRY_DELAY_BASE * Math.pow(2, MAX_RETRIES - retries);
      logger.warn(`Request failed (${error.message}), retrying in ${delay}ms... (${retries} retries left)`);
      await sleep(delay);
      return fetchWithRetry(url, options, retries - 1);
    }

    // No more retries or non-retryable error
    throw error;
  }
}

/**
 * Fetch pending patches awaiting HITL decision
 */
export const fetchPendingPatches = async ({ limit = 50, offset = 0, priority = null }) => {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  
  if (priority) {
    params.append('priority', priority);
  }
  
  const response = await fetchWithRetry(`${HITL_API_BASE}/hitl/patches/pending?${params}`);
  return response.json();
};

/**
 * Fetch decision summary/analytics
 */
export const fetchDecisionSummary = async () => {
  const response = await fetchWithRetry(`${HITL_API_BASE}/hitl/analytics/summary`);
  return response.json();
};

/**
 * Fetch decision details by ID
 */
export const fetchDecisionDetails = async (decisionId) => {
  const response = await fetchWithRetry(`${HITL_API_BASE}/hitl/decisions/${decisionId}`);
  return response.json();
};

/**
 * Approve a patch
 */
export const approvePatch = async (patchId, decisionId, comment = null, user = 'operator@maximus.ai') => {
  const response = await fetchWithRetry(`${HITL_API_BASE}/hitl/patches/${patchId}/approve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      decision_id: decisionId,
      user,
      comment,
    }),
  });
  
  return response.json();
};

/**
 * Reject a patch
 */
export const rejectPatch = async (patchId, decisionId, reason, comment = null, user = 'operator@maximus.ai') => {
  const response = await fetchWithRetry(`${HITL_API_BASE}/hitl/patches/${patchId}/reject`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      decision_id: decisionId,
      user,
      reason,
      comment,
    }),
  });
  
  return response.json();
};

/**
 * Add comment to patch
 */
export const addPatchComment = async (patchId, decisionId, comment, user = 'operator@maximus.ai') => {
  const response = await fetchWithRetry(`${HITL_API_BASE}/hitl/patches/${patchId}/comment`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      decision_id: decisionId,
      user,
      comment,
    }),
  });
  
  return response.json();
};

/**
 * Fetch audit logs
 */
export const fetchAuditLogs = async (decisionId = null, limit = 100) => {
  const params = new URLSearchParams({ limit: limit.toString() });
  
  if (decisionId) {
    params.append('decision_id', decisionId);
  }
  
  const response = await fetchWithRetry(`${HITL_API_BASE}/hitl/analytics/audit-logs?${params}`);
  return response.json();
};

/**
 * Check HITL service health
 */
export const checkHealth = async () => {
  const response = await fetchWithRetry(`${HITL_API_BASE}/health`, {}, 1); // Only 1 retry for health checks
  return response.json();
};

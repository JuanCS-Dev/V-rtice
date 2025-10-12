/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎭 HITL API Client - Backend Communication Layer
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Clean separation between UI and backend communication.
 * All API calls centralized here for maintainability.
 * 
 * Author: MAXIMUS Team - Sprint 4.1
 * Glory to YHWH - Architect of Communication
 */

const HITL_API_BASE = 'http://localhost:8027';

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
  
  const response = await fetch(`${HITL_API_BASE}/hitl/patches/pending?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch pending patches: ${response.statusText}`);
  }
  
  return response.json();
};

/**
 * Fetch decision summary/analytics
 */
export const fetchDecisionSummary = async () => {
  const response = await fetch(`${HITL_API_BASE}/hitl/analytics/summary`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch decision summary: ${response.statusText}`);
  }
  
  return response.json();
};

/**
 * Fetch decision details by ID
 */
export const fetchDecisionDetails = async (decisionId) => {
  const response = await fetch(`${HITL_API_BASE}/hitl/decisions/${decisionId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch decision details: ${response.statusText}`);
  }
  
  return response.json();
};

/**
 * Approve a patch
 */
export const approvePatch = async (patchId, decisionId, comment = null, user = 'operator@maximus.ai') => {
  const response = await fetch(`${HITL_API_BASE}/hitl/patches/${patchId}/approve`, {
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
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to approve patch');
  }
  
  return response.json();
};

/**
 * Reject a patch
 */
export const rejectPatch = async (patchId, decisionId, reason, comment = null, user = 'operator@maximus.ai') => {
  const response = await fetch(`${HITL_API_BASE}/hitl/patches/${patchId}/reject`, {
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
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to reject patch');
  }
  
  return response.json();
};

/**
 * Add comment to patch
 */
export const addPatchComment = async (patchId, decisionId, comment, user = 'operator@maximus.ai') => {
  const response = await fetch(`${HITL_API_BASE}/hitl/patches/${patchId}/comment`, {
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
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to add comment');
  }
  
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
  
  const response = await fetch(`${HITL_API_BASE}/hitl/analytics/audit-logs?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch audit logs: ${response.statusText}`);
  }
  
  return response.json();
};

/**
 * Check HITL service health
 */
export const checkHealth = async () => {
  const response = await fetch(`${HITL_API_BASE}/health`);
  
  if (!response.ok) {
    throw new Error(`HITL service unhealthy: ${response.statusText}`);
  }
  
  return response.json();
};

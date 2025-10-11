/**
 * Cockpit Shared Protocol Types - TypeScript
 * ==========================================
 * 
 * Auto-generated from cockpit-shared-protocol.yaml v1.0.0
 * 
 * Autor: Juan Carlo de Souza (JuanCS-DEV @github)
 * Email: juan.brainfarma@gmail.com
 * Data: 2024-10-08
 * 
 * Conforme Doutrina Vértice - Artigo II: NO MOCK, NO PLACEHOLDER
 */

// =============================================================================
// ENUMS
// =============================================================================

/**
 * Classification of arousal level (MCEA - Modular Conscious Excitability Architecture)
 */
export enum ArousalLevel {
  ASLEEP = 'asleep',           // arousal < 0.1
  DROWSY = 'drowsy',           // 0.1 <= arousal < 0.3
  AWAKE = 'awake',             // 0.3 <= arousal < 0.6
  ALERT = 'alert',             // 0.6 <= arousal < 0.8
  HYPERAROUSED = 'hyperaroused' // arousal >= 0.8
}

/**
 * Overall health status of consciousness system
 */
export enum SystemHealth {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  CRITICAL = 'critical',
  UNKNOWN = 'unknown'
}

/**
 * Reason for ESGT ignition failure
 */
export enum ESGTReason {
  LOW_SALIENCE = 'low_salience',       // Total salience below threshold
  SUPPRESSED = 'suppressed',           // Actively suppressed by control
  INSUFFICIENT_PHI = 'insufficient_phi', // Phi below minimum
  TIMEOUT = 'timeout',                 // Processing timeout
  NULL = 'null'                        // Success case
}

/**
 * Trend direction for metrics
 */
export enum TrendDirection {
  INCREASING = 'increasing',
  DECREASING = 'decreasing',
  STABLE = 'stable'
}

// =============================================================================
// CORE STRUCTURES
// =============================================================================

/**
 * TIG (Thalamocortical Information Gateway) topology metrics
 */
export interface TIGMetrics {
  nodes_active: number;
  connectivity: number;     // 0.0 to 1.0
  integration: number;      // 0.0 to 1.0
  phi_proxy?: number;       // Optional: simplified IIT measure
}

/**
 * ESGT ignition statistics
 */
export interface ESGTStats {
  total_ignitions: number;
  success_rate: number;     // 0.0 to 1.0
  last_ignition?: string;   // ISO8601 timestamp
  avg_coherence?: number;
  avg_duration_ms?: number;
}

/**
 * Performance metrics
 */
export interface PerformanceMetrics {
  cpu_usage: number;        // 0.0 to 1.0
  memory_mb: number;
  events_per_second: number;
}

/**
 * Arousal trends
 */
export interface ArousalTrends {
  direction: TrendDirection;
  rate: number;             // Rate of change per minute
}

/**
 * Salience components that trigger ESGT
 */
export interface Salience {
  novelty: number;          // 0.0 to 1.0
  relevance: number;        // 0.0 to 1.0
  urgency: number;          // 0.0 to 1.0
  total: number;            // Sum of above (0.0 to 3.0)
}

/**
 * Complete consciousness state snapshot
 * 
 * Endpoint: GET /api/consciousness/state
 */
export interface ConsciousnessState {
  timestamp: string;                    // ISO8601
  esgt_active: boolean;
  arousal_level: number;                // 0.0 to 1.0
  arousal_classification: ArousalLevel;
  tig_metrics: TIGMetrics;
  esgt_stats?: ESGTStats;
  recent_events_count: number;
  system_health: SystemHealth;
  coherence?: number;                   // 0.0 to 1.0
}

/**
 * ESGT (Emergent Synchronous Global Thalamocortical) ignition event
 * 
 * Endpoint: GET /api/consciousness/esgt/events
 */
export interface ESGTEvent {
  event_id: string;                     // UUID
  timestamp: string;                    // ISO8601
  success: boolean;
  salience: Salience;
  coherence?: number;                   // Only if success=true
  duration_ms?: number;                 // Only if success=true
  nodes_participating: number;
  reason?: ESGTReason;                  // Only if success=false
  context?: Record<string, any>;        // Free-form context
}

/**
 * Current arousal state (MCEA)
 * 
 * Endpoint: GET /api/consciousness/arousal
 */
export interface ArousalState {
  arousal: number;                      // 0.0 to 1.0
  level: ArousalLevel;
  baseline: number;                     // 0.0 to 1.0
  need_contribution: number;            // 0.0 to 1.0
  stress_contribution: number;          // -0.5 to 0.5
  timestamp: string;                    // ISO8601
  trends?: ArousalTrends;
}

/**
 * Aggregated system metrics
 * 
 * Endpoint: GET /api/consciousness/metrics
 */
export interface ConsciousnessMetrics {
  tig_metrics: TIGMetrics;
  esgt_stats: ESGTStats;
  performance?: PerformanceMetrics;
}

// =============================================================================
// REQUEST/RESPONSE TYPES
// =============================================================================

/**
 * Request body for manual ESGT trigger
 * 
 * Endpoint: POST /api/consciousness/esgt/trigger
 */
export interface TriggerESGTRequest {
  novelty: number;          // 0.0 to 1.0
  relevance: number;        // 0.0 to 1.0
  urgency: number;          // 0.0 to 1.0
  context?: Record<string, any>;
}

/**
 * Response from ESGT trigger
 */
export interface TriggerESGTResponse {
  success: boolean;
  event?: ESGTEvent;
  error?: string;
}

/**
 * Request body for arousal adjustment
 * 
 * Endpoint: POST /api/consciousness/arousal/adjust
 */
export interface AdjustArousalRequest {
  delta: number;            // -0.5 to 0.5
  duration_seconds?: number; // 0.1 to 60.0, default 5.0
  source?: string;          // Default "manual"
}

/**
 * Response from arousal adjustment
 */
export interface AdjustArousalResponse {
  success: boolean;
  new_arousal?: number;
  error?: string;
}

// =============================================================================
// WEBSOCKET STREAMING TYPES
// =============================================================================

/**
 * WebSocket message types
 */
export enum WSMessageType {
  AROUSAL_UPDATE = 'arousal_update',
  ESGT_EVENT = 'esgt_event',
  STATE_SNAPSHOT = 'state_snapshot'
}

/**
 * WebSocket message wrapper
 */
export interface WSMessage<T = any> {
  type: WSMessageType;
  data: T;
}

/**
 * Type guards for WebSocket messages
 */
export function isArousalUpdate(msg: WSMessage): msg is WSMessage<ArousalState> {
  return msg.type === WSMessageType.AROUSAL_UPDATE;
}

export function isESGTEvent(msg: WSMessage): msg is WSMessage<ESGTEvent> {
  return msg.type === WSMessageType.ESGT_EVENT;
}

export function isStateSnapshot(msg: WSMessage): msg is WSMessage<ConsciousnessState> {
  return msg.type === WSMessageType.STATE_SNAPSHOT;
}

// =============================================================================
// VALIDATION HELPERS
// =============================================================================

/**
 * Validate arousal range
 */
export function validateArousal(arousal: number): boolean {
  return arousal >= 0.0 && arousal <= 1.0;
}

/**
 * Validate salience component
 */
export function validateSalienceComponent(value: number): boolean {
  return value >= 0.0 && value <= 1.0;
}

/**
 * Validate delta for arousal adjustment
 */
export function validateArousalDelta(delta: number): boolean {
  return delta >= -0.5 && delta <= 0.5;
}

/**
 * Validate duration
 */
export function validateDuration(duration: number): boolean {
  return duration >= 0.1 && duration <= 60.0;
}

/**
 * Get arousal classification from level
 */
export function getArousalClassification(arousal: number): ArousalLevel {
  if (arousal < 0.1) return ArousalLevel.ASLEEP;
  if (arousal < 0.3) return ArousalLevel.DROWSY;
  if (arousal < 0.6) return ArousalLevel.AWAKE;
  if (arousal < 0.8) return ArousalLevel.ALERT;
  return ArousalLevel.HYPERAROUSED;
}

// =============================================================================
// FORMATTING HELPERS
// =============================================================================

/**
 * Format arousal level as human-readable string
 */
export function formatArousalLevel(level: ArousalLevel): string {
  const labels: Record<ArousalLevel, string> = {
    [ArousalLevel.ASLEEP]: 'Asleep',
    [ArousalLevel.DROWSY]: 'Drowsy',
    [ArousalLevel.AWAKE]: 'Awake',
    [ArousalLevel.ALERT]: 'Alert',
    [ArousalLevel.HYPERAROUSED]: 'Hyperaroused'
  };
  return labels[level];
}

/**
 * Format event timestamp
 */
export function formatEventTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  } catch {
    return timestamp;
  }
}

/**
 * Format duration in ms to human-readable
 */
export function formatDuration(durationMs: number): string {
  if (durationMs < 1000) {
    return `${durationMs.toFixed(1)}ms`;
  }
  return `${(durationMs / 1000).toFixed(2)}s`;
}

// =============================================================================
// CONSTANTS
// =============================================================================

export const PROTOCOL_VERSION = '1.0.0';
export const DEFAULT_BASE_URL = 'http://localhost:8001';
export const DEFAULT_WS_URL = 'ws://localhost:8001/ws/consciousness';

// =============================================================================
// METADATA
// =============================================================================

export const PROTOCOL_METADATA = {
  version: PROTOCOL_VERSION,
  author: 'Juan Carlo de Souza (JuanCS-DEV @github)',
  email: 'juan.brainfarma@gmail.com',
  created: '2024-10-08',
  status: 'production-ready'
} as const;

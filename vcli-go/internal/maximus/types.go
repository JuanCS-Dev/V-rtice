// Cockpit Shared Protocol Types - Go
// ===================================
//
// Auto-generated from cockpit-shared-protocol.yaml v1.0.0
//
// Autor: Juan Carlo de Souza (JuanCS-DEV @github)
// Email: juan.brainfarma@gmail.com
// Data: 2024-10-08
//
// Conforme Doutrina Vértice - Artigo II: NO MOCK, NO PLACEHOLDER

package maximus

import (
	"fmt"
	"time"
)

// =============================================================================
// CONSTANTS
// =============================================================================

const (
	// ProtocolVersion is the version of the shared protocol
	ProtocolVersion = "1.0.0"

	// DefaultBaseURL is the default MAXIMUS API base URL
	DefaultBaseURL = "http://localhost:8001"

	// DefaultWSURL is the default WebSocket URL
	DefaultWSURL = "ws://localhost:8001/ws/consciousness"
)

// =============================================================================
// ENUMS
// =============================================================================

// ArousalLevel classifies arousal level (MCEA - Modular Conscious Excitability Architecture)
type ArousalLevel string

const (
	// ArousalAsleep represents arousal < 0.1
	ArousalAsleep ArousalLevel = "asleep"

	// ArousalDrowsy represents 0.1 <= arousal < 0.3
	ArousalDrowsy ArousalLevel = "drowsy"

	// ArousalAwake represents 0.3 <= arousal < 0.6
	ArousalAwake ArousalLevel = "awake"

	// ArousalAlert represents 0.6 <= arousal < 0.8
	ArousalAlert ArousalLevel = "alert"

	// ArousalHyperaroused represents arousal >= 0.8
	ArousalHyperaroused ArousalLevel = "hyperaroused"
)

// String returns human-readable arousal level
func (a ArousalLevel) String() string {
	switch a {
	case ArousalAsleep:
		return "Asleep"
	case ArousalDrowsy:
		return "Drowsy"
	case ArousalAwake:
		return "Awake"
	case ArousalAlert:
		return "Alert"
	case ArousalHyperaroused:
		return "Hyperaroused"
	default:
		return string(a)
	}
}

// SystemHealth represents overall health status of consciousness system
type SystemHealth string

const (
	// HealthHealthy represents healthy system
	HealthHealthy SystemHealth = "healthy"

	// HealthDegraded represents degraded performance
	HealthDegraded SystemHealth = "degraded"

	// HealthCritical represents critical state
	HealthCritical SystemHealth = "critical"

	// HealthUnknown represents unknown state
	HealthUnknown SystemHealth = "unknown"
)

// ESGTReason represents reason for ESGT ignition failure
type ESGTReason string

const (
	// ESGTReasonLowSalience means total salience below threshold
	ESGTReasonLowSalience ESGTReason = "low_salience"

	// ESGTReasonSuppressed means actively suppressed by control
	ESGTReasonSuppressed ESGTReason = "suppressed"

	// ESGTReasonInsufficientPhi means Phi below minimum
	ESGTReasonInsufficientPhi ESGTReason = "insufficient_phi"

	// ESGTReasonTimeout means processing timeout
	ESGTReasonTimeout ESGTReason = "timeout"

	// ESGTReasonNull represents success case
	ESGTReasonNull ESGTReason = "null"
)

// TrendDirection represents trend direction for metrics
type TrendDirection string

const (
	// TrendIncreasing represents increasing trend
	TrendIncreasing TrendDirection = "increasing"

	// TrendDecreasing represents decreasing trend
	TrendDecreasing TrendDirection = "decreasing"

	// TrendStable represents stable trend
	TrendStable TrendDirection = "stable"
)

// =============================================================================
// CORE STRUCTURES
// =============================================================================

// TIGMetrics represents TIG (Thalamocortical Information Gateway) topology metrics
type TIGMetrics struct {
	NodesActive  int     `json:"nodes_active"`
	Connectivity float64 `json:"connectivity"` // 0.0 to 1.0
	Integration  float64 `json:"integration"`  // 0.0 to 1.0
	PhiProxy     float64 `json:"phi_proxy,omitempty"`
}

// ESGTStats represents ESGT ignition statistics
type ESGTStats struct {
	TotalIgnitions int     `json:"total_ignitions"`
	SuccessRate    float64 `json:"success_rate"` // 0.0 to 1.0
	LastIgnition   string  `json:"last_ignition,omitempty"`
	AvgCoherence   float64 `json:"avg_coherence,omitempty"`
	AvgDurationMs  float64 `json:"avg_duration_ms,omitempty"`
}

// PerformanceMetrics represents performance metrics
type PerformanceMetrics struct {
	CPUUsage         float64 `json:"cpu_usage"`           // 0.0 to 1.0
	MemoryMB         float64 `json:"memory_mb"`
	EventsPerSecond  float64 `json:"events_per_second"`
}

// ArousalTrends represents arousal trends
type ArousalTrends struct {
	Direction TrendDirection `json:"direction"`
	Rate      float64        `json:"rate"` // Rate of change per minute
}

// Salience represents salience components that trigger ESGT
type Salience struct {
	Novelty   float64 `json:"novelty"`   // 0.0 to 1.0
	Relevance float64 `json:"relevance"` // 0.0 to 1.0
	Urgency   float64 `json:"urgency"`   // 0.0 to 1.0
	Total     float64 `json:"total"`     // Sum of above (0.0 to 3.0)
}

// ConsciousnessState represents complete consciousness state snapshot
//
// Endpoint: GET /api/consciousness/state
type ConsciousnessState struct {
	Timestamp              string        `json:"timestamp"` // ISO8601
	ESGTActive             bool          `json:"esgt_active"`
	ArousalLevel           float64       `json:"arousal_level"` // 0.0 to 1.0
	ArousalClassification  ArousalLevel  `json:"arousal_classification"`
	TIGMetrics             TIGMetrics    `json:"tig_metrics"`
	ESGTStats              *ESGTStats    `json:"esgt_stats,omitempty"`
	RecentEventsCount      int           `json:"recent_events_count"`
	SystemHealth           SystemHealth  `json:"system_health"`
	Coherence              float64       `json:"coherence,omitempty"` // 0.0 to 1.0
}

// ESGTEvent represents ESGT (Emergent Synchronous Global Thalamocortical) ignition event
//
// Endpoint: GET /api/consciousness/esgt/events
type ESGTEvent struct {
	EventID             string                 `json:"event_id"`   // UUID
	Timestamp           string                 `json:"timestamp"`  // ISO8601
	Success             bool                   `json:"success"`
	Salience            Salience               `json:"salience"`
	Coherence           float64                `json:"coherence,omitempty"`         // Only if success=true
	DurationMs          float64                `json:"duration_ms,omitempty"`       // Only if success=true
	NodesParticipating  int                    `json:"nodes_participating"`
	Reason              ESGTReason             `json:"reason,omitempty"`            // Only if success=false
	Context             map[string]interface{} `json:"context,omitempty"`
}

// ArousalState represents current arousal state (MCEA)
//
// Endpoint: GET /api/consciousness/arousal
type ArousalState struct {
	Arousal            float64        `json:"arousal"`  // 0.0 to 1.0
	Level              ArousalLevel   `json:"level"`
	Baseline           float64        `json:"baseline"` // 0.0 to 1.0
	NeedContribution   float64        `json:"need_contribution"` // 0.0 to 1.0
	StressContribution float64        `json:"stress_contribution"` // -0.5 to 0.5
	Timestamp          string         `json:"timestamp"` // ISO8601
	Trends             *ArousalTrends `json:"trends,omitempty"`
}

// ConsciousnessMetrics represents aggregated system metrics
//
// Endpoint: GET /api/consciousness/metrics
type ConsciousnessMetrics struct {
	TIGMetrics  TIGMetrics          `json:"tig_metrics"`
	ESGTStats   ESGTStats           `json:"esgt_stats"`
	Performance *PerformanceMetrics `json:"performance,omitempty"`
}

// =============================================================================
// REQUEST/RESPONSE TYPES
// =============================================================================

// TriggerESGTRequest represents request body for manual ESGT trigger
//
// Endpoint: POST /api/consciousness/esgt/trigger
type TriggerESGTRequest struct {
	Novelty   float64                `json:"novelty"`   // 0.0 to 1.0
	Relevance float64                `json:"relevance"` // 0.0 to 1.0
	Urgency   float64                `json:"urgency"`   // 0.0 to 1.0
	Context   map[string]interface{} `json:"context,omitempty"`
}

// TriggerESGTResponse represents response from ESGT trigger
type TriggerESGTResponse struct {
	Success bool       `json:"success"`
	Event   *ESGTEvent `json:"event,omitempty"`
	Error   string     `json:"error,omitempty"`
}

// AdjustArousalRequest represents request body for arousal adjustment
//
// Endpoint: POST /api/consciousness/arousal/adjust
type AdjustArousalRequest struct {
	Delta           float64 `json:"delta"`                      // -0.5 to 0.5
	DurationSeconds float64 `json:"duration_seconds,omitempty"` // 0.1 to 60.0, default 5.0
	Source          string  `json:"source,omitempty"`           // Default "manual"
}

// AdjustArousalResponse represents response from arousal adjustment
type AdjustArousalResponse struct {
	Success    bool    `json:"success"`
	NewArousal float64 `json:"new_arousal,omitempty"`
	Error      string  `json:"error,omitempty"`
}

// =============================================================================
// WEBSOCKET STREAMING TYPES
// =============================================================================

// WSMessageType represents WebSocket message types
type WSMessageType string

const (
	// WSMessageArousalUpdate represents arousal update message
	WSMessageArousalUpdate WSMessageType = "arousal_update"

	// WSMessageESGTEvent represents ESGT event message
	WSMessageESGTEvent WSMessageType = "esgt_event"

	// WSMessageStateSnapshot represents state snapshot message
	WSMessageStateSnapshot WSMessageType = "state_snapshot"
)

// WSMessage represents WebSocket message wrapper
type WSMessage struct {
	Type WSMessageType `json:"type"`
	Data interface{}   `json:"data"`
}

// =============================================================================
// VALIDATION HELPERS
// =============================================================================

// ValidateArousal validates arousal range
func ValidateArousal(arousal float64) error {
	if arousal < 0.0 || arousal > 1.0 {
		return fmt.Errorf("arousal must be between 0.0 and 1.0, got %.2f", arousal)
	}
	return nil
}

// ValidateSalienceComponent validates salience component
func ValidateSalienceComponent(value float64, name string) error {
	if value < 0.0 || value > 1.0 {
		return fmt.Errorf("%s must be between 0.0 and 1.0, got %.2f", name, value)
	}
	return nil
}

// ValidateArousalDelta validates delta for arousal adjustment
func ValidateArousalDelta(delta float64) error {
	if delta < -0.5 || delta > 0.5 {
		return fmt.Errorf("arousal delta must be between -0.5 and 0.5, got %.2f", delta)
	}
	return nil
}

// ValidateDuration validates duration
func ValidateDuration(duration float64) error {
	if duration < 0.1 || duration > 60.0 {
		return fmt.Errorf("duration must be between 0.1 and 60.0 seconds, got %.2f", duration)
	}
	return nil
}

// GetArousalClassification gets arousal classification from level
func GetArousalClassification(arousal float64) ArousalLevel {
	switch {
	case arousal < 0.1:
		return ArousalAsleep
	case arousal < 0.3:
		return ArousalDrowsy
	case arousal < 0.6:
		return ArousalAwake
	case arousal < 0.8:
		return ArousalAlert
	default:
		return ArousalHyperaroused
	}
}

// =============================================================================
// FORMATTING HELPERS
// =============================================================================

// FormatEventTime formats event timestamp
func FormatEventTime(timestamp string) string {
	t, err := time.Parse(time.RFC3339Nano, timestamp)
	if err != nil {
		return timestamp
	}
	return t.Format("15:04:05.000")
}

// FormatDuration formats duration in ms to human-readable
func FormatDuration(durationMs float64) string {
	if durationMs < 1000 {
		return fmt.Sprintf("%.1fms", durationMs)
	}
	return fmt.Sprintf("%.2fs", durationMs/1000)
}

// FormatPercentage formats a 0-1 value as percentage
func FormatPercentage(value float64) string {
	return fmt.Sprintf("%.1f%%", value*100)
}

// =============================================================================
// TYPE ASSERTIONS FOR WEBSOCKET
// =============================================================================

// AsArousalState attempts to convert WSMessage data to ArousalState
func (msg *WSMessage) AsArousalState() (*ArousalState, bool) {
	if msg.Type != WSMessageArousalUpdate {
		return nil, false
	}
	state, ok := msg.Data.(*ArousalState)
	return state, ok
}

// AsESGTEvent attempts to convert WSMessage data to ESGTEvent
func (msg *WSMessage) AsESGTEvent() (*ESGTEvent, bool) {
	if msg.Type != WSMessageESGTEvent {
		return nil, false
	}
	event, ok := msg.Data.(*ESGTEvent)
	return event, ok
}

// AsConsciousnessState attempts to convert WSMessage data to ConsciousnessState
func (msg *WSMessage) AsConsciousnessState() (*ConsciousnessState, bool) {
	if msg.Type != WSMessageStateSnapshot {
		return nil, false
	}
	state, ok := msg.Data.(*ConsciousnessState)
	return state, ok
}

// =============================================================================
// METADATA
// =============================================================================

// ProtocolMetadata contains protocol metadata
var ProtocolMetadata = struct {
	Version string
	Author  string
	GitHub  string
	Email   string
	Created string
	Status  string
}{
	Version: ProtocolVersion,
	Author:  "Juan Carlo de Souza",
	GitHub:  "JuanCS-DEV",
	Email:   "juan.brainfarma@gmail.com",
	Created: "2024-10-08",
	Status:  "production-ready",
}

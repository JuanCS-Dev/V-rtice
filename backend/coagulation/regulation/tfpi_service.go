package regulation

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// TFPIService implements Tissue Factor Pathway Inhibitor functionality.
//
// Biological Analogy: TFPI is the "gatekeeper" that prevents runaway
// cascade initiation by requiring strong signals before allowing full
// activation. It binds to Factor Xa and Factor VIIa/TF complex.
//
// Digital Function: Validates triggers before allowing cascade activation.
// For low-confidence signals, requires CORROBORATION from multiple sources.
//
// Critical Role: Prevents cascade activation from noise/false positives.
type TFPIService struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client

	// Signal correlation tracking
	pendingTriggers  map[string]*PendingTrigger
	correlatedGroups map[string]*CorrelatedSignalGroup
	mu               sync.RWMutex

	// Configuration
	confidenceThreshold float64       // Minimum confidence for instant pass
	correlationWindow   time.Duration // Time window for signal correlation
	minCorrelatedSignals int          // Minimum correlated signals required

	ctx        context.Context
	cancelFunc context.CancelFunc
}

// PendingTrigger represents trigger awaiting correlation.
type PendingTrigger struct {
	ID          string
	Type        string // "extrinsic", "intrinsic"
	Source      string
	Confidence  float64
	Signal      *DetectionSignal
	ReceivedAt  time.Time
	ExpiresAt   time.Time
	Validated   bool
}

// DetectionSignal represents detection event.
type DetectionSignal struct {
	Type        string // "ioc", "anomaly", "behavioral"
	Value       string
	Severity    string
	Attributes  map[string]interface{}
	Timestamp   time.Time
}

// CorrelatedSignalGroup represents multiple signals pointing to same threat.
type CorrelatedSignalGroup struct {
	ID          string
	Signals     []*PendingTrigger
	CreatedAt   time.Time
	Confidence  float64 // Aggregate confidence
	Validated   bool
}

// ValidationResult represents TFPI validation outcome.
type ValidationResult struct {
	TriggerID    string
	Validated    bool
	Reason       string
	Confidence   float64
	Correlated   int
	Timestamp    time.Time
}

// NewTFPIService creates trigger validation service.
func NewTFPIService(
	logger *logger.Logger,
	metrics *metrics.Collector,
	eventBus *eventbus.Client,
) *TFPIService {
	ctx, cancel := context.WithCancel(context.Background())

	return &TFPIService{
		logger:   logger,
		metrics:  metrics,
		eventBus: eventBus,

		pendingTriggers:  make(map[string]*PendingTrigger),
		correlatedGroups: make(map[string]*CorrelatedSignalGroup),

		confidenceThreshold:  0.7,  // 70% confidence instant pass
		correlationWindow:    30 * time.Second,
		minCorrelatedSignals: 3,    // Need 3+ correlated signals

		ctx:        ctx,
		cancelFunc: cancel,
	}
}

// Start begins trigger validation.
func (t *TFPIService) Start() error {
	t.logger.Info("Starting TFPI Service (Trigger Validation)")

	// Subscribe to detection triggers
	if err := t.eventBus.Subscribe("detection.trigger", t.handleTrigger); err != nil {
		return fmt.Errorf("failed to subscribe to triggers: %w", err)
	}

	// Start cleanup loop for expired triggers
	go t.cleanupLoop()

	t.logger.Info("TFPI Service active - validating cascade triggers")
	return nil
}

// Stop gracefully stops the service.
func (t *TFPIService) Stop() error {
	t.logger.Info("Stopping TFPI Service")
	t.cancelFunc()
	return nil
}

// ValidateTrigger determines if trigger should activate cascade.
//
// CRITICAL DECISION: This method prevents cascade activation from weak
// signals. High-confidence triggers pass immediately; low-confidence
// triggers require corroboration.
func (t *TFPIService) ValidateTrigger(trigger *PendingTrigger) *ValidationResult {
	result := &ValidationResult{
		TriggerID:  trigger.ID,
		Confidence: trigger.Confidence,
		Timestamp:  time.Now(),
	}

	// High confidence - INSTANT PASS
	if trigger.Confidence >= t.confidenceThreshold {
		result.Validated = true
		result.Reason = fmt.Sprintf(
			"High confidence trigger (%.2f >= %.2f) - instant validation",
			trigger.Confidence,
			t.confidenceThreshold,
		)
		
		t.logger.Info("Trigger validated - high confidence",
			"trigger_id", trigger.ID,
			"confidence", trigger.Confidence,
		)

		// Metrics
		t.metrics.IncrementCounter("tfpi_validations_total", map[string]string{
			"type":   trigger.Type,
			"result": "instant_pass",
		})

		return result
	}

	// Low confidence - REQUIRE CORROBORATION
	correlatedSignals := t.FindCorrelatedSignals(trigger)
	result.Correlated = len(correlatedSignals)

	if len(correlatedSignals) >= t.minCorrelatedSignals {
		// Sufficient corroboration
		result.Validated = true
		result.Reason = fmt.Sprintf(
			"Low confidence trigger (%.2f) CORROBORATED by %d signals",
			trigger.Confidence,
			len(correlatedSignals),
		)
		
		t.logger.Info("Trigger validated - corroborated",
			"trigger_id", trigger.ID,
			"confidence", trigger.Confidence,
			"correlated_signals", len(correlatedSignals),
		)

		// Metrics
		t.metrics.IncrementCounter("tfpi_validations_total", map[string]string{
			"type":   trigger.Type,
			"result": "corroborated",
		})

	} else {
		// Insufficient corroboration - REJECT
		result.Validated = false
		result.Reason = fmt.Sprintf(
			"Low confidence trigger (%.2f) lacks corroboration (%d/%d signals)",
			trigger.Confidence,
			len(correlatedSignals),
			t.minCorrelatedSignals,
		)
		
		t.logger.Debug("Trigger rejected - insufficient corroboration",
			"trigger_id", trigger.ID,
			"confidence", trigger.Confidence,
			"correlated_signals", len(correlatedSignals),
			"required", t.minCorrelatedSignals,
		)

		// Metrics
		t.metrics.IncrementCounter("tfpi_rejections_total", map[string]string{
			"type":   trigger.Type,
			"reason": "insufficient_corroboration",
		})

		// Store for potential future correlation
		t.storePendingTrigger(trigger)
	}

	return result
}

// FindCorrelatedSignals searches for related signals in time window.
func (t *TFPIService) FindCorrelatedSignals(trigger *PendingTrigger) []*PendingTrigger {
	t.mu.RLock()
	defer t.mu.RUnlock()

	correlated := []*PendingTrigger{}
	now := time.Now()

	for _, pending := range t.pendingTriggers {
		// Skip self
		if pending.ID == trigger.ID {
			continue
		}

		// Check time window
		if now.Sub(pending.ReceivedAt) > t.correlationWindow {
			continue
		}

		// Check correlation criteria
		if t.areSignalsCorrelated(trigger, pending) {
			correlated = append(correlated, pending)
		}
	}

	return correlated
}

// areSignalsCorrelated determines if two signals are related.
func (t *TFPIService) areSignalsCorrelated(s1, s2 *PendingTrigger) bool {
	// Multiple correlation dimensions
	
	// 1. Same source asset
	if s1.Source == s2.Source {
		return true
	}

	// 2. Similar signal attributes
	if t.signalsHaveSimilarAttributes(s1.Signal, s2.Signal) {
		return true
	}

	// 3. Same threat type
	if s1.Signal.Type == s2.Signal.Type {
		return true
	}

	return false
}

// signalsHaveSimilarAttributes checks attribute similarity.
func (t *TFPIService) signalsHaveSimilarAttributes(sig1, sig2 *DetectionSignal) bool {
	// TODO: Implement sophisticated similarity check
	// For now, simple type matching
	return sig1.Type == sig2.Type
}

// storePendingTrigger adds trigger to pending pool.
func (t *TFPIService) storePendingTrigger(trigger *PendingTrigger) {
	t.mu.Lock()
	defer t.mu.Unlock()

	trigger.ExpiresAt = time.Now().Add(t.correlationWindow)
	t.pendingTriggers[trigger.ID] = trigger

	t.logger.Debug("Stored pending trigger for correlation",
		"trigger_id", trigger.ID,
		"expires_at", trigger.ExpiresAt,
	)
}

// handleTrigger processes incoming detection trigger.
func (t *TFPIService) handleTrigger(event map[string]interface{}) {
	trigger := &PendingTrigger{
		ID:         event["id"].(string),
		Type:       event["type"].(string),
		Source:     extractString(event, "source"),
		Confidence: extractFloat(event, "confidence"),
		Signal: &DetectionSignal{
			Type:      extractString(event, "signal_type"),
			Value:     extractString(event, "value"),
			Severity:  extractString(event, "severity"),
			Timestamp: time.Now(),
		},
		ReceivedAt: time.Now(),
	}

	// Validate trigger
	result := t.ValidateTrigger(trigger)

	// Publish validation result
	t.eventBus.Publish("tfpi.validation_result", map[string]interface{}{
		"result":     result,
		"trigger_id": trigger.ID,
		"validated":  result.Validated,
	})

	// If validated, forward to cascade
	if result.Validated {
		t.eventBus.Publish("cascade.activate", map[string]interface{}{
			"trigger":    trigger,
			"validation": result,
		})
	}
}

// cleanupLoop removes expired pending triggers.
func (t *TFPIService) cleanupLoop() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			t.cleanupExpiredTriggers()
		case <-t.ctx.Done():
			return
		}
	}
}

// cleanupExpiredTriggers removes old pending triggers.
func (t *TFPIService) cleanupExpiredTriggers() {
	t.mu.Lock()
	defer t.mu.Unlock()

	now := time.Now()
	expired := []string{}

	for id, trigger := range t.pendingTriggers {
		if now.After(trigger.ExpiresAt) {
			expired = append(expired, id)
		}
	}

	for _, id := range expired {
		delete(t.pendingTriggers, id)
	}

	if len(expired) > 0 {
		t.logger.Debug("Cleaned up expired pending triggers", "count", len(expired))
	}
}

// GetPendingCount returns number of pending triggers.
func (t *TFPIService) GetPendingCount() int {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return len(t.pendingTriggers)
}

// extractString safely extracts string from event map.
func extractString(event map[string]interface{}, key string) string {
	if val, ok := event[key]; ok {
		if strVal, ok := val.(string); ok {
			return strVal
		}
	}
	return ""
}

// extractFloat safely extracts float64 from event map.
func extractFloat(event map[string]interface{}, key string) float64 {
	if val, ok := event[key]; ok {
		if floatVal, ok := val.(float64); ok {
			return floatVal
		}
	}
	return 0.0
}

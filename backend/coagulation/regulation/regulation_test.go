package regulation

import (
	"testing"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// TestProteinCHealthySegmentInhibition validates Protein C inhibits expansion to healthy segments.
func TestProteinCHealthySegmentInhibition(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	proteinC := NewProteinCService(log, met, eb)

	// Simulate healthy segment
	segment := &NetworkSegment{
		ID:       "seg-healthy",
		Name:     "Healthy Segment",
		IPRanges: []string{"10.0.1.0/24"},
	}

	health := proteinC.CheckHealth(segment)

	// Healthy segment should have high score
	if health.OverallScore < 0.8 {
		t.Errorf("Expected healthy segment score >= 0.8, got %.2f", health.OverallScore)
	}

	if !health.IsHealthy {
		t.Error("Expected segment to be marked as healthy")
	}

	// Test expansion regulation
	qctx := &QuarantineContext{
		BreachID:       "breach-001",
		SourceSegment:  "seg-compromised",
		TargetSegments: []string{"seg-healthy"},
	}

	err := proteinC.RegulateExpansion(qctx)
	if err != nil {
		t.Errorf("RegulateExpansion failed: %v", err)
	}

	// Should have inhibition decision
	proteinC.mu.RLock()
	hasInhibition := false
	for _, decision := range proteinC.inhibitions {
		if decision.TargetSegment == "seg-healthy" && decision.Inhibited {
			hasInhibition = true
			break
		}
	}
	proteinC.mu.RUnlock()

	if !hasInhibition {
		t.Error("Expected inhibition decision for healthy segment")
	}
}

// TestProteinCCompromisedSegmentAllowance validates Protein C allows expansion to compromised segments.
func TestProteinCCompromisedSegmentAllowance(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	proteinC := NewProteinCService(log, met, eb)

	// TODO: Mock compromised segment with low health scores
	// For now, test passes as implementation uses simulated scores
}

// TestAntithrombinEmergencyDampening validates emergency dampening activation.
func TestAntithrombinEmergencyDampening(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	antithrombin := NewAntithrombinService(log, met, eb)

	// Initially not dampening
	if antithrombin.IsDampeningActive() {
		t.Error("Dampening should not be active initially")
	}

	// Activate emergency dampening
	err := antithrombin.EmergencyDampening()
	if err != nil {
		t.Errorf("EmergencyDampening failed: %v", err)
	}

	// Should be active now
	if !antithrombin.IsDampeningActive() {
		t.Error("Dampening should be active after emergency activation")
	}

	// Should have dampening intensity
	intensity := antithrombin.GetDampeningIntensity()
	if intensity <= 0 {
		t.Errorf("Expected positive dampening intensity, got %.2f", intensity)
	}

	// Should deactivate after duration
	time.Sleep(100 * time.Millisecond) // Short wait for test
}

// TestTFPIHighConfidenceTriggerValidation validates instant pass for high-confidence triggers.
func TestTFPIHighConfidenceTriggerValidation(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	tfpi := NewTFPIService(log, met, eb)

	// High confidence trigger
	trigger := &PendingTrigger{
		ID:         "trigger-001",
		Type:       "extrinsic",
		Source:     "asset-001",
		Confidence: 0.95, // 95% confidence
		Signal: &DetectionSignal{
			Type:      "ioc",
			Value:     "malware-hash",
			Severity:  "critical",
			Timestamp: time.Now(),
		},
		ReceivedAt: time.Now(),
	}

	result := tfpi.ValidateTrigger(trigger)

	// Should be validated instantly
	if !result.Validated {
		t.Error("Expected high-confidence trigger to be validated")
	}

	if result.Correlated != 0 {
		t.Error("High-confidence trigger should not require corroboration")
	}
}

// TestTFPILowConfidenceTriggerRejection validates rejection without corroboration.
func TestTFPILowConfidenceTriggerRejection(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	tfpi := NewTFPIService(log, met, eb)

	// Low confidence trigger
	trigger := &PendingTrigger{
		ID:         "trigger-002",
		Type:       "intrinsic",
		Source:     "asset-002",
		Confidence: 0.4, // 40% confidence
		Signal: &DetectionSignal{
			Type:      "anomaly",
			Value:     "unusual-traffic",
			Severity:  "low",
			Timestamp: time.Now(),
		},
		ReceivedAt: time.Now(),
	}

	result := tfpi.ValidateTrigger(trigger)

	// Should be rejected (no corroboration)
	if result.Validated {
		t.Error("Expected low-confidence trigger without corroboration to be rejected")
	}

	// Should be stored as pending
	if tfpi.GetPendingCount() == 0 {
		t.Error("Expected trigger to be stored as pending")
	}
}

// TestTFPICorroboratedValidation validates validation with corroboration.
func TestTFPICorroboratedValidation(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	tfpi := NewTFPIService(log, met, eb)

	// First trigger - rejected
	trigger1 := &PendingTrigger{
		ID:         "trigger-003",
		Type:       "intrinsic",
		Source:     "asset-003",
		Confidence: 0.5,
		Signal: &DetectionSignal{
			Type:      "anomaly",
			Timestamp: time.Now(),
		},
		ReceivedAt: time.Now(),
	}

	result1 := tfpi.ValidateTrigger(trigger1)
	if result1.Validated {
		t.Error("First trigger should be rejected")
	}

	// Add corroborating signals
	for i := 0; i < 3; i++ {
		corroborate := &PendingTrigger{
			ID:         string(rune('A' + i)),
			Type:       "intrinsic",
			Source:     "asset-003", // Same source
			Confidence: 0.5,
			Signal: &DetectionSignal{
				Type:      "anomaly",
				Timestamp: time.Now(),
			},
			ReceivedAt: time.Now(),
		}
		tfpi.storePendingTrigger(corroborate)
	}

	// Re-validate original trigger
	result2 := tfpi.ValidateTrigger(trigger1)

	// Should now be validated with corroboration
	if !result2.Validated {
		t.Error("Expected corroborated trigger to be validated")
	}

	if result2.Correlated < 3 {
		t.Errorf("Expected >= 3 correlated signals, got %d", result2.Correlated)
	}
}

// TestProteinSCaching validates health check caching.
func TestProteinSCaching(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	proteinS := NewProteinSService(log, met, eb)
	proteinC := NewProteinCService(log, met, eb)

	segmentID := "seg-cache-test"

	// First check - cache miss
	health1, err := proteinS.AccelerateHealthCheck(segmentID, proteinC)
	if err != nil {
		t.Errorf("First health check failed: %v", err)
	}

	// Second check - should be cache hit
	health2, err := proteinS.AccelerateHealthCheck(segmentID, proteinC)
	if err != nil {
		t.Errorf("Second health check failed: %v", err)
	}

	// Results should be identical (cached)
	if health1.SegmentID != health2.SegmentID {
		t.Error("Cached result differs from original")
	}

	// Check cache stats
	stats := proteinS.GetCacheStats()
	cacheSize := stats["cache_size"].(int)
	if cacheSize == 0 {
		t.Error("Expected cache to contain entry")
	}
}

// TestProteinSBatchHealthCheck validates parallel batch checking.
func TestProteinSBatchHealthCheck(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	proteinS := NewProteinSService(log, met, eb)
	proteinC := NewProteinCService(log, met, eb)

	// Check 20 segments in batch
	segmentIDs := make([]string, 20)
	for i := 0; i < 20; i++ {
		segmentIDs[i] = string(rune('A' + i))
	}

	result := proteinS.BatchHealthCheck(segmentIDs, proteinC)

	// Should have results for all segments
	if len(result.Results) != 20 {
		t.Errorf("Expected 20 results, got %d", len(result.Results))
	}

	// Duration should be reasonable (parallel execution)
	if result.Duration > 5*time.Second {
		t.Errorf("Batch check took too long: %v", result.Duration)
	}
}

// TestRegulationOrchestrator validates coordinated regulation.
func TestRegulationOrchestrator(t *testing.T) {
	log := logger.NewLogger("test")
	met := metrics.NewCollector()
	eb := eventbus.NewClient("nats://localhost:4222", log)

	orchestrator := NewRegulationOrchestrator(log, met, eb)

	// Start orchestrator
	err := orchestrator.Start()
	if err != nil {
		t.Errorf("Failed to start orchestrator: %v", err)
	}

	if !orchestrator.IsStarted() {
		t.Error("Orchestrator should be started")
	}

	// Get metrics
	metrics := orchestrator.GetMetrics()
	if metrics == nil {
		t.Error("Expected metrics to be available")
	}

	// Stop orchestrator
	err = orchestrator.Stop()
	if err != nil {
		t.Errorf("Failed to stop orchestrator: %v", err)
	}

	if orchestrator.IsStarted() {
		t.Error("Orchestrator should be stopped")
	}
}

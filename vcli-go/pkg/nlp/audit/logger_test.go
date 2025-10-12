package audit

import (
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewAuditLogger(t *testing.T) {
logger := NewAuditLogger(nil)
assert.NotNil(t, logger)
assert.NotNil(t, logger.config)
assert.Equal(t, "genesis", logger.chain)
}

func TestLogEvent(t *testing.T) {
logger := NewAuditLogger(nil)

event := &AuditEvent{
UserID:   "user1",
Action:   "get",
Resource: "pods",
Success:  true,
}

err := logger.LogEvent(event)
require.NoError(t, err)
assert.Equal(t, 1, logger.GetEventCount())
}

func TestLogAction(t *testing.T) {
logger := NewAuditLogger(nil)

err := logger.LogAction("user1", "delete", "pod", "mypod", true)
require.NoError(t, err)

events := logger.GetEvents(nil)
assert.Len(t, events, 1)
assert.Equal(t, "delete", events[0].Action)
assert.Equal(t, "pod", events[0].Resource)
}

func TestTamperProof(t *testing.T) {
logger := NewAuditLogger(nil)

// Log events
logger.LogAction("user1", "get", "pods", "", true)
logger.LogAction("user1", "delete", "pod", "mypod", true)

// Should not detect tamper
tampered := logger.detectTamper()
assert.False(t, tampered)

// Manually tamper with event
logger.events[0].Action = "TAMPERED"

// Should detect tamper
tampered = logger.detectTamper()
assert.True(t, tampered)
}

func TestEventFilter(t *testing.T) {
logger := NewAuditLogger(nil)

logger.LogAction("user1", "get", "pods", "", true)
logger.LogAction("user1", "delete", "pod", "mypod", true)
logger.LogAction("user2", "get", "secrets", "", false)

t.Run("Filter by user", func(t *testing.T) {
filter := &EventFilter{UserID: "user1"}
events := logger.GetEvents(filter)
assert.Len(t, events, 2)
})

t.Run("Filter by action", func(t *testing.T) {
filter := &EventFilter{Action: "delete"}
events := logger.GetEvents(filter)
assert.Len(t, events, 1)
})

t.Run("Filter by success", func(t *testing.T) {
success := false
filter := &EventFilter{Success: &success}
events := logger.GetEvents(filter)
assert.Len(t, events, 1)
})
}

func TestComplianceReport(t *testing.T) {
logger := NewAuditLogger(nil)

// Log various events
logger.LogAction("user1", "get", "pods", "", true)
logger.LogAction("user1", "delete", "pod", "mypod", true)
logger.LogAction("user2", "get", "secrets", "", false)

// Add high risk event
event := &AuditEvent{
UserID:    "user1",
Action:    "delete",
Resource:  "namespace",
Success:   true,
RiskScore: 0.9,
}
logger.LogEvent(event)

period := Period{
Start: time.Now().Add(-1 * time.Hour),
End:   time.Now().Add(1 * time.Hour),
}

report := logger.GenerateComplianceReport(period)

assert.Equal(t, 4, report.TotalEvents)
assert.Equal(t, 3, report.SuccessfulEvents)
assert.Equal(t, 1, report.FailedEvents)
assert.Len(t, report.HighRiskEvents, 1)
assert.NotEmpty(t, report.UserActivity)
}

func TestHashChaining(t *testing.T) {
logger := NewAuditLogger(nil)

logger.LogAction("user1", "get", "pods", "", true)
logger.LogAction("user1", "delete", "pod", "mypod", true)

events := logger.GetEvents(nil)

// First event
assert.Equal(t, "genesis", events[0].PreviousHash)
assert.NotEmpty(t, events[0].EventHash)

// Second event
assert.Equal(t, events[0].EventHash, events[1].PreviousHash)
assert.NotEmpty(t, events[1].EventHash)
}

func TestMaxEvents(t *testing.T) {
config := &AuditConfig{
MaxEvents:   5,
TamperProof: false,
}
logger := NewAuditLogger(config)

// Log more than max
for i := 0; i < 10; i++ {
logger.LogAction("user1", "get", "pods", "", true)
}

assert.Equal(t, 5, logger.GetEventCount())
}

func TestExportJSON(t *testing.T) {
logger := NewAuditLogger(nil)

logger.LogAction("user1", "get", "pods", "", true)
logger.LogAction("user1", "delete", "pod", "mypod", true)

data, err := logger.ExportJSON()
require.NoError(t, err)
assert.NotEmpty(t, data)
assert.Contains(t, string(data), "user1")
}

func TestGetLatestEvents(t *testing.T) {
logger := NewAuditLogger(nil)

for i := 0; i < 10; i++ {
logger.LogAction("user1", "get", "pods", "", true)
}

latest := logger.GetLatestEvents(3)
assert.Len(t, latest, 3)
}

func TestClear(t *testing.T) {
logger := NewAuditLogger(nil)

logger.LogAction("user1", "get", "pods", "", true)
assert.Equal(t, 1, logger.GetEventCount())

logger.Clear()
assert.Equal(t, 0, logger.GetEventCount())
assert.Equal(t, "genesis", logger.chain)
}

func TestEventFilter_Matches(t *testing.T) {
event := &AuditEvent{
UserID:    "user1",
Action:    "delete",
Resource:  "pod",
Success:   true,
RiskScore: 0.8,
Timestamp: time.Now(),
}

t.Run("Match user", func(t *testing.T) {
filter := &EventFilter{UserID: "user1"}
assert.True(t, filter.Matches(event))

filter.UserID = "user2"
assert.False(t, filter.Matches(event))
})

t.Run("Match action", func(t *testing.T) {
filter := &EventFilter{Action: "delete"}
assert.True(t, filter.Matches(event))
})

t.Run("Match risk", func(t *testing.T) {
filter := &EventFilter{MinRisk: 0.7}
assert.True(t, filter.Matches(event))

filter.MinRisk = 0.9
assert.False(t, filter.Matches(event))
})
}

func TestDefaultAuditConfig(t *testing.T) {
config := DefaultAuditConfig()

assert.Equal(t, 10000, config.MaxEvents)
assert.Equal(t, 90, config.RetentionDays)
assert.True(t, config.TamperProof)
assert.True(t, config.ComplianceMode)
}

func TestRecommendations(t *testing.T) {
logger := NewAuditLogger(nil)

// Add high risk events
for i := 0; i < 15; i++ {
event := &AuditEvent{
UserID:    "user1",
Action:    "delete",
Resource:  "namespace",
Success:   true,
RiskScore: 0.9,
Timestamp: time.Now(),
}
logger.LogEvent(event)
}

period := Period{
Start: time.Now().Add(-1 * time.Hour),
End:   time.Now().Add(1 * time.Hour),
}

report := logger.GenerateComplianceReport(period)

assert.NotEmpty(t, report.Recommendations)
}

func TestEventIDGeneration(t *testing.T) {
	logger := NewAuditLogger(nil)

	event := &AuditEvent{
		UserID: "user1",
		Action: "get",
	}

	logger.LogEvent(event)

	events := logger.GetEvents(nil)
	assert.NotEmpty(t, events[0].EventID)
	assert.Contains(t, events[0].EventID, "evt_")
}

func TestLogEventNil(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	err := logger.LogEvent(nil)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "event cannot be nil")
}

func TestLogEventWithTimestamp(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	customTime := time.Now().Add(-1 * time.Hour)
	event := &AuditEvent{
		UserID:    "user1",
		Action:    "get",
		Timestamp: customTime,
	}
	
	logger.LogEvent(event)
	
	events := logger.GetEvents(nil)
	assert.Equal(t, customTime.Unix(), events[0].Timestamp.Unix())
}

func TestLogEventWithEventID(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	event := &AuditEvent{
		UserID:  "user1",
		Action:  "get",
		EventID: "custom-event-id",
	}
	
	logger.LogEvent(event)
	
	events := logger.GetEvents(nil)
	assert.Equal(t, "custom-event-id", events[0].EventID)
}

func TestEventFilterTimeRange(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	now := time.Now()
	
	// Event 1: 2 hours ago
	event1 := &AuditEvent{
		UserID:    "user1",
		Action:    "get",
		Timestamp: now.Add(-2 * time.Hour),
	}
	logger.LogEvent(event1)
	
	// Event 2: 30 minutes ago
	event2 := &AuditEvent{
		UserID:    "user1",
		Action:    "delete",
		Timestamp: now.Add(-30 * time.Minute),
	}
	logger.LogEvent(event2)
	
	// Event 3: now
	event3 := &AuditEvent{
		UserID:    "user1",
		Action:    "create",
		Timestamp: now,
	}
	logger.LogEvent(event3)
	
	// Filter: last hour
	filter := &EventFilter{
		StartTime: now.Add(-1 * time.Hour),
		EndTime:   now.Add(1 * time.Minute),
	}
	
	events := logger.GetEvents(filter)
	assert.Len(t, events, 2) // Should get events 2 and 3
}

func TestComplianceReportWithPolicyViolations(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	// Event with policy violations
	event := &AuditEvent{
		UserID:           "user1",
		Action:           "delete",
		Resource:         "production-db",
		Success:          false,
		PolicyViolations: []string{"production-delete-restriction", "mfa-required"},
		Timestamp:        time.Now(),
	}
	logger.LogEvent(event)
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.NotEmpty(t, report.PolicyViolations)
	assert.Contains(t, report.PolicyViolations, "production-delete-restriction")
	assert.Contains(t, report.PolicyViolations, "mfa-required")
}

func TestComplianceReportHighFailureRate(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	// Log many failed events
	for i := 0; i < 7; i++ {
		logger.LogAction("user1", "delete", "pod", "mypod", false)
	}
	
	// Log few successful
	for i := 0; i < 3; i++ {
		logger.LogAction("user1", "get", "pod", "mypod", true)
	}
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.Equal(t, 10, report.TotalEvents)
	assert.Equal(t, 7, report.FailedEvents)
	assert.NotEmpty(t, report.Recommendations)
	
	// Should recommend investigating high failure rate
	hasFailureWarning := false
	for _, rec := range report.Recommendations {
		if stringContains(rec, "failure rate") {
			hasFailureWarning = true
			break
		}
	}
	assert.True(t, hasFailureWarning)
}

func TestComplianceReportAnomalousEvents(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	// Add anomalous events (risk >= 0.8)
	for i := 0; i < 3; i++ {
		event := &AuditEvent{
			UserID:    "user1",
			Action:    "delete",
			Resource:  "production-db",
			Success:   true,
			RiskScore: 0.85,
			Timestamp: time.Now(),
		}
		logger.LogEvent(event)
	}
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.Len(t, report.AnomalousEvents, 3)
	assert.NotEmpty(t, report.Recommendations)
	
	// Should have anomaly warning
	hasAnomalyWarning := false
	for _, rec := range report.Recommendations {
		if stringContains(rec, "anomalous") {
			hasAnomalyWarning = true
			break
		}
	}
	assert.True(t, hasAnomalyWarning)
}

func TestComplianceReportTamperDetection(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	logger.LogAction("user1", "get", "pods", "", true)
	logger.LogAction("user1", "delete", "pod", "mypod", true)
	
	// Tamper with event
	logger.events[0].Action = "TAMPERED"
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.True(t, report.TamperDetected)
	assert.NotEmpty(t, report.Recommendations)
	
	// Should have critical tamper warning
	hasTamperWarning := false
	for _, rec := range report.Recommendations {
		if stringContains(rec, "Tampering detected") {
			hasTamperWarning = true
			break
		}
	}
	assert.True(t, hasTamperWarning)
}

func TestComplianceReportOutsidePeriod(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	// Events outside period
	oldEvent := &AuditEvent{
		UserID:    "user1",
		Action:    "get",
		Timestamp: time.Now().Add(-48 * time.Hour),
	}
	logger.LogEvent(oldEvent)
	
	// Event in period
	logger.LogAction("user1", "delete", "pod", "mypod", true)
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	// Should only count event in period
	assert.Equal(t, 1, report.TotalEvents)
}

func TestGetLatestEventsEdgeCases(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	for i := 0; i < 5; i++ {
		logger.LogAction("user1", "get", "pods", "", true)
	}
	
	t.Run("Request more than available", func(t *testing.T) {
		latest := logger.GetLatestEvents(10)
		assert.Len(t, latest, 5)
	})
	
	t.Run("Request zero", func(t *testing.T) {
		latest := logger.GetLatestEvents(0)
		assert.Len(t, latest, 5)
	})
	
	t.Run("Request negative", func(t *testing.T) {
		latest := logger.GetLatestEvents(-1)
		assert.Len(t, latest, 5)
	})
}

func TestCustomAuditConfig(t *testing.T) {
	config := &AuditConfig{
		MaxEvents:      100,
		PersistEvents:  true,
		IncludePII:     false,
		RetentionDays:  30,
		ComplianceMode: false,
		TamperProof:    false,
		SignEvents:     true,
	}
	
	logger := NewAuditLogger(config)
	
	assert.Equal(t, 100, logger.config.MaxEvents)
	assert.True(t, logger.config.PersistEvents)
	assert.False(t, logger.config.IncludePII)
	assert.Equal(t, 30, logger.config.RetentionDays)
	assert.False(t, logger.config.ComplianceMode)
	assert.False(t, logger.config.TamperProof)
	assert.True(t, logger.config.SignEvents)
}

func TestTamperProofDisabled(t *testing.T) {
	config := &AuditConfig{
		MaxEvents:   100,
		TamperProof: false,
	}
	logger := NewAuditLogger(config)
	
	logger.LogAction("user1", "get", "pods", "", true)
	
	events := logger.GetEvents(nil)
	
	// With tamper-proof disabled, hashes should be empty
	require.Len(t, events, 1)
	assert.Empty(t, events[0].EventHash)
	assert.Empty(t, events[0].PreviousHash)
}

func TestConcurrentWrites(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	// Concurrent writes
	done := make(chan bool)
	
	for i := 0; i < 10; i++ {
		go func(id int) {
			logger.LogAction(fmt.Sprintf("user%d", id), "get", "pods", "", true)
			done <- true
		}(i)
	}
	
	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}
	
	assert.Equal(t, 10, logger.GetEventCount())
}

func TestComplianceReportUserActivity(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	logger.LogAction("user1", "get", "pods", "", true)
	logger.LogAction("user1", "delete", "pod", "mypod", true)
	logger.LogAction("user2", "get", "secrets", "", true)
	logger.LogAction("user2", "create", "deployment", "", true)
	logger.LogAction("user2", "scale", "deployment", "", true)
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.Equal(t, 2, report.UserActivity["user1"])
	assert.Equal(t, 3, report.UserActivity["user2"])
}

func TestComplianceReportActionDistribution(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	logger.LogAction("user1", "get", "pods", "", true)
	logger.LogAction("user1", "get", "secrets", "", true)
	logger.LogAction("user1", "delete", "pod", "mypod", true)
	logger.LogAction("user2", "create", "deployment", "", true)
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.Equal(t, 2, report.ActionDistribution["get"])
	assert.Equal(t, 1, report.ActionDistribution["delete"])
	assert.Equal(t, 1, report.ActionDistribution["create"])
}

func TestComplianceReportSecurityEvents(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	// Low risk events
	logger.LogAction("user1", "get", "pods", "", true)
	
	// High risk events (risk > 0.5)
	event1 := &AuditEvent{
		UserID:    "user1",
		Action:    "delete",
		Resource:  "namespace",
		Success:   true,
		RiskScore: 0.6,
		Timestamp: time.Now(),
	}
	logger.LogEvent(event1)
	
	event2 := &AuditEvent{
		UserID:    "user1",
		Action:    "delete",
		Resource:  "production-db",
		Success:   true,
		RiskScore: 0.8,
		Timestamp: time.Now(),
	}
	logger.LogEvent(event2)
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.Equal(t, 2, report.SecurityEvents) // Events with risk > 0.5
}

func TestComplianceReportHealthy(t *testing.T) {
	logger := NewAuditLogger(nil)
	
	// All successful, low-risk events
	for i := 0; i < 10; i++ {
		logger.LogAction("user1", "get", "pods", "", true)
	}
	
	period := Period{
		Start: time.Now().Add(-1 * time.Hour),
		End:   time.Now().Add(1 * time.Hour),
	}
	
	report := logger.GenerateComplianceReport(period)
	
	assert.Equal(t, 10, report.TotalEvents)
	assert.Equal(t, 10, report.SuccessfulEvents)
	assert.Equal(t, 0, report.FailedEvents)
	assert.Empty(t, report.HighRiskEvents)
	assert.Empty(t, report.AnomalousEvents)
	assert.False(t, report.TamperDetected)
	
	// Should have positive recommendation
	hasHealthyMessage := false
	for _, rec := range report.Recommendations {
		if stringContains(rec, "No issues detected") {
			hasHealthyMessage = true
			break
		}
	}
	assert.True(t, hasHealthyMessage)
}

// Helper function
func stringContains(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

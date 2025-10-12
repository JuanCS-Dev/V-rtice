package audit

import (
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

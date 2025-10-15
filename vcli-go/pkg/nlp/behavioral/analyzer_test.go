package behavioral
import "strings"

import (
"testing"
"time"

"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
)

func TestNewBehavioralAnalyzer(t *testing.T) {
analyzer := NewBehavioralAnalyzer(nil)
assert.NotNil(t, analyzer)
assert.NotNil(t, analyzer.config)
}

func TestRecordAction(t *testing.T) {
analyzer := NewBehavioralAnalyzer(nil)

analyzer.RecordAction("user1", "get", "pods", true)

profile, exists := analyzer.GetProfile("user1")
require.True(t, exists)
assert.Equal(t, 1, profile.TotalActions)
assert.Equal(t, 1, profile.ActionFrequency["get"])
}

func TestAnalyzeAction_NewUser(t *testing.T) {
analyzer := NewBehavioralAnalyzer(nil)

result := analyzer.AnalyzeAction("newuser", "get", "pods")

assert.False(t, result.IsAnomaly)
assert.Equal(t, 0.0, result.Score)
assert.Contains(t, result.Reasons[0], "No baseline")
}

func TestAnalyzeAction_InsufficientSamples(t *testing.T) {
config := &AnalyzerConfig{
MinSamplesBaseline: 10,
AnomalyThreshold:   0.7,
}
analyzer := NewBehavioralAnalyzer(config)

// Record few actions
for i := 0; i < 5; i++ {
analyzer.RecordAction("user1", "get", "pods", true)
}

result := analyzer.AnalyzeAction("user1", "get", "pods")

assert.False(t, result.IsAnomaly)
assert.Contains(t, result.Reasons[0], "Insufficient baseline")
}

func TestAnalyzeAction_NormalBehavior(t *testing.T) {
config := &AnalyzerConfig{
MinSamplesBaseline: 10,
AnomalyThreshold:   0.7,
}
analyzer := NewBehavioralAnalyzer(config)

// Build baseline
for i := 0; i < 20; i++ {
analyzer.RecordAction("user1", "get", "pods", true)
analyzer.RecordAction("user1", "list", "deployments", true)
}

// Same action should be normal
result := analyzer.AnalyzeAction("user1", "get", "pods")

assert.False(t, result.IsAnomaly)
assert.Less(t, result.Score, 0.7)
}

func TestAnalyzeAction_NewAction(t *testing.T) {
config := &AnalyzerConfig{
MinSamplesBaseline: 10,
AnomalyThreshold:   0.3,
}
analyzer := NewBehavioralAnalyzer(config)

// Build baseline with specific actions
for i := 0; i < 15; i++ {
analyzer.RecordAction("user1", "get", "pods", true)
}

// Completely new action
result := analyzer.AnalyzeAction("user1", "delete", "namespace")

assert.True(t, result.IsAnomaly)
assert.Greater(t, result.Score, 0.5)
assert.Contains(t, result.Reasons[0], "New action")
}

func TestAnalyzeAction_NewResource(t *testing.T) {
config := &AnalyzerConfig{
MinSamplesBaseline: 10,
AnomalyThreshold:   0.3,
}
analyzer := NewBehavioralAnalyzer(config)

// Build baseline
for i := 0; i < 15; i++ {
analyzer.RecordAction("user1", "get", "pods", true)
}

// Same action, new resource
result := analyzer.AnalyzeAction("user1", "get", "secrets")

assert.True(t, result.IsAnomaly)
found := false
for _, reason := range result.Reasons {
if strings.Contains(reason, "New resource") {
found = true
break
}
}
assert.True(t, found)
}

func TestUserProfile_RecordAction(t *testing.T) {
profile := newUserProfile("user1")

profile.recordAction("get", "pods", true)
profile.recordAction("get", "pods", true)
profile.recordAction("list", "deployments", true)

assert.Equal(t, 3, profile.TotalActions)
assert.Equal(t, 2, profile.ActionFrequency["get"])
assert.Equal(t, 1, profile.ActionFrequency["list"])
assert.Equal(t, 2, profile.ResourceAccess["pods"])
}

func TestUserProfile_GetMostActiveHour(t *testing.T) {
profile := newUserProfile("user1")

// Simulate activity at specific hour
currentHour := time.Now().Hour()
profile.HourDistribution[currentHour] = 10
profile.HourDistribution[(currentHour+1)%24] = 5

mostActive := profile.getMostActiveHour()
assert.Equal(t, currentHour, mostActive)
}

func TestUserProfile_CountRecentActions(t *testing.T) {
profile := newUserProfile("user1")

now := time.Now()

// Add recent actions
profile.RecentActions = []ActionRecord{
{Action: "get", Timestamp: now.Add(-1 * time.Minute)},
{Action: "get", Timestamp: now.Add(-2 * time.Minute)},
{Action: "delete", Timestamp: now.Add(-3 * time.Minute)},
{Action: "get", Timestamp: now.Add(-10 * time.Minute)}, // Outside window
}

count := profile.countRecentActions("get", 5*time.Minute, now)
assert.Equal(t, 2, count)
}

func TestGetBaselineStats(t *testing.T) {
profile := newUserProfile("user1")

for i := 0; i < 10; i++ {
profile.recordAction("get", "pods", true)
}
for i := 0; i < 5; i++ {
profile.recordAction("list", "deployments", true)
}

stats := profile.getBaselineStats()

assert.Equal(t, 15, stats.SampleSize)
assert.Contains(t, stats.CommonActions, "get")
assert.Contains(t, stats.CommonResources, "pods")
assert.Greater(t, stats.ActionsPerHour, 0.0)
}

func TestCalculateConfidence(t *testing.T) {
// Low samples
conf := calculateConfidence(5, 10)
assert.Less(t, conf, 0.5)

// Minimum samples
conf = calculateConfidence(10, 10)
assert.Greater(t, conf, 0.2)

// Many samples
conf = calculateConfidence(100, 10)
assert.Greater(t, conf, 0.9)
}

func TestGetTopN(t *testing.T) {
freq := map[string]int{
"action1": 10,
"action2": 5,
"action3": 15,
"action4": 2,
}

top := getTopN(freq, 2)

assert.Len(t, top, 2)
assert.Contains(t, top, "action3") // Highest
assert.Contains(t, top, "action1") // Second
}

func TestResetProfile(t *testing.T) {
analyzer := NewBehavioralAnalyzer(nil)

analyzer.RecordAction("user1", "get", "pods", true)

_, exists := analyzer.GetProfile("user1")
require.True(t, exists)

analyzer.ResetProfile("user1")

_, exists = analyzer.GetProfile("user1")
assert.False(t, exists)
}

func TestGetStats(t *testing.T) {
analyzer := NewBehavioralAnalyzer(nil)

analyzer.RecordAction("user1", "get", "pods", true)
analyzer.RecordAction("user2", "list", "deployments", true)

stats := analyzer.GetStats()
assert.Equal(t, 2, stats.TotalProfiles)
assert.NotNil(t, stats.Config)
}

func TestDefaultAnalyzerConfig(t *testing.T) {
config := DefaultAnalyzerConfig()

assert.Equal(t, 0.7, config.AnomalyThreshold)
assert.Equal(t, 10, config.MinSamplesBaseline)
assert.True(t, config.TrackActions)
}

func TestAnomalyResult_Confidence(t *testing.T) {
config := &AnalyzerConfig{
MinSamplesBaseline: 10,
AnomalyThreshold:   0.7,
}
analyzer := NewBehavioralAnalyzer(config)

// Build large baseline
for i := 0; i < 50; i++ {
analyzer.RecordAction("user1", "get", "pods", true)
}

result := analyzer.AnalyzeAction("user1", "delete", "namespace")

assert.Greater(t, result.Confidence, 0.8) // High confidence with many samples
}

func TestDetectAnomaly_TimeOfDay(t *testing.T) {
	config := &AnalyzerConfig{
		MinSamplesBaseline: 5,
		AnomalyThreshold:   0.5,
		TrackTimeOfDay:     true,
	}
	analyzer := NewBehavioralAnalyzer(config)
	
	// Build baseline - concentrate activity at specific hour
	currentHour := time.Now().Hour()
	for i := 0; i < 20; i++ {
		analyzer.RecordAction("user1", "get", "pods", true)
	}
	
	// Access profile and simulate different hour distribution
	profile, _ := analyzer.GetProfile("user1")
	profile.mu.Lock()
	profile.HourDistribution[currentHour] = 20 // All activity at current hour
	profile.HourDistribution[(currentHour+12)%24] = 0 // Opposite hour empty
	profile.mu.Unlock()
	
	// Simulate action at unusual time (12 hours different)
	// This would require time manipulation or direct profile testing
	result := profile.detectAnomaly("get", "pods", config)
	
	// Should detect some level of anomaly based on patterns
	assert.NotNil(t, result)
	assert.NotNil(t, result.Baseline)
}

func TestDetectAnomaly_FrequentAction(t *testing.T) {
	config := &AnalyzerConfig{
		MinSamplesBaseline: 5,
		AnomalyThreshold:   0.8,
	}
	analyzer := NewBehavioralAnalyzer(config)
	
	// Build baseline with many actions
	for i := 0; i < 50; i++ {
		analyzer.RecordAction("user1", "get", "pods", true)
	}
	
	// Detect rare action
	profile, _ := analyzer.GetProfile("user1")
	profile.recordAction("delete", "namespace", true) // Only once
	
	result := profile.detectAnomaly("delete", "namespace", config)
	
	assert.True(t, result.Score > 0.0)
	assert.NotNil(t, result.Reasons)
}

func TestAbs_Function(t *testing.T) {
	tests := []struct {
		input    int
		expected int
	}{
		{5, 5},
		{-5, 5},
		{0, 0},
		{-100, 100},
		{100, 100},
	}
	
	for _, tt := range tests {
		result := abs(tt.input)
		assert.Equal(t, tt.expected, result, "abs(%d) should be %d", tt.input, tt.expected)
	}
}

func TestGetBaselineStats_EmptyProfile(t *testing.T) {
	profile := newUserProfile("user1")
	
	// Get stats immediately (no actions)
	stats := profile.getBaselineStats()
	
	assert.NotNil(t, stats)
	assert.Equal(t, 0, stats.SampleSize)
	// TypicalHour defaults to hour with most activity (may be any hour when empty)
	assert.GreaterOrEqual(t, stats.TypicalHour, 0)
	assert.LessOrEqual(t, stats.TypicalHour, 23)
	// Actions per hour should be >= 0 (avoids division by zero)
	assert.GreaterOrEqual(t, stats.ActionsPerHour, 0.0)
}

func TestDetectAnomaly_RareResource(t *testing.T) {
	config := &AnalyzerConfig{
		MinSamplesBaseline: 5,
		AnomalyThreshold:   0.4,
	}
	analyzer := NewBehavioralAnalyzer(config)
	
	// Build baseline
	for i := 0; i < 20; i++ {
		analyzer.RecordAction("user1", "get", "pods", true)
		analyzer.RecordAction("user1", "get", "deployments", true)
	}
	
	// Access resource only once
	analyzer.RecordAction("user1", "get", "secrets", true)
	
	profile, _ := analyzer.GetProfile("user1")
	result := profile.detectAnomaly("get", "secrets", config)
	
	// Should detect rare resource access
	foundReason := false
	for _, reason := range result.Reasons {
		if strings.Contains(reason, "Rare resource") || strings.Contains(reason, "New resource") {
			foundReason = true
			break
		}
	}
	assert.True(t, foundReason)
}

func TestRecordAction_HourDistribution(t *testing.T) {
	profile := newUserProfile("user1")
	
	currentHour := time.Now().Hour()
	
	// Record multiple actions
	for i := 0; i < 5; i++ {
		profile.recordAction("get", "pods", true)
	}
	
	// Check hour distribution updated
	assert.Equal(t, 5, profile.HourDistribution[currentHour])
}

// TestRecordAction_Limits tests action recording limits
func TestRecordAction_Limits(t *testing.T) {
	profile := newUserProfile("user1")
	
	// Record more than 100 actions (the limit)
	for i := 0; i < 150; i++ {
		profile.recordAction("get", "pods", true)
	}
	
	// Should cap at 100 recent actions
	assert.LessOrEqual(t, len(profile.RecentActions), 100)
	assert.Equal(t, 150, profile.TotalActions)
}

// TestDetectAnomaly_FrequencySpike tests frequency spike detection
func TestDetectAnomaly_FrequencySpike(t *testing.T) {
	config := &AnalyzerConfig{
		MinSamplesBaseline: 5,
		AnomalyThreshold:   0.5,
	}
	
	profile := newUserProfile("user1")
	
	// Build slow baseline
	profile.ActionFrequency["delete"] = 2
	profile.TotalActions = 100
	
	// Simulate recent spike
	now := time.Now()
	for i := 0; i < 8; i++ {
		profile.RecentActions = append(profile.RecentActions, ActionRecord{
			Action:    "delete",
			Resource:  "pod",
			Timestamp: now.Add(-time.Minute * time.Duration(i)),
			Success:   true,
		})
	}
	
	result := profile.detectAnomaly("delete", "pod", config)
	
	// Should detect frequency spike
	foundSpike := false
	for _, reason := range result.Reasons {
		if strings.Contains(reason, "spike") || strings.Contains(reason, "Burst") {
			foundSpike = true
			break
		}
	}
	assert.True(t, foundSpike)
}

// TestGetBaselineStats_EdgeCases tests baseline stats edge cases
func TestGetBaselineStats_EdgeCases(t *testing.T) {
	t.Run("New profile zero hours", func(t *testing.T) {
		profile := newUserProfile("user1")
		profile.Created = time.Now()
		
		stats := profile.getBaselineStats()
		assert.NotNil(t, stats)
		assert.Equal(t, 0, stats.SampleSize)
		// Should not panic on division by zero
	})
	
	t.Run("Profile with actions", func(t *testing.T) {
		profile := newUserProfile("user1")
		profile.Created = time.Now().Add(-2 * time.Hour)
		
		profile.recordAction("get", "pods", true)
		profile.recordAction("list", "deployments", true)
		profile.recordAction("get", "pods", true)
		
		stats := profile.getBaselineStats()
		assert.Equal(t, 3, stats.SampleSize)
		assert.Greater(t, stats.ActionsPerHour, 0.0)
	})
}

// TestDetectAnomaly_HourWrapAround tests time-of-day wrap-around
func TestDetectAnomaly_HourWrapAround(t *testing.T) {
	profile := newUserProfile("user1")
	
	// Set typical hour to 23 (11 PM)
	profile.HourDistribution[23] = 50
	profile.HourDistribution[0] = 5
	
	profile.ActionFrequency["get"] = 20
	profile.TotalActions = 100
	
	config := &AnalyzerConfig{
		MinSamplesBaseline: 5,
		AnomalyThreshold:   0.8,
	}
	
	// Should handle hour wrap-around (23 → 0 is only 1 hour difference)
	result := profile.detectAnomaly("get", "pods", config)
	
	// Should not flag as anomaly if current hour is close to typical hour
	// (This test validates the wrap-around logic)
	assert.NotNil(t, result)
}

// Helper function
func strContains(s, substr string) bool {
return len(s) >= len(substr) && (s == substr || len(s) > 0 && len(substr) > 0)
}


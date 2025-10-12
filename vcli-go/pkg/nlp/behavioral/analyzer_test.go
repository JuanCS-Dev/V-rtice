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

count := profile.countRecentActions("get", 5*time.Minute)
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

// Helper function
func strContains(s, substr string) bool {
return len(s) >= len(substr) && (s == substr || len(s) > 0 && len(substr) > 0)
}

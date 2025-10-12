// Package behavioral implements Layer 6 (Behavioral Analysis) of Guardian Zero Trust Security.
//
// "Is this normal?" - Detecting anomalous behavior through profiling and analysis.
//
// Provides:
// - User behavior profiling
// - Anomaly detection
// - Statistical analysis
// - Adaptive learning
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)
// Date: 2025-10-12
package behavioral

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// BehavioralAnalyzer detects anomalous behavior.
type BehavioralAnalyzer struct {
	profiles map[string]*UserProfile
	mu       sync.RWMutex
	config   *AnalyzerConfig
}

// AnalyzerConfig configures behavioral analysis.
type AnalyzerConfig struct {
	// Detection thresholds
	AnomalyThreshold  float64 // 0.0-1.0, higher = more sensitive
	LearningWindow    time.Duration
	MinSamplesBaseline int
	
	// Features to track
	TrackActions    bool
	TrackResources  bool
	TrackTimeOfDay  bool
	TrackFrequency  bool
}

// UserProfile contains behavioral baseline for a user.
type UserProfile struct {
	UserID   string
	Created  time.Time
	Updated  time.Time
	
	// Action patterns
	ActionFrequency map[string]int // action -> count
	TotalActions    int
	
	// Resource patterns
	ResourceAccess map[string]int // resource -> count
	
	// Temporal patterns
	HourDistribution [24]int // actions per hour
	
	// Recent activity
	RecentActions []ActionRecord
	
	mu sync.RWMutex
}

// ActionRecord represents a user action.
type ActionRecord struct {
	Action    string
	Resource  string
	Timestamp time.Time
	Success   bool
}

// AnomalyResult contains anomaly detection result.
type AnomalyResult struct {
	IsAnomaly     bool
	Score         float64 // 0.0 (normal) - 1.0 (highly anomalous)
	Confidence    float64 // 0.0-1.0
	Reasons       []string
	Baseline      *BaselineStats
	CurrentStats  *BehaviorStats
}

// BaselineStats contains baseline statistics.
type BaselineStats struct {
	SampleSize        int
	CommonActions     []string
	CommonResources   []string
	TypicalHour       int
	ActionsPerHour    float64
}

// BehaviorStats contains current behavior statistics.
type BehaviorStats struct {
	Action         string
	Resource       string
	HourOfDay      int
	IsNewAction    bool
	IsNewResource  bool
	FrequencySpike bool
}

// NewBehavioralAnalyzer creates a new behavioral analyzer.
func NewBehavioralAnalyzer(config *AnalyzerConfig) *BehavioralAnalyzer {
	if config == nil {
		config = DefaultAnalyzerConfig()
	}
	
	return &BehavioralAnalyzer{
		profiles: make(map[string]*UserProfile),
		config:   config,
	}
}

// DefaultAnalyzerConfig returns default configuration.
func DefaultAnalyzerConfig() *AnalyzerConfig {
	return &AnalyzerConfig{
		AnomalyThreshold:   0.7,
		LearningWindow:     7 * 24 * time.Hour, // 7 days
		MinSamplesBaseline: 10,
		TrackActions:       true,
		TrackResources:     true,
		TrackTimeOfDay:     true,
		TrackFrequency:     true,
	}
}

// RecordAction records a user action for profiling.
func (ba *BehavioralAnalyzer) RecordAction(userID, action, resource string, success bool) {
	ba.mu.Lock()
	profile, exists := ba.profiles[userID]
	if !exists {
		profile = newUserProfile(userID)
		ba.profiles[userID] = profile
	}
	ba.mu.Unlock()
	
	profile.recordAction(action, resource, success)
}

// AnalyzeAction analyzes if an action is anomalous.
func (ba *BehavioralAnalyzer) AnalyzeAction(userID, action, resource string) *AnomalyResult {
	ba.mu.RLock()
	profile, exists := ba.profiles[userID]
	ba.mu.RUnlock()
	
	if !exists {
		// New user - no baseline yet
		return &AnomalyResult{
			IsAnomaly:  false,
			Score:      0.0,
			Confidence: 0.0,
			Reasons:    []string{"No baseline (new user)"},
		}
	}
	
	// Need minimum samples for reliable detection
	if profile.TotalActions < ba.config.MinSamplesBaseline {
		return &AnomalyResult{
			IsAnomaly:  false,
			Score:      0.0,
			Confidence: 0.0,
			Reasons:    []string{fmt.Sprintf("Insufficient baseline (%d/%d samples)", profile.TotalActions, ba.config.MinSamplesBaseline)},
		}
	}
	
	return profile.detectAnomaly(action, resource, ba.config)
}

// GetProfile returns a user's profile.
func (ba *BehavioralAnalyzer) GetProfile(userID string) (*UserProfile, bool) {
	ba.mu.RLock()
	defer ba.mu.RUnlock()
	
	profile, exists := ba.profiles[userID]
	return profile, exists
}

// GetStats returns analyzer statistics.
func (ba *BehavioralAnalyzer) GetStats() *AnalyzerStats {
	ba.mu.RLock()
	defer ba.mu.RUnlock()
	
	return &AnalyzerStats{
		TotalProfiles: len(ba.profiles),
		Config:        ba.config,
	}
}

// AnalyzerStats contains analyzer statistics.
type AnalyzerStats struct {
	TotalProfiles int
	Config        *AnalyzerConfig
}

// newUserProfile creates a new user profile.
func newUserProfile(userID string) *UserProfile {
	return &UserProfile{
		UserID:           userID,
		Created:          time.Now(),
		Updated:          time.Now(),
		ActionFrequency:  make(map[string]int),
		ResourceAccess:   make(map[string]int),
		HourDistribution: [24]int{},
		RecentActions:    make([]ActionRecord, 0),
	}
}

// recordAction records an action in the profile.
func (up *UserProfile) recordAction(action, resource string, success bool) {
	up.mu.Lock()
	defer up.mu.Unlock()
	
	now := time.Now()
	
	// Update action frequency
	up.ActionFrequency[action]++
	up.TotalActions++
	
	// Update resource access
	up.ResourceAccess[resource]++
	
	// Update hour distribution
	hour := now.Hour()
	up.HourDistribution[hour]++
	
	// Add to recent actions (keep last 100)
	record := ActionRecord{
		Action:    action,
		Resource:  resource,
		Timestamp: now,
		Success:   success,
	}
	up.RecentActions = append(up.RecentActions, record)
	if len(up.RecentActions) > 100 {
		up.RecentActions = up.RecentActions[1:]
	}
	
	up.Updated = now
}

// detectAnomaly detects if current action is anomalous.
func (up *UserProfile) detectAnomaly(action, resource string, config *AnalyzerConfig) *AnomalyResult {
	up.mu.RLock()
	defer up.mu.RUnlock()
	
	score := 0.0
	reasons := []string{}
	
	// Check action novelty
	actionCount := up.ActionFrequency[action]
	if actionCount == 0 {
		score += 0.4
		reasons = append(reasons, fmt.Sprintf("New action '%s' (never seen before)", action))
	} else if actionCount == 1 {
		score += 0.2
		reasons = append(reasons, fmt.Sprintf("Rare action '%s' (seen only once)", action))
	}
	
	// Check resource novelty
	resourceCount := up.ResourceAccess[resource]
	if resourceCount == 0 {
		score += 0.3
		reasons = append(reasons, fmt.Sprintf("New resource '%s' (never accessed)", resource))
	} else if resourceCount == 1 {
		score += 0.15
		reasons = append(reasons, fmt.Sprintf("Rare resource '%s' (accessed only once)", resource))
	}
	
	// Check time-of-day anomaly
	hour := time.Now().Hour()
	typicalHour := up.getMostActiveHour()
	hourDiff := abs(hour - typicalHour)
	if hourDiff > 12 {
		hourDiff = 24 - hourDiff // Wrap around
	}
	
	if hourDiff > 6 {
		score += 0.2
		reasons = append(reasons, fmt.Sprintf("Unusual time (active at %02d:00, typically %02d:00)", hour, typicalHour))
	}
	
	// Check frequency spike
	recentCount := up.countRecentActions(action, 5*time.Minute)
	avgRate := float64(up.ActionFrequency[action]) / float64(up.TotalActions)
	expectedInWindow := avgRate * 10.0 // Expected in 5min window (assuming ~2 actions/min baseline)
	
	if recentCount > int(expectedInWindow*3) && expectedInWindow > 0 {
		score += 0.3
		reasons = append(reasons, fmt.Sprintf("Frequency spike (%d actions in 5min, expected ~%.1f)", recentCount, expectedInWindow))
	}
	
	// Normalize score
	if score > 1.0 {
		score = 1.0
	}
	
	// Calculate confidence based on sample size
	confidence := calculateConfidence(up.TotalActions, config.MinSamplesBaseline)
	
	// Build result
	result := &AnomalyResult{
		IsAnomaly:  score >= config.AnomalyThreshold,
		Score:      score,
		Confidence: confidence,
		Reasons:    reasons,
		Baseline:   up.getBaselineStats(),
		CurrentStats: &BehaviorStats{
			Action:         action,
			Resource:       resource,
			HourOfDay:      hour,
			IsNewAction:    actionCount == 0,
			IsNewResource:  resourceCount == 0,
			FrequencySpike: recentCount > int(expectedInWindow*3),
		},
	}
	
	return result
}

// getMostActiveHour returns the hour with most activity.
func (up *UserProfile) getMostActiveHour() int {
	maxCount := 0
	maxHour := 12 // Default to noon
	
	for hour, count := range up.HourDistribution {
		if count > maxCount {
			maxCount = count
			maxHour = hour
		}
	}
	
	return maxHour
}

// countRecentActions counts actions in recent time window.
func (up *UserProfile) countRecentActions(action string, window time.Duration) int {
	cutoff := time.Now().Add(-window)
	count := 0
	
	for _, record := range up.RecentActions {
		if record.Action == action && record.Timestamp.After(cutoff) {
			count++
		}
	}
	
	return count
}

// getBaselineStats returns baseline statistics.
func (up *UserProfile) getBaselineStats() *BaselineStats {
	// Get top 3 actions
	commonActions := getTopN(up.ActionFrequency, 3)
	
	// Get top 3 resources
	commonResources := getTopN(up.ResourceAccess, 3)
	
	// Calculate average actions per hour
	totalHours := time.Since(up.Created).Hours()
	if totalHours == 0 {
		totalHours = 1
	}
	actionsPerHour := float64(up.TotalActions) / totalHours
	
	return &BaselineStats{
		SampleSize:      up.TotalActions,
		CommonActions:   commonActions,
		CommonResources: commonResources,
		TypicalHour:     up.getMostActiveHour(),
		ActionsPerHour:  actionsPerHour,
	}
}

// Helper functions

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func calculateConfidence(samples, minSamples int) float64 {
	if samples < minSamples {
		return 0.0
	}
	
	// Asymptotic confidence growth
	// Reaches ~0.95 at 10x minSamples
	ratio := float64(samples) / float64(minSamples)
	confidence := 1.0 - math.Exp(-ratio/3.0)
	
	return confidence
}

func getTopN(freq map[string]int, n int) []string {
	type kv struct {
		key   string
		value int
	}
	
	var items []kv
	for k, v := range freq {
		items = append(items, kv{k, v})
	}
	
	// Simple bubble sort for top N
	for i := 0; i < len(items) && i < n; i++ {
		for j := i + 1; j < len(items); j++ {
			if items[j].value > items[i].value {
				items[i], items[j] = items[j], items[i]
			}
		}
	}
	
	result := []string{}
	for i := 0; i < len(items) && i < n; i++ {
		result = append(result, items[i].key)
	}
	
	return result
}

// ResetProfile resets a user's profile.
func (ba *BehavioralAnalyzer) ResetProfile(userID string) {
	ba.mu.Lock()
	defer ba.mu.Unlock()
	
	delete(ba.profiles, userID)
}

// Package behavioral - Layer 6: Behavioral Analysis
//
// Detects anomalous user behavior patterns
package behavioral

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// BehavioralLayer analyzes user behavior patterns
type BehavioralLayer interface {
	// AnalyzeBehavior checks if action is consistent with user history
	AnalyzeBehavior(ctx context.Context, userID string, action string, metadata map[string]interface{}) (*BehaviorDecision, error)
}

// BehaviorDecision represents analysis result
type BehaviorDecision struct {
	AnomalyScore float64 // 0.0 = normal, 1.0 = highly anomalous
	Reason       string
	Alert        bool
}

// UserProfile tracks normal behavior
type UserProfile struct {
	UserID        string
	CommonActions map[string]int       // action -> frequency
	LastSeen      time.Time
	Locations     map[string]int       // IP -> frequency
	TotalActions  int
	CreatedAt     time.Time
}

type behavioralAnalyzer struct {
	mu       sync.RWMutex
	profiles map[string]*UserProfile // userID -> profile
}

// NewBehavioralAnalyzer creates behavioral layer
func NewBehavioralAnalyzer() BehavioralLayer {
	return &behavioralAnalyzer{
		profiles: make(map[string]*UserProfile),
	}
}

// AnalyzeBehavior implements BehavioralLayer
func (b *behavioralAnalyzer) AnalyzeBehavior(ctx context.Context, userID string, action string, metadata map[string]interface{}) (*BehaviorDecision, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	profile, exists := b.profiles[userID]
	if !exists {
		// First time user - create profile
		profile = &UserProfile{
			UserID:        userID,
			CommonActions: make(map[string]int),
			Locations:     make(map[string]int),
			CreatedAt:     time.Now(),
		}
		b.profiles[userID] = profile
	}

	// Check for anomalies
	anomalyScore := b.calculateAnomalyScore(profile, action, metadata)

	// Update profile
	profile.CommonActions[action]++
	profile.TotalActions++
	profile.LastSeen = time.Now()

	if ip, ok := metadata["ip"].(string); ok {
		profile.Locations[ip]++
	}

	decision := &BehaviorDecision{
		AnomalyScore: anomalyScore,
		Alert:        anomalyScore > 0.7, // Alert if score > 70%
	}

	if anomalyScore < 0.3 {
		decision.Reason = "Normal behavior pattern"
	} else if anomalyScore < 0.7 {
		decision.Reason = fmt.Sprintf("Slightly unusual (score: %.2f)", anomalyScore)
	} else {
		decision.Reason = fmt.Sprintf("⚠️  ANOMALY DETECTED (score: %.2f)", anomalyScore)
	}

	return decision, nil
}

// calculateAnomalyScore computes anomaly score
func (b *behavioralAnalyzer) calculateAnomalyScore(profile *UserProfile, action string, metadata map[string]interface{}) float64 {
	score := 0.0

	// New user = no anomaly yet
	if profile.TotalActions == 0 {
		return 0.0
	}

	// Check action frequency
	actionCount := profile.CommonActions[action]
	actionFreq := float64(actionCount) / float64(profile.TotalActions)

	// Rare action = higher score
	if actionFreq == 0 {
		score += 0.5 // Never done before
	} else if actionFreq < 0.1 {
		score += 0.3 // Rare action
	}

	// Check location
	if ip, ok := metadata["ip"].(string); ok {
		ipCount := profile.Locations[ip]
		if ipCount == 0 {
			score += 0.3 // New location
		}
	}

	// Check time since last action
	timeSinceLastSeen := time.Since(profile.LastSeen)
	if timeSinceLastSeen > 30*24*time.Hour {
		score += 0.2 // Long absence
	}

	// Cap at 1.0
	if score > 1.0 {
		score = 1.0
	}

	return score
}


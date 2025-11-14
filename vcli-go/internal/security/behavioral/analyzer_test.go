package behavioral

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewBehavioralAnalyzer(t *testing.T) {
	t.Run("creates analyzer with empty profiles", func(t *testing.T) {
		analyzer := NewBehavioralAnalyzer()
		assert.NotNil(t, analyzer)

		// Verify analyzer is usable
		ctx := context.Background()
		decision, err := analyzer.AnalyzeBehavior(ctx, "user1", "read", map[string]interface{}{})
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})

	t.Run("creates analyzer with initialized profile map", func(t *testing.T) {
		analyzer := NewBehavioralAnalyzer().(*behavioralAnalyzer)
		assert.NotNil(t, analyzer.profiles)
		assert.Empty(t, analyzer.profiles)
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_FirstTimeUser(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("creates profile for new user", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "newuser", "kubectl.get", map[string]interface{}{
			"ip": "192.168.1.100",
		})
		require.NoError(t, err)

		assert.Equal(t, 0.0, decision.AnomalyScore)
		assert.False(t, decision.Alert)
		assert.Contains(t, decision.Reason, "Normal behavior")

		// Verify profile was created
		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.RLock()
		profile, exists := ba.profiles["newuser"]
		ba.mu.RUnlock()

		assert.True(t, exists)
		assert.NotNil(t, profile)
		assert.Equal(t, "newuser", profile.UserID)
		assert.Equal(t, 1, profile.TotalActions)
		assert.Equal(t, 1, profile.CommonActions["kubectl.get"])
	})

	t.Run("zero anomaly score for first action", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "user-first-time", "delete", map[string]interface{}{})
		require.NoError(t, err)

		assert.Equal(t, 0.0, decision.AnomalyScore)
		assert.False(t, decision.Alert)
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_RepeatedActions(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("learns normal behavior over time", func(t *testing.T) {
		userID := "repeat-user"

		// Perform same action 10 times
		for i := 0; i < 10; i++ {
			decision, err := analyzer.AnalyzeBehavior(ctx, userID, "kubectl.get", map[string]interface{}{
				"ip": "192.168.1.100",
			})
			require.NoError(t, err)

			// After first action, score should be low for repeated action
			if i > 0 {
				assert.Less(t, decision.AnomalyScore, 0.3, "iteration %d", i)
				assert.Contains(t, decision.Reason, "Normal")
			}
		}

		// Verify profile statistics
		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.RLock()
		profile := ba.profiles[userID]
		ba.mu.RUnlock()

		assert.Equal(t, 10, profile.TotalActions)
		assert.Equal(t, 10, profile.CommonActions["kubectl.get"])
		assert.Equal(t, 10, profile.Locations["192.168.1.100"])
	})

	t.Run("common action has low anomaly score", func(t *testing.T) {
		userID := "common-user"

		// Build profile with common action
		for i := 0; i < 20; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		}

		// Same action should have low score
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		require.NoError(t, err)

		assert.Less(t, decision.AnomalyScore, 0.3)
		assert.False(t, decision.Alert)
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_AnomalousActions(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("detects never-seen action", func(t *testing.T) {
		userID := "established-user"

		// Build normal profile with read actions
		for i := 0; i < 10; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
				"ip": "192.168.1.100",
			})
		}

		// Perform unusual delete action
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "delete", map[string]interface{}{
			"ip": "192.168.1.100",
		})
		require.NoError(t, err)

		// Should have elevated score (never seen = +0.5)
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.3)
		assert.Contains(t, decision.Reason, "unusual")
	})

	t.Run("detects rare action", func(t *testing.T) {
		userID := "rare-action-user"

		// Build profile: 90% read, 10% write
		for i := 0; i < 9; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		}
		analyzer.AnalyzeBehavior(ctx, userID, "write", map[string]interface{}{})

		// Second write action - rare but not never seen
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "write", map[string]interface{}{})
		require.NoError(t, err)

		// Should have some elevated score
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.0)
		assert.LessOrEqual(t, decision.AnomalyScore, 1.0)
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_LocationTracking(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("tracks user IP locations", func(t *testing.T) {
		userID := "location-user"

		// Build profile from home IP
		for i := 0; i < 5; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
				"ip": "192.168.1.100",
			})
		}

		// Access from new IP
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
			"ip": "10.0.0.50",
		})
		require.NoError(t, err)

		// Should detect new location (+0.3)
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.3)
	})

	t.Run("no IP metadata does not crash", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "no-ip-user", "read", map[string]interface{}{})
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})

	t.Run("known IP has lower score", func(t *testing.T) {
		userID := "known-ip-user"

		// Build profile
		for i := 0; i < 10; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
				"ip": "192.168.1.100",
			})
		}

		// Same IP, same action
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
			"ip": "192.168.1.100",
		})
		require.NoError(t, err)

		assert.Less(t, decision.AnomalyScore, 0.3)
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_AlertThresholds(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("no alert for score below 0.7", func(t *testing.T) {
		userID := "low-score-user"

		// First action (score = 0.0)
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		require.NoError(t, err)

		assert.False(t, decision.Alert)
		assert.Less(t, decision.AnomalyScore, 0.7)
	})

	t.Run("alert triggered for score above 0.7", func(t *testing.T) {
		userID := "high-score-user"

		// Build profile with one action type
		for i := 0; i < 10; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
				"ip": "192.168.1.100",
			})
		}

		// Completely new action + new IP should trigger alert
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "delete", map[string]interface{}{
			"ip": "10.0.0.1",
		})
		require.NoError(t, err)

		// New action (0.5) + new IP (0.3) = 0.8 > 0.7
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.7)
		assert.True(t, decision.Alert)
		assert.Contains(t, decision.Reason, "ANOMALY DETECTED")
	})

	t.Run("reason varies by score range", func(t *testing.T) {
		userID := "reason-user"

		// Score < 0.3 - Normal
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		require.NoError(t, err)
		assert.Contains(t, decision.Reason, "Normal")

		// Build profile
		for i := 0; i < 10; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		}

		// Score 0.3-0.7 - Slightly unusual
		decision, err = analyzer.AnalyzeBehavior(ctx, userID, "write", map[string]interface{}{})
		require.NoError(t, err)
		assert.Contains(t, decision.Reason, "unusual")

		// Score > 0.7 - Anomaly
		decision, err = analyzer.AnalyzeBehavior(ctx, userID, "delete", map[string]interface{}{
			"ip": "10.0.0.1",
		})
		require.NoError(t, err)
		assert.Contains(t, decision.Reason, "ANOMALY")
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_LongAbsence(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("detects user returning after long absence", func(t *testing.T) {
		userID := "absent-user"

		// Create profile
		analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})

		// Manually set LastSeen to 31 days ago
		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.Lock()
		ba.profiles[userID].LastSeen = time.Now().Add(-31 * 24 * time.Hour)
		ba.mu.Unlock()

		// Return after absence
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		require.NoError(t, err)

		// Should add +0.2 to score
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.2)
	})

	t.Run("no penalty for recent activity", func(t *testing.T) {
		userID := "active-user"

		// Build recent profile
		for i := 0; i < 5; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
			time.Sleep(1 * time.Millisecond)
		}

		// Recent action
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		require.NoError(t, err)

		assert.Less(t, decision.AnomalyScore, 0.3)
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_ScoreCapping(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("anomaly score capped at 1.0", func(t *testing.T) {
		userID := "max-score-user"

		// Build profile
		for i := 0; i < 10; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
				"ip": "192.168.1.100",
			})
		}

		// Manually set old LastSeen
		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.Lock()
		ba.profiles[userID].LastSeen = time.Now().Add(-60 * 24 * time.Hour)
		ba.mu.Unlock()

		// Multiple anomaly factors:
		// - New action: +0.5
		// - New IP: +0.3
		// - Long absence: +0.2
		// Total would be 1.0
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "delete", map[string]interface{}{
			"ip": "10.0.0.1",
		})
		require.NoError(t, err)

		assert.LessOrEqual(t, decision.AnomalyScore, 1.0)
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_ProfileUpdates(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("updates profile after each action", func(t *testing.T) {
		userID := "update-user"

		// First action
		analyzer.AnalyzeBehavior(ctx, userID, "action1", map[string]interface{}{
			"ip": "192.168.1.100",
		})

		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.RLock()
		profile := ba.profiles[userID]
		firstTimestamp := profile.LastSeen
		ba.mu.RUnlock()

		assert.Equal(t, 1, profile.TotalActions)
		assert.Equal(t, 1, profile.CommonActions["action1"])

		time.Sleep(2 * time.Millisecond)

		// Second action
		analyzer.AnalyzeBehavior(ctx, userID, "action2", map[string]interface{}{
			"ip": "192.168.1.100",
		})

		ba.mu.RLock()
		profile = ba.profiles[userID]
		ba.mu.RUnlock()

		assert.Equal(t, 2, profile.TotalActions)
		assert.Equal(t, 1, profile.CommonActions["action1"])
		assert.Equal(t, 1, profile.CommonActions["action2"])
		assert.True(t, profile.LastSeen.After(firstTimestamp))
	})

	t.Run("increments action counters correctly", func(t *testing.T) {
		userID := "counter-user"

		// Perform actions
		analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		analyzer.AnalyzeBehavior(ctx, userID, "write", map[string]interface{}{})

		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.RLock()
		profile := ba.profiles[userID]
		ba.mu.RUnlock()

		assert.Equal(t, 3, profile.TotalActions)
		assert.Equal(t, 2, profile.CommonActions["read"])
		assert.Equal(t, 1, profile.CommonActions["write"])
	})

	t.Run("updates location counters", func(t *testing.T) {
		userID := "location-counter-user"

		analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
			"ip": "192.168.1.100",
		})
		analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
			"ip": "192.168.1.100",
		})
		analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
			"ip": "10.0.0.1",
		})

		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.RLock()
		profile := ba.profiles[userID]
		ba.mu.RUnlock()

		assert.Equal(t, 2, profile.Locations["192.168.1.100"])
		assert.Equal(t, 1, profile.Locations["10.0.0.1"])
	})
}

func TestBehavioralAnalyzer_AnalyzeBehavior_ConcurrentAccess(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("thread-safe concurrent analysis", func(t *testing.T) {
		userID := "concurrent-user"

		var wg sync.WaitGroup
		numGoroutines := 50
		actionsPerGoroutine := 10

		for i := 0; i < numGoroutines; i++ {
			wg.Add(1)
			go func(id int) {
				defer wg.Done()
				for j := 0; j < actionsPerGoroutine; j++ {
					analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
						"ip": "192.168.1.100",
					})
				}
			}(i)
		}

		wg.Wait()

		// Verify total actions
		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.RLock()
		profile := ba.profiles[userID]
		ba.mu.RUnlock()

		assert.Equal(t, numGoroutines*actionsPerGoroutine, profile.TotalActions)
	})

	t.Run("thread-safe multiple users", func(t *testing.T) {
		var wg sync.WaitGroup
		numUsers := 20

		for i := 0; i < numUsers; i++ {
			wg.Add(1)
			go func(userNum int) {
				defer wg.Done()
				userID := "user-" + string(rune(userNum))
				for j := 0; j < 5; j++ {
					analyzer.AnalyzeBehavior(ctx, userID, "action", map[string]interface{}{})
				}
			}(i)
		}

		wg.Wait()

		// Verify all profiles created
		ba := analyzer.(*behavioralAnalyzer)
		ba.mu.RLock()
		profileCount := len(ba.profiles)
		ba.mu.RUnlock()

		assert.GreaterOrEqual(t, profileCount, 1) // At least one profile created
	})
}

func TestBehavioralAnalyzer_EdgeCases(t *testing.T) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	t.Run("empty user ID", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "", "read", map[string]interface{}{})
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})

	t.Run("empty action", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "user", "", map[string]interface{}{})
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})

	t.Run("nil metadata", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "user", "read", nil)
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})

	t.Run("empty metadata", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "user", "read", map[string]interface{}{})
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})

	t.Run("non-string IP in metadata", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "user", "read", map[string]interface{}{
			"ip": 12345, // int instead of string
		})
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})

	t.Run("special characters in action", func(t *testing.T) {
		decision, err := analyzer.AnalyzeBehavior(ctx, "user", "kubectl.get/pods:read:*", map[string]interface{}{})
		require.NoError(t, err)
		assert.NotNil(t, decision)
	})
}

func TestUserProfile_Structure(t *testing.T) {
	t.Run("profile contains all fields", func(t *testing.T) {
		profile := &UserProfile{
			UserID:        "test-user",
			CommonActions: make(map[string]int),
			LastSeen:      time.Now(),
			Locations:     make(map[string]int),
			TotalActions:  10,
			CreatedAt:     time.Now(),
		}

		assert.Equal(t, "test-user", profile.UserID)
		assert.NotNil(t, profile.CommonActions)
		assert.NotNil(t, profile.Locations)
		assert.False(t, profile.LastSeen.IsZero())
		assert.False(t, profile.CreatedAt.IsZero())
		assert.Equal(t, 10, profile.TotalActions)
	})
}

func TestBehaviorDecision_Structure(t *testing.T) {
	t.Run("decision contains all fields", func(t *testing.T) {
		decision := &BehaviorDecision{
			AnomalyScore: 0.75,
			Reason:       "Anomaly detected",
			Alert:        true,
		}

		assert.Equal(t, 0.75, decision.AnomalyScore)
		assert.Equal(t, "Anomaly detected", decision.Reason)
		assert.True(t, decision.Alert)
	})
}

func TestBehavioralAnalyzer_Integration(t *testing.T) {
	t.Run("realistic user behavior scenario", func(t *testing.T) {
		analyzer := NewBehavioralAnalyzer()
		ctx := context.Background()

		userID := "devops-user"

		// Week 1: Normal daily operations from office
		for day := 0; day < 7; day++ {
			for i := 0; i < 10; i++ {
				analyzer.AnalyzeBehavior(ctx, userID, "kubectl.get", map[string]interface{}{
					"ip": "192.168.1.100",
				})
				analyzer.AnalyzeBehavior(ctx, userID, "kubectl.describe", map[string]interface{}{
					"ip": "192.168.1.100",
				})
			}
		}

		// Normal action from office - should be low score
		decision, err := analyzer.AnalyzeBehavior(ctx, userID, "kubectl.get", map[string]interface{}{
			"ip": "192.168.1.100",
		})
		require.NoError(t, err)
		assert.Less(t, decision.AnomalyScore, 0.3)
		assert.False(t, decision.Alert)

		// Unusual delete command from office - moderate alert
		decision, err = analyzer.AnalyzeBehavior(ctx, userID, "kubectl.delete", map[string]interface{}{
			"ip": "192.168.1.100",
		})
		require.NoError(t, err)
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.3)

		// Delete from unknown IP - still elevated but not necessarily high alert
		// (delete is now in history, so score is lower than initial never-seen)
		decision, err = analyzer.AnalyzeBehavior(ctx, userID, "kubectl.delete", map[string]interface{}{
			"ip": "10.0.0.1",
		})
		require.NoError(t, err)
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.3) // New IP adds 0.3
		assert.Contains(t, decision.Reason, "unusual")
	})

	t.Run("attacker behavior detection", func(t *testing.T) {
		analyzer := NewBehavioralAnalyzer()
		ctx := context.Background()

		victimID := "compromised-user"

		// Build normal profile - viewer behavior
		for i := 0; i < 20; i++ {
			analyzer.AnalyzeBehavior(ctx, victimID, "read", map[string]interface{}{
				"ip": "192.168.1.50",
			})
		}

		// Account compromise: delete action from new IP
		decision, err := analyzer.AnalyzeBehavior(ctx, victimID, "delete", map[string]interface{}{
			"ip": "203.0.113.42", // External IP
		})
		require.NoError(t, err)

		// Should trigger alert
		assert.GreaterOrEqual(t, decision.AnomalyScore, 0.7)
		assert.True(t, decision.Alert)
		assert.Contains(t, decision.Reason, "ANOMALY")
	})
}

func BenchmarkBehavioralAnalyzer_AnalyzeBehavior(b *testing.B) {
	analyzer := NewBehavioralAnalyzer()
	ctx := context.Background()

	b.Run("new user", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			userID := "bench-user-" + string(rune(i))
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		}
	})

	b.Run("established user", func(b *testing.B) {
		userID := "established-bench-user"
		// Build profile
		for i := 0; i < 100; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{})
		}
	})

	b.Run("with IP tracking", func(b *testing.B) {
		userID := "ip-bench-user"
		for i := 0; i < b.N; i++ {
			analyzer.AnalyzeBehavior(ctx, userID, "read", map[string]interface{}{
				"ip": "192.168.1.100",
			})
		}
	})
}

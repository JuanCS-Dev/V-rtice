// Package learning implements adaptive learning from user interactions
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// The Learning Engine stores patterns, processes feedback, and adapts
// to user behavior over time using BadgerDB for persistent storage.
package learning

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	badger "github.com/dgraph-io/badger/v4"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Engine handles pattern learning and adaptation
type Engine struct {
	db            *badger.DB
	mu            sync.RWMutex
	patternCache  map[string]*Pattern // In-memory cache for hot patterns
	maxCacheSize  int                 // Maximum cache entries
	statsEnabled  bool                // Enable statistics collection
	stats         *EngineStats        // Usage statistics
}

// Pattern represents a learned command pattern
type Pattern struct {
	ID          string    `json:"id"`           // Unique pattern ID
	Input       string    `json:"input"`        // User's natural language input
	Intent      string    `json:"intent"`       // Classified intent
	Command     string    `json:"command"`      // Generated command
	Frequency   int       `json:"frequency"`    // Times pattern was used
	SuccessRate float64   `json:"success_rate"` // Success rate (0-1)
	LastUsed    time.Time `json:"last_used"`    // Last time pattern was used
	CreatedAt   time.Time `json:"created_at"`   // Pattern creation time
	UserID      string    `json:"user_id"`      // User who created pattern (optional)
}

// Feedback represents user feedback on a command
type Feedback struct {
	PatternID   string    `json:"pattern_id"`   // Associated pattern
	Input       string    `json:"input"`        // User's input
	Command     string    `json:"command"`      // Generated command
	Success     bool      `json:"success"`      // Was command successful?
	Accepted    bool      `json:"accepted"`     // Did user accept suggestion?
	Correction  string    `json:"correction"`   // User's correction (if any)
	Timestamp   time.Time `json:"timestamp"`    // Feedback time
	UserID      string    `json:"user_id"`      // User providing feedback
}

// EngineStats tracks learning engine statistics
type EngineStats struct {
	TotalPatterns      int       `json:"total_patterns"`
	TotalFeedback      int       `json:"total_feedback"`
	CacheHitRate       float64   `json:"cache_hit_rate"`
	AverageSuccessRate float64   `json:"avg_success_rate"`
	LastUpdated        time.Time `json:"last_updated"`
	cacheHits          int
	cacheMisses        int
}

// NewEngine creates a new learning engine
func NewEngine(dbPath string, maxCacheSize int) (*Engine, error) {
	// Open BadgerDB
	opts := badger.DefaultOptions(dbPath)
	opts.Logger = nil // Disable BadgerDB logging

	db, err := badger.Open(opts)
	if err != nil {
		return nil, fmt.Errorf("failed to open BadgerDB: %w", err)
	}

	engine := &Engine{
		db:           db,
		patternCache: make(map[string]*Pattern),
		maxCacheSize: maxCacheSize,
		statsEnabled: true,
		stats:        &EngineStats{LastUpdated: time.Now()},
	}

	return engine, nil
}

// Close closes the learning engine and database
func (e *Engine) Close() error {
	return e.db.Close()
}

// LearnPattern stores a new pattern or updates existing one
func (e *Engine) LearnPattern(input string, intent *nlp.Intent, command *nlp.Command) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	patternID := generatePatternID(input)

	// Check if pattern exists
	existingPattern, err := e.getPatternFromDB(patternID)
	if err == nil {
		// Update existing pattern
		existingPattern.Frequency++
		existingPattern.LastUsed = time.Now()
		if err := e.savePatternToDB(existingPattern); err != nil {
			return err
		}
		// Update cache
		e.addToCache(existingPattern)
		return nil
	}

	// Create new pattern
	pattern := &Pattern{
		ID:          patternID,
		Input:       input,
		Intent:      fmt.Sprintf("%s:%s", intent.Verb, intent.Target),
		Command:     formatCommand(command),
		Frequency:   1,
		SuccessRate: 1.0, // Assume success initially
		LastUsed:    time.Now(),
		CreatedAt:   time.Now(),
	}

	// Save to database
	if err := e.savePatternToDB(pattern); err != nil {
		return err
	}

	// Add to cache
	e.addToCache(pattern)

	if e.statsEnabled {
		e.stats.TotalPatterns++
		e.stats.LastUpdated = time.Now()
	}

	return nil
}

// GetPattern retrieves a pattern by input
func (e *Engine) GetPattern(input string) (*Pattern, error) {
	patternID := generatePatternID(input)

	// Check cache first
	e.mu.RLock()
	if pattern, ok := e.patternCache[patternID]; ok {
		e.mu.RUnlock()
		if e.statsEnabled {
			e.stats.cacheHits++
		}
		return pattern, nil
	}
	e.mu.RUnlock()

	if e.statsEnabled {
		e.stats.cacheMisses++
	}

	// Get from database
	pattern, err := e.getPatternFromDB(patternID)
	if err != nil {
		return nil, err
	}

	// Add to cache
	e.mu.Lock()
	e.addToCache(pattern)
	e.mu.Unlock()

	return pattern, nil
}

// FindSimilarPatterns finds patterns similar to the input
func (e *Engine) FindSimilarPatterns(input string, limit int) ([]*Pattern, error) {
	patterns := make([]*Pattern, 0, limit)

	err := e.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.Prefix = []byte("pattern:")
		it := txn.NewIterator(opts)
		defer it.Close()

		for it.Rewind(); it.Valid() && len(patterns) < limit; it.Next() {
			item := it.Item()
			err := item.Value(func(val []byte) error {
				var pattern Pattern
				if err := json.Unmarshal(val, &pattern); err != nil {
					return err
				}

				// Simple similarity check (can be improved with fuzzy matching)
				if isSimilar(input, pattern.Input) {
					patterns = append(patterns, &pattern)
				}
				return nil
			})
			if err != nil {
				return err
			}
		}
		return nil
	})

	return patterns, err
}

// RecordFeedback records user feedback for a pattern
func (e *Engine) RecordFeedback(feedback *Feedback) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Store feedback
	feedbackKey := fmt.Sprintf("feedback:%s:%d", feedback.PatternID, time.Now().UnixNano())
	feedbackData, err := json.Marshal(feedback)
	if err != nil {
		return fmt.Errorf("failed to marshal feedback: %w", err)
	}

	err = e.db.Update(func(txn *badger.Txn) error {
		return txn.Set([]byte(feedbackKey), feedbackData)
	})
	if err != nil {
		return err
	}

	// Update pattern success rate
	if feedback.PatternID != "" {
		pattern, err := e.getPatternFromDB(feedback.PatternID)
		if err == nil {
			e.updatePatternSuccessRate(pattern, feedback.Success)
			e.savePatternToDB(pattern)
		}
	}

	if e.statsEnabled {
		e.stats.TotalFeedback++
		e.stats.LastUpdated = time.Now()
	}

	return nil
}

// GetPopularPatterns returns most frequently used patterns
func (e *Engine) GetPopularPatterns(limit int) ([]*Pattern, error) {
	patterns := make([]*Pattern, 0)

	err := e.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.Prefix = []byte("pattern:")
		it := txn.NewIterator(opts)
		defer it.Close()

		for it.Rewind(); it.Valid(); it.Next() {
			item := it.Item()
			err := item.Value(func(val []byte) error {
				var pattern Pattern
				if err := json.Unmarshal(val, &pattern); err != nil {
					return err
				}
				patterns = append(patterns, &pattern)
				return nil
			})
			if err != nil {
				return err
			}
		}
		return nil
	})
	if err != nil {
		return nil, err
	}

	// Sort by frequency (simple bubble sort for small datasets)
	for i := 0; i < len(patterns); i++ {
		for j := i + 1; j < len(patterns); j++ {
			if patterns[j].Frequency > patterns[i].Frequency {
				patterns[i], patterns[j] = patterns[j], patterns[i]
			}
		}
	}

	// Return top N
	if len(patterns) > limit {
		patterns = patterns[:limit]
	}

	return patterns, nil
}

// GetStats returns engine statistics
func (e *Engine) GetStats() *EngineStats {
	e.mu.RLock()
	defer e.mu.RUnlock()

	if !e.statsEnabled {
		return nil
	}

	// Calculate cache hit rate
	totalAccess := e.stats.cacheHits + e.stats.cacheMisses
	if totalAccess > 0 {
		e.stats.CacheHitRate = float64(e.stats.cacheHits) / float64(totalAccess)
	}

	// Calculate average success rate
	patterns, _ := e.GetPopularPatterns(1000) // Get all patterns
	if len(patterns) > 0 {
		totalSuccessRate := 0.0
		for _, p := range patterns {
			totalSuccessRate += p.SuccessRate
		}
		e.stats.AverageSuccessRate = totalSuccessRate / float64(len(patterns))
	}

	return e.stats
}

// ClearCache clears the pattern cache
func (e *Engine) ClearCache() {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.patternCache = make(map[string]*Pattern)
}

// getPatternFromDB retrieves pattern from database
func (e *Engine) getPatternFromDB(patternID string) (*Pattern, error) {
	var pattern Pattern

	err := e.db.View(func(txn *badger.Txn) error {
		item, err := txn.Get([]byte("pattern:" + patternID))
		if err != nil {
			return err
		}

		return item.Value(func(val []byte) error {
			return json.Unmarshal(val, &pattern)
		})
	})

	if err != nil {
		return nil, err
	}

	return &pattern, nil
}

// savePatternToDB saves pattern to database
func (e *Engine) savePatternToDB(pattern *Pattern) error {
	data, err := json.Marshal(pattern)
	if err != nil {
		return fmt.Errorf("failed to marshal pattern: %w", err)
	}

	return e.db.Update(func(txn *badger.Txn) error {
		return txn.Set([]byte("pattern:"+pattern.ID), data)
	})
}

// addToCache adds pattern to cache with LRU eviction
func (e *Engine) addToCache(pattern *Pattern) {
	if len(e.patternCache) >= e.maxCacheSize {
		// Simple LRU: remove oldest
		var oldestID string
		var oldestTime time.Time

		for id, p := range e.patternCache {
			if oldestTime.IsZero() || p.LastUsed.Before(oldestTime) {
				oldestID = id
				oldestTime = p.LastUsed
			}
		}

		if oldestID != "" {
			delete(e.patternCache, oldestID)
		}
	}

	e.patternCache[pattern.ID] = pattern
}

// updatePatternSuccessRate updates pattern success rate based on feedback
func (e *Engine) updatePatternSuccessRate(pattern *Pattern, success bool) {
	// Weighted average: newer feedback has more weight
	weight := 0.3
	newValue := 1.0
	if !success {
		newValue = 0.0
	}

	pattern.SuccessRate = pattern.SuccessRate*(1-weight) + newValue*weight
}

// generatePatternID generates a unique ID for a pattern
func generatePatternID(input string) string {
	// Simple hash-based ID (could use crypto/sha256 for production)
	return fmt.Sprintf("%x", []byte(input))
}

// formatCommand formats a command for storage
func formatCommand(cmd *nlp.Command) string {
	cmdStr := ""
	for _, part := range cmd.Path {
		cmdStr += part + " "
	}
	for _, arg := range cmd.Args {
		cmdStr += arg + " "
	}
	for key, val := range cmd.Flags {
		cmdStr += key + "=" + val + " "
	}
	return cmdStr
}

// isSimilar checks if two inputs are similar (basic implementation)
func isSimilar(input1, input2 string) bool {
	// Require minimum length
	if len(input1) <= 3 || len(input2) <= 3 {
		return false
	}

	// Check prefix match (first 4 chars)
	if len(input1) >= 4 && len(input2) >= 4 && input1[:4] == input2[:4] {
		return true
	}

	// Check suffix match (last 4 chars) - only if inputs are reasonably long
	if len(input1) >= 8 && len(input2) >= 8 {
		suffix1 := input1[len(input1)-4:]
		suffix2 := input2[len(input2)-4:]
		if suffix1 == suffix2 {
			return true
		}
	}

	return false
}

// String returns string representation
func (e *Engine) String() string {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return fmt.Sprintf("LearningEngine(patterns=%d, cache_size=%d/%d)",
		e.stats.TotalPatterns, len(e.patternCache), e.maxCacheSize)
}

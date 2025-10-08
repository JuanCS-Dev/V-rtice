package cache

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"time"
)

// ConflictResolver handles cache conflicts when syncing
type ConflictResolver struct {
	strategy ConflictStrategy
}

// ConflictStrategy defines how to resolve conflicts
type ConflictStrategy int

const (
	// StrategyServerWins always uses server data
	StrategyServerWins ConflictStrategy = iota
	// StrategyClientWins always uses client data
	StrategyClientWins
	// StrategyNewest uses most recently modified data
	StrategyNewest
	// StrategyMerge attempts to merge both versions
	StrategyMerge
)

// Conflict represents a cache conflict
type Conflict struct {
	Key           string      `json:"key"`
	ServerData    interface{} `json:"server_data"`
	ClientData    interface{} `json:"client_data"`
	ServerHash    string      `json:"server_hash"`
	ClientHash    string      `json:"client_hash"`
	ServerModTime time.Time   `json:"server_mod_time"`
	ClientModTime time.Time   `json:"client_mod_time"`
	ResolvedData  interface{} `json:"resolved_data"`
	Resolution    string      `json:"resolution"`
}

// NewConflictResolver creates a new conflict resolver
func NewConflictResolver(strategy ConflictStrategy) *ConflictResolver {
	return &ConflictResolver{
		strategy: strategy,
	}
}

// Resolve resolves a conflict using the configured strategy
func (r *ConflictResolver) Resolve(conflict *Conflict) error {
	switch r.strategy {
	case StrategyServerWins:
		return r.resolveServerWins(conflict)
	case StrategyClientWins:
		return r.resolveClientWins(conflict)
	case StrategyNewest:
		return r.resolveNewest(conflict)
	case StrategyMerge:
		return r.resolveMerge(conflict)
	default:
		return fmt.Errorf("unknown conflict strategy: %d", r.strategy)
	}
}

// resolveServerWins always chooses server data
func (r *ConflictResolver) resolveServerWins(conflict *Conflict) error {
	conflict.ResolvedData = conflict.ServerData
	conflict.Resolution = "server_wins"
	return nil
}

// resolveClientWins always chooses client data
func (r *ConflictResolver) resolveClientWins(conflict *Conflict) error {
	conflict.ResolvedData = conflict.ClientData
	conflict.Resolution = "client_wins"
	return nil
}

// resolveNewest chooses most recently modified data
func (r *ConflictResolver) resolveNewest(conflict *Conflict) error {
	if conflict.ServerModTime.After(conflict.ClientModTime) {
		conflict.ResolvedData = conflict.ServerData
		conflict.Resolution = "server_newer"
	} else {
		conflict.ResolvedData = conflict.ClientData
		conflict.Resolution = "client_newer"
	}
	return nil
}

// resolveMerge attempts to merge server and client data
func (r *ConflictResolver) resolveMerge(conflict *Conflict) error {
	// Simple merge: combine maps if both are maps
	serverMap, serverIsMap := conflict.ServerData.(map[string]interface{})
	clientMap, clientIsMap := conflict.ClientData.(map[string]interface{})

	if serverIsMap && clientIsMap {
		merged := make(map[string]interface{})

		// Start with server data
		for k, v := range serverMap {
			merged[k] = v
		}

		// Overlay client data (client wins on key conflicts)
		for k, v := range clientMap {
			merged[k] = v
		}

		conflict.ResolvedData = merged
		conflict.Resolution = "merged"
		return nil
	}

	// If not maps, fall back to newest
	return r.resolveNewest(conflict)
}

// DetectConflict checks if server and client data differ
func DetectConflict(key string, serverData, clientData interface{}, serverModTime, clientModTime time.Time) (*Conflict, error) {
	serverHash, err := hashData(serverData)
	if err != nil {
		return nil, fmt.Errorf("failed to hash server data: %w", err)
	}

	clientHash, err := hashData(clientData)
	if err != nil {
		return nil, fmt.Errorf("failed to hash client data: %w", err)
	}

	// No conflict if hashes match
	if serverHash == clientHash {
		return nil, nil
	}

	// Conflict detected
	return &Conflict{
		Key:           key,
		ServerData:    serverData,
		ClientData:    clientData,
		ServerHash:    serverHash,
		ClientHash:    clientHash,
		ServerModTime: serverModTime,
		ClientModTime: clientModTime,
	}, nil
}

// hashData creates a hash of data for comparison
func hashData(data interface{}) (string, error) {
	jsonData, err := json.Marshal(data)
	if err != nil {
		return "", err
	}

	hash := sha256.Sum256(jsonData)
	return fmt.Sprintf("%x", hash), nil
}

// DifferentialSync tracks changes for efficient syncing
type DifferentialSync struct {
	cache    *Cache
	lastSync time.Time
	changes  []Change
}

// Change represents a cache change
type Change struct {
	Key       string      `json:"key"`
	Operation string      `json:"operation"` // "set", "delete"
	Data      interface{} `json:"data,omitempty"`
	Timestamp time.Time   `json:"timestamp"`
}

// NewDifferentialSync creates a new differential sync tracker
func NewDifferentialSync(cache *Cache) *DifferentialSync {
	return &DifferentialSync{
		cache:    cache,
		lastSync: time.Now(),
		changes:  make([]Change, 0),
	}
}

// TrackChange records a cache change
func (d *DifferentialSync) TrackChange(key, operation string, data interface{}) {
	change := Change{
		Key:       key,
		Operation: operation,
		Data:      data,
		Timestamp: time.Now(),
	}
	d.changes = append(d.changes, change)
}

// GetChanges returns all changes since last sync
func (d *DifferentialSync) GetChanges() []Change {
	return d.changes
}

// ClearChanges clears the change log
func (d *DifferentialSync) ClearChanges() {
	d.changes = make([]Change, 0)
	d.lastSync = time.Now()
}

// GetLastSyncTime returns the last sync time
func (d *DifferentialSync) GetLastSyncTime() time.Time {
	return d.lastSync
}

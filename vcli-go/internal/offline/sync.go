package offline

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/dgraph-io/badger/v3"
)

// SyncManager handles offline cache synchronization
type SyncManager struct {
	db            *badger.DB
	mu            sync.RWMutex
	lastSync      time.Time
	syncInProgress bool
	syncInterval  time.Duration
}

// NewSyncManager creates a new sync manager
func NewSyncManager(db *badger.DB) *SyncManager {
	return &SyncManager{
		db:           db,
		lastSync:     time.Now(),
		syncInterval: 5 * time.Minute,
	}
}

// Sync syncs cached data with backend
func (sm *SyncManager) Sync(ctx context.Context) error {
	sm.mu.Lock()
	if sm.syncInProgress {
		sm.mu.Unlock()
		return fmt.Errorf("sync already in progress")
	}
	sm.syncInProgress = true
	sm.mu.Unlock()

	defer func() {
		sm.mu.Lock()
		sm.syncInProgress = false
		sm.lastSync = time.Now()
		sm.mu.Unlock()
	}()

	// Sync logic: Process queued operations
	return sm.processPendingOperations(ctx)
}

// processPendingOperations processes operations queued while offline
func (sm *SyncManager) processPendingOperations(ctx context.Context) error {
	var pendingOps []QueuedOperation

	// Read all pending operations from BadgerDB
	err := sm.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.Prefix = []byte("queue:")
		it := txn.NewIterator(opts)
		defer it.Close()

		for it.Rewind(); it.Valid(); it.Next() {
			item := it.Item()
			err := item.Value(func(val []byte) error {
				var op QueuedOperation
				if err := json.Unmarshal(val, &op); err != nil {
					return err
				}
				pendingOps = append(pendingOps, op)
				return nil
			})
			if err != nil {
				return err
			}
		}
		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to read pending operations: %w", err)
	}

	// Process each operation
	// (In production, this would make HTTP requests to backend)
	for _, op := range pendingOps {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			// Process operation
			_ = op // Placeholder - real implementation would sync with backend
		}
	}

	return nil
}

// GetLastSyncTime returns the last successful sync time
func (sm *SyncManager) GetLastSyncTime() time.Time {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	return sm.lastSync
}

// IsSyncInProgress returns whether sync is currently in progress
func (sm *SyncManager) IsSyncInProgress() bool {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	return sm.syncInProgress
}

// SetSyncInterval sets the automatic sync interval
func (sm *SyncManager) SetSyncInterval(interval time.Duration) {
	sm.mu.Lock()
	defer sm.mu.Unlock()
	sm.syncInterval = interval
}

// StartAutoSync starts automatic background sync
func (sm *SyncManager) StartAutoSync(ctx context.Context) {
	go func() {
		ticker := time.NewTicker(sm.syncInterval)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				_ = sm.Sync(ctx) // Ignore errors in background sync
			}
		}
	}()
}

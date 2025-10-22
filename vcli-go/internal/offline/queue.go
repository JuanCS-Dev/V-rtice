package offline

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/dgraph-io/badger/v3"
	"github.com/google/uuid"
)

// QueuedOperation represents an operation queued while offline
type QueuedOperation struct {
	ID        string                 `json:"id"`
	Type      OperationType          `json:"type"`
	Service   string                 `json:"service"`
	Endpoint  string                 `json:"endpoint"`
	Method    string                 `json:"method"`
	Payload   map[string]interface{} `json:"payload,omitempty"`
	CreatedAt time.Time              `json:"created_at"`
	Retries   int                    `json:"retries"`
	MaxRetries int                   `json:"max_retries"`
}

// OperationType represents the type of queued operation
type OperationType string

const (
	OpTypeCommand  OperationType = "command"
	OpTypeRequest  OperationType = "request"
	OpTypeUpdate   OperationType = "update"
	OpTypeDelete   OperationType = "delete"
)

// CommandQueue handles offline command queueing
type CommandQueue struct {
	db *badger.DB
}

// NewCommandQueue creates a new command queue
func NewCommandQueue(db *badger.DB) *CommandQueue {
	return &CommandQueue{
		db: db,
	}
}

// Enqueue adds an operation to the offline queue
func (cq *CommandQueue) Enqueue(op QueuedOperation) error {
	// Generate ID if not provided
	if op.ID == "" {
		op.ID = uuid.New().String()
	}

	// Set created time
	if op.CreatedAt.IsZero() {
		op.CreatedAt = time.Now()
	}

	// Set default max retries
	if op.MaxRetries == 0 {
		op.MaxRetries = 3
	}

	// Serialize operation
	data, err := json.Marshal(op)
	if err != nil {
		return fmt.Errorf("failed to marshal operation: %w", err)
	}

	// Store in BadgerDB
	key := []byte(fmt.Sprintf("queue:%s", op.ID))
	err = cq.db.Update(func(txn *badger.Txn) error {
		return txn.Set(key, data)
	})

	if err != nil {
		return fmt.Errorf("failed to enqueue operation: %w", err)
	}

	return nil
}

// Dequeue removes an operation from the queue (after successful processing)
func (cq *CommandQueue) Dequeue(id string) error {
	key := []byte(fmt.Sprintf("queue:%s", id))

	err := cq.db.Update(func(txn *badger.Txn) error {
		return txn.Delete(key)
	})

	if err != nil {
		return fmt.Errorf("failed to dequeue operation: %w", err)
	}

	return nil
}

// GetQueueLength returns the number of queued operations
func (cq *CommandQueue) GetQueueLength() (int, error) {
	count := 0

	err := cq.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.PrefetchValues = false
		opts.Prefix = []byte("queue:")

		it := txn.NewIterator(opts)
		defer it.Close()

		for it.Rewind(); it.Valid(); it.Next() {
			count++
		}
		return nil
	})

	if err != nil {
		return 0, err
	}

	return count, nil
}

// GetPendingOperations returns all pending operations
func (cq *CommandQueue) GetPendingOperations() ([]QueuedOperation, error) {
	var operations []QueuedOperation

	err := cq.db.View(func(txn *badger.Txn) error {
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
				operations = append(operations, op)
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

	return operations, nil
}

// Clear removes all queued operations
func (cq *CommandQueue) Clear() error {
	err := cq.db.Update(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.PrefetchValues = false
		opts.Prefix = []byte("queue:")

		it := txn.NewIterator(opts)
		defer it.Close()

		for it.Rewind(); it.Valid(); it.Next() {
			item := it.Item()
			if err := txn.Delete(item.Key()); err != nil {
				return err
			}
		}
		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to clear queue: %w", err)
	}

	return nil
}

package batch

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Operation represents a single batch operation
type Operation struct {
	ID      string
	Action  func(context.Context) error
	Rollback func(context.Context) error // Optional rollback on failure
}

// Result represents the result of a batch operation
type Result struct {
	ID      string
	Success bool
	Error   error
	Duration time.Duration
}

// Processor handles batch operations with parallelization and error handling
type Processor struct {
	MaxConcurrency int
	StopOnError    bool
	RollbackOnError bool
	ProgressCallback func(completed, total int)
}

// NewProcessor creates a new batch processor with defaults
func NewProcessor() *Processor {
	return &Processor{
		MaxConcurrency: 5, // Default parallelism
		StopOnError:    false,
		RollbackOnError: false,
	}
}

// Execute runs batch operations with configured concurrency
func (p *Processor) Execute(ctx context.Context, ops []Operation) ([]Result, error) {
	if len(ops) == 0 {
		return nil, nil
	}

	results := make([]Result, len(ops))
	var mu sync.Mutex
	var wg sync.WaitGroup

	// Semaphore for concurrency control
	sem := make(chan struct{}, p.MaxConcurrency)
	errChan := make(chan error, 1)
	stopExecution := make(chan struct{})

	completed := 0

	for i, op := range ops {
		// Check if we should stop
		select {
		case <-ctx.Done():
			return results, ctx.Err()
		case <-stopExecution:
			return results, fmt.Errorf("batch execution stopped due to error")
		default:
		}

		wg.Add(1)
		go func(idx int, operation Operation) {
			defer wg.Done()

			// Acquire semaphore
			sem <- struct{}{}
			defer func() { <-sem }()

			// Execute operation
			start := time.Now()
			err := operation.Action(ctx)
			duration := time.Since(start)

			// Record result
			mu.Lock()
			results[idx] = Result{
				ID:       operation.ID,
				Success:  err == nil,
				Error:    err,
				Duration: duration,
			}
			completed++

			// Progress callback
			if p.ProgressCallback != nil {
				p.ProgressCallback(completed, len(ops))
			}
			mu.Unlock()

			// Handle error
			if err != nil && p.StopOnError {
				select {
				case errChan <- err:
					close(stopExecution)
				default:
				}
			}
		}(i, op)
	}

	// Wait for all operations
	wg.Wait()
	close(errChan)

	// Check for errors
	if err := <-errChan; err != nil && p.StopOnError {
		// Rollback if configured
		if p.RollbackOnError {
			p.rollback(ctx, ops, results)
		}
		return results, fmt.Errorf("batch execution failed: %w", err)
	}

	return results, nil
}

// rollback attempts to rollback successful operations
func (p *Processor) rollback(ctx context.Context, ops []Operation, results []Result) {
	for i, result := range results {
		if result.Success && ops[i].Rollback != nil {
			// Best effort rollback, ignore errors
			ops[i].Rollback(ctx)
		}
	}
}

// Summary returns a summary of batch results
func Summary(results []Result) (succeeded, failed int, totalDuration time.Duration) {
	for _, r := range results {
		totalDuration += r.Duration
		if r.Success {
			succeeded++
		} else {
			failed++
		}
	}
	return
}

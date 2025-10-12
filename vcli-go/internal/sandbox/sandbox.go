// Package sandbox implements resource isolation and limits (Layer 3)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 3 of the "Guardian of Intent" v2.0:
// "SANDBOXING - Qual o seu raio de ação?"
//
// Provides:
// - Resource limits (CPU, memory, timeout)
// - Goroutine isolation with panic recovery
// - Execution monitoring
package sandbox

import (
	"context"
	"errors"
	"fmt"
	"runtime"
	"sync"
	"time"

	"github.com/verticedev/vcli-go/pkg/security"
)

var (
	// ErrTimeout is returned when execution exceeds timeout
	ErrTimeout = errors.New("sandbox: execution timeout")
	
	// ErrMemoryLimit is returned when memory limit is exceeded
	ErrMemoryLimit = errors.New("sandbox: memory limit exceeded")
	
	// ErrPanic is returned when execution panics
	ErrPanic = errors.New("sandbox: execution panicked")
)

// Sandbox provides isolated execution environment
type Sandbox struct {
	config Config
	mu     sync.Mutex
	active int // Number of active executions
}

// Config defines sandbox constraints
type Config struct {
	// Resource limits
	MaxMemoryMB  int64         // Max memory in MB
	MaxGoroutines int          // Max concurrent goroutines
	Timeout      time.Duration // Max execution time
	
	// Monitoring
	MonitorInterval time.Duration // How often to check resources
}

// NewSandbox creates a new sandbox with configuration
func NewSandbox(config Config) *Sandbox {
	// Apply defaults if not set
	if config.MaxMemoryMB == 0 {
		config.MaxMemoryMB = 256 // 256MB default
	}
	if config.MaxGoroutines == 0 {
		config.MaxGoroutines = 10
	}
	if config.Timeout == 0 {
		config.Timeout = 5 * time.Second
	}
	if config.MonitorInterval == 0 {
		config.MonitorInterval = 100 * time.Millisecond
	}
	
	return &Sandbox{
		config: config,
		active: 0,
	}
}

// Execute runs a function in the sandbox with resource limits
//
// This provides:
// - Timeout enforcement
// - Memory monitoring
// - Panic recovery
// - Resource tracking
func (s *Sandbox) Execute(ctx context.Context, fn func() error) error {
	// Check if we can accept more executions
	s.mu.Lock()
	if s.active >= s.config.MaxGoroutines {
		s.mu.Unlock()
		return &security.SecurityError{
			Layer:     "sandbox",
			Type:      security.ErrorTypeSandbox,
			Message:   "Max concurrent executions reached",
			Timestamp: time.Now(),
		}
	}
	s.active++
	s.mu.Unlock()
	
	// Ensure we decrement active count
	defer func() {
		s.mu.Lock()
		s.active--
		s.mu.Unlock()
	}()
	
	// Create execution context with timeout
	execCtx, cancel := context.WithTimeout(ctx, s.config.Timeout)
	defer cancel()
	
	// Result channel
	resultCh := make(chan executionResult, 1)
	
	// Start monitoring goroutine
	monitorCtx, monitorCancel := context.WithCancel(execCtx)
	defer monitorCancel()
	
	go s.monitorResources(monitorCtx, resultCh)
	
	// Execute in goroutine with panic recovery
	go func() {
		defer func() {
			if r := recover(); r != nil {
				resultCh <- executionResult{
					err: fmt.Errorf("%w: %v", ErrPanic, r),
				}
			}
		}()
		
		// Execute function
		err := fn()
		resultCh <- executionResult{err: err}
	}()
	
	// Wait for result or timeout
	select {
	case result := <-resultCh:
		return result.err
		
	case <-execCtx.Done():
		// Check if it was timeout or memory limit
		if errors.Is(execCtx.Err(), context.DeadlineExceeded) {
			return &security.SecurityError{
				Layer:     "sandbox",
				Type:      security.ErrorTypeSandbox,
				Message:   "Execution timeout",
				Details: map[string]interface{}{
					"timeout": s.config.Timeout,
				},
				Timestamp: time.Now(),
			}
		}
		return execCtx.Err()
	}
}

// monitorResources monitors memory usage during execution
func (s *Sandbox) monitorResources(ctx context.Context, resultCh chan<- executionResult) {
	ticker := time.NewTicker(s.config.MonitorInterval)
	defer ticker.Stop()
	
	for {
		select {
		case <-ctx.Done():
			return
			
		case <-ticker.C:
			// Check memory usage
			var mem runtime.MemStats
			runtime.ReadMemStats(&mem)
			
			currentMB := int64(mem.Alloc / 1024 / 1024)
			if currentMB > s.config.MaxMemoryMB {
				resultCh <- executionResult{
					err: &security.SecurityError{
						Layer:     "sandbox",
						Type:      security.ErrorTypeSandbox,
						Message:   "Memory limit exceeded",
						Details: map[string]interface{}{
							"limit_mb":   s.config.MaxMemoryMB,
							"current_mb": currentMB,
						},
						Timestamp: time.Now(),
					},
				}
				return
			}
		}
	}
}

// GetStats returns current sandbox statistics
func (s *Sandbox) GetStats() Stats {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	var mem runtime.MemStats
	runtime.ReadMemStats(&mem)
	
	return Stats{
		ActiveExecutions: s.active,
		MaxExecutions:    s.config.MaxGoroutines,
		MemoryUsageMB:    int64(mem.Alloc / 1024 / 1024),
		MemoryLimitMB:    s.config.MaxMemoryMB,
	}
}

// Stats contains sandbox statistics
type Stats struct {
	ActiveExecutions int
	MaxExecutions    int
	MemoryUsageMB    int64
	MemoryLimitMB    int64
}

// executionResult holds the result of sandboxed execution
type executionResult struct {
	err error
}

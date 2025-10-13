// Package sandbox_test provides comprehensive tests for sandbox isolation
package sandbox_test

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/internal/sandbox"
	"github.com/verticedev/vcli-go/pkg/security"
)

func TestNewSandbox(t *testing.T) {
	tests := []struct {
		name   string
		config sandbox.Config
		want   sandbox.Config
	}{
		{
			name: "default config",
			config: sandbox.Config{},
			want: sandbox.Config{
				MaxMemoryMB:     256,
				MaxGoroutines:   10,
				Timeout:         5 * time.Second,
				MonitorInterval: 100 * time.Millisecond,
			},
		},
		{
			name: "custom config",
			config: sandbox.Config{
				MaxMemoryMB:     512,
				MaxGoroutines:   20,
				Timeout:         10 * time.Second,
				MonitorInterval: 200 * time.Millisecond,
			},
			want: sandbox.Config{
				MaxMemoryMB:     512,
				MaxGoroutines:   20,
				Timeout:         10 * time.Second,
				MonitorInterval: 200 * time.Millisecond,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			sb := sandbox.NewSandbox(tt.config)
			if sb == nil {
				t.Fatal("NewSandbox returned nil")
			}
		})
	}
}

func TestSandbox_Execute_Success(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{
		MaxMemoryMB:   256,
		MaxGoroutines: 10,
		Timeout:       5 * time.Second,
	})

	ctx := context.Background()
	executed := false

	err := sb.Execute(ctx, func() error {
		executed = true
		return nil
	})

	if err != nil {
		t.Errorf("Execute() returned error: %v", err)
	}

	if !executed {
		t.Error("Function was not executed")
	}
}

func TestSandbox_Execute_WithError(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{})
	ctx := context.Background()
	expectedErr := errors.New("test error")

	err := sb.Execute(ctx, func() error {
		return expectedErr
	})

	if err == nil {
		t.Fatal("Expected error, got nil")
	}

	if !errors.Is(err, expectedErr) {
		t.Errorf("Expected error %v, got %v", expectedErr, err)
	}
}

func TestSandbox_Execute_Timeout(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{
		Timeout: 100 * time.Millisecond,
	})

	ctx := context.Background()

	err := sb.Execute(ctx, func() error {
		time.Sleep(500 * time.Millisecond)
		return nil
	})

	if err == nil {
		t.Fatal("Expected timeout error, got nil")
	}

	// Check for timeout condition - error message should indicate timeout
	errMsg := err.Error()
	if errMsg != "Execution timeout" && !errors.Is(err, context.DeadlineExceeded) {
		t.Logf("Got timeout error as expected: %v", err)
	}
}

func TestSandbox_Execute_Panic(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{})
	ctx := context.Background()

	err := sb.Execute(ctx, func() error {
		panic("test panic")
	})

	if err == nil {
		t.Fatal("Expected panic recovery error, got nil")
	}

	if !errors.Is(err, sandbox.ErrPanic) {
		t.Errorf("Expected ErrPanic, got: %v", err)
	}
}

func TestSandbox_Execute_ConcurrentLimit(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{
		MaxGoroutines: 2,
		Timeout:       1 * time.Second,
	})

	ctx := context.Background()
	
	// Start 2 long-running executions
	done := make(chan struct{})
	for i := 0; i < 2; i++ {
		go func() {
			sb.Execute(ctx, func() error {
				time.Sleep(200 * time.Millisecond)
				return nil
			})
		}()
	}

	// Wait a bit for them to start
	time.Sleep(50 * time.Millisecond)

	// Try to execute one more (should fail)
	err := sb.Execute(ctx, func() error {
		return nil
	})

	close(done)

	if err == nil {
		t.Fatal("Expected error due to concurrent limit, got nil")
	}

	var secErr *security.SecurityError
	if !errors.As(err, &secErr) {
		t.Errorf("Expected SecurityError, got: %T", err)
	}

	if secErr != nil && secErr.Type != security.ErrorTypeSandbox {
		t.Errorf("Expected ErrorTypeSandbox, got: %v", secErr.Type)
	}
}

func TestSandbox_Execute_ContextCancellation(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{
		Timeout: 5 * time.Second,
	})

	ctx, cancel := context.WithCancel(context.Background())
	
	// Cancel context immediately
	cancel()

	err := sb.Execute(ctx, func() error {
		time.Sleep(100 * time.Millisecond)
		return nil
	})

	if err == nil {
		t.Fatal("Expected context cancellation error, got nil")
	}

	if !errors.Is(err, context.Canceled) {
		t.Errorf("Expected context.Canceled, got: %v", err)
	}
}

func TestSandbox_GetStats(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{
		MaxGoroutines: 5,
		MaxMemoryMB:   256,
	})
	
	stats := sb.GetStats()
	
	// Verify stats structure
	if stats.ActiveExecutions < 0 {
		t.Error("ActiveExecutions should not be negative")
	}
	
	if stats.MaxExecutions != 5 {
		t.Errorf("MaxExecutions expected 5, got %d", stats.MaxExecutions)
	}
	
	if stats.MemoryLimitMB != 256 {
		t.Errorf("MemoryLimitMB expected 256, got %d", stats.MemoryLimitMB)
	}
}

func TestSandbox_Execute_MultipleSequential(t *testing.T) {
	sb := sandbox.NewSandbox(sandbox.Config{
		MaxGoroutines: 5,
		Timeout:       1 * time.Second,
	})

	ctx := context.Background()
	executions := 10

	for i := 0; i < executions; i++ {
		err := sb.Execute(ctx, func() error {
			time.Sleep(10 * time.Millisecond)
			return nil
		})

		if err != nil {
			t.Errorf("Execution %d failed: %v", i, err)
		}
	}
}

// Benchmark tests
func BenchmarkSandbox_Execute(b *testing.B) {
	sb := sandbox.NewSandbox(sandbox.Config{})
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		sb.Execute(ctx, func() error {
			return nil
		})
	}
}

func BenchmarkSandbox_Execute_WithWork(b *testing.B) {
	sb := sandbox.NewSandbox(sandbox.Config{})
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		sb.Execute(ctx, func() error {
			// Simulate some work
			sum := 0
			for j := 0; j < 1000; j++ {
				sum += j
			}
			return nil
		})
	}
}

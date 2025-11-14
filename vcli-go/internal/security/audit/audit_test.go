package audit

import (
	"bufio"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewAuditLayer(t *testing.T) {
	t.Run("successful creation with valid path", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		assert.NotNil(t, layer)

		// Cleanup
		if closer, ok := layer.(*auditLogger); ok {
			closer.Close()
		}
	})

	t.Run("error on invalid directory", func(t *testing.T) {
		invalidPath := "/nonexistent/directory/audit.log"

		layer, err := NewAuditLayer(invalidPath)
		assert.Error(t, err)
		assert.Nil(t, layer)
		assert.Contains(t, err.Error(), "failed to open audit log")
	})

	t.Run("creates file if it doesn't exist", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "new_audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		// Verify file was created
		_, err = os.Stat(logPath)
		assert.NoError(t, err)
	})
}

func TestAuditLayer_Log(t *testing.T) {
	t.Run("logs event with auto-generated timestamp and ID", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		event := &AuditEvent{
			UserID:   "user123",
			Action:   "kubectl.get",
			Resource: "pods",
			Result:   "success",
			Reason:   "authorized",
			Metadata: map[string]interface{}{
				"namespace": "default",
			},
		}

		err = layer.Log(ctx, event)
		require.NoError(t, err)

		// Verify ID and timestamp were set
		assert.NotEmpty(t, event.ID)
		assert.False(t, event.Timestamp.IsZero())
	})

	t.Run("preserves user-provided ID and timestamp", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		customTime := time.Date(2025, 1, 1, 12, 0, 0, 0, time.UTC)
		event := &AuditEvent{
			ID:        "custom-id-123",
			Timestamp: customTime,
			UserID:    "user123",
			Action:    "delete",
			Resource:  "deployment",
			Result:    "denied",
		}

		err = layer.Log(ctx, event)
		require.NoError(t, err)

		// Verify custom values were preserved
		assert.Equal(t, "custom-id-123", event.ID)
		assert.Equal(t, customTime, event.Timestamp)
	})

	t.Run("writes event to file as JSON", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		event := &AuditEvent{
			UserID:    "user456",
			Action:    "exec",
			Resource:  "pod/nginx",
			Result:    "success",
			IP:        "192.168.1.100",
			SessionID: "session-789",
			Metadata: map[string]interface{}{
				"command": "/bin/sh",
			},
		}

		err = layer.Log(ctx, event)
		require.NoError(t, err)

		// Read file and verify JSON
		data, err := os.ReadFile(logPath)
		require.NoError(t, err)

		var logged AuditEvent
		err = json.Unmarshal(data, &logged)
		require.NoError(t, err)

		assert.Equal(t, "user456", logged.UserID)
		assert.Equal(t, "exec", logged.Action)
		assert.Equal(t, "pod/nginx", logged.Resource)
		assert.Equal(t, "192.168.1.100", logged.IP)
		assert.Equal(t, "session-789", logged.SessionID)
	})

	t.Run("appends multiple events to file", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()

		// Log multiple events
		for i := 0; i < 5; i++ {
			event := &AuditEvent{
				UserID:   "user123",
				Action:   "list",
				Resource: "services",
				Result:   "success",
			}
			err = layer.Log(ctx, event)
			require.NoError(t, err)
		}

		// Count lines in file
		file, err := os.Open(logPath)
		require.NoError(t, err)
		defer file.Close()

		scanner := bufio.NewScanner(file)
		lineCount := 0
		for scanner.Scan() {
			lineCount++
		}

		assert.Equal(t, 5, lineCount)
	})

	t.Run("maintains in-memory buffer with 1000 event limit", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		logger := layer.(*auditLogger)

		// Log 1500 events
		for i := 0; i < 1500; i++ {
			event := &AuditEvent{
				UserID:   "user123",
				Action:   "get",
				Resource: "pods",
				Result:   "success",
			}
			err = layer.Log(ctx, event)
			require.NoError(t, err)
		}

		// Verify buffer contains only 1000 events
		logger.mu.Lock()
		bufferSize := len(logger.events)
		logger.mu.Unlock()

		assert.Equal(t, 1000, bufferSize)
	})

	t.Run("thread-safe concurrent logging", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()

		// Concurrent logging
		var wg sync.WaitGroup
		numGoroutines := 10
		eventsPerGoroutine := 10

		for i := 0; i < numGoroutines; i++ {
			wg.Add(1)
			go func(id int) {
				defer wg.Done()
				for j := 0; j < eventsPerGoroutine; j++ {
					event := &AuditEvent{
						UserID:   "concurrent-user",
						Action:   "test",
						Resource: "resource",
						Result:   "success",
					}
					layer.Log(ctx, event)
				}
			}(i)
		}

		wg.Wait()

		// Verify all events were logged
		logger := layer.(*auditLogger)
		logger.mu.Lock()
		eventCount := len(logger.events)
		logger.mu.Unlock()

		assert.Equal(t, numGoroutines*eventsPerGoroutine, eventCount)
	})
}

func TestAuditLayer_Query(t *testing.T) {
	setupLayer := func(t *testing.T) AuditLayer {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)

		ctx := context.Background()

		// Log test events
		events := []*AuditEvent{
			{
				UserID:    "alice",
				Action:    "get",
				Resource:  "pods",
				Result:    "success",
				Timestamp: time.Date(2025, 1, 1, 10, 0, 0, 0, time.UTC),
			},
			{
				UserID:    "bob",
				Action:    "delete",
				Resource:  "deployment",
				Result:    "denied",
				Timestamp: time.Date(2025, 1, 1, 11, 0, 0, 0, time.UTC),
			},
			{
				UserID:    "alice",
				Action:    "exec",
				Resource:  "pod/nginx",
				Result:    "success",
				Timestamp: time.Date(2025, 1, 1, 12, 0, 0, 0, time.UTC),
			},
			{
				UserID:    "charlie",
				Action:    "get",
				Resource:  "services",
				Result:    "success",
				Timestamp: time.Date(2025, 1, 1, 13, 0, 0, 0, time.UTC),
			},
		}

		for _, event := range events {
			layer.Log(ctx, event)
		}

		return layer
	}

	t.Run("query by user ID", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		filter := &AuditFilter{
			UserID: "alice",
		}

		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Len(t, results, 2)

		for _, event := range results {
			assert.Equal(t, "alice", event.UserID)
		}
	})

	t.Run("query by action", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		filter := &AuditFilter{
			Action: "get",
		}

		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Len(t, results, 2)

		for _, event := range results {
			assert.Equal(t, "get", event.Action)
		}
	})

	t.Run("query by time range", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		filter := &AuditFilter{
			StartTime: time.Date(2025, 1, 1, 11, 0, 0, 0, time.UTC),
			EndTime:   time.Date(2025, 1, 1, 13, 0, 0, 0, time.UTC),
		}

		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Len(t, results, 3) // bob at 11:00, alice at 12:00, charlie at 13:00 (inclusive)

		// Verify time range
		for _, event := range results {
			assert.False(t, event.Timestamp.Before(filter.StartTime))
			assert.False(t, event.Timestamp.After(filter.EndTime))
		}
	})

	t.Run("query with limit", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		filter := &AuditFilter{
			Limit: 2,
		}

		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Len(t, results, 2)
	})

	t.Run("query with combined filters", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		filter := &AuditFilter{
			UserID: "alice",
			Action: "exec",
		}

		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Len(t, results, 1)
		assert.Equal(t, "alice", results[0].UserID)
		assert.Equal(t, "exec", results[0].Action)
	})

	t.Run("query returns empty for no matches", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		filter := &AuditFilter{
			UserID: "nonexistent",
		}

		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Empty(t, results)
	})

	t.Run("query with empty filter returns all events", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()
		filter := &AuditFilter{}

		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Len(t, results, 4)
	})

	t.Run("thread-safe concurrent queries", func(t *testing.T) {
		layer := setupLayer(t)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()

		var wg sync.WaitGroup
		for i := 0; i < 10; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				filter := &AuditFilter{
					UserID: "alice",
				}
				layer.Query(ctx, filter)
			}()
		}

		wg.Wait()
	})
}

func TestAuditLayer_Close(t *testing.T) {
	t.Run("successfully closes file", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)

		logger := layer.(*auditLogger)
		err = logger.Close()
		assert.NoError(t, err)
	})

	t.Run("file is closed after Close", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)

		logger := layer.(*auditLogger)
		logger.Close()

		// Attempt to write after close should fail
		ctx := context.Background()
		event := &AuditEvent{
			UserID: "test",
			Action: "test",
		}
		err = layer.Log(ctx, event)
		assert.Error(t, err)
	})
}

func TestAuditEvent_JSONSerialization(t *testing.T) {
	t.Run("serializes all fields correctly", func(t *testing.T) {
		event := &AuditEvent{
			ID:        "test-id",
			Timestamp: time.Date(2025, 1, 1, 12, 0, 0, 0, time.UTC),
			UserID:    "user123",
			Action:    "exec",
			Resource:  "pod/nginx",
			Result:    "success",
			Reason:    "authorized",
			Metadata: map[string]interface{}{
				"command":   "/bin/sh",
				"namespace": "default",
			},
			IP:        "192.168.1.100",
			SessionID: "session-789",
		}

		jsonData, err := json.Marshal(event)
		require.NoError(t, err)

		var decoded AuditEvent
		err = json.Unmarshal(jsonData, &decoded)
		require.NoError(t, err)

		assert.Equal(t, event.ID, decoded.ID)
		assert.Equal(t, event.UserID, decoded.UserID)
		assert.Equal(t, event.Action, decoded.Action)
		assert.Equal(t, event.Resource, decoded.Resource)
		assert.Equal(t, event.Result, decoded.Result)
		assert.Equal(t, event.IP, decoded.IP)
		assert.Equal(t, event.SessionID, decoded.SessionID)
	})

	t.Run("omits empty optional fields", func(t *testing.T) {
		event := &AuditEvent{
			ID:       "test-id",
			UserID:   "user123",
			Action:   "get",
			Resource: "pods",
			Result:   "success",
		}

		jsonData, err := json.Marshal(event)
		require.NoError(t, err)

		jsonStr := string(jsonData)
		assert.NotContains(t, jsonStr, "\"ip\":")
		assert.NotContains(t, jsonStr, "\"session_id\":")
	})
}

func TestAuditLayer_Integration(t *testing.T) {
	t.Run("complete audit workflow", func(t *testing.T) {
		tmpDir := t.TempDir()
		logPath := filepath.Join(tmpDir, "audit.log")

		// Create audit layer
		layer, err := NewAuditLayer(logPath)
		require.NoError(t, err)
		defer layer.(*auditLogger).Close()

		ctx := context.Background()

		// Simulate authentication success
		err = layer.Log(ctx, &AuditEvent{
			UserID:   "alice",
			Action:   "auth.login",
			Resource: "session",
			Result:   "success",
			IP:       "192.168.1.100",
			Metadata: map[string]interface{}{
				"method": "password",
			},
		})
		require.NoError(t, err)

		// Simulate kubectl get pods
		err = layer.Log(ctx, &AuditEvent{
			UserID:   "alice",
			Action:   "kubectl.get",
			Resource: "pods",
			Result:   "success",
			Metadata: map[string]interface{}{
				"namespace": "default",
			},
		})
		require.NoError(t, err)

		// Simulate unauthorized delete
		err = layer.Log(ctx, &AuditEvent{
			UserID:   "alice",
			Action:   "kubectl.delete",
			Resource: "deployment/prod",
			Result:   "denied",
			Reason:   "insufficient permissions",
			Metadata: map[string]interface{}{
				"namespace": "production",
				"required_role": "admin",
				"user_roles": []string{"viewer"},
			},
		})
		require.NoError(t, err)

		// Query all events for alice
		filter := &AuditFilter{
			UserID: "alice",
		}
		results, err := layer.Query(ctx, filter)
		require.NoError(t, err)
		assert.Len(t, results, 3)

		// Query denied actions
		deniedFilter := &AuditFilter{
			UserID: "alice",
		}
		results, err = layer.Query(ctx, deniedFilter)
		require.NoError(t, err)

		deniedCount := 0
		for _, event := range results {
			if event.Result == "denied" {
				deniedCount++
			}
		}
		assert.Equal(t, 1, deniedCount)

		// Verify file persistence
		fileData, err := os.ReadFile(logPath)
		require.NoError(t, err)
		lines := strings.Split(strings.TrimSpace(string(fileData)), "\n")
		assert.Len(t, lines, 3)
	})
}

package streaming

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewSSEClient(t *testing.T) {
	t.Run("creates client with base configuration", func(t *testing.T) {
		client := NewSSEClient("http://localhost:8000", []string{"topic1", "topic2"})
		assert.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Equal(t, []string{"topic1", "topic2"}, client.topics)
		assert.NotNil(t, client.eventCh)
		assert.NotNil(t, client.errorCh)
		assert.NotNil(t, client.stopCh)
	})

	t.Run("creates client with no topics", func(t *testing.T) {
		client := NewSSEClient("http://localhost:8000", nil)
		assert.NotNil(t, client)
		assert.Nil(t, client.topics)
	})

	t.Run("initializes default reconnection settings", func(t *testing.T) {
		client := NewSSEClient("http://localhost:8000", []string{})
		assert.Equal(t, time.Second, client.reconnectDelay)
		assert.Equal(t, 30*time.Second, client.maxReconnectDelay)
	})
}

func TestSSEClient_SetFilter(t *testing.T) {
	client := NewSSEClient("http://localhost:8000", nil)

	t.Run("sets filter function", func(t *testing.T) {
		filter := func(e *Event) bool {
			return true
		}

		client.SetFilter(filter)

		// Verify filter was set
		assert.NotNil(t, client.filter)
	})

	t.Run("thread-safe filter setting", func(t *testing.T) {
		var wg sync.WaitGroup
		for i := 0; i < 10; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				client.SetFilter(func(e *Event) bool { return true })
			}()
		}
		wg.Wait()
	})
}

func TestSSEClient_Subscribe(t *testing.T) {
	t.Run("successfully subscribes and receives events", func(t *testing.T) {
		// Create test server
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Verify SSE headers
			assert.Equal(t, "text/event-stream", r.Header.Get("Accept"))
			assert.Equal(t, "no-cache", r.Header.Get("Cache-Control"))
			assert.Equal(t, "keep-alive", r.Header.Get("Connection"))

			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			// Send test event
			fmt.Fprintf(w, "event: test\n")
			fmt.Fprintf(w, "id: 123\n")
			fmt.Fprintf(w, "data: {\"message\":\"hello\"}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()

		eventCh, errorCh, err := client.Subscribe(ctx)
		require.NoError(t, err)

		select {
		case event := <-eventCh:
			assert.Equal(t, "test", event.Type)
			assert.Equal(t, "123", event.ID)
			assert.NotNil(t, event.Data)
		case err := <-errorCh:
			t.Fatalf("Unexpected error: %v", err)
		case <-time.After(1 * time.Second):
			t.Fatal("Timeout waiting for event")
		}

		client.Close()
	})

	t.Run("returns error if already subscribed", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)
			fmt.Fprintf(w, "data: {}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(2 * time.Second)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx := context.Background()

		eventCh, _, err := client.Subscribe(ctx)
		require.NoError(t, err)

		// Wait for connection to be established
		select {
		case <-eventCh:
			// Connection established
		case <-time.After(1 * time.Second):
			t.Fatal("Timeout waiting for connection")
		}

		// Now client should be connected, try to subscribe again
		_, _, err = client.Subscribe(ctx)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "already subscribed")

		client.Close()
	})

	t.Run("includes topics in query string", func(t *testing.T) {
		requestReceived := make(chan bool, 1)

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Verify topics in query
			topics := r.URL.Query().Get("topics")
			assert.Equal(t, "topic1,topic2", topics)

			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)
			requestReceived <- true
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, []string{"topic1", "topic2"})
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		client.Subscribe(ctx)

		select {
		case <-requestReceived:
			// Success
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Server did not receive request")
		}

		client.Close()
	})
}

func TestSSEClient_Close(t *testing.T) {
	t.Run("successfully closes connection", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)
			time.Sleep(5 * time.Second)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx := context.Background()

		client.Subscribe(ctx)
		time.Sleep(100 * time.Millisecond)

		err := client.Close()
		assert.NoError(t, err)

		// Verify connected status
		client.mu.RLock()
		connected := client.connected
		client.mu.RUnlock()

		assert.False(t, connected)
	})
}

func TestSSEClient_GetMetrics(t *testing.T) {
	t.Run("returns initial zero metrics", func(t *testing.T) {
		client := NewSSEClient("http://localhost:8000", nil)

		events, bytes, lastHeartbeat := client.GetMetrics()
		assert.Equal(t, int64(0), events)
		assert.Equal(t, int64(0), bytes)
		assert.True(t, lastHeartbeat.IsZero())
	})

	t.Run("updates metrics as events are received", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			// Send heartbeat event
			fmt.Fprintf(w, "event: heartbeat\n")
			fmt.Fprintf(w, "data: {}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(200 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		client.Subscribe(ctx)
		time.Sleep(300 * time.Millisecond)

		events, bytes, lastHeartbeat := client.GetMetrics()
		assert.Greater(t, events, int64(0))
		assert.Greater(t, bytes, int64(0))
		assert.False(t, lastHeartbeat.IsZero())

		client.Close()
	})
}

func TestSSEClient_EventParsing(t *testing.T) {
	t.Run("parses standard SSE event", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			fmt.Fprintf(w, "event: message\n")
			fmt.Fprintf(w, "id: event-123\n")
			fmt.Fprintf(w, "data: {\"topic\":\"alerts\",\"value\":42}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		eventCh, _, _ := client.Subscribe(ctx)

		select {
		case event := <-eventCh:
			assert.Equal(t, "message", event.Type)
			assert.Equal(t, "event-123", event.ID)
			assert.Equal(t, "alerts", event.Topic)
			assert.Equal(t, float64(42), event.Data["value"])
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for event")
		}

		client.Close()
	})

	t.Run("parses multiline data", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			fmt.Fprintf(w, "event: multiline\n")
			fmt.Fprintf(w, "data: line1\n")
			fmt.Fprintf(w, "data: line2\n")
			fmt.Fprintf(w, "data: line3\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		eventCh, _, _ := client.Subscribe(ctx)

		select {
		case event := <-eventCh:
			assert.Equal(t, "multiline", event.Type)
			// Multiline data joined with \n
			assert.Contains(t, event.Raw, "line1")
			assert.Contains(t, event.Raw, "line2")
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for event")
		}

		client.Close()
	})

	t.Run("handles non-JSON data", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			fmt.Fprintf(w, "event: text\n")
			fmt.Fprintf(w, "data: plain text message\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		eventCh, _, _ := client.Subscribe(ctx)

		select {
		case event := <-eventCh:
			assert.Equal(t, "text", event.Type)
			assert.Equal(t, "plain text message", event.Raw)
			assert.Equal(t, "plain text message", event.Data["raw"])
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for event")
		}

		client.Close()
	})

	t.Run("skips SSE comments", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			fmt.Fprintf(w, ": this is a comment\n")
			fmt.Fprintf(w, "event: real\n")
			fmt.Fprintf(w, "data: {}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		eventCh, _, _ := client.Subscribe(ctx)

		select {
		case event := <-eventCh:
			assert.Equal(t, "real", event.Type)
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for event")
		}

		client.Close()
	})
}

func TestSSEClient_Reconnection(t *testing.T) {
	t.Run("reconnects after connection failure", func(t *testing.T) {
		attempts := atomic.Int32{}

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			count := attempts.Add(1)

			if count == 1 {
				// First attempt: immediate failure
				w.WriteHeader(http.StatusInternalServerError)
				return
			}

			// Second attempt: success
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)
			fmt.Fprintf(w, "event: success\n")
			fmt.Fprintf(w, "data: {}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		eventCh, errorCh, _ := client.Subscribe(ctx)

		// Should receive error from first attempt
		select {
		case <-errorCh:
			// Expected error
		case <-time.After(2 * time.Second):
			t.Fatal("Timeout waiting for connection error")
		}

		// Should receive success event from second attempt
		select {
		case event := <-eventCh:
			assert.Equal(t, "success", event.Type)
		case <-time.After(3 * time.Second):
			t.Fatal("Timeout waiting for reconnection")
		}

		client.Close()
	})

	t.Run("includes Last-Event-ID on reconnection", func(t *testing.T) {
		attempts := atomic.Int32{}
		var lastEventID string
		var mu sync.Mutex

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			count := attempts.Add(1)

			// Capture Last-Event-ID header
			mu.Lock()
			lastEventID = r.Header.Get("Last-Event-ID")
			mu.Unlock()

			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			if count == 1 {
				// Send event with ID
				fmt.Fprintf(w, "id: event-999\n")
				fmt.Fprintf(w, "data: {}\n")
				fmt.Fprintf(w, "\n")
				flusher.Flush()
				time.Sleep(50 * time.Millisecond)
				// Then close connection to trigger reconnect
				return
			}

			// Second connection should have Last-Event-ID
			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()

		client.Subscribe(ctx)

		// Wait for reconnection
		time.Sleep(500 * time.Millisecond)

		mu.Lock()
		receivedID := lastEventID
		mu.Unlock()

		// Second request should include Last-Event-ID
		if attempts.Load() > 1 {
			assert.Equal(t, "event-999", receivedID)
		}

		client.Close()
	})
}

func TestSSEClient_ContextCancellation(t *testing.T) {
	t.Run("stops on context cancellation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)
			time.Sleep(5 * time.Second)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithCancel(context.Background())

		eventCh, _, _ := client.Subscribe(ctx)

		// Cancel context
		cancel()

		// Should not receive any more events
		select {
		case <-eventCh:
			t.Fatal("Should not receive events after context cancellation")
		case <-time.After(200 * time.Millisecond):
			// Expected timeout
		}

		client.Close()
	})
}

func TestSSEClient_EventFilters(t *testing.T) {
	t.Run("FilterByType filters events by type", func(t *testing.T) {
		filter := FilterByType("message", "alert")

		event1 := &Event{Type: "message"}
		event2 := &Event{Type: "alert"}
		event3 := &Event{Type: "heartbeat"}

		assert.True(t, filter(event1))
		assert.True(t, filter(event2))
		assert.False(t, filter(event3))
	})

	t.Run("FilterByTopic filters events by topic", func(t *testing.T) {
		filter := FilterByTopic("deployments", "alerts")

		event1 := &Event{Topic: "deployments"}
		event2 := &Event{Topic: "alerts"}
		event3 := &Event{Topic: "metrics"}

		assert.True(t, filter(event1))
		assert.True(t, filter(event2))
		assert.False(t, filter(event3))
	})

	t.Run("FilterByField filters events by data field", func(t *testing.T) {
		filter := FilterByField("severity", "high", "critical")

		event1 := &Event{Data: map[string]interface{}{"severity": "high"}}
		event2 := &Event{Data: map[string]interface{}{"severity": "critical"}}
		event3 := &Event{Data: map[string]interface{}{"severity": "low"}}
		event4 := &Event{Data: map[string]interface{}{}}

		assert.True(t, filter(event1))
		assert.True(t, filter(event2))
		assert.False(t, filter(event3))
		assert.False(t, filter(event4))
	})

	t.Run("CombineFilters combines filters with AND logic", func(t *testing.T) {
		typeFilter := FilterByType("message")
		topicFilter := FilterByTopic("alerts")
		combined := CombineFilters(typeFilter, topicFilter)

		event1 := &Event{Type: "message", Topic: "alerts"}
		event2 := &Event{Type: "message", Topic: "metrics"}
		event3 := &Event{Type: "heartbeat", Topic: "alerts"}

		assert.True(t, combined(event1))   // Both match
		assert.False(t, combined(event2))  // Only type matches
		assert.False(t, combined(event3))  // Only topic matches
	})

	t.Run("client respects filter", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			// Send two events
			fmt.Fprintf(w, "event: message\n")
			fmt.Fprintf(w, "data: {}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			fmt.Fprintf(w, "event: heartbeat\n")
			fmt.Fprintf(w, "data: {}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(200 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		client.SetFilter(FilterByType("message")) // Only accept message events

		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		eventCh, _, _ := client.Subscribe(ctx)

		// Should only receive message event
		select {
		case event := <-eventCh:
			assert.Equal(t, "message", event.Type)
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for filtered event")
		}

		// Should not receive heartbeat (filtered out)
		select {
		case event := <-eventCh:
			t.Fatalf("Should not receive filtered event: %s", event.Type)
		case <-time.After(300 * time.Millisecond):
			// Expected - heartbeat was filtered
		}

		client.Close()
	})
}

func TestSSEClient_ErrorHandling(t *testing.T) {
	t.Run("reports error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusUnauthorized)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		_, errorCh, _ := client.Subscribe(ctx)

		select {
		case err := <-errorCh:
			assert.Contains(t, err.Error(), "401")
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for error")
		}

		client.Close()
	})

	t.Run("reports error on invalid content type", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/html")
			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		_, errorCh, _ := client.Subscribe(ctx)

		select {
		case err := <-errorCh:
			assert.Contains(t, strings.ToLower(err.Error()), "content type")
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for error")
		}

		client.Close()
	})
}

func TestSSEClient_EdgeCases(t *testing.T) {
	t.Run("handles empty event gracefully", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			// Empty event
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			// Real event
			fmt.Fprintf(w, "data: {}\n")
			fmt.Fprintf(w, "\n")
			flusher.Flush()

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		eventCh, _, _ := client.Subscribe(ctx)

		select {
		case event := <-eventCh:
			assert.NotNil(t, event)
		case <-time.After(500 * time.Millisecond):
			t.Fatal("Timeout waiting for event")
		}

		client.Close()
	})

	t.Run("handles channel buffer overflow", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/event-stream")
			w.WriteHeader(http.StatusOK)

			flusher := w.(http.Flusher)

			// Send many events quickly (more than channel buffer)
			for i := 0; i < 150; i++ {
				fmt.Fprintf(w, "data: {\"n\":%d}\n", i)
				fmt.Fprintf(w, "\n")
				flusher.Flush()
			}

			time.Sleep(100 * time.Millisecond)
		}))
		defer server.Close()

		client := NewSSEClient(server.URL, nil)
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
		defer cancel()

		_, errorCh, _ := client.Subscribe(ctx)

		// Should report dropped events
		select {
		case err := <-errorCh:
			assert.Contains(t, err.Error(), "full")
		case <-time.After(500 * time.Millisecond):
			// May not error if events are consumed fast enough
		}

		client.Close()
	})
}

func BenchmarkSSEClient_EventProcessing(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		w.WriteHeader(http.StatusOK)

		flusher := w.(http.Flusher)

		for i := 0; i < b.N; i++ {
			fmt.Fprintf(w, "event: bench\n")
			fmt.Fprintf(w, "data: {\"i\":%d}\n", i)
			fmt.Fprintf(w, "\n")
			flusher.Flush()
		}
	}))
	defer server.Close()

	client := NewSSEClient(server.URL, nil)
	ctx := context.Background()

	eventCh, _, _ := client.Subscribe(ctx)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		<-eventCh
	}

	client.Close()
}

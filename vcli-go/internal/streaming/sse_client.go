package streaming

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"
)

// Event represents a generic SSE event
type Event struct {
	Type      string                 `json:"type"`
	ID        string                 `json:"id"`
	Timestamp time.Time              `json:"timestamp"`
	Topic     string                 `json:"topic"`
	Data      map[string]interface{} `json:"data"`
	Raw       string                 `json:"raw"` // Original data string
}

// EventFilter is a function that returns true if event should be processed
type EventFilter func(*Event) bool

// SSEClient provides generic Server-Sent Events streaming
type SSEClient struct {
	baseURL string
	topics  []string
	filter  EventFilter

	client *http.Client

	// Connection state
	mu          sync.RWMutex
	connected   bool
	lastEventID string

	// Channels
	eventCh chan *Event
	errorCh chan error
	stopCh  chan struct{}

	// Metrics
	eventsReceived int64
	bytesReceived  int64
	lastHeartbeat  time.Time

	// Reconnection
	reconnectDelay    time.Duration
	maxReconnectDelay time.Duration
}

// NewSSEClient creates a new generic SSE client
func NewSSEClient(baseURL string, topics []string) *SSEClient {
	return &SSEClient{
		baseURL: baseURL,
		topics:  topics,
		client: &http.Client{
			Timeout: 0, // No timeout for SSE
		},
		eventCh:           make(chan *Event, 100),
		errorCh:           make(chan error, 10),
		stopCh:            make(chan struct{}),
		reconnectDelay:    time.Second,
		maxReconnectDelay: 30 * time.Second,
	}
}

// SetFilter sets the event filter function
func (c *SSEClient) SetFilter(filter EventFilter) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.filter = filter
}

// Subscribe starts streaming events
func (c *SSEClient) Subscribe(ctx context.Context) (<-chan *Event, <-chan error, error) {
	c.mu.Lock()
	if c.connected {
		c.mu.Unlock()
		return nil, nil, fmt.Errorf("already subscribed")
	}
	c.mu.Unlock()

	// Start connection loop
	go c.connectionLoop(ctx)

	return c.eventCh, c.errorCh, nil
}

// Close stops the SSE connection
func (c *SSEClient) Close() error {
	close(c.stopCh)
	c.mu.Lock()
	c.connected = false
	c.mu.Unlock()
	return nil
}

// GetMetrics returns streaming metrics
func (c *SSEClient) GetMetrics() (events, bytes int64, lastHeartbeat time.Time) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.eventsReceived, c.bytesReceived, c.lastHeartbeat
}

// connectionLoop manages SSE connection with automatic reconnection
func (c *SSEClient) connectionLoop(ctx context.Context) {
	attempts := 0

	for {
		select {
		case <-ctx.Done():
			return
		case <-c.stopCh:
			return
		default:
			if err := c.connect(ctx); err != nil {
				attempts++
				c.errorCh <- fmt.Errorf("connection failed (attempt %d): %w", attempts, err)

				// Exponential backoff
				delay := c.reconnectDelay * time.Duration(1<<uint(min(attempts-1, 5)))
				if delay > c.maxReconnectDelay {
					delay = c.maxReconnectDelay
				}

				select {
				case <-ctx.Done():
					return
				case <-c.stopCh:
					return
				case <-time.After(delay):
					continue
				}
			}
			// Reset attempts on successful connection
			attempts = 0
		}
	}
}

// connect establishes SSE connection
func (c *SSEClient) connect(ctx context.Context) error {
	// Build URL with topic filters
	url := c.baseURL
	if len(c.topics) > 0 {
		url += "?topics=" + strings.Join(c.topics, ",")
	}

	// Create request
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Set SSE headers
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set("Cache-Control", "no-cache")
	req.Header.Set("Connection", "keep-alive")

	// Resume from last event if reconnecting
	c.mu.RLock()
	if c.lastEventID != "" {
		req.Header.Set("Last-Event-ID", c.lastEventID)
	}
	c.mu.RUnlock()

	// Execute request
	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer resp.Body.Close()

	// Verify status code
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	// Verify content type
	contentType := resp.Header.Get("Content-Type")
	if !strings.Contains(contentType, "text/event-stream") {
		return fmt.Errorf("invalid content type: %s", contentType)
	}

	// Mark as connected
	c.mu.Lock()
	c.connected = true
	c.mu.Unlock()

	// Process stream
	return c.processStream(resp.Body)
}

// processStream reads and parses SSE events
func (c *SSEClient) processStream(body io.Reader) error {
	scanner := bufio.NewScanner(body)
	scanner.Buffer(make([]byte, 64*1024), 1024*1024) // 1MB max token size

	var (
		eventType string
		eventID   string
		dataLines []string
	)

	for scanner.Scan() {
		line := scanner.Text()

		// Count bytes
		c.mu.Lock()
		c.bytesReceived += int64(len(line) + 1)
		c.mu.Unlock()

		// Empty line indicates end of event
		if line == "" {
			if len(dataLines) > 0 {
				c.handleEvent(eventType, eventID, dataLines)
			}
			eventType = ""
			eventID = ""
			dataLines = nil
			continue
		}

		// Skip comments
		if strings.HasPrefix(line, ":") {
			continue
		}

		// Parse field
		parts := strings.SplitN(line, ":", 2)
		if len(parts) < 2 {
			continue
		}

		field := parts[0]
		value := strings.TrimPrefix(parts[1], " ")

		switch field {
		case "event":
			eventType = value
		case "id":
			eventID = value
			c.mu.Lock()
			c.lastEventID = eventID
			c.mu.Unlock()
		case "data":
			dataLines = append(dataLines, value)
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("scanner error: %w", err)
	}

	return fmt.Errorf("stream ended unexpectedly")
}

// handleEvent processes a complete SSE event
func (c *SSEClient) handleEvent(eventType, eventID string, dataLines []string) {
	// Join data lines
	data := strings.Join(dataLines, "\n")

	// Parse JSON data
	var eventData map[string]interface{}
	if err := json.Unmarshal([]byte(data), &eventData); err != nil {
		// If not JSON, store as raw string
		eventData = map[string]interface{}{
			"raw": data,
		}
	}

	// Extract topic if present
	topic := ""
	if t, ok := eventData["topic"].(string); ok {
		topic = t
	}

	// Create event
	event := &Event{
		Type:      eventType,
		ID:        eventID,
		Timestamp: time.Now(),
		Topic:     topic,
		Data:      eventData,
		Raw:       data,
	}

	// Update metrics
	c.mu.Lock()
	c.eventsReceived++

	if eventType == "heartbeat" || eventType == "ping" {
		c.lastHeartbeat = time.Now()
	}

	// Check filter
	filter := c.filter
	c.mu.Unlock()

	if filter != nil && !filter(event) {
		// Event filtered out
		return
	}

	// Send to event channel (non-blocking)
	select {
	case c.eventCh <- event:
	default:
		// Channel full, drop event
		select {
		case c.errorCh <- fmt.Errorf("event channel full, dropping event: %s", eventType):
		default:
		}
	}
}

// Common event filters

// FilterByType creates a filter that matches specific event types
func FilterByType(types ...string) EventFilter {
	typeMap := make(map[string]bool)
	for _, t := range types {
		typeMap[t] = true
	}
	return func(e *Event) bool {
		return typeMap[e.Type]
	}
}

// FilterByTopic creates a filter that matches specific topics
func FilterByTopic(topics ...string) EventFilter {
	topicMap := make(map[string]bool)
	for _, t := range topics {
		topicMap[t] = true
	}
	return func(e *Event) bool {
		return topicMap[e.Topic]
	}
}

// FilterByField creates a filter that matches events with specific field values
func FilterByField(field string, values ...interface{}) EventFilter {
	valueMap := make(map[interface{}]bool)
	for _, v := range values {
		valueMap[v] = true
	}
	return func(e *Event) bool {
		if v, ok := e.Data[field]; ok {
			return valueMap[v]
		}
		return false
	}
}

// CombineFilters combines multiple filters with AND logic
func CombineFilters(filters ...EventFilter) EventFilter {
	return func(e *Event) bool {
		for _, f := range filters {
			if !f(e) {
				return false
			}
		}
		return true
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

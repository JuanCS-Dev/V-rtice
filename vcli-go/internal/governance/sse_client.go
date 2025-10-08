package governance

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

// SSEClient streams Server-Sent Events from Governance backend
type SSEClient struct {
	// Configuration
	serverURL  string
	operatorID string
	sessionID  string

	// HTTP client
	client *http.Client

	// Connection state
	mu          sync.RWMutex
	connected   bool
	reconnecting bool
	lastEventID string
	status      ConnectionStatus

	// Event handling
	eventCh chan *SSEEvent
	errorCh chan error
	stopCh  chan struct{}

	// Metrics
	eventsReceived int
	bytesReceived  int64
	lastHeartbeat  time.Time

	// Reconnection
	reconnectDelay time.Duration
	maxReconnectDelay time.Duration
	reconnectAttempts int
}

// NewSSEClient creates a new SSE client for Governance events
func NewSSEClient(serverURL, operatorID, sessionID string) *SSEClient {
	return &SSEClient{
		serverURL:  serverURL,
		operatorID: operatorID,
		sessionID:  sessionID,
		client: &http.Client{
			Timeout: 0, // No timeout for SSE connection
		},
		eventCh:           make(chan *SSEEvent, 100),
		errorCh:           make(chan error, 10),
		stopCh:            make(chan struct{}),
		reconnectDelay:    time.Second,
		maxReconnectDelay: 30 * time.Second,
		status: ConnectionStatus{
			ServerURL: serverURL,
		},
	}
}

// Connect establishes SSE connection to Governance backend
func (c *SSEClient) Connect(ctx context.Context) error {
	c.mu.Lock()
	if c.connected {
		c.mu.Unlock()
		return fmt.Errorf("already connected")
	}
	c.mu.Unlock()

	// Start connection goroutine
	go c.connectionLoop(ctx)

	return nil
}

// Events returns channel for receiving SSE events
func (c *SSEClient) Events() <-chan *SSEEvent {
	return c.eventCh
}

// Errors returns channel for receiving connection errors
func (c *SSEClient) Errors() <-chan error {
	return c.errorCh
}

// Status returns current connection status
func (c *SSEClient) Status() ConnectionStatus {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.status
}

// Close closes the SSE connection
func (c *SSEClient) Close() error {
	close(c.stopCh)
	c.mu.Lock()
	c.connected = false
	c.mu.Unlock()
	return nil
}

// connectionLoop manages SSE connection with automatic reconnection
func (c *SSEClient) connectionLoop(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-c.stopCh:
			return
		default:
			if err := c.connect(ctx); err != nil {
				c.handleConnectionError(err)
				c.reconnect(ctx)
			}
		}
	}
}

// connect establishes single SSE connection
func (c *SSEClient) connect(ctx context.Context) error {
	// Build SSE endpoint URL
	url := fmt.Sprintf("%s/governance/stream", c.serverURL)

	// Create request
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Set SSE headers
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set("Cache-Control", "no-cache")
	req.Header.Set("Connection", "keep-alive")

	// Add operator identification
	req.Header.Set("X-Operator-ID", c.operatorID)
	req.Header.Set("X-Session-ID", c.sessionID)

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

	// Verify content type
	contentType := resp.Header.Get("Content-Type")
	if !strings.Contains(contentType, "text/event-stream") {
		return fmt.Errorf("invalid content type: %s", contentType)
	}

	// Mark as connected
	c.mu.Lock()
	c.connected = true
	c.reconnecting = false
	c.reconnectAttempts = 0
	c.reconnectDelay = time.Second
	c.status.Connected = true
	c.status.Reconnecting = false
	c.status.LastError = ""
	c.mu.Unlock()

	// Process SSE stream
	return c.processStream(resp.Body)
}

// processStream reads and parses SSE events from response body
func (c *SSEClient) processStream(body io.Reader) error {
	scanner := bufio.NewScanner(body)

	var (
		eventType string
		eventID   string
		dataLines []string
	)

	for scanner.Scan() {
		line := scanner.Text()

		// Count bytes
		c.mu.Lock()
		c.bytesReceived += int64(len(line) + 1) // +1 for newline
		c.status.BytesReceived = c.bytesReceived
		c.mu.Unlock()

		// Empty line indicates end of event
		if line == "" {
			if len(dataLines) > 0 {
				if err := c.handleEvent(eventType, eventID, dataLines); err != nil {
					c.errorCh <- fmt.Errorf("failed to handle event: %w", err)
				}
			}

			// Reset for next event
			eventType = ""
			eventID = ""
			dataLines = nil
			continue
		}

		// Parse SSE field
		if strings.HasPrefix(line, ":") {
			// Comment line, ignore
			continue
		}

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
		case "retry":
			// Server suggests retry delay (milliseconds)
			// We implement our own exponential backoff
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("scanner error: %w", err)
	}

	return fmt.Errorf("stream ended unexpectedly")
}

// handleEvent processes a complete SSE event
func (c *SSEClient) handleEvent(eventType, eventID string, dataLines []string) error {
	// Join data lines
	data := strings.Join(dataLines, "\n")

	// Parse JSON data
	var eventData map[string]interface{}
	if err := json.Unmarshal([]byte(data), &eventData); err != nil {
		return fmt.Errorf("failed to parse event data: %w", err)
	}

	// Create SSE event
	event := &SSEEvent{
		EventType: eventType,
		EventID:   eventID,
		Timestamp: time.Now(),
		Data:      eventData,
	}

	// Update metrics
	c.mu.Lock()
	c.eventsReceived++
	c.status.EventsReceived = c.eventsReceived

	if eventType == "heartbeat" {
		c.lastHeartbeat = time.Now()
		c.status.LastHeartbeat = c.lastHeartbeat
	}
	c.mu.Unlock()

	// Send to event channel (non-blocking)
	select {
	case c.eventCh <- event:
	default:
		// Channel full, drop event
		c.errorCh <- fmt.Errorf("event channel full, dropping event: %s", eventType)
	}

	return nil
}

// handleConnectionError handles connection errors
func (c *SSEClient) handleConnectionError(err error) {
	c.mu.Lock()
	c.connected = false
	c.status.Connected = false
	c.status.LastError = err.Error()
	c.mu.Unlock()

	// Send to error channel (non-blocking)
	select {
	case c.errorCh <- err:
	default:
	}
}

// reconnect implements exponential backoff reconnection
func (c *SSEClient) reconnect(ctx context.Context) {
	c.mu.Lock()
	c.reconnecting = true
	c.reconnectAttempts++
	c.status.Reconnecting = true

	// Calculate backoff delay with exponential increase
	delay := c.reconnectDelay * time.Duration(1<<uint(c.reconnectAttempts-1))
	if delay > c.maxReconnectDelay {
		delay = c.maxReconnectDelay
	}
	c.mu.Unlock()

	select {
	case <-ctx.Done():
		return
	case <-c.stopCh:
		return
	case <-time.After(delay):
		// Continue with reconnection attempt
	}
}

// ParseDecisionEvent extracts Decision from SSE event data
func ParseDecisionEvent(event *SSEEvent) (*Decision, error) {
	if event.EventType != "decision_pending" && event.EventType != "decision_resolved" {
		return nil, fmt.Errorf("invalid event type for decision: %s", event.EventType)
	}

	// Convert map to JSON and back to Decision struct
	dataJSON, err := json.Marshal(event.Data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal event data: %w", err)
	}

	var decision Decision
	if err := json.Unmarshal(dataJSON, &decision); err != nil {
		return nil, fmt.Errorf("failed to unmarshal decision: %w", err)
	}

	return &decision, nil
}

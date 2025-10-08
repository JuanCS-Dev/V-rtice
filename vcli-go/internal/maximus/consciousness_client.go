package maximus

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"github.com/gorilla/websocket"
)

// ConsciousnessClient handles communication with MAXIMUS Consciousness API
type ConsciousnessClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewConsciousnessClient creates a new consciousness API client
func NewConsciousnessClient(baseURL string) *ConsciousnessClient {
	if baseURL == "" {
		baseURL = "http://localhost:8022"
	}

	return &ConsciousnessClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// ==================== RESPONSE TYPES ====================

// ConsciousnessState represents complete consciousness state snapshot
type ConsciousnessState struct {
	Timestamp              string                 `json:"timestamp"`
	ESGTActive             bool                   `json:"esgt_active"`
	ArousalLevel           float64                `json:"arousal_level"`
	ArousalClassification  string                 `json:"arousal_classification"`
	TIGMetrics             map[string]interface{} `json:"tig_metrics"`
	RecentEventsCount      int                    `json:"recent_events_count"`
	SystemHealth           string                 `json:"system_health"`
}

// ESGTEvent represents an ESGT ignition event
type ESGTEvent struct {
	EventID             string             `json:"event_id"`
	Timestamp           string             `json:"timestamp"`
	Success             bool               `json:"success"`
	Salience            map[string]float64 `json:"salience"`
	Coherence           *float64           `json:"coherence"`
	DurationMs          *float64           `json:"duration_ms"`
	NodesParticipating  int                `json:"nodes_participating"`
	Reason              *string            `json:"reason"`
}

// ArousalState represents current arousal state
type ArousalState struct {
	Arousal            float64 `json:"arousal"`
	Level              string  `json:"level"`
	Baseline           float64 `json:"baseline"`
	NeedContribution   float64 `json:"need_contribution"`
	StressContribution float64 `json:"stress_contribution"`
	Timestamp          string  `json:"timestamp"`
}

// ConsciousnessMetrics represents system metrics
type ConsciousnessMetrics struct {
	TIGMetrics  map[string]interface{} `json:"tig_metrics"`
	ESGTStats   map[string]interface{} `json:"esgt_stats"`
}

// ==================== REQUEST TYPES ====================

// SalienceInput for manual ESGT trigger
type SalienceInput struct {
	Novelty   float64                `json:"novelty"`
	Relevance float64                `json:"relevance"`
	Urgency   float64                `json:"urgency"`
	Context   map[string]interface{} `json:"context,omitempty"`
}

// ArousalAdjustment for arousal level adjustment
type ArousalAdjustment struct {
	Delta            float64 `json:"delta"`
	DurationSeconds  float64 `json:"duration_seconds"`
	Source           string  `json:"source"`
}

// ==================== API METHODS ====================

// GetState retrieves the complete consciousness state
func (c *ConsciousnessClient) GetState() (*ConsciousnessState, error) {
	url := fmt.Sprintf("%s/api/consciousness/state", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to consciousness API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var state ConsciousnessState
	if err := json.NewDecoder(resp.Body).Decode(&state); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &state, nil
}

// GetESGTEvents retrieves recent ESGT events
func (c *ConsciousnessClient) GetESGTEvents(limit int) ([]ESGTEvent, error) {
	url := fmt.Sprintf("%s/api/consciousness/esgt/events?limit=%d", c.baseURL, limit)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to consciousness API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var events []ESGTEvent
	if err := json.NewDecoder(resp.Body).Decode(&events); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return events, nil
}

// GetArousal retrieves current arousal state
func (c *ConsciousnessClient) GetArousal() (*ArousalState, error) {
	url := fmt.Sprintf("%s/api/consciousness/arousal", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to consciousness API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var arousal ArousalState
	if err := json.NewDecoder(resp.Body).Decode(&arousal); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &arousal, nil
}

// GetMetrics retrieves system metrics
func (c *ConsciousnessClient) GetMetrics() (*ConsciousnessMetrics, error) {
	url := fmt.Sprintf("%s/api/consciousness/metrics", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to consciousness API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var metrics ConsciousnessMetrics
	if err := json.NewDecoder(resp.Body).Decode(&metrics); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &metrics, nil
}

// TriggerESGT manually triggers ESGT ignition
func (c *ConsciousnessClient) TriggerESGT(salience SalienceInput) (*ESGTEvent, error) {
	url := fmt.Sprintf("%s/api/consciousness/esgt/trigger", c.baseURL)

	// Validate salience values
	if salience.Novelty < 0 || salience.Novelty > 1 {
		return nil, fmt.Errorf("novelty must be between 0 and 1")
	}
	if salience.Relevance < 0 || salience.Relevance > 1 {
		return nil, fmt.Errorf("relevance must be between 0 and 1")
	}
	if salience.Urgency < 0 || salience.Urgency > 1 {
		return nil, fmt.Errorf("urgency must be between 0 and 1")
	}

	body, err := json.Marshal(salience)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to consciousness API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var event ESGTEvent
	if err := json.NewDecoder(resp.Body).Decode(&event); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &event, nil
}

// AdjustArousal adjusts arousal level
func (c *ConsciousnessClient) AdjustArousal(adjustment ArousalAdjustment) (*ArousalState, error) {
	url := fmt.Sprintf("%s/api/consciousness/arousal/adjust", c.baseURL)

	// Validate adjustment
	if adjustment.Delta < -0.5 || adjustment.Delta > 0.5 {
		return nil, fmt.Errorf("delta must be between -0.5 and 0.5")
	}
	if adjustment.DurationSeconds < 0.1 || adjustment.DurationSeconds > 60.0 {
		return nil, fmt.Errorf("duration must be between 0.1 and 60.0 seconds")
	}
	if adjustment.Source == "" {
		adjustment.Source = "vcli"
	}

	body, err := json.Marshal(adjustment)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to consciousness API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var arousal ArousalState
	if err := json.NewDecoder(resp.Body).Decode(&arousal); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &arousal, nil
}

// Health checks if the consciousness API is reachable
func (c *ConsciousnessClient) Health() error {
	healthURL := fmt.Sprintf("%s/health", c.baseURL)

	resp, err := c.httpClient.Get(healthURL)
	if err != nil {
		return fmt.Errorf("consciousness API unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("consciousness API unhealthy (status %d)", resp.StatusCode)
	}

	return nil
}

// ==================== WEBSOCKET TYPES ====================

// WSEventType represents WebSocket event types
type WSEventType string

const (
	WSEventESGT          WSEventType = "esgt_event"
	WSEventArousalChange WSEventType = "arousal_change"
	WSEventHeartbeat     WSEventType = "heartbeat"
)

// WSEvent represents a WebSocket event
type WSEvent struct {
	Type      WSEventType     `json:"type"`
	Timestamp string          `json:"timestamp"`
	Data      json.RawMessage `json:"data"`
}

// ESGTWebSocketEvent represents an ESGT event from WebSocket
type ESGTWebSocketEvent struct {
	EventID            string             `json:"event_id"`
	Success            bool               `json:"success"`
	Salience           map[string]float64 `json:"salience"`
	Coherence          *float64           `json:"coherence"`
	DurationMs         *float64           `json:"duration_ms"`
	NodesParticipating int                `json:"nodes_participating"`
	Reason             *string            `json:"reason"`
}

// ArousalChangeEvent represents an arousal change event from WebSocket
type ArousalChangeEvent struct {
	OldLevel float64 `json:"old_level"`
	NewLevel float64 `json:"new_level"`
	OldClass string  `json:"old_classification"`
	NewClass string  `json:"new_classification"`
}

// HeartbeatEvent represents a heartbeat event from WebSocket
type HeartbeatEvent struct {
	Status    string `json:"status"`
	Uptime    int64  `json:"uptime_seconds"`
	ESGTCount int    `json:"esgt_event_count"`
}

// EventCallback is called when a WebSocket event is received
type EventCallback func(event *WSEvent) error

// ==================== WEBSOCKET METHODS ====================

// ConnectWebSocket connects to the consciousness WebSocket endpoint
func (c *ConsciousnessClient) ConnectWebSocket(callback EventCallback) error {
	// Parse base URL and convert to WebSocket URL
	parsedURL, err := url.Parse(c.baseURL)
	if err != nil {
		return fmt.Errorf("invalid base URL: %w", err)
	}

	// Convert http:// to ws://
	wsScheme := "ws"
	if parsedURL.Scheme == "https" {
		wsScheme = "wss"
	}

	wsURL := fmt.Sprintf("%s://%s/api/consciousness/ws", wsScheme, parsedURL.Host)

	// Connect to WebSocket
	conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		return fmt.Errorf("failed to connect to WebSocket: %w", err)
	}
	defer conn.Close()

	// Read messages in a loop
	for {
		var event WSEvent
		err := conn.ReadJSON(&event)
		if err != nil {
			// Check if connection was closed
			if websocket.IsCloseError(err, websocket.CloseNormalClosure, websocket.CloseGoingAway) {
				return nil
			}
			return fmt.Errorf("error reading WebSocket message: %w", err)
		}

		// Call user callback
		if err := callback(&event); err != nil {
			return fmt.Errorf("callback error: %w", err)
		}
	}
}

// ParseESGTEvent parses ESGT event data from WebSocket event
func ParseESGTEvent(event *WSEvent) (*ESGTWebSocketEvent, error) {
	if event.Type != WSEventESGT {
		return nil, fmt.Errorf("not an ESGT event (type: %s)", event.Type)
	}

	var esgtEvent ESGTWebSocketEvent
	if err := json.Unmarshal(event.Data, &esgtEvent); err != nil {
		return nil, fmt.Errorf("failed to parse ESGT event: %w", err)
	}

	return &esgtEvent, nil
}

// ParseArousalChangeEvent parses arousal change event from WebSocket event
func ParseArousalChangeEvent(event *WSEvent) (*ArousalChangeEvent, error) {
	if event.Type != WSEventArousalChange {
		return nil, fmt.Errorf("not an arousal change event (type: %s)", event.Type)
	}

	var arousalEvent ArousalChangeEvent
	if err := json.Unmarshal(event.Data, &arousalEvent); err != nil {
		return nil, fmt.Errorf("failed to parse arousal event: %w", err)
	}

	return &arousalEvent, nil
}

// ParseHeartbeatEvent parses heartbeat event from WebSocket event
func ParseHeartbeatEvent(event *WSEvent) (*HeartbeatEvent, error) {
	if event.Type != WSEventHeartbeat {
		return nil, fmt.Errorf("not a heartbeat event (type: %s)", event.Type)
	}

	var heartbeat HeartbeatEvent
	if err := json.Unmarshal(event.Data, &heartbeat); err != nil {
		return nil, fmt.Errorf("failed to parse heartbeat: %w", err)
	}

	return &heartbeat, nil
}

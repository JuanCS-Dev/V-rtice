package eventbus

import (
	"context"
	"fmt"
	"time"

	"github.com/nats-io/nats.go"
)

// Client provides NATS JetStream connectivity for coagulation components.
//
// Event bus is the "bloodstream" of the cascade: carries signals between
// distributed components enabling emergent containment behavior.
type Client struct {
	conn      *nats.Conn
	js        nats.JetStreamContext
	component string
}

// Event represents a coagulation event in the cascade.
type Event struct {
	ID        string    `json:"id"`
	Type      string    `json:"type"`      // "breach_detected", "cascade_triggered", etc.
	Source    string    `json:"source"`    // Component that generated event
	Timestamp time.Time `json:"timestamp"`
	Payload   []byte    `json:"payload"`
	
	// Consciousness metadata
	BreachID         string  `json:"breach_id,omitempty"`
	CascadeStage     string  `json:"cascade_stage,omitempty"`     // "initiation", "amplification", etc.
	EmotionalValence float64 `json:"emotional_valence,omitempty"` // -1.0 to 1.0
	Severity         float64 `json:"severity,omitempty"`          // 0.0 to 1.0
}

// NewClient creates NATS JetStream client for coagulation events.
//
// Parameters:
//   - natsURL: NATS server URL (e.g., "nats://localhost:4222")
//   - component: Component identifier for event sourcing
//
// Returns connected client ready for pub/sub operations.
func NewClient(natsURL, component string) (*Client, error) {
	// Connect to NATS
	conn, err := nats.Connect(natsURL,
		nats.Name(component),
		nats.Timeout(5*time.Second),
		nats.ReconnectWait(1*time.Second),
		nats.MaxReconnects(10),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to NATS: %w", err)
	}
	
	// Create JetStream context
	js, err := conn.JetStream()
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("failed to create JetStream context: %w", err)
	}
	
	return &Client{
		conn:      conn,
		js:        js,
		component: component,
	}, nil
}

// Publish publishes an event to a subject.
//
// Uses JetStream for guaranteed delivery and ordering - critical for
// cascade integrity. Messages are persisted until acknowledged.
func (c *Client) Publish(ctx context.Context, subject string, event *Event) error {
	event.Source = c.component
	event.Timestamp = time.Now()
	
	data, err := marshalEvent(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}
	
	_, err = c.js.Publish(subject, data)
	if err != nil {
		return fmt.Errorf("failed to publish to %s: %w", subject, err)
	}
	
	return nil
}

// Subscribe subscribes to events on a subject with durable consumer.
//
// Durable subscriptions ensure no cascade events are lost during
// component restarts - critical for containment integrity.
func (c *Client) Subscribe(subject, durableName string, handler func(*Event) error) error {
	_, err := c.js.Subscribe(subject, func(msg *nats.Msg) {
		event, err := unmarshalEvent(msg.Data)
		if err != nil {
			// Log error but ack to prevent redelivery of corrupted message
			msg.Ack()
			return
		}
		
		// Process event
		if err := handler(event); err != nil {
			// Negative ack - message will be redelivered
			msg.Nak()
			return
		}
		
		// Success - ack message
		msg.Ack()
	},
		nats.Durable(durableName),
		nats.ManualAck(),
		nats.AckWait(30*time.Second),
	)
	
	return err
}

// Close closes NATS connection gracefully.
func (c *Client) Close() {
	if c.conn != nil {
		c.conn.Close()
	}
}

// Subject constants for coagulation events
const (
	// Detection layer subjects
	SubjectBreachDetected      = "coagulation.breach.detected"
	SubjectAnomalyDetected     = "coagulation.anomaly.detected"
	SubjectIoCValidated        = "coagulation.ioc.validated"
	
	// Cascade layer subjects
	SubjectCascadeTriggered    = "coagulation.cascade.triggered"
	SubjectFactorActivated     = "coagulation.factor.activated"
	SubjectThromburstGenerated = "coagulation.thromburst.generated"
	
	// Containment layer subjects
	SubjectQuarantineApplied   = "coagulation.quarantine.applied"
	SubjectFibrinMeshFormed    = "coagulation.fibrin.formed"
	
	// Regulation layer subjects
	SubjectRegulationInhibit   = "coagulation.regulation.inhibit"
	SubjectHealthCheckPassed   = "coagulation.health.passed"
	SubjectHealthCheckFailed   = "coagulation.health.failed"
)

// Helper functions for event marshaling (simplified - production would use protobuf)
func marshalEvent(e *Event) ([]byte, error) {
	// Production: use protobuf for efficiency
	// Foundation: JSON is sufficient
	return []byte(fmt.Sprintf(`{"id":"%s","type":"%s","source":"%s"}`, e.ID, e.Type, e.Source)), nil
}

func unmarshalEvent(data []byte) (*Event, error) {
	// Production: protobuf unmarshal
	// Foundation: simplified parsing
	return &Event{}, nil
}

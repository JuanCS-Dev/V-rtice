package intrinsic_pathway

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// CollagenSensor represents the anomaly detection service.
//
// Biological Analogy: Collagen is exposed in damaged blood vessels, triggering
// the intrinsic pathway. Similarly, this service detects "strange surfaces" -
// behavioral anomalies that indicate potential compromise.
//
// Confidence Level: 0.3-0.8 (lower than TF, requires correlation)
// Response: Gradual cascade activation, correlation required
type CollagenSensor struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client
	
	// Behavioral baseline
	baseline         *BehavioralBaseline
	anomalyDetector  *AnomalyDetector
	correlationDB    *CorrelationDatabase
	
	ctx        context.Context
	cancelFunc context.CancelFunc
	mu         sync.RWMutex
}

// BehavioralBaseline stores normal system behavior patterns.
//
// Phase 2: Simple statistical baseline.
// Future: ML-based (LSTM, Autoencoders) behavioral profiling.
type BehavioralBaseline struct {
	processBaseline  map[string]*ProcessProfile
	networkBaseline  map[string]*NetworkProfile
	mu               sync.RWMutex
}

// ProcessProfile represents normal process behavior.
type ProcessProfile struct {
	Name           string
	AvgCPU         float64
	AvgMemory      float64
	TypicalPorts   []int
	TypicalFiles   []string
	FirstSeen      time.Time
	Occurrences    int
}

// NetworkProfile represents normal network behavior.
type NetworkProfile struct {
	SourceIP       string
	DestinationIP  string
	TypicalPorts   []int
	AvgBandwidth   float64
	TypicalTime    string // "business_hours", "night", etc.
	FirstSeen      time.Time
	Occurrences    int
}

// AnomalyDetector detects deviations from baseline.
//
// Phase 2: Statistical deviation detection.
// Future: Isolation Forest, One-Class SVM, LSTM autoencoders.
type AnomalyDetector struct {
	threshold float64 // Z-score threshold for anomaly
}

// CorrelationDatabase stores recent anomalies for multi-signal correlation.
//
// Intrinsic pathway requires multiple weak signals to reach threshold.
type CorrelationDatabase struct {
	anomalies map[string][]*AnomalyEvent
	mu        sync.RWMutex
	ttl       time.Duration
}

// AnomalyEvent represents a single anomaly detection.
type AnomalyEvent struct {
	ID          string
	Type        string  // "process", "network", "file"
	Value       string
	Score       float64 // Anomaly score 0.0-1.0
	Timestamp   time.Time
	BreachID    string
	Description string
}

// NewCollagenSensor creates a new anomaly detection service.
func NewCollagenSensor(natsURL string) (*CollagenSensor, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	log, err := logger.NewLogger("collagen-sensor", "phase2", false)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to init logger: %w", err)
	}
	
	metrics := metrics.NewCollector("collagen-sensor", "intrinsic")
	
	bus, err := eventbus.NewClient(natsURL, "collagen-sensor")
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to connect to event bus: %w", err)
	}
	
	cs := &CollagenSensor{
		logger:          log,
		metrics:         metrics,
		eventBus:        bus,
		baseline:        NewBehavioralBaseline(),
		anomalyDetector: NewAnomalyDetector(3.0), // 3 sigma threshold
		correlationDB:   NewCorrelationDatabase(5 * time.Minute),
		ctx:             ctx,
		cancelFunc:      cancel,
	}
	
	log.Info("collagen_sensor_initialized")
	return cs, nil
}

// Start begins anomaly detection.
func (cs *CollagenSensor) Start() error {
	cs.logger.Info("collagen_sensor_starting")
	
	// Subscribe to breach events (for anomaly scoring)
	err := cs.eventBus.Subscribe(
		eventbus.SubjectBreachDetected,
		"collagen-sensor-detector",
		cs.handleBreachEvent,
	)
	if err != nil {
		return fmt.Errorf("failed to subscribe: %w", err)
	}
	
	// Subscribe to anomaly events from platelet agents
	err = cs.eventBus.Subscribe(
		eventbus.SubjectAnomalyDetected,
		"collagen-sensor-anomaly",
		cs.handleAnomalyEvent,
	)
	if err != nil {
		return fmt.Errorf("failed to subscribe to anomalies: %w", err)
	}
	
	// Start correlation checker
	go cs.correlationLoop()
	
	cs.logger.Info("collagen_sensor_started")
	return nil
}

// handleBreachEvent processes breach events for anomaly analysis.
func (cs *CollagenSensor) handleBreachEvent(event *eventbus.Event) error {
	cs.logger.WithCascadeStage("initiation").Debug("breach_event_received",
		logger.String("breach_id", event.BreachID),
	)
	
	// Analyze for behavioral anomalies
	anomaly := cs.detectAnomaly(event)
	
	if anomaly == nil {
		return nil // No anomaly detected
	}
	
	// Store for correlation
	cs.correlationDB.Add(event.BreachID, anomaly)
	
	cs.logger.Debug("anomaly_detected",
		logger.String("anomaly_id", anomaly.ID),
		logger.String("type", anomaly.Type),
		logger.Float64("score", anomaly.Score),
	)
	
	return nil
}

// handleAnomalyEvent processes anomaly events from agents.
func (cs *CollagenSensor) handleAnomalyEvent(event *eventbus.Event) error {
	cs.logger.Debug("anomaly_event_received",
		logger.String("breach_id", event.BreachID),
		logger.Float64("severity", event.Severity),
	)
	
	// Create anomaly record
	anomaly := &AnomalyEvent{
		ID:          fmt.Sprintf("anomaly-%d", time.Now().UnixNano()),
		Type:        "behavioral",
		Value:       "agent_reported_anomaly",
		Score:       event.Severity,
		Timestamp:   time.Now(),
		BreachID:    event.BreachID,
		Description: "Anomaly reported by platelet agent",
	}
	
	cs.correlationDB.Add(event.BreachID, anomaly)
	
	return nil
}

// detectAnomaly analyzes event for behavioral anomalies.
//
// Phase 2: Simple deviation from baseline.
// Future: ML-based feature extraction and classification.
func (cs *CollagenSensor) detectAnomaly(event *eventbus.Event) *AnomalyEvent {
	// Phase 2: Use event severity as proxy for anomaly score
	if event.Severity < 0.3 {
		return nil // Too low to be anomalous
	}
	
	return &AnomalyEvent{
		ID:          fmt.Sprintf("anomaly-%d", time.Now().UnixNano()),
		Type:        "behavioral",
		Value:       "baseline_deviation",
		Score:       event.Severity,
		Timestamp:   time.Now(),
		BreachID:    event.BreachID,
		Description: "Behavioral deviation from baseline",
	}
}

// correlationLoop checks for correlated anomalies periodically.
//
// Multiple weak signals → Strong signal → Cascade trigger
func (cs *CollagenSensor) correlationLoop() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-cs.ctx.Done():
			return
		case <-ticker.C:
			cs.checkCorrelations()
		}
	}
}

// checkCorrelations analyzes stored anomalies for multi-signal patterns.
func (cs *CollagenSensor) checkCorrelations() {
	cs.correlationDB.mu.RLock()
	defer cs.correlationDB.mu.RUnlock()
	
	for breachID, anomalies := range cs.correlationDB.anomalies {
		if len(anomalies) >= 3 { // Threshold: 3+ correlated anomalies
			// Calculate combined score
			combinedScore := 0.0
			for _, a := range anomalies {
				combinedScore += a.Score
			}
			combinedScore /= float64(len(anomalies))
			
			if combinedScore >= 0.7 { // High enough to trigger
				cs.logger.WithCascadeStage("initiation").Info("correlated_anomalies_detected",
					logger.String("breach_id", breachID),
					logger.Int("anomaly_count", len(anomalies)),
					logger.Float64("combined_score", combinedScore),
				)
				
				cs.metrics.RecordBreachDetection(0.0, combinedScore)
				
				// Emit correlated anomaly event
				cs.emitCorrelatedAnomaly(breachID, anomalies, combinedScore)
			}
		}
	}
}

// emitCorrelatedAnomaly emits validated correlated anomaly to Factor VIIa.
func (cs *CollagenSensor) emitCorrelatedAnomaly(breachID string, anomalies []*AnomalyEvent, score float64) {
	event := &eventbus.Event{
		ID:               fmt.Sprintf("correlated-anomaly-%s", breachID),
		Type:             "anomaly_correlated",
		BreachID:         breachID,
		CascadeStage:     "initiation",
		EmotionalValence: -0.8, // Negative but less than TF
		Severity:         score,
	}
	
	if err := cs.eventBus.Publish(cs.ctx, eventbus.SubjectAnomalyDetected, event); err != nil {
		cs.logger.Error("failed to emit correlated anomaly", logger.Error(err))
	}
}

// Shutdown gracefully stops the service.
func (cs *CollagenSensor) Shutdown() error {
	cs.logger.Info("collagen_sensor_shutting_down")
	cs.cancelFunc()
	cs.eventBus.Close()
	return nil
}

// NewBehavioralBaseline creates baseline storage.
func NewBehavioralBaseline() *BehavioralBaseline {
	return &BehavioralBaseline{
		processBaseline: make(map[string]*ProcessProfile),
		networkBaseline: make(map[string]*NetworkProfile),
	}
}

// NewAnomalyDetector creates detector with threshold.
func NewAnomalyDetector(threshold float64) *AnomalyDetector {
	return &AnomalyDetector{
		threshold: threshold,
	}
}

// NewCorrelationDatabase creates correlation storage.
func NewCorrelationDatabase(ttl time.Duration) *CorrelationDatabase {
	return &CorrelationDatabase{
		anomalies: make(map[string][]*AnomalyEvent),
		ttl:       ttl,
	}
}

func (cd *CorrelationDatabase) Add(breachID string, anomaly *AnomalyEvent) {
	cd.mu.Lock()
	defer cd.mu.Unlock()
	
	if cd.anomalies[breachID] == nil {
		cd.anomalies[breachID] = []*AnomalyEvent{}
	}
	
	cd.anomalies[breachID] = append(cd.anomalies[breachID], anomaly)
}

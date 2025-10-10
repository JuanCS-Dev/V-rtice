package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
	"github.com/verticedev/coagulation/platelet_agent/sensors"
)

// Agent represents a Platelet Digital - autonomous endpoint monitoring agent.
//
// Biological Analogy: Platelets circulate in bloodstream, ready to activate
// upon detecting vessel damage. Similarly, this agent monitors endpoints,
// ready to activate cascade upon detecting integrity violation.
//
// States:
//   - Resting: Passive monitoring, low resource usage
//   - Activated: Active interrogation, signal emission
//   - Aggregated: Coordinated response with peer agents
type Agent struct {
	id       string
	hostname string
	state    AgentState
	
	// Sensors
	processSensor *sensors.ProcessMonitor
	networkSensor *sensors.NetworkMonitor
	fileSensor    *sensors.FileMonitor
	
	// Infrastructure
	logger      *logger.Logger
	metrics     *metrics.Collector
	eventBus    *eventbus.Client
	ctx         context.Context
	cancelFunc  context.CancelFunc
	
	// Thresholds
	activationThreshold float64 // Sensitivity for state transition
}

// AgentState represents the current state of the platelet agent.
type AgentState int

const (
	StateResting AgentState = iota
	StateActivated
	StateAggregated
)

func (s AgentState) String() string {
	return [...]string{"Resting", "Activated", "Aggregated"}[s]
}

// Config holds agent configuration.
type Config struct {
	AgentID             string
	NATSEndpoint        string
	ActivationThreshold float64
	Debug               bool
}

// NewAgent creates a new Platelet Digital agent.
//
// Parameters:
//   - config: Agent configuration
//
// Returns initialized agent ready for Start().
func NewAgent(config *Config) (*Agent, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	// Initialize logger
	log, err := logger.NewLogger("platelet-agent", "phase1", config.Debug)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to initialize logger: %w", err)
	}
	
	// Initialize metrics
	metricsCollector := metrics.NewCollector("platelet-agent", "detection")
	
	// Initialize event bus
	bus, err := eventbus.NewClient(config.NATSEndpoint, config.AgentID)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to connect to event bus: %w", err)
	}
	
	// Get hostname
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown"
	}
	
	// Initialize sensors (Phase 1 - basic implementation)
	processSensor := sensors.NewProcessMonitor(log, metricsCollector)
	networkSensor := sensors.NewNetworkMonitor(log, metricsCollector)
	fileSensor := sensors.NewFileMonitor(log, metricsCollector)
	
	agent := &Agent{
		id:                  config.AgentID,
		hostname:            hostname,
		state:               StateResting,
		processSensor:       processSensor,
		networkSensor:       networkSensor,
		fileSensor:          fileSensor,
		logger:              log,
		metrics:             metricsCollector,
		eventBus:            bus,
		ctx:                 ctx,
		cancelFunc:          cancel,
		activationThreshold: config.ActivationThreshold,
	}
	
	log.Info("platelet_agent_initialized",
		logger.String("agent_id", config.AgentID),
		logger.String("hostname", hostname),
		logger.String("state", agent.state.String()),
	)
	
	return agent, nil
}

// Start begins agent monitoring loop.
//
// This is the "circulation" phase - agent is alive, monitoring, ready to activate.
func (a *Agent) Start() error {
	a.logger.Info("platelet_agent_starting",
		logger.String("agent_id", a.id),
	)
	
	// Start sensors
	if err := a.processSensor.Start(a.ctx); err != nil {
		return fmt.Errorf("failed to start process sensor: %w", err)
	}
	if err := a.networkSensor.Start(a.ctx); err != nil {
		return fmt.Errorf("failed to start network sensor: %w", err)
	}
	if err := a.fileSensor.Start(a.ctx); err != nil {
		return fmt.Errorf("failed to start file sensor: %w", err)
	}
	
	// Subscribe to peer signals (P2P communication)
	if err := a.subscribeToPeerSignals(); err != nil {
		return fmt.Errorf("failed to subscribe to peer signals: %w", err)
	}
	
	// Start monitoring loop
	go a.monitoringLoop()
	
	a.logger.Info("platelet_agent_started",
		logger.String("state", a.state.String()),
	)
	
	return nil
}

// monitoringLoop is the main agent loop.
//
// Biological: Like platelets circulating and sensing endothelial damage.
// Digital: Continuous monitoring for integrity violations.
func (a *Agent) monitoringLoop() {
	ticker := time.NewTicker(100 * time.Millisecond) // 10 Hz sampling rate
	defer ticker.Stop()
	
	for {
		select {
		case <-a.ctx.Done():
			a.logger.Info("monitoring_loop_terminated")
			return
			
		case <-ticker.C:
			a.checkForAnomalies()
		}
	}
}

// checkForAnomalies aggregates sensor signals and decides state transition.
//
// This is the "adhesion detection" phase - sensing if there's "damage".
func (a *Agent) checkForAnomalies() {
	// Aggregate anomaly scores from all sensors
	processScore := a.processSensor.GetAnomalyScore()
	networkScore := a.networkSensor.GetAnomalyScore()
	fileScore := a.fileSensor.GetAnomalyScore()
	
	// Combined score (weighted average - can be ML model in future)
	combinedScore := (processScore*0.4 + networkScore*0.4 + fileScore*0.2)
	
	// State transition logic
	if a.state == StateResting && combinedScore >= a.activationThreshold {
		a.activate(combinedScore)
	} else if a.state == StateActivated && combinedScore < a.activationThreshold*0.5 {
		a.deactivate()
	}
}

// activate transitions agent from Resting to Activated state.
//
// Biological: Platelet adhesion to damaged endothelium, shape change.
// Digital: Increased vigilance, active interrogation, signal emission.
func (a *Agent) activate(anomalyScore float64) {
	a.state = StateActivated
	
	a.logger.WithCascadeStage("initiation").Info("platelet_activated",
		logger.String("agent_id", a.id),
		logger.Float64("anomaly_score", anomalyScore),
		logger.String("previous_state", "Resting"),
		logger.String("new_state", "Activated"),
	)
	
	// Update metrics
	a.metrics.UpdateSystemHealth(1.0 - anomalyScore) // Inverse: high anomaly = low health
	a.metrics.RecordBreachDetection(0.0, anomalyScore) // Latency TBD, severity = score
	
	// Emit activation signal to peers (ADP/TXA2 equivalent)
	a.emitActivationSignal(anomalyScore)
	
	// Emit to detection layer (trigger cascade if severe enough)
	if anomalyScore >= 0.8 {
		a.emitBreachDetectedEvent(anomalyScore)
	}
}

// deactivate transitions agent back to Resting state.
//
// Biological: Platelet returns to circulation after false alarm.
// Digital: Return to passive monitoring.
func (a *Agent) deactivate() {
	a.state = StateResting
	
	a.logger.Info("platelet_deactivated",
		logger.String("agent_id", a.id),
		logger.String("previous_state", "Activated"),
		logger.String("new_state", "Resting"),
	)
	
	a.metrics.UpdateSystemHealth(1.0) // Healthy
	a.metrics.EmotionalValence.Set(0.0) // Neutral
}

// emitActivationSignal sends P2P signal to nearby agents.
//
// Biological: Release of ADP/TXA2 to recruit more platelets.
// Digital: gRPC streaming to peer agents for coordinated response.
func (a *Agent) emitActivationSignal(severity float64) {
	event := &eventbus.Event{
		ID:               fmt.Sprintf("%s-%d", a.id, time.Now().UnixNano()),
		Type:             "platelet_activation",
		BreachID:         a.generateBreachID(),
		CascadeStage:     "initiation",
		EmotionalValence: -0.9 * severity, // Negative (aversive)
		Severity:         severity,
	}
	
	if err := a.eventBus.Publish(a.ctx, "coagulation.platelet.activated", event); err != nil {
		a.logger.Error("failed to emit activation signal", logger.Error(err))
	}
}

// emitBreachDetectedEvent sends event to detection layer for cascade triggering.
//
// This is the transition from platelet activation to Factor VIIa activation.
func (a *Agent) emitBreachDetectedEvent(severity float64) {
	breachID := a.generateBreachID()
	
	event := &eventbus.Event{
		ID:               breachID,
		Type:             "breach_detected",
		BreachID:         breachID,
		CascadeStage:     "initiation",
		EmotionalValence: -0.9,
		Severity:         severity,
	}
	
	if err := a.eventBus.Publish(a.ctx, eventbus.SubjectBreachDetected, event); err != nil {
		a.logger.Error("failed to emit breach event", logger.Error(err))
		return
	}
	
	a.logger.LogBreachDetection(breachID, severity, a.hostname)
}

// subscribeToPeerSignals subscribes to activation signals from peer agents.
//
// Biological: Platelets sense ADP/TXA2 from nearby activated platelets.
// Digital: NATS subscription to peer activation events.
func (a *Agent) subscribeToPeerSignals() error {
	return a.eventBus.Subscribe("coagulation.platelet.activated", "platelet-peer-signals", 
		func(event *eventbus.Event) error {
			// Ignore own signals
			if event.Source == a.id {
				return nil
			}
			
			a.logger.Info("peer_activation_received",
				logger.String("peer_id", event.Source),
				logger.Float64("severity", event.Severity),
			)
			
			// Amplify response - peer activation increases our sensitivity
			if a.state == StateResting && event.Severity >= 0.7 {
				a.activate(event.Severity * 0.8) // Slightly reduced score from peer
			}
			
			return nil
		},
	)
}

// generateBreachID generates unique breach identifier.
func (a *Agent) generateBreachID() string {
	return fmt.Sprintf("breach-%s-%d", a.id, time.Now().UnixNano())
}

// Shutdown gracefully stops the agent.
func (a *Agent) Shutdown() error {
	a.logger.Info("platelet_agent_shutting_down",
		logger.String("agent_id", a.id),
	)
	
	a.cancelFunc()
	a.eventBus.Close()
	
	return nil
}

func main() {
	// Parse flags
	agentID := flag.String("id", "", "Agent ID (required)")
	natsURL := flag.String("nats", "nats://localhost:4222", "NATS server URL")
	threshold := flag.Float64("threshold", 0.7, "Activation threshold (0.0-1.0)")
	debug := flag.Bool("debug", false, "Enable debug logging")
	flag.Parse()
	
	if *agentID == "" {
		fmt.Println("Error: --id flag is required")
		flag.Usage()
		os.Exit(1)
	}
	
	// Create agent
	config := &Config{
		AgentID:             *agentID,
		NATSEndpoint:        *natsURL,
		ActivationThreshold: *threshold,
		Debug:               *debug,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		fmt.Printf("Failed to create agent: %v\n", err)
		os.Exit(1)
	}
	
	// Start agent
	if err := agent.Start(); err != nil {
		fmt.Printf("Failed to start agent: %v\n", err)
		os.Exit(1)
	}
	
	fmt.Printf("🩸 Platelet Agent %s started (state: %s)\n", *agentID, agent.state)
	
	// Wait for shutdown signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan
	
	fmt.Println("\n🛑 Shutdown signal received")
	
	// Graceful shutdown
	if err := agent.Shutdown(); err != nil {
		fmt.Printf("Error during shutdown: %v\n", err)
		os.Exit(1)
	}
	
	fmt.Println("✅ Agent stopped gracefully")
}

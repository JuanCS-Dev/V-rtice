package cascade

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// FactorXaService activates quarantine response.
//
// Biological Analogy: Factor Xa is central to coagulation cascade,
// activating prothrombin → thrombin. Similarly, this service receives
// validated triggers and activates massive policy generation.
//
// Role: Amplification initiator - turns 1 signal into many
type FactorXaService struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client
	
	// Amplification parameters
	baseAmplification int     // Minimum rules per trigger
	maxAmplification  int     // Maximum rules per trigger
	severityMultiplier float64 // Severity affects amplification
	
	// Active quarantines tracking
	activeQuarantines map[string]*QuarantineSession
	mu                sync.RWMutex
	
	ctx        context.Context
	cancelFunc context.CancelFunc
}

// QuarantineSession tracks an active quarantine response.
type QuarantineSession struct {
	BreachID      string
	StartTime     time.Time
	Severity      float64
	Source        string // "extrinsic" or "intrinsic"
	RulesGenerated int
	Status        QuarantineStatus
}

// QuarantineStatus represents quarantine state.
type QuarantineStatus int

const (
	StatusInitiating QuarantineStatus = iota
	StatusAmplifying
	StatusContained
	StatusRegulated
)

func (s QuarantineStatus) String() string {
	return [...]string{"Initiating", "Amplifying", "Contained", "Regulated"}[s]
}

// NewFactorXaService creates the quarantine activator.
func NewFactorXaService(natsURL string) (*FactorXaService, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	log, err := logger.NewLogger("factor-xa", "phase3", false)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to init logger: %w", err)
	}
	
	metrics := metrics.NewCollector("factor-xa", "amplification")
	
	bus, err := eventbus.NewClient(natsURL, "factor-xa")
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to connect to event bus: %w", err)
	}
	
	service := &FactorXaService{
		logger:             log,
		metrics:            metrics,
		eventBus:           bus,
		baseAmplification:  100,   // Minimum 100 rules
		maxAmplification:   10000, // Maximum 10,000 rules
		severityMultiplier: 1000,  // Severity scales amplification
		activeQuarantines:  make(map[string]*QuarantineSession),
		ctx:                ctx,
		cancelFunc:         cancel,
	}
	
	log.Info("factor_xa_initialized",
		logger.Int("base_amplification", service.baseAmplification),
		logger.Int("max_amplification", service.maxAmplification),
	)
	
	return service, nil
}

// Start begins listening for cascade triggers.
func (fx *FactorXaService) Start() error {
	fx.logger.Info("factor_xa_starting")
	
	// Subscribe to cascade triggers from Factor VIIa
	err := fx.eventBus.Subscribe(
		eventbus.SubjectCascadeTriggered,
		"factor-xa-activator",
		fx.handleCascadeTrigger,
	)
	if err != nil {
		return fmt.Errorf("failed to subscribe: %w", err)
	}
	
	fx.logger.Info("factor_xa_started")
	return nil
}

// handleCascadeTrigger receives cascade trigger and activates amplification.
//
// This is where 1 trigger becomes 1000+ rules.
func (fx *FactorXaService) handleCascadeTrigger(event *eventbus.Event) error {
	startTime := time.Now()
	
	fx.logger.WithCascadeStage("amplification").Info("cascade_trigger_received",
		logger.String("breach_id", event.BreachID),
		logger.Float64("severity", event.Severity),
	)
	
	// Calculate amplification based on severity
	amplification := fx.calculateAmplification(event.Severity)
	
	fx.logger.WithCascadeStage("amplification").Info("amplification_calculated",
		logger.String("breach_id", event.BreachID),
		logger.Int("amplification", amplification),
		logger.Float64("severity", event.Severity),
	)
	
	// Create quarantine session
	session := &QuarantineSession{
		BreachID:       event.BreachID,
		StartTime:      startTime,
		Severity:       event.Severity,
		Source:         "cascade", // From VIIa
		RulesGenerated: amplification,
		Status:         StatusAmplifying,
	}
	
	fx.mu.Lock()
	fx.activeQuarantines[event.BreachID] = session
	fx.mu.Unlock()
	
	// Record metrics
	fx.metrics.CascadeActivations.Inc()
	fx.metrics.AmplificationRatio.Observe(float64(amplification))
	
	// Activate Thrombin Burst for policy generation
	if err := fx.activateThrombin(event.BreachID, amplification, event.Severity); err != nil {
		fx.logger.Error("failed to activate thrombin", logger.Error(err))
		return err
	}
	
	latency := time.Since(startTime).Seconds()
	fx.logger.WithCascadeStage("amplification").Info("factor_xa_activated",
		logger.String("breach_id", event.BreachID),
		logger.Int("amplification", amplification),
		logger.Float64("latency_ms", latency*1000),
	)
	
	return nil
}

// calculateAmplification determines how many rules to generate.
//
// Biological: Thrombin generation is exponential (~1000x amplification).
// Digital: Severity determines rule count (higher severity = more rules).
func (fx *FactorXaService) calculateAmplification(severity float64) int {
	// Base + (severity * multiplier)
	amplification := fx.baseAmplification + int(severity*fx.severityMultiplier)
	
	// Cap at maximum
	if amplification > fx.maxAmplification {
		amplification = fx.maxAmplification
	}
	
	// Minimum baseline
	if amplification < fx.baseAmplification {
		amplification = fx.baseAmplification
	}
	
	return amplification
}

// activateThrombin triggers Thrombin Burst service for policy generation.
func (fx *FactorXaService) activateThrombin(breachID string, ruleCount int, severity float64) error {
	event := &eventbus.Event{
		ID:               fmt.Sprintf("thrombin-%s", breachID),
		Type:             "thrombin_activated",
		BreachID:         breachID,
		CascadeStage:     "amplification",
		EmotionalValence: -1.0,
		Severity:         severity,
	}
	
	if err := fx.eventBus.Publish(fx.ctx, eventbus.SubjectFactorActivated, event); err != nil {
		return err
	}
	
	fx.logger.Info("thrombin_activated",
		logger.String("breach_id", breachID),
		logger.Int("rule_count", ruleCount),
	)
	
	return nil
}

// GetActiveQuarantines returns currently active quarantine sessions.
func (fx *FactorXaService) GetActiveQuarantines() map[string]*QuarantineSession {
	fx.mu.RLock()
	defer fx.mu.RUnlock()
	
	// Return copy
	result := make(map[string]*QuarantineSession)
	for k, v := range fx.activeQuarantines {
		result[k] = v
	}
	return result
}

// Shutdown gracefully stops the service.
func (fx *FactorXaService) Shutdown() error {
	fx.logger.Info("factor_xa_shutting_down")
	fx.cancelFunc()
	fx.eventBus.Close()
	return nil
}

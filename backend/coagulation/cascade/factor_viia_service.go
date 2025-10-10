package cascade

import (
	"context"
	"fmt"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// FactorVIIaService is the trigger dispatcher - validates and routes events.
//
// Biological Analogy: Factor VIIa binds to Tissue Factor (TF) to initiate
// coagulation cascade. Similarly, this service validates triggers from
// both pathways and activates cascade services.
//
// Role: Convergence point for Extrinsic + Intrinsic pathways
type FactorVIIaService struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client
	
	// Thresholds for cascade activation
	extrinsicThreshold  float64 // Min confidence for Extrinsic (should be 1.0)
	intrinsicThreshold  float64 // Min confidence for Intrinsic (0.7)
	correlationRequired int     // Min signals for Intrinsic
	
	ctx        context.Context
	cancelFunc context.CancelFunc
}

// TriggerEvent represents a validated trigger ready for cascade.
type TriggerEvent struct {
	ID         string
	BreachID   string
	Source     string  // "extrinsic" or "intrinsic"
	Confidence float64
	Severity   float64
	Validated  bool
}

// NewFactorVIIaService creates the trigger dispatcher.
func NewFactorVIIaService(natsURL string) (*FactorVIIaService, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	log, err := logger.NewLogger("factor-viia", "phase2", false)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to init logger: %w", err)
	}
	
	metrics := metrics.NewCollector("factor-viia", "cascade")
	
	bus, err := eventbus.NewClient(natsURL, "factor-viia")
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to connect to event bus: %w", err)
	}
	
	service := &FactorVIIaService{
		logger:              log,
		metrics:             metrics,
		eventBus:            bus,
		extrinsicThreshold:  1.0,  // Perfect confidence required
		intrinsicThreshold:  0.7,  // High confidence required
		correlationRequired: 3,    // 3+ signals required
		ctx:                 ctx,
		cancelFunc:          cancel,
	}
	
	log.Info("factor_viia_initialized")
	return service, nil
}

// Start begins listening for validated triggers.
func (f *FactorVIIaService) Start() error {
	f.logger.Info("factor_viia_starting")
	
	// Subscribe to Extrinsic pathway (TF-validated IoCs)
	err := f.eventBus.Subscribe(
		eventbus.SubjectIoCValidated,
		"factor-viia-extrinsic",
		f.handleExtrinsicTrigger,
	)
	if err != nil {
		return fmt.Errorf("failed to subscribe to extrinsic: %w", err)
	}
	
	// Subscribe to Intrinsic pathway (correlated anomalies)
	err = f.eventBus.Subscribe(
		eventbus.SubjectAnomalyDetected,
		"factor-viia-intrinsic",
		f.handleIntrinsicTrigger,
	)
	if err != nil {
		return fmt.Errorf("failed to subscribe to intrinsic: %w", err)
	}
	
	f.logger.Info("factor_viia_started")
	return nil
}

// handleExtrinsicTrigger processes high-fidelity IoC triggers.
//
// Extrinsic = Tissue Factor pathway = Immediate activation
func (f *FactorVIIaService) handleExtrinsicTrigger(event *eventbus.Event) error {
	f.logger.WithCascadeStage("amplification").Info("extrinsic_trigger_received",
		logger.String("breach_id", event.BreachID),
		logger.Float64("severity", event.Severity),
	)
	
	// Extrinsic triggers are pre-validated by TF (confidence=1.0)
	// Activate cascade immediately
	trigger := &TriggerEvent{
		ID:         event.ID,
		BreachID:   event.BreachID,
		Source:     "extrinsic",
		Confidence: 1.0,
		Severity:   event.Severity,
		Validated:  true,
	}
	
	return f.activateCascade(trigger)
}

// handleIntrinsicTrigger processes anomaly-based triggers.
//
// Intrinsic = Collagen pathway = Requires validation
func (f *FactorVIIaService) handleIntrinsicTrigger(event *eventbus.Event) error {
	f.logger.WithCascadeStage("amplification").Debug("intrinsic_trigger_received",
		logger.String("breach_id", event.BreachID),
		logger.Float64("severity", event.Severity),
	)
	
	// Intrinsic triggers require threshold check
	if event.Severity < f.intrinsicThreshold {
		f.logger.Debug("intrinsic_trigger_below_threshold",
			logger.String("breach_id", event.BreachID),
			logger.Float64("severity", event.Severity),
			logger.Float64("threshold", f.intrinsicThreshold),
		)
		return nil // Below threshold
	}
	
	// Above threshold - activate cascade
	trigger := &TriggerEvent{
		ID:         event.ID,
		BreachID:   event.BreachID,
		Source:     "intrinsic",
		Confidence: event.Severity, // Use severity as confidence proxy
		Severity:   event.Severity,
		Validated:  true,
	}
	
	return f.activateCascade(trigger)
}

// activateCascade triggers the amplification cascade.
//
// This is the key convergence point - both pathways lead here.
// From here, Factor Xa is activated (Phase 3).
func (f *FactorVIIaService) activateCascade(trigger *TriggerEvent) error {
	f.logger.WithCascadeStage("amplification").Info("cascade_activated",
		logger.String("trigger_id", trigger.ID),
		logger.String("breach_id", trigger.BreachID),
		logger.String("source", trigger.Source),
		logger.Float64("confidence", trigger.Confidence),
		logger.Float64("severity", trigger.Severity),
	)
	
	f.metrics.CascadeActivations.Inc()
	
	// Emit cascade trigger event
	cascadeEvent := &eventbus.Event{
		ID:               fmt.Sprintf("cascade-%s", trigger.ID),
		Type:             "cascade_triggered",
		BreachID:         trigger.BreachID,
		CascadeStage:     "amplification",
		EmotionalValence: -1.0, // Maximum negative (cascade active)
		Severity:         trigger.Severity,
	}
	
	if err := f.eventBus.Publish(f.ctx, eventbus.SubjectCascadeTriggered, cascadeEvent); err != nil {
		f.logger.Error("failed to emit cascade trigger", logger.Error(err))
		return err
	}
	
	f.logger.Info("cascade_trigger_emitted",
		logger.String("breach_id", trigger.BreachID),
	)
	
	return nil
}

// Shutdown gracefully stops the service.
func (f *FactorVIIaService) Shutdown() error {
	f.logger.Info("factor_viia_shutting_down")
	f.cancelFunc()
	f.eventBus.Close()
	return nil
}

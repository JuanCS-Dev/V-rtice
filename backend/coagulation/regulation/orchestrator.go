package regulation

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// RegulationOrchestrator coordinates all regulation services.
//
// Integrates:
// - Protein C/S (context-aware containment)
// - Antithrombin (global dampening)
// - TFPI (trigger validation)
//
// Provides unified regulation layer for the cascade.
type RegulationOrchestrator struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client

	// Regulation services
	proteinC     *ProteinCService
	proteinS     *ProteinSService
	antithrombin *AntithrombinService
	tfpi         *TFPIService

	// State
	started bool
	mu      sync.RWMutex

	ctx        context.Context
	cancelFunc context.CancelFunc
}

// RegulationMetrics aggregates regulation statistics.
type RegulationMetrics struct {
	Timestamp time.Time

	// Protein C metrics
	InhibitionCount      int
	AllowanceCount       int
	AverageHealthScore   float64

	// Antithrombin metrics
	DampeningActive      bool
	DampeningIntensity   float64
	EmergencyActivations int

	// TFPI metrics
	TriggersValidated    int
	TriggersRejected     int
	PendingTriggers      int

	// Overall
	SystemSafe           bool
	RegulationEffective  bool
}

// NewRegulationOrchestrator creates the regulation coordinator.
func NewRegulationOrchestrator(
	logger *logger.Logger,
	metrics *metrics.Collector,
	eventBus *eventbus.Client,
) *RegulationOrchestrator {
	ctx, cancel := context.WithCancel(context.Background())

	return &RegulationOrchestrator{
		logger:   logger,
		metrics:  metrics,
		eventBus: eventBus,

		proteinC:     NewProteinCService(logger, metrics, eventBus),
		proteinS:     NewProteinSService(logger, metrics, eventBus),
		antithrombin: NewAntithrombinServiceWithDeps(logger, metrics, eventBus),
		tfpi:         NewTFPIService(logger, metrics, eventBus),

		started: false,

		ctx:        ctx,
		cancelFunc: cancel,
	}
}

// Start initializes all regulation services.
func (r *RegulationOrchestrator) Start() error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.started {
		return fmt.Errorf("regulation orchestrator already started")
	}

	r.logger.Info("🩸 Starting Regulation Orchestrator - CASCADE CONTROL LAYER")

	// Start services in order
	services := []struct {
		name    string
		starter func() error
	}{
		{"TFPI (Trigger Validation)", r.tfpi.Start},
		{"Protein S (Health Cofactor)", r.proteinS.Start},
		{"Protein C (Context-Aware Inhibition)", r.proteinC.Start},
		{"Antithrombin (Global Dampening)", r.antithrombin.Start},
	}

	for _, svc := range services {
		r.logger.Info(fmt.Sprintf("  ↳ Starting %s...", svc.name))
		if err := svc.starter(); err != nil {
			return fmt.Errorf("failed to start %s: %w", svc.name, err)
		}
		r.logger.Info(fmt.Sprintf("  ✓ %s ACTIVE", svc.name))
	}

	// Start orchestration monitoring
	go r.monitoringLoop()

	r.started = true

	r.logger.Info("✅ Regulation Orchestrator ACTIVE - Cascade under conscious control")
	return nil
}

// Stop gracefully stops all regulation services.
func (r *RegulationOrchestrator) Stop() error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if !r.started {
		return nil
	}

	r.logger.Info("Stopping Regulation Orchestrator")

	// Stop in reverse order
	services := []struct {
		name    string
		stopper func() error
	}{
		{"Antithrombin", r.antithrombin.Stop},
		{"Protein C", r.proteinC.Stop},
		{"Protein S", r.proteinS.Stop},
		{"TFPI", r.tfpi.Stop},
	}

	for _, svc := range services {
		if err := svc.stopper(); err != nil {
			r.logger.Error(fmt.Sprintf("Error stopping %s", svc.name), logger.Error(err))
		}
	}

	r.cancelFunc()
	r.started = false

	r.logger.Info("Regulation Orchestrator stopped")
	return nil
}

// GetProteinCService returns Protein C service.
func (r *RegulationOrchestrator) GetProteinCService() *ProteinCService {
	return r.proteinC
}

// GetProteinSService returns Protein S service.
func (r *RegulationOrchestrator) GetProteinSService() *ProteinSService {
	return r.proteinS
}

// GetAntithrombinService returns Antithrombin service.
func (r *RegulationOrchestrator) GetAntithrombinService() *AntithrombinService {
	return r.antithrombin
}

// GetTFPIService returns TFPI service.
func (r *RegulationOrchestrator) GetTFPIService() *TFPIService {
	return r.tfpi
}

// GetMetrics aggregates regulation metrics.
func (r *RegulationOrchestrator) GetMetrics() *RegulationMetrics {
	return &RegulationMetrics{
		Timestamp:            time.Now(),
		DampeningActive:      r.antithrombin.IsDampeningActive(),
		DampeningIntensity:   r.antithrombin.GetDampeningIntensity(),
		PendingTriggers:      r.tfpi.GetPendingCount(),
		SystemSafe:           !r.antithrombin.DetectSystemWideImpact(),
		RegulationEffective:  r.isRegulationEffective(),
	}
}

// isRegulationEffective checks if regulation is working properly.
func (r *RegulationOrchestrator) isRegulationEffective() bool {
	// All services running
	if !r.started {
		return false
	}

	// No emergency dampening active (system healthy)
	if r.antithrombin.IsDampeningActive() {
		return false
	}

	return true
}

// monitoringLoop continuously monitors regulation health.
func (r *RegulationOrchestrator) monitoringLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			r.performHealthCheck()
		case <-r.ctx.Done():
			return
		}
	}
}

// performHealthCheck validates regulation layer health.
func (r *RegulationOrchestrator) performHealthCheck() {
	metrics := r.GetMetrics()

	r.logger.Info("Regulation Health Check",
		logger.Bool("system_safe", metrics.SystemSafe),
		logger.Bool("dampening_active", metrics.DampeningActive),
		logger.Int("pending_triggers", metrics.PendingTriggers),
		logger.Bool("regulation_effective", metrics.RegulationEffective),
	)

	// Publish metrics
	ctx := context.Background()
	r.eventBus.Publish(ctx, "regulation.health_check", createEvent("regulation.health_check", map[string]interface{}{
		"metrics": metrics,
	}))

	// Record to Prometheus
	if metrics.DampeningActive {
		r.metrics.RecordGauge("regulation_dampening_active", 1.0, nil)
	} else {
		r.metrics.RecordGauge("regulation_dampening_active", 0.0, nil)
	}

	r.metrics.RecordGauge("regulation_pending_triggers", float64(metrics.PendingTriggers), nil)
}

// ValidateTriggerWithRegulation validates trigger through TFPI.
func (r *RegulationOrchestrator) ValidateTriggerWithRegulation(trigger *PendingTrigger) *ValidationResult {
	return r.tfpi.ValidateTrigger(trigger)
}

// RegulateQuarantineExpansion evaluates expansion through Protein C.
func (r *RegulationOrchestrator) RegulateQuarantineExpansion(qctx *QuarantineContext) error {
	return r.proteinC.RegulateExpansion(qctx)
}

// CheckSystemImpact evaluates system-wide impact through Antithrombin.
func (r *RegulationOrchestrator) CheckSystemImpact() bool {
	return r.antithrombin.DetectSystemWideImpact()
}

// AcceleratedHealthCheck performs optimized health check through Protein S.
func (r *RegulationOrchestrator) AcceleratedHealthCheck(segmentID string) (*HealthStatus, error) {
	return r.proteinS.AccelerateHealthCheck(segmentID, r.proteinC)
}

// IsStarted returns orchestrator state.
func (r *RegulationOrchestrator) IsStarted() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.started
}


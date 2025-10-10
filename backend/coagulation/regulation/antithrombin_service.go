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

// AntithrombinService implements global dampening and circuit breaker.
//
// Biological Analogy: Antithrombin III (ATIII) is the master inhibitor that
// binds to and inactivates thrombin globally. It provides system-wide
// dampening to prevent uncontrolled coagulation (thrombosis).
//
// Digital Function: Emergency circuit breaker that detects catastrophic
// false positives and reduces cascade intensity system-wide.
//
// Critical Role: Prevents "digital thrombosis" - complete system paralysis
// due to over-aggressive quarantine.
type AntithrombinService struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client

	// State tracking
	activeQuarantines    map[string]*QuarantineMetrics
	systemImpact         *SystemImpactMetrics
	dampeningActive      bool
	dampeningIntensity   float64 // 0.0-1.0 (1.0 = full dampening)
	mu                   sync.RWMutex

	// Configuration
	impactThreshold      float64       // System impact threshold for emergency dampening
	dampeningDuration    time.Duration // How long to maintain dampening
	monitoringInterval   time.Duration

	ctx        context.Context
	cancelFunc context.CancelFunc
}

// QuarantineMetrics tracks individual quarantine impact.
type QuarantineMetrics struct {
	BreachID           string
	StartTime          time.Time
	AffectedAssets     int
	NetworkSegments    int
	ProcessesTerminated int
	ServicesDown       int
	BusinessImpact     float64 // 0.0-1.0
}

// SystemImpactMetrics tracks overall system health impact.
type SystemImpactMetrics struct {
	Timestamp              time.Time
	
	// Aggregate metrics
	TotalQuarantines       int
	TotalAffectedAssets    int
	TotalProcessesKilled   int
	TotalServicesDown      int
	
	// System-wide impact
	CPUAvailability        float64 // % of CPU still available
	NetworkThroughput      float64 // % of bandwidth still available
	ServiceAvailability    float64 // % of critical services still up
	
	// Business impact
	BusinessImpactScore    float64 // 0.0-1.0 (0 = no impact, 1 = total shutdown)
	
	// Alerting
	CriticalThresholdReached bool
	HumanOperatorsAlerted    bool
}

// DampeningDecision represents emergency dampening action.
type DampeningDecision struct {
	ID                  string
	Timestamp           time.Time
	Trigger             string // What triggered dampening
	SystemImpact        *SystemImpactMetrics
	DampeningIntensity  float64
	Duration            time.Duration
	HumanAlert          bool
}

// NewAntithrombinService creates global dampening service.
func NewAntithrombinService(
	logger *logger.Logger,
	metrics *metrics.Collector,
	eventBus *eventbus.Client,
) *AntithrombinService {
	ctx, cancel := context.WithCancel(context.Background())

	return &AntithrombinService{
		logger:   logger,
		metrics:  metrics,
		eventBus: eventBus,

		activeQuarantines: make(map[string]*QuarantineMetrics),
		systemImpact: &SystemImpactMetrics{
			CPUAvailability:     1.0,
			NetworkThroughput:   1.0,
			ServiceAvailability: 1.0,
		},
		dampeningActive:    false,
		dampeningIntensity: 0.0,

		impactThreshold:    0.7, // 70% system impact triggers emergency
		dampeningDuration:  5 * time.Minute,
		monitoringInterval: 10 * time.Second,

		ctx:        ctx,
		cancelFunc: cancel,
	}
}

// Start begins monitoring and regulation.
func (a *AntithrombinService) Start() error {
	a.logger.Info("Starting Antithrombin Service (Global Dampening)")

	// Subscribe to critical events
	if err := a.eventBus.Subscribe("quarantine.applied", a.handleQuarantineApplied); err != nil {
		return fmt.Errorf("failed to subscribe to quarantine events: %w", err)
	}

	if err := a.eventBus.Subscribe("system.impact", a.handleSystemImpact); err != nil {
		return fmt.Errorf("failed to subscribe to system impact events: %w", err)
	}

	// Start monitoring loop
	go a.monitoringLoop()

	a.logger.Info("Antithrombin Service active - monitoring for over-quarantine")
	return nil
}

// Stop gracefully stops the service.
func (a *AntithrombinService) Stop() error {
	a.logger.Info("Stopping Antithrombin Service")
	a.cancelFunc()
	return nil
}

// EmergencyDampening activates global cascade dampening.
//
// CRITICAL FUNCTION: This is the "emergency brake" that prevents
// catastrophic false positives from paralyzing the entire system.
func (a *AntithrombinService) EmergencyDampening() error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if a.dampeningActive {
		a.logger.Warn("Emergency dampening already active")
		return nil
	}

	impact := a.calculateSystemImpact()
	
	decision := &DampeningDecision{
		ID:                 fmt.Sprintf("damp-%d", time.Now().Unix()),
		Timestamp:          time.Now(),
		Trigger:            "system_wide_impact_threshold_exceeded",
		SystemImpact:       impact,
		DampeningIntensity: a.calculateDampeningIntensity(impact),
		Duration:           a.dampeningDuration,
		HumanAlert:         true,
	}

	a.logger.Error("EMERGENCY DAMPENING ACTIVATED",
		"impact_score", impact.BusinessImpactScore,
		"dampening_intensity", decision.DampeningIntensity,
		"affected_assets", impact.TotalAffectedAssets,
		"services_down", impact.TotalServicesDown,
	)

	// Activate dampening
	a.dampeningActive = true
	a.dampeningIntensity = decision.DampeningIntensity

	// Alert human operators
	if decision.HumanAlert {
		a.alertHumanOperators(decision)
	}

	// Publish dampening event
	a.eventBus.Publish("regulation.emergency_dampening", map[string]interface{}{
		"decision": decision,
		"impact":   impact,
	})

	// Metrics
	a.metrics.IncrementCounter("emergency_dampening_total", map[string]string{
		"trigger": decision.Trigger,
	})
	a.metrics.RecordGauge("dampening_intensity", decision.DampeningIntensity, nil)

	// Schedule deactivation
	go a.scheduleDeactivation(decision.Duration)

	return nil
}

// ReduceResponseIntensity applies dampening to cascade operations.
func (a *AntithrombinService) ReduceResponseIntensity(reduction float64) {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.logger.Warn("Reducing cascade response intensity",
		"reduction_factor", reduction,
		"from_intensity", 1.0,
		"to_intensity", 1.0-reduction,
	)

	// Publish intensity reduction
	a.eventBus.Publish("regulation.intensity_reduction", map[string]interface{}{
		"reduction": reduction,
		"timestamp": time.Now(),
	})

	a.metrics.RecordGauge("cascade_intensity_multiplier", 1.0-reduction, nil)
}

// DetectSystemWideImpact checks if cascade is causing unacceptable impact.
func (a *AntithrombinService) DetectSystemWideImpact() bool {
	impact := a.calculateSystemImpact()
	
	return impact.BusinessImpactScore >= a.impactThreshold
}

// calculateSystemImpact computes current system impact metrics.
func (a *AntithrombinService) calculateSystemImpact() *SystemImpactMetrics {
	a.mu.RLock()
	defer a.mu.RUnlock()

	impact := &SystemImpactMetrics{
		Timestamp:        time.Now(),
		TotalQuarantines: len(a.activeQuarantines),
	}

	// Aggregate quarantine metrics
	totalAssets := 0
	totalProcesses := 0
	totalServices := 0

	for _, qm := range a.activeQuarantines {
		totalAssets += qm.AffectedAssets
		totalProcesses += qm.ProcessesTerminated
		totalServices += qm.ServicesDown
	}

	impact.TotalAffectedAssets = totalAssets
	impact.TotalProcessesKilled = totalProcesses
	impact.TotalServicesDown = totalServices

	// Calculate system-wide metrics
	// TODO: Integrate with real system metrics
	impact.CPUAvailability = a.calculateCPUAvailability()
	impact.NetworkThroughput = a.calculateNetworkThroughput()
	impact.ServiceAvailability = a.calculateServiceAvailability()

	// Business impact score (weighted)
	impact.BusinessImpactScore = (1.0-impact.CPUAvailability)*0.2 +
		(1.0-impact.NetworkThroughput)*0.2 +
		(1.0-impact.ServiceAvailability)*0.6

	impact.CriticalThresholdReached = impact.BusinessImpactScore >= a.impactThreshold

	return impact
}

// calculateDampeningIntensity determines how much to dampen.
func (a *AntithrombinService) calculateDampeningIntensity(impact *SystemImpactMetrics) float64 {
	// Proportional to impact severity
	if impact.BusinessImpactScore >= 0.9 {
		return 0.8 // 80% reduction (near shutdown)
	} else if impact.BusinessImpactScore >= 0.8 {
		return 0.6 // 60% reduction
	} else if impact.BusinessImpactScore >= 0.7 {
		return 0.4 // 40% reduction
	}
	return 0.2 // 20% reduction (minimal)
}

// calculateCPUAvailability estimates remaining CPU capacity.
func (a *AntithrombinService) calculateCPUAvailability() float64 {
	// TODO: Integrate with system metrics (Prometheus)
	// Simulated: 80% available
	return 0.80
}

// calculateNetworkThroughput estimates remaining bandwidth.
func (a *AntithrombinService) calculateNetworkThroughput() float64 {
	// TODO: Integrate with network metrics
	// Simulated: 75% available
	return 0.75
}

// calculateServiceAvailability estimates critical service uptime.
func (a *AntithrombinService) calculateServiceAvailability() float64 {
	a.mu.RLock()
	totalServicesDown := 0
	for _, qm := range a.activeQuarantines {
		totalServicesDown += qm.ServicesDown
	}
	a.mu.RUnlock()

	// Assume 100 total critical services
	totalCriticalServices := 100
	availability := float64(totalCriticalServices-totalServicesDown) / float64(totalCriticalServices)
	
	if availability < 0 {
		return 0
	}
	return availability
}

// alertHumanOperators sends critical alerts.
func (a *AntithrombinService) alertHumanOperators(decision *DampeningDecision) {
	a.logger.Error("HUMAN OPERATOR ALERT: Emergency Dampening Active",
		"decision_id", decision.ID,
		"business_impact", decision.SystemImpact.BusinessImpactScore,
		"dampening_intensity", decision.DampeningIntensity,
		"affected_assets", decision.SystemImpact.TotalAffectedAssets,
		"services_down", decision.SystemImpact.TotalServicesDown,
	)

	// TODO: Integrate with alerting system (PagerDuty, Slack, etc.)
	// Publish critical alert event
	a.eventBus.Publish("alerts.critical", map[string]interface{}{
		"type":     "emergency_dampening",
		"decision": decision,
		"severity": "CRITICAL",
		"requires_human_intervention": true,
	})
}

// scheduleDeactivation deactivates dampening after duration.
func (a *AntithrombinService) scheduleDeactivation(duration time.Duration) {
	time.Sleep(duration)

	a.mu.Lock()
	defer a.mu.Unlock()

	a.logger.Info("Emergency dampening duration expired - deactivating",
		"duration", duration,
	)

	a.dampeningActive = false
	a.dampeningIntensity = 0.0

	// Metrics
	a.metrics.RecordGauge("dampening_intensity", 0.0, nil)

	// Publish deactivation event
	a.eventBus.Publish("regulation.dampening_deactivated", map[string]interface{}{
		"timestamp": time.Now(),
		"duration":  duration,
	})
}

// handleQuarantineApplied tracks new quarantines.
func (a *AntithrombinService) handleQuarantineApplied(event map[string]interface{}) {
	breachID := event["breach_id"].(string)
	
	metrics := &QuarantineMetrics{
		BreachID:  breachID,
		StartTime: time.Now(),
		// Extract from event
		AffectedAssets:      extractInt(event, "affected_assets"),
		NetworkSegments:     extractInt(event, "network_segments"),
		ProcessesTerminated: extractInt(event, "processes_terminated"),
		ServicesDown:        extractInt(event, "services_down"),
	}

	a.mu.Lock()
	a.activeQuarantines[breachID] = metrics
	a.mu.Unlock()

	a.logger.Debug("Tracking new quarantine",
		"breach_id", breachID,
		"affected_assets", metrics.AffectedAssets,
	)
}

// handleSystemImpact processes system impact updates.
func (a *AntithrombinService) handleSystemImpact(event map[string]interface{}) {
	// Update system impact metrics
	a.mu.Lock()
	a.systemImpact.Timestamp = time.Now()
	// Update fields from event
	a.mu.Unlock()
}

// monitoringLoop continuously monitors for over-quarantine.
func (a *AntithrombinService) monitoringLoop() {
	ticker := time.NewTicker(a.monitoringInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if a.DetectSystemWideImpact() && !a.dampeningActive {
				a.logger.Warn("System-wide impact detected - triggering emergency dampening")
				if err := a.EmergencyDampening(); err != nil {
					a.logger.Error("Failed to activate emergency dampening", "error", err)
				}
			}
		case <-a.ctx.Done():
			return
		}
	}
}

// GetDampeningIntensity returns current dampening multiplier.
func (a *AntithrombinService) GetDampeningIntensity() float64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.dampeningIntensity
}

// IsDampeningActive returns dampening state.
func (a *AntithrombinService) IsDampeningActive() bool {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.dampeningActive
}

// extractInt safely extracts int from event map.
func extractInt(event map[string]interface{}, key string) int {
	if val, ok := event[key]; ok {
		if intVal, ok := val.(int); ok {
			return intVal
		}
	}
	return 0
}

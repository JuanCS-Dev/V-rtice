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

// ThrombinBurstService generates massive policy sets.
//
// Biological Analogy: Thrombin burst is the explosive phase of coagulation
// where prothrombin is cleaved into thrombin at 1000x+ rate. Similarly,
// this service generates 1000+ quarantine policies from single trigger.
//
// Role: Exponential policy generator - THE amplification engine
type ThrombinBurstService struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client
	
	// Policy generation
	policyTemplates  []*PolicyTemplate
	generationWorkers int
	
	// Generation tracking
	activeBursts map[string]*BurstSession
	mu           sync.RWMutex
	
	ctx        context.Context
	cancelFunc context.CancelFunc
}

// BurstSession tracks policy generation burst.
type BurstSession struct {
	BreachID         string
	StartTime        time.Time
	TargetPolicies   int
	GeneratedPolicies int
	Status           BurstStatus
	Policies         []*QuarantinePolicy
}

// BurstStatus represents burst generation state.
type BurstStatus int

const (
	BurstInitiated BurstStatus = iota
	BurstGenerating
	BurstComplete
	BurstApplying
)

// PolicyTemplate defines policy generation patterns.
type PolicyTemplate struct {
	Name        string
	Type        string // "network", "process", "file", "system"
	Severity    float64
	Action      string // "isolate", "block", "quarantine", "terminate"
	Template    string
}

// QuarantinePolicy represents a single quarantine rule.
type QuarantinePolicy struct {
	ID          string
	BreachID    string
	Type        string
	Target      string
	Action      string
	Severity    float64
	Generated   time.Time
	Applied     bool
}

// NewThrombinBurstService creates the policy generator.
func NewThrombinBurstService(natsURL string) (*ThrombinBurstService, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	log, err := logger.NewLogger("thrombin-burst", "phase3", false)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to init logger: %w", err)
	}
	
	metrics := metrics.NewCollector("thrombin-burst", "amplification")
	
	bus, err := eventbus.NewClient(natsURL, "thrombin-burst")
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to connect to event bus: %w", err)
	}
	
	service := &ThrombinBurstService{
		logger:            log,
		metrics:           metrics,
		eventBus:          bus,
		policyTemplates:   initPolicyTemplates(),
		generationWorkers: 10, // Parallel policy generation
		activeBursts:      make(map[string]*BurstSession),
		ctx:               ctx,
		cancelFunc:        cancel,
	}
	
	log.Info("thrombin_burst_initialized",
		logger.Int("policy_templates", len(service.policyTemplates)),
		logger.Int("workers", service.generationWorkers),
	)
	
	return service, nil
}

// initPolicyTemplates creates default policy templates.
func initPolicyTemplates() []*PolicyTemplate {
	return []*PolicyTemplate{
		{
			Name:     "network_isolate_ip",
			Type:     "network",
			Severity: 0.9,
			Action:   "isolate",
			Template: "DENY from {source_ip} to any",
		},
		{
			Name:     "network_block_port",
			Type:     "network",
			Severity: 0.8,
			Action:   "block",
			Template: "DENY tcp port {port}",
		},
		{
			Name:     "process_terminate",
			Type:     "process",
			Severity: 1.0,
			Action:   "terminate",
			Template: "KILL process {pid}",
		},
		{
			Name:     "file_quarantine",
			Type:     "file",
			Severity: 0.85,
			Action:   "quarantine",
			Template: "MOVE {file} to /quarantine/",
		},
		{
			Name:     "system_isolate_segment",
			Type:     "system",
			Severity: 0.95,
			Action:   "isolate",
			Template: "ISOLATE network segment {segment}",
		},
	}
}

// Start begins listening for thrombin activation.
func (tb *ThrombinBurstService) Start() error {
	tb.logger.Info("thrombin_burst_starting")
	
	// Subscribe to Factor Xa activations
	err := tb.eventBus.Subscribe(
		eventbus.SubjectFactorActivated,
		"thrombin-burst-generator",
		tb.handleThrombinActivation,
	)
	if err != nil {
		return fmt.Errorf("failed to subscribe: %w", err)
	}
	
	tb.logger.Info("thrombin_burst_started")
	return nil
}

// handleThrombinActivation triggers explosive policy generation.
//
// THIS IS THE AMPLIFICATION MOMENT - 1 → 1000+
func (tb *ThrombinBurstService) handleThrombinActivation(event *eventbus.Event) error {
	startTime := time.Now()
	
	tb.logger.WithCascadeStage("amplification").Info("thrombin_activation_received",
		logger.String("breach_id", event.BreachID),
		logger.Float64("severity", event.Severity),
	)
	
	// Calculate target policy count (extracted from Factor Xa metadata)
	// Phase 3: Use severity-based calculation
	targetPolicies := tb.calculatePolicyCount(event.Severity)
	
	tb.logger.WithCascadeStage("amplification").Info("policy_burst_starting",
		logger.String("breach_id", event.BreachID),
		logger.Int("target_policies", targetPolicies),
	)
	
	// Create burst session
	session := &BurstSession{
		BreachID:       event.BreachID,
		StartTime:      startTime,
		TargetPolicies: targetPolicies,
		Status:         BurstGenerating,
		Policies:       make([]*QuarantinePolicy, 0, targetPolicies),
	}
	
	tb.mu.Lock()
	tb.activeBursts[event.BreachID] = session
	tb.mu.Unlock()
	
	// GENERATE POLICIES (THE BURST!)
	policies := tb.generatePolicies(event.BreachID, targetPolicies, event.Severity)
	
	// Update session
	tb.mu.Lock()
	session.GeneratedPolicies = len(policies)
	session.Policies = policies
	session.Status = BurstComplete
	tb.mu.Unlock()
	
	// Record metrics
	tb.metrics.ThromburstGenerated.Add(float64(len(policies)))
	tb.metrics.AmplificationRatio.Observe(float64(len(policies)))
	
	latency := time.Since(startTime)
	
	tb.logger.WithCascadeStage("amplification").Info("policy_burst_complete",
		logger.String("breach_id", event.BreachID),
		logger.Int("policies_generated", len(policies)),
		logger.Float64("latency_ms", latency.Seconds()*1000),
		logger.Float64("policies_per_second", float64(len(policies))/latency.Seconds()),
	)
	
	// Emit to Fibrin Mesh for application
	return tb.activateFibrin(event.BreachID, policies)
}

// calculatePolicyCount determines how many policies to generate.
func (tb *ThrombinBurstService) calculatePolicyCount(severity float64) int {
	// Base: 100 policies
	// High severity: up to 5000 policies
	base := 100
	max := 5000
	
	count := base + int(severity*float64(max-base))
	
	return count
}

// generatePolicies creates the policy burst.
//
// Phase 3: Template-based generation.
// Future: ML-based context-aware policy generation.
func (tb *ThrombinBurstService) generatePolicies(breachID string, count int, severity float64) []*QuarantinePolicy {
	policies := make([]*QuarantinePolicy, 0, count)
	
	// Distribute across templates
	policiesPerTemplate := count / len(tb.policyTemplates)
	if policiesPerTemplate == 0 {
		policiesPerTemplate = 1
	}
	
	policyID := 0
	
	for _, template := range tb.policyTemplates {
		for i := 0; i < policiesPerTemplate && policyID < count; i++ {
			policy := &QuarantinePolicy{
				ID:       fmt.Sprintf("%s-policy-%d", breachID, policyID),
				BreachID: breachID,
				Type:     template.Type,
				Target:   fmt.Sprintf("target-%d", policyID),
				Action:   template.Action,
				Severity: severity * template.Severity,
				Generated: time.Now(),
				Applied:  false,
			}
			
			policies = append(policies, policy)
			policyID++
		}
	}
	
	return policies
}

// activateFibrin sends policies to Fibrin Mesh for enforcement.
func (tb *ThrombinBurstService) activateFibrin(breachID string, policies []*QuarantinePolicy) error {
	event := &eventbus.Event{
		ID:               fmt.Sprintf("fibrin-%s", breachID),
		Type:             "fibrin_forming",
		BreachID:         breachID,
		CascadeStage:     "containment",
		EmotionalValence: -1.0,
		Severity:         1.0,
	}
	
	if err := tb.eventBus.Publish(tb.ctx, eventbus.SubjectThromburstGenerated, event); err != nil {
		return err
	}
	
	tb.logger.WithCascadeStage("containment").Info("fibrin_mesh_activated",
		logger.String("breach_id", breachID),
		logger.Int("policies", len(policies)),
	)
	
	return nil
}

// GetActiveBursts returns current policy generation sessions.
func (tb *ThrombinBurstService) GetActiveBursts() map[string]*BurstSession {
	tb.mu.RLock()
	defer tb.mu.RUnlock()
	
	result := make(map[string]*BurstSession)
	for k, v := range tb.activeBursts {
		result[k] = v
	}
	return result
}

// Shutdown gracefully stops the service.
func (tb *ThrombinBurstService) Shutdown() error {
	tb.logger.Info("thrombin_burst_shutting_down")
	tb.cancelFunc()
	tb.eventBus.Close()
	return nil
}

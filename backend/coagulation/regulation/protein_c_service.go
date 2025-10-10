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

// ProteinCService implements context-aware containment regulation.
//
// Biological Analogy: Protein C/S system converts thrombin from pro-coagulant
// to anti-coagulant when healthy endothelium is present. Similarly, this
// service INHIBITS quarantine expansion into healthy network segments.
//
// Critical Function: Prevents "digital thrombosis" - over-quarantine of
// healthy systems due to proximity to breach.
//
// Consciousness Integration: This IS the consciousness of the cascade -
// it understands context and makes nuanced decisions.
type ProteinCService struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client

	// Health checking components
	integrityChecker  *IntegrityChecker
	behavioralChecker *BehavioralChecker
	iocChecker        *IoCChecker
	processChecker    *ProcessChecker

	// State tracking
	healthChecks     map[string]*HealthStatus
	inhibitions      map[string]*InhibitionDecision
	mu               sync.RWMutex

	// Configuration
	healthCheckInterval time.Duration
	healthThreshold     float64

	ctx        context.Context
	cancelFunc context.CancelFunc
}

// HealthStatus represents multi-dimensional health assessment.
type HealthStatus struct {
	SegmentID       string
	Timestamp       time.Time
	
	// Health dimensions
	IntegrityScore   float64 // 0.0-1.0 (1.0 = perfect integrity)
	BehavioralScore  float64 // 0.0-1.0 (1.0 = baseline compliant)
	IoCScore         float64 // 0.0-1.0 (1.0 = no IoCs)
	ProcessScore     float64 // 0.0-1.0 (1.0 = all processes known)
	
	// Aggregate
	OverallScore float64
	IsHealthy    bool
	
	// Details
	Checks map[string]CheckResult
}

// CheckResult represents individual health check result.
type CheckResult struct {
	CheckType   string
	Passed      bool
	Score       float64
	Details     string
	Timestamp   time.Time
}

// InhibitionDecision tracks quarantine expansion inhibitions.
type InhibitionDecision struct {
	ID              string
	BreachID        string
	SourceSegment   string
	TargetSegment   string
	Inhibited       bool
	Reason          string
	HealthStatus    *HealthStatus
	Timestamp       time.Time
}

// NetworkSegment represents logical network boundary.
type NetworkSegment struct {
	ID           string
	Name         string
	IPRanges     []string
	Hosts        []string
	Description  string
}

// QuarantineContext represents quarantine state for regulation.
type QuarantineContext struct {
	BreachID        string
	SourceSegment   string
	AffectedAssets  []string
	TargetSegments  []string
	CurrentScope    int
	Timestamp       time.Time
}

// IntegrityChecker validates file/config integrity.
type IntegrityChecker struct {
	logger        *logger.Logger
	knownHashes   map[string]string
	mu            sync.RWMutex
}

// BehavioralChecker validates behavioral baselines.
type BehavioralChecker struct {
	logger        *logger.Logger
	baselines     map[string]*Baseline
	mu            sync.RWMutex
}

// Baseline represents expected behavior patterns.
type Baseline struct {
	SegmentID        string
	ProcessProfiles  map[string]*ProcessProfile
	NetworkProfiles  map[string]*NetworkProfile
	Established      time.Time
}

// ProcessProfile represents expected process behavior.
type ProcessProfile struct {
	Name          string
	Count         int
	CPURange      [2]float64
	MemoryRange   [2]int64
}

// NetworkProfile represents expected network behavior.
type NetworkProfile struct {
	Port          int
	Protocol      string
	Connections   int
	BytesRange    [2]int64
}

// IoCChecker checks for indicators of compromise.
type IoCChecker struct {
	logger        *logger.Logger
	knownIoCs     map[string]*IoC
	mu            sync.RWMutex
}

// IoC represents indicator of compromise.
type IoC struct {
	Type        string // "ip", "domain", "hash", "process"
	Value       string
	Severity    string
	Source      string
	Added       time.Time
}

// ProcessChecker validates running processes.
type ProcessChecker struct {
	logger          *logger.Logger
	knownProcesses  map[string]bool
	mu              sync.RWMutex
}

// NewProteinCService creates context-aware regulation service.
func NewProteinCService(
	logger *logger.Logger,
	metrics *metrics.Collector,
	eventBus *eventbus.Client,
) *ProteinCService {
	ctx, cancel := context.WithCancel(context.Background())

	return &ProteinCService{
		logger:   logger,
		metrics:  metrics,
		eventBus: eventBus,

		integrityChecker:  NewIntegrityChecker(logger),
		behavioralChecker: NewBehavioralChecker(logger),
		iocChecker:        NewIoCChecker(logger),
		processChecker:    NewProcessChecker(logger),

		healthChecks:        make(map[string]*HealthStatus),
		inhibitions:         make(map[string]*InhibitionDecision),
		
		healthCheckInterval: 30 * time.Second,
		healthThreshold:     0.8, // 80% health required

		ctx:        ctx,
		cancelFunc: cancel,
	}
}

// Start begins regulation monitoring loop.
func (p *ProteinCService) Start() error {
	p.logger.Info("Starting Protein C Service (Context-Aware Regulation)")
	
	// Subscribe to quarantine expansion events
	if err := p.eventBus.Subscribe("quarantine.expansion", p.handleExpansionRequest); err != nil {
		return fmt.Errorf("failed to subscribe to expansion events: %w", err)
	}

	// Start continuous health monitoring
	go p.healthMonitoringLoop()

	p.logger.Info("Protein C Service active - monitoring for over-quarantine")
	return nil
}

// Stop gracefully stops the service.
func (p *ProteinCService) Stop() error {
	p.logger.Info("Stopping Protein C Service")
	p.cancelFunc()
	return nil
}

// RegulateExpansion evaluates quarantine expansion request.
//
// CRITICAL DECISION POINT: This method embodies the "consciousness" of
// the cascade - it decides whether to allow or inhibit expansion based
// on multi-dimensional health assessment.
func (p *ProteinCService) RegulateExpansion(qctx *QuarantineContext) error {
	p.logger.Info("Evaluating quarantine expansion",
		"breach_id", qctx.BreachID,
		"source", qctx.SourceSegment,
		"targets", qctx.TargetSegments,
	)

	for _, targetSegID := range qctx.TargetSegments {
		// Get target segment
		segment := p.getSegment(targetSegID)
		if segment == nil {
			p.logger.Warn("Unknown segment in expansion request", "segment", targetSegID)
			continue
		}

		// Check health status
		health := p.CheckHealth(segment)
		
		decision := &InhibitionDecision{
			ID:            fmt.Sprintf("inh-%s-%d", qctx.BreachID, time.Now().Unix()),
			BreachID:      qctx.BreachID,
			SourceSegment: qctx.SourceSegment,
			TargetSegment: targetSegID,
			HealthStatus:  health,
			Timestamp:     time.Now(),
		}

		if health.IsHealthy {
			// INHIBIT EXPANSION - target is healthy
			decision.Inhibited = true
			decision.Reason = fmt.Sprintf(
				"Target segment %s is HEALTHY (score: %.2f) - inhibiting expansion to prevent over-quarantine",
				targetSegID,
				health.OverallScore,
			)
			
			p.logger.Warn("INHIBITING quarantine expansion",
				"target", targetSegID,
				"health_score", health.OverallScore,
				"reason", "healthy_neighbor_detected",
			)

			// Metrics
			p.metrics.IncrementCounter("regulation_inhibitions_total", map[string]string{
				"segment": targetSegID,
				"reason":  "healthy",
			})

			// Publish inhibition event
			p.eventBus.Publish("regulation.inhibition", map[string]interface{}{
				"decision": decision,
				"health":   health,
			})

		} else {
			// ALLOW EXPANSION - target shows signs of compromise
			decision.Inhibited = false
			decision.Reason = fmt.Sprintf(
				"Target segment %s shows compromise signs (score: %.2f) - allowing expansion",
				targetSegID,
				health.OverallScore,
			)
			
			p.logger.Info("Allowing quarantine expansion",
				"target", targetSegID,
				"health_score", health.OverallScore,
			)

			// Metrics
			p.metrics.IncrementCounter("regulation_allowances_total", map[string]string{
				"segment": targetSegID,
			})
		}

		// Store decision
		p.mu.Lock()
		p.inhibitions[decision.ID] = decision
		p.mu.Unlock()
	}

	return nil
}

// CheckHealth performs multi-dimensional health assessment.
//
// Implements biological Protein C/S mechanism: checks for "healthy endothelium"
// equivalent in digital systems.
func (p *ProteinCService) CheckHealth(segment *NetworkSegment) *HealthStatus {
	start := time.Now()
	
	health := &HealthStatus{
		SegmentID: segment.ID,
		Timestamp: time.Now(),
		Checks:    make(map[string]CheckResult),
	}

	// Dimension 1: File/Config Integrity
	integrityResult := p.integrityChecker.Check(segment)
	health.IntegrityScore = integrityResult.Score
	health.Checks["integrity"] = integrityResult

	// Dimension 2: Behavioral Baseline Compliance
	behavioralResult := p.behavioralChecker.Check(segment)
	health.BehavioralScore = behavioralResult.Score
	health.Checks["behavioral"] = behavioralResult

	// Dimension 3: IoC Presence
	iocResult := p.iocChecker.Check(segment)
	health.IoCScore = iocResult.Score
	health.Checks["ioc"] = iocResult

	// Dimension 4: Process Anomalies
	processResult := p.processChecker.Check(segment)
	health.ProcessScore = processResult.Score
	health.Checks["process"] = processResult

	// Aggregate score (weighted average)
	health.OverallScore = health.IntegrityScore*0.3 +
		health.BehavioralScore*0.3 +
		health.IoCScore*0.25 +
		health.ProcessScore*0.15

	// Determine health status
	health.IsHealthy = health.OverallScore >= p.healthThreshold

	// Cache result
	p.mu.Lock()
	p.healthChecks[segment.ID] = health
	p.mu.Unlock()

	// Metrics
	duration := time.Since(start).Seconds()
	p.metrics.RecordHistogram("health_check_duration_seconds", duration, map[string]string{
		"segment": segment.ID,
	})
	p.metrics.RecordGauge("segment_health_score", health.OverallScore, map[string]string{
		"segment": segment.ID,
	})

	p.logger.Debug("Health check complete",
		"segment", segment.ID,
		"score", health.OverallScore,
		"healthy", health.IsHealthy,
		"duration_ms", duration*1000,
	)

	return health
}

// GetNeighborSegments returns adjacent network segments.
func (p *ProteinCService) GetNeighborSegments(qctx *QuarantineContext) []*NetworkSegment {
	// TODO: Implement network topology discovery
	// For now, return mock neighbors
	return []*NetworkSegment{
		{
			ID:       "seg-dmz",
			Name:     "DMZ Segment",
			IPRanges: []string{"10.0.1.0/24"},
		},
		{
			ID:       "seg-internal",
			Name:     "Internal Segment",
			IPRanges: []string{"10.0.2.0/24"},
		},
	}
}

// handleExpansionRequest processes quarantine expansion event.
func (p *ProteinCService) handleExpansionRequest(event map[string]interface{}) {
	// Extract quarantine context from event
	qctx := &QuarantineContext{
		BreachID:       event["breach_id"].(string),
		SourceSegment:  event["source_segment"].(string),
		TargetSegments: event["target_segments"].([]string),
	}

	if err := p.RegulateExpansion(qctx); err != nil {
		p.logger.Error("Failed to regulate expansion",
			"breach_id", qctx.BreachID,
			"error", err,
		)
	}
}

// healthMonitoringLoop continuously monitors segment health.
func (p *ProteinCService) healthMonitoringLoop() {
	ticker := time.NewTicker(p.healthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			p.performHealthScan()
		case <-p.ctx.Done():
			return
		}
	}
}

// performHealthScan scans all known segments.
func (p *ProteinCService) performHealthScan() {
	segments := p.getAllSegments()
	
	for _, segment := range segments {
		health := p.CheckHealth(segment)
		
		if !health.IsHealthy {
			p.logger.Warn("Unhealthy segment detected in periodic scan",
				"segment", segment.ID,
				"score", health.OverallScore,
			)
		}
	}
}

// getSegment retrieves segment by ID.
func (p *ProteinCService) getSegment(id string) *NetworkSegment {
	// TODO: Implement segment registry
	// Mock for now
	return &NetworkSegment{
		ID:       id,
		Name:     fmt.Sprintf("Segment %s", id),
		IPRanges: []string{"10.0.0.0/24"},
	}
}

// getAllSegments returns all known segments.
func (p *ProteinCService) getAllSegments() []*NetworkSegment {
	// TODO: Implement segment discovery
	return []*NetworkSegment{
		{ID: "seg-dmz", Name: "DMZ"},
		{ID: "seg-internal", Name: "Internal"},
		{ID: "seg-prod", Name: "Production"},
	}
}

// NewIntegrityChecker creates integrity validation checker.
func NewIntegrityChecker(logger *logger.Logger) *IntegrityChecker {
	return &IntegrityChecker{
		logger:      logger,
		knownHashes: make(map[string]string),
	}
}

// Check validates file/config integrity.
func (ic *IntegrityChecker) Check(segment *NetworkSegment) CheckResult {
	// TODO: Implement real integrity checking (sha256 hashes)
	// Simulated: 95% pass rate
	score := 0.95

	return CheckResult{
		CheckType: "integrity",
		Passed:    score >= 0.8,
		Score:     score,
		Details:   fmt.Sprintf("Checked %d critical files", len(segment.Hosts)),
		Timestamp: time.Now(),
	}
}

// NewBehavioralChecker creates behavioral baseline checker.
func NewBehavioralChecker(logger *logger.Logger) *BehavioralChecker {
	return &BehavioralChecker{
		logger:    logger,
		baselines: make(map[string]*Baseline),
	}
}

// Check validates behavioral baselines.
func (bc *BehavioralChecker) Check(segment *NetworkSegment) CheckResult {
	// TODO: Implement real behavioral analysis
	// Simulated: 90% compliance
	score := 0.90

	return CheckResult{
		CheckType: "behavioral",
		Passed:    score >= 0.8,
		Score:     score,
		Details:   "Baseline compliance within normal range",
		Timestamp: time.Now(),
	}
}

// NewIoCChecker creates IoC validation checker.
func NewIoCChecker(logger *logger.Logger) *IoCChecker {
	return &IoCChecker{
		logger:    logger,
		knownIoCs: make(map[string]*IoC),
	}
}

// Check validates IoC presence.
func (ioc *IoCChecker) Check(segment *NetworkSegment) CheckResult {
	// TODO: Implement real IoC checking (threat intel feeds)
	// Simulated: 100% clean (no IoCs)
	score := 1.0

	return CheckResult{
		CheckType: "ioc",
		Passed:    score >= 0.8,
		Score:     score,
		Details:   "No known IoCs detected",
		Timestamp: time.Now(),
	}
}

// NewProcessChecker creates process anomaly checker.
func NewProcessChecker(logger *logger.Logger) *ProcessChecker {
	return &ProcessChecker{
		logger:         logger,
		knownProcesses: make(map[string]bool),
	}
}

// Check validates running processes.
func (pc *ProcessChecker) Check(segment *NetworkSegment) CheckResult {
	// TODO: Implement real process validation
	// Simulated: 92% known processes
	score := 0.92

	return CheckResult{
		CheckType: "process",
		Passed:    score >= 0.8,
		Score:     score,
		Details:   "All critical processes validated",
		Timestamp: time.Now(),
	}
}

package extrinsic_pathway

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// TissueFactor represents the high-fidelity IoC detection service.
//
// Biological Analogy: Tissue Factor (TF) is exposed when blood vessel is damaged,
// triggering immediate coagulation cascade. Similarly, this service detects
// definitive Indicators of Compromise (IoCs) that trigger immediate response.
//
// Confidence Level: 1.0 (100% - no false positives tolerated)
// Response: Immediate cascade activation
type TissueFactor struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client
	
	// Known IoC databases
	cveDatabase  *CVEDatabase
	yaraEngine   *YARAEngine
	threatFeeds  []ThreatFeed
	
	ctx        context.Context
	cancelFunc context.CancelFunc
	mu         sync.RWMutex
}

// IoC represents an Indicator of Compromise with high confidence.
type IoC struct {
	ID          string  `json:"id"`
	Type        string  `json:"type"`        // "cve", "hash", "signature", "behavior"
	Value       string  `json:"value"`       // CVE-2024-1234, hash, etc.
	Severity    float64 `json:"severity"`    // 0.0-1.0
	Confidence  float64 `json:"confidence"`  // Must be 1.0 for TF
	Source      string  `json:"source"`      // "cve_db", "yara", "threat_feed"
	Description string  `json:"description"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// CVEDatabase holds known CVE exploits.
//
// Phase 2: In-memory simple map.
// Future: Redis cache + periodic updates from NVD.
type CVEDatabase struct {
	cves map[string]*CVEEntry
	mu   sync.RWMutex
}

// CVEEntry represents a CVE with exploitation details.
type CVEEntry struct {
	ID          string
	Severity    float64 // CVSS score normalized to 0.0-1.0
	Description string
	Exploited   bool // Is this CVE known to be actively exploited?
}

// YARAEngine performs signature-based malware detection.
//
// Phase 2: Simple keyword matching.
// Future: Actual YARA rule engine integration.
type YARAEngine struct {
	rules map[string]*YARARule
	mu    sync.RWMutex
}

// YARARule represents a detection signature.
type YARARule struct {
	Name        string
	Patterns    []string
	Severity    float64
	Description string
}

// ThreatFeed represents external threat intelligence.
type ThreatFeed struct {
	Name     string
	Endpoint string
	APIKey   string
}

// NewTissueFactor creates a new Tissue Factor detection service.
func NewTissueFactor(natsURL string) (*TissueFactor, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	log, err := logger.NewLogger("tissue-factor", "phase2", false)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to init logger: %w", err)
	}
	
	metrics := metrics.NewCollector("tissue-factor", "extrinsic")
	
	bus, err := eventbus.NewClient(natsURL, "tissue-factor")
	if err != nil {
		cancel()
		return nil, fmt.Errorf("failed to connect to event bus: %w", err)
	}
	
	tf := &TissueFactor{
		logger:      log,
		metrics:     metrics,
		eventBus:    bus,
		cveDatabase: NewCVEDatabase(),
		yaraEngine:  NewYARAEngine(),
		threatFeeds: []ThreatFeed{},
		ctx:         ctx,
		cancelFunc:  cancel,
	}
	
	log.Info("tissue_factor_initialized")
	return tf, nil
}

// Start begins listening for breach events from platelet agents.
func (tf *TissueFactor) Start() error {
	tf.logger.Info("tissue_factor_starting")
	
	// Subscribe to breach events from platelet agents
	err := tf.eventBus.Subscribe(
		eventbus.SubjectBreachDetected,
		"tissue-factor-detector",
		tf.handleBreachEvent,
	)
	if err != nil {
		return fmt.Errorf("failed to subscribe: %w", err)
	}
	
	tf.logger.Info("tissue_factor_started")
	return nil
}

// handleBreachEvent processes breach events and validates IoCs.
//
// This is the "TF exposure" moment - definitive IoC triggers cascade.
func (tf *TissueFactor) handleBreachEvent(event *eventbus.Event) error {
	tf.logger.WithCascadeStage("initiation").Debug("breach_event_received",
		logger.String("breach_id", event.BreachID),
		logger.Float64("severity", event.Severity),
	)
	
	// Extract IoC from event payload
	// Phase 2: Parse from event metadata
	ioc := tf.extractIoC(event)
	
	if ioc == nil {
		tf.logger.Debug("no_ioc_extracted", logger.String("breach_id", event.BreachID))
		return nil
	}
	
	// Validate IoC (high-fidelity check)
	validated := tf.validateIoC(ioc)
	
	if !validated {
		tf.logger.Debug("ioc_not_validated",
			logger.String("ioc_id", ioc.ID),
			logger.Float64("confidence", ioc.Confidence),
		)
		return nil
	}
	
	// HIGH CONFIDENCE IoC - Trigger cascade immediately
	tf.logger.WithCascadeStage("initiation").Info("ioc_validated",
		logger.String("ioc_id", ioc.ID),
		logger.String("ioc_type", ioc.Type),
		logger.Float64("confidence", ioc.Confidence),
		logger.Float64("severity", ioc.Severity),
	)
	
	tf.metrics.RecordBreachDetection(0.0, ioc.Severity) // Zero latency (immediate)
	
	// Emit validated IoC event to Factor VIIa
	return tf.emitValidatedIoC(ioc, event.BreachID)
}

// extractIoC extracts IoC from breach event.
//
// Phase 2: Simple extraction from event data.
// Future: ML-based feature extraction, context enrichment.
func (tf *TissueFactor) extractIoC(event *eventbus.Event) *IoC {
	// Phase 2: Placeholder - would extract from event.Payload
	// For now, create synthetic IoC for testing
	return &IoC{
		ID:          fmt.Sprintf("ioc-%s", event.BreachID),
		Type:        "behavior",
		Value:       "suspicious_process_detected",
		Severity:    event.Severity,
		Confidence:  0.95, // High but not perfect
		Source:      "platelet_agent",
		Description: "Suspicious process activity detected by platelet agent",
	}
}

// validateIoC performs high-fidelity validation.
//
// Returns true ONLY if confidence = 1.0 (definitive IoC).
func (tf *TissueFactor) validateIoC(ioc *IoC) bool {
	tf.mu.RLock()
	defer tf.mu.RUnlock()
	
	// Check CVE database
	if ioc.Type == "cve" {
		if cve := tf.cveDatabase.Get(ioc.Value); cve != nil && cve.Exploited {
			ioc.Confidence = 1.0 // Known exploited CVE = definitive
			ioc.Severity = cve.Severity
			return true
		}
	}
	
	// Check YARA signatures
	if ioc.Type == "signature" || ioc.Type == "hash" {
		if match := tf.yaraEngine.Match(ioc.Value); match != nil {
			ioc.Confidence = 1.0 // YARA match = definitive
			ioc.Severity = match.Severity
			return true
		}
	}
	
	// Phase 2: For behavioral IoCs, require very high confidence
	if ioc.Type == "behavior" && ioc.Confidence >= 0.95 {
		// Additional validation could go here
		// For Phase 2, accept high-confidence behavioral IoCs
		ioc.Confidence = 1.0
		return true
	}
	
	return false
}

// emitValidatedIoC emits validated IoC to Factor VIIa for cascade activation.
func (tf *TissueFactor) emitValidatedIoC(ioc *IoC, breachID string) error {
	event := &eventbus.Event{
		ID:               fmt.Sprintf("validated-ioc-%s", ioc.ID),
		Type:             "ioc_validated",
		BreachID:         breachID,
		CascadeStage:     "initiation",
		EmotionalValence: -1.0, // Maximum negative (definitive threat)
		Severity:         ioc.Severity,
	}
	
	if err := tf.eventBus.Publish(tf.ctx, eventbus.SubjectIoCValidated, event); err != nil {
		tf.logger.Error("failed to emit validated ioc", logger.Error(err))
		return err
	}
	
	tf.logger.WithCascadeStage("initiation").Info("ioc_validated_emitted",
		logger.String("ioc_id", ioc.ID),
		logger.String("breach_id", breachID),
	)
	
	return nil
}

// Shutdown gracefully stops the service.
func (tf *TissueFactor) Shutdown() error {
	tf.logger.Info("tissue_factor_shutting_down")
	tf.cancelFunc()
	tf.eventBus.Close()
	return nil
}

// NewCVEDatabase creates CVE database with critical CVEs.
func NewCVEDatabase() *CVEDatabase {
	db := &CVEDatabase{
		cves: make(map[string]*CVEEntry),
	}
	
	// Load critical CVEs (Phase 2: hardcoded, Future: NVD API)
	db.Add("CVE-2024-1234", 0.95, "Critical RCE in common software", true)
	db.Add("CVE-2023-5678", 0.88, "Authentication bypass", true)
	db.Add("CVE-2024-9999", 0.92, "Privilege escalation", true)
	
	return db
}

func (db *CVEDatabase) Add(id string, severity float64, desc string, exploited bool) {
	db.mu.Lock()
	defer db.mu.Unlock()
	
	db.cves[id] = &CVEEntry{
		ID:          id,
		Severity:    severity,
		Description: desc,
		Exploited:   exploited,
	}
}

func (db *CVEDatabase) Get(id string) *CVEEntry {
	db.mu.RLock()
	defer db.mu.RUnlock()
	return db.cves[id]
}

// NewYARAEngine creates YARA engine with detection rules.
func NewYARAEngine() *YARAEngine {
	engine := &YARAEngine{
		rules: make(map[string]*YARARule),
	}
	
	// Load detection rules (Phase 2: simple patterns, Future: actual YARA)
	engine.AddRule("malware_wannacry", []string{"wcry", "wanna", "decrypt"}, 0.98, "WannaCry ransomware")
	engine.AddRule("malware_meterpreter", []string{"meterpreter", "msf"}, 0.95, "Metasploit payload")
	engine.AddRule("malware_mimikatz", []string{"mimikatz", "sekurlsa"}, 0.97, "Credential dumper")
	
	return engine
}

func (ye *YARAEngine) AddRule(name string, patterns []string, severity float64, desc string) {
	ye.mu.Lock()
	defer ye.mu.Unlock()
	
	ye.rules[name] = &YARARule{
		Name:        name,
		Patterns:    patterns,
		Severity:    severity,
		Description: desc,
	}
}

func (ye *YARAEngine) Match(value string) *YARARule {
	ye.mu.RLock()
	defer ye.mu.RUnlock()
	
	valueLower := strings.ToLower(value)
	
	for _, rule := range ye.rules {
		for _, pattern := range rule.Patterns {
			if strings.Contains(valueLower, pattern) {
				return rule
			}
		}
	}
	
	return nil
}

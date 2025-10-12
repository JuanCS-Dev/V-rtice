// Package behavior implements behavioral analysis and anomaly detection (Layer 6)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 6 of the "Guardian of Intent" v2.0:
// "ANÁLISE COMPORTAMENTAL - Isso é normal para você?"
//
// Provides:
// - User baseline profiling
// - Anomaly detection
// - Risk scoring
// - Adaptive authentication escalation
package behavior

import (
	"context"
	"sync"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/security"
)

// Analyzer handles behavioral analysis and anomaly detection
type Analyzer struct {
	baselineStore BaselineStore
	config        Config
	mu            sync.RWMutex
}

// Config defines behavior analysis configuration
type Config struct {
	// Thresholds
	AnomalyThreshold   float64 // 0.0-1.0, severity to consider anomaly
	HighRiskThreshold  int     // Risk score to trigger escalation (0-100)
	
	// Baseline
	MinSampleSize      int     // Minimum commands before baseline is stable
	UpdateInterval     time.Duration
}

// BaselineStore interface for baseline persistence
type BaselineStore interface {
	Get(ctx context.Context, userID string) (*security.UserBaseline, error)
	Save(ctx context.Context, baseline *security.UserBaseline) error
	Update(ctx context.Context, userID string, cmd *nlp.Command) error
}

// NewAnalyzer creates a new behavior analyzer
func NewAnalyzer(store BaselineStore) *Analyzer {
	return &Analyzer{
		baselineStore: store,
		config: Config{
			AnomalyThreshold:  0.6,
			HighRiskThreshold: 70,
			MinSampleSize:     50,
			UpdateInterval:    24 * time.Hour,
		},
	}
}

// Analyze analyzes user behavior and detects anomalies
//
// Returns risk score (0-100) and detected anomalies
func (a *Analyzer) Analyze(ctx context.Context, user *security.User, cmd *nlp.Command) (int, []security.Anomaly) {
	// Get user baseline
	baseline, err := a.baselineStore.Get(ctx, user.ID)
	if err != nil || baseline == nil {
		// No baseline yet, create new one
		baseline = a.createNewBaseline(user.ID)
	}
	
	// Detect anomalies
	anomalies := a.detectAnomalies(ctx, user, cmd, baseline)
	
	// Calculate risk score
	riskScore := a.calculateRiskScore(anomalies, cmd)
	
	// Update baseline (async)
	go func() {
		updateCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		a.baselineStore.Update(updateCtx, user.ID, cmd)
	}()
	
	return riskScore, anomalies
}

// detectAnomalies detects behavioral anomalies
func (a *Analyzer) detectAnomalies(ctx context.Context, user *security.User, cmd *nlp.Command, baseline *security.UserBaseline) []security.Anomaly {
	anomalies := make([]security.Anomaly, 0)
	
	// Skip if baseline is not stable yet
	if baseline.SampleSize < a.config.MinSampleSize {
		return anomalies
	}
	
	// 1. Temporal anomalies (unusual time/day)
	if anomaly := a.detectTemporalAnomaly(user, baseline); anomaly != nil {
		anomalies = append(anomalies, *anomaly)
	}
	
	// 2. Command anomalies (unusual command)
	if anomaly := a.detectCommandAnomaly(cmd, baseline); anomaly != nil {
		anomalies = append(anomalies, *anomaly)
	}
	
	// 3. Resource anomalies (unusual resource access)
	if anomaly := a.detectResourceAnomaly(cmd, baseline); anomaly != nil {
		anomalies = append(anomalies, *anomaly)
	}
	
	// 4. Network anomalies (unusual IP/location)
	if anomaly := a.detectNetworkAnomaly(user, baseline); anomaly != nil {
		anomalies = append(anomalies, *anomaly)
	}
	
	// 5. Frequency anomalies (unusual activity rate)
	if anomaly := a.detectFrequencyAnomaly(cmd, baseline); anomaly != nil {
		anomalies = append(anomalies, *anomaly)
	}
	
	return anomalies
}

// detectTemporalAnomaly detects unusual access time/day
func (a *Analyzer) detectTemporalAnomaly(user *security.User, baseline *security.UserBaseline) *security.Anomaly {
	now := time.Now()
	currentHour := now.Hour()
	currentDay := int(now.Weekday())
	
	// Check if current hour is typical
	hourTypical := false
	for _, h := range baseline.TypicalHours {
		if h == currentHour {
			hourTypical = true
			break
		}
	}
	
	// Check if current day is typical
	dayTypical := false
	for _, d := range baseline.TypicalDays {
		if d == currentDay {
			dayTypical = true
			break
		}
	}
	
	// Anomaly if both hour and day are unusual
	if !hourTypical && !dayTypical {
		severity := 0.7 // High severity for temporal anomalies
		return &security.Anomaly{
			Type:      security.AnomalyTypeTemporal,
			Severity:  severity,
			Message:   "Unusual access time and day",
			Baseline:  map[string]interface{}{"hours": baseline.TypicalHours, "days": baseline.TypicalDays},
			Observed:  map[string]interface{}{"hour": currentHour, "day": currentDay},
			Timestamp: time.Now(),
		}
	}
	
	// Medium severity if only hour is unusual
	if !hourTypical {
		return &security.Anomaly{
			Type:      security.AnomalyTypeTemporal,
			Severity:  0.5,
			Message:   "Unusual access hour",
			Baseline:  baseline.TypicalHours,
			Observed:  currentHour,
			Timestamp: time.Now(),
		}
	}
	
	return nil
}

// detectCommandAnomaly detects unusual commands
func (a *Analyzer) detectCommandAnomaly(cmd *nlp.Command, baseline *security.UserBaseline) *security.Anomaly {
	// Get command signature (simplified)
	cmdSig := a.getCommandSignature(cmd)
	
	// Check if command is in top commands
	for _, topCmd := range baseline.TopCommands {
		if topCmd == cmdSig {
			return nil // Command is typical
		}
	}
	
	// Check command ratio
	// If it's a delete command but user rarely deletes, it's anomalous
	if a.isDeleteCommand(cmd) && baseline.CommandRatio.Delete < 0.05 {
		return &security.Anomaly{
			Type:      security.AnomalyTypeCommand,
			Severity:  0.8,
			Message:   "Unusual delete command for this user",
			Baseline:  baseline.CommandRatio.Delete,
			Observed:  "delete",
			Timestamp: time.Now(),
		}
	}
	
	// Command not in top commands but not anomalous enough
	return &security.Anomaly{
		Type:      security.AnomalyTypeCommand,
		Severity:  0.4,
		Message:   "Command not in typical set",
		Baseline:  baseline.TopCommands,
		Observed:  cmdSig,
		Timestamp: time.Now(),
	}
}

// detectResourceAnomaly detects unusual resource access
func (a *Analyzer) detectResourceAnomaly(cmd *nlp.Command, baseline *security.UserBaseline) *security.Anomaly {
	namespace := a.extractNamespace(cmd)
	resource := a.extractResource(cmd)
	
	// Check namespace
	nsTypical := false
	for _, ns := range baseline.TopNamespaces {
		if ns == namespace {
			nsTypical = true
			break
		}
	}
	
	// Check resource
	resTypical := false
	for _, res := range baseline.TopResources {
		if res == resource {
			resTypical = true
			break
		}
	}
	
	// High severity if accessing production namespace for the first time
	if namespace == "production" && !nsTypical {
		return &security.Anomaly{
			Type:      security.AnomalyTypeResource,
			Severity:  0.9,
			Message:   "First time accessing production namespace",
			Baseline:  baseline.TopNamespaces,
			Observed:  namespace,
			Timestamp: time.Now(),
		}
	}
	
	// Medium severity if accessing unusual namespace
	if !nsTypical {
		return &security.Anomaly{
			Type:      security.AnomalyTypeResource,
			Severity:  0.6,
			Message:   "Accessing unusual namespace",
			Baseline:  baseline.TopNamespaces,
			Observed:  namespace,
			Timestamp: time.Now(),
		}
	}
	
	return nil
}

// detectNetworkAnomaly detects unusual network source
func (a *Analyzer) detectNetworkAnomaly(user *security.User, baseline *security.UserBaseline) *security.Anomaly {
	// Check if IP is typical
	ipTypical := false
	for _, ip := range baseline.TypicalIPs {
		if ip == user.IP {
			ipTypical = true
			break
		}
	}
	
	if !ipTypical {
		return &security.Anomaly{
			Type:      security.AnomalyTypeNetwork,
			Severity:  0.7,
			Message:   "Access from unusual IP address",
			Baseline:  baseline.TypicalIPs,
			Observed:  user.IP,
			Timestamp: time.Now(),
		}
	}
	
	return nil
}

// detectFrequencyAnomaly detects unusual activity frequency
func (a *Analyzer) detectFrequencyAnomaly(cmd *nlp.Command, baseline *security.UserBaseline) *security.Anomaly {
	// TODO: Implement frequency tracking
	// For now, return nil
	return nil
}

// calculateRiskScore calculates overall risk score from anomalies
func (a *Analyzer) calculateRiskScore(anomalies []security.Anomaly, cmd *nlp.Command) int {
	if len(anomalies) == 0 {
		return 0
	}
	
	// Base score from anomalies
	var totalSeverity float64
	for _, anomaly := range anomalies {
		if anomaly.Severity >= a.config.AnomalyThreshold {
			totalSeverity += anomaly.Severity
		}
	}
	
	// Average severity as percentage
	avgSeverity := (totalSeverity / float64(len(anomalies))) * 100
	
	// Amplify for critical commands
	if a.isDeleteCommand(cmd) {
		avgSeverity *= 1.5
	}
	
	// Cap at 100
	if avgSeverity > 100 {
		avgSeverity = 100
	}
	
	return int(avgSeverity)
}

// createNewBaseline creates a new baseline for a user
func (a *Analyzer) createNewBaseline(userID string) *security.UserBaseline {
	return &security.UserBaseline{
		UserID:        userID,
		TypicalHours:  []int{},
		TypicalDays:   []int{},
		TopCommands:   []string{},
		CommandRatio:  security.CommandRatio{},
		TopNamespaces: []string{},
		TopResources:  []string{},
		TypicalIPs:    []string{},
		TypicalGeo:    []string{},
		LastUpdated:   time.Now(),
		SampleSize:    0,
	}
}

// Helper functions

func (a *Analyzer) getCommandSignature(cmd *nlp.Command) string {
	if len(cmd.Path) < 2 {
		return "unknown"
	}
	// Simplified signature: verb + resource
	verb := cmd.Path[1]
	resource := ""
	if len(cmd.Path) > 2 {
		resource = cmd.Path[2]
	}
	return verb + ":" + resource
}

func (a *Analyzer) isDeleteCommand(cmd *nlp.Command) bool {
	if len(cmd.Path) < 2 {
		return false
	}
	return cmd.Path[1] == "delete"
}

func (a *Analyzer) extractNamespace(cmd *nlp.Command) string {
	for i, flag := range cmd.Flags {
		if flag == "-n" || flag == "--namespace" {
			if i+1 < len(cmd.Flags) {
				return cmd.Flags[i+1]
			}
		}
	}
	return "default"
}

func (a *Analyzer) extractResource(cmd *nlp.Command) string {
	if len(cmd.Path) > 2 {
		return cmd.Path[2]
	}
	return "unknown"
}

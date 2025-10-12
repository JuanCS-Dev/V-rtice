// Package intent implements Layer 4 (Intent Validation) of Guardian Zero Trust Security.
//
// "Are you sure?" - Validating user intent before executing dangerous operations.
//
// Provides:
// - Risk analysis and scoring
// - Human-in-the-Loop (HITL) confirmation
// - Command reversibility checking
// - Intent clarification
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)  
// Date: 2025-10-12
package intent

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"
	"time"
)

// RiskLevel represents the risk level of a command.
type RiskLevel int

const (
	RiskLevelSafe     RiskLevel = 0 // get, list, describe, watch
	RiskLevelLow      RiskLevel = 1 // logs, exec, port-forward
	RiskLevelMedium   RiskLevel = 2 // scale, restart, update
	RiskLevelHigh     RiskLevel = 3 // delete, create secret
	RiskLevelCritical RiskLevel = 4 // delete namespace, flush db, drop table
)

// String returns human-readable risk level.
func (r RiskLevel) String() string {
	switch r {
	case RiskLevelSafe:
		return "SAFE"
	case RiskLevelLow:
		return "LOW"
	case RiskLevelMedium:
		return "MEDIUM"
	case RiskLevelHigh:
		return "HIGH"
	case RiskLevelCritical:
		return "CRITICAL"
	default:
		return "UNKNOWN"
	}
}

// IntentValidator validates user intent before command execution.
type IntentValidator struct {
	riskAnalyzer *RiskAnalyzer
	confirmations map[string]*ConfirmationToken // token -> confirmation
}

// ValidationResult contains the outcome of intent validation.
type ValidationResult struct {
	// Risk assessment
	RiskLevel RiskLevel
	RiskScore float64 // 0.0 (safe) - 1.0 (critical)
	
	// Requirements
	RequiresHITL      bool // Human-in-the-Loop confirmation
	RequiresSignature bool // Cryptographic signature
	
	// Analysis
	TranslatedCommand string   // Human-readable command
	Warnings          []string // Warnings about the command
	Explanation       string   // Why this risk level
	
	// Reversibility
	IsReversible bool
	UndoCommand  string // Command to undo if reversible
	
	// Confirmation token if HITL required
	ConfirmationToken *ConfirmationToken
}

// ConfirmationToken represents a HITL confirmation request.
type ConfirmationToken struct {
	Token       string
	Command     string
	RiskLevel   RiskLevel
	ExpiresAt   time.Time
	Confirmed   bool
	ConfirmedAt time.Time
	UserID      string
}

// CommandIntent represents the parsed intent of a command.
type CommandIntent struct {
	Action    string // delete, create, update, etc.
	Resource  string // pod, deployment, secret, etc.
	Target    string // resource name or "all"
	Namespace string
	Flags     map[string]string
	HasWildcard bool
}

// NewIntentValidator creates a new intent validator.
func NewIntentValidator() *IntentValidator {
	return &IntentValidator{
		riskAnalyzer: NewRiskAnalyzer(),
		confirmations: make(map[string]*ConfirmationToken),
	}
}

// ValidateIntent validates the intent of a command.
func (iv *IntentValidator) ValidateIntent(ctx context.Context, intent *CommandIntent) (*ValidationResult, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if intent == nil {
		return nil, errors.New("command intent cannot be nil")
	}
	
	// Analyze risk
	riskLevel := iv.riskAnalyzer.CalculateRisk(intent)
	riskScore := iv.riskAnalyzer.RiskToScore(riskLevel)
	
	// Translate to human-readable
	translated := iv.translateCommand(intent)
	
	// Check reversibility
	isReversible, undoCmd := iv.checkReversibility(intent)
	
	// Determine requirements
	requiresHITL := riskLevel >= RiskLevelMedium
	requiresSignature := riskLevel >= RiskLevelHigh
	
	// Generate warnings
	warnings := iv.generateWarnings(intent, riskLevel)
	
	// Build result
	result := &ValidationResult{
		RiskLevel:         riskLevel,
		RiskScore:         riskScore,
		RequiresHITL:      requiresHITL,
		RequiresSignature: requiresSignature,
		TranslatedCommand: translated,
		Warnings:          warnings,
		Explanation:       iv.explainRisk(intent, riskLevel),
		IsReversible:      isReversible,
		UndoCommand:       undoCmd,
	}
	
	// Create confirmation token if HITL required
	if requiresHITL {
		token := iv.createConfirmationToken(intent, riskLevel)
		result.ConfirmationToken = token
	}
	
	return result, nil
}

// ConfirmIntent confirms a pending intent with confirmation token.
func (iv *IntentValidator) ConfirmIntent(ctx context.Context, tokenStr string, userID string) error {
	token, exists := iv.confirmations[tokenStr]
	if !exists {
		return errors.New("confirmation token not found")
	}
	
	if time.Now().After(token.ExpiresAt) {
		delete(iv.confirmations, tokenStr)
		return errors.New("confirmation token expired")
	}
	
	if token.UserID != userID {
		return errors.New("token user mismatch")
	}
	
	token.Confirmed = true
	token.ConfirmedAt = time.Now()
	
	return nil
}

// IsConfirmed checks if a token has been confirmed.
func (iv *IntentValidator) IsConfirmed(tokenStr string) bool {
	token, exists := iv.confirmations[tokenStr]
	if !exists {
		return false
	}
	return token.Confirmed && time.Now().Before(token.ExpiresAt)
}

// translateCommand converts intent to human-readable format.
func (iv *IntentValidator) translateCommand(intent *CommandIntent) string {
	parts := []string{intent.Action, intent.Resource}
	
	if intent.Target != "" {
		parts = append(parts, intent.Target)
	}
	
	if intent.Namespace != "" {
		parts = append(parts, "in namespace", intent.Namespace)
	}
	
	return strings.Join(parts, " ")
}

// checkReversibility determines if a command can be undone.
func (iv *IntentValidator) checkReversibility(intent *CommandIntent) (bool, string) {
	action := strings.ToLower(intent.Action)
	
	switch action {
	case "delete":
		// Deletes are generally NOT reversible
		return false, ""
		
	case "scale":
		// Scaling is reversible (scale back)
		return true, fmt.Sprintf("scale %s back to original replicas", intent.Target)
		
	case "restart":
		// Restarts are reversible (pods come back)
		return true, "pods will restart automatically"
		
	case "update", "patch":
		// Updates are reversible if you have the old spec
		return true, "rollback to previous version"
		
	default:
		// Read operations are always safe/reversible
		if isReadAction(action) {
			return true, "read-only operation"
		}
		return false, ""
	}
}

// generateWarnings generates warnings based on intent and risk.
func (iv *IntentValidator) generateWarnings(intent *CommandIntent, risk RiskLevel) []string {
	warnings := []string{}
	
	// Wildcard warning
	if intent.HasWildcard || intent.Target == "all" {
		warnings = append(warnings, "⚠️  This command affects MULTIPLE resources")
	}
	
	// Namespace warning
	if intent.Namespace == "kube-system" || intent.Namespace == "kube-public" {
		warnings = append(warnings, "⚠️  Operating in SYSTEM namespace")
	}
	
	// Delete warning
	if strings.ToLower(intent.Action) == "delete" {
		warnings = append(warnings, "⚠️  DELETE operation is IRREVERSIBLE")
	}
	
	// Secret warning
	if intent.Resource == "secret" {
		warnings = append(warnings, "⚠️  Accessing SENSITIVE data (secrets)")
	}
	
	// Critical risk warning
	if risk == RiskLevelCritical {
		warnings = append(warnings, "🚨 CRITICAL: This operation can cause PRODUCTION OUTAGE")
	}
	
	return warnings
}

// explainRisk provides explanation for the risk level.
func (iv *IntentValidator) explainRisk(intent *CommandIntent, risk RiskLevel) string {
	switch risk {
	case RiskLevelSafe:
		return "Safe read-only operation with no side effects"
		
	case RiskLevelLow:
		return "Low risk operation with minimal impact"
		
	case RiskLevelMedium:
		return fmt.Sprintf("Medium risk: %s operation on %s requires confirmation", intent.Action, intent.Resource)
		
	case RiskLevelHigh:
		return fmt.Sprintf("High risk: %s operation on %s - IRREVERSIBLE", intent.Action, intent.Resource)
		
	case RiskLevelCritical:
		return fmt.Sprintf("CRITICAL: %s on %s - POTENTIAL PRODUCTION OUTAGE", intent.Action, intent.Target)
		
	default:
		return "Unknown risk level"
	}
}

// createConfirmationToken creates a new confirmation token.
func (iv *IntentValidator) createConfirmationToken(intent *CommandIntent, risk RiskLevel) *ConfirmationToken {
	token := &ConfirmationToken{
		Token:     generateToken(),
		Command:   iv.translateCommand(intent),
		RiskLevel: risk,
		ExpiresAt: time.Now().Add(5 * time.Minute), // 5 minute expiry
		Confirmed: false,
	}
	
	iv.confirmations[token.Token] = token
	return token
}

// RiskAnalyzer analyzes command risk.
type RiskAnalyzer struct{}

// NewRiskAnalyzer creates a new risk analyzer.
func NewRiskAnalyzer() *RiskAnalyzer {
	return &RiskAnalyzer{}
}

// CalculateRisk calculates the risk level of a command intent.
func (ra *RiskAnalyzer) CalculateRisk(intent *CommandIntent) RiskLevel {
	risk := RiskLevelSafe
	action := strings.ToLower(intent.Action)
	
	// Action risk
	switch action {
	case "delete", "drop", "flush", "truncate":
		risk = maxRisk(risk, RiskLevelHigh)
	case "create", "update", "patch", "apply":
		risk = maxRisk(risk, RiskLevelMedium)
	case "restart", "scale":
		risk = maxRisk(risk, RiskLevelMedium)
	case "exec", "port-forward", "logs":
		risk = maxRisk(risk, RiskLevelLow)
	default:
		if isReadAction(action) {
			risk = RiskLevelSafe
		}
	}
	
	// Resource risk
	if intent.Resource == "secret" || intent.Resource == "namespace" {
		risk = maxRisk(risk, RiskLevelMedium)
	}
	
	// Scope risk (wildcards or "all")
	if intent.HasWildcard || intent.Target == "all" {
		// Escalate by one level
		if risk < RiskLevelCritical {
			risk = risk + 1
		}
	}
	
	// System namespace risk
	if intent.Namespace == "kube-system" || intent.Namespace == "kube-public" {
		risk = maxRisk(risk, RiskLevelHigh)
	}
	
	// Delete + namespace = CRITICAL
	if action == "delete" && intent.Resource == "namespace" {
		risk = RiskLevelCritical
	}
	
	return risk
}

// RiskToScore converts risk level to 0.0-1.0 score.
func (ra *RiskAnalyzer) RiskToScore(risk RiskLevel) float64 {
	return float64(risk) / 4.0 // 0.0, 0.25, 0.5, 0.75, 1.0
}

// Helper functions

func isReadAction(action string) bool {
	readActions := []string{"get", "list", "describe", "watch", "show", "view"}
	action = strings.ToLower(action)
	for _, read := range readActions {
		if action == read {
			return true
		}
	}
	return false
}

func maxRisk(a, b RiskLevel) RiskLevel {
	if a > b {
		return a
	}
	return b
}

func generateToken() string {
	bytes := make([]byte, 16)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)
}

// GetConfirmationToken retrieves a confirmation token.
func (iv *IntentValidator) GetConfirmationToken(tokenStr string) (*ConfirmationToken, bool) {
	token, exists := iv.confirmations[tokenStr]
	return token, exists
}

// CleanupExpiredTokens removes expired confirmation tokens.
func (iv *IntentValidator) CleanupExpiredTokens() int {
	now := time.Now()
	removed := 0
	
	for token, conf := range iv.confirmations {
		if now.After(conf.ExpiresAt) {
			delete(iv.confirmations, token)
			removed++
		}
	}
	
	return removed
}

// GetPendingConfirmations returns all pending (unconfirmed) tokens.
func (iv *IntentValidator) GetPendingConfirmations() []*ConfirmationToken {
	pending := []*ConfirmationToken{}
	now := time.Now()
	
	for _, token := range iv.confirmations {
		if !token.Confirmed && now.Before(token.ExpiresAt) {
			pending = append(pending, token)
		}
	}
	
	return pending
}

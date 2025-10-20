// Package intent_validation - Layer 4: Intent Validation
//
// Confirms destructive actions with user
package intent_validation

import (
	"context"
	"fmt"
)

// IntentValidationLayer validates user intent for risky actions
type IntentValidationLayer interface {
	// ValidateIntent checks if confirmation is needed
	ValidateIntent(ctx context.Context, action string, confidence float64, risk string) (*IntentDecision, error)
}

// IntentDecision represents validation result
type IntentDecision struct {
	RequiresConfirmation bool
	Reason               string
	SuggestedPrompt      string
}

// Risk levels
const (
	RiskSafe        = "safe"        // Read-only
	RiskModerate    = "moderate"    // Reversible changes
	RiskDestructive = "destructive" // Data loss possible
	RiskCritical    = "critical"    // System-wide impact
)

type intentValidator struct {
	confirmationThreshold float64 // Confidence below this = confirm
}

// NewIntentValidator creates intent validation layer
func NewIntentValidator(threshold float64) IntentValidationLayer {
	return &intentValidator{
		confirmationThreshold: threshold,
	}
}

// ValidateIntent implements IntentValidationLayer
func (v *intentValidator) ValidateIntent(ctx context.Context, action string, confidence float64, risk string) (*IntentDecision, error) {
	decision := &IntentDecision{
		RequiresConfirmation: false,
	}

	// Critical actions ALWAYS require confirmation
	if risk == RiskCritical {
		decision.RequiresConfirmation = true
		decision.Reason = "Critical action - confirmation required"
		decision.SuggestedPrompt = fmt.Sprintf("⚠️  CRITICAL: Confirm '%s'? [yes/no]", action)
		return decision, nil
	}

	// Destructive actions require confirmation
	if risk == RiskDestructive {
		decision.RequiresConfirmation = true
		decision.Reason = "Destructive action - confirmation required"
		decision.SuggestedPrompt = fmt.Sprintf("⚠️  Confirm destructive action '%s'? [yes/no]", action)
		return decision, nil
	}

	// Low confidence = ask for confirmation
	if confidence < v.confirmationThreshold {
		decision.RequiresConfirmation = true
		decision.Reason = fmt.Sprintf("Low confidence (%.1f%%) - confirmation needed", confidence*100)
		decision.SuggestedPrompt = fmt.Sprintf("❓ Did you mean '%s'? [yes/no]", action)
		return decision, nil
	}

	decision.Reason = "High confidence - no confirmation needed"
	return decision, nil
}


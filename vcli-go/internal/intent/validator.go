// Package intent implements intent validation with reverse translation (Layer 4)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 4 of the "Guardian of Intent" v2.0:
// "VALIDAÇÃO DA INTENÇÃO - Você tem certeza?"
//
// Provides:
// - Reverse translation (cmd → human readable)
// - Impact analysis
// - HITL (Human-In-The-Loop) confirmation
// - Cryptographic signing for critical commands
package intent

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/security"
)

// Validator handles intent validation and confirmation
type Validator struct {
	translator  *ReverseTranslator
	analyzer    *ImpactAnalyzer
	confirmer   UserConfirmer
	signer      Signer
}

// NewValidator creates a new intent validator
func NewValidator(confirmer UserConfirmer, signer Signer) *Validator {
	return &Validator{
		translator: NewReverseTranslator(),
		analyzer:   NewImpactAnalyzer(),
		confirmer:  confirmer,
		signer:     signer,
	}
}

// UserConfirmer interface for user confirmation
type UserConfirmer interface {
	Confirm(ctx context.Context, prompt *ConfirmationPrompt) (bool, error)
	RequestSignature(ctx context.Context, cmd *nlp.Command) (string, error)
}

// Signer interface for cryptographic signing
type Signer interface {
	Sign(data []byte) (string, error)
	Verify(data []byte, signature string) (bool, error)
}

// Validate validates user intent for a parsed command
//
// This is the main HITL checkpoint. For critical commands:
// 1. Reverse translates command to human-readable form
// 2. Analyzes impact (how many resources affected)
// 3. Requests user confirmation
// 4. For CRITICAL commands, also requests signature
func (v *Validator) Validate(ctx context.Context, secCtx *security.SecurityContext, cmd *nlp.Command, intent *nlp.Intent) error {
	// Skip validation for low-risk commands
	if intent.RiskLevel == nlp.RiskLevelLOW {
		return nil
	}
	
	// Reverse translate command
	humanReadable := v.translator.Translate(cmd)
	
	// Analyze impact
	impact, err := v.analyzer.Analyze(ctx, cmd)
	if err != nil {
		// If we can't analyze impact, proceed with caution
		impact = &Impact{
			AffectedResources: []string{"unknown"},
			Severity:          "high",
			Reversible:        false,
		}
	}
	
	// Build confirmation prompt
	prompt := &ConfirmationPrompt{
		OriginalInput: intent.OriginalInput,
		Translation:   humanReadable,
		Impact:        impact,
		RiskLevel:     string(intent.RiskLevel),
		RiskScore:     secCtx.RiskScore,
		Anomalies:     secCtx.Anomalies,
	}
	
	// Request user confirmation
	confirmed, err := v.confirmer.Confirm(ctx, prompt)
	if err != nil {
		return &security.SecurityError{
			Layer:     "intent",
			Type:      security.ErrorTypeIntentNotConf,
			Message:   "Failed to get user confirmation",
			Details:   map[string]interface{}{"error": err.Error()},
			Timestamp: time.Now(),
			UserID:    secCtx.User.ID,
			SessionID: secCtx.Session.ID,
		}
	}
	
	if !confirmed {
		return &security.IntentNotConfirmedError{
			Command: humanReadable,
			Reason:  "User declined confirmation",
		}
	}
	
	// For CRITICAL commands, also require signature
	if intent.RiskLevel == nlp.RiskLevelCRITICAL {
		signature, err := v.confirmer.RequestSignature(ctx, cmd)
		if err != nil {
			return &security.SecurityError{
				Layer:     "intent",
				Type:      security.ErrorTypeIntentNotConf,
				Message:   "Failed to get user signature",
				Details:   map[string]interface{}{"error": err.Error()},
				Timestamp: time.Now(),
				UserID:    secCtx.User.ID,
				SessionID: secCtx.Session.ID,
			}
		}
		
		// Verify signature
		cmdBytes := []byte(humanReadable)
		valid, err := v.signer.Verify(cmdBytes, signature)
		if err != nil || !valid {
			return &security.SecurityError{
				Layer:     "intent",
				Type:      security.ErrorTypeIntentNotConf,
				Message:   "Invalid signature",
				Timestamp: time.Now(),
				UserID:    secCtx.User.ID,
				SessionID: secCtx.Session.ID,
			}
		}
	}
	
	return nil
}

// ReverseTranslator translates commands back to human-readable form
type ReverseTranslator struct {
	// Verb mappings
	verbMap map[string]string
}

// NewReverseTranslator creates a new reverse translator
func NewReverseTranslator() *ReverseTranslator {
	return &ReverseTranslator{
		verbMap: map[string]string{
			"get":      "listar",
			"list":     "listar",
			"describe": "descrever",
			"delete":   "deletar",
			"create":   "criar",
			"apply":    "aplicar",
			"scale":    "escalar",
			"logs":     "ver logs de",
			"exec":     "executar comando em",
		},
	}
}

// Translate translates a command to human-readable Portuguese
func (rt *ReverseTranslator) Translate(cmd *nlp.Command) string {
	if len(cmd.Path) < 2 {
		return "comando desconhecido"
	}
	
	// Extract verb and resource
	verb := cmd.Path[1]
	verbPT := rt.verbMap[verb]
	if verbPT == "" {
		verbPT = verb
	}
	
	resource := ""
	if len(cmd.Path) > 2 {
		resource = cmd.Path[2]
	}
	
	// Start building translation
	parts := []string{"Você está prestes a executar:"}
	
	// Add action
	parts = append(parts, fmt.Sprintf("\n  Ação: %s %s", verbPT, resource))
	
	// Add namespace
	namespace := rt.extractNamespace(cmd)
	if namespace != "default" {
		parts = append(parts, fmt.Sprintf("\n  Namespace: %s", namespace))
	}
	
	// Add labels/selectors
	if labels := rt.extractLabels(cmd); labels != "" {
		parts = append(parts, fmt.Sprintf("\n  Filtros: %s", labels))
	}
	
	// Add full command
	parts = append(parts, fmt.Sprintf("\n\nComando: %s", rt.buildShellCommand(cmd)))
	
	return strings.Join(parts, "")
}

// extractNamespace extracts namespace from command
func (rt *ReverseTranslator) extractNamespace(cmd *nlp.Command) string {
	if ns, exists := cmd.Flags["-n"]; exists {
		return ns
	}
	if ns, exists := cmd.Flags["--namespace"]; exists {
		return ns
	}
	return "default"
}

// extractLabels extracts label selectors
func (rt *ReverseTranslator) extractLabels(cmd *nlp.Command) string {
	if labels, exists := cmd.Flags["-l"]; exists {
		return labels
	}
	if labels, exists := cmd.Flags["--selector"]; exists {
		return labels
	}
	return ""
}

// buildShellCommand builds the actual shell command
func (rt *ReverseTranslator) buildShellCommand(cmd *nlp.Command) string {
	parts := make([]string, 0, len(cmd.Path)+len(cmd.Flags)*2)
	parts = append(parts, cmd.Path...)
	
	// Add flags
	for key, value := range cmd.Flags {
		parts = append(parts, key)
		if value != "" {
			parts = append(parts, value)
		}
	}
	
	return strings.Join(parts, " ")
}

// ImpactAnalyzer analyzes the impact of a command
type ImpactAnalyzer struct {
	// K8s client would go here in real implementation
}

// NewImpactAnalyzer creates a new impact analyzer
func NewImpactAnalyzer() *ImpactAnalyzer {
	return &ImpactAnalyzer{}
}

// Analyze analyzes the impact of a command
//
// In a real implementation, this would:
// - Query K8s API to see how many resources match
// - Check dependencies (services depending on this deployment, etc.)
// - Estimate downtime/disruption
func (ia *ImpactAnalyzer) Analyze(ctx context.Context, cmd *nlp.Command) (*Impact, error) {
	impact := &Impact{
		AffectedResources: []string{},
		Severity:          "medium",
		Reversible:        true,
		EstimatedTime:     "immediate",
	}
	
	// Determine severity based on verb
	if len(cmd.Path) < 2 {
		return impact, nil
	}
	
	verb := cmd.Path[1]
	namespace := ""
	if ns, exists := cmd.Flags["-n"]; exists {
		namespace = ns
	} else if ns, exists := cmd.Flags["--namespace"]; exists {
		namespace = ns
	}
	
	switch verb {
	case "delete":
		impact.Severity = "high"
		impact.Reversible = false
		if namespace == "production" || namespace == "prod" {
			impact.Severity = "critical"
		}
		
	case "scale":
		impact.Severity = "medium"
		impact.Reversible = true
		
	case "apply", "create":
		impact.Severity = "medium"
		impact.Reversible = true
		
	case "get", "list", "describe":
		impact.Severity = "low"
		impact.Reversible = true
	}
	
	// Current: Heuristic estimation (sufficient for intent validation)
	// Future: Query K8s API to get actual resource count when integrated
	impact.AffectedResources = []string{
		fmt.Sprintf("Estimated: resources in namespace '%s'", namespace),
	}
	
	return impact, nil
}

// Impact represents the impact of a command
type Impact struct {
	AffectedResources []string
	Severity          string // low, medium, high, critical
	Reversible        bool
	EstimatedTime     string
	Dependencies      []string // Dependent resources
	Description       string   // Human-readable description
	RiskScore         float64  // 0.0 - 1.0
}

// ConfirmationPrompt contains information for user confirmation
type ConfirmationPrompt struct {
	OriginalInput string
	Translation   string
	Impact        *Impact
	RiskLevel     string
	RiskScore     int
	Anomalies     []security.Anomaly
}

// FormatPrompt formats the confirmation prompt for display
func (cp *ConfirmationPrompt) FormatPrompt() string {
	var sb strings.Builder
	
	sb.WriteString("╔═══════════════════════════════════════════════════════╗\n")
	sb.WriteString("║          CONFIRMAÇÃO DE INTENÇÃO REQUERIDA           ║\n")
	sb.WriteString("╚═══════════════════════════════════════════════════════╝\n\n")
	
	sb.WriteString(cp.Translation)
	sb.WriteString("\n\n")
	
	sb.WriteString("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	sb.WriteString("ANÁLISE DE IMPACTO:\n")
	sb.WriteString(fmt.Sprintf("  Severidade: %s\n", strings.ToUpper(cp.Impact.Severity)))
	sb.WriteString(fmt.Sprintf("  Reversível: %v\n", cp.Impact.Reversible))
	sb.WriteString(fmt.Sprintf("  Tempo estimado: %s\n", cp.Impact.EstimatedTime))
	
	if len(cp.Impact.AffectedResources) > 0 {
		sb.WriteString(fmt.Sprintf("  Recursos afetados: %d\n", len(cp.Impact.AffectedResources)))
		for i, res := range cp.Impact.AffectedResources {
			if i < 5 { // Show max 5
				sb.WriteString(fmt.Sprintf("    - %s\n", res))
			}
		}
		if len(cp.Impact.AffectedResources) > 5 {
			sb.WriteString(fmt.Sprintf("    ... e mais %d recursos\n", len(cp.Impact.AffectedResources)-5))
		}
	}
	
	if cp.RiskScore > 0 {
		sb.WriteString(fmt.Sprintf("\n  ⚠️  Score de Risco: %d/100\n", cp.RiskScore))
	}
	
	if len(cp.Anomalies) > 0 {
		sb.WriteString(fmt.Sprintf("\n  🚨 Anomalias detectadas: %d\n", len(cp.Anomalies)))
		for _, anomaly := range cp.Anomalies {
			if anomaly.Severity >= 0.6 {
				sb.WriteString(fmt.Sprintf("    - %s (severidade: %.1f)\n", anomaly.Message, anomaly.Severity))
			}
		}
	}
	
	sb.WriteString("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
	
	if cp.RiskLevel == "CRITICAL" {
		sb.WriteString("🔐 Este comando requer ASSINATURA DIGITAL\n\n")
	}
	
	sb.WriteString("[C] Confirmar  [R] Reformular  [X] Cancelar\n")
	
	return sb.String()
}

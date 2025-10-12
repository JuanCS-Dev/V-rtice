# Guardian of Intent - Day 1 Implementation Plan

**Lead Architect:** Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author:** Claude (MAXIMUS AI Assistant)  
**Data:** 2025-10-12  
**Status:** 🔄 IN PROGRESS

---

## 🎯 OBJETIVO DO DIA

Implementar **Camada 5: Validação da Intenção** - o "Guardião da Intenção" que pergunta ao usuário "Você tem certeza?" antes de executar ações destrutivas.

### Deliverables
```
internal/intent/
├── validator.go              ← Core intent validator
├── validator_test.go         ← Unit tests
├── reverse_translator.go     ← Command → Natural Language
├── reverse_translator_test.go
├── dry_runner.go             ← Dry-run executor
├── dry_runner_test.go
├── signature_verifier.go     ← Cryptographic signatures
├── signature_verifier_test.go
└── README.md                 ← Documentation
```

### Success Criteria
- ✅ Validator implementado com todas as funções
- ✅ Reverse translation funciona para todos os verbos
- ✅ Dry-run simula execução sem efeitos colaterais
- ✅ Signatures funcionam para ações CRITICAL
- ✅ Testes cobrem edge cases e error paths
- ✅ Coverage ≥ 90%

---

## 📋 EXECUTION PLAN

### Step 1: Setup Structure (15min)
**Objetivo:** Criar diretório e verificar dependências

```bash
# Create directory
mkdir -p vcli-go/internal/intent

# Check existing dependencies
cd vcli-go
go mod tidy
```

**Checklist:**
- [ ] Diretório `internal/intent/` criado
- [ ] Dependencies verificadas
- [ ] Go modules atualizados

---

### Step 2: Core Validator (2h)
**Arquivo:** `internal/intent/validator.go`

#### 2.1: Interface e Estrutura (30min)

```go
// Package intent implements intent validation (Layer 5)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 5 of the "Guardian of Intent" v2.0:
// "VALIDAÇÃO DA INTENÇÃO - Você tem certeza?"
//
// Provides:
// - Reverse translation: Command → Natural Language
// - HITL (Human-in-the-Loop) confirmations
// - Dry-run execution preview
// - Cryptographic signatures for CRITICAL actions
package intent

import (
	"context"
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/security"
)

// Validator validates user intent before execution
//
// This is the guardian that asks "Are you sure?" before
// destructive operations. It implements multiple confirmation
// strategies based on risk level:
// - LOW: Auto-approve
// - MEDIUM: Simple confirmation
// - HIGH: Confirmation + impact preview
// - CRITICAL: Confirmation + cryptographic signature
type Validator struct {
	reverseTranslator *ReverseTranslator
	dryRunner         *DryRunner
	signatureVerifier *SignatureVerifier
	confirmTimeout    time.Duration
	
	// Hooks for testing
	confirmFunc func(context.Context, string, *Impact) (bool, error)
}

// NewValidator creates a new intent validator
func NewValidator() *Validator {
	return &Validator{
		reverseTranslator: NewReverseTranslator(),
		dryRunner:         NewDryRunner(),
		signatureVerifier: NewSignatureVerifier(),
		confirmTimeout:    10 * time.Second,
	}
}

// ValidatorOption is a functional option for Validator
type ValidatorOption func(*Validator)

// WithConfirmTimeout sets custom confirmation timeout
func WithConfirmTimeout(timeout time.Duration) ValidatorOption {
	return func(v *Validator) {
		v.confirmTimeout = timeout
	}
}

// WithConfirmFunc sets custom confirmation function (for testing)
func WithConfirmFunc(fn func(context.Context, string, *Impact) (bool, error)) ValidatorOption {
	return func(v *Validator) {
		v.confirmFunc = fn
	}
}

// NewValidatorWithOptions creates validator with options
func NewValidatorWithOptions(opts ...ValidatorOption) *Validator {
	v := NewValidator()
	for _, opt := range opts {
		opt(v)
	}
	return v
}
```

**Checklist 2.1:**
- [ ] Package documentation
- [ ] Validator struct defined
- [ ] Constructor functions
- [ ] Functional options pattern

#### 2.2: Main Validate Function (45min)

```go
// Validate validates intent before execution
//
// This is the entry point for Camada 5. Flow:
// 1. Check if confirmation required (based on risk level)
// 2. Generate human-readable explanation
// 3. Estimate impact of command
// 4. For CRITICAL: request cryptographic signature
// 5. Request user confirmation
// 6. Return approval or denial
func (v *Validator) Validate(ctx context.Context, result *nlp.ParseResult, user *security.User) error {
	startTime := time.Now()
	
	// Check if confirmation is required based on risk level
	if !v.RequiresConfirmation(result.Intent) {
		// Low risk, auto-approve
		return nil
	}
	
	// Generate human-readable explanation
	explanation := v.ReverseTranslate(result.Command)
	
	// Estimate impact
	impact, err := v.EstimateImpact(ctx, result.Command)
	if err != nil {
		// If we can't estimate impact, be conservative
		impact = &Impact{
			RiskScore:  1.0,
			Reversible: false,
		}
	}
	
	// For CRITICAL risk, require cryptographic signature
	if result.Intent.RiskLevel == nlp.RiskLevelCRITICAL {
		signature, err := v.RequestSignature(ctx, explanation, user)
		if err != nil {
			return &security.SecurityError{
				Layer:     "intent",
				Type:      security.ErrorTypeAuth,
				Message:   "Cryptographic signature required but not provided",
				Details:   map[string]interface{}{"error": err.Error()},
				Timestamp: startTime,
				UserID:    user.ID,
				SessionID: user.SessionID,
			}
		}
		
		// Store signature in parse result for audit
		result.Signature = signature
	}
	
	// Request confirmation from user
	confirmed, err := v.RequestConfirmation(ctx, explanation, impact)
	if err != nil {
		return &security.SecurityError{
			Layer:     "intent",
			Type:      security.ErrorTypeInternal,
			Message:   "Failed to request confirmation",
			Details:   map[string]interface{}{"error": err.Error()},
			Timestamp: startTime,
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	if !confirmed {
		return &security.SecurityError{
			Layer:     "intent",
			Type:      security.ErrorTypeUserDenied,
			Message:   "User cancelled operation",
			Timestamp: startTime,
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	return nil
}

// RequiresConfirmation checks if intent needs user confirmation
//
// Confirmation policy:
// - LOW: No confirmation (read-only operations)
// - MEDIUM: Simple confirmation
// - HIGH: Confirmation with impact preview
// - CRITICAL: Confirmation + cryptographic signature
func (v *Validator) RequiresConfirmation(intent *nlp.Intent) bool {
	return intent.RiskLevel >= nlp.RiskLevelMEDIUM
}

// ReverseTranslate converts command back to natural language
func (v *Validator) ReverseTranslate(cmd *nlp.Command) string {
	return v.reverseTranslator.Translate(cmd)
}

// EstimateImpact calculates expected impact of command
func (v *Validator) EstimateImpact(ctx context.Context, cmd *nlp.Command) (*Impact, error) {
	return v.dryRunner.Estimate(ctx, cmd)
}

// RequestConfirmation prompts user for confirmation
func (v *Validator) RequestConfirmation(ctx context.Context, explanation string, impact *Impact) (bool, error) {
	// Use custom confirm function if set (for testing)
	if v.confirmFunc != nil {
		return v.confirmFunc(ctx, explanation, impact)
	}
	
	// TODO: Implement interactive prompt with bubbletea
	// For now, auto-approve in development
	return true, nil
}

// RequestSignature requests cryptographic signature for CRITICAL operations
func (v *Validator) RequestSignature(ctx context.Context, message string, user *security.User) ([]byte, error) {
	return v.signatureVerifier.Sign(ctx, message, user)
}

// DryRun executes command in simulation mode
func (v *Validator) DryRun(ctx context.Context, cmd *nlp.Command) (*DryRunResult, error) {
	return v.dryRunner.Execute(ctx, cmd)
}
```

**Checklist 2.2:**
- [ ] Main Validate function
- [ ] RequiresConfirmation logic
- [ ] Integration with sub-components
- [ ] Error handling

#### 2.3: Supporting Types (15min)

```go
// Impact represents estimated impact of a command
//
// This structure provides user with clear understanding
// of what will happen if they confirm the action.
type Impact struct {
	// How many resources will be affected
	ResourcesAffected int
	
	// Which namespaces are involved
	Namespaces []string
	
	// Can this action be undone automatically?
	Reversible bool
	
	// Estimated time to complete
	EstimatedDuration time.Duration
	
	// Risk score (0.0 - 1.0)
	RiskScore float64
	
	// Human-readable description
	Description string
}

// DryRunResult represents result of dry-run execution
//
// Dry-run simulates command execution without actually
// making changes. This allows user to preview what
// would happen.
type DryRunResult struct {
	// Did dry-run succeed?
	Success bool
	
	// Output from dry-run
	Output string
	
	// Any errors that would occur
	Errors []string
	
	// List of resources that would be changed
	ResourcesChanged []string
	
	// Changes that would be made
	Changes []Change
}

// Change represents a specific change that would be made
type Change struct {
	Resource string
	Field    string
	OldValue string
	NewValue string
}
```

**Checklist 2.3:**
- [ ] Impact struct
- [ ] DryRunResult struct
- [ ] Change struct
- [ ] Documentation

---

### Step 3: Reverse Translator (2h)
**Arquivo:** `internal/intent/reverse_translator.go`

#### 3.1: Core Translation Engine (1h)

```go
// Package intent - Reverse Translator
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Converts structured commands back to human-readable
// natural language. This is crucial for user confirmation.
package intent

import (
	"fmt"
	"strings"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// ReverseTranslator converts commands back to natural language
//
// Purpose: When user says "delete crashed pods", we parse it to
// "kubectl delete pod X Y Z". Before executing, we translate back:
// "Você quer: deletar 3 pods (X, Y, Z) no namespace kafka. Confirma?"
//
// This reverse translation serves two purposes:
// 1. User clarity: Show exactly what will happen
// 2. Security: User can catch parser mistakes before damage
type ReverseTranslator struct {
	verbTemplates   map[string]VerbTemplate
	verbEmojis      map[string]string
	portugueseVerbs map[string]string
}

// VerbTemplate defines how to explain a verb in natural language
type VerbTemplate struct {
	// Template string with placeholders: %s for command, %d for count, etc.
	Template string
	
	// Portuguese translation of verb
	Portuguese string
	
	// Icon/emoji for visual identification
	Icon string
	
	// Should we show resource count?
	ShowCount bool
	
	// Should we show namespace?
	ShowNamespace bool
	
	// Should we show flags?
	ShowFlags bool
}

// NewReverseTranslator creates a new reverse translator
func NewReverseTranslator() *ReverseTranslator {
	return &ReverseTranslator{
		verbTemplates:   buildVerbTemplates(),
		verbEmojis:      buildVerbEmojis(),
		portugueseVerbs: buildPortugueseVerbs(),
	}
}

// Translate converts command to human-readable explanation
//
// Example input:
//   Command{Path: ["kubectl", "delete", "pod"], Args: ["kafka-0", "kafka-1"]}
//
// Example output:
//   "❌ DELETAR: 2 pods (kafka-0, kafka-1)"
func (rt *ReverseTranslator) Translate(cmd *nlp.Command) string {
	if len(cmd.Path) == 0 {
		return "Comando vazio"
	}
	
	// Extract verb (e.g., "delete", "get", "scale")
	verb := rt.extractVerb(cmd)
	
	// Get template for this verb
	template := rt.getTemplate(verb)
	
	// Build explanation
	explanation := rt.buildExplanation(cmd, verb, template)
	
	return explanation
}

// TranslateWithDetails adds extra details (namespace, flags, etc.)
func (rt *ReverseTranslator) TranslateWithDetails(cmd *nlp.Command) string {
	base := rt.Translate(cmd)
	details := rt.buildDetails(cmd)
	
	if details != "" {
		return base + "\n" + details
	}
	
	return base
}

// extractVerb identifies the action verb from command
func (rt *ReverseTranslator) extractVerb(cmd *nlp.Command) string {
	// For kubectl commands: kubectl [verb] [resource]
	if len(cmd.Path) >= 2 && cmd.Path[0] == "kubectl" {
		return cmd.Path[1]
	}
	
	// For other commands, use first path element
	if len(cmd.Path) > 0 {
		return cmd.Path[0]
	}
	
	return "execute"
}

// getTemplate returns template for verb
func (rt *ReverseTranslator) getTemplate(verb string) VerbTemplate {
	if template, exists := rt.verbTemplates[verb]; exists {
		return template
	}
	
	// Default template
	return VerbTemplate{
		Template:      "%s",
		Portuguese:    "executar",
		Icon:          "⚡",
		ShowCount:     true,
		ShowNamespace: true,
		ShowFlags:     true,
	}
}

// buildExplanation constructs human-readable explanation
func (rt *ReverseTranslator) buildExplanation(cmd *nlp.Command, verb string, template VerbTemplate) string {
	// Get Portuguese verb
	ptVerb := template.Portuguese
	icon := template.Icon
	
	// Extract resource type
	resource := rt.extractResource(cmd)
	
	// Count resources being affected
	count := len(cmd.Args)
	if count == 0 {
		count = 1
	}
	
	// Build base message
	var msg string
	if template.ShowCount && count > 1 {
		msg = fmt.Sprintf("%s %s: %d %s", icon, strings.ToUpper(ptVerb), count, resource)
	} else if count == 1 && len(cmd.Args) > 0 {
		msg = fmt.Sprintf("%s %s: %s %s", icon, strings.ToUpper(ptVerb), resource, cmd.Args[0])
	} else {
		msg = fmt.Sprintf("%s %s: %s", icon, strings.ToUpper(ptVerb), resource)
	}
	
	// Add resource names if multiple
	if count > 1 && len(cmd.Args) > 0 {
		resourceList := strings.Join(cmd.Args, ", ")
		if len(resourceList) > 50 {
			resourceList = resourceList[:47] + "..."
		}
		msg += fmt.Sprintf(" (%s)", resourceList)
	}
	
	return msg
}

// buildDetails adds namespace, flags, and other details
func (rt *ReverseTranslator) buildDetails(cmd *nlp.Command) string {
	var details []string
	
	// Add namespace if present
	if namespace, exists := cmd.Flags["-n"]; exists && namespace != "" {
		details = append(details, fmt.Sprintf("📍 Namespace: %s", namespace))
	}
	
	// Add important flags
	for key, value := range cmd.Flags {
		if key == "-n" {
			continue // Already handled
		}
		
		// Only show important flags
		if rt.isImportantFlag(key) {
			details = append(details, fmt.Sprintf("🔧 %s: %s", key, value))
		}
	}
	
	return strings.Join(details, "\n")
}

// extractResource gets resource type from command
func (rt *ReverseTranslator) extractResource(cmd *nlp.Command) string {
	// For kubectl: kubectl [verb] [resource] [names...]
	if len(cmd.Path) >= 3 && cmd.Path[0] == "kubectl" {
		return cmd.Path[2]
	}
	
	// Check flags
	if resource, exists := cmd.Flags["resource"]; exists {
		return resource
	}
	
	return "resource"
}

// isImportantFlag checks if flag should be shown to user
func (rt *ReverseTranslator) isImportantFlag(flag string) bool {
	importantFlags := map[string]bool{
		"--replicas": true,
		"--image":    true,
		"--all":      true,
		"--force":    true,
		"--cascade":  true,
	}
	
	return importantFlags[flag]
}

// buildVerbTemplates creates template database
func buildVerbTemplates() map[string]VerbTemplate {
	return map[string]VerbTemplate{
		"delete": {
			Template:      "❌ DELETAR: %s",
			Portuguese:    "deletar",
			Icon:          "❌",
			ShowCount:     true,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"remove": {
			Template:      "❌ REMOVER: %s",
			Portuguese:    "remover",
			Icon:          "❌",
			ShowCount:     true,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"scale": {
			Template:      "📊 ESCALAR: %s",
			Portuguese:    "escalar",
			Icon:          "📊",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"apply": {
			Template:      "✅ APLICAR: %s",
			Portuguese:    "aplicar",
			Icon:          "✅",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"create": {
			Template:      "➕ CRIAR: %s",
			Portuguese:    "criar",
			Icon:          "➕",
			ShowCount:     true,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"patch": {
			Template:      "🔧 MODIFICAR: %s",
			Portuguese:    "modificar",
			Icon:          "🔧",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"update": {
			Template:      "🔧 ATUALIZAR: %s",
			Portuguese:    "atualizar",
			Icon:          "🔧",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"get": {
			Template:      "🔍 CONSULTAR: %s",
			Portuguese:    "consultar",
			Icon:          "🔍",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     false,
		},
		"list": {
			Template:      "📋 LISTAR: %s",
			Portuguese:    "listar",
			Icon:          "📋",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     false,
		},
		"describe": {
			Template:      "📝 DESCREVER: %s",
			Portuguese:    "descrever",
			Icon:          "📝",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     false,
		},
		"logs": {
			Template:      "📜 LOGS: %s",
			Portuguese:    "ver logs",
			Icon:          "📜",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     true,
		},
		"exec": {
			Template:      "⚡ EXECUTAR: %s",
			Portuguese:    "executar comando",
			Icon:          "⚡",
			ShowCount:     false,
			ShowNamespace: true,
			ShowFlags:     true,
		},
	}
}

// buildVerbEmojis creates emoji mapping
func buildVerbEmojis() map[string]string {
	return map[string]string{
		"delete":   "❌",
		"remove":   "❌",
		"scale":    "📊",
		"apply":    "✅",
		"create":   "➕",
		"patch":    "🔧",
		"update":   "🔧",
		"get":      "🔍",
		"list":     "📋",
		"describe": "📝",
		"logs":     "📜",
		"exec":     "⚡",
	}
}

// buildPortugueseVerbs creates PT-BR verb mapping
func buildPortugueseVerbs() map[string]string {
	return map[string]string{
		"delete":   "deletar",
		"remove":   "remover",
		"scale":    "escalar",
		"apply":    "aplicar",
		"create":   "criar",
		"patch":    "modificar",
		"update":   "atualizar",
		"get":      "consultar",
		"list":     "listar",
		"describe": "descrever",
		"logs":     "ver logs",
		"exec":     "executar",
	}
}
```

**Checklist 3.1:**
- [ ] ReverseTranslator struct
- [ ] Translate function
- [ ] Template system
- [ ] Portuguese support
- [ ] Emoji icons

---

### Step 4: Dry Runner (1.5h)
**Arquivo:** `internal/intent/dry_runner.go`

```go
// Package intent - Dry Runner
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Executes commands in simulation mode to preview impact
// without actually making changes.
package intent

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// DryRunner executes commands in simulation mode
//
// Purpose: Before actually executing a destructive command,
// we simulate it to show user what would happen. This is
// similar to kubectl's --dry-run flag.
type DryRunner struct {
	// TODO: Add kubectl client for actual dry-run
}

// NewDryRunner creates a new dry runner
func NewDryRunner() *DryRunner {
	return &DryRunner{}
}

// Execute runs command in dry-run mode
//
// This simulates command execution without making actual changes.
// Returns detailed information about what would happen.
func (dr *DryRunner) Execute(ctx context.Context, cmd *nlp.Command) (*DryRunResult, error) {
	// TODO: Implement actual dry-run execution
	// For now, return simulated result
	
	result := &DryRunResult{
		Success: true,
		Output:  "Dry-run simulation",
		Errors:  []string{},
		ResourcesChanged: dr.extractResourceNames(cmd),
		Changes: []Change{},
	}
	
	return result, nil
}

// Estimate calculates impact without running command
//
// This is faster than Execute() - it just analyzes the command
// structure to estimate impact, without actually talking to K8s.
func (dr *DryRunner) Estimate(ctx context.Context, cmd *nlp.Command) (*Impact, error) {
	// Extract resource count
	resourceCount := dr.countResources(cmd)
	
	// Extract namespaces
	namespaces := dr.extractNamespaces(cmd)
	
	// Determine if reversible
	reversible := dr.isReversible(cmd)
	
	// Calculate risk score
	riskScore := dr.calculateRisk(cmd, resourceCount)
	
	// Estimate duration
	duration := dr.estimateDuration(cmd, resourceCount)
	
	// Build description
	description := dr.buildDescription(cmd, resourceCount, namespaces)
	
	impact := &Impact{
		ResourcesAffected: resourceCount,
		Namespaces:        namespaces,
		Reversible:        reversible,
		EstimatedDuration: duration,
		RiskScore:         riskScore,
		Description:       description,
	}
	
	return impact, nil
}

// countResources counts how many resources will be affected
func (dr *DryRunner) countResources(cmd *nlp.Command) int {
	// If specific resources are named, count them
	if len(cmd.Args) > 0 {
		return len(cmd.Args)
	}
	
	// If using selectors or --all, estimate higher
	if _, hasAll := cmd.Flags["--all"]; hasAll {
		return 10 // Conservative estimate
	}
	
	if _, hasSelector := cmd.Flags["-l"]; hasSelector {
		return 5 // Conservative estimate
	}
	
	// Default to 1 resource
	return 1
}

// extractNamespaces gets affected namespaces
func (dr *DryRunner) extractNamespaces(cmd *nlp.Command) []string {
	namespaces := []string{}
	
	if ns, exists := cmd.Flags["-n"]; exists && ns != "" {
		namespaces = append(namespaces, ns)
	} else {
		namespaces = append(namespaces, "default")
	}
	
	if _, hasAllNamespaces := cmd.Flags["--all-namespaces"]; hasAllNamespaces {
		namespaces = []string{"ALL"}
	}
	
	return namespaces
}

// isReversible determines if action can be undone
func (dr *DryRunner) isReversible(cmd *nlp.Command) bool {
	verb := dr.extractVerb(cmd)
	
	// Delete operations
	if verb == "delete" || verb == "remove" {
		// Check if resource has controller (reversible)
		// For now, assume pods with controllers are reversible
		resource := dr.extractResource(cmd)
		if resource == "pod" || resource == "pods" {
			return true // Pods are recreated by controllers
		}
		return false
	}
	
	// Scale operations are reversible
	if verb == "scale" {
		return true
	}
	
	// Apply/patch are reversible (can re-apply previous state)
	if verb == "apply" || verb == "patch" {
		return true
	}
	
	// Default to not reversible (be conservative)
	return false
}

// calculateRisk computes risk score (0.0 - 1.0)
func (dr *DryRunner) calculateRisk(cmd *nlp.Command, resourceCount int) float64 {
	verb := dr.extractVerb(cmd)
	
	// Base risk by verb
	baseRisk := 0.0
	switch verb {
	case "delete", "remove":
		baseRisk = 0.8
	case "scale":
		baseRisk = 0.5
	case "patch", "apply":
		baseRisk = 0.4
	case "create":
		baseRisk = 0.2
	default:
		baseRisk = 0.1
	}
	
	// Increase risk for multiple resources
	if resourceCount > 5 {
		baseRisk += 0.1
	}
	if resourceCount > 10 {
		baseRisk += 0.1
	}
	
	// Increase risk for production namespace
	namespaces := dr.extractNamespaces(cmd)
	for _, ns := range namespaces {
		if ns == "production" || ns == "prod" || ns == "ALL" {
			baseRisk += 0.2
		}
	}
	
	// Cap at 1.0
	if baseRisk > 1.0 {
		baseRisk = 1.0
	}
	
	return baseRisk
}

// estimateDuration estimates how long command will take
func (dr *DryRunner) estimateDuration(cmd *nlp.Command, resourceCount int) time.Duration {
	verb := dr.extractVerb(cmd)
	
	// Base duration by verb
	baseDuration := time.Second
	switch verb {
	case "delete":
		baseDuration = 5 * time.Second
	case "scale":
		baseDuration = 10 * time.Second
	case "apply":
		baseDuration = 3 * time.Second
	case "get", "list":
		baseDuration = 1 * time.Second
	}
	
	// Scale by resource count
	return baseDuration * time.Duration(resourceCount)
}

// buildDescription creates human-readable impact description
func (dr *DryRunner) buildDescription(cmd *nlp.Command, resourceCount int, namespaces []string) string {
	verb := dr.extractVerb(cmd)
	resource := dr.extractResource(cmd)
	
	var desc strings.Builder
	
	desc.WriteString(fmt.Sprintf("Esta ação irá %s ", verb))
	if resourceCount > 1 {
		desc.WriteString(fmt.Sprintf("%d %s", resourceCount, resource))
	} else {
		desc.WriteString(fmt.Sprintf("1 %s", resource))
	}
	
	if len(namespaces) > 0 && namespaces[0] != "default" {
		desc.WriteString(fmt.Sprintf(" no namespace %s", namespaces[0]))
	}
	
	desc.WriteString(".")
	
	return desc.String()
}

// extractVerb gets action verb from command
func (dr *DryRunner) extractVerb(cmd *nlp.Command) string {
	if len(cmd.Path) >= 2 && cmd.Path[0] == "kubectl" {
		return cmd.Path[1]
	}
	if len(cmd.Path) > 0 {
		return cmd.Path[0]
	}
	return "execute"
}

// extractResource gets resource type from command
func (dr *DryRunner) extractResource(cmd *nlp.Command) string {
	if len(cmd.Path) >= 3 && cmd.Path[0] == "kubectl" {
		return cmd.Path[2]
	}
	if resource, exists := cmd.Flags["resource"]; exists {
		return resource
	}
	return "resource"
}

// extractResourceNames gets names of specific resources
func (dr *DryRunner) extractResourceNames(cmd *nlp.Command) []string {
	return cmd.Args
}
```

**Checklist Step 4:**
- [ ] DryRunner struct
- [ ] Execute function (simulation)
- [ ] Estimate function (impact calculation)
- [ ] Risk calculation
- [ ] Duration estimation

---

### Step 5: Signature Verifier (1h)
**Arquivo:** `internal/intent/signature_verifier.go`

```go
// Package intent - Signature Verifier
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Handles cryptographic signatures for CRITICAL operations.
package intent

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"fmt"

	"github.com/verticedev/vcli-go/pkg/security"
)

// SignatureVerifier handles cryptographic signatures
//
// For CRITICAL operations (e.g., "delete namespace production"),
// we require the user to cryptographically sign the action.
// This prevents accidental execution and provides non-repudiation.
type SignatureVerifier struct {
	// TODO: Add key management
}

// NewSignatureVerifier creates a new signature verifier
func NewSignatureVerifier() *SignatureVerifier {
	return &SignatureVerifier{}
}

// Sign requests user to cryptographically sign a message
//
// For now, this is a placeholder. In production, we would:
// 1. Display message to user
// 2. User signs with their private key (GPG, SSH key, etc.)
// 3. We verify signature with their public key
// 4. Store signature in audit log
func (sv *SignatureVerifier) Sign(ctx context.Context, message string, user *security.User) ([]byte, error) {
	// TODO: Implement actual cryptographic signing
	// Options:
	// - GPG signing: echo "message" | gpg --sign
	// - SSH signing: echo "message" | ssh-keygen -Y sign
	// - PKCS#11 hardware token
	// - WebAuthn for browser-based
	
	// For now, return simulated signature
	signature := []byte(fmt.Sprintf("SIG:%s:%s", user.ID, message))
	return signature, nil
}

// Verify verifies a signature
func (sv *SignatureVerifier) Verify(ctx context.Context, message string, signature []byte, user *security.User) error {
	// TODO: Implement actual verification
	
	expected := []byte(fmt.Sprintf("SIG:%s:%s", user.ID, message))
	if string(signature) != string(expected) {
		return errors.New("signature verification failed")
	}
	
	return nil
}

// GenerateKeyPair generates RSA key pair for user (helper function)
func (sv *SignatureVerifier) GenerateKeyPair() (*rsa.PrivateKey, *rsa.PublicKey, error) {
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, nil, err
	}
	
	return privateKey, &privateKey.PublicKey, nil
}

// SignWithRSA signs message with RSA private key
func (sv *SignatureVerifier) SignWithRSA(message string, privateKey *rsa.PrivateKey) (string, error) {
	hashed := sha256.Sum256([]byte(message))
	
	signature, err := rsa.SignPKCS1v15(rand.Reader, privateKey, crypto.SHA256, hashed[:])
	if err != nil {
		return "", err
	}
	
	return base64.StdEncoding.EncodeToString(signature), nil
}

// VerifyRSA verifies RSA signature
func (sv *SignatureVerifier) VerifyRSA(message string, signatureB64 string, publicKey *rsa.PublicKey) error {
	signature, err := base64.StdEncoding.DecodeString(signatureB64)
	if err != nil {
		return err
	}
	
	hashed := sha256.Sum256([]byte(message))
	
	return rsa.VerifyPKCS1v15(publicKey, crypto.SHA256, hashed[:], signature)
}
```

**Checklist Step 5:**
- [ ] SignatureVerifier struct
- [ ] Sign function (placeholder)
- [ ] Verify function
- [ ] RSA helpers (for future use)

---

### Step 6: Tests (2h)
**Arquivos:** `*_test.go`

#### 6.1: Validator Tests (45min)

```go
// Package intent - Tests
package intent

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/security"
)

func TestValidator_RequiresConfirmation(t *testing.T) {
	validator := NewValidator()

	tests := []struct {
		name     string
		intent   *nlp.Intent
		expected bool
	}{
		{
			name: "LOW risk - no confirmation",
			intent: &nlp.Intent{
				RiskLevel: nlp.RiskLevelLOW,
				Verb:      "get",
				Target:    "pods",
			},
			expected: false,
		},
		{
			name: "MEDIUM risk - requires confirmation",
			intent: &nlp.Intent{
				RiskLevel: nlp.RiskLevelMEDIUM,
				Verb:      "create",
				Target:    "deployment",
			},
			expected: true,
		},
		{
			name: "HIGH risk - requires confirmation",
			intent: &nlp.Intent{
				RiskLevel: nlp.RiskLevelHIGH,
				Verb:      "delete",
				Target:    "pod",
			},
			expected: true,
		},
		{
			name: "CRITICAL risk - requires confirmation + signature",
			intent: &nlp.Intent{
				RiskLevel: nlp.RiskLevelCRITICAL,
				Verb:      "delete",
				Target:    "namespace",
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.RequiresConfirmation(tt.intent)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestValidator_Validate_AutoApprove(t *testing.T) {
	validator := NewValidator()
	ctx := context.Background()

	// LOW risk command should auto-approve
	parseResult := &nlp.ParseResult{
		Intent: &nlp.Intent{
			RiskLevel: nlp.RiskLevelLOW,
			Verb:      "get",
			Target:    "pods",
		},
		Command: &nlp.Command{
			Path: []string{"kubectl", "get", "pods"},
		},
	}

	user := &security.User{
		ID:       "test-user",
		Username: "testuser",
	}

	err := validator.Validate(ctx, parseResult, user)
	assert.NoError(t, err)
}

func TestValidator_Validate_WithConfirmation(t *testing.T) {
	// Setup validator with mock confirmation function
	confirmCalled := false
	mockConfirm := func(ctx context.Context, explanation string, impact *Impact) (bool, error) {
		confirmCalled = true
		assert.Contains(t, explanation, "DELETAR")
		return true, nil
	}

	validator := NewValidatorWithOptions(
		WithConfirmFunc(mockConfirm),
	)
	ctx := context.Background()

	// MEDIUM risk command should request confirmation
	parseResult := &nlp.ParseResult{
		Intent: &nlp.Intent{
			RiskLevel: nlp.RiskLevelMEDIUM,
			Verb:      "delete",
			Target:    "pod",
		},
		Command: &nlp.Command{
			Path: []string{"kubectl", "delete", "pod"},
			Args: []string{"test-pod"},
		},
	}

	user := &security.User{
		ID:       "test-user",
		Username: "testuser",
	}

	err := validator.Validate(ctx, parseResult, user)
	assert.NoError(t, err)
	assert.True(t, confirmCalled, "Confirmation should have been requested")
}

func TestValidator_Validate_UserDenies(t *testing.T) {
	// Setup validator that auto-denies
	mockConfirm := func(ctx context.Context, explanation string, impact *Impact) (bool, error) {
		return false, nil // User says NO
	}

	validator := NewValidatorWithOptions(
		WithConfirmFunc(mockConfirm),
	)
	ctx := context.Background()

	parseResult := &nlp.ParseResult{
		Intent: &nlp.Intent{
			RiskLevel: nlp.RiskLevelHIGH,
			Verb:      "delete",
			Target:    "deployment",
		},
		Command: &nlp.Command{
			Path: []string{"kubectl", "delete", "deployment"},
			Args: []string{"critical-service"},
		},
	}

	user := &security.User{
		ID:       "test-user",
		Username: "testuser",
	}

	err := validator.Validate(ctx, parseResult, user)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "User cancelled")
}
```

#### 6.2: Reverse Translator Tests (45min)

```go
func TestReverseTranslator_Translate(t *testing.T) {
	translator := NewReverseTranslator()

	tests := []struct {
		name        string
		cmd         *nlp.Command
		shouldContain []string
	}{
		{
			name: "delete single pod",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
				Args: []string{"kafka-0"},
				Flags: map[string]string{
					"-n": "kafka",
				},
			},
			shouldContain: []string{"DELETAR", "pod", "kafka-0"},
		},
		{
			name: "delete multiple pods",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
				Args: []string{"kafka-0", "kafka-1", "kafka-2"},
				Flags: map[string]string{
					"-n": "kafka",
				},
			},
			shouldContain: []string{"DELETAR", "3", "pods"},
		},
		{
			name: "get pods (query)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "get", "pods"},
				Flags: map[string]string{
					"-n": "default",
				},
			},
			shouldContain: []string{"CONSULTAR", "pods"},
		},
		{
			name: "scale deployment",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "scale", "deployment"},
				Args: []string{"webapp"},
				Flags: map[string]string{
					"-n":         "production",
					"--replicas": "5",
				},
			},
			shouldContain: []string{"ESCALAR", "deployment"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := translator.Translate(tt.cmd)
			
			for _, expected := range tt.shouldContain {
				assert.Contains(t, result, expected,
					"Translation should contain '%s'. Got: %s", expected, result)
			}
		})
	}
}

func TestReverseTranslator_TranslateWithDetails(t *testing.T) {
	translator := NewReverseTranslator()

	cmd := &nlp.Command{
		Path: []string{"kubectl", "delete", "pod"},
		Args: []string{"test-pod"},
		Flags: map[string]string{
			"-n":      "kafka",
			"--force": "true",
		},
	}

	result := translator.TranslateWithDetails(cmd)
	
	assert.Contains(t, result, "DELETAR")
	assert.Contains(t, result, "Namespace: kafka")
	assert.Contains(t, result, "--force")
}
```

#### 6.3: Dry Runner Tests (30min)

```go
func TestDryRunner_Estimate(t *testing.T) {
	runner := NewDryRunner()
	ctx := context.Background()

	tests := []struct {
		name              string
		cmd               *nlp.Command
		expectedResources int
		expectedRisk      float64
	}{
		{
			name: "single pod delete",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
				Args: []string{"test-pod"},
			},
			expectedResources: 1,
			expectedRisk:      0.8,
		},
		{
			name: "multiple pods delete",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
				Args: []string{"pod-1", "pod-2", "pod-3"},
			},
			expectedResources: 3,
			expectedRisk:      0.8,
		},
		{
			name: "scale operation",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "scale", "deployment"},
				Args: []string{"webapp"},
				Flags: map[string]string{
					"--replicas": "5",
				},
			},
			expectedResources: 1,
			expectedRisk:      0.5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			impact, err := runner.Estimate(ctx, tt.cmd)
			require.NoError(t, err)
			require.NotNil(t, impact)
			
			assert.Equal(t, tt.expectedResources, impact.ResourcesAffected)
			assert.InDelta(t, tt.expectedRisk, impact.RiskScore, 0.2)
		})
	}
}

func TestDryRunner_IsReversible(t *testing.T) {
	runner := NewDryRunner()

	tests := []struct {
		name     string
		cmd      *nlp.Command
		expected bool
	}{
		{
			name: "delete pod (reversible - controller recreates)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
			},
			expected: true,
		},
		{
			name: "delete deployment (not reversible)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "deployment"},
			},
			expected: false,
		},
		{
			name: "scale (reversible)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "scale", "deployment"},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := runner.isReversible(tt.cmd)
			assert.Equal(t, tt.expected, result)
		})
	}
}
```

**Checklist Step 6:**
- [ ] Validator tests
- [ ] Reverse translator tests
- [ ] Dry runner tests
- [ ] Edge cases covered
- [ ] Error paths tested

---

### Step 7: Documentation (30min)
**Arquivo:** `internal/intent/README.md`

```markdown
# Intent Validation (Camada 5)

**Lead Architect:** Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author:** Claude (MAXIMUS AI Assistant)  
**Status:** ✅ COMPLETE

## Purpose

Camada 5 do **Guardian of Intent v2.0** - pergunta ao usuário "Você tem certeza?" antes de executar ações destrutivas.

## Components

### Validator
Core component que orquestra validação de intenções.

**Responsibilities:**
- Determinar se confirmação é necessária
- Gerar explicação em linguagem natural
- Estimar impacto da ação
- Solicitar confirmação do usuário
- Para ações CRITICAL: solicitar assinatura criptográfica

### Reverse Translator
Converte comandos estruturados de volta para linguagem natural.

**Example:**
```go
cmd := &Command{Path: ["kubectl", "delete", "pod"], Args: ["kafka-0"]}
explanation := translator.Translate(cmd)
// Output: "❌ DELETAR: pod kafka-0"
```

### Dry Runner
Simula execução de comandos e estima impacto.

**Features:**
- Dry-run execution (quando possível)
- Impact estimation
- Risk calculation
- Duration estimation

### Signature Verifier
Gerencia assinaturas criptográficas para ações CRITICAL.

**Future:** Integração com GPG, SSH keys, hardware tokens.

## Risk Levels & Confirmation Strategy

| Risk | Confirmation Required | Details |
|------|----------------------|---------|
| LOW | ❌ No | Auto-approve read-only ops |
| MEDIUM | ✅ Yes | Simple confirmation prompt |
| HIGH | ✅ Yes | + Impact preview |
| CRITICAL | ✅ Yes | + Cryptographic signature |

## Usage

```go
validator := intent.NewValidator()

// Parse natural language
parseResult, _ := parser.Parse(ctx, "delete crashed pods")

// Validate intent
err := validator.Validate(ctx, parseResult, user)
if err != nil {
    // User denied or validation failed
    return err
}

// Proceed with execution
```

## Testing

Run tests:
```bash
cd internal/intent
go test -v -cover
```

Expected coverage: ≥90%

## Architecture Decision Records

**Why reverse translation?**
- User clarity: Show exactly what will happen
- Security: Catch parser mistakes before damage
- Trust: Transparency builds confidence

**Why dry-run?**
- Preview changes before committing
- Estimate impact accurately
- Reduce accidental damage

**Why crypto signatures for CRITICAL?**
- Non-repudiation: Prove who authorized
- Deliberate action: Requires extra step
- Audit trail: Signature in immutable log

## Future Enhancements

- [ ] Integrate with kubectl --dry-run
- [ ] Implement actual GPG signing
- [ ] Impact visualization (before/after)
- [ ] Undo/rollback automatic
- [ ] Learn from user confirmations

---

**Gloria a Deus. "Eu sou porque ELE é."**
```

**Checklist Step 7:**
- [ ] README with overview
- [ ] Usage examples
- [ ] Architecture decisions
- [ ] Future enhancements

---

### Step 8: Validation & Coverage (30min)

```bash
# Run tests
cd vcli-go/internal/intent
go test -v -cover

# Check coverage
go test -coverprofile=coverage.out
go tool cover -html=coverage.out

# Run linting
golangci-lint run

# Format code
gofmt -s -w .
```

**Checklist Step 8:**
- [ ] All tests passing
- [ ] Coverage ≥ 90%
- [ ] No linting errors
- [ ] Code formatted

---

## 🎯 END OF DAY CHECKLIST

- [ ] All 8 steps completed
- [ ] Code committed to Git
- [ ] Progress report written
- [ ] Tomorrow's plan ready
- [ ] Documentation updated

---

## 📊 METRICS

**Expected Stats:**
- Files created: 9
- Lines of code: ~2000
- Tests written: ~30
- Coverage: ≥90%
- Time invested: 8h

---

**Gloria a Deus. Transformamos dias em minutos.**

**Status:** 🔄 IN PROGRESS | **Day:** 1/12

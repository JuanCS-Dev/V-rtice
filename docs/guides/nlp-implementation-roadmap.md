# NLP Parser Implementation Roadmap
## vcli-go Natural Language Interface - Plano de Execução

**Arquiteto:** Juan Carlos (Inspiração: Jesus)  
**Co-Autor:** Claude (GitHub Copilot)  
**Data:** 2025-10-12  
**Status:** PLANO DE IMPLEMENTAÇÃO ATIVO

---

## 🎯 VISÃO GERAL

**Objetivo:** Implementar parser NLP security-first em vcli-go seguindo as 7 Camadas de Verificação do "Guardião da Intenção" v2.0.

**Duração Total:** 10 sprints (20 semanas)  
**Início:** 2025-10-12  
**Término Previsto:** 2026-02-28

**Princípios:**
- ✅ **Metodicidade** - Um passo de cada vez
- ✅ **Simplicidade** - Tarefas complexas, passos simples
- ✅ **Qualidade** - Zero mocks, zero placeholders, zero TODOs
- ✅ **Segurança** - Security-first em cada linha
- ✅ **Sustentabilidade** - Progresso consistente > sprints heroicos

---

## 📊 ROADMAP VISUAL

```
┌────────────────────────────────────────────────────────────────────────┐
│                         NLP PARSER ROADMAP                              │
│                         10 Sprints = 20 Weeks                           │
└────────────────────────────────────────────────────────────────────────┘

FASE 1: FUNDAÇÃO (Sprint 1-2) ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 20%
├─ Sprint 1: Parser Core + Basic Grammar
└─ Sprint 2: Integration + Basic Commands

FASE 2: SEGURANÇA CORE (Sprint 3-4) ░░░░░░░░████████░░░░░░░░░░░░░░ 40%
├─ Sprint 3: Camadas 1-2 (Auth + Authz)
└─ Sprint 4: Camadas 3-4 (Sandbox + Intent Validation)

FASE 3: RESILIÊNCIA (Sprint 5-6) ░░░░░░░░░░░░░░░░████████░░░░░░░░ 60%
├─ Sprint 5: Camadas 5-6 (Rate Limit + Behavior)
└─ Sprint 6: Camada 7 (Audit) + Observability

FASE 4: INTELIGÊNCIA (Sprint 7-8) ░░░░░░░░░░░░░░░░░░░░░░░░████████ 80%
├─ Sprint 7: ML Model + Continuous Learning
└─ Sprint 8: Advanced Grammar + Context Awareness

FASE 5: POLIMENTO (Sprint 9-10) ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 100%
├─ Sprint 9: Multi-Domain + Performance
└─ Sprint 10: Documentation + Release
```

---

## 🏃 FASE 1: FUNDAÇÃO (Sprint 1-2)

### **Sprint 1: Parser Core + Basic Grammar** (2 semanas)

#### Objetivos
- [ ] Setup da estrutura de diretórios
- [ ] Implementar pipeline básico de parsing
- [ ] Criar gramáticas para comandos básicos K8s
- [ ] Integração com shell existente
- [ ] Testes unitários

#### Tarefas Detalhadas

##### 1.1 Setup da Estrutura (Dia 1)
```bash
# Criar diretórios
mkdir -p vcli-go/internal/{nlp,auth,authz,sandbox,intent,ratelimit,behavior,audit,crypto}
mkdir -p vcli-go/internal/nlp/grammar
mkdir -p vcli-go/test/nlp/{fixtures,mocks}
```

**Arquivos a criar:**
- `internal/nlp/parser.go` - Interface principal
- `internal/nlp/models.go` - Structs de dados
- `internal/nlp/tokenizer.go` - Tokenização
- `internal/nlp/normalizer.go` - Normalização

**Deliverable:** Estrutura de pastas criada, arquivos vazios commitados

---

##### 1.2 Tokenizer (Dia 2)
**Arquivo:** `internal/nlp/tokenizer.go`

```go
package nlp

import (
	"strings"
	"unicode"
)

// Token represents a parsed token
type Token struct {
	Value    string
	Type     TokenType
	Start    int
	End      int
	Original string
}

type TokenType int

const (
	TokenUnknown TokenType = iota
	TokenVerb              // list, delete, create
	TokenResource          // pod, deployment, service
	TokenNamespace         // namespace name
	TokenLabel             // label selector
	TokenNumber            // numeric values
	TokenOperator          // =, !=, in
)

type Tokenizer struct {
	vocabulary map[string]TokenType
}

func NewTokenizer() *Tokenizer {
	return &Tokenizer{
		vocabulary: map[string]TokenType{
			"lista":      TokenVerb,
			"list":       TokenVerb,
			"mostra":     TokenVerb,
			"ver":        TokenVerb,
			"delete":     TokenVerb,
			"deleta":     TokenVerb,
			"remove":     TokenVerb,
			"pod":        TokenResource,
			"pods":       TokenResource,
			"deployment": TokenResource,
			"deploy":     TokenResource,
			"service":    TokenResource,
			"svc":        TokenResource,
		},
	}
}

func (t *Tokenizer) Tokenize(input string) []Token {
	tokens := []Token{}
	words := t.splitWords(input)
	
	position := 0
	for _, word := range words {
		token := Token{
			Value:    word,
			Start:    position,
			End:      position + len(word),
			Original: word,
		}
		
		// Determine token type
		if tokenType, found := t.vocabulary[strings.ToLower(word)]; found {
			token.Type = tokenType
		} else if t.isNumber(word) {
			token.Type = TokenNumber
		} else if t.isLabelSelector(word) {
			token.Type = TokenLabel
		} else {
			token.Type = TokenUnknown
		}
		
		tokens = append(tokens, token)
		position += len(word) + 1 // +1 for space
	}
	
	return tokens
}

func (t *Tokenizer) splitWords(input string) []string {
	return strings.FieldsFunc(input, func(r rune) bool {
		return unicode.IsSpace(r)
	})
}

func (t *Tokenizer) isNumber(word string) bool {
	for _, r := range word {
		if !unicode.IsDigit(r) {
			return false
		}
	}
	return len(word) > 0
}

func (t *Tokenizer) isLabelSelector(word string) bool {
	return strings.Contains(word, "=") || strings.Contains(word, "!=")
}
```

**Testes:**
```go
// test/nlp/tokenizer_test.go
func TestTokenizer_Basic(t *testing.T) {
	tokenizer := nlp.NewTokenizer()
	
	tokens := tokenizer.Tokenize("lista os pods")
	assert.Len(t, tokens, 3)
	assert.Equal(t, nlp.TokenVerb, tokens[0].Type)
	assert.Equal(t, nlp.TokenResource, tokens[2].Type)
}
```

**Deliverable:** Tokenizer funcional com 20+ testes

---

##### 1.3 Normalizer (Dia 3)
**Arquivo:** `internal/nlp/normalizer.go`

```go
package nlp

import (
	"strings"
	"github.com/agnivade/levenshtein"
)

type Normalizer struct {
	vocabulary   []string
	abbreviations map[string]string
	stopWords    map[string]bool
}

func NewNormalizer() *Normalizer {
	return &Normalizer{
		vocabulary: []string{
			"lista", "list", "mostra", "ver",
			"delete", "deleta", "remove",
			"pod", "pods", "deployment", "service",
		},
		abbreviations: map[string]string{
			"k8s":    "kubernetes",
			"ns":     "namespace",
			"svc":    "service",
			"deploy": "deployment",
			"sts":    "statefulset",
			"ds":     "daemonset",
			"cm":     "configmap",
			"pv":     "persistentvolume",
			"pvc":    "persistentvolumeclaim",
		},
		stopWords: map[string]bool{
			"o":   true,
			"os":  true,
			"a":   true,
			"as":  true,
			"que": true,
			"no":  true,
			"na":  true,
		},
	}
}

func (n *Normalizer) Normalize(input string) string {
	// 1. Lowercase
	normalized := strings.ToLower(input)
	
	// 2. Trim
	normalized = strings.TrimSpace(normalized)
	
	// 3. Expand abbreviations
	for abbr, full := range n.abbreviations {
		normalized = strings.ReplaceAll(normalized, abbr, full)
	}
	
	return normalized
}

func (n *Normalizer) CorrectSpelling(word string) string {
	minDistance := 999
	bestMatch := word
	
	for _, knownWord := range n.vocabulary {
		distance := levenshtein.ComputeDistance(word, knownWord)
		if distance < minDistance && distance <= 2 {
			minDistance = distance
			bestMatch = knownWord
		}
	}
	
	return bestMatch
}

func (n *Normalizer) RemoveStopWords(tokens []Token) []Token {
	filtered := []Token{}
	for _, token := range tokens {
		if !n.stopWords[strings.ToLower(token.Value)] {
			filtered = append(filtered, token)
		}
	}
	return filtered
}
```

**Deliverable:** Normalizer com spell correction e stop words

---

##### 1.4 Intent Classifier (Rules-Based) (Dia 4-5)
**Arquivo:** `internal/nlp/intent_classifier.go`

```go
package nlp

import (
	"regexp"
	"sort"
)

type IntentType int

const (
	IntentUnknown IntentType = iota
	IntentList
	IntentDescribe
	IntentCreate
	IntentDelete
	IntentUpdate
	IntentScale
	IntentLogs
	IntentExec
	IntentApply
)

type IntentRule struct {
	Pattern  *regexp.Regexp
	Intent   IntentType
	Priority int
}

type IntentClassifier struct {
	rules []IntentRule
}

func NewIntentClassifier() *IntentClassifier {
	return &IntentClassifier{
		rules: []IntentRule{
			{
				Pattern:  regexp.MustCompile(`(?i)(list|lista|mostra|ver).*(pod|deployment|service)`),
				Intent:   IntentList,
				Priority: 100,
			},
			{
				Pattern:  regexp.MustCompile(`(?i)(describe|descreve|detalhe).*(pod|deployment|service)`),
				Intent:   IntentDescribe,
				Priority: 100,
			},
			{
				Pattern:  regexp.MustCompile(`(?i)(delete|deleta|remove).*(pod|deployment|service)`),
				Intent:   IntentDelete,
				Priority: 100,
			},
			{
				Pattern:  regexp.MustCompile(`(?i)(scale|escala).*(deployment|sts)`),
				Intent:   IntentScale,
				Priority: 100,
			},
			{
				Pattern:  regexp.MustCompile(`(?i)(log|logs).*(pod)`),
				Intent:   IntentLogs,
				Priority: 100,
			},
		},
	}
}

type IntentResult struct {
	Intent     IntentType
	Confidence float64
	Matches    []IntentMatch
}

type IntentMatch struct {
	Rule       IntentRule
	MatchScore float64
}

func (ic *IntentClassifier) Classify(input string) IntentResult {
	matches := []IntentMatch{}
	
	for _, rule := range ic.rules {
		if rule.Pattern.MatchString(input) {
			matches = append(matches, IntentMatch{
				Rule:       rule,
				MatchScore: 1.0, // Simple boolean match for now
			})
		}
	}
	
	if len(matches) == 0 {
		return IntentResult{
			Intent:     IntentUnknown,
			Confidence: 0.0,
		}
	}
	
	// Sort by priority
	sort.Slice(matches, func(i, j int) bool {
		return matches[i].Rule.Priority > matches[j].Rule.Priority
	})
	
	// Return highest priority match
	return IntentResult{
		Intent:     matches[0].Rule.Intent,
		Confidence: matches[0].MatchScore,
		Matches:    matches,
	}
}
```

**Deliverable:** Classifier reconhece 5 intents básicos

---

##### 1.5 Entity Extractor (Dia 6)
**Arquivo:** `internal/nlp/entity_extractor.go`

```go
package nlp

import "strings"

type EntityType int

const (
	EntityUnknown EntityType = iota
	EntityResource
	EntityNamespace
	EntityLabel
	EntityField
	EntityNumber
)

type Entity struct {
	Type     EntityType
	Value    string
	Start    int
	End      int
	Metadata map[string]interface{}
}

type EntityExtractor struct {
	resources  map[string]string
	namespaces []string
}

func NewEntityExtractor() *EntityExtractor {
	return &EntityExtractor{
		resources: map[string]string{
			"pod":        "pods",
			"pods":       "pods",
			"deployment": "deployments",
			"deploy":     "deployments",
			"service":    "services",
			"svc":        "services",
		},
	}
}

func (ee *EntityExtractor) Extract(tokens []Token) []Entity {
	entities := []Entity{}
	
	for i, token := range tokens {
		// Extract resources
		if resourceType, found := ee.resources[strings.ToLower(token.Value)]; found {
			entities = append(entities, Entity{
				Type:  EntityResource,
				Value: resourceType,
				Start: token.Start,
				End:   token.End,
				Metadata: map[string]interface{}{
					"original": token.Original,
				},
			})
		}
		
		// Extract namespaces
		if strings.ToLower(token.Value) == "namespace" || strings.ToLower(token.Value) == "ns" {
			if i+1 < len(tokens) {
				entities = append(entities, Entity{
					Type:  EntityNamespace,
					Value: tokens[i+1].Value,
					Start: tokens[i+1].Start,
					End:   tokens[i+1].End,
				})
			}
		}
		
		// Extract labels
		if token.Type == TokenLabel {
			parts := strings.Split(token.Value, "=")
			if len(parts) == 2 {
				entities = append(entities, Entity{
					Type:  EntityLabel,
					Value: token.Value,
					Start: token.Start,
					End:   token.End,
					Metadata: map[string]interface{}{
						"key":   parts[0],
						"value": parts[1],
					},
				})
			}
		}
	}
	
	return entities
}
```

**Deliverable:** Extractor identifica resources, namespaces, labels

---

##### 1.6 Main Parser (Dia 7-8)
**Arquivo:** `internal/nlp/parser.go`

```go
package nlp

import (
	"fmt"
	"time"
)

type Parser struct {
	tokenizer   *Tokenizer
	normalizer  *Normalizer
	classifier  *IntentClassifier
	extractor   *EntityExtractor
}

func NewParser() *Parser {
	return &Parser{
		tokenizer:  NewTokenizer(),
		normalizer: NewNormalizer(),
		classifier: NewIntentClassifier(),
		extractor:  NewEntityExtractor(),
	}
}

type ParsedCommand struct {
	RawInput   string
	Intent     IntentType
	Resource   string
	Namespace  string
	Labels     []string
	Confidence float64
	Tokens     []Token
	Entities   []Entity
	Timestamp  time.Time
}

func (p *Parser) Parse(input string) (*ParsedCommand, error) {
	// 1. Normalize
	normalized := p.normalizer.Normalize(input)
	
	// 2. Tokenize
	tokens := p.tokenizer.Tokenize(normalized)
	
	// 3. Remove stop words
	tokens = p.normalizer.RemoveStopWords(tokens)
	
	// 4. Classify intent
	intentResult := p.classifier.Classify(normalized)
	if intentResult.Intent == IntentUnknown {
		return nil, fmt.Errorf("unable to understand intent: %s", input)
	}
	
	// 5. Extract entities
	entities := p.extractor.Extract(tokens)
	
	// 6. Build command
	cmd := &ParsedCommand{
		RawInput:   input,
		Intent:     intentResult.Intent,
		Confidence: intentResult.Confidence,
		Tokens:     tokens,
		Entities:   entities,
		Timestamp:  time.Now(),
	}
	
	// Extract specific fields
	for _, entity := range entities {
		switch entity.Type {
		case EntityResource:
			cmd.Resource = entity.Value
		case EntityNamespace:
			cmd.Namespace = entity.Value
		case EntityLabel:
			cmd.Labels = append(cmd.Labels, entity.Value)
		}
	}
	
	return cmd, nil
}
```

**Deliverable:** Parser completo conectando todos os componentes

---

##### 1.7 Integration com Shell (Dia 9)
**Arquivo:** `cmd/nlp.go`

```go
package main

import (
	"fmt"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/nlp"
)

var nlpCmd = &cobra.Command{
	Use:   "nlp [command]",
	Short: "Execute commands using natural language",
	Long:  `Parse and execute commands using natural language.`,
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		executeNLP(cmd, args)
	},
}

func executeNLP(cmd *cobra.Command, args []string) {
	// Join all args as one input
	input := ""
	for i, arg := range args {
		if i > 0 {
			input += " "
		}
		input += arg
	}
	
	// Parse
	parser := nlp.NewParser()
	parsed, err := parser.Parse(input)
	if err != nil {
		fmt.Printf("❌ Error: %v\n", err)
		return
	}
	
	// Display parsed result
	fmt.Printf("📝 Parsed Command:\n")
	fmt.Printf("   Intent: %v\n", parsed.Intent)
	fmt.Printf("   Resource: %s\n", parsed.Resource)
	fmt.Printf("   Namespace: %s\n", parsed.Namespace)
	fmt.Printf("   Confidence: %.2f\n", parsed.Confidence)
	
	// Execute (TODO: Phase 2)
	fmt.Printf("\n⚠️  Execution not yet implemented (Phase 2)\n")
}

func init() {
	rootCmd.AddCommand(nlpCmd)
}
```

**Deliverable:** Comando `vcli nlp` funcional

---

##### 1.8 Testes E2E (Dia 10)
```go
// test/nlp/e2e_test.go
func TestE2E_ListPods(t *testing.T) {
	parser := nlp.NewParser()
	
	tests := []struct {
		input             string
		expectedIntent    nlp.IntentType
		expectedResource  string
	}{
		{
			input:            "lista os pods",
			expectedIntent:   nlp.IntentList,
			expectedResource: "pods",
		},
		{
			input:            "mostra os deployments no namespace production",
			expectedIntent:   nlp.IntentList,
			expectedResource: "deployments",
		},
	}
	
	for _, tt := range tests {
		parsed, err := parser.Parse(tt.input)
		assert.NoError(t, err)
		assert.Equal(t, tt.expectedIntent, parsed.Intent)
		assert.Equal(t, tt.expectedResource, parsed.Resource)
	}
}
```

**Deliverable:** 20+ testes E2E passando

---

#### Sprint 1 Deliverables
- ✅ Estrutura de diretórios completa
- ✅ Tokenizer funcional (20+ testes)
- ✅ Normalizer com spell correction (15+ testes)
- ✅ Intent Classifier rules-based (10+ testes)
- ✅ Entity Extractor (15+ testes)
- ✅ Main Parser integrando tudo (10+ testes)
- ✅ Comando `vcli nlp` funcional
- ✅ 20+ testes E2E

**Critério de Sucesso:** Parser reconhece e parseia corretamente 10 comandos básicos com >90% confidence.

---

### **Sprint 2: Integration + Basic Commands** (2 semanas)

#### Objetivos
- [ ] Command Builder - traduz ParsedCommand para kubectl
- [ ] Executor - executa comandos kubectl
- [ ] Shell integration - NLP no shell interativo
- [ ] Error handling robusto
- [ ] Documentação básica

#### Tarefas Detalhadas

##### 2.1 Command Builder (Dia 1-3)
**Arquivo:** `internal/nlp/command_builder.go`

```go
package nlp

import (
	"fmt"
	"strings"
)

type CommandBuilder struct {
	defaultNamespace string
}

func NewCommandBuilder() *CommandBuilder {
	return &CommandBuilder{
		defaultNamespace: "default",
	}
}

type KubectlCommand struct {
	Binary    string
	Verb      string
	Resource  string
	Name      string
	Namespace string
	Flags     map[string]string
	Args      []string
}

func (cb *CommandBuilder) Build(parsed *ParsedCommand) (*KubectlCommand, error) {
	cmd := &KubectlCommand{
		Binary:    "kubectl",
		Flags:     make(map[string]string),
	}
	
	// Map intent to kubectl verb
	switch parsed.Intent {
	case IntentList:
		cmd.Verb = "get"
	case IntentDescribe:
		cmd.Verb = "describe"
	case IntentDelete:
		cmd.Verb = "delete"
	case IntentScale:
		cmd.Verb = "scale"
	case IntentLogs:
		cmd.Verb = "logs"
	default:
		return nil, fmt.Errorf("unsupported intent: %v", parsed.Intent)
	}
	
	// Set resource
	cmd.Resource = parsed.Resource
	
	// Set namespace
	if parsed.Namespace != "" {
		cmd.Namespace = parsed.Namespace
	} else {
		cmd.Namespace = cb.defaultNamespace
	}
	cmd.Flags["namespace"] = cmd.Namespace
	
	// Set labels
	if len(parsed.Labels) > 0 {
		cmd.Flags["selector"] = strings.Join(parsed.Labels, ",")
	}
	
	return cmd, nil
}

func (cmd *KubectlCommand) ToShellCommand() string {
	parts := []string{cmd.Binary, cmd.Verb, cmd.Resource}
	
	if cmd.Name != "" {
		parts = append(parts, cmd.Name)
	}
	
	for flag, value := range cmd.Flags {
		parts = append(parts, fmt.Sprintf("--%s=%s", flag, value))
	}
	
	parts = append(parts, cmd.Args...)
	
	return strings.Join(parts, " ")
}
```

**Deliverable:** Builder traduz 5 intents para kubectl

---

##### 2.2 Executor (Dia 4-5)
**Arquivo:** `internal/nlp/executor.go`

```go
package nlp

import (
	"context"
	"fmt"
	"os/exec"
	"time"
)

type Executor struct {
	timeout time.Duration
	dryRun  bool
}

func NewExecutor() *Executor {
	return &Executor{
		timeout: 30 * time.Second,
		dryRun:  false,
	}
}

type ExecutionResult struct {
	Command    string
	Output     string
	Error      string
	ExitCode   int
	Duration   time.Duration
	Success    bool
}

func (e *Executor) Execute(cmd *KubectlCommand) (*ExecutionResult, error) {
	shellCmd := cmd.ToShellCommand()
	
	if e.dryRun {
		return &ExecutionResult{
			Command: shellCmd,
			Output:  "[DRY RUN] Would execute: " + shellCmd,
			Success: true,
		}, nil
	}
	
	ctx, cancel := context.WithTimeout(context.Background(), e.timeout)
	defer cancel()
	
	startTime := time.Now()
	
	execCmd := exec.CommandContext(ctx, "sh", "-c", shellCmd)
	output, err := execCmd.CombinedOutput()
	
	duration := time.Since(startTime)
	
	result := &ExecutionResult{
		Command:  shellCmd,
		Output:   string(output),
		Duration: duration,
	}
	
	if err != nil {
		result.Error = err.Error()
		result.Success = false
		if exitErr, ok := err.(*exec.ExitError); ok {
			result.ExitCode = exitErr.ExitCode()
		}
	} else {
		result.Success = true
		result.ExitCode = 0
	}
	
	return result, nil
}
```

**Deliverable:** Executor com timeout e error handling

---

##### 2.3 Shell Integration (Dia 6-7)
Modificar `internal/shell/executor.go` para detectar linguagem natural:

```go
func (e *Executor) Execute(input string) error {
	// Detect if input is natural language
	if e.isNaturalLanguage(input) {
		return e.executeNLP(input)
	}
	
	// Execute as regular command
	return e.executeRegular(input)
}

func (e *Executor) isNaturalLanguage(input string) bool {
	// Simple heuristic: check for Portuguese/English verbs
	nlpVerbs := []string{
		"lista", "list", "mostra", "ver",
		"deleta", "delete", "remove",
		"cria", "create",
	}
	
	for _, verb := range nlpVerbs {
		if strings.Contains(strings.ToLower(input), verb) {
			return true
		}
	}
	
	return false
}

func (e *Executor) executeNLP(input string) error {
	parser := nlp.NewParser()
	builder := nlp.NewCommandBuilder()
	executor := nlp.NewExecutor()
	
	// Parse
	parsed, err := parser.Parse(input)
	if err != nil {
		return err
	}
	
	// Build
	cmd, err := builder.Build(parsed)
	if err != nil {
		return err
	}
	
	// Execute
	result, err := executor.Execute(cmd)
	if err != nil {
		return err
	}
	
	// Display output
	fmt.Println(result.Output)
	
	return nil
}
```

**Deliverable:** Shell reconhece e executa NLP automaticamente

---

##### 2.4 Error Handling (Dia 8)
Adicionar error types específicos:

```go
// internal/nlp/errors.go
package nlp

import "errors"

var (
	ErrUnknownIntent     = errors.New("unable to determine intent")
	ErrAmbiguousCommand  = errors.New("command is ambiguous")
	ErrMissingResource   = errors.New("resource not specified")
	ErrMissingNamespace  = errors.New("namespace not specified")
	ErrLowConfidence     = errors.New("confidence too low")
	ErrExecutionFailed   = errors.New("command execution failed")
	ErrTimeout           = errors.New("execution timeout")
)

type ParseError struct {
	Input   string
	Message string
	Err     error
}

func (e *ParseError) Error() string {
	return fmt.Sprintf("parse error for '%s': %s", e.Input, e.Message)
}

func (e *ParseError) Unwrap() error {
	return e.Err
}
```

**Deliverable:** Error handling robusto

---

##### 2.5 Documentação (Dia 9-10)
```markdown
# NLP Parser - User Guide

## Comandos Suportados

### List
- `lista os pods`
- `mostra os deployments no namespace production`
- `ver os services com label app=frontend`

### Delete
- `deleta o pod nginx`
- `remove os deployments com label env=test`

### Logs
- `mostra os logs do pod api-7d9f8b-abc12`

## Exemplos

```bash
# Listar pods
$ vcli nlp lista os pods

# Com namespace
$ vcli nlp mostra os deployments no namespace staging

# Com label
$ vcli nlp lista pods com label app=cache
```
```

**Deliverable:** README.md com exemplos

---

#### Sprint 2 Deliverables
- ✅ Command Builder traduzindo para kubectl
- ✅ Executor com timeout e error handling
- ✅ Shell detecta e executa NLP automaticamente
- ✅ Error handling robusto com tipos específicos
- ✅ Documentação de uso

**Critério de Sucesso:** Usuário pode executar 10 comandos básicos via NLP no shell interativo.

---

## 🔒 FASE 2: SEGURANÇA CORE (Sprint 3-4)

### **Sprint 3: Camadas 1-2 (Auth + Authz)** (2 semanas)

[Continua com implementação detalhada das camadas de segurança...]

---

## 📈 MÉTRICAS DE PROGRESSO

### Por Sprint
- [ ] Todos os testes unitários passando (>90% coverage)
- [ ] Zero linter warnings
- [ ] Zero TODOs no código
- [ ] Documentação atualizada
- [ ] Demo gravado e commitado

### Por Fase
- [ ] Validation checkpoint com stakeholders
- [ ] Performance benchmarks atingidos
- [ ] Security audit aprovado
- [ ] Retrospectiva documentada

---

## 🎯 DEFINIÇÃO DE PRONTO

Para considerar cada sprint **COMPLETO**:

1. ✅ **Código**
   - Todos os arquivos implementados
   - Zero mocks, zero placeholders
   - Type hints completos
   - Docstrings no formato correto

2. ✅ **Testes**
   - Coverage >90%
   - Todos os testes passando
   - Testes de segurança incluídos

3. ✅ **Qualidade**
   - Zero linter warnings
   - `go vet` clean
   - `golangci-lint` clean

4. ✅ **Documentação**
   - README atualizado
   - Exemplos funcionais
   - Changelog atualizado

5. ✅ **Git**
   - Commits atômicos e descritivos
   - Branch mergeado em main
   - Tag de versão criada

---

## 🚀 PRÓXIMOS PASSOS

**Agora (2025-10-12):**
1. Review deste roadmap
2. Aprovação para iniciar Sprint 1
3. Setup do ambiente

**Hoje ainda:**
- Criar estrutura de diretórios (Tarefa 1.1)
- Implementar Tokenizer (Tarefa 1.2)

**Amanhã:**
- Implementar Normalizer (Tarefa 1.3)
- Começar Intent Classifier (Tarefa 1.4)

---

**Glória a Deus. Seguimos metodicamente.**

**Arquiteto:** Juan Carlos  
**Co-Autor:** Claude  
**Status:** PRONTO PARA IMPLEMENTAÇÃO  
**Data:** 2025-10-12

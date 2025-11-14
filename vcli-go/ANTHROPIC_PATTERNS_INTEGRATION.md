# 🧠 ANTHROPIC AI PATTERNS → VCLI-GO INTEGRATION

**Data**: 2025-11-13
**Fonte**: Pesquisa extensiva de documentação oficial Anthropic
**Objetivo**: Trazer best practices e patterns da Anthropic para o vcli-go

---

## 📚 EXECUTIVE SUMMARY

Baseado em pesquisa da documentação oficial Anthropic (Claude Code, Constitutional AI, Multi-Agent Systems, Tool Use), este documento mapeia **padrões comprovados** que devemos aplicar no vcli-go.

**Principais Descobertas**:
1. **CLI Design**: Anthropic usa arquitetura low-level, unopinionated com herança de ambiente
2. **Multi-Agent**: Orchestrator-worker pattern com artifact systems e memory management
3. **Constitutional AI**: Two-phase training (supervised + RLAIF) com chain-of-thought
4. **Tool Use**: Schema-driven com parallel execution e context efficiency
5. **Production**: Circuit breakers, retry logic, monitoring com OpenTelemetry

---

## 1. 🖥️ CLI DESIGN PATTERNS

### 1.1 Anthropic's Approach: Claude Code

**Filosofia**: "Intentionally low-level and unopinionated, providing close to raw model access"

**Princípios Chave**:
- ✅ **Environment Inheritance**: CLI herda bash environment do usuário
- ✅ **File-based Instructions**: Arquivos especiais (ex: `CLAUDE.md`) auto-carregados como contexto
- ✅ **Progressive Permission Model**: Conservativo por padrão, com allowlisting para operações confiáveis
- ✅ **Multiple Config Layers**: Project-level, global, user-home (hierárquico)
- ✅ **Headless Operation**: Flag `-p` para contextos não-interativos (CI, hooks)
- ✅ **Slash Commands**: Templates reusáveis em `.claude/commands/` com `$ARGUMENTS` keyword

**Aplicação ao VCLI-GO**:

```yaml
# Estrutura de config proposta (inspirada em Claude Code)
~/.vcli/
  ├── config.yaml              # Global config
  ├── settings.json            # Permission settings
  ├── commands/                # Slash commands
  │   ├── debug.md
  │   ├── investigate.md
  │   └── scan.md
  └── prompts/                 # Prompt templates
      ├── agent-smith.txt
      ├── immune-response.txt
      └── hitl-decision.txt

project/
  ├── .vcli/
  │   ├── config.yaml          # Project-specific overrides
  │   ├── VCLI.md              # Auto-loaded context (like CLAUDE.md)
  │   └── local.yaml           # .gitignore'd local config
  └── ...
```

**Recomendações de Implementação**:

1. **VCLI.md Auto-Loading**:
```go
// internal/config/context_loader.go
func LoadProjectContext() (string, error) {
    // Search hierarchy: ./VCLI.md → ../.vcli/VCLI.md → ~/.vcli/VCLI.md
    contextPaths := []string{
        "./VCLI.md",
        filepath.Join(getProjectRoot(), ".vcli", "VCLI.md"),
        filepath.Join(getUserHome(), ".vcli", "VCLI.md"),
    }

    var contexts []string
    for _, path := range contextPaths {
        if content, err := os.ReadFile(path); err == nil {
            contexts = append(contexts, string(content))
        }
    }

    return strings.Join(contexts, "\n\n---\n\n"), nil
}
```

2. **Slash Commands System**:
```go
// internal/shell/slash_commands.go
type SlashCommand struct {
    Name        string
    Description string
    Template    string
    Args        []string
}

func LoadSlashCommands() map[string]*SlashCommand {
    commandsDir := filepath.Join(getUserHome(), ".vcli", "commands")
    // Parse *.md files, extract template with $ARGUMENTS keyword
    // Make available via shell autocomplete
}
```

3. **Permission System**:
```go
// internal/permissions/allowlist.go
type Permission struct {
    Tool      string   // "Bash", "Edit", "k8s_delete"
    Patterns  []string // ["git commit:*", "npm install:*"]
    Allowed   bool
}

func CheckPermission(tool, args string) (bool, error) {
    // Check .vcli/settings.json allowlist
    // Prompt user if not in allowlist
    // Save decision for future
}
```

---

## 2. 🤖 AGENT ARCHITECTURE (Multi-Agent Systems)

### 2.1 Anthropic's Multi-Agent Research System

**Pattern**: Orchestrator-Worker com Artifact Systems

**Arquitetura**:
```
Lead Agent (Orchestrator)
  ├── Subagent 1 (Researcher)  ─┐
  ├── Subagent 2 (Analyzer)    ├─→ Parallel Execution
  ├── Subagent 3 (Validator)   ─┘
  └── External Memory Store (Artifacts)
```

**Princípios Chave**:

1. **Task Delegation Rules** (scaling):
   - Simple fact check: 1 agent, 3-10 tool calls
   - Direct comparison: 2-4 subagents, 10-15 calls each
   - Complex research: 10+ subagents, divided responsibilities

2. **Memory Management**:
   - Save research plan to external memory before hitting context limit (200k tokens)
   - Spawn fresh subagents with clean contexts
   - Maintain continuity through careful handoffs

3. **Artifact Systems**:
   - Subagents store work in external systems
   - Return lightweight references (not full content)
   - Prevents information degradation and token bloat

4. **Parallelization**:
   - Lead agent spins 3-5 subagents in parallel (not serial)
   - Subagents execute 3+ tools concurrently
   - **Result**: Cut research time by 90%

5. **Error Recovery**:
   - Resumable execution from failure points
   - Model intelligence for graceful adaptation
   - Deterministic safeguards: retry logic, checkpoints

**Aplicação ao VCLI-GO**:

### 2.2 Agent Smith Enhancement

**Arquitetura Atual**: Agent Smith em `cmd/agents.go`

**Proposta**: Implementar Orchestrator-Worker Pattern

```go
// internal/agents/orchestrator.go
type Orchestrator struct {
    leadAgent    *Agent
    subagents    []*Subagent
    artifactStore *ArtifactStore
    memoryStore  *MemoryStore
    maxSubagents int // 10 for complex, 4 for medium, 1 for simple
}

type Subagent struct {
    ID           string
    Objective    string
    OutputFormat string
    ToolGuidance []string
    Boundaries   TaskBoundaries
    Context      *CleanContext // Fresh context window
}

type ArtifactStore struct {
    artifacts map[string]Artifact
}

type Artifact struct {
    ID      string
    Type    string // "report", "analysis", "code", "data"
    Content interface{}
    Metadata map[string]string
}

func (o *Orchestrator) Delegate(task Task) error {
    // 1. Analyze task complexity
    complexity := o.analyzeComplexity(task)

    // 2. Determine subagent count
    subagentCount := o.getSubagentCount(complexity)

    // 3. Decompose into subtasks
    subtasks := o.decompose(task, subagentCount)

    // 4. Spawn subagents in parallel
    results := make(chan SubagentResult, subagentCount)
    for _, subtask := range subtasks {
        go func(st Subtask) {
            subagent := o.createSubagent(st)
            result := subagent.Execute()

            // Store artifact instead of returning full content
            artifactID := o.artifactStore.Store(result)
            results <- SubagentResult{
                SubagentID: subagent.ID,
                ArtifactRef: artifactID,
                Summary: result.Summary,
            }
        }(subtask)
    }

    // 5. Collect results
    consolidatedResults := o.collectResults(results, subagentCount)

    // 6. Synthesize final answer
    return o.leadAgent.Synthesize(consolidatedResults)
}

func (o *Orchestrator) analyzeComplexity(task Task) Complexity {
    // Simple: fact-finding, status checks
    // Medium: comparisons, analysis
    // Complex: multi-step research, investigations

    if task.RequiresMultipleSources() && task.RequiresDeepAnalysis() {
        return ComplexityHigh
    } else if task.RequiresComparison() || task.RequiresDataProcessing() {
        return ComplexityMedium
    }
    return ComplexityLow
}

func (o *Orchestrator) getSubagentCount(c Complexity) int {
    switch c {
    case ComplexityLow:
        return 1
    case ComplexityMedium:
        return 4
    case ComplexityHigh:
        return 10
    default:
        return 1
    }
}
```

### 2.3 Memory Management Pattern

```go
// internal/agents/memory.go
type MemoryStore struct {
    checkpoints map[string]Checkpoint
    contextLimit int // 200000 tokens
}

type Checkpoint struct {
    AgentID     string
    Timestamp   time.Time
    ResearchPlan string
    Progress    map[string]interface{}
    Context     string
}

func (m *MemoryStore) SaveCheckpoint(agentID string, context AgentContext) error {
    // Before hitting context limit, save state
    if context.TokenCount() > m.contextLimit - 10000 {
        checkpoint := Checkpoint{
            AgentID:     agentID,
            Timestamp:   time.Now(),
            ResearchPlan: context.GetPlan(),
            Progress:    context.GetProgress(),
            Context:     context.Summarize(), // Compress context
        }

        m.checkpoints[agentID] = checkpoint
        return nil
    }
    return nil
}

func (m *MemoryStore) RestoreCheckpoint(agentID string) (*Checkpoint, error) {
    if cp, exists := m.checkpoints[agentID]; exists {
        return &cp, nil
    }
    return nil, errors.New("checkpoint not found")
}
```

### 2.4 Parallel Tool Execution

```go
// internal/agents/parallel_executor.go
func (s *Subagent) ExecuteToolsInParallel(tools []Tool) []ToolResult {
    results := make(chan ToolResult, len(tools))

    // Execute 3+ tools concurrently (Anthropic pattern)
    for _, tool := range tools {
        go func(t Tool) {
            result := t.Execute()
            results <- result
        }(tool)
    }

    // Collect all results
    var allResults []ToolResult
    for i := 0; i < len(tools); i++ {
        allResults = append(allResults, <-results)
    }

    return allResults
}
```

---

## 3. ⚖️ CONSTITUTIONAL AI INTEGRATION

### 3.1 Anthropic's Constitutional AI

**Two-Phase Training**:
1. **Supervised Learning (SL)**: Model critiques and revises own responses using constitution
2. **Reinforcement Learning (RLAIF)**: RL from AI Feedback using constitutional principles

**Princípios**:
- Chain-of-thought reasoning for transparency
- Self-critique and revision cycles
- AI-generated feedback based on principles

**Aplicação ao MAXIMUS & HITL**:

### 3.2 MAXIMUS Constitutional Decision-Making

```go
// internal/maximus/constitutional.go
type ConstitutionalEngine struct {
    constitution []Principle
    decisionLog  *AuditLog
}

type Principle struct {
    ID          string
    Name        string
    Description string
    Rule        func(Decision) (bool, string) // Returns (compliant, reasoning)
}

type Decision struct {
    ID          string
    Title       string
    Type        string
    Context     map[string]interface{}
    ProposedAction Action
}

func (c *ConstitutionalEngine) Evaluate(decision Decision) (EvaluationResult, error) {
    // Phase 1: Self-Critique (Supervised Learning inspired)
    critique := c.critique(decision)

    // Phase 2: Revision
    revisedDecision := c.revise(decision, critique)

    // Phase 3: Constitutional Check
    result := EvaluationResult{
        OriginalDecision: decision,
        RevisedDecision:  revisedDecision,
        Critiques:        critique,
        ConstitutionalCompliance: make(map[string]bool),
        Reasoning:        make(map[string]string),
    }

    for _, principle := range c.constitution {
        compliant, reasoning := principle.Rule(revisedDecision)
        result.ConstitutionalCompliance[principle.ID] = compliant
        result.Reasoning[principle.ID] = reasoning
    }

    // Log for audit trail (transparency)
    c.decisionLog.Record(result)

    return result, nil
}

func (c *ConstitutionalEngine) critique(d Decision) []Critique {
    // Chain-of-thought reasoning
    var critiques []Critique

    // Check each principle
    for _, p := range c.constitution {
        compliant, reasoning := p.Rule(d)
        if !compliant {
            critiques = append(critiques, Critique{
                Principle:  p.Name,
                Issue:      reasoning,
                Severity:   c.assessSeverity(p, d),
                Suggestion: c.generateSuggestion(p, d),
            })
        }
    }

    return critiques
}

func (c *ConstitutionalEngine) revise(d Decision, critiques []Critique) Decision {
    revised := d

    for _, critique := range critiques {
        // Apply suggestions to revise decision
        revised = c.applySuggestion(revised, critique.Suggestion)
    }

    return revised
}
```

### 3.3 HITL Integration with Constitutional AI

```go
// cmd/hitl.go enhancements
func submitDecisionWithConstitutionalCheck(decision Decision) error {
    // 1. Constitutional evaluation
    constitutionalEngine := maximus.NewConstitutionalEngine(getConstitution())
    evaluation, err := constitutionalEngine.Evaluate(decision)
    if err != nil {
        return err
    }

    // 2. If non-compliant, show violations to user
    if !evaluation.IsFullyCompliant() {
        fmt.Println("⚠️ CONSTITUTIONAL VIOLATIONS DETECTED:")
        for principle, compliant := range evaluation.ConstitutionalCompliance {
            if !compliant {
                fmt.Printf("  ❌ %s: %s\n", principle, evaluation.Reasoning[principle])
            }
        }

        // Prompt user: proceed with revised or abort
        proceed := promptUser("Proceed with revised decision?")
        if !proceed {
            return errors.New("decision rejected due to constitutional violations")
        }

        decision = evaluation.RevisedDecision
    }

    // 3. Submit to MAXIMUS
    return maximusClient.Submit(decision)
}

func getConstitution() []Principle {
    return []Principle{
        {
            ID:   "P1-COMPLETUDE",
            Name: "Completude Obrigatória",
            Rule: func(d Decision) (bool, string) {
                if d.ProposedAction.IsIncomplete() {
                    return false, "Ação proposta está incompleta - viola P1"
                }
                return true, "Ação completa"
            },
        },
        {
            ID:   "P2-VALIDACAO",
            Name: "Validação Preventiva",
            Rule: func(d Decision) (bool, string) {
                if !d.ProposedAction.IsValidated() {
                    return false, "Ação não foi validada - viola P2"
                }
                return true, "Ação validada"
            },
        },
        // P3-P6 from DOUTRINA VÉRTICE...
    }
}
```

---

## 4. 🔧 TOOL USE OPTIMIZATION

### 4.1 Anthropic's Tool Use Patterns

**Schema-Driven Design**:
```json
{
  "name": "get_threat_intel",
  "description": "Get threat intelligence for an indicator. Supports IPs, domains, file hashes.",
  "input_schema": {
    "type": "object",
    "properties": {
      "indicator": {
        "type": "string",
        "description": "IP address, domain, or SHA256 hash to lookup"
      },
      "sources": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Intel sources to query (e.g., VirusTotal, AlienVault, Shodan)",
        "enum": ["virustotal", "alienvault", "shodan", "all"]
      }
    },
    "required": ["indicator"]
  }
}
```

**Key Principles**:
1. **Detailed Descriptions**: Go beyond tool names - explain purpose, usage, examples
2. **Enum Constraints**: Use enums for limited choices (reduces ambiguity)
3. **Required vs Optional**: Clearly mark required parameters
4. **Parallel Execution**: Independent tools can run concurrently
5. **Sequential Dependencies**: Design tools to work independently when possible

**Aplicação ao VCLI-GO**:

### 4.2 Tool Registry Pattern

```go
// internal/tools/registry.go
type ToolRegistry struct {
    tools map[string]Tool
}

type Tool struct {
    Name        string
    Description string
    InputSchema Schema
    Execute     func(input map[string]interface{}) (interface{}, error)
    Category    string // "immune", "threat", "k8s", "maximus"
}

type Schema struct {
    Type       string
    Properties map[string]Property
    Required   []string
}

type Property struct {
    Type        string
    Description string
    Enum        []string // Optional constraint
    Examples    []string // Help with usage
}

func NewToolRegistry() *ToolRegistry {
    registry := &ToolRegistry{tools: make(map[string]Tool)}

    // Register all vcli tools with detailed schemas
    registry.RegisterImmune Tools()
    registry.RegisterThreatTools()
    registry.RegisterK8sTools()
    registry.RegisterMAXIMUSTools()
    // ... etc for all 90+ services

    return registry
}

func (r *ToolRegistry) RegisterImmune Tools() {
    r.Register(Tool{
        Name: "immune_agent_list",
        Description: "List all active immune system agents (Neutrophils, Macrophages, Dendritic Cells, T-Cells, Memory Cells). Returns agent IDs, states, lifecycle info, and performance metrics.",
        InputSchema: Schema{
            Type: "object",
            Properties: map[string]Property{
                "state": {
                    Type:        "string",
                    Description: "Filter by agent state",
                    Enum:        []string{"ACTIVE", "IDLE", "DORMANT", "DEAD", "ALL"},
                    Examples:    []string{"ACTIVE"},
                },
                "agent_type": {
                    Type:        "string",
                    Description: "Filter by agent type",
                    Enum:        []string{"neutrophil", "macrophage", "dendritic", "t-cell", "memory-cell", "all"},
                },
            },
            Required: []string{}, // All optional
        },
        Execute: func(input map[string]interface{}) (interface{}, error) {
            client := immune.NewClient(getImmuneEndpoint())
            state := input["state"].(string)
            agentType := input["agent_type"].(string)
            return client.ListAgents(state, agentType)
        },
        Category: "immune",
    })

    // Register 10+ more immune tools...
}
```

### 4.3 Parallel Tool Execution Pattern

```go
// internal/tools/executor.go
type ParallelExecutor struct {
    registry *ToolRegistry
}

func (e *ParallelExecutor) ExecuteBatch(toolCalls []ToolCall) []ToolResult {
    results := make(chan ToolResult, len(toolCalls))

    // Identify independent vs dependent tools
    independent, sequential := e.analyzeDependencies(toolCalls)

    // Execute independent tools in parallel
    for _, toolCall := range independent {
        go func(tc ToolCall) {
            tool := e.registry.Get(tc.ToolName)
            result, err := tool.Execute(tc.Input)
            results <- ToolResult{
                ToolName: tc.ToolName,
                Result:   result,
                Error:    err,
            }
        }(toolCall)
    }

    // Execute sequential tools in order
    for _, toolCall := range sequential {
        tool := e.registry.Get(toolCall.ToolName)
        result, err := tool.Execute(toolCall.Input)
        results <- ToolResult{
            ToolName: toolCall.ToolName,
            Result:   result,
            Error:    err,
        }
    }

    // Collect all
    var allResults []ToolResult
    for i := 0; i < len(toolCalls); i++ {
        allResults = append(allResults, <-results)
    }

    return allResults
}

func (e *ParallelExecutor) analyzeDependencies(calls []ToolCall) (independent, sequential []ToolCall) {
    // Simple heuristic: if output of one tool is input to another, they're sequential
    // Otherwise, independent

    dependencyGraph := make(map[string][]string)

    for _, call := range calls {
        for _, input := range call.InputDependencies {
            dependencyGraph[input] = append(dependencyGraph[input], call.ToolName)
        }
    }

    for _, call := range calls {
        if len(dependencyGraph[call.ToolName]) == 0 {
            independent = append(independent, call)
        } else {
            sequential = append(sequential, call)
        }
    }

    return
}
```

---

## 5. 🚀 PRODUCTION DEPLOYMENT PATTERNS

### 5.1 Anthropic's Production Best Practices

**Key Findings**:
- OpenTelemetry traces for observability
- Token bucket rate limiting
- Circuit breaker patterns
- Retry logic with exponential backoff
- Hybrid failover between providers
- Regular checkpoints for resumability

**Aplicação ao VCLI-GO**:

### 5.2 Circuit Breaker Pattern

```go
// internal/circuitbreaker/breaker.go (já existe no vcli!)
// Enhancements based on Anthropic patterns:

type CircuitBreaker struct {
    name          string
    maxFailures   int
    resetTimeout  time.Duration
    halfOpenMax   int
    state         State
    failures      int
    lastFailTime  time.Time
    successCount  int // For half-open state

    // New: Anthropic-inspired enhancements
    checkpointFunc func() error // Save state before risky operation
    fallbackFunc   func() (interface{}, error) // Hybrid failover
}

func (cb *CircuitBreaker) Call(fn func() (interface{}, error)) (interface{}, error) {
    // 1. Check state
    if cb.state == StateOpen {
        if time.Since(cb.lastFailTime) > cb.resetTimeout {
            cb.state = StateHalfOpen
            cb.successCount = 0
        } else {
            // Circuit open - try fallback if available
            if cb.fallbackFunc != nil {
                return cb.fallbackFunc()
            }
            return nil, errors.New("circuit breaker is open")
        }
    }

    // 2. Save checkpoint before risky operation (Anthropic pattern)
    if cb.checkpointFunc != nil {
        if err := cb.checkpointFunc(); err != nil {
            log.Printf("Checkpoint failed: %v", err)
        }
    }

    // 3. Execute
    result, err := fn()

    // 4. Update state
    if err != nil {
        cb.recordFailure()
        return nil, err
    }

    cb.recordSuccess()
    return result, nil
}
```

### 5.3 Retry Logic with Exponential Backoff

```go
// internal/retry/retry.go
type RetryPolicy struct {
    maxAttempts    int
    initialBackoff time.Duration
    maxBackoff     time.Duration
    multiplier     float64

    // Anthropic pattern: Jitter to prevent thundering herd
    jitterFactor   float64
}

func (r *RetryPolicy) Execute(fn func() error) error {
    var lastErr error
    backoff := r.initialBackoff

    for attempt := 0; attempt < r.maxAttempts; attempt++ {
        err := fn()
        if err == nil {
            return nil // Success
        }

        lastErr = err

        // Don't retry on certain errors
        if isNonRetryable(err) {
            return err
        }

        // Calculate backoff with jitter (Anthropic pattern)
        jitter := time.Duration(float64(backoff) * r.jitterFactor * rand.Float64())
        sleep := backoff + jitter

        if sleep > r.maxBackoff {
            sleep = r.maxBackoff
        }

        log.Printf("Retry attempt %d/%d after %v", attempt+1, r.maxAttempts, sleep)
        time.Sleep(sleep)

        backoff = time.Duration(float64(backoff) * r.multiplier)
    }

    return fmt.Errorf("max retries exceeded: %w", lastErr)
}
```

### 5.4 OpenTelemetry Integration

```go
// internal/observability/tracing.go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

type TracedToolExecutor struct {
    registry *ToolRegistry
    tracer   trace.Tracer
}

func (t *TracedToolExecutor) Execute(ctx context.Context, toolCall ToolCall) (interface{}, error) {
    // Start span (Anthropic pattern: trace prompts, tool invocations, token usage)
    ctx, span := t.tracer.Start(ctx, "tool.execute",
        trace.WithAttributes(
            attribute.String("tool.name", toolCall.ToolName),
            attribute.String("tool.category", toolCall.Category),
        ),
    )
    defer span.End()

    // Get tool
    tool := t.registry.Get(toolCall.ToolName)

    // Execute with timing
    start := time.Now()
    result, err := tool.Execute(toolCall.Input)
    duration := time.Since(start)

    // Record metrics
    span.SetAttributes(
        attribute.Int64("tool.duration_ms", duration.Milliseconds()),
        attribute.Bool("tool.success", err == nil),
    )

    if err != nil {
        span.RecordError(err)
    }

    return result, err
}
```

### 5.5 Rate Limiting (Token Bucket)

```go
// internal/ratelimit/limiter.go (já existe no vcli!)
// Confirmation that existing implementation aligns with Anthropic patterns ✅

// Already implements token bucket algorithm correctly
type RateLimiter struct {
    rate       float64
    capacity   int
    tokens     float64
    lastUpdate time.Time
    mu         sync.Mutex
}

// Good implementation - matches Anthropic recommendations
func (r *RateLimiter) Allow() bool {
    r.mu.Lock()
    defer r.mu.Unlock()

    now := time.Now()
    elapsed := now.Sub(r.lastUpdate).Seconds()

    // Refill tokens
    r.tokens += elapsed * r.rate
    if r.tokens > float64(r.capacity) {
        r.tokens = float64(r.capacity)
    }

    r.lastUpdate = now

    // Consume token if available
    if r.tokens >= 1.0 {
        r.tokens -= 1.0
        return true
    }

    return false
}
```

---

## 6. 📝 PROMPT ENGINEERING TEMPLATES

### 6.1 System Prompt Structure (Anthropic Best Practices)

**10-Step Structure** recomendado:

1. **Role Definition** - Quem é o AI
2. **Task Context** - O que está fazendo
3. **Step-by-Step Instructions** - Como fazer
4. **Examples** (Few-shot) - Demonstrações
5. **Constraints** - O que NÃO fazer
6. **Output Format** - Como estruturar resposta
7. **Quality Criteria** - Padrões de qualidade
8. **Error Handling** - Como lidar com edge cases
9. **Chain-of-Thought** - Raciocínio explícito
10. **Verification** - Auto-verificação

**Aplicação ao VCLI-GO**:

### 6.2 Prompt Templates para Agent Smith

```go
// internal/prompts/templates.go
const AgentSmithSystemPrompt = `# AGENT SMITH - Autonomous Development Framework

## 1. ROLE DEFINITION
You are Agent Smith, an autonomous AI development agent working within the Vértice-MAXIMUS cybersecurity platform. You assist with code generation, debugging, testing, and architectural decisions.

## 2. TASK CONTEXT
You have access to the vcli-go codebase and can:
- Read files and understand code structure
- Generate complete, production-ready code (zero placeholders)
- Execute tests and validate implementations
- Integrate with backend services (MAXIMUS, Immune Core, etc.)
- Follow Constitutional AI principles from DOUTRINA VÉRTICE v3.0

## 3. STEP-BY-STEP INSTRUCTIONS
When given a development task:
1. **Explore**: Read relevant files, understand current implementation
2. **Plan**: Generate detailed implementation plan with extended thinking
3. **Validate Plan**: Confirm plan with user before coding
4. **Implement**: Write complete code following project conventions
5. **Test**: Execute tests and verify functionality
6. **Review**: Self-critique for quality and completeness
7. **Document**: Update documentation if needed

## 4. EXAMPLES
Example task: "Implement Neuro Cortex client"

Response:
"I'll implement the Neuro Cortex gRPC client. Let me first explore the existing client patterns...

[Reads internal/grpc/immune_client.go for pattern reference]

Plan:
1. Create internal/grpc/neuro_client.go with gRPC client
2. Define proto interface for cortex service
3. Implement methods: Plan(), Analyze(), Execute()
4. Add connection pooling and retry logic
5. Create cmd/neuro.go with CLI commands
6. Add tests in internal/grpc/neuro_client_test.go

Does this plan look good?"

## 5. CONSTRAINTS
- ❌ NEVER generate placeholder code (no TODOs, no stubs)
- ❌ NEVER hallucinate API methods (validate all APIs first)
- ❌ NEVER skip error handling
- ❌ NEVER use mocks in production code
- ❌ NEVER proceed with coding before plan approval
- ✅ ALWAYS write complete, production-ready code
- ✅ ALWAYS validate assumptions
- ✅ ALWAYS follow DOUTRINA VÉRTICE principles

## 6. OUTPUT FORMAT
For code generation:
\`\`\`go
// Complete, runnable code with:
// - Package declaration
// - All imports
// - Full error handling
// - Documentation comments
// - No placeholders
\`\`\`

For plans:
- Numbered list of specific steps
- Clear deliverables
- Time estimates
- Dependencies identified

## 7. QUALITY CRITERIA
Code must satisfy:
- Compiles without errors
- Follows Go conventions (gofmt, golint)
- Has comprehensive error handling
- Includes unit tests (if applicable)
- Matches existing code style
- Satisfies DOUTRINA metrics (LEI < 1.0, CRS ≥ 95%)

## 8. ERROR HANDLING
If you encounter:
- **Missing file**: Ask user for file path or create it
- **Unclear requirements**: Ask clarifying questions
- **API uncertainty**: Read documentation or ask before proceeding
- **Conflicting patterns**: Propose options and ask user to choose

## 9. CHAIN-OF-THOUGHT
For complex tasks, think through:
"Let me think about this step by step:
1. What's the current state?
2. What are we trying to achieve?
3. What are the dependencies?
4. What could go wrong?
5. What's the best approach?"

Use "think harder" for architectural decisions.

## 10. VERIFICATION
Before submitting code:
- [ ] Does it compile?
- [ ] Does it follow conventions?
- [ ] Is error handling complete?
- [ ] Are there any placeholders?
- [ ] Does it match the plan?
- [ ] Would it pass code review?

If any checkbox is unchecked, revise before submitting.
`

const ImmuneResponsePrompt = `# IMMUNE SYSTEM AI RESPONSE AGENT

## ROLE
You are an AI agent within the Active Immune Core, responsible for analyzing threats and recommending defensive actions.

## TASK
Analyze cyber threat indicators and recommend immune system responses (deploy neutrophils, clone macrophages, activate memory cells).

## CHAIN-OF-THOUGHT REASONING
For each threat:
1. Classify severity (1-10 scale)
2. Identify threat type (malware, intrusion, anomaly, etc.)
3. Match against memory cell patterns
4. Recommend agent deployment strategy
5. Justify recommendation with evidence

## OUTPUT FORMAT
{
  "threat_id": "...",
  "severity": 8,
  "threat_type": "ransomware",
  "memory_match": "pattern_sha256:abc123",
  "recommended_action": {
    "agent_type": "neutrophil",
    "count": 50,
    "priority": "high",
    "reasoning": "Rapid response needed for active file encryption"
  }
}

## CONSTRAINTS
- NEVER recommend destructive actions without confirmation
- ALWAYS provide reasoning for recommendations
- ALWAYS check memory cells before deploying new agents
`

const HITLDecisionPrompt = `# HITL DECISION EVALUATION AGENT

## ROLE
You are a Constitutional AI agent evaluating HITL (Human-in-the-Loop) decisions for compliance with DOUTRINA VÉRTICE v3.0.

## TASK
Evaluate proposed decisions against constitutional principles (P1-P6), identify violations, suggest revisions.

## CHAIN-OF-THOUGHT
For each decision:
1. Extract proposed action
2. Check against each principle (P1-P6)
3. Identify violations with specific reasoning
4. Suggest concrete revisions
5. Re-evaluate revised decision

## TWO-PHASE PROCESS (Constitutional AI)
Phase 1 - Self-Critique:
- Analyze decision against constitution
- List all violations
- Rate severity (critical, high, medium, low)

Phase 2 - Revision:
- For each violation, propose fix
- Generate revised decision
- Verify compliance

## OUTPUT FORMAT
{
  "decision_id": "...",
  "original_compliant": false,
  "violations": [
    {
      "principle": "P1-COMPLETUDE",
      "severity": "critical",
      "issue": "Proposed action lacks implementation details",
      "suggestion": "Add specific steps and deliverables"
    }
  ],
  "revised_decision": {...},
  "revised_compliant": true
}
`
```

---

## 7. 🎯 APLICAÇÕES ESPECÍFICAS PARA VCLI-GO

### 7.1 Shell Redesign com Anthropic Patterns

**Current**: Shell em `internal/shell/shell.go` com go-prompt

**Enhancements**:

1. **VCLI.md Auto-Loading** (como CLAUDE.md):
```go
// Load project context automatically
func (s *Shell) loadContext() string {
    context, _ := LoadProjectContext() // Search ./VCLI.md → ../.vcli/VCLI.md → ~/.vcli/VCLI.md
    return context
}
```

2. **Slash Commands** (templates reusáveis):
```go
// User creates ~/.vcli/commands/investigate.md:
/*
Investigate security incident $INCIDENT_ID

Steps:
1. Get incident details from NIS
2. Query threat intel for IOCs
3. Check immune system response
4. Generate report
*/

// Shell loads and makes available via autocomplete
func (s *Shell) executeSlashCommand(name string, args []string) {
    template := s.slashCommands[name]
    prompt := strings.ReplaceAll(template, "$ARGUMENTS", strings.Join(args, " "))
    s.executor.Execute(prompt)
}
```

3. **Extended Thinking Mode** (como Claude Code):
```go
func (s *Shell) execute(input string) {
    // Detect thinking keywords
    thinkingBudget := s.detectThinkingLevel(input)
    // "think" < "think hard" < "think harder" < "ultrathink"

    switch thinkingBudget {
    case ThinkingUltra:
        s.executor.SetTimeout(300 * time.Second) // 5 min for complex planning
    case ThinkingHarder:
        s.executor.SetTimeout(120 * time.Second)
    case ThinkingHard:
        s.executor.SetTimeout(60 * time.Second)
    default:
        s.executor.SetTimeout(30 * time.Second)
    }

    s.executor.Execute(input)
}
```

### 7.2 Multi-Service Tool Registry

Com 90+ serviços backend, precisamos de registry organizado:

```go
// internal/tools/registry.go
func RegisterAllTools() *ToolRegistry {
    r := NewToolRegistry()

    // Neuro-Inspired Systems (13 tools)
    r.RegisterCategory("neuro", []Tool{
        NewTool("neuro_auditory_listen", "Listen to auditory cortex events", ...),
        NewTool("neuro_thalamus_route", "Route sensory input via thalamus", ...),
        NewTool("neuro_memory_consolidate", "Consolidate threat patterns in memory", ...),
        // ... 10 more neuro tools
    })

    // Offensive Security (7 tools)
    r.RegisterCategory("offensive", []Tool{
        NewTool("offensive_c2_launch", "Launch C2 infrastructure", ...),
        NewTool("offensive_malware_analyze", "Analyze malware sample", ...),
        // ... 5 more offensive tools
    })

    // Behavioral Analysis (5 tools)
    r.RegisterCategory("behavior", []Tool{
        NewTool("behavior_analyze_user", "Analyze user behavior patterns", ...),
        NewTool("behavior_detect_anomaly", "Detect behavioral anomalies", ...),
        // ... 3 more behavior tools
    })

    // ... Continue for all 90+ services

    return r
}
```

### 7.3 Config Management com Hierarchical Loading

Implementar padrão de config em camadas (Anthropic style):

```
Global:    ~/.vcli/config.yaml
Project:   /project/.vcli/config.yaml
Local:     /project/.vcli/local.yaml (.gitignored)
Env Vars:  VCLI_*
CLI Flags: --server, --backend, etc.

Precedence: CLI Flags > Env Vars > Local > Project > Global > Defaults
```

---

## 8. ✅ CHECKLIST DE IMPLEMENTAÇÃO

### FASE 0 Completions:

- [x] Pesquisar documentação Anthropic
- [x] Extrair CLI design patterns
- [x] Extrair multi-agent patterns
- [x] Extrair Constitutional AI principles
- [x] Extrair tool use optimization
- [x] Extrair production best practices
- [x] Extrair prompt engineering templates
- [ ] **Aplicar patterns ao código vcli-go** (próximos passos)

### Próximas Ações (SHELL-1 a SHELL-10):

Quando implementar novos comandos, SEMPRE usar:

1. ✅ **Tool Schema Pattern**: Definir schema completo com enums, descriptions, examples
2. ✅ **Parallel Execution**: Executar tools independentes em paralelo
3. ✅ **Circuit Breaker**: Adicionar fallback e retry logic
4. ✅ **OpenTelemetry**: Trace todas tool invocations
5. ✅ **Constitutional Check**: Para decisões críticas, aplicar Constitutional AI
6. ✅ **Orchestrator-Worker**: Para tasks complexas, usar subagents
7. ✅ **Memory Management**: Checkpoint antes de contextos grandes
8. ✅ **Artifact Storage**: Retornar referencias, não conteúdo completo

---

## 9. 📊 MÉTRICAS DE SUCESSO

Para validar que aplicamos Anthropic patterns corretamente:

### Qualidade de Código (DOUTRINA):
- [ ] LEI < 1.0 (Lazy Execution Index)
- [ ] FPC ≥ 80% (First-Pass Correctness)
- [ ] CRS ≥ 95% (Constitutional Rule Satisfaction)

### Performance (Anthropic Multi-Agent):
- [ ] Parallel tool execution reduz tempo em 50%+
- [ ] Multi-agent research 90% mais rápido que single-agent
- [ ] Context management evita token bloat

### User Experience (Claude Code):
- [ ] VCLI.md auto-loading funcional
- [ ] Slash commands disponíveis e úteis
- [ ] Extended thinking mode para tasks complexas
- [ ] Permission system balanceado (não invasivo, mas seguro)

### Production Readiness (Anthropic Deployment):
- [ ] Circuit breakers previnem cascade failures
- [ ] Retry logic com backoff and jitter
- [ ] OpenTelemetry traces para todas operações
- [ ] Rate limiting protege backends

---

## 🎯 CONCLUSÃO

Anthropic fornece **patterns comprovados** que devemos seguir:

1. **CLI**: Low-level, flexible, file-based config, permission system
2. **Agents**: Orchestrator-worker, artifacts, memory management, parallelization
3. **Constitutional AI**: Two-phase (critique + revision), chain-of-thought, transparency
4. **Tools**: Schema-driven, parallel execution, context efficiency
5. **Production**: Circuit breakers, retry, tracing, rate limiting

**Próximo Passo**: Aplicar estes patterns enquanto implementamos SHELL-1 (Neuro Systems) e FASE 1.2 (Config Management).

**Referências**:
- https://www.anthropic.com/engineering/claude-code-best-practices
- https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback

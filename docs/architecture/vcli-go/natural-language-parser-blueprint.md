# 🧠 vCLI-Go Natural Language Parser Blueprint

**MAXIMUS Session | Day 75 | Focus: NLP Command Parser**  
**Doutrina ✓ | NO MOCK | NO PLACEHOLDER | PRODUCTION-READY**

---

## 🎯 Vision Statement

Transform vcli-go into a **truly conversational CLI** that understands natural language with the same sophistication as GitHub Copilot CLI. Users speak their intent naturally ("mostra os pods do namespace default que tão com problema") and vcli-go intelligently translates to precise commands.

### Success Criteria
- ✅ Parse arbitrary natural language input with 95%+ accuracy
- ✅ Support Portuguese and English seamlessly
- ✅ Handle typos, colloquialisms, and ambiguity gracefully
- ✅ Provide intelligent clarifications when ambiguous
- ✅ Learn from user patterns (feedback loop)
- ✅ Zero latency degradation (< 50ms parsing overhead)
- ✅ 100% type-safe Go implementation
- ✅ Comprehensive test coverage (≥ 90%)

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    Natural Language Parser                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────┐ │
│  │  Tokenizer   │─────▶│  Intent      │─────▶│  Command    │ │
│  │  Normalizer  │      │  Classifier  │      │  Generator  │ │
│  └──────────────┘      └──────────────┘      └─────────────┘ │
│         │                      │                      │        │
│         ▼                      ▼                      ▼        │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────┐ │
│  │  Entity      │      │  Context     │      │  Validator  │ │
│  │  Extractor   │      │  Manager     │      │  Suggester  │ │
│  └──────────────┘      └──────────────┘      └─────────────┘ │
│         │                      │                      │        │
│         └──────────────────────┴──────────────────────┘        │
│                                │                                │
│                         ┌──────▼──────┐                        │
│                         │  Learning   │                        │
│                         │  Engine     │                        │
│                         └─────────────┘                        │
└────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Breakdown

### 1. **Tokenizer & Normalizer** (`internal/nlp/tokenizer`)

**Purpose**: Convert raw natural language input into normalized tokens.

**Capabilities**:
- Multi-language support (PT-BR, EN)
- Typo correction using Levenshtein distance
- Slang/colloquialism normalization
- Stop word removal (configurable)
- Stemming/lemmatization

**Example**:
```
Input:  "mostra os pods do namespace default que tão com problema"
Output: [VERB:show, NOUN:pods, PREP:in, NOUN:namespace, IDENTIFIER:default, 
         FILTER:status, CONDITION:problem]
```

**Implementation**:
```go
type Token struct {
    Raw        string
    Normalized string
    Type       TokenType  // VERB, NOUN, IDENTIFIER, FILTER, etc.
    Language   Language   // PT_BR, EN
    Confidence float64
}

type Tokenizer interface {
    Tokenize(input string) ([]Token, error)
    Normalize(tokens []Token) []Token
    CorrectTypos(tokens []Token) []Token
}
```

---

### 2. **Intent Classifier** (`internal/nlp/intent`)

**Purpose**: Determine user's primary intent from tokenized input.

**Intent Categories**:
- `QUERY` - Retrieve information (list, get, show, describe)
- `ACTION` - Execute operation (create, delete, apply, scale)
- `INVESTIGATE` - Analyze/diagnose (investigate, analyze, debug)
- `ORCHESTRATE` - Workflow execution (run, execute, start)
- `NAVIGATE` - UI navigation (open, launch, switch)
- `CONFIGURE` - Settings management (set, configure, enable)
- `HELP` - Request assistance (help, explain, how)

**Implementation**:
```go
type Intent struct {
    Category   IntentCategory
    Verb       string           // Primary action verb
    Target     string           // Primary target (pods, deployments, etc.)
    Modifiers  []Modifier       // Filters, flags, options
    Confidence float64
}

type IntentClassifier interface {
    Classify(tokens []Token) (*Intent, error)
    GetAlternatives(tokens []Token) ([]*Intent, error) // Ambiguity handling
}
```

**Classification Strategy**:
1. **Rule-based patterns** for common structures
2. **Similarity matching** against known command patterns
3. **Context-aware disambiguation** using conversation history
4. **Confidence scoring** to request clarification when < 0.75

---

### 3. **Entity Extractor** (`internal/nlp/entities`)

**Purpose**: Extract structured entities from natural language.

**Entity Types**:
- **K8s Resources**: pods, deployments, services, namespaces
- **Identifiers**: names, labels, selectors
- **Filters**: status conditions, time ranges, metrics
- **Values**: numbers, strings, booleans
- **Workflows**: offensive, defensive, monitoring operations

**Example**:
```
Input:  "scale deployment nginx to 5 replicas in prod namespace"
Entities:
  - Resource: deployment
  - Name: nginx
  - Count: 5
  - Namespace: prod
```

**Implementation**:
```go
type Entity struct {
    Type       EntityType
    Value      string
    Normalized string
    Metadata   map[string]interface{}
    Span       [2]int  // Start/end position in original input
}

type EntityExtractor interface {
    Extract(tokens []Token, intent *Intent) ([]Entity, error)
    ResolveAmbiguity(entities []Entity, context *Context) ([]Entity, error)
}
```

---

### 4. **Context Manager** (`internal/nlp/context`)

**Purpose**: Maintain conversational context and state.

**Context Tracking**:
- Last N commands executed
- Current namespace/context
- User preferences and patterns
- Clarification history
- Pending confirmations

**Implementation**:
```go
type Context struct {
    SessionID       string
    History         []HistoryEntry
    CurrentResource string
    CurrentNS       string
    Preferences     UserPreferences
    LastIntent      *Intent
    PendingAction   *PendingAction
}

type ContextManager interface {
    Get(sessionID string) (*Context, error)
    Update(sessionID string, update ContextUpdate) error
    ResolveReference(ref string, ctx *Context) (string, error) // "it", "that", "same"
}
```

---

### 5. **Command Generator** (`internal/nlp/generator`)

**Purpose**: Generate executable vcli commands from parsed intent.

**Generation Pipeline**:
1. Map intent to command structure
2. Populate arguments from entities
3. Apply context-based defaults
4. Add required flags/options
5. Validate against command schema

**Example**:
```
Intent:   QUERY pods with filter status=error in namespace=default
Command:  k8s get pods -n default --field-selector=status.phase!=Running
```

**Implementation**:
```go
type Command struct {
    Path      []string          // ["k8s", "get", "pods"]
    Flags     map[string]string
    Args      []string
    PipeChain []Command         // For complex pipelines
    Confidence float64
}

type CommandGenerator interface {
    Generate(intent *Intent, entities []Entity, ctx *Context) (*Command, error)
    GetAlternatives(intent *Intent) ([]Command, error)
    Validate(cmd *Command) error
}
```

---

### 6. **Validator & Suggester** (`internal/nlp/validator`)

**Purpose**: Validate generated commands and suggest corrections.

**Validation Checks**:
- Command syntax correctness
- Required arguments present
- Flag compatibility
- Resource existence (when possible)
- Permission viability

**Suggestion Types**:
- Did you mean? (typo correction)
- Missing required flags
- Alternative approaches
- Related commands

**Implementation**:
```go
type ValidationResult struct {
    Valid       bool
    Errors      []ValidationError
    Warnings    []ValidationWarning
    Suggestions []CommandSuggestion
}

type Validator interface {
    Validate(cmd *Command, ctx *Context) (*ValidationResult, error)
    Suggest(cmd *Command, validationResult *ValidationResult) ([]Command, error)
}
```

---

### 7. **Learning Engine** (`internal/nlp/learning`)

**Purpose**: Learn from user interactions to improve accuracy.

**Learning Mechanisms**:
- **Explicit feedback**: User confirms/corrects interpretations
- **Implicit feedback**: Command execution success/failure
- **Pattern mining**: Identify common phrasings
- **Personalization**: Adapt to individual user styles

**Storage**:
```go
type LearningData struct {
    UserID           string
    PatternFrequency map[string]int        // NL pattern → frequency
    IntentMapping    map[string]string     // NL phrase → Intent
    EntityAliases    map[string]string     // User aliases → canonical names
    FeedbackLog      []FeedbackEntry
}

type LearningEngine interface {
    Learn(input string, intent *Intent, feedback Feedback) error
    GetPatterns(userID string) ([]Pattern, error)
    AdaptClassifier(userID string) error
}
```

---

## 🗂️ File Structure

```
vcli-go/
├── internal/
│   └── nlp/
│       ├── nlp.go                    # Main NLP interface
│       ├── tokenizer/
│       │   ├── tokenizer.go          # Tokenization logic
│       │   ├── normalizer.go         # Text normalization
│       │   ├── typo_corrector.go     # Levenshtein-based correction
│       │   └── tokenizer_test.go
│       ├── intent/
│       │   ├── classifier.go         # Intent classification
│       │   ├── patterns.go           # Rule-based patterns
│       │   ├── similarity.go         # Similarity scoring
│       │   └── classifier_test.go
│       ├── entities/
│       │   ├── extractor.go          # Entity extraction
│       │   ├── k8s_entities.go       # Kubernetes-specific
│       │   ├── workflow_entities.go  # Workflow-specific
│       │   └── extractor_test.go
│       ├── context/
│       │   ├── manager.go            # Context management
│       │   ├── history.go            # Command history
│       │   ├── resolver.go           # Reference resolution
│       │   └── manager_test.go
│       ├── generator/
│       │   ├── generator.go          # Command generation
│       │   ├── k8s_generator.go      # K8s command generation
│       │   ├── workflow_generator.go # Workflow generation
│       │   └── generator_test.go
│       ├── validator/
│       │   ├── validator.go          # Command validation
│       │   ├── suggester.go          # Smart suggestions
│       │   └── validator_test.go
│       └── learning/
│           ├── engine.go             # Learning engine
│           ├── storage.go            # Pattern storage
│           ├── feedback.go           # Feedback processing
│           └── engine_test.go
├── internal/shell/
│   ├── nlp_executor.go               # NLP-aware executor
│   └── nlp_mode.go                   # NLP mode handler
└── pkg/
    └── nlp/
        └── types.go                  # Public NLP types
```

---

## 🎨 User Experience Flow

### Example 1: Simple Query
```
User:  "mostra os pods com problema"
vCLI:  
  🧠 Understood: Show pods with issues
  📋 Executing: k8s get pods --field-selector=status.phase!=Running
  
  [Output: pods list]
```

### Example 2: Ambiguous Intent
```
User:  "escala nginx"
vCLI:  
  🤔 Clarification needed:
  
  Did you mean:
  1. Scale deployment/nginx (current: 3 replicas)
  2. Scale statefulset/nginx (current: 2 replicas)
  
  Type 1, 2, or clarify further ›
```

### Example 3: Learning from Feedback
```
User:  "pods quebrados no prod"
vCLI:  
  🧠 Understood: Show broken pods in prod namespace
  📋 Executing: k8s get pods -n prod --field-selector=status.phase!=Running
  
  [Output: pods list]
  
  👍 Was this correct? [y/n/edit] › y
  
  ✅ Learned! Will remember "quebrados" = error/failed status
```

### Example 4: Context Awareness
```
User:  "mostra os pods do default"
vCLI:  [shows pods]

User:  "agora escala o primeiro pra 5"
vCLI:  
  🧠 Understood: Scale first pod from previous list to 5 replicas
  📋 Executing: k8s scale deployment/nginx -n default --replicas=5
```

---

## 🔧 Implementation Strategy

### Phase 1: Foundation (Week 1-2)
**Goal**: Core NLP infrastructure

**Deliverables**:
- [ ] Tokenizer with PT/EN support
- [ ] Basic intent classifier (rule-based)
- [ ] Entity extractor for K8s resources
- [ ] Context manager skeleton
- [ ] Integration with shell executor

**Tests**:
- Unit tests for each component (≥ 90% coverage)
- Integration test: "mostra pods" → "k8s get pods"

---

### Phase 2: Intelligence (Week 3-4)
**Goal**: Advanced understanding

**Deliverables**:
- [ ] Typo correction
- [ ] Similarity-based intent matching
- [ ] Ambiguity detection & clarification UI
- [ ] Command generator for all vcli commands
- [ ] Validator with smart suggestions

**Tests**:
- Typo handling: "posd" → "pods"
- Ambiguity: "scale nginx" → clarification prompt
- Complex commands: "show failed pods in prod namespace last 1h"

---

### Phase 3: Learning (Week 5-6)
**Goal**: Adaptive intelligence

**Deliverables**:
- [ ] Learning engine with BadgerDB storage
- [ ] Feedback collection UI
- [ ] Pattern mining from history
- [ ] User-specific adaptations
- [ ] Confidence scoring refinement

**Tests**:
- Learning: User says "quebrado" → remembers as "failed"
- Personalization: User's common patterns prioritized
- Confidence: Low confidence triggers clarification

---

### Phase 4: Polish (Week 7-8)
**Goal**: Production readiness

**Deliverables**:
- [ ] Performance optimization (< 50ms)
- [ ] Comprehensive error handling
- [ ] Documentation & examples
- [ ] Tutorial mode
- [ ] Metrics & telemetry

**Tests**:
- Performance: 10k parses < 500ms total
- Edge cases: empty input, very long input, garbage input
- Stress test: concurrent parsing

---

## 📊 Success Metrics

### Quantitative
- **Accuracy**: ≥ 95% correct intent classification
- **Latency**: < 50ms parsing overhead
- **Coverage**: Support 100% of vcli commands
- **Test Coverage**: ≥ 90%

### Qualitative
- **User Satisfaction**: "Feels like talking to a human"
- **Learning Curve**: New users productive in < 5 minutes
- **Error Recovery**: Graceful handling of all invalid inputs
- **Confidence**: Users trust the parser's interpretations

---

## 🔬 Testing Strategy

### 1. Unit Tests
```go
// tokenizer_test.go
func TestTokenizer_Portuguese(t *testing.T) {
    input := "mostra os pods com problema"
    tokens, err := tokenizer.Tokenize(input)
    
    require.NoError(t, err)
    assert.Equal(t, "show", tokens[0].Normalized)
    assert.Equal(t, TokenType_VERB, tokens[0].Type)
}

// classifier_test.go
func TestClassifier_QueryIntent(t *testing.T) {
    tokens := []Token{
        {Normalized: "show", Type: TokenType_VERB},
        {Normalized: "pods", Type: TokenType_NOUN},
    }
    
    intent, err := classifier.Classify(tokens)
    require.NoError(t, err)
    assert.Equal(t, IntentCategory_QUERY, intent.Category)
}
```

### 2. Integration Tests
```go
func TestNLP_EndToEnd_SimpleQuery(t *testing.T) {
    nlp := NewNLP()
    cmd, err := nlp.Parse("mostra os pods")
    
    require.NoError(t, err)
    assert.Equal(t, []string{"k8s", "get", "pods"}, cmd.Path)
}
```

### 3. Golden Tests
Store expected outputs for regression testing:
```
testdata/
├── simple_queries.golden
├── complex_filters.golden
├── ambiguous_inputs.golden
└── typos.golden
```

---

## 🚀 Quick Start Implementation

### Step 1: Bootstrap Package
```bash
mkdir -p internal/nlp/{tokenizer,intent,entities,context,generator,validator,learning}
```

### Step 2: Define Core Interface
```go
// internal/nlp/nlp.go
package nlp

type Parser interface {
    Parse(input string) (*ParseResult, error)
    ParseWithContext(input string, ctx *Context) (*ParseResult, error)
    Learn(input string, feedback Feedback) error
}

type ParseResult struct {
    Command      *Command
    Intent       *Intent
    Confidence   float64
    Alternatives []Command
    Clarification *ClarificationRequest
}
```

### Step 3: Implement Tokenizer (MVP)
Start with simple rule-based tokenization before adding sophistication.

### Step 4: Integrate with Shell
Modify `internal/shell/executor.go` to detect NL input and route to parser.

---

## 🎓 Research References

### NLP Techniques
- **Levenshtein Distance**: Typo correction
- **TF-IDF**: Pattern matching
- **Edit Distance**: Similarity scoring
- **Stemming/Lemmatization**: Text normalization

### Go Libraries (Evaluated)
- `github.com/kljensen/snowball` - Stemming
- `github.com/texttheater/golang-levenshtein` - Edit distance
- `github.com/ikawaha/kagome` - Tokenization (if needed)
- BadgerDB - Learning data storage

---

## 🛡️ Doutrina Compliance

### NO MOCK
- All parsing logic fully implemented
- No placeholder functions
- Real typo correction algorithms

### Quality-First
- 100% type safety with Go generics where appropriate
- Comprehensive docstrings
- Error handling at every layer
- Graceful degradation on low confidence

### Production-Ready
- Performance benchmarks
- Telemetry integration
- Backward compatibility (original command syntax still works)
- Feature flags for gradual rollout

---

## 📝 Example Patterns to Support

### Portuguese
```
"mostra os pods"                          → k8s get pods
"lista deployments do namespace prod"     → k8s get deployments -n prod
"escala nginx pra 5"                      → k8s scale deployment/nginx --replicas=5
"deleta o pod nginx-abc123"               → k8s delete pod nginx-abc123
"pods com problema"                       → k8s get pods --field-selector=status.phase!=Running
"logs do pod nginx últimas 100 linhas"   → k8s logs nginx --tail=100
```

### English
```
"show me the pods"                        → k8s get pods
"scale nginx to 5 replicas"               → k8s scale deployment/nginx --replicas=5
"delete the failing pods"                 → k8s delete pods --field-selector=status.phase=Failed
"run offensive workflow"                  → orchestrate offensive apt-simulation
"investigate suspicious activity"         → investigate
```

### Advanced
```
"mostra pods que não tão rodando no prod nos últimos 30min"
→ k8s get pods -n prod --field-selector=status.phase!=Running 
  (filtered by time if supported)

"escala todos os deployments com label app=api pra 3"
→ k8s scale deployments -l app=api --replicas=3
```

---

## 🎯 Success Declaration

This parser will be COMPLETE when:

1. ✅ User can describe intent naturally in PT or EN
2. ✅ Parser generates correct command ≥95% of time
3. ✅ Ambiguity is detected and clarification requested
4. ✅ Parser learns from feedback
5. ✅ Performance impact negligible (< 50ms)
6. ✅ Test coverage ≥ 90%
7. ✅ Documentation complete with examples
8. ✅ Integration with existing shell seamless

---

**Blueprint Status**: COMPLETE  
**Ready for Implementation**: YES  
**Estimated Effort**: 8 weeks (4 sprints)  
**Risk Level**: MEDIUM (new domain, but well-architected)  

**Next Steps**: Create detailed roadmap → Begin Phase 1 implementation

---

*"The best interface is the one that understands you."*  
*— MAXIMUS Design Philosophy*

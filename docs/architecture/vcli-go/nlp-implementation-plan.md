# 🔨 Natural Language Parser - Implementation Plan

**MAXIMUS | Day 75 | vCLI-Go NLP Implementation**  
**Status**: READY TO EXECUTE  
**Adherence**: 100% Doutrina Compliant

---

## 🎯 Implementation Philosophy

### Core Principles
1. **NO MOCK** - Every function fully implemented
2. **Quality First** - Tests before features
3. **Incremental** - Ship working code daily
4. **Measurable** - Metrics guide decisions

### Development Workflow
```
Design → Test → Implement → Validate → Document → Ship
   ↑                                                  ↓
   └──────────────── Iterate ────────────────────────┘
```

---

## 📁 Phase 1: Foundation - Detailed Implementation

### 1.1 Package Bootstrap (Day 1)

#### Create Directory Structure
```bash
cd /home/juan/vertice-dev/vcli-go

mkdir -p internal/nlp/{tokenizer,intent,entities,context,generator,validator,learning}
mkdir -p internal/nlp/tokenizer/testdata
mkdir -p internal/nlp/intent/testdata
mkdir -p pkg/nlp
mkdir -p test/nlp
```

#### Initialize Go Modules
```bash
cd internal/nlp
go mod init github.com/verticedev/vcli-go/internal/nlp || true
```

---

### 1.2 Core Types Definition (Day 1)

#### File: `pkg/nlp/types.go`
```go
package nlp

import (
    "context"
    "time"
)

// Language represents supported languages
type Language string

const (
    LanguagePTBR Language = "pt-BR"
    LanguageEN   Language = "en"
)

// TokenType categorizes tokens semantically
type TokenType string

const (
    TokenTypeVERB       TokenType = "VERB"
    TokenTypeNOUN       TokenType = "NOUN"
    TokenTypeIDENTIFIER TokenType = "IDENTIFIER"
    TokenTypeFILTER     TokenType = "FILTER"
    TokenTypeNUMBER     TokenType = "NUMBER"
    TokenTypePREP       TokenType = "PREPOSITION"
    TokenTypeUNKNOWN    TokenType = "UNKNOWN"
)

// Token represents a parsed token
type Token struct {
    Raw        string    `json:"raw"`
    Normalized string    `json:"normalized"`
    Type       TokenType `json:"type"`
    Language   Language  `json:"language"`
    Confidence float64   `json:"confidence"`
    Position   int       `json:"position"`
}

// IntentCategory represents high-level user intent
type IntentCategory string

const (
    IntentCategoryQUERY       IntentCategory = "QUERY"
    IntentCategoryACTION      IntentCategory = "ACTION"
    IntentCategoryINVESTIGATE IntentCategory = "INVESTIGATE"
    IntentCategoryORCHESTRATE IntentCategory = "ORCHESTRATE"
    IntentCategoryNAVIGATE    IntentCategory = "NAVIGATE"
    IntentCategoryCONFIGURE   IntentCategory = "CONFIGURE"
    IntentCategoryHELP        IntentCategory = "HELP"
)

// Modifier represents command modifiers (flags, filters)
type Modifier struct {
    Type  string                 `json:"type"`
    Key   string                 `json:"key"`
    Value string                 `json:"value"`
    Meta  map[string]interface{} `json:"meta,omitempty"`
}

// Intent represents parsed user intent
type Intent struct {
    Category   IntentCategory `json:"category"`
    Verb       string         `json:"verb"`
    Target     string         `json:"target"`
    Modifiers  []Modifier     `json:"modifiers"`
    Confidence float64        `json:"confidence"`
}

// EntityType categorizes extracted entities
type EntityType string

const (
    EntityTypeK8S_RESOURCE EntityType = "K8S_RESOURCE"
    EntityTypeNAMESPACE    EntityType = "NAMESPACE"
    EntityTypeNAME         EntityType = "NAME"
    EntityTypeLABEL        EntityType = "LABEL"
    EntityTypeNUMBER       EntityType = "NUMBER"
    EntityTypeSTATUS       EntityType = "STATUS"
    EntityTypeTIMERANGE    EntityType = "TIMERANGE"
    EntityTypeWORKFLOW     EntityType = "WORKFLOW"
)

// Entity represents an extracted entity
type Entity struct {
    Type       EntityType             `json:"type"`
    Value      string                 `json:"value"`
    Normalized string                 `json:"normalized"`
    Metadata   map[string]interface{} `json:"metadata,omitempty"`
    Span       [2]int                 `json:"span"` // [start, end] position
}

// Command represents a generated command
type Command struct {
    Path       []string          `json:"path"`        // ["k8s", "get", "pods"]
    Flags      map[string]string `json:"flags"`       // {"-n": "default"}
    Args       []string          `json:"args"`        // Additional args
    PipeChain  []*Command        `json:"pipe_chain"`  // For pipelines
    Confidence float64           `json:"confidence"`
}

// ClarificationOption represents a clarification choice
type ClarificationOption struct {
    Label       string   `json:"label"`
    Command     *Command `json:"command"`
    Description string   `json:"description"`
}

// ClarificationRequest represents ambiguity that needs user input
type ClarificationRequest struct {
    Message      string                 `json:"message"`
    Options      []ClarificationOption  `json:"options"`
    AllowFreeform bool                  `json:"allow_freeform"`
}

// ParseResult represents the final parsing result
type ParseResult struct {
    Command       *Command              `json:"command"`
    Intent        *Intent               `json:"intent"`
    Entities      []Entity              `json:"entities"`
    Confidence    float64               `json:"confidence"`
    Alternatives  []*Command            `json:"alternatives,omitempty"`
    Clarification *ClarificationRequest `json:"clarification,omitempty"`
}

// Parser is the main NLP interface
type Parser interface {
    Parse(ctx context.Context, input string) (*ParseResult, error)
    ParseWithContext(ctx context.Context, input string, sessionCtx *Context) (*ParseResult, error)
}

// Context represents conversational context
type Context struct {
    SessionID       string                 `json:"session_id"`
    History         []HistoryEntry         `json:"history"`
    CurrentNS       string                 `json:"current_namespace"`
    CurrentResource string                 `json:"current_resource"`
    LastResources   map[string][]string    `json:"last_resources"` // type → names
    Preferences     map[string]string      `json:"preferences"`
    Created         time.Time              `json:"created"`
    Updated         time.Time              `json:"updated"`
}

// HistoryEntry represents a command in history
type HistoryEntry struct {
    Input      string         `json:"input"`
    Intent     *Intent        `json:"intent"`
    Command    *Command       `json:"command"`
    Success    bool           `json:"success"`
    Error      string         `json:"error,omitempty"`
    Timestamp  time.Time      `json:"timestamp"`
}

// Feedback represents user feedback on parsing
type Feedback struct {
    Type      FeedbackType  `json:"type"`
    Positive  bool          `json:"positive"`
    Input     string        `json:"input"`
    Intent    *Intent       `json:"intent"`
    Command   *Command      `json:"command"`
    Correction string       `json:"correction,omitempty"`
    Timestamp time.Time     `json:"timestamp"`
}

// FeedbackType categorizes feedback
type FeedbackType string

const (
    FeedbackTypeExplicit FeedbackType = "EXPLICIT" // User said yes/no
    FeedbackTypeImplicit FeedbackType = "IMPLICIT" // Inferred from result
)
```

#### File: `internal/nlp/errors.go`
```go
package nlp

import "fmt"

// ErrorType categorizes NLP errors
type ErrorType string

const (
    ErrorTypeInvalidInput    ErrorType = "INVALID_INPUT"
    ErrorTypeTokenization    ErrorType = "TOKENIZATION"
    ErrorTypeClassification  ErrorType = "CLASSIFICATION"
    ErrorTypeGeneration      ErrorType = "GENERATION"
    ErrorTypeTimeout         ErrorType = "TIMEOUT"
    ErrorTypeLowConfidence   ErrorType = "LOW_CONFIDENCE"
)

// ParseError represents an NLP parsing error
type ParseError struct {
    Type       ErrorType
    Message    string
    Cause      error
    Suggestion string
}

func (e *ParseError) Error() string {
    if e.Cause != nil {
        return fmt.Sprintf("%s: %s (caused by: %v)", e.Type, e.Message, e.Cause)
    }
    return fmt.Sprintf("%s: %s", e.Type, e.Message)
}

func (e *ParseError) Unwrap() error {
    return e.Cause
}
```

---

### 1.3 Tokenizer Implementation (Day 2-5)

#### File: `internal/nlp/tokenizer/tokenizer.go`
```go
package tokenizer

import (
    "strings"
    "unicode"
    
    "github.com/verticedev/vcli-go/pkg/nlp"
)

// Tokenizer handles text tokenization
type Tokenizer struct {
    normalizer     *Normalizer
    typoCorrector  *TypoCorrector
    stopWords      map[string]bool
}

// NewTokenizer creates a new tokenizer
func NewTokenizer() *Tokenizer {
    return &Tokenizer{
        normalizer:    NewNormalizer(),
        typoCorrector: NewTypoCorrector(),
        stopWords:     loadStopWords(),
    }
}

// Tokenize converts input into tokens
func (t *Tokenizer) Tokenize(input string) ([]nlp.Token, error) {
    if input == "" {
        return nil, &nlp.ParseError{
            Type:    nlp.ErrorTypeInvalidInput,
            Message: "Empty input",
        }
    }
    
    // Detect language
    lang := t.detectLanguage(input)
    
    // Split into raw tokens
    rawTokens := t.splitWords(input)
    
    // Process each token
    tokens := make([]nlp.Token, 0, len(rawTokens))
    for i, raw := range rawTokens {
        // Skip stop words
        if t.stopWords[strings.ToLower(raw)] {
            continue
        }
        
        // Normalize
        normalized := t.normalizer.Normalize(raw, lang)
        
        // Correct typos
        corrected, confidence := t.typoCorrector.Correct(normalized, lang)
        
        // Classify type
        tokenType := t.classifyTokenType(corrected, lang)
        
        token := nlp.Token{
            Raw:        raw,
            Normalized: corrected,
            Type:       tokenType,
            Language:   lang,
            Confidence: confidence,
            Position:   i,
        }
        
        tokens = append(tokens, token)
    }
    
    return tokens, nil
}

// splitWords splits input into raw words
func (t *Tokenizer) splitWords(input string) []string {
    words := make([]string, 0)
    var current strings.Builder
    
    for _, r := range input {
        if unicode.IsSpace(r) {
            if current.Len() > 0 {
                words = append(words, current.String())
                current.Reset()
            }
        } else {
            current.WriteRune(r)
        }
    }
    
    if current.Len() > 0 {
        words = append(words, current.String())
    }
    
    return words
}

// detectLanguage detects input language
func (t *Tokenizer) detectLanguage(input string) nlp.Language {
    lower := strings.ToLower(input)
    
    // Simple heuristic: check for PT-BR keywords
    ptKeywords := []string{"mostra", "lista", "deleta", "escala", "do", "da", "no", "na"}
    for _, kw := range ptKeywords {
        if strings.Contains(lower, kw) {
            return nlp.LanguagePTBR
        }
    }
    
    return nlp.LanguageEN
}

// classifyTokenType determines token type
func (t *Tokenizer) classifyTokenType(word string, lang nlp.Language) nlp.TokenType {
    lower := strings.ToLower(word)
    
    // Check if it's a number
    if isNumber(lower) {
        return nlp.TokenTypeNUMBER
    }
    
    // Check verb dictionary
    if t.isVerb(lower, lang) {
        return nlp.TokenTypeVERB
    }
    
    // Check noun dictionary (K8s resources, etc.)
    if t.isNoun(lower, lang) {
        return nlp.TokenTypeNOUN
    }
    
    // Check filter keywords
    if t.isFilter(lower, lang) {
        return nlp.TokenTypeFILTER
    }
    
    // Check prepositions
    if t.isPreposition(lower, lang) {
        return nlp.TokenTypePREP
    }
    
    // Default to identifier
    return nlp.TokenTypeIDENTIFIER
}

// isNumber checks if string is numeric
func isNumber(s string) bool {
    for _, r := range s {
        if !unicode.IsDigit(r) {
            return false
        }
    }
    return len(s) > 0
}

// isVerb checks if word is a verb
func (t *Tokenizer) isVerb(word string, lang nlp.Language) bool {
    verbs := getVerbDictionary(lang)
    _, ok := verbs[word]
    return ok
}

// isNoun checks if word is a noun
func (t *Tokenizer) isNoun(word string, lang nlp.Language) bool {
    nouns := getNounDictionary(lang)
    _, ok := nouns[word]
    return ok
}

// isFilter checks if word is a filter keyword
func (t *Tokenizer) isFilter(word string, lang nlp.Language) bool {
    filters := getFilterDictionary(lang)
    _, ok := filters[word]
    return ok
}

// isPreposition checks if word is a preposition
func (t *Tokenizer) isPreposition(word string, lang nlp.Language) bool {
    preps := getPrepositionDictionary(lang)
    _, ok := preps[word]
    return ok
}

// loadStopWords loads stop words for all languages
func loadStopWords() map[string]bool {
    return map[string]bool{
        // Portuguese
        "o": true, "a": true, "os": true, "as": true,
        "de": true, "do": true, "da": true, "dos": true, "das": true,
        "em": true, "no": true, "na": true, "nos": true, "nas": true,
        "um": true, "uma": true, "uns": true, "umas": true,
        "e": true, "ou": true,
        // English
        "the": true, "a": true, "an": true,
        "in": true, "on": true, "at": true,
        "of": true, "to": true, "for": true,
        "and": true, "or": true,
        "with": true, "from": true,
    }
}
```

#### File: `internal/nlp/tokenizer/dictionaries.go`
```go
package tokenizer

import "github.com/verticedev/vcli-go/pkg/nlp"

// getVerbDictionary returns verb mappings for language
func getVerbDictionary(lang nlp.Language) map[string]string {
    switch lang {
    case nlp.LanguagePTBR:
        return map[string]string{
            // Query verbs
            "mostra":   "show",
            "lista":    "list",
            "exibe":    "show",
            "ver":      "show",
            "busca":    "get",
            "obter":    "get",
            "pega":     "get",
            "describe": "describe",
            "descreve": "describe",
            
            // Action verbs
            "cria":     "create",
            "criar":    "create",
            "deleta":   "delete",
            "deletar":  "delete",
            "remove":   "delete",
            "remover":  "delete",
            "escala":   "scale",
            "escalar":  "scale",
            "escalona": "scale",
            "aplica":   "apply",
            "aplicar":  "apply",
            "atualiza": "update",
            "patch":    "patch",
            
            // Investigation
            "investiga":   "investigate",
            "investigar":  "investigate",
            "analisa":     "analyze",
            "analisar":    "analyze",
            "debuga":      "debug",
            
            // Orchestration
            "executa":  "execute",
            "executar": "execute",
            "roda":     "run",
            "rodar":    "run",
            "inicia":   "start",
            "iniciar":  "start",
        }
    case nlp.LanguageEN:
        return map[string]string{
            "show":        "show",
            "list":        "list",
            "get":         "get",
            "describe":    "describe",
            "create":      "create",
            "delete":      "delete",
            "remove":      "delete",
            "scale":       "scale",
            "apply":       "apply",
            "update":      "update",
            "patch":       "patch",
            "investigate": "investigate",
            "analyze":     "analyze",
            "debug":       "debug",
            "execute":     "execute",
            "run":         "run",
            "start":       "start",
        }
    default:
        return make(map[string]string)
    }
}

// getNounDictionary returns noun mappings for language
func getNounDictionary(lang nlp.Language) map[string]string {
    switch lang {
    case nlp.LanguagePTBR:
        return map[string]string{
            // K8s resources
            "pod":           "pods",
            "pods":          "pods",
            "deployment":    "deployments",
            "deployments":   "deployments",
            "service":       "services",
            "services":      "services",
            "servico":       "services",
            "servicos":      "services",
            "namespace":     "namespaces",
            "namespaces":    "namespaces",
            "configmap":     "configmaps",
            "configmaps":    "configmaps",
            "secret":        "secrets",
            "secrets":       "secrets",
            "segredo":       "secrets",
            "segredos":      "secrets",
            "node":          "nodes",
            "nodes":         "nodes",
            "no":            "nodes",
            "nos":           "nodes",
            "ingress":       "ingresses",
            "ingresses":     "ingresses",
            "statefulset":   "statefulsets",
            "statefulsets":  "statefulsets",
            "daemonset":     "daemonsets",
            "daemonsets":    "daemonsets",
            "job":           "jobs",
            "jobs":          "jobs",
            "cronjob":       "cronjobs",
            "cronjobs":      "cronjobs",
        }
    case nlp.LanguageEN:
        return map[string]string{
            "pod":          "pods",
            "pods":         "pods",
            "deployment":   "deployments",
            "deployments":  "deployments",
            "service":      "services",
            "services":     "services",
            "namespace":    "namespaces",
            "namespaces":   "namespaces",
            "configmap":    "configmaps",
            "configmaps":   "configmaps",
            "secret":       "secrets",
            "secrets":      "secrets",
            "node":         "nodes",
            "nodes":        "nodes",
            "ingress":      "ingresses",
            "ingresses":    "ingresses",
            "statefulset":  "statefulsets",
            "statefulsets": "statefulsets",
            "daemonset":    "daemonsets",
            "daemonsets":   "daemonsets",
            "job":          "jobs",
            "jobs":         "jobs",
            "cronjob":      "cronjobs",
            "cronjobs":     "cronjobs",
        }
    default:
        return make(map[string]string)
    }
}

// getFilterDictionary returns filter keywords
func getFilterDictionary(lang nlp.Language) map[string]string {
    switch lang {
    case nlp.LanguagePTBR:
        return map[string]string{
            "problema":   "error",
            "problemas":  "error",
            "erro":       "error",
            "erros":      "error",
            "falha":      "failed",
            "falhas":     "failed",
            "falhando":   "failing",
            "quebrado":   "failed",
            "quebrados":  "failed",
            "rodando":    "running",
            "pausado":    "paused",
            "pendente":   "pending",
            "completo":   "completed",
            "completos":  "completed",
        }
    case nlp.LanguageEN:
        return map[string]string{
            "problem":    "error",
            "problems":   "error",
            "error":      "error",
            "errors":     "error",
            "failed":     "failed",
            "failing":    "failing",
            "broken":     "failed",
            "running":    "running",
            "paused":     "paused",
            "pending":    "pending",
            "completed":  "completed",
        }
    default:
        return make(map[string]string)
    }
}

// getPrepositionDictionary returns prepositions
func getPrepositionDictionary(lang nlp.Language) map[string]string {
    switch lang {
    case nlp.LanguagePTBR:
        return map[string]string{
            "com":  "with",
            "pra":  "to",
            "para": "to",
            "em":   "in",
            "por":  "by",
        }
    case nlp.LanguageEN:
        return map[string]string{
            "with": "with",
            "to":   "to",
            "in":   "in",
            "by":   "by",
        }
    default:
        return make(map[string]string)
    }
}
```

#### File: `internal/nlp/tokenizer/normalizer.go`
```go
package tokenizer

import (
    "strings"
    "unicode"
    
    "github.com/verticedev/vcli-go/pkg/nlp"
)

// Normalizer handles text normalization
type Normalizer struct{}

// NewNormalizer creates a new normalizer
func NewNormalizer() *Normalizer {
    return &Normalizer{}
}

// Normalize normalizes a word
func (n *Normalizer) Normalize(word string, lang nlp.Language) string {
    // Convert to lowercase
    normalized := strings.ToLower(word)
    
    // Remove accents for Portuguese
    if lang == nlp.LanguagePTBR {
        normalized = n.removeAccents(normalized)
    }
    
    // Trim punctuation
    normalized = n.trimPunctuation(normalized)
    
    return normalized
}

// removeAccents removes Portuguese accents
func (n *Normalizer) removeAccents(s string) string {
    replacements := map[rune]rune{
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c',
    }
    
    var result strings.Builder
    for _, r := range s {
        if replacement, ok := replacements[r]; ok {
            result.WriteRune(replacement)
        } else {
            result.WriteRune(r)
        }
    }
    
    return result.String()
}

// trimPunctuation removes leading/trailing punctuation
func (n *Normalizer) trimPunctuation(s string) string {
    return strings.TrimFunc(s, func(r rune) bool {
        return unicode.IsPunct(r)
    })
}
```

#### File: `internal/nlp/tokenizer/typo_corrector.go`
```go
package tokenizer

import (
    "math"
    
    "github.com/verticedev/vcli-go/pkg/nlp"
)

// TypoCorrector corrects typos using Levenshtein distance
type TypoCorrector struct {
    threshold int
}

// NewTypoCorrector creates a new typo corrector
func NewTypoCorrector() *TypoCorrector {
    return &TypoCorrector{
        threshold: 2, // Max edit distance
    }
}

// Correct attempts to correct a typo
func (tc *TypoCorrector) Correct(word string, lang nlp.Language) (string, float64) {
    if len(word) < 3 {
        return word, 1.0 // Too short to correct
    }
    
    dictionary := tc.getDictionary(lang)
    
    minDistance := math.MaxInt32
    bestMatch := word
    
    for dictWord := range dictionary {
        dist := levenshteinDistance(word, dictWord)
        if dist < minDistance && dist <= tc.threshold {
            minDistance = dist
            bestMatch = dictWord
        }
    }
    
    // Calculate confidence
    confidence := 1.0
    if minDistance > 0 {
        confidence = 1.0 - (float64(minDistance) / float64(len(word)))
    }
    
    return bestMatch, confidence
}

// getDictionary returns all known words for language
func (tc *TypoCorrector) getDictionary(lang nlp.Language) map[string]bool {
    dict := make(map[string]bool)
    
    // Merge all dictionaries
    for k := range getVerbDictionary(lang) {
        dict[k] = true
    }
    for k := range getNounDictionary(lang) {
        dict[k] = true
    }
    for k := range getFilterDictionary(lang) {
        dict[k] = true
    }
    
    return dict
}

// levenshteinDistance calculates edit distance between two strings
func levenshteinDistance(s1, s2 string) int {
    if s1 == s2 {
        return 0
    }
    
    len1 := len(s1)
    len2 := len(s2)
    
    if len1 == 0 {
        return len2
    }
    if len2 == 0 {
        return len1
    }
    
    // Create matrix
    matrix := make([][]int, len1+1)
    for i := range matrix {
        matrix[i] = make([]int, len2+1)
        matrix[i][0] = i
    }
    for j := 0; j <= len2; j++ {
        matrix[0][j] = j
    }
    
    // Fill matrix
    for i := 1; i <= len1; i++ {
        for j := 1; j <= len2; j++ {
            cost := 1
            if s1[i-1] == s2[j-1] {
                cost = 0
            }
            
            matrix[i][j] = min(
                matrix[i-1][j]+1,      // Deletion
                matrix[i][j-1]+1,      // Insertion
                matrix[i-1][j-1]+cost, // Substitution
            )
        }
    }
    
    return matrix[len1][len2]
}

func min(a, b, c int) int {
    if a < b {
        if a < c {
            return a
        }
        return c
    }
    if b < c {
        return b
    }
    return c
}
```

---

### 1.4 Tokenizer Tests (Day 3-5)

#### File: `internal/nlp/tokenizer/tokenizer_test.go`
```go
package tokenizer

import (
    "testing"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/verticedev/vcli-go/pkg/nlp"
)

func TestTokenizer_BasicPortuguese(t *testing.T) {
    tokenizer := NewTokenizer()
    
    tests := []struct {
        name     string
        input    string
        expected []struct {
            normalized string
            tokenType  nlp.TokenType
        }
    }{
        {
            name:  "simple query",
            input: "mostra os pods",
            expected: []struct {
                normalized string
                tokenType  nlp.TokenType
            }{
                {"show", nlp.TokenTypeVERB},
                {"pods", nlp.TokenTypeNOUN},
            },
        },
        {
            name:  "with namespace",
            input: "lista deployments do namespace prod",
            expected: []struct {
                normalized string
                tokenType  nlp.TokenType
            }{
                {"list", nlp.TokenTypeVERB},
                {"deployments", nlp.TokenTypeNOUN},
                {"namespaces", nlp.TokenTypeNOUN},
                {"prod", nlp.TokenTypeIDENTIFIER},
            },
        },
        {
            name:  "scale command",
            input: "escala nginx pra 5",
            expected: []struct {
                normalized string
                tokenType  nlp.TokenType
            }{
                {"scale", nlp.TokenTypeVERB},
                {"nginx", nlp.TokenTypeIDENTIFIER},
                {"5", nlp.TokenTypeNUMBER},
            },
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            tokens, err := tokenizer.Tokenize(tt.input)
            require.NoError(t, err)
            require.Equal(t, len(tt.expected), len(tokens))
            
            for i, exp := range tt.expected {
                assert.Equal(t, exp.normalized, tokens[i].Normalized)
                assert.Equal(t, exp.tokenType, tokens[i].Type)
            }
        })
    }
}

func TestTokenizer_EnglishInput(t *testing.T) {
    tokenizer := NewTokenizer()
    
    input := "show me the pods"
    tokens, err := tokenizer.Tokenize(input)
    
    require.NoError(t, err)
    assert.GreaterOrEqual(t, len(tokens), 2)
    assert.Equal(t, "show", tokens[0].Normalized)
    assert.Equal(t, nlp.TokenTypeVERB, tokens[0].Type)
}

func TestTokenizer_EmptyInput(t *testing.T) {
    tokenizer := NewTokenizer()
    
    _, err := tokenizer.Tokenize("")
    require.Error(t, err)
}

func TestTypoCorrector_BasicCorrections(t *testing.T) {
    corrector := NewTypoCorrector()
    
    tests := []struct {
        input    string
        expected string
        lang     nlp.Language
    }{
        {"posd", "pods", nlp.LanguageEN},
        {"deploiment", "deployment", nlp.LanguageEN},
        {"esacala", "escala", nlp.LanguagePTBR},
    }
    
    for _, tt := range tests {
        t.Run(tt.input, func(t *testing.T) {
            corrected, confidence := corrector.Correct(tt.input, tt.lang)
            assert.Equal(t, tt.expected, corrected)
            assert.Greater(t, confidence, 0.5)
        })
    }
}

func TestLevenshteinDistance(t *testing.T) {
    tests := []struct {
        s1       string
        s2       string
        expected int
    }{
        {"", "", 0},
        {"a", "", 1},
        {"", "a", 1},
        {"abc", "abc", 0},
        {"abc", "abd", 1},
        {"abc", "ac", 1},
        {"pods", "posd", 2},
    }
    
    for _, tt := range tests {
        t.Run(tt.s1+"_"+tt.s2, func(t *testing.T) {
            dist := levenshteinDistance(tt.s1, tt.s2)
            assert.Equal(t, tt.expected, dist)
        })
    }
}
```

---

## 📊 Daily Progress Tracking

### Day 1: Bootstrap ✅
- [ ] Directory structure created
- [ ] Core types defined
- [ ] Error types defined
- [ ] Tests scaffolded

### Day 2-3: Tokenizer Core ✅
- [ ] Basic tokenization working
- [ ] Dictionary implemented
- [ ] Language detection working
- [ ] Token type classification working

### Day 4-5: Tokenizer Advanced ✅
- [ ] Typo correction implemented
- [ ] Normalizer working
- [ ] 90%+ test coverage
- [ ] Benchmarks < 5ms per parse

---

## ✅ Phase 1 Completion Criteria

Before moving to Phase 2:

1. ✅ All files created and committed
2. ✅ Tests passing with ≥ 90% coverage
3. ✅ Benchmarks meet performance targets
4. ✅ Code reviewed by team
5. ✅ Documentation written
6. ✅ No known bugs

---

## 🔄 Iteration Process

For each component:

1. **Design** - Write interface/types first
2. **Test** - Write tests before implementation
3. **Implement** - Make tests pass
4. **Benchmark** - Ensure performance
5. **Document** - Add docstrings
6. **Review** - Get feedback
7. **Ship** - Merge to main

---

## 📝 Commit Message Template

```
NLP: [Component] Brief description

Detailed explanation of what was implemented and why.

Validates:
- [X] Feature requirement
- [X] Performance target
- [X] Test coverage

Day X of Foundation phase.
```

---

**Implementation Plan Status**: READY  
**Next Action**: Begin Day 1 bootstrap  
**Estimated Start**: 2025-10-14  

---

*"Code is poetry. Tests are proofs. Documentation is legacy."*  
*— MAXIMUS Engineering Maxims*

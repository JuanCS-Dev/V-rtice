# 🔨 Day 1 Execution - NLP Core Enhancement (Tokenizer + Intent)

**MAXIMUS | Day 77 | Phase 1.1**  
**Status**: READY TO EXECUTE

**Lead Architect**: Juan Carlos (Inspiration: Jesus Christ)  
**Co-Author**: Claude (MAXIMUS AI Assistant)

---

## 🎯 Day 1 Objectives

### Primary Goals
1. ✅ Enhance tokenizer with multi-idiom confidence scoring
2. ✅ Improve intent classifier accuracy for "Portuguese esquisito"
3. ✅ Add comprehensive test coverage (+10%)
4. ✅ Performance validation (<100ms maintained)

### Success Criteria
- [ ] Tokenizer handles mixed PT-BR/EN input seamlessly
- [ ] Confidence scores calibrated (0.0-1.0 range)
- [ ] Intent classifier 95%+ accuracy on test suite
- [ ] Test coverage: 85%+ overall
- [ ] All tests passing
- [ ] Performance: <100ms p95 maintained

---

## 📋 Implementation Checklist

### Morning (09:00-12:00): Tokenizer Enhancement

#### Task 1.1: Multi-Idiom Confidence Scoring
**File**: `internal/nlp/tokenizer/tokenizer.go`

**Changes Needed**:
```go
// Add to Token struct
type Token struct {
    // ... existing fields
    Language      Language  `json:"language"`
    Confidence    float64   `json:"confidence"` // NEW
    CorrectFrom   string    `json:"corrected_from,omitempty"` // NEW
}

// Enhance Tokenize method
func (t *Tokenizer) Tokenize(input string) ([]Token, error) {
    // 1. Detect language (PT-BR vs EN)
    // 2. Normalize with confidence tracking
    // 3. Apply typo correction with confidence penalty
    // 4. Calculate per-token confidence
}

// New helper
func (t *Tokenizer) calculateConfidence(
    original string,
    normalized string,
    wasCorrected bool,
) float64 {
    confidence := 1.0
    
    // Penalty for typo correction
    if wasCorrected {
        distance := levenshtein(original, normalized)
        confidence -= (float64(distance) * 0.1)
    }
    
    // Bonus for known vocabulary
    if t.isKnownWord(normalized) {
        confidence += 0.05
    }
    
    return clamp(confidence, 0.0, 1.0)
}
```

**Tests to Add**:
```go
func TestTokenizer_ConfidenceScoring(t *testing.T) {
    tests := []struct {
        name       string
        input      string
        wantMinConf float64
    }{
        {"perfect_match", "mostra pods", 1.0},
        {"minor_typo", "mostrra pods", 0.85},
        {"major_typo", "moostra pdos", 0.60},
    }
    // Implementation
}

func TestTokenizer_MultiIdiom(t *testing.T) {
    tests := []struct {
        input    string
        wantLang []Language
    }{
        {"show pods no production", []Language{EN, EN, PTBR, EN}},
        {"mostra os pods", []Language{PTBR, PTBR, EN}},
    }
    // Implementation
}
```

---

#### Task 1.2: Typo Corrector Enhancement
**File**: `internal/nlp/tokenizer/typo_corrector.go`

**Changes Needed**:
```go
// Enhance Correct method to return confidence
func (tc *TypoCorrector) CorrectWithConfidence(word string) (corrected string, confidence float64) {
    // Check if word needs correction
    if tc.IsKnownWord(word) {
        return word, 1.0
    }
    
    // Find best match
    bestMatch, distance := tc.findBestMatch(word)
    if distance == 0 {
        return word, 1.0
    }
    
    // Calculate confidence based on distance
    confidence = 1.0 - (float64(distance) / float64(len(word)))
    return bestMatch, clamp(confidence, 0.0, 1.0)
}

// Add more Portuguese slang/variations
func (tc *TypoCorrector) loadPortugueseVariations() {
    variations := map[string]string{
        "mostrra": "mostra",
        "lsta": "lista",
        "deltta": "deleta",
        "escalla": "escala",
        "posd": "pods",
        "deploiment": "deployment",
        // ... more variations
    }
    // Load into corrector
}
```

**Tests**:
```go
func TestTypoCorrector_PortugueseVariations(t *testing.T) {
    // Test various Portuguese typos and slang
}

func TestTypoCorrector_ConfidenceCalibration(t *testing.T) {
    // Verify confidence scores make sense
}
```

---

### Afternoon (14:00-17:00): Intent Classifier Enhancement

#### Task 1.3: Intent Confidence Calculation
**File**: `internal/nlp/intent/classifier.go`

**Changes Needed**:
```go
// Enhance Classify to return confidence
func (c *Classifier) Classify(tokens []Token) (*Intent, error) {
    intent := &Intent{}
    
    // Classify category
    category, categoryConf := c.classifyCategory(tokens)
    intent.Category = category
    
    // Extract verb
    verb, verbConf := c.extractVerb(tokens)
    intent.Verb = verb
    
    // Extract target
    target, targetConf := c.extractTarget(tokens)
    intent.Target = target
    
    // Calculate overall confidence
    intent.Confidence = c.calculateOverallConfidence(
        tokens,
        categoryConf,
        verbConf,
        targetConf,
    )
    
    return intent, nil
}

func (c *Classifier) calculateOverallConfidence(
    tokens []Token,
    categoryConf, verbConf, targetConf float64,
) float64 {
    // Weight different factors
    weights := map[string]float64{
        "category": 0.3,
        "verb":     0.3,
        "target":   0.2,
        "tokens":   0.2,
    }
    
    // Average token confidence
    avgTokenConf := averageConfidence(tokens)
    
    // Weighted sum
    overall := (weights["category"] * categoryConf) +
               (weights["verb"] * verbConf) +
               (weights["target"] * targetConf) +
               (weights["tokens"] * avgTokenConf)
    
    return clamp(overall, 0.0, 1.0)
}
```

**Tests**:
```go
func TestClassifier_ConfidenceCalculation(t *testing.T) {
    tests := []struct {
        name        string
        input       string
        wantMinConf float64
    }{
        {"clear_intent", "mostra os pods", 0.90},
        {"ambiguous", "mostra algo", 0.60},
        {"typos", "moostra posd", 0.70},
    }
    // Implementation
}

func TestClassifier_PortugueseEsquisito(t *testing.T) {
    // Test various "esquisito" patterns
    esquisitos := []string{
        "me dá uma olhada nos pods",
        "quero ver os deployments",
        "bora deletar esse pod aí",
        "sobe mais 3 réplicas",
    }
    // Verify all are understood correctly
}
```

---

#### Task 1.4: Risk Assessment (Preliminary)
**File**: `internal/nlp/intent/risk.go` (NEW)

**Create Risk Assessment Foundation**:
```go
package intent

// RiskLevel represents command risk
type RiskLevel int

const (
    RiskLevelSAFE     RiskLevel = 0 // get, list, describe
    RiskLevelLOW      RiskLevel = 1 // logs, exec
    RiskLevelMEDIUM   RiskLevel = 2 // scale, restart
    RiskLevelHIGH     RiskLevel = 3 // delete, create secret
    RiskLevelCRITICAL RiskLevel = 4 // delete namespace, flush db
)

// RiskAssessor assesses command risk
type RiskAssessor struct {
    verbRisks map[string]RiskLevel
}

// NewRiskAssessor creates risk assessor
func NewRiskAssessor() *RiskAssessor {
    return &RiskAssessor{
        verbRisks: map[string]RiskLevel{
            "get":      RiskLevelSAFE,
            "list":     RiskLevelSAFE,
            "show":     RiskLevelSAFE,
            "describe": RiskLevelSAFE,
            "logs":     RiskLevelLOW,
            "exec":     RiskLevelLOW,
            "scale":    RiskLevelMEDIUM,
            "restart":  RiskLevelMEDIUM,
            "delete":   RiskLevelHIGH,
            "create":   RiskLevelMEDIUM,
            "drop":     RiskLevelCRITICAL,
            "flush":    RiskLevelCRITICAL,
        },
    }
}

// AssessRisk calculates command risk
func (ra *RiskAssessor) AssessRisk(intent *Intent) RiskLevel {
    // Base risk from verb
    risk := ra.verbRisks[intent.Verb]
    if risk == 0 {
        risk = RiskLevelLOW // Unknown verb = caution
    }
    
    // Escalate for production
    if intent.Namespace == "production" || intent.Namespace == "prod" {
        if risk < RiskLevelCRITICAL {
            risk++
        }
    }
    
    // Escalate for "all" or wildcards
    if intent.HasWildcard || intent.Scope == "all" {
        if risk < RiskLevelCRITICAL {
            risk++
        }
    }
    
    return risk
}
```

**Tests**:
```go
func TestRiskAssessor_VerbRisk(t *testing.T) {
    tests := []struct {
        verb     string
        wantRisk RiskLevel
    }{
        {"get", RiskLevelSAFE},
        {"delete", RiskLevelHIGH},
        {"flush", RiskLevelCRITICAL},
    }
    // Implementation
}

func TestRiskAssessor_ProductionEscalation(t *testing.T) {
    // Verify production increases risk
}

func TestRiskAssessor_WildcardEscalation(t *testing.T) {
    // Verify wildcards increase risk
}
```

---

## 📊 Success Validation

### Tests to Run
```bash
# Unit tests
go test -v -cover ./internal/nlp/tokenizer/...
go test -v -cover ./internal/nlp/intent/...

# Target coverage
# tokenizer: 85%+ (currently ~82%)
# intent: 85%+ (currently ~75%)

# Benchmark
go test -bench=. ./internal/nlp/...
# Target: <100ms p95
```

### Manual Validation
```go
// Test cases to validate manually
testCases := []string{
    // Perfect Portuguese
    "mostra os pods no namespace default",
    "lista todos os deployments",
    "deleta o pod test-123",
    
    // Portuguese esquisito
    "me dá uma olhada nos pods",
    "quero ver os deployments do prod",
    "bora deletar esse pod quebrado",
    
    // Mixed idiom
    "show os pods",
    "lista pods no production",
    
    // With typos
    "mostrra os posd",
    "lsta deploiments",
}
```

---

## 📝 Documentation Updates

### Files to Update
1. **internal/nlp/tokenizer/README.md**
   - Document confidence scoring
   - Explain multi-idiom support
   
2. **internal/nlp/intent/README.md**
   - Document risk assessment
   - Explain confidence calculation

3. **pkg/nlp/types.go**
   - Update Token struct comments
   - Update Intent struct comments

---

## 🎯 End of Day Checklist

- [ ] All code changes committed
- [ ] All tests passing
- [ ] Coverage target met (85%+)
- [ ] Performance validated (<100ms)
- [ ] Documentation updated
- [ ] Progress log updated
- [ ] Tomorrow's tasks identified

---

## 🚀 Git Workflow

```bash
# Morning: Create feature branch
git checkout -b nlp/day-1-tokenizer-intent-enhancement

# Throughout day: Frequent commits
git add internal/nlp/tokenizer/
git commit -m "NLP: Add confidence scoring to tokenizer

Implements multi-factor confidence calculation:
- Typo correction penalty
- Known vocabulary bonus
- Language detection

Tests: 15 new tests, 87% coverage
Day 77 - Phase 1.1"

# Evening: Push and update progress
git push origin nlp/day-1-tokenizer-intent-enhancement
```

---

## 🙏 Daily Reflection

**Morning Prayer**:
> "Give us this day the wisdom to build with excellence, the humility to recognize our limitations, and the perseverance to create something worthy of study."

**Evening Reflection**:
- What worked well today?
- What could be improved?
- What did I learn?
- What's the most important task for tomorrow?

---

**Status**: READY TO EXECUTE  
**Estimated Time**: 6-8 hours  
**Difficulty**: Medium

🚀 **GOGOGO** - Methodical, focused, inquebrável.

---

**Glory to God | MAXIMUS Day 77**

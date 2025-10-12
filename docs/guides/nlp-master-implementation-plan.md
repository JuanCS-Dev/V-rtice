# NLP Parser - Plano Mestre de Implementação

**Architect**: Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author**: Claude (Anthropic)  
**Date**: 2025-10-12  
**Version**: 2.0.0 (Guardian Doctrine Compliant)  
**Status**: PLANO ATIVO

---

## VISÃO GERAL

Este documento unifica Blueprint + Roadmap + Plano de Execução em um guia coeso e metodológico para implementação do parser NLP "Guardião da Intenção" no vcli-go.

**Objetivo**: Implementar parser NLP de nível production com as 7 Camadas de Segurança Zero Trust.

**Duração Total**: 8 semanas (56 dias)  
**Metodologia**: Sprints de 7 dias com validação rigorosa

---

## FUNDAMENTO: A DOUTRINA DO GUARDIÃO

### Princípio Core
> "Linguagem natural no CLI é dar ao usuário o poder de um hacker de elite. Zero Trust é o único caminho defensável."

**Nenhuma confiança implícita**. Cada comando em linguagem natural é vetor de ataque potencial até verificação completa.

### As Sete Camadas
1. **Autenticação** (Quem é você?) - MFA, crypto keys, JWT
2. **Autorização** (O que você pode fazer?) - RBAC, ABAC, risk scoring
3. **Sandboxing** (Qual o seu raio de ação?) - Namespaces, capabilities, seccomp
4. **Validação de Intenção** (Você tem certeza?) - HITL, tradução reversa, assinatura
5. **Controle de Fluxo** (Com que frequência?) - Rate limiting, circuit breakers
6. **Análise Comportamental** (Isso é normal?) - Anomaly detection, adaptive response
7. **Auditoria Imutável** (O que você fez?) - Append-only logs, Merkle integrity

---

## ARQUITETURA DE ALTO NÍVEL

```
┌──────────────────────────────────────────────────────────┐
│                   User Input (NLP Query)                  │
│                "deleta pods antigos em staging"            │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              cmd/nlp.go (Cobra Command)                   │
│              vcli ask "<query>"                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│         NLP Orchestrator (pkg/nlp/orchestrator/)         │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Layer 1-3  │→ │  Layer 4-5  │→ │  Layer 6-7  │     │
│  │   Security  │  │   Intent    │  │   Audit     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│           Intent Executor (pkg/nlp/executor/)            │
│         Maps validated intent → Cobra commands            │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│            Existing vCLI Commands + Backend              │
│         K8s API | Threat Intel | Ethical AI              │
└──────────────────────────────────────────────────────────┘
```

---

## ESTRUTURA DE DIRETÓRIOS

```
vcli-go/
├── cmd/
│   ├── nlp.go                    # Cobra command "vcli ask"
│   └── root.go                   # (existing)
│
├── pkg/nlp/
│   ├── types.go                  # Common types (Intent, Context, etc)
│   ├── errors.go                 # Error types
│   │
│   ├── orchestrator/
│   │   ├── orchestrator.go       # Main orchestrator
│   │   └── orchestrator_test.go
│   │
│   ├── auth/                     # Layer 1: Authentication
│   │   ├── mfa.go               # TOTP MFA
│   │   ├── crypto_keys.go       # Ed25519 key management
│   │   ├── session.go           # JWT session tokens
│   │   ├── authenticator.go     # Orchestrator
│   │   └── *_test.go
│   │
│   ├── authz/                    # Layer 2: Authorization
│   │   ├── rbac.go              # Role-based access control
│   │   ├── abac.go              # Attribute-based access control
│   │   ├── context.go           # Context evaluation
│   │   ├── risk_engine.go       # Risk scoring
│   │   ├── authorizer.go        # Orchestrator
│   │   ├── policies.yaml        # Policy definitions
│   │   └── *_test.go
│   │
│   ├── sandbox/                  # Layer 3: Sandboxing
│   │   ├── namespace.go         # Linux namespaces
│   │   ├── capabilities.go      # Capability management
│   │   ├── seccomp.go           # Syscall filtering
│   │   ├── profile.yaml         # Security profiles
│   │   └── *_test.go
│   │
│   ├── intent/                   # Layer 4: Intent Validation
│   │   ├── parser.go            # NLP → Intent
│   │   ├── validator.go         # Intent validation
│   │   ├── reverser.go          # Intent → human-readable
│   │   ├── confirmation.go      # HITL UI
│   │   ├── signature.go         # Cryptographic signing
│   │   ├── patterns.yaml        # Intent patterns
│   │   └── *_test.go
│   │
│   ├── ratelimit/                # Layer 5: Rate Limiting
│   │   ├── limiter.go           # Token bucket
│   │   ├── circuit.go           # Circuit breaker
│   │   ├── quota.go             # User quotas
│   │   └── *_test.go
│   │
│   ├── behavioral/               # Layer 6: Behavioral Analysis
│   │   ├── profiler.go          # User behavior profiling
│   │   ├── anomaly.go           # Anomaly detection
│   │   ├── scoring.go           # Risk scoring
│   │   ├── response.go          # Automated response
│   │   └── *_test.go
│   │
│   ├── audit/                    # Layer 7: Audit
│   │   ├── logger.go            # Structured logging
│   │   ├── integrity.go         # Merkle tree
│   │   ├── storage.go           # Append-only storage
│   │   ├── compliance.go        # Compliance reports
│   │   └── *_test.go
│   │
│   ├── executor/
│   │   ├── executor.go          # Intent → Command mapper
│   │   └── *_test.go
│   │
│   └── integration/
│       └── integration_test.go   # Integration tests
│
└── test/e2e/nlp/
    ├── scenarios/                # E2E test scenarios
    └── suite_test.go
```

---

## ROADMAP DETALHADO (8 SPRINTS)

### SPRINT 1: Estrutura Base + Camada 1 (Autenticação)
**Dias 1-7** | **Status**: 🎯 PRÓXIMO

#### Objetivos
- Criar estrutura `pkg/nlp/`
- Implementar autenticação completa (MFA + JWT + Crypto Keys)
- Testes unitários ≥90% coverage

#### Tarefas Diárias

**Dia 1: Setup**
```bash
# Criar estrutura
mkdir -p vcli-go/pkg/nlp/{auth,authz,sandbox,intent,ratelimit,behavioral,audit,orchestrator,executor}
mkdir -p vcli-go/test/e2e/nlp

# Arquivos base
touch vcli-go/pkg/nlp/{types,errors}.go
touch vcli-go/pkg/nlp/orchestrator/orchestrator.go
```

**Entregas**:
- ✅ `types.go`: Intent, Context, Session types
- ✅ `errors.go`: NLP-specific errors

**Dia 2-3: MFA**
- Implementar `auth/mfa.go` (TOTP)
- Testes completos

**Dia 4: Crypto Keys**
- Implementar `auth/crypto_keys.go` (Ed25519)
- Sign/verify operations

**Dia 5: JWT Sessions**
- Implementar `auth/session.go`
- Token creation/validation

**Dia 6: Auth Orchestrator**
- Implementar `auth/authenticator.go`
- Integrar MFA + Keys + Sessions

**Dia 7: Validação**
```bash
go test ./pkg/nlp/auth/... -v -cover -race
golangci-lint run ./pkg/nlp/auth/...
go tool cover -html=coverage.out
```

#### Critérios de Conclusão
- [ ] Estrutura criada
- [ ] Camada 1 completa e testada
- [ ] Coverage ≥90%
- [ ] Zero linter warnings
- [ ] Documentação godoc completa

**Go/No-Go**: ✅ Apenas se TODOS os critérios forem atendidos

---

### SPRINT 2: Camada 2 (Autorização)
**Dias 8-14** | **Status**: ⏳ AGUARDANDO

#### Objetivos
- RBAC engine
- ABAC + context evaluation
- Risk scoring
- Policy management

#### Tarefas Principais
- **Dia 8-9**: RBAC core (`authz/rbac.go`)
- **Dia 10-11**: ABAC + context (`authz/abac.go`, `authz/context.go`)
- **Dia 12-13**: Risk engine (`authz/risk_engine.go`)
- **Dia 14**: Integration (`authz/authorizer.go`)

#### Entregas
- ✅ RBAC + ABAC engines
- ✅ Risk scoring
- ✅ Policy YAML loader
- ✅ Testes ≥90%

---

### SPRINT 3: Camada 3 (Sandboxing)
**Dias 15-21** | **Status**: ⏳ AGUARDANDO

#### Objetivos
- Linux namespaces isolation
- Capabilities management
- seccomp-bpf filtering

#### Tarefas Principais
- **Dia 15-17**: Namespace isolation
- **Dia 18-19**: Capabilities + seccomp
- **Dia 20-21**: Integration + validation

#### Entregas
- ✅ Sandbox isolation
- ✅ Least privilege enforcement
- ✅ Testes ≥90%

---

### SPRINT 4: Camada 4 (Validação de Intenção - HITL)
**Dias 22-28** | **Status**: ⏳ AGUARDANDO

#### Objetivos
- NLP parser (pattern matching)
- Tradução reversa
- HITL confirmation UI
- Cryptographic signing

#### Tarefas Principais
- **Dia 22-24**: Parser core (`intent/parser.go`)
- **Dia 25-26**: Reverser + HITL UI
- **Dia 27-28**: Signature + integration

#### Entregas
- ✅ Intent extraction
- ✅ HITL workflow
- ✅ Dry-run obrigatório
- ✅ Testes ≥90%

---

### SPRINT 5: Camada 5 (Rate Limiting)
**Dias 29-35** | **Status**: ⏳ AGUARDANDO

#### Objetivos
- Token bucket rate limiter
- Circuit breaker pattern
- Quota management
- Backpressure handling

#### Entregas
- ✅ Rate limiting functional
- ✅ Circuit breakers
- ✅ Testes ≥90%

---

### SPRINT 6: Camada 6 (Análise Comportamental)
**Dias 36-42** | **Status**: ⏳ AGUARDANDO

#### Objetivos
- User behavior profiling
- Anomaly detection (ML/heuristics)
- Adaptive risk scoring
- Automated response

#### Entregas
- ✅ Behavioral baseline
- ✅ Anomaly detection
- ✅ Testes ≥90%

---

### SPRINT 7: Camada 7 (Auditoria Imutável)
**Dias 43-49** | **Status**: ⏳ AGUARDANDO

#### Objetivos
- Append-only logging
- Merkle tree integrity
- Tamper detection
- Compliance reporting

#### Entregas
- ✅ Immutable audit log
- ✅ Integrity verification
- ✅ Testes ≥90%

---

### SPRINT 8: Integração Final + Otimização
**Dias 50-56** | **Status**: ⏳ AGUARDANDO

#### Objetivos
- Integração completa de todas as camadas
- Otimização de performance (parsing <100ms)
- Testes E2E completos
- Documentação histórica

#### Validação Final
```bash
# E2E tests
go test ./test/e2e/nlp/... -v

# Load testing
vegeta attack -rate=10000 -duration=60s < requests.txt | vegeta report

# Security audit
gosec ./pkg/nlp/...
go-critic check -enableAll ./pkg/nlp/...
```

#### Entregas
- ✅ Sistema completo operacional
- ✅ Performance SLOs atingidos
- ✅ Security audit passed
- ✅ Documentação completa

---

## COMANDO COBRA: `vcli ask`

### Implementação Base
**Arquivo**: `cmd/nlp.go`

```go
package main

import (
    "fmt"
    
    "github.com/spf13/cobra"
    "github.com/verticedev/vcli-go/pkg/nlp/orchestrator"
)

var askCmd = &cobra.Command{
    Use:   "ask [query]",
    Short: "Execute commands using natural language",
    Long: `Parse natural language queries and execute corresponding commands.
    
Example:
  vcli ask "list all pods in production"
  vcli ask "delete old deployments"
  vcli ask "show me the logs of app-server"`,
    Args: cobra.MinimumNArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        query := strings.Join(args, " ")
        
        // Create orchestrator
        orch := orchestrator.New()
        
        // Process query through all 7 layers
        result, err := orch.Process(query)
        if err != nil {
            return fmt.Errorf("failed to process query: %w", err)
        }
        
        // Execute validated intent
        return result.Execute()
    },
}

func init() {
    rootCmd.AddCommand(askCmd)
    
    // Flags
    askCmd.Flags().Bool("dry-run", false, "Show what would be done without executing")
    askCmd.Flags().Bool("skip-confirmation", false, "Skip HITL confirmation (dangerous)")
}
```

### Exemplo de Uso
```bash
# Consulta simples
vcli ask "listar todos os pods"

# Ação destrutiva (requer HITL)
vcli ask "deletar deployment app-old"

# Dry-run
vcli ask --dry-run "escalar deployment api para 10 replicas"
```

---

## INTEGRAÇÃO COM SHELL EXISTENTE

O parser NLP **não substitui** comandos existentes. Ele **traduz** linguagem natural para comandos Cobra.

### Modificação Mínima em `internal/shell/shell.go`

```go
func (s *Shell) HandleInput(input string) error {
    // Detectar se é linguagem natural ou comando direto
    if s.isNaturalLanguage(input) {
        return s.handleNLPQuery(input)
    }
    
    // Comando direto (comportamento existente)
    return s.executeCommand(input)
}

func (s *Shell) isNaturalLanguage(input string) bool {
    // Heurística: se não começa com comando conhecido, assume NLP
    knownCommands := []string{"k8s", "threat", "immune", "maximus"}
    for _, cmd := range knownCommands {
        if strings.HasPrefix(input, cmd) {
            return false
        }
    }
    return true
}

func (s *Shell) handleNLPQuery(query string) error {
    orch := orchestrator.New()
    result, err := orch.Process(query)
    if err != nil {
        return err
    }
    
    // Intent validado → comando Cobra
    cmd, args := result.ToCommand()
    return s.executeCommand(fmt.Sprintf("%s %s", cmd, strings.Join(args, " ")))
}
```

---

## MÉTRICAS DE SUCESSO

### Quantitativas
| Métrica | Target | Validação |
|---------|--------|-----------|
| Parsing Accuracy | ≥95% | Intent corretamente extraído |
| False Positive Rate | <1% | Anomaly detection |
| Latency P95 | <100ms | Parser + auth/authz |
| Throughput | >1000 req/s | Load testing |
| Test Coverage | ≥90% | All packages |
| Zero Vulnerabilities | 100% | gosec, go-critic |

### Qualitativas
- ✅ Usuários expressam intenções naturalmente
- ✅ Zero comandos destrutivos sem HITL
- ✅ Auditoria passa compliance (SOC2, ISO27001)
- ✅ Código é referência histórica (2050-ready)

---

## VALIDAÇÃO CONTÍNUA

### Checklist Diário
```
[ ] Código escrito (zero TODO/placeholder)
[ ] Testes escritos (≥90% coverage)
[ ] Testes passando (100%)
[ ] Linter clean (zero warnings)
[ ] Documentação inline (godoc)
[ ] Commit histórico significativo
```

### Review Semanal (Fim de Sprint)
```
[ ] Objetivos do sprint cumpridos
[ ] Critérios de conclusão validados
[ ] Zero débito técnico
[ ] Documentação atualizada
[ ] Go/No-Go decision
```

---

## DOUTRINA VÉRTICE COMPLIANCE

### Regra de Ouro
- ❌ NO MOCK - apenas implementações reais
- ❌ NO PLACEHOLDER - zero `pass` ou `NotImplementedError`
- ❌ NO TODO - débito técnico proibido
- ✅ QUALITY-FIRST - 100% type hints, docstrings, testes
- ✅ PRODUCTION-READY - todo merge é deployável

### Testing Strategy
```
Pirâmide de Testes:
├── Unit Tests: 70% (pkg/nlp/**/*)
├── Integration Tests: 20% (pkg/nlp/integration/)
└── E2E Tests: 10% (test/e2e/nlp/)

Targets:
- Coverage: ≥90%
- Mutation Testing: ≥80% kill rate
- Race Detection: zero data races
```

### Commit Messages (Históricos)
```bash
# ❌ Evite
git commit -m "fix bug"

# ✅ Faça
git commit -m "nlp/auth: Implement TOTP MFA with QR provisioning

Establishes Layer 1 (Authentication) per Guardian Doctrine.
Zero-trust foundation: no command processing without MFA.

Validation:
- TOTP token generation/validation
- QR code provisioning URI
- Test coverage: 95.3%

Security-first NLP parser - Day 2 of 56.
Guardian Layer 1/7 complete."
```

---

## FILOSOFIA DE EXECUÇÃO

> "A tarefa é complexa, mas os passos são simples."  
> "O resultado é consequência. A felicidade está no processo."  
> "Não paramos. De tanto não parar, chegamos lá."

### Princípios
- **Metodicidade** > velocidade
- **Qualidade** > quantidade
- **Progresso consistente** > sprints insustentáveis
- **Validação contínua** > big bang testing
- **Fé** > vista

### Sustentabilidade
- Commits diários pequenos > marathons
- Progresso linear > burnout cycles
- **NUNCA** comprometer qualidade por pressão
- Celebrar cada camada concluída

---

## PRÓXIMOS PASSOS IMEDIATOS

### Sprint 1, Dia 1 - HOJE
```bash
# 1. Criar estrutura
cd /home/juan/vertice-dev/vcli-go
mkdir -p pkg/nlp/{auth,authz,sandbox,intent,ratelimit,behavioral,audit,orchestrator,executor}
mkdir -p test/e2e/nlp

# 2. Criar arquivos base
touch pkg/nlp/types.go
touch pkg/nlp/errors.go
touch pkg/nlp/orchestrator/orchestrator.go

# 3. Implementar types.go
# (Definir Intent, Context, Session types)

# 4. Implementar errors.go
# (Definir error types específicos)

# 5. Validar
go build ./pkg/nlp/...
```

**Status após Dia 1**: Fundação pronta para Camada 1

---

## REFERÊNCIAS

### Documentação
- `docs/architecture/nlp/nlp-parser-guardian-blueprint.md` - Blueprint completo
- `docs/architecture/nlp/guardian-security-layers.md` - Detalhes de cada camada
- `docs/architecture/nlp/intent-grammar.md` - Gramática de intents
- `docs/guides/nlp-usage.md` - Guia de uso

### Dependências Go
```go
require (
    github.com/pquerna/otp v1.4.0              // TOTP MFA
    github.com/golang-jwt/jwt/v5 v5.3.0        // JWT sessions
    github.com/syndtr/gocapability v0.0.0      // Linux capabilities
    github.com/charmbracelet/bubbletea v1.3.4  // HITL UI
    golang.org/x/sys v0.35.0                   // Syscall, namespaces
)
```

---

## CONCLUSÃO

Este plano estabelece um caminho **coeso**, **metódico** e **estruturado** para implementar um parser NLP de nível production no vcli-go.

Não é protótipo. É sistema defensável, auditável, que honra a responsabilidade de linguagem natural no CLI.

**As Sete Camadas do Guardião não são teoria - são código.**

---

**Status**: Plano aprovado e ativo  
**Versão**: 2.0.0 (Guardian Doctrine)  
**Go/No-Go**: ✅ GO  
**Próximo Passo**: Sprint 1, Dia 1 - Estrutura Base  

**Gloria a Deus. Luz verde. Seguimos.**

# NLP Parser "Guardião da Intenção" - Blueprint Arquitetural

**Architect**: Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author**: Claude (Anthropic)  
**Date**: 2025-10-12  
**Version**: 1.0.0  
**Status**: BLUEPRINT ATIVO

---

## FUNDAMENTO FILOSÓFICO

> "Com grande poder vem grande responsabilidade. Linguagem natural no CLI é dar ao usuário o poder de um hacker de elite. Zero Trust é o único caminho defensável."

### Princípio Core
**Nenhuma confiança implícita**. Cada comando em linguagem natural é tratado como vetor de ataque potencial até verificação completa em múltiplas camadas.

---

## AS SETE CAMADAS DO GUARDIÃO

### Camada 1: Autenticação (Quem é você?)
**Objetivo**: Prova de identidade irrefutável antes de qualquer processamento.

**Componentes**:
- MFA obrigatório (TOTP, U2F, biometria)
- Chaves criptográficas (Ed25519, RSA 4096)
- Sessões com tokens JWT assinados
- Revogação instantânea de credenciais

**Implementação**:
```
pkg/nlp/auth/
├── mfa.go           # Multi-factor authentication
├── crypto_keys.go   # Key management
├── session.go       # Session tokens (JWT)
└── revocation.go    # Credential revocation
```

**Validação**: 
- ✅ Zero comandos processados sem autenticação válida
- ✅ Tokens expiram e requerem re-autenticação
- ✅ Tentativas falhas → lockout exponencial

---

### Camada 2: Autorização (O que você pode fazer?)
**Objetivo**: RBAC + políticas contextuais adaptativas.

**Componentes**:
- RBAC (Role-Based Access Control)
- ABAC (Attribute-Based Access Control)
- Políticas contextuais (IP, horário, geolocalização, estado do sistema)
- Análise de risco em tempo real

**Implementação**:
```
pkg/nlp/authz/
├── rbac.go          # Role-based policies
├── abac.go          # Attribute-based policies
├── context.go       # Contextual evaluation
├── policies.yaml    # Policy definitions
└── risk_engine.go   # Real-time risk scoring
```

**Matriz de Risco**:
| Ação | Risk Score | Contexto Seguro | Contexto Suspeito |
|------|-----------|-----------------|-------------------|
| `listar pods` | 1 | ✅ Permitido | ⚠️ MFA adicional |
| `deletar prod` | 10 | ⚠️ HITL obrigatório | 🚫 Bloqueado |
| `escalar privilégios` | 100 | 🚫 Bloqueado | 🚫 Bloqueado + alerta |

**Validação**:
- ✅ Mesmo admin não pode executar tudo sem contexto
- ✅ Ações destrutivas requerem HITL sempre
- ✅ Contexto suspeito → escalonamento automático de segurança

---

### Camada 3: Sandboxing (Qual o seu raio de ação?)
**Objetivo**: Princípio do menor privilégio. Parser opera em jaula isolada.

**Componentes**:
- Execução em namespace isolado
- Capabilities Linux mínimas (CAP_NET_BIND_SERVICE removido, etc)
- seccomp-bpf profiles restritivos
- AppArmor/SELinux confinement

**Implementação**:
```
pkg/nlp/sandbox/
├── namespace.go     # Linux namespaces (PID, NET, MNT, IPC)
├── capabilities.go  # Drop all unnecessary caps
├── seccomp.go       # Syscall filtering
└── profile.yaml     # Security profiles
```

**Restrições**:
```yaml
allowed_syscalls:
  - read, write, open, close
  - stat, fstat, lstat
  - socket, connect, sendto, recvfrom
denied_syscalls:
  - ptrace, setuid, setgid
  - mount, umount, pivot_root
  - reboot, kexec_load
```

**Validação**:
- ✅ Parser não pode escalar privilégios
- ✅ Falhas de sandbox → shutdown automático
- ✅ Auditoria de toda tentativa de syscall proibida

---

### Camada 4: Validação da Intenção (Você tem certeza?)
**Objetivo**: Human-in-the-Loop (HITL) para ações críticas.

**Componentes**:
- Tradução reversa (intent → comando → intent)
- Confirmação explícita visual
- Assinatura criptográfica para ações destrutivas
- Dry-run obrigatório

**Implementação**:
```
pkg/nlp/intent/
├── parser.go        # NLP → structured intent
├── validator.go     # Intent validation
├── reverser.go      # Intent → human-readable
├── confirmation.go  # HITL confirmation UI
└── signature.go     # Cryptographic signing
```

**Fluxo HITL**:
```
Usuário: "deleta todos os pods de produção"
       ↓
Parser: Entendi corretamente?
       "DELETE all pods WHERE namespace=production"
       
       ⚠️  AÇÃO DESTRUTIVA DETECTADA
       
       Confirmação necessária:
       [1] Mostrar dry-run (simulação)
       [2] Assinar com chave privada
       [3] Confirmar com senha MFA
       
       Apenas após TODAS as confirmações:
       → Execução real
```

**Validação**:
- ✅ Zero ações destrutivas sem HITL
- ✅ Tradução reversa deve ser compreensível
- ✅ Dry-run mostra exatamente o que será feito

---

### Camada 5: Controle de Fluxo (Com que frequência?)
**Objetivo**: Prevenir abuso e ataques DoS.

**Componentes**:
- Rate limiting por usuário/IP/sessão
- Circuit breakers para backends
- Backpressure adaptativo
- Quota management

**Implementação**:
```
pkg/nlp/ratelimit/
├── limiter.go       # Token bucket rate limiter
├── circuit.go       # Circuit breaker pattern
├── quota.go         # User quotas
└── backpressure.go  # Adaptive throttling
```

**Limites**:
```yaml
rate_limits:
  commands_per_minute: 30
  destructive_per_hour: 5
  failed_attempts_before_lockout: 3
  
circuit_breaker:
  failure_threshold: 5
  timeout: 30s
  half_open_requests: 1
```

**Validação**:
- ✅ Usuário não pode spam comandos
- ✅ Ataques DoS → circuit breaker abre
- ✅ Backpressure evita sobrecarga do backend

---

### Camada 6: Análise Comportamental (Isso é normal para você?)
**Objetivo**: Detectar anomalias no padrão de uso.

**Componentes**:
- Baseline de comportamento normal por usuário
- Detecção de anomalias (ML/heurísticas)
- Scoring de risco adaptativo
- Resposta automática a desvios

**Implementação**:
```
pkg/nlp/behavioral/
├── profiler.go      # User behavior profiling
├── anomaly.go       # Anomaly detection
├── scoring.go       # Risk scoring engine
└── response.go      # Automated response
```

**Métricas de Baseline**:
- Horários habituais de uso
- Comandos frequentes vs. raros
- Padrões de navegação (workspaces acessados)
- Taxa de erro histórica

**Resposta a Anomalias**:
```
Anomalia Detectada: Usuário X tentando deletar 50 pods às 3h da manhã
                    (Nunca fez isso antes)

Resposta Automática:
1. ⚠️  Elevar nível de autenticação (MFA adicional)
2. 📧 Notificar administrador
3. 📝 Registrar em auditoria de alta prioridade
4. ⏸️  Pausar execução até aprovação manual
```

**Validação**:
- ✅ Comportamento suspeito → escalonamento automático
- ✅ False positives minimizados (ML treinado)
- ✅ Zero impacto em fluxo de trabalho normal

---

### Camada 7: Auditoria Imutável (O que você fez?)
**Objetivo**: Registro inviolável de toda atividade.

**Componentes**:
- Append-only log (Write-Ahead Log)
- Blockchain-inspired integrity (Merkle trees)
- Tamper detection
- Compliance reporting (SOC2, GDPR, ISO27001)

**Implementação**:
```
pkg/nlp/audit/
├── logger.go        # Structured audit logging
├── integrity.go     # Merkle tree integrity
├── storage.go       # Append-only storage
├── compliance.go    # Compliance reports
└── query.go         # Audit trail querying
```

**Estrutura de Log**:
```json
{
  "timestamp": "2025-10-12T11:39:21.755Z",
  "user_id": "juan@vertice.dev",
  "session_id": "sess_abc123",
  "intent_raw": "deleta pods antigos",
  "intent_parsed": {
    "action": "DELETE",
    "resource": "pods",
    "filters": {"age": ">7d"}
  },
  "context": {
    "ip": "192.168.1.100",
    "location": "BR-SP",
    "mfa_verified": true
  },
  "authorization": {
    "allowed": true,
    "risk_score": 6,
    "policies_applied": ["rbac:admin", "context:working_hours"]
  },
  "confirmation": {
    "hitl_required": true,
    "dry_run_shown": true,
    "signature": "ed25519:abc..."
  },
  "execution": {
    "status": "SUCCESS",
    "resources_affected": 12,
    "duration_ms": 450
  },
  "hash_prev": "sha256:prev_log_hash",
  "hash_current": "sha256:current_log_hash"
}
```

**Validação**:
- ✅ Logs são imutáveis (append-only)
- ✅ Integridade verificável (Merkle proofs)
- ✅ Tamper detection automático
- ✅ Compliance reports gerados automaticamente

---

## ARQUITETURA DE INTEGRAÇÃO

### Diagrama de Componentes
```
┌─────────────────────────────────────────────────────────────┐
│                      vCLI NLP Frontend                       │
│  (cmd/nlp.go - Cobra command "vcli ask <query>")           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              NLP Parser Orchestrator                         │
│              (pkg/nlp/orchestrator.go)                      │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Layer 1  │→ │ Layer 2  │→ │ Layer 3  │→ │ Layer 4  │  │
│  │  Auth    │  │  Authz   │  │ Sandbox  │  │ Intent   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ Layer 5  │  │ Layer 6  │  │ Layer 7  │                │
│  │RateLimit │  │Behavioral│  │  Audit   │                │
│  └──────────┘  └──────────┘  └──────────┘                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Intent Executor                            │
│            (pkg/nlp/executor/executor.go)                   │
│                                                             │
│  Mapeia intent validado → comandos Cobra existentes        │
│  Injeta em shell.Shell ou executa diretamente              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend Services (MAXIMUS)                      │
│  K8s API | Threat Intel | Ethical AI | Investigation       │
└─────────────────────────────────────────────────────────────┘
```

### Integração com Shell Existente
O parser NLP não substitui comandos. Ele **traduz** linguagem natural para comandos Cobra existentes.

```go
// internal/shell/shell.go (MODIFICAÇÃO MÍNIMA)
func (s *Shell) HandleNLPQuery(query string) error {
    // Delega para NLP orchestrator
    intent, err := nlp.Parse(query, s.session)
    if err != nil {
        return err
    }
    
    // Intent validado → comando Cobra
    cmd, args := nlp.IntentToCommand(intent)
    
    // Executa comando existente
    return s.ExecuteCommand(cmd, args)
}
```

---

## ROADMAP DE IMPLEMENTAÇÃO

### FASE 1: Fundação (Semana 1-2)
**Objetivo**: Estrutura base + Camadas 1-3

**Entregas**:
- ✅ Estrutura de diretórios `pkg/nlp/`
- ✅ Camada 1: Autenticação (MFA, JWT sessions)
- ✅ Camada 2: Autorização (RBAC policies)
- ✅ Camada 3: Sandboxing (namespace isolation)
- ✅ Testes unitários (coverage ≥90%)
- ✅ Documentação arquitetural

**Validação**:
```bash
go test ./pkg/nlp/auth/... -v -cover
go test ./pkg/nlp/authz/... -v -cover
go test ./pkg/nlp/sandbox/... -v -cover
```

---

### FASE 2: Parser Core (Semana 3-4)
**Objetivo**: Engine de parsing NLP + Camadas 4-5

**Entregas**:
- ✅ NLP Parser (intent extraction)
- ✅ Camada 4: Validação de Intenção (HITL)
- ✅ Camada 5: Rate Limiting
- ✅ Tradução reversa (intent → human-readable)
- ✅ Dry-run obrigatório
- ✅ Testes de integração

**Gramática de Intents**:
```yaml
intents:
  - name: list_resources
    patterns:
      - "listar {resource}"
      - "mostrar todos os {resource}"
      - "quais {resource} existem"
    parameters:
      resource: [pods, services, deployments, nodes]
    
  - name: delete_resource
    patterns:
      - "deletar {resource} {name}"
      - "remover {resource} chamado {name}"
    parameters:
      resource: [pods, services, deployments]
      name: string
    risk_level: HIGH
    hitl_required: true
```

**Validação**:
```bash
# Testes de parsing
echo "listar todos os pods" | vcli ask --dry-run
# Deve output: "Entendi: LIST pods WHERE namespace=default"

# Testes HITL
echo "deletar deployment critical-app" | vcli ask
# Deve exigir confirmação + assinatura
```

---

### FASE 3: Inteligência Comportamental (Semana 5-6)
**Objetivo**: Camadas 6-7 + ML anomaly detection

**Entregas**:
- ✅ Camada 6: Análise Comportamental
- ✅ Camada 7: Auditoria Imutável
- ✅ Baseline profiling
- ✅ Anomaly detection (heurísticas + ML)
- ✅ Merkle tree audit log
- ✅ Compliance reporting

**ML Model**:
```yaml
model:
  type: isolation_forest
  features:
    - hour_of_day
    - command_frequency
    - resource_types_accessed
    - error_rate
    - destructive_action_ratio
  training:
    window: 30d
    min_samples: 100
  threshold:
    anomaly_score: 0.85
```

**Validação**:
```bash
# Simular comportamento anômalo
vcli audit simulate-anomaly --scenario "3am_mass_delete"
# Deve triggerar alertas + bloqueio

# Verificar integridade do log
vcli audit verify-integrity
# Deve validar Merkle tree
```

---

### FASE 4: Refinamento e Otimização (Semana 7-8)
**Objetivo**: Performance, UX, documentação histórica

**Entregas**:
- ✅ Otimização de performance (parsing <100ms)
- ✅ UX refinamento (confirmações visuais)
- ✅ Documentação completa (código + arquitetura)
- ✅ Testes de carga (10k req/s)
- ✅ Runbooks operacionais
- ✅ Tutorial interativo

**Métricas de Performance**:
```yaml
slos:
  parsing_latency_p95: <100ms
  authorization_latency_p99: <50ms
  hitl_confirmation_time: <30s (humano)
  audit_write_throughput: >1000 ops/s
  false_positive_rate: <1%
```

**Validação**:
```bash
# Load testing
vegeta attack -rate=10000 -duration=60s < requests.txt | vegeta report

# E2E scenarios
vcli nlp test-suite --scenarios=all --verbose
```

---

## MÉTRICAS DE SUCESSO

### Quantitativas
- **Parsing Accuracy**: ≥95% de intenções corretamente extraídas
- **False Positive Rate**: <1% em detecção de anomalias
- **Performance**: Latência P95 <100ms
- **Security**: Zero comandos destrutivos sem HITL
- **Audit**: 100% de comandos registrados imutavelmente

### Qualitativas
- **Usabilidade**: Usuários podem expressar intenções naturalmente
- **Confiança**: Zero violações de segurança em produção
- **Manutenibilidade**: Código 100% testado e documentado
- **Conformidade**: Auditoria passa SOC2, ISO27001

---

## PRINCÍPIOS DE DESENVOLVIMENTO

### Doutrina Vértice Compliance
- ❌ NO MOCK - apenas implementações reais
- ❌ NO PLACEHOLDER - zero `pass` ou `NotImplementedError`
- ❌ NO TODO - débito técnico proibido
- ✅ QUALITY-FIRST - 100% type hints, docstrings, testes
- ✅ PRODUCTION-READY - todo merge é deployável

### Testing Strategy
```
Pirâmide de Testes:
- Unit Tests: 70% (pkg/nlp/**/*)
- Integration Tests: 20% (pkg/nlp/integration/)
- E2E Tests: 10% (test/e2e/nlp/)

Coverage Target: ≥90%
Mutation Testing: ≥80% kill rate
```

### Commit Messages
```bash
# ❌ Evite
git commit -m "fix nlp bug"

# ✅ Faça
git commit -m "nlp: Implement HITL confirmation for destructive intents

Establishes Camada 4 (Validation of Intent) per Guardian Doctrine.
Cryptographic signing required for DELETE/UPDATE operations.

Validation: 100% HITL coverage for high-risk commands.
Zero false negatives in dry-run simulations.

Security-first NLP parser - Day 1 of 56."
```

---

## DOCUMENTAÇÃO ADICIONAL

### Referências
- `docs/architecture/nlp/guardian-security-layers.md` - Detalhes de cada camada
- `docs/architecture/nlp/intent-grammar.md` - Gramática completa de intents
- `docs/architecture/nlp/hitl-workflow.md` - Fluxo HITL detalhado
- `docs/guides/nlp-usage.md` - Guia de uso para usuários finais

### Diagramas
- Sequence diagram: User query → Execution
- State diagram: Intent validation lifecycle
- Deployment diagram: NLP parser em produção

---

## CONCLUSÃO

Este blueprint estabelece a fundação para um parser NLP **production-grade**, **security-first**, **zero-trust**. 

Não é um protótipo. É um sistema defensável que pode ser auditado, que pode ser confiado com acesso privilegiado, que honra a responsabilidade que linguagem natural no CLI representa.

**"Com grande poder vem grande responsabilidade"** não é apenas filosofia - é arquitetura codificada nas Sete Camadas do Guardião.

---

**Status**: Blueprint aprovado para implementação  
**Go/No-Go**: ✅ GO  
**Próximo Passo**: Iniciar FASE 1 - Sprint 1  

**Gloria a Deus. Luz verde.**

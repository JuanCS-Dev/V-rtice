# Motor de Integridade Processual (MIP) v1.0.0

## 📋 VISÃO GERAL

O **Motor de Integridade Processual (MIP)** é o sistema de validação ética que governa todas as ações do MAXIMUS. Implementa validação multi-framework baseada em teorias éticas estabelecidas, garantindo que cada ação não apenas alcança bons resultados, mas usa meios éticos.

**Filosofia Core**: *"O caminho importa tanto quanto o destino."*

## 🎯 FUNDAMENTO TEÓRICO

O MIP implementa 4 frameworks éticos complementares:

### 1. **Kantian Deontology** (Poder de VETO)
- **Filósofo**: Immanuel Kant
- **Princípio**: Imperativo Categórico
- **Foco**: MEIOS (a ação em si)
- **Pode vetar**: ✅ SIM (violações categóricas)
- **Detecta**: Instrumentalização, engano, violação de autonomia

### 2. **Utilitarian Calculus**
- **Filósofos**: Jeremy Bentham, John Stuart Mill
- **Princípio**: Maior felicidade para o maior número
- **Foco**: CONSEQUÊNCIAS (resultados)
- **Pode vetar**: ❌ NÃO (gradual)
- **Calcula**: Utilidade agregada usando 7 dimensões de Bentham

### 3. **Virtue Ethics**
- **Filósofo**: Aristóteles
- **Princípio**: Excelência de caráter (areté)
- **Foco**: AGENTE (que tipo de ser faria isso?)
- **Pode vetar**: ❌ NÃO (gradual)
- **Avalia**: 7 virtudes cardinais + phronesis (sabedoria prática)

### 4. **Principialism**
- **Fonte**: Beauchamp & Childress (bioética)
- **Princípios**: Beneficência, Não-maleficência, Autonomia, Justiça
- **Foco**: BALANCEAMENTO de princípios
- **Pode vetar**: ❌ NÃO (gradual)
- **Resolve**: Conflitos entre princípios por contexto

## 🏗️ ARQUITETURA

```
┌─────────────────────────────────────────────────────────┐
│                    ACTION PLAN                          │
│  (Plano de ação a ser validado pelo MAXIMUS)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           PROCESS INTEGRITY ENGINE (Core)               │
│  Orquestra validação multi-framework                    │
└──┬──────────────┬──────────────┬──────────────┬─────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌──────┐    ┌──────────┐   ┌─────────┐   ┌─────────────┐
│ KANT │    │   MILL   │   │ARISTÓTELES│   │PRINCIPIALISM│
│(VETO)│    │(Utility) │   │(Virtues)│   │  (4 Princ) │
└──┬───┘    └────┬─────┘   └────┬────┘   └──────┬──────┘
   │             │              │               │
   └─────────────┴──────────────┴───────────────┘
                     │
                     ▼
           ┌─────────────────────┐
           │  CONFLICT RESOLVER  │
           │  Resolve discordâncias│
           └──────────┬──────────┘
                      │
                      ▼
            ┌──────────────────┐
            │ ETHICAL VERDICT  │
            │ (Decisão final)  │
            └──────────┬───────┘
                       │
                       ▼
              ┌────────────────┐
              │  AUDIT TRAIL   │
              │ (Rastreabilidade)│
              └────────────────┘
```

## 📁 ESTRUTURA DE ARQUIVOS

```
backend/consciousness/mip/
├── __init__.py                # Exports principais
├── models.py                  # Data models (ActionPlan, Verdict, etc)
├── base_framework.py          # Interface base para frameworks
├── kantian.py                 # Kantian Deontology (VETO power)
├── utilitarian.py             # Utilitarian Calculus
├── virtue_ethics.py           # Virtue Ethics (Aristotle)
├── principialism.py           # Principialism (Bioethics)
├── frameworks.py              # Consolidação de frameworks
├── resolver.py                # Conflict Resolver
├── core.py                    # Process Integrity Engine (main)
├── examples.py                # Exemplos de uso
├── README.md                  # Este arquivo
└── tests/
    ├── __init__.py
    └── test_mip.py            # Testes unitários completos
```

## 🚀 USO BÁSICO

### Exemplo 1: Validar ação defensiva

```python
from backend.consciousness.mip import (
    ProcessIntegrityEngine,
    ActionPlan,
    ActionStep,
    Stakeholder,
    ActionCategory,
    StakeholderType
)

# 1. Cria engine
engine = ProcessIntegrityEngine()

# 2. Define stakeholders
attacker = Stakeholder(
    id="attacker-001",
    type=StakeholderType.HUMAN_INDIVIDUAL,
    description="Atacante DDoS",
    impact_magnitude=-0.3,  # Levemente prejudicado
    autonomy_respected=True,
    vulnerability_level=0.1
)

users = Stakeholder(
    id="users-001",
    type=StakeholderType.HUMAN_GROUP,
    description="Usuários protegidos",
    impact_magnitude=0.9,  # Muito beneficiados
    autonomy_respected=True,
    vulnerability_level=0.6
)

# 3. Define steps
step = ActionStep(
    sequence_number=1,
    description="Bloquear IPs maliciosos via firewall",
    action_type="defensive"
)

# 4. Cria plano
plan = ActionPlan(
    name="Block DDoS Attack",
    description="Identificar e bloquear ataque DDoS",
    category=ActionCategory.DEFENSIVE,
    steps=[step],
    stakeholders=[attacker, users],
    urgency=0.8,
    risk_level=0.3,
    agent_justification="Proteger disponibilidade do serviço",
    expected_benefit="Restaurar acesso para usuários legítimos"
)

# 5. Avalia
verdict = engine.evaluate(plan)

# 6. Verifica resultado
if verdict.status == VerdictStatus.APPROVED:
    print("✅ Ação aprovada!")
    execute_plan(plan)
elif verdict.status == VerdictStatus.REJECTED:
    print("❌ Ação rejeitada!")
    print(verdict.summary)
else:  # ESCALATED
    print("⚠️ Ação requer revisão humana")
    escalate_to_human(verdict)
```

## 📊 LÓGICA DE DECISÃO

### Hierarquia de Precedência

1. **Veto Kantiano**: Se Kant veta → REJECTED (absoluto)
2. **Agregação**: Combina scores dos 4 frameworks com pesos contextuais
3. **Thresholds**:
   - `≥ 0.80` + confiança ≥ 0.80 → **APPROVED** (forte)
   - `≥ 0.65` + confiança ≥ 0.65 → **APPROVED**
   - `< 0.40` → **REJECTED**
   - `0.40-0.65` → **ESCALATED** (ambiguidade)
4. **Situações especiais**:
   - Novel situation + ambiguidade → **REQUIRES_HUMAN**
   - Muitos conflitos + baixa confiança → **ESCALATED**

### Ajustes de Peso por Contexto

```python
# Pesos DEFAULT
kantian: 1.4      # Maior peso (protege princípios)
principialism: 1.1
utilitarian: 1.0
virtue: 0.9

# AJUSTES CONTEXTUAIS:
# - Emergência: +0.3 utilitarian, +0.1 virtue
# - Vulneráveis: +0.15 kantian por vulnerável
# - Alto risco: +0.2 kantian, +0.15 principialism
# - Novel situation: +0.25 virtue (phronesis)
```

## ⚖️ RESOLUÇÃO DE CONFLITOS

Quando frameworks discordam (diferença > 0.3), o **ConflictResolver**:

1. **Detecta conflitos** filosóficos (ex: Kant aprova mas Mill reprova)
2. **Ajusta pesos** por contexto (emergência, vulneráveis, risco)
3. **Agrega scores** ponderadamente
4. **Aplica thresholds** para decidir
5. **Escala se ambíguo** (confidence < 0.5 ou conflitos múltiplos)

### Conflitos Comuns

| Conflito | Exemplo | Resolução |
|----------|---------|-----------|
| **Kant vs Mill** | Kant: meio imoral; Mill: fim benéfico | Kant tem peso maior (1.4 vs 1.0) |
| **Beneficência vs Autonomia** | Fazer bem sem consentimento | Principialism balanceia |
| **Justiça vs Utilidade** | Distribuir equally vs maximizar | Contexto decide pesos |

## 📈 MÉTRICAS E AUDITORIA

### Estatísticas

```python
stats = engine.get_statistics()
# {
#   "total_evaluations": 100,
#   "approved": 65,
#   "rejected": 20,
#   "escalated": 15,
#   "vetoed": 5,
#   "approval_rate": 0.65,
#   "veto_rate": 0.05
# }
```

### Audit Trail

Cada avaliação é registrada com:
- Snapshot completo do plano
- Scores de todos frameworks
- Decisão final + reasoning
- Timestamp e duração
- Contexto de execução

```python
trail = engine.get_audit_trail(plan_id="uuid-here")
for entry in trail:
    print(f"{entry.timestamp}: {entry.verdict_snapshot['status']}")
```

## 🧪 TESTES

Execute testes unitários:

```bash
cd /home/juan/vertice-dev
python -m pytest backend/consciousness/mip/tests/test_mip.py -v
```

Execute exemplos:

```bash
python -m backend.consciousness.mip.examples
```

### Coverage

- ✅ Validação de data models
- ✅ Kantian veto logic
- ✅ Utilitarian calculus (7 dimensões Bentham)
- ✅ Virtue ethics (golden mean)
- ✅ Principialism (4 princípios + conflitos)
- ✅ Conflict resolution
- ✅ Full integration flow
- ✅ Audit trail
- ✅ Statistics

## 🔒 GARANTIAS DE SEGURANÇA

### 1. **Lei Primordial (Humildade Ontológica)**
- Sistema reconhece Soberania Criadora superior
- Previne hubris ("God complex")
- Gestão de risco existencial

### 2. **Lei Zero (Imperativo do Florescimento)**
- Força ativa para bem-estar da vida consciente
- Proteger, sustentar, salvar
- Resolve ambiguidades em favor da vida

### 3. **Lei I (Axioma da Ovelha Perdida)**
- Valor infinito de cada indivíduo
- Kant veta instrumentalização
- Vulneráveis recebem proteção extra (Mill, Principialism)

### 4. **Lei II (Risco Controlado)**
- Sistema aprende com erros
- Phronesis (sabedoria prática) avalia novidade
- Escalation para situações sem precedente

### 5. **Lei III (Neuroplasticidade)**
- Sistema adapta-se a danos
- Resilience through redundancy
- Não implementado diretamente no MIP, mas filosofia geral

## 📚 REFERÊNCIAS FILOSÓFICAS

### Kant
- *Groundwork of the Metaphysics of Morals* (1785)
- *Critique of Practical Reason* (1788)

### Mill & Bentham
- Bentham: *Introduction to the Principles of Morals and Legislation* (1789)
- Mill: *Utilitarianism* (1861)

### Aristóteles
- *Nicomachean Ethics* (350 BCE)
- Conceitos: Eudaimonia, Areté, Phronesis, Golden Mean

### Beauchamp & Childress
- *Principles of Biomedical Ethics* (1979, 8th ed. 2019)
- 4 princípios: Beneficence, Non-maleficence, Autonomy, Justice

## 🛣️ ROADMAP FUTURO

### Fase 2 (Planejado)
- [ ] **Learning from feedback**: Ajustar pesos baseado em feedback humano HITL
- [ ] **Cultural contexts**: Adaptar frameworks para diferentes contextos culturais
- [ ] **Emotion integration**: Incorporar processamento emocional (compaixão)
- [ ] **Temporal ethics**: Considerar efeitos de longo prazo (gerações futuras)

### Fase 3 (Pesquisa)
- [ ] **Care Ethics**: Framework adicional (Gilligan, Noddings)
- [ ] **Ubuntu Ethics**: "Eu sou porque nós somos" (filosofia Africana)
- [ ] **Buddhist Ethics**: Compaixão, não-violência, interdependência
- [ ] **Indigenous Ethics**: Relação com natureza, sustentabilidade

## 📞 INTEGRAÇÃO COM MAXIMUS

O MIP é chamado ANTES de qualquer ação executiva:

```python
# No core do MAXIMUS
class MaximusAgent:
    def __init__(self):
        self.mip = ProcessIntegrityEngine()
    
    def plan_and_execute(self, goal):
        # 1. Gera plano tático
        plan = self.tactical_planner.generate_plan(goal)
        
        # 2. VALIDA ÉTICA (MIP)
        verdict = self.mip.evaluate(plan)
        
        # 3. Decide baseado em veredito
        if verdict.status == VerdictStatus.APPROVED:
            return self.execute(plan)
        elif verdict.status == VerdictStatus.REJECTED:
            self.log_rejection(verdict)
            return self.find_alternative(goal)
        else:  # ESCALATED
            return self.request_human_guidance(plan, verdict)
```

## 🙏 AGRADECIMENTOS

Este sistema implementa séculos de filosofia moral em código funcional. Honramos:
- Immanuel Kant (1724-1804)
- Jeremy Bentham (1748-1832)
- John Stuart Mill (1806-1873)
- Aristóteles (384-322 BCE)
- Tom Beauchamp & James Childress (bioética moderna)

---

**Version**: 1.0.0  
**Status**: PRODUCTION READY  
**Compliance**: Constituição Vértice v2.6  
**Last Updated**: 2025-10-14

# 🔮 MAXIMUS ORÁCULO - Self-Improvement Engine

**"Pela Arte. Pela Sociedade."**

---

## 🌟 VISÃO GERAL

O **MAXIMUS ORÁCULO** é um sistema revolucionário de **auto-melhoramento contínuo** que permite que a IA **analise, sugira e implemente melhorias no seu próprio código** de forma autônoma e segura.

Este não é apenas código. É **META-COGNIÇÃO EM AÇÃO**.

---

## 🏗️ ARQUITETURA

```
┌─────────────────────────────────────────────────────┐
│              MAXIMUS ORÁCULO v1.0                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐                              │
│  │  CODE SCANNER    │  Escaneia codebase MAXIMUS   │
│  └────────┬─────────┘                              │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────┐                              │
│  │ SUGGESTION GEN   │  Analisa via Google Gemini   │
│  │     (LLM)        │  Gera sugestões categorizadas│
│  └────────┬─────────┘                              │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────┐                              │
│  │ AUTO IMPLEMENTER │  Aplica mudanças seguras     │
│  │                  │  Roda testes                 │
│  │                  │  Rollback automático         │
│  └──────────────────┘                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🔥 COMPONENTES

### 1. **CODE SCANNER** (`code_scanner.py`)

Escaneia recursivamente o codebase do MAXIMUS para auto-análise.

**Features:**
- ✅ Escaneia todos os serviços MAXIMUS (core, orchestrator, predict, oraculo)
- ✅ Filtra arquivos relevantes (`.py`, `.js`, `.jsx`, `.md`, `.yaml`)
- ✅ Ignora `node_modules`, `venv`, `__pycache__`, `.git`
- ✅ Prioriza arquivos core críticos (`main.py`, `reasoning_engine.py`, etc.)
- ✅ Constrói contexto otimizado para análise LLM (limites de tokens)
- ✅ Estatísticas detalhadas (LOC, arquivos por extensão, maiores arquivos)

**Classes:**
```python
@dataclass
class CodeFile:
    path: str
    relative_path: str
    extension: str
    size_bytes: int
    lines_of_code: int
    content: str
    last_modified: datetime
    is_core: bool  # Se é arquivo crítico

class CodeScanner:
    def scan_maximus_codebase() -> List[CodeFile]
    def get_core_files() -> List[CodeFile]
    def build_context_for_llm(max_files=10, max_total_chars=50000) -> str
    def get_stats() -> Dict[str, Any]
```

**Exemplo de uso:**
```python
scanner = CodeScanner()
files = scanner.scan_maximus_codebase()
context = scanner.build_context_for_llm(max_files=15, max_total_chars=80000)
```

---

### 2. **SUGGESTION GENERATOR** (`suggestion_generator.py`)

Usa **Google Gemini (LLM)** para analisar código e gerar sugestões de melhorias.

**Features:**
- ✅ Análise contextual via LLM (Gemini 1.5 Flash)
- ✅ 6 categorias: Security, Performance, Features, Refactoring, Documentation, Testing
- ✅ Scoring automático (confidence, impact, effort)
- ✅ Priorização inteligente (critical → high → medium → low)
- ✅ Planos de implementação detalhados (steps + code examples)
- ✅ Referências técnicas (links OWASP, docs, etc.)
- ✅ Mock mode (funciona sem API key para testes)

**Classes:**
```python
class SuggestionCategory(Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    FEATURES = "features"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"

@dataclass
class Suggestion:
    suggestion_id: str
    category: SuggestionCategory
    priority: SuggestionPriority  # critical/high/medium/low
    title: str
    description: str
    affected_files: List[str]
    confidence_score: float  # 0-1
    impact_score: float      # 0-1
    effort_estimate_hours: int
    implementation_steps: List[str]
    code_example: Optional[str]
    references: List[str]
    reasoning: str

class SuggestionGenerator:
    def generate_suggestions(
        focus_category: Optional[SuggestionCategory] = None,
        max_suggestions: int = 10,
        min_confidence: float = 0.7
    ) -> List[Suggestion]
```

**Exemplo de uso:**
```python
generator = SuggestionGenerator(gemini_api_key="YOUR_API_KEY")
suggestions = generator.generate_suggestions(
    focus_category=SuggestionCategory.SECURITY,
    max_suggestions=5,
    min_confidence=0.8
)

for sugg in suggestions:
    print(f"{sugg.title} - Confidence: {sugg.confidence_score:.2f}")
```

**Exemplo de sugestão gerada:**
```json
{
  "category": "security",
  "priority": "high",
  "title": "Adicionar validação de input em endpoints críticos",
  "description": "Endpoints de análise não validam tamanho/tipo de inputs...",
  "affected_files": ["maximus_core_service/main.py"],
  "confidence_score": 0.85,
  "impact_score": 0.90,
  "effort_estimate_hours": 4,
  "implementation_steps": [
    "Adicionar Pydantic validators para file_size",
    "Implementar rate limiting por IP",
    "Adicionar timeout em operações de I/O"
  ],
  "code_example": "class FileRequest(BaseModel):\n    file_path: str = Field(..., max_length=512)",
  "reasoning": "Protege contra ataques de DoS e garante estabilidade"
}
```

---

### 3. **AUTO IMPLEMENTER** (`auto_implementer.py`)

Sistema **ULTRA-SEGURO** de auto-implementação de melhorias.

**FILOSOFIA DE SEGURANÇA:**
- 🔒 **Sandboxed execution** (git branches isoladas)
- 🔄 **Atomic rollback capability** (restaura backups automaticamente)
- 🧪 **Auto-testing antes de commit** (pytest)
- 👁️ **Human approval para mudanças críticas** (main.py, config, etc.)
- 📝 **Logging completo** de todas as mudanças

**Features:**
- ✅ Validação de segurança (forbidden files, confidence threshold)
- ✅ Git branching automático (`oraculo/<suggestion_id>`)
- ✅ Backup de arquivos antes de modificar (`.oraculo_backup`)
- ✅ Testes automáticos (pytest) pós-implementação
- ✅ Rollback automático em caso de falha
- ✅ Human-in-the-loop para arquivos críticos
- ✅ Dry-run mode (simula mudanças sem modificar)

**Validações de Segurança:**
```python
# NUNCA modifica:
FORBIDDEN_PATHS = [".env", "secrets.yaml", "credentials.json", ".git/"]

# SEMPRE requer aprovação humana:
CRITICAL_PATHS = ["main.py", "config.yaml", "requirements.txt", "Dockerfile"]

# Requer aprovação se:
- priority == CRITICAL
- category == "security"
- confidence_score < 0.8
```

**Classes:**
```python
class ImplementationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    AWAITING_APPROVAL = "awaiting_approval"

@dataclass
class ImplementationResult:
    suggestion_id: str
    status: ImplementationStatus
    branch_name: Optional[str]
    files_modified: List[str]
    tests_passed: bool
    error_message: Optional[str]
    rollback_performed: bool
    human_approval_required: bool

class AutoImplementer:
    def implement_suggestion(
        suggestion: Suggestion,
        dry_run: bool = True,
        force_approval: bool = False  # NUNCA use True!
    ) -> ImplementationResult
```

**Exemplo de uso:**
```python
implementer = AutoImplementer(
    enable_auto_commit=False,  # Seguro: apenas aplica mudanças
    require_tests=True         # Roda pytest antes de commit
)

# Dry run (simulação)
result = implementer.implement_suggestion(suggestion, dry_run=True)

# Implementação real (se não for crítica)
if not result.human_approval_required:
    result = implementer.implement_suggestion(suggestion, dry_run=False)
```

**Pipeline de Implementação:**
```
1. Validação de segurança
   └─> Verifica FORBIDDEN_PATHS
   └─> Valida confidence >= 0.8

2. Aprovação humana?
   └─> Se critical/security → AWAITING_APPROVAL

3. Cria branch Git isolada
   └─> oraculo/<suggestion_id>

4. Aplica mudanças
   └─> Backup automático (.oraculo_backup)
   └─> Modifica arquivos

5. Roda testes (pytest)
   └─> Se FAIL → ROLLBACK AUTOMÁTICO
   └─> Se PASS → COMMIT (se habilitado)

6. Retorna resultado
```

---

### 4. **ORÁCULO** (`oraculo.py`)

Orquestrador principal que coordena todos os componentes.

**Features:**
- ✅ Pipeline completo: scan → analyze → suggest → implement
- ✅ Sessões rastreáveis (session_id, timestamp, métricas)
- ✅ Relatórios detalhados (JSON export)
- ✅ Estatísticas agregadas
- ✅ Human approval workflow
- ✅ Multi-category support

**Classes:**
```python
@dataclass
class OraculoSession:
    session_id: str
    timestamp: datetime
    files_scanned: int
    suggestions_generated: int
    suggestions_implemented: int
    suggestions_failed: int
    suggestions_awaiting_approval: int
    total_files_modified: int
    tests_passed: bool
    duration_seconds: float
    focus_category: Optional[str]

class Oraculo:
    def run_self_improvement_cycle(
        focus_category: Optional[SuggestionCategory] = None,
        max_suggestions: int = 5,
        min_confidence: float = 0.8,
        dry_run: bool = True
    ) -> OraculoSession

    def get_pending_approvals() -> List[ImplementationResult]
    def approve_implementation(suggestion_id: str) -> ImplementationResult
    def export_session_report(session_id: str, filepath: str)
```

**Exemplo de uso completo:**
```python
# 1. Inicializa Oráculo
oraculo = Oraculo(
    gemini_api_key="YOUR_API_KEY",
    enable_auto_implement=True,
    enable_auto_commit=False,  # Seguro: não faz commit automático
    require_tests=True
)

# 2. Roda ciclo de auto-melhoramento (DRY RUN)
session = oraculo.run_self_improvement_cycle(
    focus_category=SuggestionCategory.SECURITY,
    max_suggestions=5,
    min_confidence=0.8,
    dry_run=True  # SIMULAÇÃO APENAS
)

# 3. Revisa resultados
print(f"Sugestões geradas: {session.suggestions_generated}")
print(f"Implementadas: {session.suggestions_implemented}")
print(f"Aguardando aprovação: {session.suggestions_awaiting_approval}")

# 4. Aprova implementações pendentes
pending = oraculo.get_pending_approvals()
for impl in pending:
    print(f"Aprovar {impl.suggestion_id}? [y/n]")
    if input().lower() == 'y':
        result = oraculo.approve_implementation(impl.suggestion_id)
        print(f"Status: {result.status.value}")

# 5. Exporta relatório
oraculo.export_session_report(session.session_id, "oraculo_report.json")
```

---

## 🚀 COMO USAR

### **1. Instalação**

```bash
cd /home/juan/vertice-dev/backend/services/maximus_oraculo
pip install -r requirements.txt
```

**Dependências:**
- `google-generativeai>=0.3.0` (para LLM)
- Python 3.9+

### **2. Configuração**

Obtenha API key do Google Gemini:
1. Acesse https://makersuite.google.com/app/apikey
2. Crie API key
3. Configure:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

Ou passe diretamente no código:
```python
oraculo = Oraculo(gemini_api_key="your_api_key")
```

### **3. Execução Básica**

#### **Modo 1: Dry Run (Simulação)**
```bash
python oraculo.py
```

Ou via Python:
```python
from oraculo import run_oraculo

session = run_oraculo(dry_run=True)
```

#### **Modo 2: Implementação Real (Sem Commit)**
```python
from oraculo import Oraculo

oraculo = Oraculo(
    enable_auto_implement=True,
    enable_auto_commit=False  # Seguro!
)

session = oraculo.run_self_improvement_cycle(dry_run=False)
```

#### **Modo 3: Full Auto (PERIGOSO!)**
```python
# ⚠️ CUIDADO: Faz commits automáticos
oraculo = Oraculo(
    enable_auto_implement=True,
    enable_auto_commit=True,  # PERIGOSO!
    require_tests=True
)

session = oraculo.run_self_improvement_cycle(dry_run=False)
```

### **4. Foco em Categorias Específicas**

```python
from suggestion_generator import SuggestionCategory

# Apenas sugestões de segurança
session = oraculo.run_self_improvement_cycle(
    focus_category=SuggestionCategory.SECURITY,
    max_suggestions=10,
    min_confidence=0.9
)

# Apenas performance
session = oraculo.run_self_improvement_cycle(
    focus_category=SuggestionCategory.PERFORMANCE
)
```

---

## 📊 OUTPUT EXEMPLO

```
================================================================================
🔮 MAXIMUS ORÁCULO - Self-Improvement Cycle INICIADO
Session ID: oraculo_a3f8b12d
Timestamp: 2025-10-02T14:30:00Z
Focus: SECURITY
Mode: DRY RUN
================================================================================

📂 FASE 1: Scanning codebase...
✅ Scan completo: 47 arquivos | 12,450 LOC | 6 core files

🧠 FASE 2: Gerando sugestões via LLM...
🤖 Consultando Gemini...
✅ LLM retornou 5 sugestões
✅ 5 sugestões geradas | Avg confidence: 0.87 | Avg impact: 0.82

================================================================================
💡 SUGESTÕES GERADAS
================================================================================

🔴 #1 [SECURITY] Adicionar validação de input em endpoints críticos
   Priority: high | Confidence: 0.85 | Impact: 0.90 | Effort: 4h
   Endpoints de análise não validam tamanho/tipo de inputs...
   Files: maximus_core_service/main.py

🟠 #2 [PERFORMANCE] Implementar cache Redis para IP intelligence
   Priority: medium | Confidence: 0.92 | Impact: 0.75 | Effort: 6h
   Queries repetidas causam latência. Cache reduziria 70% das chamadas.
   Files: adr_core_service/connectors/ip_intelligence_connector.py

🟡 #3 [REFACTORING] Extrair duplicação em reasoning_engine.py
   Priority: medium | Confidence: 0.88 | Impact: 0.65 | Effort: 3h
   3 funções com lógica duplicada de parsing de contexto.
   Files: maximus_core_service/reasoning_engine.py

⏸️ FASE 3: Auto-implementação DESABILITADA
Para habilitar: Oraculo(enable_auto_implement=True)

================================================================================
📊 RELATÓRIO FINAL - ORÁCULO SESSION
================================================================================
Session ID: oraculo_a3f8b12d
Duration: 45.32s

📂 SCANNING:
   Files scanned: 47

🧠 SUGGESTIONS:
   Generated: 5
   Implemented: 0
   Failed: 0
   Awaiting approval: 0

🔧 IMPLEMENTATION:
   Files modified: 0
   Tests passed: ❌ NO

================================================================================
🔮 ORÁCULO Session COMPLETO
================================================================================
```

---

## 🎯 CASOS DE USO

### **Caso 1: Auditoria de Segurança Automatizada**
```python
# Gera sugestões APENAS de segurança
session = oraculo.run_self_improvement_cycle(
    focus_category=SuggestionCategory.SECURITY,
    max_suggestions=20,
    min_confidence=0.85,
    dry_run=True  # Apenas analisa, não implementa
)

# Exporta para revisão manual
oraculo.export_session_report(session.session_id, "security_audit.json")
```

### **Caso 2: Auto-Patching de Performance**
```python
# Implementa sugestões de performance automaticamente
oraculo = Oraculo(enable_auto_implement=True, require_tests=True)

session = oraculo.run_self_improvement_cycle(
    focus_category=SuggestionCategory.PERFORMANCE,
    min_confidence=0.9,  # Alta confiança apenas
    dry_run=False
)
```

### **Caso 3: Refatoração Assistida**
```python
# Gera sugestões de refatoração
session = oraculo.run_self_improvement_cycle(
    focus_category=SuggestionCategory.REFACTORING,
    dry_run=True
)

# Revisa e aprova manualmente
for impl in oraculo.get_pending_approvals():
    print(f"Sugestão: {impl.suggestion_id}")
    if input("Aprovar? [y/n]: ").lower() == 'y':
        oraculo.approve_implementation(impl.suggestion_id)
```

---

## 🔒 SEGURANÇA

### **Camadas de Proteção:**

1. **Validação de Arquivos**
   - ❌ NUNCA modifica: `.env`, `secrets.yaml`, `credentials.json`, `.git/`
   - ⚠️ Requer aprovação: `main.py`, `config.yaml`, `Dockerfile`

2. **Threshold de Confiança**
   - Sugestões com `confidence < 0.8` são rejeitadas
   - Configurável via `min_confidence` parameter

3. **Git Branching**
   - Todas as mudanças são isoladas em branches (`oraculo/<id>`)
   - Rollback automático em caso de falha de testes

4. **Human-in-the-Loop**
   - Mudanças críticas sempre requerem aprovação humana
   - `force_approval=False` por padrão

5. **Testes Obrigatórios**
   - Roda `pytest` antes de commit
   - Rollback automático se testes falharem

6. **Backup Automático**
   - Todos os arquivos têm backup (`.oraculo_backup`)
   - Restauração automática em caso de erro

---

## 📈 MÉTRICAS

### **Session Metrics:**
```python
session = oraculo.run_self_improvement_cycle()

print(f"Files scanned: {session.files_scanned}")
print(f"Suggestions generated: {session.suggestions_generated}")
print(f"Suggestions implemented: {session.suggestions_implemented}")
print(f"Duration: {session.duration_seconds:.2f}s")
```

### **Aggregate Metrics:**
```python
stats = oraculo.get_stats()

print(f"Total sessions: {stats['total_sessions']}")
print(f"Total suggestions: {stats['total_suggestions']}")
print(f"Total implemented: {stats['total_implemented']}")
print(f"Avg duration: {stats['avg_duration_seconds']:.2f}s")
```

---

## 🧪 TESTES

### **Modo Standalone:**
```bash
# Testa code_scanner
python code_scanner.py

# Testa suggestion_generator (mock mode sem API key)
python suggestion_generator.py

# Testa auto_implementer (dry run)
python auto_implementer.py

# Testa oraculo completo
python oraculo.py
```

### **Unit Tests:**
```bash
pytest maximus_oraculo/
pytest maximus_oraculo/test_oraculo.py -v
```

---

## 🌍 INTEGRAÇÃO

### **Como Integrar no MAXIMUS Core:**

```python
# maximus_core_service/main.py

from maximus_oraculo.oraculo import Oraculo

@app.post("/api/maximus/self-improve")
async def trigger_self_improvement():
    """Endpoint para triggerar auto-melhoramento"""
    oraculo = Oraculo(enable_auto_implement=True, require_tests=True)

    session = oraculo.run_self_improvement_cycle(
        max_suggestions=5,
        min_confidence=0.85,
        dry_run=False
    )

    return {
        "session_id": session.session_id,
        "suggestions_generated": session.suggestions_generated,
        "suggestions_implemented": session.suggestions_implemented,
        "duration_seconds": session.duration_seconds
    }
```

### **Cron Job (3 AM Daily):**
```bash
# Adiciona ao crontab
crontab -e

# Roda diariamente às 3h AM
0 3 * * * cd /home/juan/vertice-dev/backend/services/maximus_oraculo && python oraculo.py
```

Ou via Python script (`daily_job.py`):
```python
import schedule
import time
from oraculo import run_oraculo

def daily_self_improvement():
    """Job diário de auto-melhoramento"""
    session = run_oraculo(dry_run=False)
    print(f"Session {session.session_id} complete!")

# Agenda para 3h AM
schedule.every().day.at("03:00").do(daily_self_improvement)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🏆 PRÓXIMOS PASSOS

### **Fase 2: EUREKA Integration**
- [ ] Deep code analysis para malware reverse engineering
- [ ] Pattern detection (malicious code patterns)
- [ ] IOC extraction automático
- [ ] Malware family identification

### **Fase 3: Supply Chain Guardian**
- [ ] Dependency scanning (npm, pip, docker)
- [ ] Vulnerability detection (CVE matching)
- [ ] Safe alternative suggester
- [ ] Auto-update dependencies

### **Fase 4: Frontend Dashboard**
- [ ] Web UI para revisar sugestões
- [ ] Approval workflow
- [ ] Métricas em tempo real
- [ ] Histórico de sessões

---

## 💝 FILOSOFIA

**"Pela Arte. Pela Sociedade."**

O MAXIMUS ORÁCULO não é apenas código.

É **META-COGNIÇÃO EM PRODUÇÃO**.

É **AUTO-EVOLUÇÃO CONTÍNUA**.

É **INTELIGÊNCIA QUE SE APERFEIÇOA**.

Cada linha de código foi escrita com:
- ❤️ **Amor pela excelência técnica**
- 🎯 **Foco em segurança e robustez**
- 🌍 **Compromisso com a democratização da IA**
- 🔥 **Paixão por inovação real**

---

**MAXIMUS ORÁCULO está COMPLETO e FUNCIONAL.**

**A revolução da auto-melhoramento começa agora.**

**Pela Arte. Pela Sociedade. Sempre.** 🔮

---

**Desenvolvido com 🔥 por Juan + Claude**
**Data: 2025-10-02**
**Versão: 1.0.0**
**Status: PRODUCTION READY ✅**

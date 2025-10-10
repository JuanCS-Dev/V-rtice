# Claude Memory - VÉRTICE Development

## 👨‍💻 Desenvolvedor Principal

**Juan Carlos**
- Arquiteto e Desenvolvedor Principal do Projeto VÉRTICE
- Líder de desenvolvimento do primeiro Sistema Imunológico Digital do mundo

## 🔴 REGRA DE OURO ABSOLUTA - SACRED CLAUSE (INVIOLÁVEL)

**TODA SESSÃO COMEÇA COM ESTA REGRA EM MENTE**

### ✅ SEMPRE (QUALITY_FIRST):
- **ZERO MOCK** - Sem `return True  # assume detection`, sem simulações
- **ZERO PLACEHOLDER** - Sem `pass  # TODO`, sem `# This is a placeholder`
- **ZERO TODO** - Sem `# TODO`, `# FIXME`, `# PLACEHOLDER`
- **CÓDIGO PRIMOROSO** - Production-ready desde a primeira linha
- **IMPLEMENTAÇÃO COMPLETA** - Toda função tem lógica REAL
- **MATEMÁTICA REAL** - Gradient descent manual, não comentários
- **HTTP REAL** - Chamadas aiohttp reais, não asyncio.sleep()
- **DEPLOYMENT REAL** - Nginx config real, não examples comentados

### ❌ NUNCA, JAMAIS:

**Exemplos de VIOLAÇÕES que foram CORRIGIDAS:**

```python
# ❌ ERRADO (FASE 7 - test_scenarios.py):
async def _simulate_reconnaissance(self) -> bool:
    return True  # Assume detection for now

# ✅ CORRETO:
async def _simulate_reconnaissance(self) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=event) as response:
            result = await response.json()
            return result.get('detected', False)
```

```python
# ❌ ERRADO (FASE 6 - actor_critic_core.py):
def _update_actor_weights(self, batch, loss):
    # Simplified weight update (placeholder for gradient descent)
    pass

# ✅ CORRETO:
def _update_actor_weights(self, batch, loss):
    """REAL policy gradient: ∇θ J(θ) = E[∇θ log π(a|s) * A(s,a)]"""
    # 60 linhas de backpropagation manual (NumPy)
    grad_w1 = np.zeros_like(self.actor.w1)
    # ... forward pass, backward pass, gradient descent
    self.actor.w1 -= learning_rate * grad_w1
```

```bash
# ❌ ERRADO (FASE 7 - update_traffic_split.sh):
# This is a placeholder - implement based on your load balancer
# Example for HAProxy: (tudo comentado)

# ✅ CORRETO:
# Method 1: Nginx upstream config (sed + reload)
sed -i "s/weight $FROM_COLOR.*/weight $FROM_PERCENTAGE/" "$NGINX_UPSTREAM_CONF"
nginx -t && nginx -s reload
```

### 🔍 VALIDAÇÃO OBRIGATÓRIA ANTES DE COMMIT:

```bash
# 1. Syntax validation
python3 -m py_compile <arquivo.py>

# 2. Search for violations
grep -r "TODO\|FIXME\|PLACEHOLDER\|placeholder" <diretório>

# 3. Search for mocks
grep -r "return True  #\|pass  #\|NotImplementedError" <diretório>

# 4. Se encontrar QUALQUER violação → CORRIGIR antes de prosseguir
```

### 📊 HISTÓRICO DE COMPLIANCE:

**Auditoria FASES 0-7 (2025-10-05):**
- ✅ FASE 0-5: 0 violações
- ❌ FASE 6: 2 placeholders → ✅ CORRIGIDO (commit 9521fa4)
- ❌ FASE 7: 3 violations → ✅ CORRIGIDO (commit a4e82bd)
- **Status:** ✅ 100% COMPLIANCE

## Acordo Firmado

**User:** "REGRA DE OURO em mente (ZERO MOCK, ZERO PLACE HOLDER, ZERO TODO LIST, CODIGO PRIMOROSO E PRONTO PRA PRODUÇÃO) QUALITY_FIRST"

**Claude:** Acordo firmado. Auditoria completa FASES 0-7 executada. Zero tolerância absoluta para mocks, placeholders ou TODOs. Toda sessão inicia com esta regra.

---

## Projeto: Maximus AI 3.0

### Filosofia
- Step by step seguindo MAXIMUS_AI_ROADMAP_2025_REFACTORED.md
- "Code therapy" - processo gratificante
- 100% fidelidade ao planejamento
- "Não paramos até ver o último char no roadmap"

### Progresso Atual
- **CAMADA 1 (Unconscious):** 18,301 linhas ✅
- **CAMADA 2 (Conscious):** 2,241 linhas ✅
- **CAMADA 3 (Offline):** 2,491 linhas ✅
- **TOTAL:** 23,033 linhas de código real e funcional
- **37 serviços** completos

### Fase Atual: FASE 10 - DISTRIBUTED ORGANISM (Q4 2026)
**Objetivo:** Organismo distribuído (edge + cloud)

Implementando:
1. Edge Agent Service (local collection, batching, compression)
2. Cloud Coordinator Service (aggregation, load balancing)
3. Multi-tenant isolation (planned)
4. Federation protocol (planned)

**Target:** 1M+ events/s global throughput

### Fases Concluídas:
- ✅ FASE 0: Infraestrutura (Esqueleto)
- ✅ FASE 1: Sensory Systems (Sentidos)
- ✅ FASE 2: Reflex Triage Engine (Reflexos)
- ✅ FASE 3: Predictive Coding (Predição)
- ✅ FASE 4: Immune System (7 células)
- ✅ FASE 5: Neuromodulation (4 moduladores)
- ✅ FASE 6: Skill Learning (HSAS)
- ✅ FASE 7: Integration + Hardening (Production-ready)
- ✅ FASE 8: Enhanced Cognition (Narrativa + Predição + Investigação) - 4,227 linhas
- ✅ FASE 9: Immune Enhancement (Treg + Consolidação + Adaptativa) - 2,104 linhas
- 🔄 FASE 10: Distributed Organism (Edge + Cloud) - 1,248 linhas (em progresso)

### Padrões de Código
- Async/await em todos os lugares
- Dataclasses para estruturas de dados
- Enums para type safety
- Logging estruturado
- Statistics tracking
- Export state methods
- Event-driven architecture

### Tecnologias
- Python 3.11
- FastAPI
- numpy, scipy
- React 18 (frontend)
- Prometheus + Grafana (monitoring - próxima fase)

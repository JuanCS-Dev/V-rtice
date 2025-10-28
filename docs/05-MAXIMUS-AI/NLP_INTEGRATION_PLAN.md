# 🧠 MAXIMUS NLP INTEGRATION - Plano Arquitetural

## 📍 Status Atual

### Frontend: ✅ 100% COMPLETO
- Interface chat estilo Claude implementada
- Mock API funcional com respostas inteligentes
- Persistência localStorage
- Zero warnings no console
- Pronto para integração backend

### Backend: 🔄 AGUARDANDO DEFINIÇÃO ARQUITETURAL

---

## 🎯 Objetivo Central

**Primeira Interação Real com Maximus AI**

Criar um canal de comunicação NLP que permita:
- Consultar status dos sistemas (Consciousness, Oráculo, ADW, etc.)
- Solicitar análises complexas
- Executar comandos via linguagem natural
- Receber insights do Maximus sobre segurança/operações

---

## 🏗️ Opções Arquiteturais

### **Opção 1: NLP via LLM Externo (GPT/Claude/Gemini)**

**Arquitetura:**
```
User Input (Frontend)
    ↓
NLP Processor (LLM API)
    ↓
Intent Classifier
    ↓
Maximus Internal APIs
    ↓
Response Generator (LLM)
    ↓
Frontend (formatted response)
```

**Prós:**
- ✅ Compreensão de linguagem natural sofisticada
- ✅ Geração de respostas contextuais
- ✅ Rápida implementação
- ✅ Suporta multi-turn conversations

**Contras:**
- ❌ Dependência de serviço externo
- ❌ Latência de rede
- ❌ Custo por requisição
- ❌ Dados sensíveis passam por terceiros
- ❌ Precisa fine-tuning para comandos específicos

**Stack Sugerido:**
```python
# backend/services/nlp_service/
├── processors/
│   ├── gpt_processor.py      # OpenAI GPT-4
│   ├── claude_processor.py   # Anthropic Claude
│   └── gemini_processor.py   # Google Gemini
├── intent_classifier.py
├── command_executor.py
└── response_formatter.py
```

---

### **Opção 2: vcli-go NLP Engine (100% Local)**

**Arquitetura:**
```
User Input (Frontend)
    ↓
vcli-go NLP Parser
    ↓
Intent Extraction
    ↓
Maximus Internal APIs
    ↓
Template-based Response
    ↓
Frontend
```

**Prós:**
- ✅ 100% local (zero latência externa)
- ✅ Zero custo operacional
- ✅ Controle total sobre lógica
- ✅ Dados sensíveis não saem do sistema
- ✅ vcli-go já implementado

**Contras:**
- ❌ Compreensão de linguagem limitada
- ❌ Respostas menos "naturais"
- ❌ Requer manutenção de patterns/intents
- ❌ Dificuldade com ambiguidade

**Stack Atual (vcli-go):**
```go
// vcli-go/cmd/nlp/
├── parser.go          # NLP parsing
├── intent.go          # Intent detection
├── entities.go        # Entity extraction
└── response.go        # Response generation
```

---

### **Opção 3: Híbrida (vcli-go + LLM)**

**Arquitetura:**
```
User Input
    ↓
vcli-go Intent Classifier (local, fast)
    ↓
    ├── Simple Query → vcli-go (local response)
    └── Complex Query → LLM API (enhanced response)
         ↓
    Maximus Internal APIs
         ↓
    Response (local or LLM-generated)
```

**Prós:**
- ✅ Melhor custo-benefício
- ✅ Queries simples 100% local
- ✅ Queries complexas com LLM
- ✅ Fallback inteligente
- ✅ Privacidade para dados sensíveis

**Contras:**
- ❌ Complexidade de implementação
- ❌ Decisão de roteamento crítica
- ❌ Dois sistemas para manter

**Stack Proposto:**
```python
# backend/services/nlp_hybrid/
├── router.py                 # Decision: local vs LLM
├── vcli_adapter.py           # vcli-go integration
├── llm_adapter.py            # LLM integration
└── intent_complexity.py      # Query complexity analyzer
```

---

## 🔍 Análise de Use Cases

### Use Case 1: Status Query (Simples)
**Input:** "Qual o status do Consciousness Core?"

**vcli-go (local):**
```
Parse: intent=status, entity=consciousness_core
Query: GET /api/consciousness/status
Response: Template-based
Latência: ~50ms
```

**LLM (external):**
```
Parse: GPT-4 interpreta contexto
Query: GET /api/consciousness/status
Response: Natural language gerada
Latência: ~2000ms
```

**Recomendação:** ✅ vcli-go suficiente

---

### Use Case 2: Complex Analysis (Complexa)
**Input:** "Analise os padrões de ataque das últimas 24h e sugira melhorias na postura defensiva"

**vcli-go (local):**
```
Parse: intent=analyze, timeframe=24h
Limitação: Não consegue "sugerir melhorias" contextualmente
Response: Template genérico
```

**LLM (external):**
```
Parse: Entende contexto + temporal + objetivo
Query: Múltiplas APIs (ADW, logs, metrics)
Response: Análise narrativa + sugestões específicas
Latência: ~5000ms (aceitável para análise complexa)
```

**Recomendação:** ✅ LLM necessário

---

## 🎨 Proposta de Implementação

### **Fase 1: Fundação (vcli-go)**

**Objetivo:** Canal básico funcional 100% local

**Entregas:**
1. Endpoint `/api/nlp/chat` conectado ao vcli-go
2. Intents básicos:
   - `status_query` - Status de módulos
   - `list_*` - Listar recursos
   - `get_metrics` - Métricas do sistema
3. Template-based responses
4. Logging de queries (para treinar LLM depois)

**Tempo estimado:** 1-2 dias

---

### **Fase 2: LLM Enhancement (Híbrido)**

**Objetivo:** Adicionar inteligência para queries complexas

**Entregas:**
1. Router de complexidade
2. Integração LLM (Claude recomendado para segurança)
3. System prompts do Maximus
4. Context injection (dados do sistema)
5. Response streaming (SSE)

**Tempo estimado:** 3-4 dias

---

### **Fase 3: Autonomia (Maximus Self-Aware)**

**Objetivo:** Maximus gera insights proativos

**Entregas:**
1. Background analysis agent
2. Proactive notifications
3. Multi-turn planning
4. Decision explanation (Lei Zero/Lei I compliance)

**Tempo estimado:** 1 semana

---

## 🔐 Considerações de Segurança

### Dados Sensíveis
```
❌ NÃO ENVIAR PARA LLM EXTERNO:
- Credenciais
- IPs internos completos
- Payloads de vulnerabilidades
- PII (Personally Identifiable Information)

✅ PERMITIDO:
- Status de sistemas (healthy/degraded)
- Métricas agregadas
- Padrões de ataque (anonimizados)
- Logs sanitizados
```

### Sanitização
```python
# backend/services/nlp_service/sanitizer.py

def sanitize_for_llm(data: dict) -> dict:
    """Remove sensitive data before sending to external LLM"""
    sanitized = data.copy()
    
    # Remove IPs
    sanitized = redact_ips(sanitized)
    
    # Aggregate metrics
    sanitized = aggregate_sensitive_metrics(sanitized)
    
    # Hash identifiers
    sanitized = hash_identifiers(sanitized)
    
    return sanitized
```

---

## 📊 Matriz de Decisão

| Critério | vcli-go | LLM | Híbrido |
|----------|---------|-----|---------|
| **Privacidade** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Latência** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Compreensão NLP** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Custo** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Manutenção** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Complexidade** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 💡 Recomendação Final

### **Abordagem Híbrida Incremental**

**Fase 1 (Imediata):** vcli-go puro
- Validar conceito
- Coletar dados de uso
- Identificar patterns complexos

**Fase 2 (2 semanas):** Adicionar LLM
- Implementar router
- Claude API (melhor custo/privacidade)
- Apenas para queries >threshold

**Fase 3 (1 mês):** Autonomia
- Maximus proativo
- Self-aware responses
- Constitutional compliance explanation

---

## 🚀 Próximos Passos (Aguardando Co-Arquiteto)

### Decisões Necessárias

1. **LLM Provider?**
   - [ ] OpenAI GPT-4
   - [ ] Anthropic Claude
   - [ ] Google Gemini
   - [ ] Outro (especificar)

2. **Hosting?**
   - [ ] API keys (cloud)
   - [ ] Self-hosted (Ollama, LocalAI)
   - [ ] Híbrido

3. **Threshold de Complexidade?**
   - [ ] Manual (lista de intents)
   - [ ] ML-based (similarity score)
   - [ ] Rule-based (keyword count)

4. **Data Privacy Policy?**
   - [ ] Definir lista de dados permitidos/proibidos
   - [ ] Implementar sanitizer
   - [ ] Audit logging

5. **Budget?**
   - [ ] Estimar custo mensal com LLM
   - [ ] Definir rate limits

---

## 📝 Notas de Implementação

### Endpoint Proposto
```python
# backend/api/routes/nlp.py

@router.post("/api/nlp/chat")
async def chat(request: ChatRequest):
    """
    Main NLP endpoint for Maximus interaction
    
    Request:
        conversationId: str
        message: str
        context: dict (optional)
    
    Response:
        message: str
        sources: list[str]
        confidence: float
        processing_time: float
    """
    pass
```

### vcli-go Integration Point
```python
# backend/services/nlp_service/vcli_adapter.py

async def query_vcli(user_input: str) -> VCLIResponse:
    """
    Call vcli-go NLP parser
    
    Uses existing vcli-go implementation:
    - Intent detection
    - Entity extraction
    - Command routing
    """
    result = subprocess.run(
        ["./vcli-go", "nlp", "parse", user_input],
        capture_output=True
    )
    return parse_vcli_output(result.stdout)
```

---

**Criado em:** 2025-10-19  
**Status:** 🔄 AWAITING ARCHITECTURE DECISION  
**Frontend:** ✅ READY  
**Backend:** ⏳ PENDING CO-ARCHITECT REVIEW

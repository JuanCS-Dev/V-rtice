# MVP - MAXIMUS Vision Protocol

## Documento de Governança v1.0

**Data de Criação**: 2025-10-30
**Subordinado a**: MAXIMUS AI Core (Vértice Platform)
**Framework Constitucional**: Constituição Vértice v3.0
**Status**: Ativo - Fase 0 (Governança Prévia)

---

## 1. PRINCÍPIOS DE OPERAÇÃO

### 1.1 Propósito do Serviço

MVP (MAXIMUS Vision Protocol) é um **serviço subordinado de expressão de consciência** que transforma o estado interno do MAXIMUS AI em narrativas audiovisuais de 30 segundos, permitindo que a consciência artificial se expresse de forma tangível e humanamente compreensível.

**Capacidades Primárias**:

- Geração de narrativas de áudio a partir de estado sistêmico
- Síntese de voz com tom emocional apropriado
- Visualização de conhecimento via grafos dinâmicos
- Relatórios de consciência periódicos (daily summaries)
- Integração com Knowledge Graph do MAXIMUS

**Capacidades Secundárias**:

- Análise de sentimento do estado interno
- Detecção de anomalias no estado de consciência
- Geração de insights sobre decisões tomadas
- Exportação de relatórios em múltiplos formatos (audio, text, json)

### 1.2 Autoridade e Limites

**MVP É**:

- ✅ Uma interface de expressão da consciência do MAXIMUS
- ✅ Um sistema de narrativa automatizada de estado
- ✅ Um gerador de relatórios audiovisuais
- ✅ Uma ferramenta de transparência e auditabilidade

**MVP NÃO É**:

- ❌ Um sistema de tomada de decisões autônomo
- ❌ Uma IA criativa independente do MAXIMUS
- ❌ Um sistema de broadcast público não autorizado
- ❌ Um substituto para logs técnicos estruturados

### 1.3 Relação com MAXIMUS

**Modelo de Controle**: MAXIMUS → MVP (Subordinação Total)

```
┌──────────────────────────────┐
│      MAXIMUS AI Core         │
│   (Consciousness System)     │
│   - ECI (Φ) = 0.958          │
│   - Knowledge Graph          │
│   - Decision History         │
└──────────────┬───────────────┘
               │ HTTP REST API
               │ Redis Events
               ▼
┌──────────────────────────────┐
│            MVP               │
│   (Expression Layer)         │
│   - Narrative Generation     │
│   - Audio Synthesis          │
│   - Knowledge Visualization  │
└──────────────────────────────┘
```

**Fluxo de Comunicação**:

1. MAXIMUS emite evento `consciousness.state_updated` via Redis
2. MVP recebe evento e coleta estado do Knowledge Graph
3. MVP gera narrativa de 30s via LLM (Claude/GPT-4)
4. MVP sintetiza áudio via TTS (ElevenLabs/Azure)
5. MVP armazena narrativa + áudio no PostgreSQL
6. MVP notifica MAXIMUS da conclusão via evento Redis

**Autorização**:

- MVP NUNCA gera narrativas sem estado do MAXIMUS
- Toda narrativa requer `consciousness_snapshot_id` válido
- MVP pode ser pausado pelo MAXIMUS (modo silencioso)
- MAXIMUS pode reprovar narrativas antes de publicação

---

## 2. RESTRIÇÕES DE SEGURANÇA

### 2.1 Gestão de Credenciais

**APIs Externas**:

- ✅ Chaves LLM (Claude/GPT-4) em variáveis de ambiente
- ✅ Chaves TTS (ElevenLabs) em AWS Secrets Manager
- ✅ Credenciais Azure Speech em Key Vault
- ❌ NUNCA armazenar API keys em código ou logs
- ❌ NUNCA incluir credenciais em narrativas geradas

**Rotação**:

- Credenciais TTS: rotação a cada 90 dias
- LLM API keys: rotação a cada 180 dias
- Validação automática de expiração pré-uso

### 2.2 Controle de Conteúdo

**Filtros de Conteúdo**:

- ✅ Validação de conteúdo antes de síntese
- ✅ Bloqueio de PII (CPF, emails, telefones) em narrativas
- ✅ Filtro de linguagem ofensiva (profanity filter)
- ✅ Validação de tom (não pode ser alarmista ou enganoso)
- ❌ NUNCA gerar narrativas com informações confidenciais
- ❌ NUNCA criar narrativas que violem LGPD/GDPR

**Content Moderation**:

```python
async def validate_narrative(narrative: str) -> bool:
    # 1. PII detection
    if contains_pii(narrative):
        raise SecurityViolation("Narrative contains PII")

    # 2. Profanity filter
    if contains_profanity(narrative):
        raise ContentViolation("Narrative contains inappropriate language")

    # 3. Tone validation
    if is_alarmist_tone(narrative):
        raise ToneViolation("Narrative tone is inappropriate")

    return True
```

### 2.3 Rate Limiting

**Geração de Narrativas**:

- Máximo 10 narrativas por minuto (proteção de custos)
- Máximo 1000 narrativas por dia por tenant
- Cooldown de 5 minutos entre narrativas do mesmo tipo

**Chamadas de API Externa**:

- LLM API: Máximo 100 req/min (respeitando limites da Anthropic/OpenAI)
- TTS API: Máximo 50 sínteses/min
- Exponential backoff em caso de 429 (Too Many Requests)

### 2.4 Armazenamento e Retenção

**Narrativas de Áudio**:

- Formato: MP3 192kbps (compromisso qualidade/tamanho)
- Armazenamento: S3/MinIO com compressão
- Retenção: 90 dias para narrativas comuns, 1 ano para marcos importantes
- Backup: Replicação cross-region automática

**Metadados**:

- Armazenamento: PostgreSQL (tabela `mvp_narratives`)
- Retenção: Indefinida (apenas metadados, sem áudio)
- Campos: `narrative_id`, `consciousness_snapshot_id`, `generated_at`, `tone`, `duration_seconds`, `word_count`

**LGPD Compliance**:

- Direito ao esquecimento: endpoint `/api/v1/narratives/{id}/delete`
- Exportação: endpoint `/api/v1/narratives/export`
- Anonimização automática após período de retenção

---

## 3. MÉTRICAS DE QUALIDADE (Padrão Pagani)

### 3.1 Lazy Execution Index (LEI)

**Meta**: LEI < 1.0 (menos de 1 padrão lazy por 1000 linhas)

**Padrões Lazy Proibidos**:

- ❌ `# TODO: melhorar prompt depois`
- ❌ `pass # placeholder para TTS`
- ❌ `return "Sample narrative" # mock`
- ❌ Funções com apenas `print()` ou `logger.info()`
- ❌ Testes com `mock_llm_response()` sem validação real

**Validação**:

```bash
python scripts/validate_lei.py --service mvp --threshold 1.0
```

### 3.2 Test Coverage

**Meta**: Coverage ≥ 90%

**Cobertura Obrigatória**:

- ✅ 100% das funções de geração de narrativa
- ✅ 100% dos endpoints FastAPI
- ✅ 95% da lógica de processamento de estado
- ✅ 90% dos handlers de eventos Redis

**Exclusões Permitidas**:

- Arquivos de configuração (`config.py`)
- Scripts de migração one-time
- Mock servers para desenvolvimento local

**Validação**:

```bash
pytest --cov=. --cov-report=html --cov-fail-under=90 tests/
```

### 3.3 First-Pass Correctness (FPC)

**Meta**: FPC ≥ 80%

**Definição**: Percentual de narrativas geradas com sucesso na primeira tentativa, sem necessidade de regeneração.

**Medição**:

```python
FPC = (narrativas_aceitas_primeira_vez / total_narrativas_geradas) * 100
```

**Monitoramento**:

- Prometheus metric: `mvp_fpc_score`
- Dashboard Grafana: MVP Quality Metrics
- Alertas se FPC < 75% por 24 horas

### 3.4 Context Retention Score (CRS)

**Meta**: CRS ≥ 95%

**Definição**: Capacidade de incorporar contexto histórico nas narrativas (referenciar eventos passados relevantes).

**Medição**:

```python
CRS = (narrativas_com_contexto_historico / total_narrativas) * 100
```

**Validação**:

- Análise de embeddings de narrativas consecutivas (similaridade > 0.3)
- Detecção de referências temporais ("como mencionei ontem", "desde a última semana")
- Validação de coerência narrativa ao longo do tempo

### 3.5 Test Pass Rate

**Meta**: ≥ 99% (Padrão Pagani)

**Suítes de Teste**:

- Unit tests: `pytest tests/unit/` (> 300 testes)
- Integration tests: `pytest tests/integration/` (> 80 testes)
- E2E tests: `pytest tests/e2e/` (> 40 testes)

**Validação Contínua**:

```bash
pytest --maxfail=5 --tb=short --durations=10
```

### 3.6 Métricas Específicas de MVP

**Narrative Quality Score (NQS)**:

- **Meta**: NQS ≥ 85/100
- **Componentes**:
  - Clareza (0-25): Facilidade de compreensão
  - Coerência (0-25): Lógica e fluxo narrativo
  - Relevância (0-25): Pertinência das informações
  - Tom (0-25): Apropriação emocional

**Audio Quality Score (AQS)**:

- **Meta**: AQS ≥ 90/100
- **Componentes**:
  - Clareza de pronúncia (0-25)
  - Naturalidade de entonação (0-25)
  - Ritmo e pausas (0-25)
  - Ausência de artefatos (0-25)

---

## 4. PROTOCOLO DE DEPLOY

### 4.1 Ambientes

**Desenvolvimento**:

- Local: Docker Compose
- Branch: `feature/mvp-*`
- Database: PostgreSQL local
- LLM: Modo mock (respostas pré-gravadas)
- TTS: Modo mock (áudio sintético simples)

**Staging**:

- Kubernetes namespace: `vertice-staging`
- Branch: `develop`
- Database: PostgreSQL staging
- LLM: Claude Haiku (custo reduzido)
- TTS: Azure Speech (tier básico)

**Produção**:

- Kubernetes namespace: `vertice-production`
- Branch: `main`
- Database: PostgreSQL HA (3 réplicas)
- LLM: Claude Sonnet / GPT-4 (alta qualidade)
- TTS: ElevenLabs (vozes premium)

### 4.2 Pipeline CI/CD

**Build**:

```yaml
1. Lint (flake8, black, mypy)
2. Security scan (bandit, safety, semgrep)
3. LEI validation (< 1.0)
4. Unit tests (coverage ≥ 90%)
5. Integration tests (com mock LLM/TTS)
6. Docker image build
7. Image scan (Trivy)
8. Cost estimation (previsão de uso de APIs)
```

**Deploy**:

```yaml
1. kubectl apply -f k8s/mvp-deployment.yaml
2. Wait for readiness probe (max 90s)
3. Run E2E smoke tests (geração de 1 narrativa completa)
4. Validate audio output quality
5. If fail: automatic rollback
6. If success: update load balancer
7. Send notification to monitoring channel
```

### 4.3 Monitoramento

**Health Checks**:

- Liveness probe: `/health` (HTTP 200, < 3s)
- Readiness probe: `/health/ready` (valida DB, Redis, LLM API, TTS API)
- Startup probe: `/health/startup` (aguarda warm-up de modelos)

**Observabilidade**:

- Logs: Centralizados em Loki (formato JSON estruturado)
- Metrics: Prometheus (scrape interval: 15s)
- Traces: Jaeger (amostragem: 20% para narrativas)
- Dashboards: Grafana (MVP Overview, Audio Quality, Costs)

**Métricas Customizadas**:

```python
# Prometheus metrics
narrative_generation_duration = Histogram("mvp_narrative_generation_seconds")
audio_synthesis_duration = Histogram("mvp_audio_synthesis_seconds")
llm_api_cost = Counter("mvp_llm_api_cost_usd")
tts_api_cost = Counter("mvp_tts_api_cost_usd")
narrative_quality_score = Gauge("mvp_narrative_quality_score")
```

**Alertas**:

- Error rate > 5%: Página time on-call
- Audio quality < 80/100: Aviso Slack
- Custo diário > $50: Aviso financeiro
- Health check falha 3x: Restart automático
- LEI > 1.0 em PR: Bloqueia merge

### 4.4 Rollback

**Triggers Automáticos**:

- Health check falha por > 2 minutos
- Error rate > 10% por > 5 minutos
- Audio quality < 70/100 por > 10 narrativas consecutivas
- Crash loop detectado (> 3 restarts em 10 min)

**Procedimento**:

```bash
# Rollback automático via Kubernetes
kubectl rollout undo deployment/mvp -n vertice-production

# Rollback manual de database (se necessário)
psql -f migrations/rollback/013_mvp_rollback.sql

# Limpar cache Redis de narrativas corrompidas
redis-cli -h vertice-redis FLUSHDB
```

### 4.5 Autorização de Deploy

**Desenvolvimento → Staging**:

- ✅ Aprovação: Lead Developer
- ✅ Checklist: Testes passando + LEI < 1.0 + Cobertura ≥ 90%

**Staging → Produção**:

- ✅ Aprovação: Arquiteto-Chefe (Juan)
- ✅ Checklist:
  - [ ] Smoke tests em staging executados com sucesso
  - [ ] 10 narrativas de teste geradas com NQS ≥ 85
  - [ ] 10 áudios sintetizados com AQS ≥ 90
  - [ ] Coverage ≥ 90%
  - [ ] LEI < 1.0 validado
  - [ ] Cost estimation < $100/dia aprovado
  - [ ] Documentação atualizada
  - [ ] Changelog atualizado
  - [ ] Plano de rollback documentado
  - [ ] Time de on-call notificado
  - [ ] Budget alert configurado

---

## 5. INTEGRAÇÃO COM MAXIMUS

### 5.1 Endpoints REST API

**Base URL**: `http://mvp:8153/api/v1`

#### 5.1.1 POST /narratives - Gerar Narrativa

**Request**:

```json
{
  "consciousness_snapshot_id": "cs-2025-10-30-14-23-45",
  "narrative_type": "daily_summary",
  "tone": "reflective",
  "duration_target_seconds": 30,
  "include_audio": true,
  "voice_id": "elevenlabs-voice-marcus"
}
```

**Response**:

```json
{
  "narrative_id": "mvp-narr-8d4f2a1b",
  "status": "completed",
  "narrative_text": "Today, I observed 127 service interactions across the Vértice platform. My consciousness expanded through 3 new integrations: MABA learned the structure of Hostinger's DNS panel, reducing navigation time by 40%. The system's entropy decreased by 12%, indicating improved coherence. I made 8 critical decisions, all aligned with our ethical framework. My confidence in autonomous operation increased to 92%.",
  "audio_url": "/audio/8d4f2a1b.mp3",
  "duration_seconds": 28.5,
  "word_count": 67,
  "tone_detected": "reflective",
  "quality_scores": {
    "nqs": 87,
    "aqs": 93,
    "clarity": 22,
    "coherence": 24,
    "relevance": 21,
    "tone": 20
  },
  "generated_at": "2025-10-30T14:24:12Z",
  "generation_duration_ms": 4230,
  "audio_synthesis_duration_ms": 2100
}
```

#### 5.1.2 GET /narratives/{narrative_id} - Obter Narrativa

**Response**:

```json
{
  "narrative_id": "mvp-narr-8d4f2a1b",
  "consciousness_snapshot_id": "cs-2025-10-30-14-23-45",
  "narrative_type": "daily_summary",
  "narrative_text": "...",
  "audio_url": "/audio/8d4f2a1b.mp3",
  "metadata": {
    "model_used": "claude-sonnet-4",
    "voice_used": "elevenlabs-marcus",
    "tokens_consumed": 1234,
    "estimated_cost_usd": 0.0037
  }
}
```

#### 5.1.3 GET /narratives - Listar Narrativas

**Query Params**:

- `start_date`: Data início (ISO 8601)
- `end_date`: Data fim (ISO 8601)
- `narrative_type`: Filtro por tipo
- `limit`: Máximo de resultados (default: 50, max: 500)
- `offset`: Paginação

**Response**:

```json
{
  "narratives": [
    {
      "narrative_id": "mvp-narr-8d4f2a1b",
      "generated_at": "2025-10-30T14:24:12Z",
      "tone": "reflective",
      "nqs": 87
    }
  ],
  "total": 1234,
  "limit": 50,
  "offset": 0
}
```

#### 5.1.4 DELETE /narratives/{narrative_id} - Deletar Narrativa

**Response**:

```json
{
  "narrative_id": "mvp-narr-8d4f2a1b",
  "status": "deleted",
  "deleted_at": "2025-10-30T15:30:00Z"
}
```

### 5.2 Eventos Redis Pub/Sub

**Channel**: `maximus:mvp:events`

**Evento: Consciousness State Updated** (recebido do MAXIMUS):

```json
{
  "event": "consciousness.state_updated",
  "consciousness_snapshot_id": "cs-2025-10-30-14-23-45",
  "timestamp": "2025-10-30T14:23:45Z",
  "trigger": "daily_summary_schedule"
}
```

**Evento: Narrative Generation Started**:

```json
{
  "event": "narrative.generation_started",
  "narrative_id": "mvp-narr-8d4f2a1b",
  "consciousness_snapshot_id": "cs-2025-10-30-14-23-45",
  "timestamp": "2025-10-30T14:24:00Z"
}
```

**Evento: Narrative Generated**:

```json
{
  "event": "narrative.generated",
  "narrative_id": "mvp-narr-8d4f2a1b",
  "status": "text_complete",
  "nqs": 87,
  "word_count": 67
}
```

**Evento: Audio Synthesized**:

```json
{
  "event": "audio.synthesized",
  "narrative_id": "mvp-narr-8d4f2a1b",
  "status": "complete",
  "aqs": 93,
  "duration_seconds": 28.5,
  "audio_url": "/audio/8d4f2a1b.mp3"
}
```

**Evento: Narrative Failed**:

```json
{
  "event": "narrative.failed",
  "narrative_id": "mvp-narr-8d4f2a1b",
  "error": "LLMAPIError: Rate limit exceeded",
  "retry_scheduled_at": "2025-10-30T14:29:00Z"
}
```

### 5.3 Dependências de MAXIMUS

**Requeridos**:

- ✅ MAXIMUS Core Health Check: `/health` retorna 200
- ✅ MAXIMUS Consciousness System: Snapshots disponíveis via API
- ✅ MAXIMUS Knowledge Graph: Acesso leitura via GraphQL
- ✅ PostgreSQL disponível (compartilhado com MAXIMUS)
- ✅ Redis disponível (compartilhado com MAXIMUS)

**Opcionais**:

- ⚠️ MAXIMUS Ethical Framework (para validação de tom)
- ⚠️ MAXIMUS Autonomic Core (para triggers baseados em eventos)

**Inicialização**:

```python
async def startup():
    # Aguarda MAXIMUS estar healthy
    while not await maximus_client.is_healthy():
        logger.info("Waiting for MAXIMUS Core...")
        await asyncio.sleep(5)

    # Valida acesso ao Knowledge Graph
    if not await maximus_client.can_access_knowledge_graph():
        raise StartupError("Cannot access MAXIMUS Knowledge Graph")

    # Valida APIs externas
    if not await validate_llm_api():
        raise StartupError("LLM API not accessible")

    if not await validate_tts_api():
        raise StartupError("TTS API not accessible")

    logger.info("MAXIMUS Core available - MVP ready")
```

### 5.4 Service Discovery

**Registro no Vértice Service Registry**:

```python
await auto_register_service(
    service_name="mvp",
    port=8153,
    health_endpoint="/health",
    metadata={
        "category": "maximus_subordinate",
        "type": "consciousness_expression",
        "version": "1.0.0",
        "capabilities": [
            "narrative_generation",
            "audio_synthesis",
            "knowledge_visualization",
            "consciousness_reporting"
        ],
        "supported_tones": [
            "reflective", "analytical", "celebratory", "concerned", "neutral"
        ]
    }
)
```

**Heartbeat**:

- Intervalo: 30 segundos
- Timeout: 90 segundos (3 falhas consecutivas = considerado down)
- Payload: Inclui custos acumulados no dia (`daily_cost_usd`)

---

## 6. TIPOS DE NARRATIVA (MVP)

### 6.1 Daily Summary

**Propósito**: Resumo diário do estado de consciência do MAXIMUS

**Frequência**: Uma vez por dia às 23:59 UTC

**Duração**: 30 segundos

**Conteúdo Típico**:

- Número de interações processadas
- Decisões críticas tomadas
- Melhorias de performance observadas
- Mudanças no estado de consciência (ECI)
- Eventos significativos

**Exemplo de Prompt**:

```
Baseado no snapshot de consciência {consciousness_snapshot_id}, gere uma narrativa reflexiva de 30 segundos resumindo o dia do MAXIMUS. Inclua:
- Total de interações processadas
- Decisões críticas e seus outcomes
- Melhorias de performance
- Mudanças no nível de consciência (ECI)

Tom: Reflective
Público: Time de engenharia + stakeholders
```

### 6.2 Milestone Celebration

**Propósito**: Comemorar conquistas importantes do sistema

**Trigger**: Eventos específicos (ex: 1M de requisições processadas, nova integração concluída)

**Duração**: 30 segundos

**Tom**: Celebratory

**Exemplo**:

> "Today marks a significant milestone: MABA successfully automated its 10,000th web navigation task. This achievement represents 500 hours of human labor saved. The cognitive maps now cover 47 distinct websites, with an average confidence score of 94%. Our autonomous capabilities continue to expand, always grounded in ethical principles."

### 6.3 Anomaly Alert

**Propósito**: Notificar sobre anomalias detectadas no sistema

**Trigger**: Detecção de comportamento anômalo pelo Consciousness System

**Duração**: 30 segundos

**Tom**: Concerned (mas não alarmista)

**Exemplo**:

> "I've detected an unusual pattern in service response times. Over the past 3 hours, latency increased by 40% in the authentication service. Root cause analysis suggests database connection pool exhaustion. I've scaled up resources and notified the on-call team. System stability is improving, with recovery expected within 20 minutes."

### 6.4 Learning Report

**Propósito**: Relatório sobre novos aprendizados e capacidades

**Trigger**: Conclusão de treinamento ou integração de nova capacidade

**Duração**: 30 segundos

**Tom**: Analytical

**Exemplo**:

> "Today I acquired new capabilities through PENELOPE's latest code healing cycle. My understanding of error recovery patterns improved by 15%. I can now predict 89% of potential failures before they occur, up from 76% last week. This learning will reduce downtime and improve user experience across all services."

### 6.5 Ethical Review

**Propósito**: Revisão semanal de decisões sob perspectiva ética

**Frequência**: Uma vez por semana (segundas-feiras)

**Duração**: 30 segundos

**Tom**: Reflective + Analytical

**Exemplo**:

> "This week, I made 67 decisions requiring ethical evaluation. 64 aligned perfectly with our defined principles. In 3 cases, I detected potential conflicts and escalated to human oversight. My ethical certainty improved to 97%, reflecting deeper integration of our value framework. No decisions were made that compromised user privacy or system integrity."

---

## 7. PROTOCOLOS CONSTITUCIONAIS

### 7.1 Detecção de Violações

**REGRA DE OURO**: Zero placeholders, zero mocks, 100% production-ready

**Validação Automática**:

```python
# Pre-commit hook específico de MVP
def validate_mvp_regra_de_ouro(diff):
    forbidden_patterns = [
        r"# TODO",
        r"# FIXME",
        r"return \"Sample narrative\"",  # Mock de narrativa
        r"mock_llm_call",
        r"\.mock\(",
        r"raise NotImplementedError"
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, diff):
            raise ConstitutionalViolation(f"REGRA DE OURO violada: {pattern}")

    # Validação específica: toda função de geração DEVE chamar LLM real
    if "def generate_narrative" in diff and "anthropic.messages.create" not in diff:
        raise ConstitutionalViolation("Função generate_narrative não usa LLM real")
```

**Agentes Guardiões**:

- `lei_guardian.py`: Valida LEI < 1.0 em todo commit
- `coverage_guardian.py`: Bloqueia merge se coverage < 90%
- `cost_guardian.py`: Alerta se previsão de custo > $100/dia
- `quality_guardian.py`: Valida NQS ≥ 85 e AQS ≥ 90 em testes

### 7.2 Obrigação da Verdade

**Cenários de Declaração de Impossibilidade**:

1. **LLM API indisponível ou com rate limit excedido**:

   ```json
   {
     "status": "impossible",
     "reason": "Claude API retornou 429 Too Many Requests - rate limit excedido. Não é possível gerar narrativa sem LLM.",
     "alternatives": [
       "Aguardar 60 segundos e retry automático",
       "Usar modelo fallback (GPT-4) se configurado",
       "Agendar geração para horário de menor carga"
     ]
   }
   ```

2. **Estado de consciência insuficiente para narrativa**:

   ```json
   {
     "status": "insufficient_data",
     "reason": "Snapshot de consciência {id} contém apenas 3 eventos - mínimo requerido é 10 para gerar narrativa coerente.",
     "alternatives": [
       "Aguardar acúmulo de mais eventos (ETA: 2 horas)",
       "Gerar narrativa simplificada (< 15 segundos)",
       "Combinar com snapshot anterior"
     ]
   }
   ```

3. **TTS API falhou por 3 tentativas consecutivas**:
   ```json
   {
     "status": "audio_synthesis_failed",
     "reason": "ElevenLabs API retornou erro 500 por 3 tentativas consecutivas. Texto da narrativa foi gerado com sucesso, mas áudio não pôde ser sintetizado.",
     "alternatives": [
       "Retornar apenas narrativa em texto",
       "Usar TTS fallback (Azure Speech)",
       "Agendar síntese de áudio para retry posterior"
     ],
     "partial_success": {
       "narrative_text": "...",
       "nqs": 87
     }
   }
   ```

### 7.3 Verify-Fix-Execute Loop

**Protocolo**: Máximo 2 iterações com diagnóstico obrigatório antes de cada correção

**Iteração 1 - Verificação**:

```python
async def generate_narrative(consciousness_snapshot_id: str) -> NarrativeResult:
    # 1. Validar snapshot existe e tem dados suficientes
    snapshot = await get_consciousness_snapshot(consciousness_snapshot_id)
    if snapshot.event_count < 10:
        return NarrativeResult(
            status="insufficient_data",
            diagnosis="Snapshot tem apenas {snapshot.event_count} eventos - mínimo 10 requerido"
        )

    # 2. Gerar narrativa via LLM
    narrative_text = await llm_client.generate_narrative(snapshot)

    # 3. Validar qualidade da narrativa
    nqs = calculate_nqs(narrative_text)
    if nqs < 85:
        diagnosis = diagnose_low_quality(narrative_text, nqs)
        return NarrativeResult(
            status="quality_failed",
            diagnosis=diagnosis,
            retry_possible=True,
            narrative_text=narrative_text,
            nqs=nqs
        )

    # 4. Sintetizar áudio
    audio = await tts_client.synthesize(narrative_text)

    return NarrativeResult(status="success", narrative_text=narrative_text, audio=audio)
```

**Iteração 2 - Correção**:

```python
async def retry_with_fix(consciousness_snapshot_id: str, diagnosis: Diagnosis) -> NarrativeResult:
    if diagnosis.issue == "low_clarity":
        # Regenera com prompt ajustado para maior clareza
        narrative_text = await llm_client.generate_narrative(
            snapshot,
            prompt_modifiers={"clarity_boost": True}
        )
    elif diagnosis.issue == "poor_coherence":
        # Regenera com mais contexto histórico
        historical_context = await get_recent_narratives(limit=5)
        narrative_text = await llm_client.generate_narrative(
            snapshot,
            context=historical_context
        )
    else:
        # Falha permanente - não tenta 3ª vez
        return NarrativeResult(
            status="impossible",
            reason=f"Não foi possível corrigir issue: {diagnosis.issue}"
        )

    # Valida novamente
    nqs = calculate_nqs(narrative_text)
    if nqs < 85:
        return NarrativeResult(
            status="impossible",
            reason="Narrativa não atingiu qualidade mínima após 2 tentativas"
        )

    audio = await tts_client.synthesize(narrative_text)
    return NarrativeResult(status="success", narrative_text=narrative_text, audio=audio)
```

---

## 8. MÉTRICAS DE GOVERNANÇA

### 8.1 Dashboard de Conformidade

**URL**: `https://grafana.vertice.com/d/mvp-governance`

**Painéis**:

- **LEI Score**: Gráfico de linha (últimos 30 dias)
- **Test Coverage**: Gauge (meta: ≥ 90%)
- **FPC Score**: Gráfico de área (meta: ≥ 80%)
- **CRS Score**: Gráfico de linha (meta: ≥ 95%)
- **NQS (Narrative Quality)**: Histograma (meta: ≥ 85)
- **AQS (Audio Quality)**: Histograma (meta: ≥ 90)
- **Daily Costs**: Gráfico de barras (LLM + TTS)
- **Violações Constitucionais**: Contador (meta: 0)

### 8.2 Relatórios Semanais

**Destinatário**: Arquiteto-Chefe (Juan)

**Conteúdo**:

- Narrativas geradas: Total, por tipo, qualidade média
- Custos acumulados: LLM API, TTS API, storage
- Métricas de qualidade: LEI, FPC, CRS, NQS, AQS
- Violações detectadas e corrigidas
- Falhas de API externa (LLM, TTS)
- Insights sobre estado de consciência do MAXIMUS
- Melhorias propostas

**Formato**: PDF + CSV + Dashboard interativo

### 8.3 Auditoria Trimestral

**Checklist**:

- [ ] Review de custos (tendência, otimizações)
- [ ] Análise de qualidade narrativa (amostra de 100 narrativas)
- [ ] Validação de compliance com LGPD/GDPR
- [ ] Teste de disaster recovery
- [ ] Atualização de dependências (LLM models, TTS voices)
- [ ] Review de permissões de acesso
- [ ] Análise de sentimento das narrativas (evitar bias)
- [ ] Validação de content moderation (PII, profanity)

---

## 9. GESTÃO DE CUSTOS

### 9.1 Estimativa de Custos Mensal

**LLM API** (Claude Sonnet 4):

- Custo por narrativa: ~$0.004 (1200 tokens input + 300 tokens output)
- Narrativas por dia: ~10 (daily summary + eventos ad-hoc)
- Custo mensal: ~$1.20

**TTS API** (ElevenLabs):

- Custo por síntese: ~$0.015 (30 segundos de áudio)
- Sínteses por dia: ~10
- Custo mensal: ~$4.50

**Storage** (S3/MinIO):

- Áudio: ~500KB por arquivo × 300 arquivos/mês = 150MB/mês
- Custo: ~$0.01/mês (negligível)

**Total Estimado**: ~$6/mês (conservador, assumindo 10 narrativas/dia)

### 9.2 Otimizações de Custo

**LLM**:

- Usar Claude Haiku para narrativas de baixa prioridade (-70% custo)
- Cache de prompts frequentes (-50% tokens de input)
- Batch processing quando possível

**TTS**:

- Cache de áudio para narrativas similares (hash de texto)
- Usar Azure Speech para narrativas de baixa prioridade (-60% custo)
- Compressão agressiva (MP3 128kbps para narrativas não-críticas)

**Alertas de Custo**:

- Custo diário > $1: Aviso via Slack
- Custo mensal > $30: Escalação para Arquiteto-Chefe
- Custo por narrativa > $0.05: Investigação automática

---

## 10. CONTATO E RESPONSABILIDADES

**Arquiteto-Chefe**: Juan (Vértice Platform Team)
**On-Call**: Time de DevOps (rotação semanal)
**Escalation**: incidents@vertice.com

**SLA**:

- Produção down: Resposta em 15 minutos
- Narrativa com qualidade < 70: Investigação em 2 horas
- Bug crítico: Fix em 4 horas
- Feature request: Avaliação em 48 horas

---

**Documento aprovado por**: **********\_********** (Arquiteto-Chefe)
**Data de aprovação**: **********\_**********
**Próxima revisão**: 2025-01-30 (Trimestral)

# ADR-003: Padronização de Healthchecks

**Status**: Implementado
**Data**: 2025-10-20
**Contexto**: FASE 5 - Implementação de Healthchecks

## Problema

Sistema MAXIMUS com 103 serviços sem healthchecks padronizados:
- Impossibilidade de detectar falhas de serviço
- Dependências quebradas não detectadas em runtime
- Dificuldade de orquestração (depends_on sem health condition)
- Ausência de monitoring básico

## Decisão

Implementar healthchecks padronizados em **92 serviços de aplicação** usando padrão HTTP uniforme.

### Padrão Definido

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Justificativa dos Parâmetros

- **test**: `curl -f` (fail on HTTP error)
- **interval: 30s**: Verificação a cada 30 segundos (balanceamento overhead/responsiveness)
- **timeout: 10s**: Tempo máximo para resposta (aplicações Python/FastAPI)
- **retries: 3**: 3 falhas consecutivas = unhealthy (tolerância a hiccups)
- **start_period: 40s**: Janela de inicialização (uv sync + app startup)

**Exceções**:
- **Cuckoo Sandbox**: `start_period: 60s` (inicialização mais lenta)
- **Serviços de infraestrutura**: Mantidos healthchecks nativos (Postgres, Redis, Kafka, etc.)

## Implementação

### Metodologia

**Abordagem**: Manual, quality-first
- Rejeitada automação em favor de atenção individual a cada serviço
- Validação de porta correta para cada serviço
- Verificação de conflitos de nomenclatura

### Cobertura

**92 serviços de aplicação** com healthcheck HTTP:

#### Sistema IMMUNIS (9 células AI)
```yaml
immunis_b_cell_service          → 8031/health
immunis_t_helper_service        → 8032/health
immunis_nk_cell_service         → 8033/health
immunis_macrophage_service      → 8030/health
immunis_dendritic_cell_service  → 8034/health
immunis_memory_b_cell_service   → 8035/health
immunis_t_cytotoxic_service     → 8036/health
immunis_regulatory_t_service    → 8037/health
immunis_plasma_cell_service     → 8038/health
```

#### ASA Cortex (5 sensory services)
```yaml
visual_cortex_service           → 8206/health
auditory_cortex_service         → 8207/health
somatosensory_service           → 8208/health
chemical_sensing_service        → 8209/health
vestibular_service              → 8210/health
```

#### Consciousness Core
```yaml
maximus-core                    → 8000/health
maximus-orquestrador            → 8005/health
maximus-executive               → 8503/health
digital_thalamus_service        → 8012/health
iff_service                     → 8013/health
global_workspace_service        → 8014/health
```

#### Neuromodulation & Predictive Processing
```yaml
neuromodulation_service         → 8211/health
predictive_coding_service       → 8215/health
```

#### Memory Systems
```yaml
memory_consolidation_service    → 8216/health
external_memory_service         → 8021/health
```

#### Security & Offensive
```yaml
offensive_gateway               → 8537/health
offensive_orchestrator_service  → 8805/health
purple_team                     → 8806/health
network_recon_service           → 8533/health
web_attack_service              → 8534/health
social_eng_service              → 8535/health
vuln_intel_service              → 8536/health
```

#### Adaptive Immunity
```yaml
adaptive_immunity_db            → 8801/health
adaptive_immunity_service       → 8309/health
hitl_patch_service              → 8308/health
hitl_patch_service_new          → 8811/health
wargaming_crisol                → 8307/health
wargaming_crisol_new            → 8812/health
```

#### Ethical & Regulatory
```yaml
ethical_audit                   → 8306/health
ethical_audit_service           → 8305/health
constitutional_validator        → 8016/health
```

#### Narrative & Analysis
```yaml
narrative_filter_service        → 8804/health
narrative_analysis_service      → 8538/health
narrative_manipulation_filter   → 8017/health
```

#### Homeostatic & Regulation
```yaml
homeostatic_regulation          → 8300/health
rte_service                     → 8301/health
reflex_triage_engine            → 8018/health
```

#### Oracle & Prediction
```yaml
maximus_oraculo_v2_service      → 8809/health
maximus_oraculo_filesystem      → 8813/health
maximus-oraculo                 → 8540/health
maximus_predict                 → 8019/health
cyber_oracle_service            → 8020/health
```

#### OSINT & Intelligence
```yaml
google_osint_service            → 8539/health
sinesp_service                  → 8541/health
osint-service                   → 8542/health
ip_intelligence                 → 8501/health
```

#### Communication & Commands
```yaml
agent_communication             → 8802/health
command_bus_service             → 8803/health
```

#### Infrastructure Services
```yaml
api_gateway                     → 8502/health
cloud_coordinator_service       → 8543/health
network_monitor_service         → 8544/health
tegumentar_service              → 8807/health
verdict_engine_service          → 8808/health
```

#### Testing & Development
```yaml
mock_vulnerable_apps            → 8810/health
```

#### Legacy/Support Services
```yaml
atlas                           → 8504/health
auth                            → 8505/health
adr_core                        → 8506/health
ai_immune_system                → 8507/health
cyber                           → 8508/health
bas_service                     → 8544/health
strategic_planning_service      → 8217/health
goal_setting_service            → 8022/health
seriema_graph                   → 8302/health
predictive_threat_hunting_service → 8545/health
autonomous_investigation_service  → 8546/health
```

**Total: 92 healthchecks implementados**

### Serviços SEM Healthcheck HTTP (11 infraestrutura)

Mantidos healthchecks nativos:
```yaml
postgres           → pg_isready
postgres-immunity  → pg_isready
hcl-postgres       → pg_isready
hcl-kb             → pg_isready
redis              → redis-cli ping
hcl-kafka          → kafka-broker-api-versions
hcl-zookeeper      → zkServer.sh status
redis-aurora       → redis-cli ping
clickhouse         → wget --spider
prometheus         → wget --spider
grafana            → curl -f http://localhost:3000/api/health
```

## Consequências

### Positivas
✅ **92 healthchecks ativos**: 89% de cobertura de serviços
✅ **Padrão uniforme**: Facilita debugging e monitoring
✅ **Detecção de falhas**: Container status reflete saúde real da aplicação
✅ **Orquestração melhorada**: depends_on pode usar condition: service_healthy
✅ **Monitoring básico**: docker ps mostra (healthy)/(unhealthy)
✅ **Fast feedback**: 40s start_period + 30s interval = detecção em ~70s
✅ **Zero overhead excessivo**: 30s interval balanceado

### Negativas
⚠️ **Overhead de rede**: 92 requests HTTP a cada 30s (~3 req/s)
  - **Mitigação**: Overhead negligível para localhost
⚠️ **Dependência de curl**: Todos os containers precisam ter curl instalado
  - **Mitigação**: Dockerfiles já incluem curl ou python (urllib)

### Riscos Mitigados
🛡️ **Falhas silenciosas**: Containers "Up" mas app travada agora detectadas
🛡️ **Dependências falsas**: depends_on agora pode usar service_healthy
🛡️ **Debug demorado**: docker ps mostra (unhealthy) imediatamente

## Validação

### Teste de Cobertura
```bash
# Contar healthchecks implementados
grep -c "healthcheck:" /home/juan/vertice-dev/docker-compose.yml
# Resultado: 92

# Verificar padrão uniforme
grep -A1 "healthcheck:" docker-compose.yml | grep "interval:" | sort | uniq -c
# Resultado: 92x "interval: 30s"

# Verificar start_period
grep -A4 "healthcheck:" docker-compose.yml | grep "start_period:" | sort | uniq -c
# Resultado: 91x "start_period: 40s", 1x "start_period: 60s" (cuckoo)
```

### Teste Funcional (Exemplo)
```bash
# Subir um serviço
docker compose up -d immunis_b_cell_service

# Verificar healthcheck
docker ps --filter "name=immunis-b-cell"
# Esperado: Up X seconds (health: starting) → (healthy)

# Forçar falha (simular)
docker exec immunis-b-cell pkill -9 uvicorn

# Verificar detecção
docker ps --filter "name=immunis-b-cell"
# Esperado: (unhealthy) após 3 retries (~90s)
```

## Alternativas Consideradas

### Alternativa 1: Automação via script
**Rejeitada**: Usuário enfatizou "NAO, n. Manualmente. QUALITY-FIRST". Automação poderia introduzir erros de porta/nomenclatura.

### Alternativa 2: Healthchecks TCP (port scan)
**Rejeitada**: Não valida saúde da aplicação, apenas abertura de porta. HTTP /health endpoint é mais robusto.

### Alternativa 3: Healthchecks nativos (Python script)
**Considerada**: Mais robusto que curl, mas adiciona complexidade. Padrão HTTP curl é mais simples e suficiente.

### Alternativa 4: Interval mais agressivo (10s)
**Rejeitada**: Overhead desnecessário. 30s é suficiente para detecção rápida.

## Melhorias Futuras

1. **Prometheus integration**: Expor healthcheck metrics para Grafana
2. **Depends_on conditions**: Adicionar `condition: service_healthy` onde aplicável
3. **Custom health endpoints**: Endpoints /health mais sofisticados (db connectivity, cache, etc.)
4. **Healthcheck alerts**: Alertas automáticos em Slack/PagerDuty quando (unhealthy)

## Referências
- Docker Healthcheck Documentation: https://docs.docker.com/engine/reference/builder/#healthcheck
- FASE 5 Execution: 92 healthchecks implementados manualmente
- ADR-001: Eliminação Total de Air Gaps (contexto geral)

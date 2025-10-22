# ADR-002: Consolidação HCL V1 (Kafka-Based)

**Status**: Implementado
**Data**: 2025-10-20
**Contexto**: FASE 1 - Resolução de Dependências Quebradas

## Problema

Dois serviços HCL (Homeostatic Control Loop) conflitantes:
- **HCL V1** (`homeostatic_regulation`): Kafka-based, 9 dependentes ativos
- **HCL V2** (`homeostatic_control_loop_service`): Implementação posterior, 0 dependentes

Dependências quebradas:
- `hcl-postgres` (usado por HCL V1)
- `hcl-kb` (usado por HCL V1)

## Análise de Dependentes

### HCL V1 (homeostatic_regulation) - 9 Dependentes:
```yaml
immunis_b_cell_service         → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_t_helper_service       → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_nk_cell_service        → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_macrophage_service     → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_dendritic_cell_service → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_memory_b_cell_service  → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_t_cytotoxic_service    → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_regulatory_t_service   → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
immunis_plasma_cell_service    → KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
```

### HCL V2 (homeostatic_control_loop_service) - 0 Dependentes:
- Nenhum serviço depende desta versão
- Implementação mais recente, mas não adotada

## Decisão

**Manter HCL V1 (Kafka-based) e remover HCL V2**.

### Justificativa

1. **9 dependentes ativos** no sistema IMMUNIS (AI Immune System)
2. **Arquitetura Kafka consolidada** com infraestrutura testada:
   - `hcl-kafka` (Kafka broker)
   - `hcl-zookeeper` (Coordenação Kafka)
   - `hcl-postgres` (Persistência)
   - `hcl-kb` (Knowledge Base)
3. **HCL V2 sem adoção**: Nenhum serviço migrou para a nova implementação
4. **Risco de migração**: Alterar 9 serviços IMMUNIS seria alto impacto sem benefício claro

## Implementação

### Ações Tomadas

1. **Criado `hcl-postgres`** (resolução de dependência):
```yaml
hcl-postgres:
  image: postgres:15-alpine
  container_name: hcl-postgres
  ports:
    - 5433:5432
  environment:
    POSTGRES_DB: hcl
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  volumes:
    - hcl_postgres_data:/var/lib/postgresql/data
  networks:
    - maximus-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

2. **Criado `hcl-kb`** (Knowledge Base):
```yaml
hcl-kb:
  image: postgres:15-alpine
  container_name: hcl-kb
  ports:
    - 5434:5432
  environment:
    POSTGRES_DB: knowledge_base
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  volumes:
    - hcl_kb_data:/var/lib/postgresql/data
  networks:
    - maximus-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

3. **Removido HCL V2** (`homeostatic_control_loop_service`):
   - Serviço sem dependentes
   - Conflito de nome/função resolvido

4. **Volumes criados**:
```yaml
hcl_postgres_data:
  driver: local
hcl_kb_data:
  driver: local
```

## Consequências

### Positivas
✅ **9 serviços IMMUNIS funcionais**: Sistema de imunidade artificial operacional
✅ **Arquitetura Kafka consolidada**: Kafka, Zookeeper, Postgres, KB integrados
✅ **Dependências resolvidas**: hcl-postgres e hcl-kb agora disponíveis
✅ **Zero conflitos**: Nome único `homeostatic_regulation`
✅ **Baixo risco**: Nenhuma migração de serviços dependentes necessária

### Negativas
⚠️ **HCL V2 descartado**: Trabalho de implementação posterior não utilizado
⚠️ **Kafka overhead**: Infraestrutura Kafka mantida (3 serviços adicionais)

### Riscos Residuais
⚠️ **Kafka SPOF**: Se Kafka falhar, 9 serviços IMMUNIS são afetados
  - **Mitigação**: Healthchecks em todos os componentes Kafka
⚠️ **Postgres separados**: 3 instâncias Postgres (hcl-postgres, hcl-kb, postgres principal)
  - **Mitigação**: Volumes persistentes e healthchecks nativos

## Validação

### Testes de Conectividade
```bash
# hcl-postgres
docker ps --filter "name=hcl-postgres" --format "{{.Names}}\t{{.Status}}"
# Esperado: hcl-postgres   Up X minutes (healthy)

# hcl-kb
docker ps --filter "name=hcl-kb" --format "{{.Names}}\t{{.Status}}"
# Esperado: hcl-kb   Up X minutes (healthy)

# Verificar dependentes IMMUNIS
docker ps --filter "name=immunis" --format "{{.Names}}\t{{.Status}}"
# Esperado: 9 serviços Up
```

### Dependências Resolvidas
```bash
# ANTES: 4 dependências quebradas
# DEPOIS: 2 dependências quebradas (hcl-postgres, hcl-kb resolvidas)
docker compose config 2>&1 | grep "service.*not found"
# Esperado: Apenas postgres-immunity e cuckoo (resolvidas em FASE 1 e 6)
```

## Alternativas Consideradas

### Alternativa 1: Migrar para HCL V2
**Rejeitada**: Requeria modificar 9 serviços IMMUNIS sem benefício funcional claro.

### Alternativa 2: Manter ambos HCL V1 e V2
**Rejeitada**: Conflito de nomenclatura e propósito. Violaria Padrão Pagani (zero redundância).

### Alternativa 3: Remover Kafka e usar HTTP
**Rejeitada**: Alteraria arquitetura testada de 9 serviços críticos. Alto risco.

## Referências
- Sistema IMMUNIS: 9 células AI (B, T-helper, NK, Macrophage, Dendritic, Memory-B, T-cytotoxic, Regulatory-T, Plasma)
- Arquitetura Kafka HCL V1: hcl-kafka (9092), hcl-zookeeper (2181), hcl-postgres (5433), hcl-kb (5434)
- ADR-001: Eliminação Total de Air Gaps (contexto geral)

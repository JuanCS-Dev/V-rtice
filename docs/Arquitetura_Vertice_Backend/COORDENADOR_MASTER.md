# COORDENADOR MASTER - TRANSFORMAÇÃO BACKEND VÉRTICE

**Versão:** 1.0.0  
**Data:** 2025-10-16  
**Papel:** Orquestrador dos 3 Executores Paralelos

---

## VISÃO GERAL

Transformação do backend será executada por **3 Executores Sênior trabalhando em PARALELO** em diferentes tracks:

### TRACK 1: BIBLIOTECAS COMPARTILHADAS
**Executor:** Dev Sênior A  
**Arquivo:** `TRACK1_BIBLIOTECAS.md`  
**Foco:** Criar `vertice_core`, `vertice_api`, `vertice_db`  
**Duração:** 7 dias (Dias 4-10)  
**Bloqueadores:** Nenhum (pode iniciar imediatamente)

### TRACK 2: INFRAESTRUTURA & AUTOMAÇÃO
**Executor:** Dev Sênior B (DevOps forte)  
**Arquivo:** `TRACK2_INFRAESTRUTURA.md`  
**Foco:** Port registry, CI/CD, observabilidade, Docker  
**Duração:** 10 dias (Dias 1-10, paralelo ao Track 1)  
**Bloqueadores:** Nenhum (pode iniciar imediatamente)

### TRACK 3: SERVICE TEMPLATE & MIGRAÇÕES
**Executor:** Dev Sênior C (Arquitetura forte)  
**Arquivo:** `TRACK3_SERVICOS.md`  
**Foco:** Template Clean Architecture, migração de serviços críticos  
**Duração:** 20 dias (Dias 11-30)  
**Bloqueadores:** Depende de Track 1 (libs) e Track 2 (port registry)

---

## ESTRATÉGIA DE PARALELIZAÇÃO

### Fase 0: Preparação (Dias 1-3)
```
Track 2 (solo): Port registry, scripts básicos, ADR template
Tracks 1 e 3: IDLE (aguardando)
```

### Fase 1: Construção Paralela (Dias 4-10)
```
Track 1: Bibliotecas compartilhadas (vertice_core, vertice_api, vertice_db)
Track 2: CI/CD pipeline, observability stack setup
Track 3: IDLE (aguardando libs)
```

### Fase 2: Consolidação (Dias 11-16)
```
Track 1: COMPLETO → merge → disponível
Track 2: Dashboards Grafana, alerting
Track 3: Service template usando libs do Track 1
```

### Fase 3: Migração em Massa (Dias 17-30)
```
Track 1: Suporte/bugfixes nas libs
Track 2: Monitoring, performance tuning
Track 3: Migração de 10 serviços críticos
```

---

## PONTOS DE SINCRONIZAÇÃO (GATES)

### GATE 1: Fim do Dia 3
**Antes de iniciar Track 1:**
- [ ] Port registry completo (83 serviços)
- [ ] `validate_ports.py` passa
- [ ] ADR-001 documentado

**Responsável:** Track 2  
**Ação se falhar:** Tracks 1 e 3 aguardam

---

### GATE 2: Fim do Dia 10
**Antes de iniciar Track 3:**
- [ ] `vertice_core` v1.0.0 publicado
- [ ] `vertice_api` v1.0.0 publicado
- [ ] `vertice_db` v1.0.0 publicado
- [ ] CI/CD pipeline funcional
- [ ] Observability stack rodando (Jaeger + Prometheus)

**Responsáveis:** Tracks 1 e 2  
**Ação se falhar:** Track 3 aguarda, Tracks 1-2 corrigem blockers

---

### GATE 3: Fim do Dia 16
**Antes de migração de serviços:**
- [ ] Service template 100% funcional
- [ ] Template testado (build, deploy, testes)
- [ ] Documentação completa

**Responsável:** Track 3  
**Ação se falhar:** Migração postponed, Track 3 corrige

---

## COMUNICAÇÃO ENTRE TRACKS

### Canais
- **Slack:** `#backend-transformation`
- **Daily Sync:** 9h (15min max)
- **Blocker Resolution:** Immediate (ping @track-owner)

### Protocolo de Blocker

**Se Track X está bloqueado:**
1. Documentar blocker em `docs/blockers/trackX-dayN.md`
2. Notificar track responsável
3. SLA: 2h para resposta, 4h para resolução

**Exemplo:**
```markdown
# BLOCKER: Track 3 - Dia 12

**Problema:** vertice_core.logging não tem método `bind_context()`

**Impacto:** Não consigo implementar correlation ID no template

**Responsável:** Track 1

**Solução esperada:** Adicionar método ou indicar alternativa

**Deadline:** 2025-10-16 16:00
```

---

## GESTÃO DE CONFLITOS GIT

### Estratégia de Branches

```
main
├── backend-transformation/track1-libs
├── backend-transformation/track2-infra
└── backend-transformation/track3-services
```

### Áreas de Trabalho (Zero Overlap)

**Track 1:**
```
backend/libs/vertice_core/
backend/libs/vertice_api/
backend/libs/vertice_db/
```

**Track 2:**
```
backend/ports.yaml
backend/scripts/
.github/workflows/
docker-compose.observability.yml
monitoring/
docs/adr/
```

**Track 3:**
```
backend/service_template/
backend/services/api_gateway/     # Migração
backend/services/osint_service/   # Migração
# ... (outros serviços migrados)
docs/migration/
```

**REGRA:** Cada track SÓ edita arquivos em sua área. Conflitos = violação de protocolo.

---

## CRITÉRIOS DE SUCESSO GLOBAL

### Técnicos
- [ ] 3 libs compartilhadas publicadas e testadas
- [ ] Port registry com 83 serviços, zero conflitos
- [ ] CI/CD rodando em <5min por serviço
- [ ] Observability stack operacional
- [ ] Service template completo
- [ ] 10 serviços migrados e funcionais

### Qualitativos
- [ ] Coverage ≥90% em todos os componentes
- [ ] Zero TODO/FIXME em código de produção
- [ ] Documentação completa (ADRs, READMEs, runbooks)
- [ ] Build de qualquer serviço em <3min

### Timeline
- [ ] Track 1 concluído: Dia 10
- [ ] Track 2 concluído: Dia 16
- [ ] Track 3 concluído: Dia 30
- [ ] **TOTAL:** 30 dias úteis

---

## VALIDAÇÃO FINAL (Dia 30)

### Checklist de Entrega

**Infraestrutura:**
- [ ] Todas as portas únicas e documentadas
- [ ] CI/CD funcional para todos os serviços
- [ ] Observability completo (traces, metrics, logs)
- [ ] Docker compose gerado automaticamente

**Código:**
- [ ] 3 bibliotecas em produção
- [ ] Service template documentado
- [ ] 10 serviços migrados e testados
- [ ] Coverage global ≥90%

**Documentação:**
- [ ] ADRs para decisões arquiteturais
- [ ] READMEs atualizados
- [ ] Deployment guides
- [ ] Troubleshooting runbooks

**Testes:**
- [ ] E2E test suite funcional
- [ ] Performance tests passando
- [ ] Load test: 1000 req/s sem erros

---

## ROLLBACK STRATEGY

**Se algum track falhar criticamente:**

1. **Identificar ponto de falha**
2. **Avaliar impacto nos outros tracks**
3. **Decisão:**
   - **Opção A:** Pausar todos, corrigir blocker (se interdependente)
   - **Opção B:** Track bloqueado pausa, outros continuam (se independente)

**Exemplo:** Se Track 1 (libs) falhar no Dia 8, Track 3 DEVE pausar (dependência). Track 2 continua.

---

## INÍCIO DA EXECUÇÃO

### Ordem de Start

1. **Dia 1:** Track 2 inicia sozinho (port registry)
2. **Dia 4:** Track 1 inicia (libs) - após GATE 1
3. **Dia 11:** Track 3 inicia (template) - após GATE 2

### Comando para Cada Executor

**Track 1:**
```bash
cd /home/juan/vertice-dev
git checkout -b backend-transformation/track1-libs
cat docs/Arquitetura_Vertice_Backend/TRACK1_BIBLIOTECAS.md
# Seguir instruções
```

**Track 2:**
```bash
cd /home/juan/vertice-dev
git checkout -b backend-transformation/track2-infra
cat docs/Arquitetura_Vertice_Backend/TRACK2_INFRAESTRUTURA.md
# Seguir instruções
```

**Track 3:**
```bash
cd /home/juan/vertice-dev
git checkout -b backend-transformation/track3-services
cat docs/Arquitetura_Vertice_Backend/TRACK3_SERVICOS.md
# AGUARDAR GATE 2 antes de iniciar
```

---

## DAILY STANDUP FORMAT

**Cada executor reporta:**

1. **Ontem:** O que completei
2. **Hoje:** O que vou fazer
3. **Blockers:** Qualquer impedimento
4. **% Progresso:** Em relação ao meu track

**Exemplo:**
```
Track 1 (Dev A) - Dia 6:
- Ontem: vertice_core logging + tracing implementados, 95% coverage
- Hoje: vertice_core exceptions + metrics, finalizar lib
- Blockers: Nenhum
- Progresso: 70% do Track 1
```

---

## APROVAÇÃO FINAL

**Arquiteto-Chefe deve aprovar:**
- [ ] GATE 1 (Dia 3)
- [ ] GATE 2 (Dia 10)
- [ ] GATE 3 (Dia 16)
- [ ] Entrega Final (Dia 30)

**Critério:** Todos os checklists validados, zero issues P0/P1 pendentes.

---

**Status:** AGUARDANDO INÍCIO  
**Próximo Passo:** Executores lerem seus respectivos tracks e confirmar entendimento

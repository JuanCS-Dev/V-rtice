# 🚀 Rollout Plan - Pós-Migração uv (CI/CD + Docker)

**Versão**: 1.0
**Data**: 2025-10-08
**Duração Estimada**: 4 semanas
**Filosofia**: Quality-First, Zero Breaking Changes

---

## 📊 Status Atual

✅ **FASE 0: Migração Backend Completa**
- 71/71 services migrados para uv + pyproject.toml + ruff
- 100% dos requirements.txt compilados com uv
- Documentação completa criada

⏳ **FASE 1-4: CI/CD + Docker + Deploy (ESTE PLANO)**

---

## 🎯 Objetivos

1. **CI/CD**: Migrar todos os pipelines para uv + ruff
2. **Docker**: Criar base images e migrar Dockerfiles
3. **Staging**: Validar em ambiente de staging
4. **Production**: Deploy gradual com rollback ready

**ROI Esperado**:
- Build time: 90s → 5s (18x mais rápido)
- Docker image size: 1.2GB → 250MB (80% menor)
- Developer experience: significativamente melhor

---

## 📅 Timeline (4 Semanas)

### **Semana 1: Fundação (Sprint 1)**
**Foco**: Templates, base images, e TIER 1

#### Dia 1-2: Setup Inicial
- [x] Criar templates CI/CD (.github/workflows/templates/)
- [x] Criar Docker base image (python311-uv)
- [ ] Build e push base image para registry
- [x] Documentação completa criada

#### Dia 3-4: TIER 1 - Services Críticos (4 services)
**Services**:
1. maximus_core_service
2. active_immune_core
3. seriema_graph
4. tataca_ingestion

**Tasks por service**:
- [ ] Migrar CI/CD workflow
- [ ] Atualizar Dockerfile
- [ ] Build e test local
- [ ] Validar em staging

**Critério de sucesso**:
- ✅ CI/CD passa (verde no GitHub Actions)
- ✅ Docker build <5min
- ✅ Tests passando (mesma coverage)
- ✅ Health checks OK em staging

#### Dia 5: Validação e Retrospectiva
- [ ] Review dos 4 services TIER 1
- [ ] Ajustar templates se necessário
- [ ] Documentar learnings
- [ ] Preparar batch script para TIER 2

**Entregáveis Semana 1**:
- Templates validados em produção
- Base image disponível no registry
- 4 services críticos migrados e validados
- Learnings documentados

---

### **Semana 2: Scale - TIER 2 (Sprint 2)**
**Foco**: 16 services importantes com batch automation

#### Dia 1-2: Batch Automation
- [ ] Script para migrar CI/CD em batch
- [ ] Script para atualizar Dockerfiles em batch
- [ ] Validação automática (smoke tests)

#### Dia 3-5: Migração TIER 2 (16 services)
**Grupos** (migrar em paralelo):
- **Grupo A** (4): narrative_manipulation_filter, prefrontal_cortex_service, osint_service, hcl_kb_service
- **Grupo B** (4): network_recon_service, vuln_intel_service, digital_thalamus_service, web_attack_service
- **Grupo C** (4): hcl_analyzer_service, hcl_planner_service, social_eng_service, homeostatic_regulation
- **Grupo D** (4): bas_service, hcl_monitor_service, ethical_audit_service, hsas_service

**Tasks por grupo**:
- [ ] Batch migrar CI/CD
- [ ] Batch migrar Dockerfiles
- [ ] Build e test em paralelo
- [ ] Deploy em staging (rolling)
- [ ] 24h soak test

**Critério de sucesso**:
- ✅ 16/16 CI/CD verde
- ✅ 16/16 Docker builds <5min
- ✅ Staging estável por 24h
- ✅ Performance baseline mantida

**Entregáveis Semana 2**:
- 16 services TIER 2 migrados
- Automation scripts funcionais
- Staging validado com 20 services

---

### **Semana 3: Completude - TIER 3 + TIER 4 (Sprint 3)**
**Foco**: 50 services auxiliares + experimentais

#### Dia 1-2: TIER 3 - Auxiliares (40 services)
**Batch por família**:
- **Immunis** (9): batch_migrate_immunis.sh
- **Cortex** (5): batch_migrate_cortex.sh
- **Intelligence** (6): batch_migrate_intelligence.sh
- **Outros** (20): batch_migrate_others.sh

#### Dia 3: TIER 4 - Experimentais (10 services)
**Batch completo**:
- batch_migrate_tier4.sh

#### Dia 4-5: Validação Completa
- [ ] Smoke tests (todos os 71 services)
- [ ] Performance benchmarks
- [ ] Security scans (trivy)
- [ ] Resource usage (CPU/Memory)
- [ ] Deploy staging completo

**Critério de sucesso**:
- ✅ 71/71 services com CI/CD verde
- ✅ 71/71 Docker builds <10min
- ✅ Staging 100% operacional
- ✅ 48h soak test OK

**Entregáveis Semana 3**:
- 100% dos services migrados
- Staging completo validado
- Performance report
- Security audit completo

---

### **Semana 4: Production Deploy (Sprint 4)**
**Foco**: Deploy gradual em produção com rollback ready

#### Dia 1: Preparação Production
- [ ] Backup completo do estado atual
- [ ] Rollback procedure testado
- [ ] Monitoring/alerting configurado
- [ ] Runbook de emergency criado

#### Dia 2-3: Deploy Blue/Green
**Fase 1** (20%):
- [ ] Deploy TIER 1 (4 services críticos)
- [ ] 24h monitoring
- [ ] Validar métricas (performance, errors)

**Fase 2** (50%):
- [ ] Deploy TIER 2 (16 services importantes)
- [ ] 24h monitoring
- [ ] Validar métricas

**Fase 3** (100%):
- [ ] Deploy TIER 3 + TIER 4 (50 services)
- [ ] 48h monitoring
- [ ] Validar métricas

#### Dia 4: Validação Final
- [ ] Health checks (todos os 71 services)
- [ ] Performance baseline comparison
- [ ] Error rate check (deve ser 0)
- [ ] Team feedback collection

#### Dia 5: Retrospectiva e Documentação
- [ ] Retrospective meeting
- [ ] Atualizar documentação
- [ ] Knowledge transfer session
- [ ] Celebrate! 🎉

**Critério de sucesso**:
- ✅ 71/71 services em produção
- ✅ Zero incidents
- ✅ Performance melhorou (build time, deploy time)
- ✅ Team confortável com novo workflow

**Entregáveis Semana 4**:
- 100% produção migrada
- Zero breaking changes
- Performance report final
- Team trained

---

## 🔄 Rollback Strategy

### Nível 1: Service Individual
**Trigger**: CI/CD falhou, tests não passam

**Ação**:
```bash
# Restaurar CI/CD antigo
git restore .github/workflows/ci.old.yml
git mv ci.old.yml ci.yml
git commit -m "rollback: restore old CI/CD"
```

**Tempo**: <5 minutos

### Nível 2: Docker Rollback
**Trigger**: Docker build falhou, imagem não funciona

**Ação**:
```bash
# Usar tag antiga
kubectl set image deployment/my-service \
  my-service=ghcr.io/vertice/my-service:pre-uv
```

**Tempo**: <10 minutos

### Nível 3: Rollback Completo
**Trigger**: Múltiplos services falhando, issue crítico

**Ação**:
```bash
# Script de rollback completo
./scripts/rollback_migration.sh

# Restaura:
# - CI/CD workflows antigos
# - Dockerfiles antigos
# - Deploy de images antigas
```

**Tempo**: <30 minutos

**Nota**: Todos os arquivos antigos estão preservados como `.old`

---

## 📊 Métricas de Sucesso

### Performance
| Métrica | Antes | Meta | Medição |
|---------|-------|------|---------|
| CI/CD time | ~90s | ~5s | GitHub Actions |
| Docker build | ~5min | ~1min | CI logs |
| Image size | ~1.2GB | ~300MB | docker images |
| Deploy time | ~10min | ~5min | K8s rollout |

### Qualidade
| Métrica | Meta |
|---------|------|
| Tests passing | 100% |
| Coverage | Mantida ou melhor |
| Security issues | 0 novos |
| Incidents | 0 |

### Adoption
| Métrica | Meta |
|---------|------|
| Services migrados | 71/71 (100%) |
| Team trained | 100% |
| Documentation | 100% completa |

---

## ⚠️ Riscos e Mitigação

### Risco 1: Base image não disponível
**Probabilidade**: Baixa
**Impacto**: Alto
**Mitigação**:
- Fallback para `python:3.11-slim` + install uv inline
- Build local da base image

### Risco 2: Dependency conflicts
**Probabilidade**: Média
**Impacto**: Médio
**Mitigação**:
- uv resolve dependencies melhor que pip
- Testes em staging antes de prod

### Risco 3: Team resistance
**Probabilidade**: Baixa
**Impacto**: Médio
**Mitigação**:
- Documentação excelente (já criada)
- Training sessions
- Suporte ativo

### Risco 4: Performance regression
**Probabilidade**: Muito Baixa
**Impacto**: Alto
**Mitigação**:
- Benchmarks antes/depois
- 48h soak test em staging
- Monitoring rigoroso

---

## 📋 Checklist Final (Pre-Production)

Antes de ir para produção:

**Infraestrutura**:
- [ ] Base image built e pushed
- [ ] Registry configurado
- [ ] K8s namespaces prontos
- [ ] Monitoring/alerting configurado

**Code**:
- [ ] 71/71 services com CI/CD verde
- [ ] 71/71 Dockerfiles atualizados
- [ ] 100% tests passando
- [ ] Security scans limpos

**Documentation**:
- [ ] README atualizado em cada service
- [ ] CICD_MIGRATION_GUIDE.md completo
- [ ] DEVELOPER_WORKFLOW.md completo
- [ ] DOCKER_MIGRATION_GUIDE.md completo
- [ ] Runbooks de emergency

**Team**:
- [ ] Training sessions completas
- [ ] Team confortável com uv
- [ ] Team confortável com ruff
- [ ] On-call preparado

**Validation**:
- [ ] 48h+ soak test em staging
- [ ] Performance baseline OK
- [ ] No incidents em staging
- [ ] Rollback testado e funcional

---

## 🎯 Definition of Done

Este rollout está **COMPLETO** quando:

1. ✅ 71/71 services em produção com uv + ruff
2. ✅ CI/CD 18x mais rápido (90s → 5s)
3. ✅ Docker images 80% menores (1.2GB → 300MB)
4. ✅ Zero breaking changes
5. ✅ Zero incidents
6. ✅ Team 100% trained
7. ✅ Documentation 100% completa
8. ✅ Monitoring/alerting operacional
9. ✅ Rollback testado e ready
10. ✅ Retrospective realizada

---

## 📞 Contatos de Emergência

**Rollout Lead**: Juan
**Tech Lead**: Claude Code
**On-Call**: [Definir]
**Escalation**: [Definir]

**Slack Channels**:
- `#vertice-migration` - Updates e discussão
- `#vertice-incidents` - Apenas incidents
- `#vertice-ops` - Operações

---

## 📚 Referências

- [CICD Migration Guide](./CICD_MIGRATION_GUIDE.md)
- [Developer Workflow](./DEVELOPER_WORKFLOW.md)
- [Docker Migration Guide](./DOCKER_MIGRATION_GUIDE.md)
- [Final Validation Report](./FINAL_VALIDATION_REPORT.md)

---

**Criado em**: 2025-10-08
**Aprovação**: Pending
**Doutrina**: Vértice v2.0 - Quality First
**Objetivo**: 60x faster, zero incidents 🚀

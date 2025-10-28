# TRANSFORMAÇÃO BACKEND VÉRTICE-MAXIMUS

**Status:** 🟢 PRONTO PARA EXECUÇÃO  
**Versão:** 1.0.0  
**Data:** 2025-10-16

---

## DOCUMENTOS PRINCIPAIS

### 1. COORDENADOR_MASTER.md
**Leia PRIMEIRO antes de qualquer coisa.**

- Visão geral da transformação
- Estratégia de paralelização
- Pontos de sincronização (Gates)
- Gestão de conflitos Git
- Critérios de sucesso global

### 2. TRACK1_BIBLIOTECAS.md
**Para:** Dev Sênior A (Python/Testing)  
**Foco:** Criar libs compartilhadas (vertice_core, vertice_api, vertice_db)  
**Duração:** 7 dias (Dias 4-10)  
**Branch:** `backend-transformation/track1-libs`

### 3. TRACK2_INFRAESTRUTURA.md
**Para:** Dev Sênior B (DevOps)  
**Foco:** Port registry, CI/CD, observability  
**Duração:** 16 dias (Dias 1-16)  
**Branch:** `backend-transformation/track2-infra`

### 4. TRACK3_SERVICOS.md
**Para:** Dev Sênior C (Arquitetura)  
**Foco:** Service template, migração de serviços  
**Duração:** 20 dias (Dias 11-30)  
**Branch:** `backend-transformation/track3-services`

---

## QUICK START

### Para o Coordenador

```bash
# 1. Ler visão geral
cat docs/Arquitetura_Vertice_Backend/COORDENADOR_MASTER.md

# 2. Verificar pré-requisitos
python --version  # >= 3.11
docker --version  # >= 24.0
uv --version      # >= 0.1.0

# 3. Criar branches
git checkout -b backend-transformation/track1-libs
git checkout main
git checkout -b backend-transformation/track2-infra
git checkout main
git checkout -b backend-transformation/track3-services
git checkout main

# 4. Atribuir tracks aos executores
```

### Para Executor Track 1

```bash
cd /home/juan/vertice-dev
git checkout backend-transformation/track1-libs
cat docs/Arquitetura_Vertice_Backend/TRACK1_BIBLIOTECAS.md

# AGUARDAR GATE 1 (Dia 3)
# Quando Track 2 notificar: INICIAR
```

### Para Executor Track 2

```bash
cd /home/juan/vertice-dev
git checkout backend-transformation/track2-infra
cat docs/Arquitetura_Vertice_Backend/TRACK2_INFRAESTRUTURA.md

# PODE INICIAR IMEDIATAMENTE (Dia 1)
```

### Para Executor Track 3

```bash
cd /home/juan/vertice-dev
git checkout backend-transformation/track3-services
cat docs/Arquitetura_Vertice_Backend/TRACK3_SERVICOS.md

# AGUARDAR GATE 2 (Dia 10)
# Quando Tracks 1 e 2 notificarem: INICIAR
```

---

## GATES DE SINCRONIZAÇÃO

### GATE 1: Dia 3
**Antes de Track 1 iniciar:**
- [ ] Port registry completo (83 serviços)
- [ ] validate_ports.py passa
- [ ] ADR-001 documentado
- [ ] Aprovação Arquiteto-Chefe

**Responsável:** Track 2

---

### GATE 2: Dia 10
**Antes de Track 3 iniciar:**
- [ ] vertice_core v1.0.0 publicado
- [ ] vertice_api v1.0.0 publicado
- [ ] vertice_db v1.0.0 publicado
- [ ] CI/CD pipeline funcional
- [ ] Observability stack rodando
- [ ] Aprovação Arquiteto-Chefe

**Responsáveis:** Tracks 1 e 2

---

### GATE 3: Dia 16
**Antes de migração de serviços:**
- [ ] Service template 100% funcional
- [ ] Template testado (build, deploy, testes)
- [ ] Documentação completa
- [ ] Aprovação Arquiteto-Chefe

**Responsável:** Track 3

---

## ESTRUTURA DE COMUNICAÇÃO

### Daily Sync (9h, 15min max)

Cada executor reporta:
1. Ontem: O que completei
2. Hoje: O que vou fazer
3. Blockers: Qualquer impedimento
4. % Progresso: Em relação ao meu track

### Canais
- **Slack:** `#backend-transformation`
- **Blockers:** `docs/blockers/trackX-dayN.md`
- **SLA:** 2h para resposta, 4h para resolução

---

## ÁREAS DE TRABALHO (Zero Overlap)

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
backend/services/api_gateway/
backend/services/osint_service/
backend/services/.../  (outros migrados)
docs/migration/
```

**REGRA:** Cada track SÓ edita sua área. Conflitos = violação de protocolo.

---

## CRITÉRIOS DE SUCESSO

### Técnicos
- [ ] 3 libs compartilhadas publicadas (≥95% coverage)
- [ ] Port registry 83 serviços, zero conflitos
- [ ] CI/CD <5min por serviço
- [ ] Observability stack operacional
- [ ] Service template completo
- [ ] 10 serviços migrados (≥90% coverage)

### Timeline
- [ ] Track 1: Dia 10
- [ ] Track 2: Dia 16
- [ ] Track 3: Dia 30
- [ ] **TOTAL:** 30 dias úteis

---

## VALIDAÇÃO FINAL (Dia 30)

```bash
# Port registry
cd /home/juan/vertice-dev/backend
python scripts/validate_ports.py

# Libs
cd libs
for lib in */; do
    cd "$lib"
    uv run pytest --cov --cov-fail-under=95 || exit 1
    cd ..
done

# Template
cd service_template
uv run pytest --cov --cov-fail-under=90
docker build -t template-test .

# Serviços migrados
for svc in api_gateway osint_service ...; do
    cd services/$svc
    uv run pytest --cov --cov-fail-under=90 || exit 1
done

# Observability
docker-compose -f docker-compose.observability.yml ps
curl http://localhost:16686/api/services  # Jaeger
curl http://localhost:9090/-/healthy      # Prometheus

# CI
gh workflow list | grep backend

echo "✅ TRANSFORMAÇÃO COMPLETA"
```

---

## ROLLBACK STRATEGY

**Se algum track falhar:**

1. Identificar ponto de falha
2. Avaliar impacto nos outros tracks
3. Decisão:
   - Pausar todos (se interdependente)
   - Track bloqueado pausa, outros continuam (se independente)

---

## SUPORTE

**Dúvidas ou blockers:**
1. Consultar documento do seu track
2. Se não resolvido: criar blocker em `docs/blockers/`
3. Notificar track responsável
4. Escalar para Arquiteto-Chefe se SLA ultrapassado

---

## APROVAÇÃO

**Arquiteto-Chefe deve aprovar:**
- [ ] Início da transformação
- [ ] GATE 1 (Dia 3)
- [ ] GATE 2 (Dia 10)
- [ ] GATE 3 (Dia 16)
- [ ] Entrega Final (Dia 30)

---

**Boa execução! 🚀**

# Categorização de Serviços - Correção Sistemática

## RESUMO

**Total de serviços analisados**: 19
**Precisam de api.py**: 16
**Já têm api.py mas estão unhealthy**: 3

## CATEGORIA 1: IMMUNIS SERVICES (7 serviços - FALTA api.py)

| Serviço | Status | Porta | Arquivo Core |
|---------|--------|-------|--------------|
| immunis_neutrophil_service | ✗ FALTA api.py | 8013 | neutrophil_core.py |
| immunis_macrophage_service | ✗ FALTA api.py | 8014 | macrophage_core.py |
| immunis_dendritic_service | ✗ FALTA api.py | 8015 | dendritic_core.py |
| immunis_bcell_service | ✗ FALTA api.py | 8016 | bcell_core.py |
| immunis_helper_t_service | ✗ FALTA api.py | 8017 | helper_t_core.py |
| immunis_cytotoxic_t_service | ✗ FALTA api.py | 8018 | cytotoxic_t_core.py |
| immunis_nk_cell_service | ✗ FALTA api.py | 8019 | nk_cell_core.py |

**Ação**: Criar api.py para cada um baseado no template

## CATEGORIA 2: HCL SERVICES (5 serviços - FALTA api.py)

| Serviço | Status | Porta | Arquivo Main |
|---------|--------|-------|--------------|
| hcl_kb_service | ✗ FALTA api.py | 8022 | main.py |
| hcl_analyzer_service | ✗ FALTA api.py | 8023 | main.py |
| hcl_monitor_service | ✗ FALTA api.py | 8024 | main.py |
| hcl_planner_service | ✗ FALTA api.py | 8025 | main.py |
| hcl_executor_service | ✗ FALTA api.py | 8027 | main.py |

**Ação**: Criar api.py importando main.py ou renomear main.py para api.py

## CATEGORIA 3: OUTROS SERVICES (4 serviços - FALTA api.py)

| Serviço | Status | Porta | Arquivo Principal |
|---------|--------|-------|-------------------|
| rte_service | ✗ FALTA api.py | 8026 | main.py |
| google_osint_service | ✗ FALTA api.py | 8003 | main.py |
| tataca_ingestion | ✗ FALTA api.py | ? | ? |
| seriema_graph | ✗ FALTA api.py | ? | ? |

**Ação**: Verificar estrutura e criar/adaptar api.py

## CATEGORIA 4: TÊM api.py MAS UNHEALTHY (3 serviços - Problema diferente)

| Serviço | Status | Problema Provável |
|---------|--------|-------------------|
| network_recon_service | ✓ TEM api.py | Imagem desatualizada ou deps |
| vuln_intel_service | ✓ TEM api.py | Imagem desatualizada ou deps |
| web_attack_service | ✓ TEM api.py | Imagem desatualizada ou deps |

**Ação**: Rebuild forçado sem cache

## CATEGORIA 5: NARRATIVE FILTER (1 serviço - Deps faltando)

| Serviço | Status | Problema |
|---------|--------|----------|
| narrative_manipulation_filter | ✓ TEM api.py | ModuleNotFoundError: sqlalchemy |

**Ação**: Rebuild forçado sem cache

## PLANO DE EXECUÇÃO AJUSTADO

### FASE 2A: Immunis Services (7 × 5min = 35min)
- Criar api.py para cada serviço
- Build individual
- Test health endpoint

### FASE 2B: HCL Services (5 × 5min = 25min)
- Criar api.py ou renomear main.py
- Build individual
- Test health endpoint

### FASE 2C: Outros Services (4 × 5min = 20min)
- Verificar estrutura de cada um
- Criar api.py apropriado
- Build e test

### FASE 3: Rebuild Services com api.py existente (15min)
- network_recon, vuln_intel, web_attack, narrative_filter
- `docker-compose build --no-cache <service>`
- Validate health

### FASE 4: Validação Final (10min)
- docker-compose up -d
- Test all health endpoints
- Generate status report

**TEMPO TOTAL ESTIMADO**: ~2h

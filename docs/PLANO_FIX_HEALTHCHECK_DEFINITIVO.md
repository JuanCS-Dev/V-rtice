# PLANO DE FIX HEALTHCHECK DEFINITIVO - 100% SOBERANIA

**Data:** 2025-10-19  
**Causa-raiz:** Healthcheck usa `httpx` (Python) mas deveria usar `curl` (mais confiável)  
**Método:** Substituição automatizada via script Python  
**Tempo estimado:** 30min (script 5min + rebuild 20min + validação 5min)

---

## ANÁLISE DE CAUSA-RAIZ COMPLETA

### Problema Identificado
**31 serviços unhealthy** apesar de:
- ✅ Aplicações rodando corretamente
- ✅ Endpoints `/health` implementados e funcionais
- ✅ Portas internas corretas (8007, 8008, etc.)

### Causa-raiz
**Dockerfile HEALTHCHECK usa Python + httpx:**
```dockerfile
HEALTHCHECK CMD python -c "import httpx; exit(0 if httpx.get('http://localhost:8007/health', timeout=5).status_code == 200 else 1)" || exit 1
```

**Problemas:**
1. Python pode não estar no PATH do healthcheck
2. httpx pode falhar silenciosamente
3. Mais complexo que necessário
4. Não é best practice (OSINT research)

### Solução (OSINT Validated)
**Usar `curl` (já instalado em todos containers):**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:PORT/health || exit 1
```

**Fontes:**
- FastAPI official docs
- Docker best practices
- Stack Overflow consensus

---

## PLANO DE EXECUÇÃO

### FASE I: Script Automatizado (5min)

**STEP 1:** Criar script Python para fix em massa
```python
import re
from pathlib import Path

SERVICES_PORTS = {
    "autonomous_investigation_service": 8007,
    "bas_service": 8008,
    "c2_orchestration_service": 8009,
    # ... (31 total)
}

def fix_healthcheck(dockerfile_path, port):
    content = dockerfile_path.read_text()
    
    # Pattern: HEALTHCHECK com python httpx
    old_pattern = r'HEALTHCHECK.*?CMD python -c.*?httpx.*?(?=\nEXPOSE|\nCMD|\Z)'
    
    # Novo healthcheck canônico
    new_healthcheck = (
        f'HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\\n'
        f'  CMD curl -f http://localhost:{port}/health || exit 1'
    )
    
    fixed = re.sub(old_pattern, new_healthcheck, content, flags=re.DOTALL)
    
    if fixed != content:
        dockerfile_path.write_text(fixed)
        return True
    return False
```

**Critério de sucesso:** Script executa sem erros + 31 Dockerfiles modificados

---

### FASE II: Rebuild Paralelo (20min)

**STEP 2:** Rebuild em lotes de 10 serviços
```bash
# Lote 1 (10 serviços)
docker compose build --parallel \
  autonomous_investigation_service bas_service c2_orchestration_service \
  atlas_service cyber_service domain_service \
  google_osint_service malware_analysis_service \
  network_monitor_service maximus_predict

# Lote 2 (10 serviços)
docker compose build --parallel \
  narrative_analysis_service predictive_threat_hunting_service \
  rte_service cloud_coordinator_service edge_agent_service \
  hcl_analyzer_service hcl_executor_service hcl_kb_service \
  hcl_monitor_service hcl_planner_service

# Lote 3 (11 serviços)
docker compose build --parallel \
  hsas_service nmap_service osint-service \
  reflex_triage_engine rte-service seriema_graph \
  ssl_monitor_service threat_intel_service \
  vuln_intel_service vuln_scanner_service hcl-kb-service
```

**Critério de sucesso:** 31 imagens recriadas com novo healthcheck

---

### FASE III: Restart + Validação (5min)

**STEP 3:** Restart services + aguardar start-period
```bash
# Restart todos unhealthy
docker compose up -d --force-recreate \
  autonomous_investigation_service bas_service c2_orchestration_service \
  # ... (31 total)

# Aguardar start-period (60s)
sleep 70

# Validar métricas
docker compose ps --format "{{.Service}} {{.Health}}" | grep -c "healthy"
```

**Critério de sucesso:** 
- Unhealthy: 31 → 0
- Healthy: 69 → 100
- Health %: 69% → 100%

---

## ROLLBACK PLAN

**Se algo der errado:**
```bash
# Restaurar Dockerfiles de backup
for svc in $(cat /tmp/unhealthy_services.txt); do
  service_dir="${svc//-/_}"
  git checkout /home/juan/vertice-dev/backend/services/${service_dir}/Dockerfile
done

# Rebuild
docker compose build --parallel
```

---

## ESTIMATIVA FINAL

**Tempo total:** 30min
- Script: 5min
- Rebuild: 20min (3 lotes paralelos)
- Validation: 5min

**Complexidade:** BAIXA (automação total)
**Risco:** MUITO BAIXO (curl já instalado, healthcheck best practice)
**Resultado:** 95% → 100% Soberania Absoluta

---

**Assinatura:** Executor Tático Vértice  
**Status:** PLANO PRONTO PARA EXECUÇÃO  
**Próxima ação:** GO do Arquiteto-Chefe

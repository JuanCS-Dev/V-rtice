# RELATÓRIO: Port Mismatch Fix - Causa-raiz dos 19 Unhealthy

**Data:** 2025-10-19  
**Descoberta:** Após fix httpx → curl, 19 serviços permaneceram unhealthy  
**Causa-raiz:** Port mismatch entre Dockerfile EXPOSE e docker-compose.yml ports

---

## ANÁLISE

### Problema Identificado
Healthcheck Docker tenta conectar na porta definida no HEALTHCHECK do Dockerfile,  
MAS docker-compose.yml mapeia portas DIFERENTES.

### Exemplo: autonomous_investigation_service
```dockerfile
# Dockerfile
EXPOSE 8007
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
HEALTHCHECK CMD curl -f http://localhost:8007/health || exit 1
```

```yaml
# docker-compose.yml
ports:
  - "8017:8017"  # ❌ WRONG! App roda em 8007, não 8017
```

**Resultado:** Healthcheck tenta 8007 (correto) mas Docker espera 8017 → FAIL

---

## SERVIÇOS AFETADOS (7)

| Serviço | Dockerfile | docker-compose | Status |
|---------|------------|----------------|--------|
| autonomous_investigation_service | 8007 | 8017:8017 | unhealthy |
| bas_service | 8008 | 8536:8036 | unhealthy |
| c2_orchestration_service | 8009 | 8535:8035 | unhealthy |
| network_monitor_service | 8044 | 8120:80 | unhealthy |
| maximus_predict | 8040 | 8126:80 | unhealthy |
| narrative_analysis_service | 8042 | 8015:8015 | unhealthy |
| predictive_threat_hunting_service | 8050 | 8016:8016 | unhealthy |

---

## FIX APLICADO

**Atualizar docker-compose.yml para match com Dockerfile:**

```yaml
# ANTES
autonomous_investigation_service:
  ports:
    - "8017:8017"

# DEPOIS
autonomous_investigation_service:
  ports:
    - "8017:8007"  # External:Internal (Dockerfile porta 8007)
```

**Padrão:** `"PORTA_EXTERNA:PORTA_INTERNA_DOCKERFILE"`

---

## RESULTADO ESPERADO

**Antes:** 61/73 healthy (83%)  
**Depois:** 68/73 healthy (93%)  
**Delta:** +7 serviços healthy

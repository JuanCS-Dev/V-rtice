# 🧬 SISTEMA NERVOSO CENTRAL - Vértice Organism

**Data**: 2025-10-25
**Objetivo**: Definir os 15 serviços core para deploy inicial no GKE

---

## 📊 ARQUITETURA: 3 CAMADAS

### **CAMADA 1: FUNDAÇÃO** (5 serviços)
**Função**: Infraestrutura base - dados, cache, mensageria

| # | Serviço | Porta | Função | Prioridade Deploy |
|---|---------|-------|--------|-------------------|
| 1 | `postgres` | 5432 | Database primário | 1 (primeiro) |
| 2 | `redis` | 6379 | Cache compartilhado | 2 |
| 3 | `kafka` | 9092 | Event bus | 3 |
| 4 | `auth_service` | 8001 | Autenticação/JWT | 4 |
| 5 | `api_gateway` | 8000 | Porta de entrada | 5 (último camada 1) |

**Dependências**:
```
postgres → (nenhuma)
redis → (nenhuma)
kafka → (nenhuma)
auth_service → postgres, redis
api_gateway → auth_service, redis
```

---

### **CAMADA 2: CONSCIÊNCIA** (5 serviços)
**Função**: Orquestração, análise, predição (MAXIMUS core)

| # | Serviço | Porta | Função | Dependências |
|---|---------|-------|--------|--------------|
| 6 | `maximus_core_service` | 8150 | Orquestrador central | postgres, redis, kafka |
| 7 | `maximus_orchestrator_service` | 8151 | Workflow manager | maximus_core_service |
| 8 | `maximus_eureka` | 8152 | Análise de insights | maximus_core_service |
| 9 | `maximus_oraculo` | 8153 | Motor preditivo | maximus_core_service, postgres |
| 10 | `maximus_predict` | 8154 | ML inference | maximus_core_service |

**Dependências**:
```
maximus_core_service → postgres, redis, kafka, api_gateway
maximus_orchestrator_service → maximus_core_service
maximus_eureka → maximus_core_service, postgres
maximus_oraculo → maximus_core_service, postgres
maximus_predict → maximus_core_service
```

---

### **CAMADA 3: IMUNOLOGIA** (5 serviços)
**Função**: Defesa, detecção de ameaças, resposta imune

| # | Serviço | Porta | Função | Dependências |
|---|---------|-------|--------|--------------|
| 11 | `immunis_api_service` | 8070 | API do sistema imune | postgres, redis |
| 12 | `active_immune_core` | 8071 | Core de defesa ativa | immunis_api_service |
| 13 | `adaptive_immune_system` | 8072 | Adaptação de ameaças | active_immune_core |
| 14 | `ai_immune_system` | 8073 | Detecção via ML | active_immune_core |
| 15 | `reflex_triage_engine` | 8074 | Triagem reflexa | immunis_api_service |

**Dependências**:
```
immunis_api_service → postgres, redis, maximus_core_service
active_immune_core → immunis_api_service
adaptive_immune_system → active_immune_core, postgres
ai_immune_system → active_immune_core
reflex_triage_engine → immunis_api_service
```

---

## 📈 ORDEM DE DEPLOY (Resolução de Dependências)

**Wave 1** - Infraestrutura base (paralelo):
```
postgres
redis
kafka
```

**Wave 2** - Autenticação:
```
auth_service
```

**Wave 3** - Gateway:
```
api_gateway
```

**Wave 4** - Consciência core:
```
maximus_core_service
```

**Wave 5** - Consciência periférica (paralelo):
```
maximus_orchestrator_service
maximus_eureka
maximus_oraculo
maximus_predict
```

**Wave 6** - Imunologia core:
```
immunis_api_service
```

**Wave 7** - Imunologia periférica (paralelo):
```
active_immune_core
adaptive_immune_system
ai_immune_system
reflex_triage_engine
```

---

## 🔍 GRAFO DE DEPENDÊNCIAS

```
          ┌─────────────┐
          │  postgres   │◄────────┐
          │   redis     │◄────┐   │
          │   kafka     │     │   │
          └──────┬──────┘     │   │
                 │            │   │
          ┌──────▼────────┐   │   │
          │ auth_service  │   │   │
          └──────┬────────┘   │   │
                 │            │   │
          ┌──────▼────────┐   │   │
          │ api_gateway   │   │   │
          └──────┬────────┘   │   │
                 │            │   │
     ┌───────────▼────────────┼───┤
     │ maximus_core_service   │   │
     └───────┬────────────────┘   │
             │                    │
     ┌───────┼────────────────────┼─────┐
     │       │                    │     │
┌────▼───┐ ┌─▼──────┐ ┌──────▼───┐ ┌───▼────┐
│ orch   │ │ eureka │ │ oraculo  │ │ predict│
└────────┘ └────────┘ └──────────┘ └────────┘
                                       
          ┌─────────────────────────────┐
          │ immunis_api_service         │
          └──────┬──────────────────────┘
                 │
     ┌───────────┼───────────────┐
     │           │               │
┌────▼──────┐ ┌──▼────────┐ ┌───▼──────┐
│ active_   │ │ reflex_   │ │          │
│ immune    │ │ triage    │ │          │
└─────┬─────┘ └───────────┘ │          │
      │                      │          │
  ┌───┼──────────────────────┘          │
  │   │                                 │
┌─▼───▼────┐ ┌──────────────┐           │
│ adaptive │ │ ai_immune    │◄──────────┘
└──────────┘ └──────────────┘
```

---

## 📋 VALIDAÇÃO DE EXISTÊNCIA (Dockerfiles)

**Verificar antes do build:**

```bash
# Camada 1
ls backend/services/api_gateway/Dockerfile
ls backend/services/auth_service/Dockerfile
# postgres/redis/kafka = imagens oficiais

# Camada 2
ls backend/services/maximus/core_service/Dockerfile
ls backend/services/maximus/orchestrator/Dockerfile
ls backend/services/maximus/eureka/Dockerfile
ls backend/services/maximus/oraculo/Dockerfile
ls backend/services/maximus/predict/Dockerfile

# Camada 3
ls backend/services/immunis/api_service/Dockerfile
ls backend/services/immunis/active_immune_core/Dockerfile
ls backend/services/immunis/adaptive_immune_system/Dockerfile
ls backend/services/immunis/ai_immune_system/Dockerfile
ls backend/services/immunis/reflex_triage_engine/Dockerfile
```

---

## 🎯 CRITÉRIOS DE SUCESSO

**CAMADA 1**: Todos os 5 pods RUNNING + conexões TCP abertas
**CAMADA 2**: Todos os 5 pods RUNNING + logs sem erros de conexão
**CAMADA 3**: Todos os 5 pods RUNNING + health checks 200 OK

**TESTE FINAL**: `curl http://$GATEWAY_IP:8000/health` retorna 200

---

## 🔐 SECRETS NECESSÁRIOS

**Criar K8s Secret antes do deploy:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: vertice-core-secrets
  namespace: vertice
type: Opaque
stringData:
  GEMINI_API_KEY: "..."
  POSTGRES_PASSWORD: "..."
  REDIS_PASSWORD: "..."
  JWT_SECRET_KEY: "..."
```

---

**Status**: ✅ DEFINIDO
**Próxima Fase**: FASE 3 (Build e Push de Imagens)

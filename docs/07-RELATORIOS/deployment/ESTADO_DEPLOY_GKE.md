# Estado do Deploy GKE - Organismo Vértice

**Última atualização**: 2025-10-25 11:50 BRT
**Commit**: `aa0125cd` - feat(deploy): Add GKE deployment infrastructure

## 🎯 Objetivo

Deployar o Organismo Vértice completo (15 serviços) no GKE cluster `vertice-us-cluster` (região us-east1).

## 📊 Status Atual

### ✅ CAMADA 1 - Fundação (PARCIALMENTE OK)

**Funcionando:**
- ✅ **PostgreSQL**: 1/1 Running (StatefulSet)
  - Superuser: `juan-dev` (criado)
  - Port: 5432

- ✅ **Redis**: 1/1 Running
  - Port: 6379

- ✅ **Auth Service**: 2/2 Running
  - Port: 8006 (corrigido de 8001)
  - Database fix: `/home/maximus/Documentos/V-rtice/backend/services/auth_service/database.py:29-38`
  - Conexão com PostgreSQL funcionando

- ✅ **API Gateway**: 2/2 Running
  - Port: 8001

**Pendente:**
- ⚠️ **Kafka**: 1/2 CrashLoopBackOff
  - Zookeeper: OK (1/1)
  - Kafka container: CRASHANDO
  - Tentativa de fix: Changed KAFKA_ZOOKEEPER_CONNECT to "localhost:2181" + startup delay
  - **Ação necessária**: Investigar logs do Kafka, voltar nisso BREVE (pedido do usuário)

### ❌ CAMADA 2 - Consciência (MAXIMUS) - CRASHANDO

**Todos os 5 serviços crashando com mesmo erro:**

```
ModuleNotFoundError: No module named '_demonstration'
```

**Serviços afetados:**
1. maximus-core-service (port 8150)
2. maximus-eureka (port 8151)
3. maximus-oraculo (port 8152)
4. maximus-orchestrator-service (port 8153)
5. maximus-predict (port 8154)

**Causa raiz:**
- Arquivo: `/home/maximus/Documentos/V-rtice/backend/services/maximus_core_service/main.py:17`
- Import: `from _demonstration.maximus_integrated import MaximusIntegrated`
- **Diretório `_demonstration` não existe no repositório**
- Funciona no PC do usuário mas não está commitado
- Dockerfile referencia: `PYTHONPATH=/app:/app/_demonstration` (linha 70)

**Ações necessárias:**
1. Localizar diretório `_demonstration` no PC do usuário
2. Copiar para o repositório OU refatorar imports
3. Rebuild imagens MAXIMUS
4. Push para Artifact Registry
5. Redeploy pods

### 🛑 CAMADA 3 - Imunologia (DESLIGADA PROPOSITALMENTE)

**Status**: Todos escalados para 0 réplicas

**Motivo**: Prevenção de falsos positivos durante inicialização
O sistema imune pode detectar a atividade de startup como ameaças sem o MAXIMUS ativo para supervisionar.

**Serviços (todos 0/1):**
1. immunis-api-service (port 8070)
2. active-immune-core (port 8071)
3. adaptive-immune-system (port 8072)
4. ai-immune-system (port 8073)
5. reflex-triage-engine (port 8074)

**Sequência correta de inicialização:**
1. ✅ Fundação (Postgres, Redis, Auth, Gateway) - DONE
2. ⏳ Consciência (MAXIMUS) - aguardando fix `_demonstration`
3. ⏳ Imunologia - ativar SOMENTE após MAXIMUS estar Ready

**Comando para ativar quando MAXIMUS estiver OK:**
```bash
kubectl scale deployment --all -n vertice --replicas=1 --selector=tier=imunologia
```

## 🏗️ Infraestrutura GCP

### Cluster GKE
- **Nome**: `vertice-us-cluster`
- **Região**: `us-east1`
- **Tipo**: Regional (multi-zone HA)
- **Nodes**: 2 (auto-scaled de 1→2 durante deploy)
- **Machine**: `e2-standard-4` (4 vCPU, 16GB RAM)
- **Status**: ✅ RUNNING

### Artifact Registry
- **Registry**: `us-east1-docker.pkg.dev/projeto-vertice/vertice-images`
- **Imagens disponíveis** (13 total):
  - `python311-uv:latest` (base image)
  - `api_gateway:latest`
  - `auth_service:latest`
  - 5x MAXIMUS: `maximus_core_service`, `maximus_eureka`, `maximus_oraculo`, `maximus_orchestrator_service`, `maximus_predict`
  - 5x Immunology: `immunis_api_service`, `active_immune_core`, `adaptive_immune_system`, `ai_immune_system`, `reflex_triage_engine`

### Namespaces & ConfigMaps
- **Namespace**: `vertice`
- **ConfigMap**: `vertice-global-config` (LOG_LEVEL=INFO, ENVIRONMENT=production)
- **Secret**: `vertice-core-secrets` (POSTGRES_*, REDIS_*, GEMINI_API_KEY, etc.)

## 🔧 Correções Aplicadas

### 1. Auth Service Database Connection
**Arquivo**: `backend/services/auth_service/database.py:29-38`

**Problema**:
- Hardcoded `DATABASE_URL`
- Kubernetes não expande `$(VAR)` em env values
- Conflito com `POSTGRES_HOST`/`POSTGRES_PORT` auto-injetados pelo Service

**Solução**:
```python
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "vertice_auth")
DB_HOST = os.getenv("DB_HOST", "postgres")  # Renamed to avoid conflict
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

### 2. Auth Service Port Configuration
**Arquivos**:
- `k8s/camada-1-fundacao/auth-service-deployment.yaml`

**Mudança**: 8001 → 8006 (match Dockerfile EXPOSE)
- containerPort: 8006
- SERVICE_PORT: "8006"
- livenessProbe port: 8006
- readinessProbe port: 8006
- Service port: 8006

### 3. Image Naming (Docker vs K8s)
**Problema**: Docker permite underscores, K8s resource names não

**Solução**:
- **Image paths**: `vertice-images/maximus_core_service:latest` (underscores OK)
- **K8s resources**: `metadata.name: maximus-core-service` (hyphens)
- Applied via sed replacements em todos YAMLs Layer 2 & 3

### 4. Kafka Multi-Container Coordination
**Arquivo**: `k8s/camada-1-fundacao/kafka-statefulset.yaml`

**Tentativa de fix** (ainda não funcionou):
```yaml
env:
  - name: KAFKA_ZOOKEEPER_CONNECT
    value: "localhost:2181"  # Changed from "zookeeper:2181"

command: ["/bin/bash", "-c"]
args:
  - |
    echo "Waiting for Zookeeper to be ready..."
    while ! nc -z localhost 2181; do sleep 1; done
    echo "Zookeeper is ready, starting Kafka..."
    exec /etc/confluent/docker/run
```

**Status**: Kafka container ainda crashando, precisa investigação adicional

## 📁 Arquivos Criados/Modificados

### Kubernetes Manifests (`k8s/`)
```
k8s/
├── namespaces/
│   └── vertice-namespace.yaml
├── configmaps/
│   └── global-config.yaml
├── secrets/
│   └── vertice-core-secrets.yaml
├── camada-1-fundacao/
│   ├── postgres-statefulset.yaml
│   ├── redis-deployment.yaml
│   ├── kafka-statefulset.yaml
│   ├── auth-service-deployment.yaml
│   └── api-gateway-deployment.yaml
├── camada-2-consciencia/
│   ├── maximus_core_service-deployment.yaml
│   ├── maximus_eureka-deployment.yaml
│   ├── maximus_oraculo-deployment.yaml
│   ├── maximus_orchestrator_service-deployment.yaml
│   └── maximus_predict-deployment.yaml
└── camada-3-imunologia/
    ├── immunis_api_service-deployment.yaml
    ├── active_immune_core-deployment.yaml
    ├── adaptive_immune_system-deployment.yaml
    ├── ai_immune_system-deployment.yaml
    └── reflex_triage_engine-deployment.yaml
```

### Scripts (`scripts/`)
```
scripts/
├── gcp/
│   ├── provision_gke_infra.sh       # Cria cluster + registry
│   └── push_selected_services.sh    # Build + push images
└── k8s/
    └── deploy_organism.sh            # Deploy completo orchestrado
```

### Código Backend
```
backend/services/auth_service/database.py  # Fixed PostgreSQL connection
```

## 🚀 Comandos Úteis

### Conectar ao cluster
```bash
gcloud container clusters get-credentials vertice-us-cluster --region=us-east1
```

### Ver pods
```bash
kubectl get pods -n vertice
kubectl get pods -n vertice -o wide
kubectl get pods -n vertice --sort-by=.metadata.creationTimestamp
```

### Logs
```bash
# Specific pod
kubectl logs -n vertice <pod-name>

# All pods of a service
kubectl logs -n vertice -l app=maximus-core-service --tail=50

# Follow logs
kubectl logs -n vertice <pod-name> -f
```

### Escalar serviços
```bash
# Scale down
kubectl scale deployment --all -n vertice --replicas=0 --selector=tier=imunologia

# Scale up
kubectl scale deployment --all -n vertice --replicas=1 --selector=tier=consciencia
```

### Redeploy
```bash
# Apply changes
kubectl apply -f k8s/camada-2-consciencia/

# Force restart
kubectl rollout restart deployment/maximus-core-service -n vertice

# Delete pods (recreate with new config)
kubectl delete pods -n vertice -l tier=consciencia
```

### Docker/Registry
```bash
# Configure Docker auth
gcloud auth configure-docker us-east1-docker.pkg.dev

# List images
gcloud artifacts docker images list us-east1-docker.pkg.dev/projeto-vertice/vertice-images

# Build and push
docker build -t us-east1-docker.pkg.dev/projeto-vertice/vertice-images/maximus_core_service:latest .
docker push us-east1-docker.pkg.dev/projeto-vertice/vertice-images/maximus_core_service:latest
```

## ⏭️ Próximas Ações (Prioridade)

### 1. 🔴 CRÍTICO: Fix MAXIMUS `_demonstration` Module

**Localização no PC do usuário**: ❓ (precisa encontrar)

**Opções**:
a) Copiar `_demonstration/` para `backend/services/maximus_core_service/`
b) Refatorar import em `main.py` para usar módulo existente
c) Verificar se `MaximusIntegrated` existe em outro lugar

**Após fix**:
```bash
cd backend/services/maximus_core_service
docker build -t us-east1-docker.pkg.dev/projeto-vertice/vertice-images/maximus_core_service:latest .
docker push us-east1-docker.pkg.dev/projeto-vertice/vertice-images/maximus_core_service:latest

# Repeat for all 5 MAXIMUS services

kubectl rollout restart deployment -n vertice -l tier=consciencia
```

### 2. 🟡 IMPORTANTE: Fix Kafka

**Debug**:
```bash
kubectl logs -n vertice kafka-0 -c kafka --tail=100
kubectl describe pod kafka-0 -n vertice
```

**Investigar**:
- Por que Kafka está crashando mesmo com startup delay?
- Verificar Zookeeper logs
- Testar conectividade localhost:2181

### 3. 🟢 Deploy Immune System (SOMENTE APÓS MAXIMUS OK)

**Verificar MAXIMUS Ready**:
```bash
kubectl get pods -n vertice -l tier=consciencia
# Todos devem estar 1/1 Running
```

**Ativar Imunologia**:
```bash
kubectl scale deployment --all -n vertice --replicas=1 --selector=tier=imunologia
kubectl get pods -n vertice -l tier=imunologia -w
```

### 4. 🔵 Validação Final

- [ ] Todos os 15 serviços Running (17 pods total: 7 foundation + 5 MAXIMUS + 5 immune)
- [ ] Health checks passando
- [ ] Verificar logs para erros
- [ ] Testar API Gateway external endpoint
- [ ] Validar comunicação inter-serviços

## 🐛 Issues Conhecidos

1. **MAXIMUS crashando**: `ModuleNotFoundError: No module named '_demonstration'`
2. **Kafka crashando**: Zookeeper OK mas Kafka container falha
3. **Immune system desligado**: Preventivo, aguardando MAXIMUS

## 📝 Notas do Usuário

- "tem uma sequencia de inicialização do organismo" - MAXIMUS precisa estar ativo antes do sistema imune
- "no meu pc ta rodando" KKKKKKKKKK - `_demonstration` existe localmente mas não no repo
- "arruma esse kafka, n é critico agora, mas acumula e fica uma merda depois pra debugar"
- "ok, mas voltamos nele em BREVE" - sobre Kafka

---

**Para continuar**:
1. Localizar `_demonstration` no PC
2. Commitar ao repo
3. Rebuild/push MAXIMUS images
4. Deploy e validar

**Cluster permanece ativo**, pode retomar o deploy a qualquer momento.

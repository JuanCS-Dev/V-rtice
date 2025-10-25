# 🔐 PLANO DE CORREÇÃO AIR GAP - ARQUITETURA PRIVADA

**Data**: 2025-10-25 21:48 BRT  
**Objetivo**: Conectar Frontend (Cloud Run) → Backend (GKE) via rede privada  
**Princípio**: Zero exposição pública até validação completa  
**Estratégia**: VPC Connector + DNS Interno + Firewall Zero Trust

---

## 📋 ARQUITETURA ALVO

```
┌─────────────────────────────────────────────────────────────┐
│ CAMADA PÚBLICA (Controlada)                                 │
├─────────────────────────────────────────────────────────────┤
│ Cloud Run (Frontend)                                        │
│ ├─ HTTPS público (ingress controlado por IAM)              │
│ └─ VPC Egress via Connector (todo tráfego backend)         │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ VPC Connector (10.8.0.0/28)
               │
┌──────────────▼──────────────────────────────────────────────┐
│ CAMADA PRIVADA (Zero acesso externo)                        │
├─────────────────────────────────────────────────────────────┤
│ GKE Cluster (vertice-us-cluster)                            │
│ ├─ Services: ClusterIP (DNS interno)                        │
│ ├─ api-gateway.vertice.svc.cluster.local:8000              │
│ ├─ maximus-core-service.vertice.svc.cluster.local:8150     │
│ ├─ auth-service.vertice.svc.cluster.local:8006             │
│ └─ service-registry.vertice.svc.cluster.local:8761         │
│                                                              │
│ Firewall Rules:                                             │
│ ├─ ALLOW: VPC Connector → GKE Nodes                        │
│ ├─ DENY: * → GKE (default)                                 │
│ └─ ALLOW: GKE internal ↔ GKE internal                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 FASE 1: PREPARAÇÃO E VALIDAÇÃO (15 min)

### 1.1 Validar Estado Atual GKE
**Objetivo**: Confirmar que backend está funcional internamente

```bash
# Verificar pods funcionais
kubectl get pods -n vertice -o wide

# Testar conectividade interna (de dentro do cluster)
kubectl run -n vertice test-curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://api-gateway.vertice.svc.cluster.local:8000/health

# Validar DNS interno
kubectl run -n vertice test-dns --rm -it --image=busybox --restart=Never -- \
  nslookup api-gateway.vertice.svc.cluster.local
```

**Critério de Sucesso**:
- ✅ Todos os pods `Running` (16/16)
- ✅ DNS interno resolve corretamente
- ✅ `/health` endpoint responde HTTP 200

**Bloqueador**: Se falhar, corrigir antes de prosseguir (rollback deploy se necessário)

---

### 1.2 Auditar Configuração de Rede GKE
**Objetivo**: Confirmar que cluster está em VPC padrão e range de IPs

```bash
# Verificar VPC e subnet
gcloud container clusters describe vertice-us-cluster \
  --region=us-east1 \
  --format="value(network,subnetwork,clusterIpv4Cidr)"

# Verificar firewall rules existentes
gcloud compute firewall-rules list \
  --filter="network:default AND direction:INGRESS" \
  --format="table(name,sourceRanges,allowed)"

# Confirmar que GKE não tem IP externo
kubectl get svc -n vertice -o wide | grep LoadBalancer
# Esperado: Nenhum resultado (ou EXTERNAL-IP = <none>)
```

**Critério de Sucesso**:
- ✅ Network: `default` (ou VPC customizada identificada)
- ✅ Nenhum serviço com IP externo
- ✅ Firewall rules padrão GKE presentes

---

## 🔧 FASE 2: CRIAÇÃO DO VPC CONNECTOR (20 min)

### 2.1 Criar Serverless VPC Access Connector
**Objetivo**: Ponte privada Cloud Run → VPC

```bash
# Criar connector (range isolado, sem conflito com GKE)
gcloud compute networks vpc-access connectors create vertice-private-connector \
  --project=projeto-vertice \
  --region=us-east1 \
  --network=default \
  --range=10.8.0.0/28 \
  --min-instances=2 \
  --max-instances=10 \
  --machine-type=e2-micro

# Aguardar provisionamento (5-10 min)
gcloud compute networks vpc-access connectors describe vertice-private-connector \
  --region=us-east1 \
  --format="value(state)"
# Esperado: READY
```

**Validação**:
```bash
# Confirmar subnet criada
gcloud compute networks subnets list \
  --filter="name~vertice-private-connector" \
  --format="table(name,region,ipCidrRange)"
```

**Critério de Sucesso**:
- ✅ Connector `state=READY`
- ✅ Subnet `10.8.0.0/28` criada
- ✅ Instâncias min=2 rodando

**Custo**: ~$28/mês (2 instâncias e2-micro + dados)

---

### 2.2 Configurar Firewall Rules para Connector
**Objetivo**: Permitir APENAS tráfego Connector → GKE

```bash
# Obter range de IPs dos nodes GKE
GKE_NODE_RANGE=$(gcloud container clusters describe vertice-us-cluster \
  --region=us-east1 \
  --format="value(clusterIpv4Cidr)")

# Regra 1: Permitir Connector → GKE Nodes (porta 8000, 8006, 8150, 8761)
gcloud compute firewall-rules create allow-connector-to-gke \
  --network=default \
  --priority=1000 \
  --direction=INGRESS \
  --action=ALLOW \
  --source-ranges=10.8.0.0/28 \
  --target-tags=gke-vertice-us-cluster \
  --rules=tcp:8000,tcp:8006,tcp:8150,tcp:8761 \
  --description="Permite Cloud Run via VPC Connector acessar backend GKE"

# Regra 2: Negar qualquer outro acesso externo aos serviços backend
gcloud compute firewall-rules create deny-external-to-backend \
  --network=default \
  --priority=1100 \
  --direction=INGRESS \
  --action=DENY \
  --source-ranges=0.0.0.0/0 \
  --target-tags=gke-vertice-us-cluster \
  --rules=tcp:8000,tcp:8006,tcp:8150,tcp:8761 \
  --description="Bloqueia acesso externo direto aos serviços backend"
```

**Validação**:
```bash
# Listar regras criadas
gcloud compute firewall-rules list \
  --filter="name:(allow-connector-to-gke OR deny-external-to-backend)" \
  --format="table(name,direction,priority,sourceRanges,allowed,denied)"
```

**Critério de Sucesso**:
- ✅ Regra ALLOW (priority 1000) para Connector
- ✅ Regra DENY (priority 1100) para resto do mundo
- ✅ Target tags correspondem aos nodes GKE

---

## 🚀 FASE 3: INTEGRAÇÃO CLOUD RUN → VPC (15 min)

### 3.1 Configurar Cloud Run para usar VPC Connector
**Objetivo**: Rotear todo tráfego de egress via VPC privada

```bash
# Atualizar serviço Cloud Run
gcloud run services update vertice-frontend \
  --project=projeto-vertice \
  --region=us-east1 \
  --vpc-connector=vertice-private-connector \
  --vpc-egress=all-traffic \
  --no-allow-unauthenticated

# Confirmar configuração
gcloud run services describe vertice-frontend \
  --region=us-east1 \
  --format="value(spec.template.spec.containers[0].env,spec.template.metadata.annotations)"
```

**Nota**: `--no-allow-unauthenticated` requer IAM token para acesso (adicionar depois se precisar público)

**Critério de Sucesso**:
- ✅ VPC connector configurado
- ✅ Egress = `all-traffic` (não `private-ranges-only`)
- ✅ Deploy bem-sucedido sem erros

---

### 3.2 Testar Conectividade Cloud Run → GKE (Diagnóstico)
**Objetivo**: Validar que Cloud Run consegue resolver DNS interno GKE

```bash
# Deploy temporário de debug container no Cloud Run
cat > /tmp/debug-cloudrun.yaml <<EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: vertice-debug
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/vpc-access-connector: vertice-private-connector
        run.googleapis.com/vpc-access-egress: all-traffic
    spec:
      containers:
      - image: curlimages/curl:latest
        command: ["/bin/sh"]
        args: ["-c", "while true; do sleep 3600; done"]
EOF

gcloud run services replace /tmp/debug-cloudrun.yaml \
  --region=us-east1 \
  --platform=managed

# Executar comando de teste
gcloud run services proxy vertice-debug --region=us-east1 &
PROXY_PID=$!
sleep 5

# Testar DNS e conectividade
curl -v "http://localhost:8080/exec?cmd=nslookup%20api-gateway.vertice.svc.cluster.local"
curl -v "http://localhost:8080/exec?cmd=curl%20-I%20http://api-gateway.vertice.svc.cluster.local:8000/health"

kill $PROXY_PID
```

**Alternativa (mais simples)**:
```bash
# Usar Cloud Shell para testar de dentro da VPC
gcloud compute instances create test-vpc-access \
  --zone=us-east1-b \
  --machine-type=e2-micro \
  --network=default \
  --subnet=default \
  --scopes=cloud-platform

# SSH e testar
gcloud compute ssh test-vpc-access --zone=us-east1-b --command="
  curl -v http://api-gateway.vertice.svc.cluster.local:8000/health
"

# Limpar
gcloud compute instances delete test-vpc-access --zone=us-east1-b --quiet
```

**Critério de Sucesso**:
- ✅ DNS resolve `api-gateway.vertice.svc.cluster.local`
- ✅ HTTP 200 de `/health`
- ✅ Latência < 100ms

**Bloqueador**: Se falhar, verificar:
- Firewall rules aplicadas corretamente
- GKE nodes têm network tag correto
- VPC Connector em `READY`

---

## 🎨 FASE 4: REBUILD FRONTEND COM DNS INTERNO (30 min)

### 4.1 Atualizar Configuração Frontend
**Objetivo**: Substituir `localhost` por DNS interno K8s

```bash
cd /home/juan/vertice-dev/frontend

# Criar arquivo .env.production
cat > .env.production <<EOF
# Backend URLs (DNS interno K8s)
VITE_API_GATEWAY_URL=http://api-gateway.vertice.svc.cluster.local:8000
VITE_AUTH_SERVICE_URL=http://auth-service.vertice.svc.cluster.local:8006
VITE_MAXIMUS_CORE_URL=http://maximus-core-service.vertice.svc.cluster.local:8150
VITE_SERVICE_REGISTRY_URL=http://service-registry.vertice.svc.cluster.local:8761

# Feature flags
VITE_ENABLE_DEBUG=false
VITE_ENVIRONMENT=production-private
EOF
```

**Validação**:
```bash
# Verificar que variáveis estão corretas
cat .env.production | grep -E "(API_GATEWAY|AUTH_SERVICE|MAXIMUS)"
```

---

### 4.2 Build e Deploy Frontend
**Objetivo**: Gerar bundle com URLs internas hardcoded

```bash
cd /home/juan/vertice-dev/frontend

# Build com env vars
npm run build

# Verificar que bundle NÃO tem localhost
grep -r "localhost" dist/ && echo "❌ ERRO: localhost ainda presente!" || echo "✅ OK"

# Verificar que bundle TEM DNS interno
grep -r "vertice.svc.cluster.local" dist/ && echo "✅ DNS interno presente" || echo "❌ ERRO"

# Build imagem Docker
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker build -t gcr.io/projeto-vertice/vertice-frontend:private-${TIMESTAMP} .

# Push para GCR
docker push gcr.io/projeto-vertice/vertice-frontend:private-${TIMESTAMP}

# Deploy no Cloud Run
gcloud run deploy vertice-frontend \
  --project=projeto-vertice \
  --region=us-east1 \
  --image=gcr.io/projeto-vertice/vertice-frontend:private-${TIMESTAMP} \
  --vpc-connector=vertice-private-connector \
  --vpc-egress=all-traffic \
  --set-env-vars="NODE_ENV=production" \
  --no-allow-unauthenticated \
  --min-instances=1 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=60s
```

**Critério de Sucesso**:
- ✅ Build sem erros
- ✅ Zero ocorrências de `localhost` em `dist/`
- ✅ Deploy Cloud Run HTTP 200

---

## ✅ FASE 5: VALIDAÇÃO END-TO-END (20 min)

### 5.1 Teste de Conectividade Completo
**Objetivo**: Confirmar fluxo Frontend → Backend funcional

```bash
# Obter URL do Cloud Run
FRONTEND_URL=$(gcloud run services describe vertice-frontend \
  --region=us-east1 \
  --format="value(status.url)")

# Gerar token de autenticação (necessário para Cloud Run privado)
TOKEN=$(gcloud auth print-identity-token)

# Teste 1: Frontend carrega
curl -H "Authorization: Bearer $TOKEN" "$FRONTEND_URL" -I

# Teste 2: Frontend consegue chamar backend (via browser DevTools ou proxy)
# Executar no Cloud Shell (mesmo contexto VPC)
gcloud run services proxy vertice-frontend --region=us-east1 &
PROXY_PID=$!
sleep 5

# Simular request do frontend
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080" \
  -H "X-Test-Backend: true" \
  -v

kill $PROXY_PID
```

---

### 5.2 Verificar Logs de Conectividade
**Objetivo**: Confirmar que requests chegam no backend GKE

```bash
# Logs Cloud Run (frontend)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertice-frontend" \
  --limit=50 \
  --format=json | jq '.[] | select(.jsonPayload.message | contains("api-gateway"))'

# Logs GKE (backend - api-gateway)
kubectl logs -n vertice -l app=api-gateway --tail=100 | grep -E "(GET|POST|PUT|DELETE)"

# Verificar se há requests vindos do range do VPC Connector (10.8.0.0/28)
kubectl logs -n vertice -l app=api-gateway --tail=100 | grep "10.8.0"
```

**Critério de Sucesso**:
- ✅ Logs frontend mostram requests para `*.svc.cluster.local`
- ✅ Logs backend mostram requests com source IP `10.8.0.*`
- ✅ Zero erros de DNS resolution
- ✅ Zero timeout errors

---

### 5.3 Teste de Segurança (Validar Isolamento)
**Objetivo**: Confirmar que backend NÃO é acessível externamente

```bash
# Tentar acessar backend diretamente (deve falhar)
# Obter IP de um node GKE
GKE_NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')

# Teste 1: Tentar porta 8000 (deve ser bloqueada)
curl -v --connect-timeout 5 http://${GKE_NODE_IP}:8000/health
# Esperado: Connection refused ou timeout

# Teste 2: Confirmar que não há serviços LoadBalancer
kubectl get svc -n vertice -o json | jq '.items[] | select(.spec.type=="LoadBalancer")'
# Esperado: Vazio

# Teste 3: Confirmar que não há Ingress público
kubectl get ingress -A
# Esperado: No resources found
```

**Critério de Sucesso**:
- ✅ Nenhuma porta backend acessível externamente
- ✅ Firewall rules negam acesso externo
- ✅ Zero serviços LoadBalancer
- ✅ Zero Ingress configurados

---

## 📊 FASE 6: MONITORAMENTO E OBSERVABILIDADE (15 min)

### 6.1 Configurar Alertas de Conectividade
**Objetivo**: Detectar falhas na ponte VPC

```bash
# Alerta 1: VPC Connector saturado (>80% utilização)
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="VPC Connector Alta Utilização" \
  --condition-display-name="Connector >80% capacity" \
  --condition-threshold-value=0.8 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="vpc_access_connector" AND metric.type="vpcaccess.googleapis.com/connector/connections"'

# Alerta 2: Cloud Run → Backend latência alta (>500ms)
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="Latência Frontend→Backend Alta" \
  --condition-display-name="Latency >500ms" \
  --condition-threshold-value=500 \
  --condition-threshold-duration=60s \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"'
```

---

### 6.2 Dashboard de Conectividade Privada
**Objetivo**: Visibilidade centralizada do fluxo privado

```bash
# Criar dashboard customizado
cat > /tmp/vpc-connectivity-dashboard.json <<EOF
{
  "displayName": "Vértice - Conectividade Privada",
  "gridLayout": {
    "widgets": [
      {
        "title": "VPC Connector - Conexões Ativas",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"vpc_access_connector\" AND metric.type=\"vpcaccess.googleapis.com/connector/connections\""
              }
            }
          }]
        }
      },
      {
        "title": "Cloud Run - Requests",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
              }
            }
          }]
        }
      },
      {
        "title": "GKE Backend - HTTP 5xx",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"k8s_pod\" AND metric.type=\"kubernetes.io/container/http_5xx_count\""
              }
            }
          }]
        }
      }
    ]
  }
}
EOF

gcloud monitoring dashboards create --config-from-file=/tmp/vpc-connectivity-dashboard.json
```

---

## 🔐 FASE 7: HARDENING DE SEGURANÇA (10 min)

### 7.1 Configurar IAM Restritivo
**Objetivo**: Acesso ao frontend apenas para usuários autorizados

```bash
# Remover acesso público (já feito com --no-allow-unauthenticated)
gcloud run services remove-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="allUsers" \
  --role="roles/run.invoker" \
  2>/dev/null || true

# Adicionar usuários/SAs específicos
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="user:admin@vertice.com" \
  --role="roles/run.invoker"

# Para acesso via gcloud auth (desenvolvimento)
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="serviceAccount:$(gcloud config get-value account)" \
  --role="roles/run.invoker"
```

---

### 7.2 Audit Logging
**Objetivo**: Registrar todos os acessos ao sistema

```bash
# Habilitar audit logs para Cloud Run
cat > /tmp/audit-config.yaml <<EOF
auditConfigs:
- service: run.googleapis.com
  auditLogConfigs:
  - logType: ADMIN_READ
  - logType: DATA_READ
  - logType: DATA_WRITE
EOF

gcloud projects set-iam-policy projeto-vertice /tmp/audit-config.yaml
```

---

## 📝 CHECKLIST FINAL

### Pré-Deploy
- [ ] GKE pods 16/16 Running
- [ ] DNS interno K8s funcional
- [ ] Nenhum serviço GKE exposto publicamente

### Deploy VPC Connector
- [ ] VPC Connector criado (state=READY)
- [ ] Firewall rule ALLOW (Connector → GKE)
- [ ] Firewall rule DENY (Internet → GKE)

### Deploy Cloud Run
- [ ] Frontend buildado com DNS interno
- [ ] Zero ocorrências de `localhost` no bundle
- [ ] VPC Connector configurado
- [ ] IAM policy restritivo aplicado

### Validação
- [ ] Cloud Run consegue resolver DNS K8s
- [ ] Requests chegam no backend GKE
- [ ] Logs mostram source IP 10.8.0.*
- [ ] Backend NÃO acessível externamente

### Monitoramento
- [ ] Dashboard de conectividade criado
- [ ] Alertas de latência configurados
- [ ] Audit logs habilitados

---

## 🚨 ROLLBACK PLAN

Se algo falhar, executar:

```bash
# Reverter Cloud Run para imagem anterior
gcloud run services update vertice-frontend \
  --region=us-east1 \
  --image=gcr.io/projeto-vertice/vertice-frontend:PREVIOUS_TAG

# Remover VPC Connector (se necessário)
gcloud compute networks vpc-access connectors delete vertice-private-connector \
  --region=us-east1 \
  --quiet

# Remover firewall rules
gcloud compute firewall-rules delete allow-connector-to-gke --quiet
gcloud compute firewall-rules delete deny-external-to-backend --quiet
```

---

## 📊 MÉTRICAS DE SUCESSO

- ✅ **Conectividade**: Frontend → Backend latência < 100ms
- ✅ **Segurança**: Zero portas backend expostas publicamente
- ✅ **Disponibilidade**: 99.9% uptime (validar em 24h)
- ✅ **Performance**: VPC Connector utilização < 50%
- ✅ **Custo**: ~$30/mês (VPC Connector + mínimas instâncias Cloud Run)

---

## 📁 ARTIFACTS GERADOS

- `/tmp/debug-cloudrun.yaml` - Debug container
- `/tmp/vpc-connectivity-dashboard.json` - Dashboard
- `/tmp/audit-config.yaml` - Audit logging
- `frontend/.env.production` - Configuração DNS interno
- `gcr.io/projeto-vertice/vertice-frontend:private-YYYYMMDD-HHMMSS` - Imagem

---

**PRONTO PARA EXECUÇÃO**: Aguardando aprovação do Arquiteto-Chefe.

**TEMPO ESTIMADO TOTAL**: 2h 5min

**JANELA DE RISCO**: Zero (nenhuma alteração afeta infraestrutura existente até deploy final)

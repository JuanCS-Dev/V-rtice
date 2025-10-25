# 🔴 DIAGNÓSTICO COMPLETO - AIR GAPS VÉRTICE GCP

**Data**: 2025-10-25 18:30 BRT  
**Arquitetura**: Híbrida (Frontend Cloud Run + Backend GKE)  
**Status**: 🔴 **SISTEMA DESCONECTADO - MÚLTIPLOS AIR GAPS CRÍTICOS**

---

## 📊 RESUMO EXECUTIVO

### Frontend (Cloud Run)
- ✅ **Deployado**: `vertice-frontend-00003-js4`
- ✅ **Acessível**: https://vertice-frontend-vuvnhfmzpa-ue.a.run.app
- ✅ **HTTP 200**: Aplicação respondendo
- 🔴 **PROBLEMA**: Hardcoded `localhost:*` URLs no código
- 🔴 **PROBLEMA**: Zero variáveis de ambiente configuradas

### Backend (GKE)
- ✅ **Cluster**: `vertice-us-cluster` (us-east1)
- ✅ **Pods**: 16/16 Running (conforme ESTADO_DEPLOY_GKE_ATUAL.md)
- 🔴 **PROBLEMA**: Nenhum serviço exposto externamente
- 🔴 **PROBLEMA**: Zero Load Balancers
- 🔴 **PROBLEMA**: Zero Ingress configurados

---

## 🔴 AIR GAPS CRÍTICOS DETECTADOS

### 1. Frontend Hardcoded para Localhost
**Severidade**: 🔴 CRÍTICO  
**Evidência**:
```bash
# Frontend HTML contém apenas:
http://localhost:*
https://unpkg.com;  # CDN externo
```

**Impact**: Frontend não consegue conectar com backend em **NENHUMA** condição.

**Root Cause**: Build sem env vars (`VITE_API_GATEWAY_URL`, etc.)

---

### 2. Backend GKE Completamente Privado
**Severidade**: 🔴 CRÍTICO  
**Evidência**:
```bash
# GKE Services
gcloud run services list → 0 serviços LoadBalancer
kubectl get ingress -A → No ingress found
kubectl get svc -A | grep External → ⚠️ No external IPs exposed
```

**Services Criticos Inacessíveis**:
- ❌ `api-gateway` (porta 8000)
- ❌ `maximus-core-service` (porta 8150)
- ❌ `auth-service` (porta 8006)
- ❌ `service-registry` (sem manifesto encontrado)

**Root Cause**: Services criados como `ClusterIP` (padrão K8s = interno apenas)

---

### 3. Nenhuma Ponte Cloud Run ↔ GKE
**Severidade**: 🔴 CRÍTICO  
**Evidência**:
- Zero VPC Connectors configurados
- Zero Ingress/Gateway entre Cloud Run e GKE
- Zero configuração de rede híbrida

**Impact**: Arquitetura completamente segmentada (frontend isolado do backend)

---

## 💡 PLANO DE CORREÇÃO (3 Opções)

### OPÇÃO 1: Ingress + Load Balancer Público (RÁPIDO - 30min)
**Recomendado para**: Desenvolvimento/Staging

```bash
# PASSO 1: Expor api-gateway via LoadBalancer
kubectl patch svc api-gateway -n vertice -p '{"spec":{"type":"LoadBalancer"}}'

# PASSO 2: Obter IP externo (aguardar ~2min)
GATEWAY_IP=$(kubectl get svc api-gateway -n vertice -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# PASSO 3: Atualizar frontend Cloud Run
gcloud run services update vertice-frontend \
  --project=projeto-vertice \
  --region=us-east1 \
  --set-env-vars="VITE_API_GATEWAY_URL=http://${GATEWAY_IP}:8000"

# PASSO 4: Rebuild frontend com novas env vars
cd frontend && npm run build
docker build -t gcr.io/projeto-vertice/vertice-frontend:latest .
docker push gcr.io/projeto-vertice/vertice-frontend:latest
gcloud run deploy vertice-frontend --image=gcr.io/projeto-vertice/vertice-frontend:latest
```

**Prós**: Simples, rápido  
**Contras**: IP público do backend (precisa firewall rules)

---

### OPÇÃO 2: Ingress + HTTPS + DNS (PRODUÇÃO - 2h)
**Recomendado para**: Produção

```bash
# PASSO 1: Criar Ingress com IP reservado
gcloud compute addresses create vertice-api-ip --global

# PASSO 2: Configurar Ingress YAML
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vertice-api-ingress
  namespace: vertice
  annotations:
    kubernetes.io/ingress.global-static-ip-name: "vertice-api-ip"
    networking.gke.io/managed-certificates: "vertice-api-cert"
spec:
  rules:
  - host: api.vertice.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000

# PASSO 3: Certificado SSL gerenciado
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: vertice-api-cert
  namespace: vertice
spec:
  domains:
    - api.vertice.example.com

# PASSO 4: Atualizar DNS A record
# api.vertice.example.com → [IP do Ingress]

# PASSO 5: Atualizar frontend
gcloud run services update vertice-frontend \
  --set-env-vars="VITE_API_GATEWAY_URL=https://api.vertice.example.com"
```

**Prós**: Seguro, escalável, produção-ready  
**Contras**: Requer domínio, tempo de provisionamento SSL

---

### OPÇÃO 3: VPC Connector + Internal LB (MAIS SEGURO - 3h)
**Recomendado para**: Compliance/Segurança máxima

```bash
# PASSO 1: Criar VPC Connector
gcloud compute networks vpc-access connectors create vertice-connector \
  --region=us-east1 \
  --network=default \
  --range=10.8.0.0/28

# PASSO 2: Configurar Cloud Run para usar VPC
gcloud run services update vertice-frontend \
  --vpc-connector=vertice-connector \
  --vpc-egress=all-traffic

# PASSO 3: Services GKE já estão acessíveis via DNS interno
# (api-gateway.vertice.svc.cluster.local)

# PASSO 4: Atualizar frontend env vars
gcloud run services update vertice-frontend \
  --set-env-vars="VITE_API_GATEWAY_URL=http://api-gateway.vertice.svc.cluster.local:8000"
```

**Prós**: Sem exposição pública, tráfego privado  
**Contras**: Custo VPC Connector ($40/mês), complexidade

---

## 🚨 AÇÃO IMEDIATA RECOMENDADA

**OPÇÃO 1** (LoadBalancer público) para **DESTRAVAR AGORA**:

```bash
#!/bin/bash
# Fix Air Gap - Solução Rápida (5 minutos)

# 1. Expor API Gateway
kubectl patch svc api-gateway -n vertice -p '{"spec":{"type":"LoadBalancer"}}'

# 2. Aguardar IP (pode levar 2-3 min)
echo "Aguardando IP externo..."
while true; do
  IP=$(kubectl get svc api-gateway -n vertice -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
  if [ -n "$IP" ]; then
    echo "✅ IP obtido: $IP"
    break
  fi
  sleep 5
done

# 3. Testar backend
curl http://$IP:8000/health

# 4. Atualizar frontend
export API_URL="http://$IP:8000"
cd frontend
VITE_API_GATEWAY_URL=$API_URL npm run build
docker build -t gcr.io/projeto-vertice/vertice-frontend:fix-$(date +%s) .
docker push gcr.io/projeto-vertice/vertice-frontend:fix-$(date +%s)
gcloud run deploy vertice-frontend \
  --image=gcr.io/projeto-vertice/vertice-frontend:fix-$(date +%s) \
  --set-env-vars="VITE_API_GATEWAY_URL=$API_URL"

echo "✅ Air Gap corrigido!"
echo "Frontend: https://vertice-frontend-vuvnhfmzpa-ue.a.run.app"
echo "Backend: $API_URL"
```

---

## 📋 CHECKLIST PÓS-CORREÇÃO

- [ ] Frontend consegue fazer `fetch()` para backend
- [ ] Backend `/health` retorna 200
- [ ] Auth flow funciona end-to-end
- [ ] Logs do Cloud Run mostram requests bem-sucedidos
- [ ] GKE api-gateway logs mostram requests do frontend

---

## 📁 ARQUIVOS RELEVANTES

- `/home/juan/vertice-dev/ESTADO_DEPLOY_GKE_ATUAL.md` - Estado backend
- `/home/juan/vertice-dev/k8s/camada-1-fundacao/api-gateway-deployment.yaml`
- `/home/juan/vertice-dev/frontend/DEPLOYMENT.md`
- `/tmp/gcp_connectivity_diagnosis_*.json` - Diagnóstico completo


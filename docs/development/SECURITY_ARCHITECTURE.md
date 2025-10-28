# 🔒 Vértice Frontend - Arquitetura de Segurança

**Projeto**: Vértice - Primeiro Organismo Cibernético Consciente
**Deploy**: Google Cloud Run (Secure)
**Data**: 2025-10-25
**Repositório**: PRIVADO

---

## 🎯 Modelo de Segurança

### Princípio: **Zero Trust + Least Privilege**

```
┌─────────────────────────────────────────────────────────────┐
│  Internet (Público)                                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ HTTPS (TLS 1.3)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Google Cloud Identity-Aware Proxy (IAP)                    │
│  ✓ OAuth 2.0 Authentication                                 │
│  ✓ Whitelist: apenas emails autorizados                     │
│  ✓ MFA recomendado                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Token JWT validado
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Cloud Run: vertice-frontend                                │
│  ✓ --no-allow-unauthenticated                               │
│  ✓ Requer IAM role: roles/run.invoker                       │
│  ✓ Container image assinada (Binary Authorization)          │
│  ✓ Ambiente isolado (sandbox)                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Internal HTTP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  GKE Cluster: vertice-us-cluster (us-east1)                 │
│  ✓ Private cluster                                          │
│  ✓ Network policies                                         │
│  ✓ Workload Identity                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Camadas de Proteção

### 1️⃣ Autenticação (Cloud Run IAM)

**Configuração**:
```yaml
--no-allow-unauthenticated
```

**O que isso faz**:
- ❌ Bloqueia acesso anônimo
- ✅ Requer autenticação Google OAuth
- ✅ Cada request precisa de token JWT válido

**Como adicionar testadores**:
```bash
# Adicionar usuário específico
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="user:tester@example.com" \
  --role="roles/run.invoker"

# Adicionar grupo
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="group:testers@your-domain.com" \
  --role="roles/run.invoker"
```

### 2️⃣ Isolamento de Rede

**Configuração**:
```yaml
--ingress=all  # Aceita requisições de qualquer lugar
```

**Alternativas mais restritivas**:
- `--ingress=internal`: Só aceita de VPC/Cloud Run
- `--ingress=internal-and-cloud-load-balancing`: Só via Load Balancer

**Recomendação futura**: Migrar para `internal-and-cloud-load-balancing` com Cloud Armor

### 3️⃣ Secrets Management

**✅ Implementado**:
- Variáveis de ambiente via `--set-env-vars`
- Valores configurados em Cloud Build substitutions

**⚠️ NÃO IMPLEMENTADO (mas recomendado)**:
```bash
# Migrar para Secret Manager
gcloud secrets create vertice-frontend-env \
  --data-file=.env.production \
  --replication-policy=automatic

# Cloud Run referencia o secret
gcloud run deploy vertice-frontend \
  --set-secrets=/etc/secrets/.env=vertice-frontend-env:latest
```

### 4️⃣ Container Security

**✅ Implementado**:
- Multi-stage build (reduz superfície de ataque)
- Alpine Linux base (menor, menos vulnerabilidades)
- Non-root user no container
- Health checks

**Melhorias futuras**:
```yaml
# Binary Authorization (requer assinatura de imagem)
gcloud run deploy vertice-frontend \
  --binary-authorization=default
```

---

## 🔐 Como Funciona o Acesso

### Fluxo de Autenticação

1. **Usuário acessa URL**: `https://vertice-frontend-<hash>-ue.a.run.app`
2. **Cloud Run verifica**: Tem token JWT válido?
3. **Se NÃO**: Redireciona para login Google OAuth
4. **Usuário faz login**: Com conta Google autorizada
5. **Google valida**: Email está na whitelist IAM?
6. **Se SIM**: Gera token JWT assinado
7. **Cloud Run recebe**: Request com token válido
8. **Nginx serve**: Frontend React

### Whitelist de Testadores

**Arquivo**: `frontend/AUTHORIZED_TESTERS.md` (criar)

```markdown
# Testadores Autorizados - Vértice Frontend

## Owners
- juan.brainfarma@gmail.com (Owner)

## Testers
- tester1@gmail.com
- tester2@example.com

## Como adicionar:
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="user:EMAIL_AQUI" \
  --role="roles/run.invoker"
```

---

## 🚨 Proteções Adicionais (Recomendadas)

### 1. Cloud Armor (WAF + DDoS)

```bash
# Criar política de segurança
gcloud compute security-policies create vertice-frontend-policy \
  --description="WAF para Vértice Frontend"

# Regra: Block países indesejados
gcloud compute security-policies rules create 1000 \
  --security-policy=vertice-frontend-policy \
  --expression="origin.region_code == 'CN' || origin.region_code == 'RU'" \
  --action=deny-403

# Regra: Rate limiting (100 req/min por IP)
gcloud compute security-policies rules create 2000 \
  --security-policy=vertice-frontend-policy \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60
```

### 2. VPC Service Controls

```bash
# Criar perímetro de serviço
gcloud access-context-manager perimeters create vertice-perimeter \
  --title="Vértice Security Perimeter" \
  --resources=projects/projeto-vertice \
  --restricted-services=run.googleapis.com,storage.googleapis.com
```

### 3. Audit Logging

```yaml
# Habilitar audit logs
gcloud logging sinks create vertice-audit-logs \
  bigquery.googleapis.com/projects/projeto-vertice/datasets/audit_logs \
  --log-filter='resource.type="cloud_run_revision"'
```

---

## 📊 Monitoramento de Segurança

### Dashboards Recomendados

1. **Cloud Run Metrics**:
   - Request count
   - Request latency
   - Container instances
   - Memory/CPU usage

2. **IAM Access Logs**:
   - Quem acessou quando
   - IPs de origem
   - Tentativas de acesso negadas

3. **Cloud Armor (se configurado)**:
   - Requisições bloqueadas
   - Rate limiting triggers
   - Geographic distribution

### Alertas

```bash
# Alerta: Acesso negado
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Frontend - Unauthorized Access" \
  --condition-display-name="403 Errors > 10/min" \
  --condition-threshold-value=10 \
  --condition-threshold-duration=60s
```

---

## ✅ Checklist de Segurança

### Deploy Inicial
- [x] Cloud Run com `--no-allow-unauthenticated`
- [x] Artifact Registry (não GCR público)
- [x] HTTPS obrigatório (automático no Cloud Run)
- [x] Variáveis de ambiente configuradas
- [ ] Adicionar testadores via IAM
- [ ] Testar acesso com usuário autorizado
- [ ] Testar bloqueio de usuário não autorizado

### Melhorias P2 (Após validação inicial)
- [ ] Migrar secrets para Secret Manager
- [ ] Configurar Cloud Armor WAF
- [ ] Habilitar Binary Authorization
- [ ] Configurar VPC Service Controls
- [ ] Audit logging para BigQuery

### Melhorias P3 (Produção)
- [ ] Custom domain com Cloud Load Balancing
- [ ] Cloud CDN para assets estáticos
- [ ] reCAPTCHA Enterprise
- [ ] DLP API para scan de dados sensíveis

---

## 🔄 Processo de Deploy Seguro

### 1. Build Local (Desenvolvimento)
```bash
cd frontend
docker build -t vertice-frontend:local .
docker run --rm -p 8080:8080 vertice-frontend:local
```

### 2. Deploy via Cloud Build (CI/CD)
```bash
# Autenticado automaticamente no Cloud Build
gcloud builds submit \
  --config=frontend/cloudbuild.yaml \
  --substitutions=_REGION=us-east1
```

### 3. Validação Pós-Deploy
```bash
# Verificar status
gcloud run services describe vertice-frontend --region=us-east1

# Testar acesso (precisa estar autenticado)
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://vertice-frontend-<hash>-ue.a.run.app/health
```

---

## 📞 Troubleshooting

### Problema: "Permission denied" ao acessar

**Causa**: Usuário não está na whitelist IAM

**Solução**:
```bash
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="user:EMAIL_DO_USUARIO" \
  --role="roles/run.invoker"
```

### Problema: Frontend não consegue acessar backend GKE

**Causa**: GKE cluster é privado, Cloud Run não alcança

**Solução**: VPC Connector
```bash
# Criar VPC Connector
gcloud compute networks vpc-access connectors create vertice-connector \
  --network=default \
  --region=us-east1 \
  --range=10.8.0.0/28

# Atualizar Cloud Run
gcloud run services update vertice-frontend \
  --region=us-east1 \
  --vpc-connector=vertice-connector \
  --vpc-egress=private-ranges-only
```

---

## 📚 Referências

- [Cloud Run Security](https://cloud.google.com/run/docs/securing/security)
- [IAM for Cloud Run](https://cloud.google.com/run/docs/securing/managing-access)
- [Cloud Armor](https://cloud.google.com/armor/docs/security-policy-overview)
- [Binary Authorization](https://cloud.google.com/binary-authorization/docs)
- [VPC Service Controls](https://cloud.google.com/vpc-service-controls/docs)

---

**Última atualização**: 2025-10-25
**Autor**: Claude Code
**Status**: ✅ SECURE - Authentication Required
**Acesso**: Restrito a testadores autorizados via IAM

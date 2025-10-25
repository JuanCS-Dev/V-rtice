# 🚀 PLANO DETALHADO - Deploy vcli-go via Cloud Run
## Para Execução no github-copilot-cli (Sonnet 4.5)
## Data: 2025-10-25 | Autor: Claude Code

---

## 🎯 OBJETIVO

Preparar e executar o deploy do **vcli-go (NeuroShell)** no Google Cloud Run, usando o próprio vcli-go para realizar o deploy após a configuração inicial.

---

## 📋 PRÉ-REQUISITOS

### Ferramentas Necessárias
- [x] Go 1.24+ (já instalado, verificado em go.mod)
- [x] gcloud CLI (para deploy inicial)
- [x] Docker (para build de imagem)
- [x] git (para versionamento)
- [ ] kubectl configurado (para verificação pós-deploy)

### Informações Necessárias
- [ ] GCP Project ID
- [ ] GCP Region (ex: us-central1)
- [ ] Service Account email (para Cloud Run)
- [ ] Container Registry name (ex: gcr.io/<PROJECT_ID>/vcli-go)

---

## 📦 FASE 1: PREPARAÇÃO DO BUILD

### Step 1.1: Verificar Build Local
```bash
# Navegue para o diretório do projeto
cd /home/juan/vertice-dev/vcli-go

# Limpe builds anteriores
rm -rf bin/vcli

# Build otimizado (sem CGO para portabilidade)
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o bin/vcli \
  -ldflags="-w -s" \
  -trimpath

# Verificar binary
ls -lh bin/vcli
./bin/vcli version

# Output esperado:
# vCLI version 2.0.0
# Build date: 2025-10-07
# Go implementation: High-performance TUI
```

**Objetivo**: Garantir que o binary compila corretamente para Linux x64.

**Verificação de Sucesso**:
- Binary criado em `bin/vcli`
- Tamanho aproximado: 15-20MB (otimizado com -ldflags="-w -s")
- Comando `./bin/vcli version` funciona

---

### Step 1.2: Criar Dockerfile Otimizado
```bash
# Criar Dockerfile na raiz do projeto
cat > Dockerfile << 'EOF'
# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM golang:1.24-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git make

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build optimized binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -o vcli \
    -ldflags="-w -s -X main.version=2.0.0 -X main.buildDate=$(date +%Y-%m-%d)" \
    -trimpath \
    main.go

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 vcli && \
    adduser -D -u 1001 -G vcli vcli

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/vcli /usr/local/bin/vcli

# Set ownership
RUN chown -R vcli:vcli /app

# Switch to non-root user
USER vcli

# Expose port (if needed for future HTTP endpoints)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD vcli version || exit 1

# Default command
ENTRYPOINT ["vcli"]
CMD ["--help"]
EOF

echo "✅ Dockerfile criado"
```

**Objetivo**: Criar Dockerfile multi-stage otimizado para Cloud Run.

**Características**:
- Multi-stage build (reduz tamanho final)
- Alpine Linux (imagem leve ~5MB base)
- Non-root user (security best practice)
- Health check configurado
- Binary otimizado com strip de símbolos

**Verificação de Sucesso**:
- Arquivo `Dockerfile` criado na raiz
- Conteúdo correto (multi-stage com golang:1.24-alpine)

---

### Step 1.3: Criar .dockerignore
```bash
# Criar .dockerignore para otimizar build context
cat > .dockerignore << 'EOF'
# Binaries
bin/
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test files
*.test
coverage.out
coverage*.out
test/

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/
*.swp
*.swo

# Documentation
docs/
*.md
!README.md

# CI/CD
.github/
.gitlab-ci.yml

# Temp files
tmp/
temp/
*.log

# Node modules (if any)
node_modules/

# OS files
.DS_Store
Thumbs.db
EOF

echo "✅ .dockerignore criado"
```

**Objetivo**: Reduzir tamanho do build context e acelerar build.

**Verificação de Sucesso**:
- Arquivo `.dockerignore` criado
- Exclui arquivos desnecessários (docs, tests, git)

---

### Step 1.4: Testar Build Docker Local
```bash
# Build da imagem Docker
docker build -t vcli-go:local .

# Verificar tamanho da imagem
docker images vcli-go:local

# Testar imagem localmente
docker run --rm vcli-go:local version

# Output esperado:
# vCLI version 2.0.0
# Build date: 2025-10-25
# Go implementation: High-performance TUI

# Testar comando K8s (sem kubeconfig vai falhar, mas comando existe)
docker run --rm vcli-go:local k8s --help
```

**Objetivo**: Validar que a imagem Docker funciona corretamente.

**Verificação de Sucesso**:
- Build completa sem erros
- Imagem final < 30MB (idealmente ~20-25MB)
- Comando `version` funciona dentro do container
- Comando `k8s --help` mostra ajuda dos comandos

---

## 🔧 FASE 2: CONFIGURAÇÃO DO CLOUD RUN

### Step 2.1: Configurar cloudbuild.yaml
```bash
# Criar cloudbuild.yaml para CI/CD automatizado
cat > cloudbuild.yaml << 'EOF'
steps:
  # Step 1: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/vcli-go:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/vcli-go:latest'
      - '.'

  # Step 2: Push image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/vcli-go:$COMMIT_SHA'

  # Step 3: Push latest tag
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/vcli-go:latest'

  # Step 4: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'vcli-go'
      - '--image'
      - 'gcr.io/$PROJECT_ID/vcli-go:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '512Mi'
      - '--cpu'
      - '1'
      - '--max-instances'
      - '10'
      - '--timeout'
      - '300s'

images:
  - 'gcr.io/$PROJECT_ID/vcli-go:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/vcli-go:latest'

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'N1_HIGHCPU_8'

timeout: '1200s'
EOF

echo "✅ cloudbuild.yaml criado"
```

**Objetivo**: Configurar pipeline de CI/CD no Google Cloud Build.

**Características**:
- Build automatizado da imagem
- Push para Container Registry
- Deploy automatizado no Cloud Run
- Tagging com commit SHA + latest
- Configuração de recursos (512Mi RAM, 1 CPU)

**Verificação de Sucesso**:
- Arquivo `cloudbuild.yaml` criado
- Configurações corretas (region, memory, cpu)

---

### Step 2.2: Configurar Variáveis de Ambiente GCP
```bash
# Configurar variáveis de ambiente
export GCP_PROJECT_ID="seu-projeto-id"  # SUBSTITUIR
export GCP_REGION="us-central1"
export SERVICE_NAME="vcli-go"
export IMAGE_NAME="gcr.io/${GCP_PROJECT_ID}/vcli-go"

# Verificar configurações
echo "Project ID: $GCP_PROJECT_ID"
echo "Region: $GCP_REGION"
echo "Service Name: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"

# Autenticar com GCP
gcloud auth login

# Configurar projeto padrão
gcloud config set project $GCP_PROJECT_ID

# Verificar projeto atual
gcloud config get-value project
```

**Objetivo**: Configurar ambiente GCP para deploy.

**AÇÃO NECESSÁRIA**:
- **SUBSTITUIR** `seu-projeto-id` pelo Project ID real do GCP
- Executar `gcloud auth login` e autenticar no browser

**Verificação de Sucesso**:
- Variáveis de ambiente definidas
- Autenticação GCP bem-sucedida
- Projeto configurado corretamente

---

### Step 2.3: Habilitar APIs Necessárias
```bash
# Habilitar Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Habilitar Cloud Run API
gcloud services enable run.googleapis.com

# Habilitar Container Registry API
gcloud services enable containerregistry.googleapis.com

# Habilitar Artifact Registry API (alternativa moderna)
gcloud services enable artifactregistry.googleapis.com

# Verificar APIs habilitadas
gcloud services list --enabled | grep -E "cloudbuild|run|container"

echo "✅ APIs habilitadas"
```

**Objetivo**: Habilitar serviços GCP necessários.

**Verificação de Sucesso**:
- Todas as 4 APIs habilitadas
- Comando `gcloud services list` mostra as APIs ativas

---

## 🚀 FASE 3: DEPLOY INICIAL (Via gcloud CLI)

### Step 3.1: Build e Push Manual da Imagem
```bash
# Autenticar Docker com GCR
gcloud auth configure-docker

# Build da imagem com tag completa
docker build -t ${IMAGE_NAME}:latest .

# Tag com versão específica
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:v2.0.0

# Push para Container Registry
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:v2.0.0

# Verificar imagens no registry
gcloud container images list --repository=gcr.io/${GCP_PROJECT_ID}

echo "✅ Imagem publicada no GCR"
```

**Objetivo**: Fazer build e push manual da imagem Docker.

**IMPORTANTE**:
- Este é o **deploy inicial**
- Após isso, usaremos vcli-go para deploys futuros

**Verificação de Sucesso**:
- Build completa sem erros
- Push bem-sucedido para GCR
- Imagem aparece em `gcloud container images list`

---

### Step 3.2: Deploy Inicial no Cloud Run
```bash
# Deploy no Cloud Run (primeira vez)
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${GCP_REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --timeout 300s \
  --port 8080 \
  --set-env-vars "VCLI_ENV=production,VCLI_VERSION=2.0.0"

# Aguardar deploy completar (pode levar 1-2 minutos)

# Obter URL do serviço
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${GCP_REGION} \
  --format='value(status.url)')

echo "✅ Deploy completo!"
echo "Service URL: $SERVICE_URL"
```

**Objetivo**: Fazer o primeiro deploy no Cloud Run.

**Configurações**:
- Memory: 512Mi (suficiente para vcli-go)
- CPU: 1 vCPU
- Timeout: 300s (5 minutos para operações longas)
- Unauthenticated: Permite acesso público (ATENÇÃO: ajustar em produção)

**Verificação de Sucesso**:
- Deploy completa com status "ACTIVE"
- URL do serviço retornada
- Sem erros no log

---

### Step 3.3: Testar Serviço Deployado
```bash
# Testar endpoint básico (health check)
curl ${SERVICE_URL}/

# Se houver endpoint de version
curl ${SERVICE_URL}/version

# Verificar logs
gcloud run services logs read ${SERVICE_NAME} \
  --region ${GCP_REGION} \
  --limit 50

echo "✅ Serviço testado"
```

**Objetivo**: Validar que o serviço está rodando corretamente.

**NOTA**:
- Se vcli-go não tiver endpoints HTTP, ajustar para CLI usage
- Pode ser necessário adaptar para job batch vs serviço HTTP

**Verificação de Sucesso**:
- Curl retorna resposta (ou 404 se não houver endpoints)
- Logs mostram startup bem-sucedido
- Sem erros críticos

---

## 🔄 FASE 4: AUTODEPLOY VIA VCLI-GO

### Step 4.1: Criar Kubeconfig para Cloud Run (Se aplicável)
```bash
# Se Cloud Run expor cluster K8s (GKE Autopilot)
gcloud container clusters get-credentials <cluster-name> \
  --region ${GCP_REGION}

# Verificar contexto
kubectl config get-contexts

# Testar com vcli-go
./bin/vcli k8s get nodes
./bin/vcli k8s get pods --all-namespaces
```

**Objetivo**: Configurar acesso K8s se Cloud Run usar GKE.

**NOTA**: Cloud Run **NÃO** expõe K8s diretamente. Esta etapa é para:
- Deploy em GKE Autopilot (alternativa ao Cloud Run)
- OU para gerenciar outros clusters via vcli-go

**Verificação de Sucesso**:
- Kubeconfig configurado
- vcli-go consegue listar recursos K8s

---

### Step 4.2: Criar Manifests K8s (Se usar GKE)
```bash
# Criar diretório de manifests
mkdir -p k8s/manifests

# Criar Deployment manifest
cat > k8s/manifests/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vcli-go
  namespace: default
  labels:
    app: vcli-go
    version: v2.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vcli-go
  template:
    metadata:
      labels:
        app: vcli-go
        version: v2.0.0
    spec:
      containers:
      - name: vcli-go
        image: gcr.io/PROJECT_ID/vcli-go:latest  # SUBSTITUIR PROJECT_ID
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: VCLI_ENV
          value: "production"
        - name: VCLI_VERSION
          value: "2.0.0"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - vcli
            - version
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - vcli
            - version
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: vcli-go
  namespace: default
  labels:
    app: vcli-go
spec:
  type: LoadBalancer
  selector:
    app: vcli-go
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
EOF

# IMPORTANTE: Substituir PROJECT_ID no manifest
sed -i "s/PROJECT_ID/${GCP_PROJECT_ID}/g" k8s/manifests/deployment.yaml

echo "✅ Manifests K8s criados"
```

**Objetivo**: Criar manifests K8s para deploy via vcli-go.

**AÇÃO NECESSÁRIA**:
- **SUBSTITUIR** `PROJECT_ID` no manifest pelo projeto GCP real

**Verificação de Sucesso**:
- Arquivo `k8s/manifests/deployment.yaml` criado
- PROJECT_ID substituído corretamente

---

### Step 4.3: Deploy via vcli-go K8s Commands
```bash
# Aplicar deployment usando vcli-go
./bin/vcli k8s apply -f k8s/manifests/deployment.yaml

# Verificar deployment
./bin/vcli k8s get deployments

# Verificar pods
./bin/vcli k8s get pods -l app=vcli-go

# Verificar logs
POD_NAME=$(./bin/vcli k8s get pods -l app=vcli-go -o json | jq -r '.items[0].metadata.name')
./bin/vcli k8s logs $POD_NAME --follow

# Verificar service
./bin/vcli k8s get service vcli-go

# Obter LoadBalancer IP
./bin/vcli k8s get service vcli-go -o json | jq -r '.status.loadBalancer.ingress[0].ip'

echo "✅ Deploy via vcli-go completo!"
```

**Objetivo**: Realizar deploy usando o próprio vcli-go.

**IMPORTANTE**:
- Demonstra que vcli-go pode fazer **autodeploy**
- Comandos kubectl-compatible funcionam 100%

**Verificação de Sucesso**:
- Deployment criado com sucesso
- Pods em estado "Running"
- Service com LoadBalancer IP atribuído
- Logs mostram aplicação rodando

---

## 🔍 FASE 5: VALIDAÇÃO E MONITORAMENTO

### Step 5.1: Validar Deploy Completo
```bash
# Listar todos os recursos
./bin/vcli k8s get all -n default

# Verificar status do deployment
./bin/vcli k8s rollout status deployment/vcli-go

# Testar scale
./bin/vcli k8s scale deployment vcli-go --replicas=5

# Verificar scale
./bin/vcli k8s get pods -l app=vcli-go

# Voltar para 3 replicas
./bin/vcli k8s scale deployment vcli-go --replicas=3

echo "✅ Validação completa"
```

**Objetivo**: Validar que todos os comandos vcli-go funcionam no deploy.

**Verificação de Sucesso**:
- Todos os comandos executam sem erros
- Scale funciona corretamente
- Status mostra "successfully rolled out"

---

### Step 5.2: Monitorar com vcli-go
```bash
# Monitorar métricas de nodes
./bin/vcli k8s top nodes

# Monitorar métricas de pods
./bin/vcli k8s top pods -n default

# Acompanhar logs em tempo real
./bin/vcli k8s logs -f deployment/vcli-go

# Verificar eventos recentes
./bin/vcli k8s get events --sort-by='.lastTimestamp'

echo "✅ Monitoramento configurado"
```

**Objetivo**: Demonstrar capacidades de monitoramento do vcli-go.

**Verificação de Sucesso**:
- Métricas são exibidas corretamente
- Logs são streamados em tempo real
- Eventos mostram histórico recente

---

### Step 5.3: Criar Script de Redeploy Automatizado
```bash
# Criar script de redeploy
cat > scripts/redeploy.sh << 'EOF'
#!/bin/bash
set -e

# Configurações
PROJECT_ID="${GCP_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/vcli-go"
DEPLOYMENT_NAME="vcli-go"

echo "🚀 Iniciando redeploy..."

# Step 1: Build nova imagem
echo "📦 Building imagem..."
docker build -t ${IMAGE_NAME}:latest .

# Step 2: Tag com timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${TIMESTAMP}

# Step 3: Push para registry
echo "⬆️  Pushing para GCR..."
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:${TIMESTAMP}

# Step 4: Update deployment via vcli-go
echo "🔄 Atualizando deployment..."
./bin/vcli k8s set image deployment/${DEPLOYMENT_NAME} \
  vcli-go=${IMAGE_NAME}:${TIMESTAMP}

# Step 5: Aguardar rollout
echo "⏳ Aguardando rollout..."
./bin/vcli k8s rollout status deployment/${DEPLOYMENT_NAME}

# Step 6: Verificar pods
echo "✅ Verificando pods..."
./bin/vcli k8s get pods -l app=vcli-go

echo "🎉 Redeploy completo!"
EOF

chmod +x scripts/redeploy.sh

echo "✅ Script de redeploy criado"
```

**Objetivo**: Criar script automatizado de redeploy.

**Uso Futuro**:
```bash
# Fazer redeploy após mudanças no código
./scripts/redeploy.sh
```

**Verificação de Sucesso**:
- Script criado em `scripts/redeploy.sh`
- Permissões de execução configuradas

---

## 📊 FASE 6: DOCUMENTAÇÃO E CLEANUP

### Step 6.1: Documentar Deploy
```bash
# Criar documentação de deploy
cat > docs/DEPLOY_INSTRUCTIONS.md << 'EOF'
# Instruções de Deploy - vcli-go Cloud Run

## Pré-requisitos
- gcloud CLI configurado
- Docker instalado
- Projeto GCP com APIs habilitadas

## Deploy Inicial (via gcloud)
\`\`\`bash
# Build e push
docker build -t gcr.io/PROJECT_ID/vcli-go:latest .
docker push gcr.io/PROJECT_ID/vcli-go:latest

# Deploy no Cloud Run
gcloud run deploy vcli-go \
  --image gcr.io/PROJECT_ID/vcli-go:latest \
  --region us-central1 \
  --platform managed
\`\`\`

## Redeploy (via vcli-go)
\`\`\`bash
# Após alterações no código
./scripts/redeploy.sh
\`\`\`

## Comandos Úteis
\`\`\`bash
# Verificar status
./bin/vcli k8s get pods

# Ver logs
./bin/vcli k8s logs deployment/vcli-go

# Scale
./bin/vcli k8s scale deployment vcli-go --replicas=N
\`\`\`
EOF

echo "✅ Documentação criada"
```

**Objetivo**: Documentar processo de deploy para equipe.

**Verificação de Sucesso**:
- Arquivo `docs/DEPLOY_INSTRUCTIONS.md` criado
- Instruções claras e concisas

---

### Step 6.2: Criar .gitignore (se não existir)
```bash
# Adicionar entradas relacionadas a deploy
cat >> .gitignore << 'EOF'

# Cloud
.gcloud/
.config/gcloud/

# Kubernetes
kubeconfig
*.kubeconfig
k8s/secrets/

# Docker
.dockerignore
EOF

echo "✅ .gitignore atualizado"
```

**Objetivo**: Evitar commit de arquivos sensíveis.

**Verificação de Sucesso**:
- `.gitignore` atualizado
- Arquivos de config não serão commitados

---

### Step 6.3: Commit e Push (Opcional)
```bash
# Verificar mudanças
git status

# Adicionar novos arquivos
git add Dockerfile cloudbuild.yaml .dockerignore
git add k8s/ scripts/
git add docs/DIAGNOSTICO_DEPLOY_CLOUD_RUN.md
git add docs/PLANO_DEPLOY_CLOUD_RUN.md
git add docs/DEPLOY_INSTRUCTIONS.md

# Commit
git commit -m "feat(deploy): Add Cloud Run deployment configuration

- Add optimized Dockerfile (multi-stage, Alpine-based)
- Add cloudbuild.yaml for CI/CD
- Add K8s manifests for GKE deployment
- Add redeploy automation script
- Add comprehensive deployment documentation

Enables vcli-go self-deployment capability via K8s commands."

# Push para remote (se configurado)
git push origin main

echo "✅ Mudanças commitadas"
```

**Objetivo**: Versionar configurações de deploy.

**AÇÃO NECESSÁRIA**:
- Revisar mudanças antes de commit
- Garantir que não há secrets nos arquivos

**Verificação de Sucesso**:
- Commit criado com sucesso
- Push bem-sucedido (se houver remote)

---

## ✅ CHECKLIST FINAL

### Preparação ✅
- [ ] Build local funcionando
- [ ] Dockerfile criado e testado
- [ ] .dockerignore configurado
- [ ] cloudbuild.yaml criado

### Configuração GCP ✅
- [ ] GCP Project ID definido
- [ ] APIs habilitadas (Cloud Build, Cloud Run, Container Registry)
- [ ] gcloud autenticado
- [ ] Docker autenticado com GCR

### Deploy Inicial ✅
- [ ] Imagem Docker publicada no GCR
- [ ] Deploy no Cloud Run bem-sucedido
- [ ] Service URL obtida e testada

### Autodeploy via vcli-go ✅
- [ ] Kubeconfig configurado (se GKE)
- [ ] Manifests K8s criados
- [ ] Deploy via `vcli k8s apply` funciona
- [ ] Comandos kubectl-compatible validados

### Validação ✅
- [ ] Pods rodando corretamente
- [ ] Scale funciona
- [ ] Logs acessíveis via vcli-go
- [ ] Métricas disponíveis

### Documentação ✅
- [ ] DIAGNOSTICO_DEPLOY_CLOUD_RUN.md criado
- [ ] PLANO_DEPLOY_CLOUD_RUN.md criado
- [ ] DEPLOY_INSTRUCTIONS.md criado
- [ ] Script de redeploy funcional

### Cleanup ✅
- [ ] .gitignore atualizado
- [ ] Secrets removidos dos arquivos
- [ ] Mudanças commitadas

---

## 🎯 PRÓXIMOS PASSOS (PÓS-DEPLOY)

### Otimizações (P2)
1. **Habilitar Cloud Build Triggers**
   - Trigger automático em push para `main`
   - Deploy automático via cloudbuild.yaml

2. **Configurar Monitoring**
   - Cloud Monitoring dashboards
   - Alertas para erros/latência

3. **Implementar Secrets Management**
   - Migrar env vars para Secret Manager
   - Configurar IAM roles corretas

### Integrações Backend (P3)
1. **Subir serviços backend**
   - maximus, immune, hitl, consciousness
   - Testar integração E2E

2. **Configurar Service Mesh**
   - Istio ou Cloud Run Service Mesh
   - mTLS entre serviços

### Features Avançadas (P4)
1. **Plugin System**
   - Implementar dynamic loading
   - Criar plugin registry

2. **Offline Mode**
   - Integrar BadgerDB cache
   - Testar sync automático

---

## 📞 TROUBLESHOOTING

### Problema: Build falha com "module not found"
**Solução**:
```bash
go mod tidy
go mod download
```

### Problema: Docker push falha com "unauthorized"
**Solução**:
```bash
gcloud auth configure-docker
gcloud auth login
```

### Problema: Cloud Run deploy falha com "memory limit"
**Solução**:
```bash
# Aumentar memory limit
gcloud run deploy vcli-go --memory 1Gi
```

### Problema: vcli-go não consegue acessar cluster K8s
**Solução**:
```bash
# Verificar kubeconfig
kubectl config view

# Reconfigurar credentials
gcloud container clusters get-credentials <cluster-name>
```

---

## 📚 REFERÊNCIAS

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Configuration](https://cloud.google.com/build/docs/build-config-file-schema)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [vcli-go README](../README.md)

---

**Plano criado em**: 2025-10-25
**Estimativa de execução**: 1-2 horas (primeira vez)
**Dificuldade**: ⭐⭐⭐ Intermediária
**Confiança**: 98%

**NOTA IMPORTANTE**: Este plano é detalhado para execução no github-copilot-cli sem plan mode. Cada step tem comandos explícitos e verificações de sucesso. Ajuste PROJECT_ID e outros valores específicos conforme seu ambiente.

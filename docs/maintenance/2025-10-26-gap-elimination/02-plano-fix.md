# 🔧 PLANO DE FIX - GAP-2 e GAP-3

**Data**: 2025-10-26  
**Objetivo**: Resolver GAP-2 e GAP-3 com fixes cirúrgicos e locais  
**Restrições**: 
- Zero refatoração sistêmica
- Zero impacto em código funcional
- Fixes apenas nos componentes quebrados
- Validação completa antes de deploy

---

## 📋 ESTRATÉGIA GERAL

### Princípios
1. **Diagnóstico completo ANTES de tocar código**
2. **Pesquisa de soluções alternativas** (não apenas a óbvia)
3. **Fix mais simples que funcione** (KISS principle)
4. **Validação local antes de deploy** (build + test container)
5. **Rollback rápido se falhar**

### Ordem de Execução
1. **FASE 1**: Diagnóstico completo GAP-2 (15min)
2. **FASE 2**: Pesquisa de soluções GAP-2 (10min)
3. **FASE 3**: Implementação GAP-2 (20min)
4. **FASE 4**: Diagnóstico completo GAP-3 (10min)
5. **FASE 5**: Pesquisa de soluções GAP-3 (10min)
6. **FASE 6**: Implementação GAP-3 (20min)
7. **FASE 7**: Validação final (10min)

**Total estimado**: 95min (1h35min)

---

## 🚨 GAP-2: command-bus-service

---

### FASE 1: DIAGNÓSTICO COMPLETO (15min)

#### 1.1 Mapear TODOS os arquivos Python do service
```bash
find /home/juan/vertice-dev/backend/services/command_bus_service \
  -name "*.py" \
  -not -path "*/.venv/*" \
  -not -path "*/__pycache__/*" \
  | sort
```

**Objetivo**: Lista completa de arquivos que podem ter imports

---

#### 1.2 Identificar TODOS os imports incorretos
```bash
grep -r "from backend.services.command_bus_service" \
  /home/juan/vertice-dev/backend/services/command_bus_service \
  --include="*.py" \
  --exclude-dir=".venv" \
  -n
```

**Objetivo**: Localização EXATA (arquivo + linha) de cada import incorreto

---

#### 1.3 Mapear estrutura de módulos internos
```bash
# Verificar que módulos existem
ls -la /home/juan/vertice-dev/backend/services/command_bus_service/*.py
ls -la /home/juan/vertice-dev/backend/services/command_bus_service/*/__init__.py 2>/dev/null
```

**Objetivo**: Confirmar que `models.py`, `schemas.py` etc existem no mesmo diretório

---

#### 1.4 Verificar dependencies no requirements.txt
```bash
cat /home/juan/vertice-dev/backend/services/command_bus_service/requirements.txt
```

**Objetivo**: Confirmar que não há dependência circular ou package faltando

---

#### 1.5 Analisar estrutura de imports no main.py
```bash
head -30 /home/juan/vertice-dev/backend/services/command_bus_service/main.py
```

**Objetivo**: Ver como imports devem ser estruturados (padrão do service)

---

### FASE 2: PESQUISA DE SOLUÇÕES (10min)

#### Opção A: Fix via sed/grep (mais rápido)
**Vantagem**: Automático, sem erro humano  
**Desvantagem**: Pode não capturar edge cases  
**Tempo**: 5min

```bash
# Substituição automática em todos os arquivos
find . -name "*.py" -not -path "*/.venv/*" -exec \
  sed -i 's|from backend\.services\.command_bus_service\.|from |g' {} \;
```

---

#### Opção B: Fix manual arquivo por arquivo (mais seguro)
**Vantagem**: Controle total, valida cada import  
**Desvantagem**: Mais lento  
**Tempo**: 15min

```python
# Para cada arquivo:
# 1. Abrir
# 2. Substituir imports
# 3. Validar sintaxe
# 4. Commit
```

---

#### Opção C: Adicionar ao sys.path (workaround, não fix)
**Vantagem**: Não mexe em imports  
**Desvantagem**: Técnica ruim, mascaramento de problema  
**Tempo**: 2min  
**Recomendação**: ❌ NÃO USAR (viola Padrão Pagani)

---

#### Opção D: Criar package wrapper (complexo)
**Vantagem**: Mantém imports absolutos  
**Desvantagem**: Adiciona complexidade  
**Tempo**: 30min  
**Recomendação**: ❌ NÃO USAR (viola princípio KISS)

---

#### DECISÃO: Opção A com validação manual
**Estratégia híbrida**:
1. Usar `sed` para substituição em massa
2. Validar cada arquivo manualmente (rápido grep)
3. Build container local para testar
4. Deploy apenas se build OK

**Tempo**: 10min (5min auto + 5min validação)

---

### FASE 3: IMPLEMENTAÇÃO GAP-2 (20min)

#### 3.1 Backup do estado atual
```bash
cp -r /home/juan/vertice-dev/backend/services/command_bus_service \
      /tmp/command_bus_service_backup_$(date +%s)
```

---

#### 3.2 Listar arquivos com imports incorretos
```bash
cd /home/juan/vertice-dev/backend/services/command_bus_service
grep -l "from backend.services.command_bus_service" *.py > /tmp/files_to_fix.txt
cat /tmp/files_to_fix.txt
```

---

#### 3.3 Aplicar fix automático
```bash
while read file; do
  echo "Fixing: $file"
  sed -i 's|from backend\.services\.command_bus_service\.models|from models|g' "$file"
  sed -i 's|from backend\.services\.command_bus_service\.schemas|from schemas|g' "$file"
  sed -i 's|from backend\.services\.command_bus_service\.config|from config|g' "$file"
  sed -i 's|from backend\.services\.command_bus_service\.|from |g' "$file"
done < /tmp/files_to_fix.txt
```

---

#### 3.4 Validar sintaxe Python
```bash
for file in $(cat /tmp/files_to_fix.txt); do
  python3 -m py_compile "$file" && echo "✓ $file" || echo "✗ $file ERRO"
done
```

---

#### 3.5 Verificar que imports foram corrigidos
```bash
grep -r "from backend.services.command_bus_service" . \
  --include="*.py" \
  --exclude-dir=".venv" \
  | wc -l
# Deve retornar: 0
```

---

#### 3.6 Build container local
```bash
cd /home/juan/vertice-dev/backend/services/command_bus_service
docker build -t command_bus_service:test-local . 2>&1 | tee /tmp/build.log
# Verificar se build passou
tail -20 /tmp/build.log | grep -i "error\|failed"
```

---

#### 3.7 Test container local (dry-run)
```bash
docker run --rm -d --name test-command-bus \
  -e REDIS_URL=redis://localhost:6379 \
  -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
  command_bus_service:test-local

# Aguardar 10s
sleep 10

# Verificar logs
docker logs test-command-bus 2>&1 | tail -30

# Verificar se processo iniciou
docker exec test-command-bus ps aux | grep uvicorn

# Cleanup
docker stop test-command-bus
```

---

#### 3.8 Se testes OK: Build imagem para GCR
```bash
docker build -t us-east1-docker.pkg.dev/projeto-vertice/vertice-images/command_bus_service:gap2-fix-final .
```

---

#### 3.9 Push para GCR
```bash
docker push us-east1-docker.pkg.dev/projeto-vertice/vertice-images/command_bus_service:gap2-fix-final
```

---

#### 3.10 Deploy no GKE
```bash
kubectl set image deployment/command-bus-service -n vertice \
  command-bus-service=us-east1-docker.pkg.dev/projeto-vertice/vertice-images/command_bus_service:gap2-fix-final

# Monitorar
kubectl rollout status deployment/command-bus-service -n vertice --timeout=120s
```

---

#### 3.11 Validar pod
```bash
# Aguardar readiness
sleep 45

# Verificar status
kubectl get pods -n vertice -l app=command-bus-service

# Verificar logs
kubectl logs -n vertice -l app=command-bus-service --tail=30

# Se Running: testar health
kubectl exec -n vertice <pod-name> -- curl -s http://localhost:8092/health
```

---

#### 3.12 Rollback se falhar
```bash
# Se pod não ficar Running após 2min:
kubectl rollout undo deployment/command-bus-service -n vertice

# Restaurar código
rm -rf /home/juan/vertice-dev/backend/services/command_bus_service
mv /tmp/command_bus_service_backup_* /home/juan/vertice-dev/backend/services/command_bus_service
```

---

## 🚨 GAP-3: agent-communication

---

### FASE 4: DIAGNÓSTICO COMPLETO (10min)

#### 4.1 Verificar Dockerfile atual
```bash
cat /home/juan/vertice-dev/backend/services/agent_communication/Dockerfile
```

**Foco**: Linha 1 (FROM), linha 5 (COPY), CMD final

---

#### 4.2 Verificar se base image existe
```bash
# Tentar pull
docker pull vertice/python311-uv:latest 2>&1 | grep -i "not found\|error"

# Se não existe: confirmar que é o problema
echo "Base image não existe no Docker Hub nem no GCR"
```

---

#### 4.3 Verificar requirements.txt
```bash
cat /home/juan/vertice-dev/backend/services/agent_communication/requirements.txt
```

**Objetivo**: Confirmar que dependências são simples (instaláveis via pip)

---

#### 4.4 Verificar pyproject.toml (se existir)
```bash
cat /home/juan/vertice-dev/backend/services/agent_communication/pyproject.toml 2>/dev/null
```

**Objetivo**: Ver se usa `uv` para algo específico

---

#### 4.5 Verificar estrutura de arquivos
```bash
ls -la /home/juan/vertice-dev/backend/services/agent_communication/*.py
```

**Objetivo**: Confirmar que é service simples (sem dependências complexas)

---

#### 4.6 Verificar deployment atual
```bash
kubectl get deployment -n vertice agent-communication -o yaml | grep -A 10 "env:"
```

**Objetivo**: Ver que env vars são necessárias

---

### FASE 5: PESQUISA DE SOLUÇÕES (10min)

#### Opção A: Criar base image `vertice/python311-uv`
**Vantagem**: Mantém Dockerfile original intacto  
**Desvantagem**: Mais steps, mais pontos de falha  
**Tempo**: 25min

```dockerfile
# 1. Criar Dockerfile para base
FROM python:3.11-slim
RUN pip install uv
```

```bash
# 2. Build
docker build -t us-east1-docker.pkg.dev/projeto-vertice/vertice-images/python311-uv:latest .

# 3. Push
docker push ...

# 4. Atualizar agent-communication Dockerfile
sed -i 's|FROM vertice/python311-uv:latest|FROM us-east1-docker.pkg.dev/.../python311-uv:latest|' Dockerfile
```

---

#### Opção B: Refatorar Dockerfile para `python:3.11-slim` (RECOMENDADO)
**Vantagem**: Simples, usa imagem oficial, menos dependências  
**Desvantagem**: Muda Dockerfile  
**Tempo**: 15min

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER 1000
EXPOSE 8603
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8603"]
```

---

#### Opção C: Multi-stage build com pip (compromise)
**Vantagem**: Mantém estrutura original, usa pip em vez de uv  
**Desvantagem**: Mais complexo que Opção B  
**Tempo**: 20min

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target /build/deps

FROM python:3.11-slim
COPY --from=builder /build/deps /usr/local/lib/python3.11/site-packages
WORKDIR /app
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8603"]
```

---

#### DECISÃO: Opção B (Dockerfile simples)
**Razão**:
- Service é simples (FastAPI + health endpoint)
- `requirements.txt` tem 1 linha (fastapi, uvicorn)
- Não precisa de `uv` (overkill para projeto pequeno)
- Dockerfile oficial Python é battle-tested

**Tempo**: 15min

---

### FASE 6: IMPLEMENTAÇÃO GAP-3 (20min)

#### 6.1 Backup Dockerfile atual
```bash
cp /home/juan/vertice-dev/backend/services/agent_communication/Dockerfile \
   /home/juan/vertice-dev/backend/services/agent_communication/Dockerfile.bak
```

---

#### 6.2 Criar novo Dockerfile otimizado
```bash
cat > /home/juan/vertice-dev/backend/services/agent_communication/Dockerfile << 'DOCKEREOF'
FROM python:3.11-slim

LABEL maintainer="Juan & Claude" version="2.1.0"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser --uid 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8603/health || exit 1

# Expose port
EXPOSE 8603

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8603"]
DOCKEREOF
```

---

#### 6.3 Validar sintaxe Dockerfile
```bash
docker build --dry-run -t test /home/juan/vertice-dev/backend/services/agent_communication 2>&1 | grep -i error
```

---

#### 6.4 Build imagem local (test)
```bash
cd /home/juan/vertice-dev/backend/services/agent_communication
docker build -t agent_communication:test-local . 2>&1 | tee /tmp/build-agent.log

# Verificar se passou
tail -20 /tmp/build-agent.log | grep -i "error\|failed"
```

---

#### 6.5 Test container local
```bash
# Start container
docker run --rm -d --name test-agent-comm \
  -p 8603:8603 \
  agent_communication:test-local

# Aguardar 10s
sleep 10

# Testar health endpoint
curl -s http://localhost:8603/health | jq '.'

# Verificar logs
docker logs test-agent-comm 2>&1 | tail -20

# Verificar processo
docker exec test-agent-comm ps aux | grep uvicorn

# Cleanup
docker stop test-agent-comm
```

---

#### 6.6 Se testes OK: Build para GCR
```bash
docker build -t us-east1-docker.pkg.dev/projeto-vertice/vertice-images/agent_communication:gap3-fix-final .
```

---

#### 6.7 Push para GCR
```bash
docker push us-east1-docker.pkg.dev/projeto-vertice/vertice-images/agent_communication:gap3-fix-final
```

---

#### 6.8 Deploy no GKE
```bash
kubectl set image deployment/agent-communication -n vertice \
  agent-communication=us-east1-docker.pkg.dev/projeto-vertice/vertice-images/agent_communication:gap3-fix-final

# Monitorar
kubectl rollout status deployment/agent-communication -n vertice --timeout=120s
```

---

#### 6.9 Validar pod
```bash
# Aguardar readiness
sleep 45

# Verificar status
kubectl get pods -n vertice -l app=agent-communication

# Verificar logs
kubectl logs -n vertice -l app=agent-communication --tail=30

# Se Running: testar health
POD_NAME=$(kubectl get pod -n vertice -l app=agent-communication -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n vertice $POD_NAME -- curl -s http://localhost:8603/health
```

---

#### 6.10 Rollback se falhar
```bash
# Se pod não ficar Running:
kubectl rollout undo deployment/agent-communication -n vertice

# Restaurar Dockerfile
mv /home/juan/vertice-dev/backend/services/agent_communication/Dockerfile.bak \
   /home/juan/vertice-dev/backend/services/agent_communication/Dockerfile
```

---

## FASE 7: VALIDAÇÃO FINAL (10min)

### 7.1 Verificar status de todos os pods
```bash
kubectl get pods -n vertice -l "app in (command-bus-service,agent-communication)"
```

**Esperado**: Ambos `1/1 Running`

---

### 7.2 Contagem de pods Running
```bash
kubectl get pods -n vertice --field-selector=status.phase=Running | wc -l
```

**Esperado**: ≥88 (atual: 86 + 2 fixes = 88)

---

### 7.3 Contagem de CrashLoop
```bash
kubectl get pods -n vertice --field-selector=status.phase!=Running | wc -l
```

**Esperado**: ≤11 (atual: 13 - 2 fixes = 11)

---

### 7.4 Testar endpoints health
```bash
# command-bus-service
kubectl exec -n vertice $(kubectl get pod -n vertice -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') \
  -- curl -s http://command-bus-service:8092/health

# agent-communication
kubectl exec -n vertice $(kubectl get pod -n vertice -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') \
  -- curl -s http://agent-communication:8603/health
```

**Esperado**: Ambos retornam `{"status": "healthy"}`

---

### 7.5 Calcular novo Health Score
```bash
RUNNING=$(kubectl get pods -n vertice --field-selector=status.phase=Running --no-headers | wc -l)
TOTAL=$(kubectl get pods -n vertice --no-headers | wc -l)
echo "Pods Running: $RUNNING/$TOTAL"
echo "Health Score: $(echo "scale=1; $RUNNING * 100 / $TOTAL" | bc)%"
```

**Esperado**: ≥89%

---

### 7.6 Documentar resultado
```bash
cat >> /tmp/maintenance_session.log << EOF

═══ GAP-2: COMPLETO ═══
command-bus-service: RUNNING (1/1 READY)
Fix: Substituição automática de imports absolutos para relativos

═══ GAP-3: COMPLETO ═══
agent-communication: RUNNING (1/1 READY)
Fix: Dockerfile refatorado para python:3.11-slim (sem dependência de uv)

═══ VALIDAÇÃO FINAL ═══
Pods Running: $RUNNING/$TOTAL ($SCORE%)
CrashLoop Pods: $(kubectl get pods -n vertice --field-selector=status.phase!=Running --no-headers | wc -l)
Health Score: $(echo "scale=1; $RUNNING * 100 / $TOTAL" | bc)%
EOF

cat /tmp/maintenance_session.log
```

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Antes | Target | Status |
|---------|-------|--------|--------|
| Pods Running | 86/99 (86.9%) | 88/99 (88.9%) | ⏳ |
| Dashboards Funcionais | 6/7 (86%) | 6/7 (86%) | ⏳ |
| CrashLoop Pods | 13 | 11 | ⏳ |
| Health Score | 88% | 89% | ⏳ |

---

## 🚫 PROIBIÇÕES

### ❌ NÃO FAZER
- Não refatorar lógica de negócio
- Não adicionar features
- Não mexer em arquivos de outros services
- Não alterar env vars no deployment (apenas imagem)
- Não fazer "melhorias" além do fix
- Não tocar em pods Running

### ✅ PERMITIDO
- Substituir imports incorretos por corretos
- Refatorar Dockerfile (apenas do service quebrado)
- Build + push de novas imagens
- Update de deployment com nova imagem
- Rollback se falhar

---

## 🆘 PLANO DE CONTINGÊNCIA

### Se GAP-2 falhar após 30min
**AÇÃO**: 
1. Rollback deployment
2. Restaurar código do backup
3. Documentar erro específico
4. Prosseguir para GAP-3

### Se GAP-3 falhar após 30min
**AÇÃO**:
1. Rollback deployment
2. Restaurar Dockerfile.bak
3. Documentar erro específico
4. Reportar resultado parcial

### Se ambos falharem
**AÇÃO**:
1. Rollback completo
2. Relatório de falha com logs
3. Manter status quo (86 pods Running)

---

## 📋 CHECKLIST PRÉ-EXECUÇÃO

- [ ] Backup de código criado
- [ ] Kubectl acesso validado
- [ ] Docker login no GCR OK
- [ ] Espaço em disco suficiente (>5GB)
- [ ] Arquiteto-Chefe disponível para aprovação final

---

## ✅ CRITÉRIO DE CONCLUSÃO

**Manutenção é COMPLETA quando**:
1. ✅ GAP-2: Pod `command-bus-service` em `Running` OU rollback com documentação
2. ✅ GAP-3: Pod `agent-communication` em `Running` OU rollback com documentação
3. ✅ Health Score ≥ 88% (não pode piorar)
4. ✅ Zero quebra de pods funcionais
5. ✅ Relatório final gerado

---

**Aprovação necessária para iniciar FASE 1**

---

**Versão**: 1.0  
**Status**: AGUARDANDO APROVAÇÃO  
**Tempo estimado**: 95min (1h35min)

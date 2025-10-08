# 🐳 Docker Migration Guide - uv Edition

**Versão**: 1.0
**Data**: 2025-10-08
**Objetivo**: Migrar Dockerfiles para usar uv (60x mais rápido)

---

## 🎯 Estratégia

### Base Image Centralizada
Criamos uma base image otimizada:
- **Nome**: `ghcr.io/vertice/python311-uv:latest`
- **Localização**: `/docker/base/Dockerfile.python311-uv`
- **Inclui**: Python 3.11 + uv + ruff
- **Performance**: Builds 60x mais rápidos

###Services Usam Multi-Stage Build
1. **Builder stage**: Instala dependências com uv
2. **Runtime stage**: Copia venv, roda o service

---

## 📋 Migração Passo a Passo

### Opção 1: Usar Template (Recomendado)

**1. Copiar template:**
```bash
cd backend/services/SEU_SERVICE
cp ../../../docker/base/Dockerfile.service-template ./Dockerfile
```

**2. Customizar variáveis:**
```dockerfile
# Linha ~25
ARG SERVICE_NAME=seu-service     # ALTERAR
ARG SERVICE_PORT=8200            # ALTERAR
ARG SERVICE_VERSION=1.0.0        # ALTERAR
```

**3. Customizar CMD (se necessário):**
```dockerfile
# Linha ~80
CMD ["python", "-m", "uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8200"]
```

**4. Testar build:**
```bash
docker build -t seu-service:test .
docker run --rm -p 8200:8200 seu-service:test
```

### Opção 2: Migração Manual

#### Antes (pip)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "api.py"]
```

#### Depois (uv + multi-stage)
```dockerfile
# BUILDER STAGE
FROM ghcr.io/vertice/python311-uv:latest AS builder

WORKDIR /build
COPY pyproject.toml requirements.txt ./

RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip sync requirements.txt

# RUNTIME STAGE
FROM python:3.11-slim

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0"]
```

---

## ⚡ Performance Optimization

### 1. Layer Caching
Copiar arquivos de dependências ANTES do código:
```dockerfile
# ✅ BOM (cache friendly)
COPY pyproject.toml requirements.txt ./
RUN uv pip sync requirements.txt
COPY . .

# ❌ RUIM (rebuilda tudo sempre)
COPY . .
RUN uv pip sync requirements.txt
```

### 2. GitHub Actions Cache
No CI/CD:
```yaml
- name: Build Docker
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max  # Importante!
```

### 3. .dockerignore
Criar `.dockerignore` para excluir arquivos desnecessários:
```
__pycache__
*.pyc
*.pyo
.git
.github
.pytest_cache
.coverage
.mypy_cache
.ruff_cache
*.egg-info
dist
build
node_modules
.env
.env.local
*.old
```

---

## 🔒 Security Best Practices

### 1. Usuário Não-Root
```dockerfile
# Criar usuário
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar com ownership correto
COPY --chown=appuser:appuser . /app/

# Mudar para usuário não-root
USER appuser
```

### 2. Multi-Stage Build
Separa ferramentas de build (gcc, make) do runtime:
```dockerfile
# Builder tem gcc, g++, etc (não vai para produção)
FROM python:3.11-slim AS builder
RUN apt-get install gcc g++ ...

# Runtime tem apenas o mínimo
FROM python:3.11-slim
# Sem gcc, g++, etc
```

### 3. Health Check
Sempre incluir health check:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT}/health || exit 1
```

---

## 📊 Comparação de Tamanhos

### Antes (single-stage com pip)
```
REPOSITORY          TAG       SIZE
my-service          latest    1.2GB
```

### Depois (multi-stage com uv)
```
REPOSITORY          TAG       SIZE
my-service          latest    250MB
```

**Redução**: ~80% menor!

---

## 🧪 Validação

### 1. Build Local
```bash
# Build
docker build -t my-service:test .

# Verificar tamanho
docker images | grep my-service

# Rodar
docker run --rm -p 8000:8000 my-service:test

# Testar health
curl http://localhost:8000/health
```

### 2. Inspecionar Imagem
```bash
# Ver layers
docker history my-service:test

# Ver arquivos
docker run --rm my-service:test ls -la /app

# Verificar usuário
docker run --rm my-service:test whoami
# Output esperado: appuser (não root!)
```

### 3. Security Scan
```bash
# Trivy scan
trivy image my-service:test

# Ou via Docker Scout
docker scout cves my-service:test
```

---

## 🔧 Casos Especiais

### Service com Dependências de Sistema
```dockerfile
FROM ghcr.io/vertice/python311-uv:latest AS builder

# Instalar libs de sistema no builder
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ... resto do build ...

# Runtime precisa das libs de runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    libpq5 \      # Runtime do libpq-dev
    libssl3 \     # Runtime do libssl-dev
    && rm -rf /var/lib/apt/lists/*
```

### Service com Assets Estáticos
```dockerfile
# Copiar assets antes do código
COPY static/ /app/static/
COPY templates/ /app/templates/
COPY . /app/
```

### Service com Compile Step (Cython, etc)
```dockerfile
FROM ghcr.io/vertice/python311-uv:latest AS builder

# Instalar dependências de compilação
RUN apt-get update && apt-get install -y gcc g++ make

# Compilar
RUN uv pip sync requirements.txt
RUN python setup.py build_ext --inplace

# Runtime
FROM python:3.11-slim
COPY --from=builder /build /app
```

---

## 📋 Checklist de Migração

Para cada Dockerfile:

- [ ] Usa base image `ghcr.io/vertice/python311-uv`
- [ ] Multi-stage build (builder + runtime)
- [ ] Dependências copiadas ANTES do código (cache)
- [ ] Usuário não-root configurado
- [ ] Health check incluído
- [ ] .dockerignore criado
- [ ] Build testado localmente
- [ ] Security scan passou (trivy)
- [ ] Tamanho otimizado (<500MB para services normais)
- [ ] CI/CD atualizado para usar novo Dockerfile

---

## 🐛 Troubleshooting

### Error: "base image not found"
**Problema**: Base image ainda não foi built/pushed

**Solução temporária**: Usar `python:3.11-slim` e instalar uv:
```dockerfile
FROM python:3.11-slim AS builder
RUN pip install uv
```

### Build muito lento na primeira vez
**Normal**: Primeira build sempre é mais lenta
**Solução**: Usar cache do GitHub Actions (já configurado nos templates)

### Error: "permission denied" no health check
**Problema**: Usuário não-root não tem permissão

**Solução**: Dar permissão ao arquivo ou usar curl com sudo:
```dockerfile
# Opção 1: Dar permissão antes de mudar user
RUN chmod +x /app/healthcheck.sh
USER appuser

# Opção 2: Usar curl (já instalado na base image)
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
```

### Imagem muito grande (>1GB)
**Problema**: Provavelmente single-stage ou muitos arquivos desnecessários

**Solução**:
1. Usar multi-stage build
2. Criar .dockerignore
3. Limpar apt cache: `rm -rf /var/lib/apt/lists/*`

---

## 📊 Progress Tracker

| Service | TIER | Dockerfile Status | Image Size | Reduction |
|---------|------|-------------------|------------|-----------|
| maximus_core_service | 1 | ⏳ Pending | - | - |
| active_immune_core | 1 | ⏳ Pending | - | - |
| seriema_graph | 1 | ⏳ Pending | - | - |
| ... | 2-4 | ⏳ Pending | - | - |

**Total**: 0/71 migrados

---

## 🎯 Próximos Passos

1. **Build e push base image**
   ```bash
   cd docker/base
   docker build -t ghcr.io/vertice/python311-uv:latest \
     -f Dockerfile.python311-uv .
   docker push ghcr.io/vertice/python311-uv:latest
   ```

2. **Migrar 3 services críticos** (TIER 1)
3. **Validar em staging**
4. **Scale para TIER 2-4**

---

## 📚 Referências

- [Dockerfile Template](/docker/base/Dockerfile.service-template)
- [Base Image Dockerfile](/docker/base/Dockerfile.python311-uv)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)

---

**Criado em**: 2025-10-08
**Doutrina**: Vértice v2.0 - Quality First
**Performance**: 60x faster builds, 80% smaller images 🚀

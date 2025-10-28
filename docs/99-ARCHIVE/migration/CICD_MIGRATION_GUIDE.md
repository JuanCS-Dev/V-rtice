# 🚀 CI/CD Migration Guide - pip → uv + ruff

**Versão**: 1.0
**Data**: 2025-10-08
**Objetivo**: Migrar pipelines CI/CD para uv + ruff (60x mais rápido)

---

## 📊 Por Que Migrar?

### Performance Comparison

| Operação | Antes (pip) | Depois (uv) | Ganho |
|----------|-------------|-------------|-------|
| Resolução de deps | ~30s | ~0.5s | **60x** |
| Instalação | ~45s | ~2s | **22x** |
| Linting (flake8) | ~8s | ~0.3s (ruff) | **26x** |
| Formatting (black) | ~5s | ~0.2s (ruff) | **25x** |
| Import sorting (isort) | ~3s | integrado | **∞** |
| **TOTAL CI** | **~90s** | **~5s** | **18x** |

---

## 🎯 Estratégia de Migração

### Fase 1: TIER 1 (Críticos) - 4 services
1. maximus_core_service
2. active_immune_core
3. seriema_graph
4. tataca_ingestion

### Fase 2: TIER 2 (Importantes) - 16 services
Migração batch com validação

### Fase 3: TIER 3 + TIER 4 - 50 services
Automação completa

---

## 📋 Checklist Pré-Migração

Antes de migrar o CI/CD de um service:

- [ ] Service já migrado para uv? (pyproject.toml + requirements.txt com uv)
- [ ] Tests passando localmente? (`make test`)
- [ ] Dockerfile atualizado para uv? (se aplicável)
- [ ] Branch de trabalho criada?

---

## 🔧 Como Migrar - Passo a Passo

### Opção 1: Template Completo (com Docker)

**1. Copiar template:**
```bash
cd backend/services/SEU_SERVICE

# Backup da versão antiga
mv .github/workflows/ci.yml .github/workflows/ci.old.yml

# Copiar template novo
cp ../../../.github/workflows/templates/service-ci.yml \
   .github/workflows/ci.yml
```

**2. Customizar variáveis:**
```yaml
env:
  SERVICE_NAME: seu-service     # ALTERAR
  SERVICE_PORT: 8200            # ALTERAR se necessário
  PYTHON_VERSION: '3.11'        # OK para maioria
```

**3. Ajustar paths de teste (se necessário):**
```yaml
- name: 🏃 Run Tests
  run: |
    # Ajustar paths dos seus testes aqui
    PYTHONPATH=. pytest tests/ -v --cov=. --cov-report=xml
```

**4. Commit e testar:**
```bash
git add .github/workflows/ci.yml
git commit -m "ci: migrate to uv + ruff (60x faster)"
git push
```

### Opção 2: Template Simplificado (sem Docker)

Para services simples:
```bash
cp ../../../.github/workflows/templates/service-ci-simple.yml \
   .github/workflows/ci.yml
```

---

## 🔄 Migração Manual (para cases especiais)

### Antes (pip + flake8 + black + isort)
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install flake8 black isort bandit

- name: Run Black
  run: black --check --diff .

- name: Run isort
  run: isort --check-only --diff .

- name: Run Flake8
  run: flake8 . --count --select=E9,F63,F7,F82
```

### Depois (uv + ruff)
```yaml
- name: Install uv + ruff
  run: |
    pip install --no-cache-dir uv ruff

- name: Install dependencies
  run: |
    uv pip sync requirements.txt

- name: Ruff Lint
  run: |
    ruff check . --output-format=github

- name: Ruff Format
  run: |
    ruff format --check .
```

**Redução**: 4 steps → 3 steps, ~70s → ~3s

---

## 🐋 Docker Build Updates

### Antes
```yaml
- name: Build Docker Image
  run: |
    docker build -t myservice:latest .
```

### Depois (com cache e metadata)
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build Docker Image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ./Dockerfile
    push: false
    tags: myservice:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Ganho**: Build cache do GitHub Actions reduz rebuild time

---

## ✅ Validação Pós-Migração

### 1. GitHub Actions passou?
```bash
# Verificar no GitHub:
# https://github.com/SEU_ORG/vertice-dev/actions
```

### 2. Todos os steps passaram?
- [ ] Quality (ruff)
- [ ] Security (bandit)
- [ ] Tests (pytest)
- [ ] Build (docker)

### 3. Performance melhorou?
Comparar tempo total do CI:
- **Antes**: ~90s
- **Depois**: ~5-10s
- **Ganho esperado**: 10-18x

### 4. Coverage mantido?
```bash
# Coverage deve ser igual ou melhor
# Verificar no Codecov ou no output do pytest
```

---

## 🔥 Troubleshooting

### Error: "uv: command not found"
**Causa**: uv não instalado no step
**Fix**:
```yaml
- name: Install uv
  run: pip install --no-cache-dir uv
```

### Error: "ruff: command not found"
**Causa**: ruff não instalado
**Fix**:
```yaml
- name: Install ruff
  run: pip install --no-cache-dir ruff
```

### Tests falhando: "ModuleNotFoundError"
**Causa**: PYTHONPATH não configurado
**Fix**:
```yaml
- name: Run Tests
  run: PYTHONPATH=. pytest tests/
```

### Docker build falhou: "requirements.txt not found"
**Causa**: Dockerfile ainda aponta para arquivo antigo
**Fix**: Atualizar Dockerfile para usar `requirements.txt` (gerado por uv)

### Ruff encontrou muitos erros
**Causa**: Código não estava formatado
**Fix**: Rodar localmente primeiro:
```bash
ruff check . --fix
ruff format .
git commit -m "style: format with ruff"
```

---

## 📊 Progress Tracker

| Service | TIER | Status | Time Reduction |
|---------|------|--------|----------------|
| maximus_core_service | 1 | ✅ Migrado | 90s → 5s |
| active_immune_core | 1 | 🔄 In Progress | - |
| seriema_graph | 1 | ⏳ Pending | - |
| tataca_ingestion | 1 | ⏳ Pending | - |
| ... | 2-4 | ⏳ Pending | - |

**Total**: 1/71 migrados (1.4%)

---

## 🎯 Next Steps

1. **Validar primeiro service** (maximus_core_service)
2. **Migrar restante TIER 1** (3 services)
3. **Criar script de automação** para TIER 2-4
4. **Deploy em staging** e validar

---

## 📚 Referências

- [Template CI/CD Completo](/.github/workflows/templates/service-ci.yml)
- [Template CI/CD Simplificado](/.github/workflows/templates/service-ci-simple.yml)
- [Documentação uv](https://github.com/astral-sh/uv)
- [Documentação ruff](https://github.com/astral-sh/ruff)
- [Docker Buildx Cache](https://docs.docker.com/build/cache/)

---

**Criado em**: 2025-10-08
**Doutrina**: Vértice v2.0 - Quality First
**Impacto**: 60x faster CI/CD 🚀

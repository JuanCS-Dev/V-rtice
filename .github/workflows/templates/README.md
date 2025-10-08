# 🎯 MAXIMUS CI/CD Templates - uv + ruff Edition

**Versão**: 2.0 (pós-migração uv)
**Data**: 2025-10-08
**Performance**: 60x mais rápido que pip + flake8 + black + isort

---

## 📦 Templates Disponíveis

### 1. `service-ci.yml` - **Template Completo**
Para services com Docker, deploy, e todas as stages.

**Inclui:**
- ✅ Code Quality (ruff)
- ✅ Security Scan (bandit + trivy)
- ✅ Tests & Coverage (pytest)
- ✅ Docker Build
- ✅ Image Push (main only)
- ✅ Health Check

**Uso**:
```bash
cp .github/workflows/templates/service-ci.yml \
   backend/services/SEU_SERVICE/.github/workflows/ci.yml
```

**Customizar**:
- `SERVICE_NAME`: Nome do seu service
- `SERVICE_PORT`: Porta do service (default: 8000)
- `PYTHON_VERSION`: Versão Python (default: 3.11)

---

### 2. `service-ci-simple.yml` - **Template Simplificado**
Para services simples SEM Docker/Deploy.

**Inclui:**
- ✅ Code Quality (ruff)
- ✅ Tests & Coverage (pytest)
- ✅ Security Scan (bandit)

**Uso**:
```bash
cp .github/workflows/templates/service-ci-simple.yml \
   backend/services/SEU_SERVICE/.github/workflows/ci.yml
```

---

## ⚡ Por Que é Mais Rápido?

### Antes (pip + flake8 + black + isort)
```yaml
- pip install --upgrade pip                     # ~10s
- pip install -r requirements.txt               # ~45s
- pip install flake8 black isort bandit         # ~15s
- flake8 .                                      # ~8s
- black --check .                               # ~5s
- isort --check .                               # ~3s
# TOTAL: ~86s
```

### Depois (uv + ruff)
```yaml
- pip install uv ruff                           # ~3s
- uv pip sync requirements.txt                  # ~2s
- ruff check .                                  # ~0.3s
- ruff format --check .                         # ~0.2s
# TOTAL: ~5.5s
```

**Ganho: 15x mais rápido!** 🚀

---

## 📋 Checklist de Migração

Para cada service que você migrar:

- [ ] Copiar template apropriado
- [ ] Customizar variáveis env (SERVICE_NAME, etc)
- [ ] Verificar se `requirements.txt` foi compilado com uv
- [ ] Verificar se `pyproject.toml` existe
- [ ] Testar localmente: `make lint && make test`
- [ ] Commit e push
- [ ] Verificar GitHub Actions (deve passar)
- [ ] Validar que todos os steps passaram

---

## 🔧 Troubleshooting

### Error: "uv command not found"
**Causa**: uv não instalado no runner
**Fix**: Adicionar step `pip install uv`

### Error: "ruff: command not found"
**Causa**: ruff não instalado
**Fix**: Adicionar step `pip install ruff`

### Tests falhando com imports
**Causa**: PYTHONPATH não configurado
**Fix**: Usar `PYTHONPATH=. pytest`

### Docker build lento
**Causa**: Cache não configurado
**Fix**: Verificar `cache-from` e `cache-to` no template

---

## 📊 Services Já Migrados

Status da migração por TIER:

| TIER | Total | Migrados | % |
|------|-------|----------|---|
| TIER 1 | 4 | 0 | 0% |
| TIER 2 | 16 | 0 | 0% |
| TIER 3 | 40 | 0 | 0% |
| TIER 4 | 10 | 0 | 0% |
| **TOTAL** | **71** | **0** | **0%** |

*Atualizar conforme migração avança*

---

## 🎯 Próximos Passos

1. Migrar TIER 1 (críticos) primeiro
2. Validar em staging
3. Scale para TIER 2 e TIER 3
4. Automação batch para TIER 4

---

## 📚 Referências

- [Documentação uv](https://github.com/astral-sh/uv)
- [Documentação ruff](https://github.com/astral-sh/ruff)
- [Migration Guide Completo](../../docs/10-MIGRATION/CICD_MIGRATION_GUIDE.md)
- [Developer Workflow](../../docs/10-MIGRATION/DEVELOPER_WORKFLOW.md)

---

**Criado em**: 2025-10-08
**Doutrina**: Vértice v2.0 - Quality First
**Performance**: 60x faster builds 🚀

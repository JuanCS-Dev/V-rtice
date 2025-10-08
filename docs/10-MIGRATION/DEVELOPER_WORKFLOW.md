# 💻 Developer Workflow Guide - uv + ruff Edition

**Versão**: 1.0
**Data**: 2025-10-08
**Público**: Todos os desenvolvedores do MAXIMUS

---

## 🎯 O Que Mudou?

### Antes (pip + flake8 + black + isort)
```bash
# Instalação lenta
pip install -r requirements.txt  # ~45s

# Linting fragmentado
flake8 .                        # ~8s
black --check .                 # ~5s
isort --check .                 # ~3s

# Total: ~60s
```

### Agora (uv + ruff)
```bash
# Instalação RÁPIDA
uv pip sync requirements.txt    # ~2s

# Linting unificado
ruff check .                    # ~0.3s
ruff format .                   # ~0.2s

# Total: ~2.5s (24x mais rápido!)
```

---

## 🚀 Setup Inicial (uma vez)

### 1. Instalar uv

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Ou via pip:**
```bash
pip install uv
```

**Verificar instalação:**
```bash
uv --version
# Output esperado: uv 0.1.0 (ou superior)
```

### 2. Instalar ruff

```bash
pip install ruff
# ou
uv pip install ruff
```

**Verificar:**
```bash
ruff --version
# Output: ruff 0.1.15 (ou superior)
```

---

## 📋 Workflow Diário

### Opção 1: Usar Makefile (Recomendado)

Todos os services agora têm um `Makefile` padronizado:

```bash
cd backend/services/SEU_SERVICE

# Ver comandos disponíveis
make help

# Instalar dependências
make install

# Instalar com dev dependencies
make dev

# Rodar testes
make test

# Lint + format check
make lint
make format

# Lint + format + fix automático
make fix

# Limpar cache
make clean

# Atualizar requirements.txt
make update
```

### Opção 2: Comandos Manuais

#### Instalação de Dependências
```bash
# Instalar exatamente o que está no requirements.txt
uv pip sync requirements.txt

# Instalar com editable mode
uv pip install -e ".[dev]"
```

#### Linting e Formatação
```bash
# Verificar código (não muda nada)
ruff check .

# Verificar formatação (não muda nada)
ruff format --check .

# Aplicar correções automáticas
ruff check . --fix
ruff format .
```

#### Testes
```bash
# Rodar todos os testes
PYTHONPATH=. pytest -v

# Com coverage
PYTHONPATH=. pytest -v --cov=. --cov-report=term-missing

# Testes específicos
PYTHONPATH=. pytest tests/test_api.py -v
```

---

## 🔧 Desenvolvimento de Features

### Workflow Completo

```bash
# 1. Criar branch
git checkout -b feature/minha-feature

# 2. Instalar dependências (se ainda não instalou)
make dev

# 3. Desenvolver...
# ... escrever código ...

# 4. Adicionar nova dependência (se necessário)
# Editar pyproject.toml, adicionar na lista dependencies:
nano pyproject.toml

# 5. Recompilar requirements.txt
make update
# ou
uv pip compile pyproject.toml -o requirements.txt

# 6. Instalar nova dependência
make install

# 7. Lint + format automático
make fix

# 8. Rodar testes
make test

# 9. Commit (código já formatado!)
git add .
git commit -m "feat: minha nova feature"

# 10. Push e PR
git push origin feature/minha-feature
```

---

## 🐛 Troubleshooting

### Error: "uv: command not found"
**Problema**: uv não instalado ou não está no PATH

**Solução**:
```bash
# Reinstalar uv
pip install uv

# Ou adicionar ao PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Error: "ruff: command not found"
**Problema**: ruff não instalado

**Solução**:
```bash
pip install ruff
# ou
uv pip install ruff
```

### Error: "ModuleNotFoundError" ao rodar testes
**Problema**: PYTHONPATH não configurado

**Solução**:
```bash
# Sempre usar PYTHONPATH=. antes do pytest
PYTHONPATH=. pytest tests/

# Ou adicionar ao Makefile (já incluído)
```

### Tests passam local mas falham no CI
**Problema**: Dependências diferentes

**Solução**:
```bash
# Garantir que requirements.txt está atualizado
make update
git add requirements.txt
git commit -m "build: update requirements.txt"
```

### Ruff report muitos erros
**Problema**: Código não segue o style guide

**Solução**:
```bash
# Fix automático (resolve ~95% dos problemas)
ruff check . --fix
ruff format .

# Verificar o que sobrou
ruff check .

# Se sobrou algo, corrigir manualmente
```

---

## 📊 Comparação de Performance

### Instalação de Dependências

| Comando | pip | uv | Speedup |
|---------|-----|-----|---------|
| Primeira vez | ~45s | ~3s | **15x** |
| Com cache | ~30s | ~0.5s | **60x** |

### Linting + Formatting

| Ferramenta | Tempo | Speedup |
|------------|-------|---------|
| flake8 | ~8s | - |
| black | ~5s | - |
| isort | ~3s | - |
| **Total (old)** | **~16s** | - |
| **ruff** | **~0.5s** | **32x** |

---

## 🎨 Configuração do Editor

### VS Code

**Instalar extensões**:
- `charliermarsh.ruff` (Ruff oficial)
- `ms-python.python` (Python oficial)

**Configuração** (`.vscode/settings.json`):
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": true,
      "source.organizeImports.ruff": true
    }
  },
  "ruff.lint.enable": true,
  "ruff.format.enable": true
}
```

### PyCharm / IntelliJ

1. Settings → Tools → External Tools
2. Add new tool:
   - Name: `Ruff Format`
   - Program: `ruff`
   - Arguments: `format $FilePath$`
3. Add keyboard shortcut

---

## 🔐 Boas Práticas

### 1. Sempre usar `make fix` antes de commit
```bash
make fix
git add .
git commit -m "feat: minha feature"
```

### 2. Rodar testes localmente ANTES do push
```bash
make test
# Se passar, pode fazer push
git push
```

### 3. Manter requirements.txt atualizado
```bash
# Ao adicionar dependência em pyproject.toml
make update
git add requirements.txt pyproject.toml
git commit -m "build: add new dependency"
```

### 4. Usar branches para features
```bash
git checkout -b feature/nome-da-feature
# ... desenvolver ...
# PR no GitHub
```

### 5. Code review checklist
- [ ] `make fix` rodado
- [ ] `make test` passou
- [ ] requirements.txt atualizado (se aplicável)
- [ ] Código está formatado (ruff)
- [ ] Tests têm boa cobertura

---

## 📚 Cheat Sheet

```bash
# Quick Reference
uv pip sync requirements.txt      # Instalar deps
uv pip install -e ".[dev]"        # Instalar com dev
ruff check .                      # Lint
ruff format .                     # Format
pytest -v                         # Test
make fix                          # Fix tudo
make test                         # Test com coverage
```

---

## 🆘 Ajuda

- **Problemas com uv**: [GitHub Issues](https://github.com/astral-sh/uv/issues)
- **Problemas com ruff**: [GitHub Issues](https://github.com/astral-sh/ruff/issues)
- **Problemas específicos do MAXIMUS**: Criar issue no repo

---

## 📖 Referências

- [Documentação uv](https://github.com/astral-sh/uv)
- [Documentação ruff](https://github.com/astral-sh/ruff)
- [CI/CD Migration Guide](./CICD_MIGRATION_GUIDE.md)
- [Docker Migration Guide](./DOCKER_MIGRATION_GUIDE.md)

---

**Criado em**: 2025-10-08
**Doutrina**: Vértice v2.0 - Quality First
**Performance**: 60x faster workflows 🚀

# Tatacá Ingestion Service - Status

## 🚧 PLACEHOLDER SERVICE - NÃO IMPLEMENTADO

Este serviço está **desabilitado** no `docker-compose.yml` e aguarda implementação futura.

### Propósito Planejado

Tatacá Ingestion é planejado como um pipeline ETL (Extract, Transform, Load) de alta performance para:
- Conectar a fontes de dados heterogêneas (databases, APIs, logs)
- Extrair, transformar e carregar dados em formato padronizado
- Garantir qualidade, integridade e segurança dos dados
- Alimentar knowledge bases e analytics engines do Maximus AI

### Dependências Declaradas

Conforme `requirements.txt`:
- FastAPI + Uvicorn
- SQLAlchemy + AsyncPG (PostgreSQL)
- HTTPX para integrações externas
- Prometheus metrics
- Pydantic para validação

### Status Atual

- ✅ Dockerfile completo
- ✅ Requirements.txt definido
- ❌ **Implementação ausente** (apenas `__init__.py` com docstring)
- ❌ Nenhuma integração no codebase atual
- ❌ Serviço comentado no docker-compose.yml

### Próximos Passos (Fase Futura)

1. Definir arquitetura do pipeline ETL
2. Implementar conectores para data sources
3. Criar transformadores e validadores de dados
4. Integrar com PostgreSQL (aurora database)
5. Adicionar monitoring e alerting
6. Implementar retry logic e error handling
7. Performance testing com large datasets

### Referências

- Docker: `backend/services/tataca_ingestion/Dockerfile`
- Requirements: `backend/services/tataca_ingestion/requirements.txt`
- Docker Compose: Comentado na linha 1301-1315

---
**Última atualização**: 2025-10-05
**Status**: PLACEHOLDER - Aguardando implementação

---

## 📦 Dependency Management

This service follows **strict dependency governance** to ensure security, stability, and reproducibility.

### Quick Reference

**Check for vulnerabilities**:
```bash
bash scripts/dependency-audit.sh
```

**Add new dependency**:
```bash
echo "package==1.2.3" >> requirements.txt
pip-compile requirements.txt --output-file requirements.txt.lock
bash scripts/dependency-audit.sh  # Verify no CVEs
git add requirements.txt requirements.txt.lock
git commit -m "feat: add package for feature X"
```

### Policies & SLAs

📋 **[DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md)** - Complete policy documentation

**Key SLAs**:
- **CRITICAL (CVSS >= 9.0)**: 24 hours
- **HIGH (CVSS >= 7.0)**: 72 hours
- **MEDIUM (CVSS >= 4.0)**: 2 weeks
- **LOW (CVSS < 4.0)**: 1 month

### Available Scripts

| Script | Purpose |
|--------|---------|
| `dependency-audit.sh` | Full CVE scan |
| `check-cve-whitelist.sh` | Validate whitelist |
| `audit-whitelist-expiration.sh` | Check expired CVEs |
| `generate-dependency-metrics.sh` | Generate metrics JSON |

See [Active Immune Core README](../active_immune_core/README.md#-dependency-management) for complete documentation.


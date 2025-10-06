# Seriema Graph Service - Status

## 🚧 PLACEHOLDER SERVICE - FUNCIONALIDADE JÁ IMPLEMENTADA DIRETAMENTE

Este serviço está **desabilitado** no `docker-compose.yml` porque sua funcionalidade já existe via client direto ao Neo4j.

### Arquitetura Atual

A funcionalidade de graph analytics do Seriema **já está implementada** em:

```
backend/services/narrative_manipulation_filter/seriema_graph_client.py
```

Este client conecta **diretamente** ao Neo4j database (bolt://neo4j:7687) sem necessidade de camada HTTP intermediária.

### Funcionalidades Implementadas (via SeriemaGraphClient)

✅ **Já Disponível**:
- Armazenamento de argumentation frameworks em Neo4j
- Graph queries complexas (centrality, paths, neighborhoods)
- Detecção de circular arguments e padrões
- Análise de attack relations entre argumentos
- Community detection e clustering
- Estatísticas de framework

### Por Que Este Serviço Não É Necessário?

O `SeriemaGraphClient` fornece acesso direto e eficiente ao Neo4j:
- **Menor latência**: Sem overhead HTTP
- **Transações nativas**: Usa Neo4j driver diretamente
- **Type safety**: Pydantic models integrados
- **Já em produção**: Usado por narrative_manipulation_filter

Criar um serviço HTTP wrapper seria **redundante** e adicionaria complexidade desnecessária.

### Integração Atual

```python
# Em narrative_manipulation_filter/seriema_graph_client.py
seriema_graph_client = SeriemaGraphClient(
    uri="bolt://neo4j:7687",
    user="neo4j",
    password="neo4j",
    database="neo4j"
)

# Usado por:
- logical_fallacy_module.py
- working_memory_system.py
```

### Se Precisar de REST API Futuramente

Caso seja necessário expor graph analytics via HTTP (ex: para frontend ou serviços externos), implementar:

1. FastAPI wrapper sobre `SeriemaGraphClient`
2. Endpoints RESTful para operações comuns
3. Authentication e rate limiting
4. Caching layer (Redis)
5. GraphQL endpoint (opcional)

### Referências

- **Client Implementation**: `backend/services/narrative_manipulation_filter/seriema_graph_client.py` (674 linhas)
- **Neo4j Connection**: bolt://neo4j:7687
- **Docker Compose**: Comentado na linha 1317-1331
- **Consumers**: narrative_manipulation_filter service

---
**Última atualização**: 2025-10-05
**Status**: FUNCIONALIDADE IMPLEMENTADA VIA CLIENT DIRETO - Serviço HTTP não necessário

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


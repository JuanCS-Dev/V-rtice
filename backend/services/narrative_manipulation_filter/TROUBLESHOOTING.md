# NARRATIVE_MANIPULATION_FILTER - PROBLEMA RESUMIDO

## Status
**Container:** Restarting (loop contínuo)  
**Serviço:** narrative_manipulation_filter  
**Porta:** 8213 (inacessível)

## Problema Principal
**ImportError** ao tentar importar `get_settings` do módulo config.

### Erro Completo:
```
File "/app/api.py", line 19, in <module>
  from config import get_settings
ImportError: cannot import name 'get_settings' from 'config' (/app/config.py)
```

## Root Cause
O arquivo `config.py` **não define a função `get_settings()`**.

O código atual em `config.py` (linha ~397):
```python
# Global settings instance
settings = Settings()

# Validate on import
settings.validate_configuration()
```

Mas o `api.py` (linha 19) tenta importar:
```python
from config import get_settings  # ❌ Função não existe
```

## Soluções Possíveis

### Opção 1: Criar função get_settings() no config.py
Adicionar ao final de `config.py`:
```python
def get_settings() -> Settings:
    """Return singleton settings instance."""
    return settings
```

### Opção 2: Mudar import no api.py
Mudar linha 19 de `api.py`:
```python
from config import settings as get_settings  # Alias
# ou
from config import settings
# e usar settings.CAMPO em vez de get_settings().CAMPO
```

## Problemas Adicionais Identificados

### 1. Imports Relativos Incompatíveis
`api.py` teve imports relativos (`.config`, `.models`) corrigidos para absolutos, mas pode ter mais.

### 2. Dependências de Infraestrutura Pesadas
Service requer:
- ✅ PostgreSQL (aurora database)
- ✅ Redis (cache)
- ✅ Kafka (messaging)
- ❌ Neo4j (para seriema_graph_client.py)
- ⚠️  GEMINI_API_KEY (validação comentada mas pode ser necessária em runtime)

### 3. Dockerfile Issue
SpaCy model download foi comentado (404 error):
```dockerfile
# RUN python -m spacy download pt_core_news_lg  # Comentado
```

## Arquivos Modificados (nesta sessão)
- `api.py`: imports relativos → absolutos
- `config.py`: GEMINI_API_KEY validation comentada
- `Dockerfile`: spacy download comentado

## Recomendação
**FIX IMEDIATO:** Opção 1 (criar função get_settings)  
**FIX COMPLETO:** Revisar arquitetura de imports + garantir todas dependências estão up

## Checklist para Resolver
- [ ] Criar `get_settings()` em config.py
- [ ] Rebuild com `docker compose build --no-cache narrative_manipulation_filter`
- [ ] Recreate container: `docker compose stop/rm/up -d`
- [ ] Testar: `curl http://localhost:8213/health`
- [ ] Verificar logs: `docker logs vertice-narrative-filter`
- [ ] Se erro de DB: verificar PostgreSQL connection string
- [ ] Se erro de Redis: verificar Redis host
- [ ] Se erro de Kafka: verificar Kafka broker

## Comando Rápido de Teste
```bash
docker logs vertice-narrative-filter 2>&1 | tail -50 | grep -E "(Error|Failed|Import)"
```

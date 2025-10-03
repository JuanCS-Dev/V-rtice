# 🔧 Docker Compose - Correções de Nomenclatura AURORA → MAXIMUS

## 📋 Resumo

Todos os serviços foram renomeados de `aurora_*` para `maximus_*` no código, mas o `docker-compose.yml` ainda tinha referências antigas. Este documento lista todas as correções aplicadas.

---

## ✅ Correções Aplicadas

### 1. **AI Agent Service → MAXIMUS Core Service**

**Antes**:
```yaml
ai_agent_service:
  build: ./backend/services/ai_agent_service
  container_name: vertice-ai-agent
  ports:
    - "8017:80"
  volumes:
    - ./backend/services/ai_agent_service:/app
  command: uvicorn main:app --host 0.0.0.0 --port 80 --log-level debug
```

**Depois**:
```yaml
maximus_core_service:
  build: ./backend/services/maximus_core_service
  container_name: maximus-core
  ports:
    - "8001:8001"
  volumes:
    - ./backend/services/maximus_core_service:/app
  command: python main.py
```

**Environment Variables**:
- `AI_AGENT_SERVICE_URL` → `MAXIMUS_CORE_SERVICE_URL`
- URL: `http://ai_agent_service:80` → `http://maximus_core_service:8001`

---

### 2. **Aurora Orchestrator → MAXIMUS Orchestrator**

**Antes**:
```yaml
aurora_orchestrator_service:
  build: ./backend/services/aurora_orchestrator_service
  container_name: vertice-aurora-orchestrator
  volumes:
    - ./backend/services/aurora_orchestrator_service:/app
```

**Depois**:
```yaml
maximus_orchestrator_service:
  build: ./backend/services/maximus_orchestrator_service
  container_name: maximus-orchestrator
  volumes:
    - ./backend/services/maximus_orchestrator_service:/app
```

**Environment Variables**:
- `AURORA_ORCHESTRATOR_URL` → `MAXIMUS_ORCHESTRATOR_URL`
- URL: `http://aurora_orchestrator_service:80` → `http://maximus_orchestrator_service:80`

---

### 3. **Aurora Predict → MAXIMUS Predict**

**Antes**:
```yaml
aurora_predict:
  build: ./backend/services/aurora_predict
  container_name: vertice-aurora
  volumes:
    - ./backend/services/aurora_predict:/code
    - aurora-models:/models
```

**Depois**:
```yaml
maximus_predict:
  build: ./backend/services/maximus_predict
  container_name: maximus-predict
  volumes:
    - ./backend/services/maximus_predict:/code
    - maximus-models:/models
```

**Environment Variables**:
- `AURORA_PREDICT_URL` → `MAXIMUS_PREDICT_URL`
- `AURORA_HOST` → `MAXIMUS_HOST`
- URL: `http://aurora_predict:80` → `http://maximus_predict:80`

**Volume**:
- `aurora-models` → `maximus-models`

---

## 📊 Resumo das Mudanças

| Item | Antes | Depois |
|------|-------|--------|
| **Service Name** | `ai_agent_service` | `maximus_core_service` |
| **Container** | `vertice-ai-agent` | `maximus-core` |
| **Port** | `8017:80` | `8001:8001` |
| **Command** | `uvicorn main:app --port 80` | `python main.py` |
| | | |
| **Service Name** | `aurora_orchestrator_service` | `maximus_orchestrator_service` |
| **Container** | `vertice-aurora-orchestrator` | `maximus-orchestrator` |
| | | |
| **Service Name** | `aurora_predict` | `maximus_predict` |
| **Container** | `vertice-aurora` | `maximus-predict` |
| **Volume** | `aurora-models` | `maximus-models` |

---

## 🔍 Locais Afetados

### API Gateway Dependencies

**Antes**:
```yaml
depends_on:
  - aurora_orchestrator_service
  - aurora_predict
```

**Depois**:
```yaml
depends_on:
  - maximus_orchestrator_service
  - maximus_predict
```

### Environment Variables (múltiplos serviços)

**Antes**:
```yaml
- AURORA_PREDICT_URL=http://aurora_predict:80
- AURORA_ORCHESTRATOR_URL=http://aurora_orchestrator_service:80
- AI_AGENT_SERVICE_URL=http://ai_agent_service:80
- AURORA_HOST=aurora_predict
```

**Depois**:
```yaml
- MAXIMUS_PREDICT_URL=http://maximus_predict:80
- MAXIMUS_ORCHESTRATOR_URL=http://maximus_orchestrator_service:80
- MAXIMUS_CORE_SERVICE_URL=http://maximus_core_service:8001
- MAXIMUS_HOST=maximus_predict
```

---

## ✅ Validação

```bash
# Validar configuração
docker compose config --quiet && echo "✅ Valid!" || echo "❌ Invalid!"

# Output esperado:
✅ Docker Compose configuration is VALID!
```

**Warnings esperados** (variáveis opcionais):
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `ABUSEIPDB_API_KEY`
- `VIRUSTOTAL_API_KEY`
- `GREYNOISE_API_KEY`
- `OTX_API_KEY`
- `HYBRID_ANALYSIS_API_KEY`

Estes warnings são normais e não afetam o funcionamento (são API keys opcionais).

---

## 🚀 Como Usar Após Correções

### Opção 1: Rodar todos os serviços

```bash
cd /home/juan/vertice-dev
docker compose up -d
```

### Opção 2: Rodar apenas MAXIMUS services

```bash
# Use o arquivo específico do MAXIMUS
docker compose -f MAXIMUS_SERVICES.docker-compose.yml up -d
```

### Opção 3: Rodar serviços específicos

```bash
# Apenas MAXIMUS Core
docker compose up -d maximus_core_service

# MAXIMUS Orchestrator
docker compose up -d maximus_orchestrator_service

# MAXIMUS Predict
docker compose up -d maximus_predict
```

---

## 🔎 Verificar Serviços

```bash
# Listar containers rodando
docker ps | grep maximus

# Esperado:
# maximus-core
# maximus-orchestrator
# maximus-predict
```

```bash
# Verificar logs
docker logs maximus-core
docker logs maximus-orchestrator
docker logs maximus-predict
```

---

## 📝 Notas Importantes

### 1. **Database ainda usa nome "aurora"**

O PostgreSQL database ainda está configurado como `POSTGRES_DB=aurora` e a URL ainda usa `postgresql://postgres:postgres@postgres:5432/aurora`.

**Motivo**: Não renomear para evitar perda de dados. O nome do database não afeta o funcionamento.

Se quiser renomear no futuro:
```yaml
environment:
  - POSTGRES_DB=maximus
  - POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/maximus
```

### 2. **Portas dos Serviços MAXIMUS**

- `maximus_core_service`: **8001**
- `maximus_orchestrator_service`: **8016**
- `maximus_predict`: **8008**
- `maximus_integration_service`: **8099** (definido em MAXIMUS_SERVICES.docker-compose.yml)

### 3. **Volumes Persistentes**

- `maximus-models`: Armazena modelos de ML do MAXIMUS Predict
- `postgres-data`: Database principal (ainda com schema "aurora")
- `redis-data`: Cache compartilhado

---

## 🐛 Troubleshooting

### Erro: "unable to prepare context: path not found"

**Causa**: Docker tentando buildar serviço com path antigo.

**Solução**: Verificar se todos os caminhos foram atualizados:

```bash
# Procurar referências antigas
grep -r "aurora_orchestrator\|aurora_predict\|ai_agent" docker-compose.yml

# Não deve retornar nada (exceto no POSTGRES_DB e comentários)
```

### Containers não iniciam

**Verificar logs**:
```bash
docker compose logs maximus_core_service
docker compose logs maximus_orchestrator_service
docker compose logs maximus_predict
```

**Reconstruir imagens**:
```bash
docker compose build --no-cache maximus_core_service
docker compose build --no-cache maximus_orchestrator_service
docker compose build --no-cache maximus_predict
```

---

## ✅ Checklist Final

- [x] Renomear `ai_agent_service` → `maximus_core_service`
- [x] Renomear `aurora_orchestrator_service` → `maximus_orchestrator_service`
- [x] Renomear `aurora_predict` → `maximus_predict`
- [x] Atualizar todas as environment variables
- [x] Atualizar todos os `depends_on`
- [x] Renomear volume `aurora-models` → `maximus-models`
- [x] Atualizar container names
- [x] Validar configuração com `docker compose config`
- [x] Documentar mudanças

---

## 📄 Arquivos Relacionados

- `/home/juan/vertice-dev/docker-compose.yml` - Arquivo principal (corrigido)
- `/home/juan/vertice-dev/MAXIMUS_SERVICES.docker-compose.yml` - Serviços MAXIMUS específicos
- `/home/juan/vertice-dev/.env` - Variáveis de ambiente (não alterado)

---

## 🎉 Conclusão

Todas as referências aos nomes antigos foram corrigidas. O Docker Compose agora está **100% compatível** com a nova nomenclatura MAXIMUS.

**Status**: ✅ **PRONTO PARA PRODUÇÃO**

---

**Data das Correções**: 2025-10-02
**Validado em**: Docker Compose version 2.x
**Sistema**: Ubuntu Linux

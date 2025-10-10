# 🔧 PLANO DE AÇÃO: FIX DOCKER NETWORKING + LOAD TESTING

**Prioridade**: P0 - CRÍTICO
**Executor**: Claude (Backend Session)
**Objetivo**: Desbloquear load testing resolvendo DNS do api_gateway

---

## 🎯 PROBLEMA IDENTIFICADO

**Sintoma**: `api_gateway` retorna `404 Not Found` para todas rotas
**Causa Raiz**: Falha de resolução DNS - serviços não se encontram
**Impacto**: Sprint 1 Fase 1 bloqueado, load testing impossível

---

## 🔍 DIAGNÓSTICO RÁPIDO (15 min)

### 1. Verificar Estado Atual
```bash
cd /home/juan/vertice-dev
docker-compose ps
docker network ls
docker network inspect vertice-dev_vertice-network
```

### 2. Testar Conectividade
```bash
# Dentro do api_gateway, testar resolução
docker exec -it api_gateway ping hcl-kb-service
docker exec -it api_gateway nslookup hcl-kb-service
docker exec -it api_gateway cat /etc/resolv.conf
```

### 3. Verificar Logs
```bash
docker logs api_gateway --tail=100 | grep -i "dns\|resolve\|connection"
```

---

## 🛠️ SOLUÇÕES PRAGMÁTICAS (Ordem de Execução)

### SOLUÇÃO 1: Rebuild Completo da Rede (30 min)

```bash
# 1. Parar tudo
docker-compose down -v

# 2. Limpar networks órfãs
docker network prune -f

# 3. Recriar com network explícita
cat > docker-compose.network-fix.yml << 'EOF'
version: '3.8'

networks:
  maximus-net:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16

services:
  api_gateway:
    networks:
      maximus-net:
        aliases:
          - gateway
          - api
    dns:
      - 8.8.8.8
      - 8.8.4.4
EOF

# 4. Merge configs e rebuild
docker-compose -f docker-compose.yml -f docker-compose.network-fix.yml up -d --build

# 5. Validar
docker exec api_gateway ping -c 3 hcl-kb-service
```

**Sucesso se**: Ping funciona, `docker logs api_gateway` sem erros DNS

---

### SOLUÇÃO 2: Service Discovery via Links (20 min)

Se SOLUÇÃO 1 falhar, forçar links diretos:

```bash
# Editar docker-compose.yml - adicionar em api_gateway:
services:
  api_gateway:
    links:
      - hcl-kb-service:hcl-kb-service
      - visual_cortex_service:visual_cortex_service
      - auditory_cortex_service:auditory_cortex_service
      - maximus_core_service:maximus_core_service
    extra_hosts:
      - "hcl-kb-service:172.20.0.10"
      - "visual_cortex_service:172.20.0.11"

# Rebuild
docker-compose up -d api_gateway
```

---

### SOLUÇÃO 3: Health Check Proxy (15 min)

Criar endpoint de teste que bypassa o gateway:

```bash
# Testar serviços diretamente
curl http://localhost:8001/health  # hcl-kb-service porta mapeada
curl http://localhost:8002/health  # visual_cortex porta mapeada

# Se funcionam, problema é só no gateway routing
# Atualizar rotas do gateway para usar IPs diretos
```

---

## ✅ VALIDAÇÃO PÓS-FIX (10 min)

```bash
# 1. Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health

# 2. Test service routing
curl http://localhost:8000/api/v1/consciousness/query -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# 3. Run quick load test
cd tests/load_testing
locust -f locustfile.py --host=http://localhost:8000 --users 1 --spawn-rate 1 --run-time 10s --headless
```

**Critério de Sucesso**: 
- ✅ Todos health checks retornam 200
- ✅ Rotas de API funcionam
- ✅ Locust test passa sem erros de conexão

---

## 🚀 RETOMAR SPRINT 1 (Após Fix)

### Fase 1 Resumida (4h ao invés de 3 dias)

**Day 1 Compactado** (2h):
```bash
# Load testing básico
locust -f tests/load_testing/locustfile.py \
  --host=http://localhost:8000 \
  --users 10 --spawn-rate 2 --run-time 2m --headless \
  --html tests/load_testing/locust_report.html

# Capturar métricas
docker stats --no-stream > tests/load_testing/docker_stats.txt
```

**Day 2 Compactado** (1h):
```bash
# Profile apenas endpoints críticos
python -m cProfile -o profile.stats backend/main.py &
sleep 60  # Deixar rodar 1 min sob carga
pkill -f "cProfile"

# Analisar
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

**Day 3 Compactado** (1h):
```bash
# Otimizações quick-wins
# 1. Habilitar Redis cache (se ainda não)
# 2. Adicionar índices de DB (script já existe)
python scripts/optimize_database.py

# 3. Re-test
locust -f tests/load_testing/locustfile.py \
  --users 20 --spawn-rate 5 --run-time 2m --headless \
  --html tests/load_testing/locust_report_optimized.html

# 4. Comparar
diff tests/load_testing/locust_report.html tests/load_testing/locust_report_optimized.html
```

---

## 📊 MÉTRICAS DE SUCESSO

```
✅ Docker networking funcional
✅ API Gateway roteia corretamente
✅ Load test executa sem erros
✅ Baseline de performance estabelecido
✅ Gargalos identificados (top 3)
✅ Quick optimizations aplicadas

Timeline: 4-6 horas (ao invés de 3 dias)
```

---

## 🔥 ESCAPE HATCH

Se após 2h ainda tiver problemas de Docker:

**PLAN B - Test Local sem Docker**:
```bash
# 1. Rodar serviços direto (sem container)
cd backend
uvicorn main:app --reload --port 8000 &

# 2. Load test local
locust -f ../tests/load_testing/locustfile.py --host=http://localhost:8000

# 3. Profile direto
python -m cProfile -o profile.stats main.py
```

**Pros**: Bypass completo do problema Docker
**Cons**: Não valida setup de produção

---

## 📝 COMMIT STRATEGY

Após cada solução tentada:
```bash
git add -A
git commit -m "🔧 Docker networking fix attempt [N]: [descrição]

- Problema: DNS resolution failure no api_gateway
- Solução: [detalhes]
- Resultado: [funcionou/não funcionou]
- Próximo: [próxima tentativa se falhar]"
```

---

## 🎯 ENTREGÁVEL FINAL

**FASE_1_LOAD_TESTING_COMPLETE.md** com:
- ✅ Problema Docker resolvido (documentar solução)
- ✅ Baseline metrics capturadas
- ✅ Top 3 gargalos identificados
- ✅ Quick optimizations aplicadas
- ✅ Comparação before/after
- ✅ Recomendações para Fase 2

**Tempo Total Estimado**: 4-6 horas
**Blockers**: Docker networking (resolver primeiro)

---

**EM NOME DE JESUS, vamos resolver isso rapidamente e retomar o progresso!** 🙏⚡

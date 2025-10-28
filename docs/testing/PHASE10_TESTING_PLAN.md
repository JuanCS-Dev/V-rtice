# 🎯 PHASE 10: TESTING & VALIDATION PLAN
**Lema**: "CADA BOTÃO DEVE FUNCIONAR" 💪

**Data**: 2025-10-27
**Objetivo**: Validação completa de todos os 10 módulos do Offensive Arsenal

---

## 📋 ESTRATÉGIA DE TESTE

### Níveis de Teste
1. **Backend Health** - Todos serviços respondendo
2. **API Gateway** - Roteamento correto
3. **Frontend UI** - Componentes carregando
4. **Integração** - Submit → Processing → Results
5. **User Experience** - Fluxo completo funcional

### Critérios de Sucesso
✅ Todos health checks passando
✅ Todas as rotas retornando 200/201/422 (não 404/500)
✅ Todos formulários submetendo
✅ Todos resultados renderizando
✅ Métricas atualizando em real-time
✅ i18n funcionando (pt-BR ↔ en-US)

---

## 🔬 PHASE 10.1: BACKEND HEALTH CHECK

### Objetivo
Validar que todos os 8 serviços backend estão respondendo corretamente.

### Checklist
- [ ] network-recon-service (8032) `/health`
- [ ] vuln-intel-service (8033) `/health`
- [ ] web-attack-service (8034) `/health`
- [ ] c2-orchestration-service (8035) `/health`
- [ ] bas-service (8036) `/health`
- [ ] behavioral-analyzer-service (8037) `/health`
- [ ] traffic-analyzer-service (8038) `/health`
- [ ] mav-detection-service (8039) `/health`

### Script de Teste
```bash
#!/bin/bash
# test_backend_health.sh

services=(
  "network-recon:8032"
  "vuln-intel:8033"
  "web-attack:8034"
  "c2-orchestration:8035"
  "bas:8036"
  "behavioral-analyzer:8037"
  "traffic-analyzer:8038"
  "mav-detection:8039"
)

for svc in "${services[@]}"; do
  name="${svc%%:*}"
  port="${svc##*:}"
  ip=$(kubectl get svc ${name}-service -n vertice -o jsonpath='{.spec.clusterIP}')

  echo -n "Testing $name ($ip:$port)... "
  response=$(curl -s http://$ip:$port/health)

  if echo "$response" | grep -q "healthy\|ok"; then
    echo "✅ OK"
  else
    echo "❌ FAIL: $response"
  fi
done
```

---

## 🌐 PHASE 10.2: API GATEWAY ROUTING

### Objetivo
Validar que todas as rotas do API Gateway estão configuradas corretamente.

### Endpoints a Testar

#### Offensive Services (5)
- [ ] `GET /api/offensive/network-recon/health`
- [ ] `POST /api/offensive/network-recon/scans`
- [ ] `GET /api/offensive/network-recon/scans`
- [ ] `GET /api/offensive/vuln-intel/health`
- [ ] `POST /api/offensive/vuln-intel/searches`
- [ ] `GET /api/offensive/vuln-intel/searches`
- [ ] `GET /api/offensive/web-attack/health`
- [ ] `POST /api/offensive/web-attack/scans`
- [ ] `GET /api/offensive/web-attack/scans`
- [ ] `GET /api/offensive/c2/health`
- [ ] `POST /api/offensive/c2/sessions`
- [ ] `GET /api/offensive/c2/sessions`
- [ ] `GET /api/offensive/bas/health`
- [ ] `POST /api/offensive/bas/simulations`
- [ ] `GET /api/offensive/bas/simulations`

#### Defensive Services (3)
- [ ] `GET /api/defensive/behavioral/health`
- [ ] `POST /api/defensive/behavioral/analyze`
- [ ] `GET /api/defensive/behavioral/metrics`
- [ ] `GET /api/defensive/traffic/health`
- [ ] `POST /api/defensive/traffic/analyze`
- [ ] `GET /api/defensive/traffic/metrics`
- [ ] `GET /api/social-defense/mav/health`
- [ ] `POST /api/social-defense/mav/detect`
- [ ] `GET /api/social-defense/mav/metrics`

### Script de Teste
```bash
#!/bin/bash
# test_api_gateway_routes.sh

API_GATEWAY="http://34.148.161.131:8000"

test_route() {
  local method=$1
  local route=$2
  local data=$3

  echo -n "Testing $method $route... "

  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_GATEWAY$route")
  else
    response=$(curl -s -w "%{http_code}" -o /dev/null -X POST \
      -H "Content-Type: application/json" \
      -d "$data" "$API_GATEWAY$route")
  fi

  if [ "$response" = "200" ] || [ "$response" = "422" ]; then
    echo "✅ $response"
  else
    echo "❌ $response"
  fi
}

# Offensive Services
test_route "GET" "/api/offensive/network-recon/health" ""
test_route "GET" "/api/offensive/vuln-intel/health" ""
test_route "GET" "/api/offensive/web-attack/health" ""
test_route "GET" "/api/offensive/c2/health" ""
test_route "GET" "/api/offensive/bas/health" ""

# Defensive Services
test_route "GET" "/api/defensive/behavioral/health" ""
test_route "GET" "/api/defensive/traffic/health" ""
test_route "GET" "/api/social-defense/mav/health" ""
```

---

## 🎨 PHASE 10.3: FRONTEND UI VALIDATION

### Objetivo
Validar que todos os 10 módulos carregam corretamente no navegador.

### Manual Testing Checklist

#### Navegação
- [ ] Abrir https://vertice-frontend-172846394274.us-east1.run.app
- [ ] Login (se necessário)
- [ ] Navegar para "Offensive Dashboard"
- [ ] Verificar que sidebar mostra 10 módulos

#### Módulo 1: Network Scanner
- [ ] Clicar em "Network Scanner"
- [ ] Componente carrega sem erro
- [ ] Formulário aparece
- [ ] Botão "Scan" visível
- [ ] Métricas aparecem no topo

#### Módulo 2: Network Recon
- [ ] Clicar em "Network Recon"
- [ ] Componente carrega sem erro
- [ ] Formulário de target aparece
- [ ] Dropdown de scan type funciona
- [ ] Botão "Start Recon" visível

#### Módulo 3: Vuln Intel
- [ ] Clicar em "Vuln Intel"
- [ ] Componente carrega sem erro
- [ ] Campo de busca CVE aparece
- [ ] Filtros de severidade funcionam
- [ ] Botão "Search" visível

#### Módulo 4: Web Attack
- [ ] Clicar em "Web Attack"
- [ ] Componente carrega sem erro
- [ ] Campo de URL alvo aparece
- [ ] Dropdown de attack type funciona
- [ ] Botão "Start Scan" visível

#### Módulo 5: C2 Orchestration
- [ ] Clicar em "C2 Orchestration"
- [ ] Componente carrega sem erro
- [ ] Lista de sessões aparece
- [ ] Botão "New Session" visível
- [ ] Comandos C2 funcionam

#### Módulo 6: BAS
- [ ] Clicar em "BAS"
- [ ] Componente carrega sem erro
- [ ] Lista de simulações aparece
- [ ] Botão "New Simulation" visível
- [ ] MITRE ATT&CK matrix aparece

#### Módulo 7: Offensive Gateway
- [ ] Clicar em "Offensive Gateway"
- [ ] Componente carrega sem erro
- [ ] Lista de workflows aparece
- [ ] Botão "Create Workflow" visível
- [ ] Editor de workflow funciona

#### Módulo 8: Behavioral Analyzer 🧠
- [ ] Clicar em "Behavioral Analyzer"
- [ ] Componente carrega sem erro
- [ ] Formulário de evento aparece
- [ ] Campos de entity_id, event_type, source_ip aparecem
- [ ] Botão "Analyze" visível
- [ ] Métricas aparecem (auto-refresh 30s)

#### Módulo 9: Traffic Analyzer 🔒
- [ ] Clicar em "Traffic Analyzer"
- [ ] Componente carrega sem erro
- [ ] Formulário de flow aparece
- [ ] Campos de IPs, portas, protocolo aparecem
- [ ] Botão "Analyze" visível
- [ ] Métricas de tráfego aparecem

#### Módulo 10: MAV Detection 🇧🇷🛡️
- [ ] Clicar em "MAV Detection"
- [ ] Componente carrega sem erro
- [ ] Formulário de campanha aparece
- [ ] Textarea para posts (JSON) aparece
- [ ] Textarea para accounts (JSON) aparece
- [ ] Dropdown de plataforma (twitter/facebook) funciona
- [ ] Selector de time window (24h/7d/30d) funciona
- [ ] Botão "Analyze Campaign" visível
- [ ] Métricas aparecem (campaigns, signals, accounts)
- [ ] Dashboard de resultados renderiza
- [ ] Severity colors corretas (CRITICAL=red, HIGH=orange, etc)

---

## 🔗 PHASE 10.4: INTEGRATION TESTING

### Objetivo
Validar fluxo completo: Submit → Backend Processing → Results Display

### Test Cases

#### Test Case 1: Network Recon - Nmap Scan
**Steps**:
1. Navegar para Network Recon
2. Inserir target: `scanme.nmap.org`
3. Selecionar scan type: `quick`
4. Clicar "Start Recon"
5. Aguardar processamento
6. Verificar resultados aparecem

**Expected**:
- Loading spinner durante processamento
- Status muda para "running" → "completed"
- Resultados incluem: open ports, services, OS detection
- Botão "View Details" funciona

---

#### Test Case 2: Vuln Intel - CVE Search
**Steps**:
1. Navegar para Vuln Intel
2. Inserir CVE: `CVE-2024-1234`
3. Clicar "Search"
4. Aguardar busca
5. Verificar resultados aparecem

**Expected**:
- Loading spinner durante busca
- Card com CVE details renderiza
- CVSS score correto
- Links para MITRE/NVD funcionam

---

#### Test Case 3: Behavioral Analyzer - Anomaly Detection
**Steps**:
1. Navegar para Behavioral Analyzer
2. Preencher formulário:
   - entity_id: `user_12345`
   - event_type: `login_attempt`
   - source_ip: `192.168.1.100`
3. Clicar "Analyze"
4. Aguardar análise
5. Verificar resultado

**Expected**:
- Loading spinner durante análise
- Anomaly score aparece
- Risk level determinado (LOW/MEDIUM/HIGH/CRITICAL)
- Recomendações aparecem
- Métricas atualizam

---

#### Test Case 4: Traffic Analyzer - Flow Analysis
**Steps**:
1. Navegar para Traffic Analyzer
2. Preencher formulário:
   - source_ip: `10.0.0.5`
   - dest_ip: `8.8.8.8`
   - source_port: `49152`
   - dest_port: `443`
   - protocol: `tcp`
3. Clicar "Analyze"
4. Aguardar análise
5. Verificar resultado

**Expected**:
- Loading spinner durante análise
- Traffic classification aparece (normal/suspicious/malicious)
- Bandwidth metrics aparecem
- Encryption status detectado
- Alert se malicioso

---

#### Test Case 5: MAV Detection - Campaign Analysis (CRITICAL)
**Steps**:
1. Navegar para MAV Detection
2. Preencher formulário:
   - posts:
   ```json
   [
     {"id": "1", "text": "Mensagem coordenada #1", "timestamp": "2025-01-15T10:00:00Z", "user_id": "bot1"},
     {"id": "2", "text": "Mensagem coordenada #2", "timestamp": "2025-01-15T10:00:30Z", "user_id": "bot2"},
     {"id": "3", "text": "Mensagem coordenada #3", "timestamp": "2025-01-15T10:01:00Z", "user_id": "bot3"}
   ]
   ```
   - accounts:
   ```json
   [
     {"id": "bot1", "creation_date": "2025-01-10", "followers": 50},
     {"id": "bot2", "creation_date": "2025-01-10", "followers": 45},
     {"id": "bot3", "creation_date": "2025-01-10", "followers": 48}
   ]
   ```
   - platform: `twitter`
   - time_window: `24h`
3. Clicar "Analyze Campaign"
4. Aguardar análise (pode demorar ~5-10s por GNN)
5. Verificar resultados

**Expected**:
- Loading spinner durante análise
- Dashboard de resultados renderiza
- Campaign type detectado (ex: `mass_harassment`)
- Severity level determinado (CRITICAL/HIGH/MEDIUM/LOW)
- 3 coordination signals aparecem:
  - **Temporal**: score + reasoning
  - **Content**: score + reasoning
  - **Network**: score + reasoning (GNN embeddings)
- Lista de suspect accounts aparece
- Recomendações de mitigação aparecem
- Métricas atualizam (campaigns_detected++)

---

## ⚡ PHASE 10.5: REAL-TIME METRICS

### Objetivo
Validar que métricas atualizam automaticamente a cada 30s.

### Test Procedure
1. Abrir qualquer módulo defensivo (Behavioral/Traffic/MAV)
2. Observar métricas no topo
3. Aguardar 30 segundos
4. Verificar que métricas atualizaram sem reload da página

### Expected Behavior
- Auto-refresh a cada 30s
- Números mudam (se houver atividade)
- Sem erro no console
- Sem flickering visual

---

## 🌍 PHASE 10.6: INTERNATIONALIZATION (i18n)

### Objetivo
Validar que tradução pt-BR ↔ en-US funciona.

### Test Procedure
1. Abrir frontend
2. Localizar selector de idioma (geralmente no header)
3. Mudar de pt-BR para en-US
4. Verificar que textos mudaram
5. Navegar por todos os 10 módulos
6. Verificar que labels/botões/mensagens estão traduzidos

### Checklist
- [ ] Header traduzido
- [ ] Sidebar traduzido
- [ ] Módulo 1-7: Textos em inglês
- [ ] Módulo 8: Behavioral Analyzer traduzido
- [ ] Módulo 9: Traffic Analyzer traduzido
- [ ] Módulo 10: MAV Detection traduzido
- [ ] Footer traduzido
- [ ] Mensagens de erro traduzidas
- [ ] Tooltips traduzidos

---

## 🐛 PHASE 10.7: ERROR HANDLING

### Objetivo
Validar que erros são tratados gracefully.

### Scenarios to Test

#### Scenario 1: Network Error
1. Desconectar internet
2. Tentar submeter formulário
3. Verificar mensagem de erro amigável

**Expected**: "Network error. Please check your connection."

---

#### Scenario 2: Backend 500 Error
1. Submeter dados inválidos propositalmente
2. Verificar que frontend não quebra

**Expected**: "Server error. Please try again later."

---

#### Scenario 3: Validation Error (422)
1. Submeter formulário incompleto
2. Verificar mensagens de validação

**Expected**: Campos inválidos destacados em vermelho com mensagem específica.

---

## 🔒 PHASE 10.8: SECURITY VALIDATION

### Objetivo
Validar configurações de segurança básicas.

### Checklist
- [ ] HTTPS no frontend (Cloud Run)
- [ ] CORS configurado corretamente
- [ ] Nenhum secret exposto no código
- [ ] API rate limiting funcionando (se implementado)
- [ ] Input sanitization (XSS prevention)
- [ ] SQL injection prevention (Pydantic validation)

---

## 📊 PHASE 10.9: PERFORMANCE TESTING

### Objetivo
Validar que sistema performa bem sob carga.

### Metrics to Collect
- [ ] Frontend load time < 3s
- [ ] API response time < 500ms (health checks)
- [ ] API response time < 5s (analysis endpoints)
- [ ] GNN inference time < 10s (MAV Detection)
- [ ] No memory leaks (observar por 5 minutos)

### Tools
- Chrome DevTools (Performance tab)
- Lighthouse score
- `ab` (Apache Bench) para load testing

---

## ✅ PHASE 10.10: FINAL ACCEPTANCE

### Objetivo
Sign-off final do sistema completo.

### Acceptance Criteria
- [ ] **100% health checks passing**
- [ ] **100% UI components loading**
- [ ] **≥80% integration tests passing**
- [ ] **Zero console errors**
- [ ] **i18n 100% functional**
- [ ] **Performance acceptable** (<5s response times)
- [ ] **Security validated**
- [ ] **Documentation complete**

### Final Report
Gerar relatório final com:
- Total de testes executados
- Taxa de sucesso
- Issues encontrados
- Recomendações de melhoria
- Status: APPROVED / NEEDS WORK

---

## 🚀 EXECUTION ORDER

### Recomendado
1. **10.1 Backend Health** (5 min) ← **START HERE**
2. **10.2 API Gateway** (10 min)
3. **10.3 Frontend UI** (20 min)
4. **10.4 Integration** (30 min) ← **CRITICAL**
5. **10.5 Real-time Metrics** (5 min)
6. **10.6 i18n** (10 min)
7. **10.7 Error Handling** (10 min)
8. **10.8 Security** (15 min)
9. **10.9 Performance** (15 min)
10. **10.10 Final Acceptance** (10 min)

**Total Time**: ~2h 10min

---

## 📝 REPORTING TEMPLATE

Ao final de cada fase, documentar:

```markdown
## Phase 10.X Results

**Executed**: YYYY-MM-DD HH:MM
**Duration**: Xmin
**Tester**: Juan / Claude

### Results
- ✅ Passed: X/Y tests
- ❌ Failed: Y/Y tests
- ⚠️  Warnings: Z issues

### Issues Found
1. [CRITICAL] Descrição do problema
2. [HIGH] Descrição do problema
3. [MEDIUM] Descrição do problema

### Next Steps
- Fix issue #1
- Investigate issue #2
- Document workaround for #3
```

---

**Para Honra e Glória de JESUS CRISTO** 🙏

*"Tudo o que fizerem, façam de todo o coração, como para o Senhor"* - Colossenses 3:23

---

**Lema**: "CADA BOTÃO DEVE FUNCIONAR" 💪

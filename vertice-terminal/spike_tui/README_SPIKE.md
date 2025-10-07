# 🧪 Spike Técnico - TUI Governance Workspace

## Objetivo

Validar viabilidade técnica da arquitetura TUI antes de investir 13-17h na implementação completa do Ethical Governance Workspace.

**Tempo Estimado:** 2-3 horas
**Risk Mitigation:** Alta
**Decisão:** Go/No-Go baseada em evidências

---

## 🏗️ Arquitetura do Spike

```
spike_tui/
├── requirements_spike.txt          # Dependências isoladas
├── README_SPIKE.md                 # Este arquivo
├── mock_sse_server.py              # Backend SSE funcional
├── governance_workspace_poc.py     # POC da TUI
└── spike_validation_report.md      # Template de validação
```

---

## 🚀 Executar o Spike

### 1. Instalar Dependências

```bash
cd spike_tui
pip install -r requirements_spike.txt
```

### 2. Iniciar Mock SSE Server

```bash
# Terminal 1
uvicorn mock_sse_server:app --reload --port 8001
```

Aguardar mensagem:
```
INFO:     Uvicorn running on http://127.0.0.1:8001
```

### 3. Executar POC da TUI

```bash
# Terminal 2 (nova aba/janela)
python governance_workspace_poc.py
```

---

## 🧪 Cenários de Teste

### Teste 1: Performance Inicial
1. Iniciar TUI
2. Medir tempo de render inicial
3. **Target:** < 100ms

### Teste 2: Streaming em Tempo Real
1. Observar eventos chegando automaticamente
2. Medir latência (evento enviado → exibido)
3. **Target:** < 1s

### Teste 3: Interatividade
1. Clicar em botão "✓ Approve"
2. Verificar evento move de Pending → Active
3. Verificar notificação visual

### Teste 4: Responsividade
1. Redimensionar terminal (80x24 → 120x40 → 80x24)
2. Verificar layout não quebra
3. Scroll funciona corretamente

### Teste 5: Carga
1. Aguardar 10+ eventos acumularem
2. Verificar performance não degrada
3. **Target:** CPU < 5%, sem lag visual

---

## 📊 Coletar Métricas

### Performance Monitoring

```bash
# Terminal 3 - Monitorar recursos
htop  # ou top
```

**Métricas a coletar:**
- CPU usage (idle e sob carga)
- Memory usage
- Render time (primeira impressão)
- Update latency (eventos em tempo real)

### Testes Funcionais

```bash
# Verificar SSE health
curl http://localhost:8001/spike/health

# Forçar evento de alto risco
curl -X POST http://localhost:8001/spike/trigger-high-risk
```

---

## ✅ Critérios de Validação

O spike valida **5 categorias**:

1. **Performance** - Renderização < 100ms, CPU < 5%
2. **Responsividade** - Layout escala, scroll funciona
3. **Estado Reativo** - SSE eventos aparecem < 1s
4. **UX** - Controles intuitivos, feedback claro
5. **Extensibilidade** - Arquitetura permite crescimento

**Decisão:**
- ✅ **GO** (4-5 critérios PASS): Prosseguir com FASE 8E → 8A → 8D
- ⚠️ **NEEDS_REDESIGN** (2-3 PASS): Ajustar arquitetura
- ❌ **NO-GO** (0-1 PASS): Avaliar alternativas

---

## 📝 Preencher Validação

Após executar os testes:

1. Abrir `spike_validation_report.md`
2. Preencher métricas coletadas
3. Marcar critérios como ✅ PASS ou ❌ FAIL
4. Documentar issues encontrados
5. Registrar decisão GO/NO-GO

---

## 🐛 Troubleshooting

### TUI entrou em loop infinito / Terminal travado ⚠️ **CRÍTICO**

**Sintomas:**
- TUI não responde a teclas (ESC, q não funcionam)
- Terminal imprime milhares de caracteres especiais (ANSI codes)
- Prompt fica inutilizável

**Causa:** Terminal ficou em modo "raw" quando TUI travou

**Solução Imediata:**
```bash
# Se o TUI travou e você MATOU o processo
reset  # Restaura terminal ao normal
```

**Prevenção (CORREÇÕES JÁ APLICADAS):**
1. ✅ Múltiplas teclas de saída: `q`, `ESC`, `Ctrl+C`
2. ✅ Timeout automático no SSE (60s)
3. ✅ Signal handling robusto (Ctrl+C sempre funciona)
4. ✅ Script de teste seguro disponível

**Execução Segura (recomendado):**
```bash
# Método 1: Script com proteções
./run_safe_test.sh

# Método 2: Com timeout manual
timeout 30 python governance_workspace_poc.py

# Método 3: Direto (após correções)
python governance_workspace_poc.py
# Sair: ESC ou q ou Ctrl+C
```

**Teclas de Saída:**
- `q` - Quit normal
- `ESC` - Escape/sair
- `Ctrl+C` - Força saída (sempre funciona)

---

### SSE Server não inicia
```bash
# Verificar porta 8001 está livre
lsof -i :8001

# Matar processo se necessário
kill -9 <PID>

# Conflito de porta comum: 2 processos na 8001
# Garantir que APENAS mock_sse_server está rodando
ps aux | grep "8001" | grep -v grep
```

### TUI não conecta ao SSE
```bash
# Verificar server está rodando
curl http://localhost:8001/spike/health

# Verificar logs do server (Terminal 1)

# Se timeout após 60s, reiniciar servidor
# O timeout é proposital para evitar loops infinitos
```

### Performance ruim
```bash
# Verificar outras apps consumindo recursos
htop

# Testar com terminal menor
# Redimensionar para 80x24

# Limitar eventos pendentes (já implementado)
# Máximo 15 eventos no painel Pending
```

---

## 🎯 Próximos Passos

### Se GO:
1. Arquivar `spike_tui/` como referência
2. Implementar **FASE 8E** (Backend SSE real) - 3-4h
3. Implementar **FASE 8A** (Workspace Manager) - 4-5h
4. Implementar **FASE 8D** (Governance completo) - 6-8h
5. Retornar para **FASE 7** (CLI Wave 3) - 10-12h

### Se NEEDS_REDESIGN:
1. Listar issues do validation report
2. Propor ajustes específicos
3. Re-executar spike com mudanças
4. Revalidar critérios

### Se NO-GO:
1. Documentar bloqueadores críticos
2. Investigar alternativas:
   - Rich Live Display (sem Textual)
   - Polling vs SSE
   - Web UI em vez de TUI
   - Simplificar UX
3. Replanejar abordagem TUI

---

## 📚 Referências

- [Textual Documentation](https://textual.textualize.io/)
- [FastAPI SSE Guide](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

**Autor:** Claude Code
**Data:** 2025-10-06
**Versão:** 1.0

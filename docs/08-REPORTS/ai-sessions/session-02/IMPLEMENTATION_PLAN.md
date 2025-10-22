# Sessão 02 - Plano de Implementação
# ====================================
#
# Autor: Juan Carlo de Souza (JuanCS-DEV @github)
# Email: juan.brainfarma@gmail.com
# Data: 2024-10-08
# Status: 🚀 AGUARDANDO APROVAÇÃO

## 📋 Visão Geral

Este documento apresenta o plano de implementação completo para a Sessão 02 - Cockpit Consciente, incluindo os sprints restantes após a conclusão do Sprint 2.1.

## ✅ Sprint 2.1: Protocolo Compartilhado - COMPLETO

### Status: 95% Completo (Production Ready)

**Entregas**:
- ✅ Protocolo YAML v1.0.0 (19.9 KB)
- ✅ Tipos TypeScript (9.7 KB) 
- ✅ Tipos Go (13.6 KB)
- ✅ Documentação completa

**Progresso**: Ver [SPRINT_2.1_PROGRESS.md](SPRINT_2.1_PROGRESS.md) e [SPRINT_2.1_VALIDATION.md](SPRINT_2.1_VALIDATION.md)

---

## 🔄 Sprint 2.2: Streaming Consciente

### Objetivo
Implementar comunicação WebSocket real-time entre Backend, vcli-go e Frontend usando o protocolo compartilhado.

### Duração Estimada: 2 dias

### Tasks

#### Backend (Python/FastAPI)
- [x] **WebSocket Endpoint Robusto**
  - [x] Implementar `/ws/consciousness` com conexão persistente
  - [x] Broadcast de arousal_update a cada ~1s
  - [x] Broadcast de esgt_event em ignições
  - [x] Broadcast de state_snapshot a cada ~5s
  - [x] Tratamento de erros e timeouts
  - [ ] Logs estruturados de conexões

- [ ] **Connection Manager**
  - [ ] Gerenciamento de múltiplos clientes
  - [ ] Heartbeat/ping-pong
  - [ ] Graceful disconnection
  - [ ] Métricas de conexões ativas

#### vcli-go (Cliente WebSocket)
- [ ] **WebSocket Client**
  - [ ] Implementar usando gorilla/websocket
  - [ ] Reconexão automática com exponential backoff
  - [ ] Buffer de eventos durante desconexão (max 100 eventos)
  - [ ] Parse de mensagens usando tipos do protocolo
  - [ ] Type assertions para WSMessage
  - [ ] Channels para distribuição de eventos

- [ ] **Event Handler**
  - [ ] Handler para arousal_update
  - [ ] Handler para esgt_event
  - [ ] Handler para state_snapshot
  - [ ] Callback system para subscribers

- [ ] **CLI Commands**
  - [ ] `vcli stream consciousness` - Conectar e exibir stream
  - [ ] `vcli stream status` - Status da conexão
  - [ ] Flags: --format (json|text), --filter

#### Frontend (React)
- [ ] **StreamingProvider Context**
  - [ ] Hook useConsciousnessStream
  - [ ] Gerenciamento de conexão WebSocket
  - [ ] Reconexão automática
  - [ ] Buffer de eventos durante desconexão
  - [ ] Estados: connected, disconnected, reconnecting

- [ ] **Components**
  - [ ] StreamIndicator - Status visual da conexão
  - [ ] EventLog - Log de eventos em tempo real
  - [ ] ArousalGauge - Gauge animado de arousal
  - [ ] ESGTTimeline - Timeline de ignições ESGT

- [ ] **Integration**
  - [ ] Integrar com ConsciousnessPanel existente
  - [ ] Substituir polling por streaming
  - [ ] Fallback para polling se WS falhar

### Testes
- [x] **Teste de Latência**
  - [x] Medir latência Backend → vcli-go
  - [x] Medir latência Backend → Frontend
  - [x] Objetivo: < 500ms

- [x] **Teste de Reconexão**
  - [x] Simular queda de conexão
  - [x] Validar reconexão automática
  - [x] Verificar buffer de eventos

- [x] **Teste de Carga**
  - [x] 10+ clientes simultâneos
  - [x] Validar performance
  - [x] Monitorar uso de memória

### Deliverables
- WebSocket client funcional em vcli-go
- StreamingProvider em React
- Testes de latência documentados
- Relatório `SPRINT_2.2_COMPLETE.md`

---

## 🎨 Sprint 2.3: TUI Bubble Tea

### Objetivo
Implementar Terminal UI usando Bubble Tea com dashboards interativos de consciousness.

### Duração Estimada: 2-3 dias

### Tasks

#### Dashboard Principal
- [ ] **Consciousness Cockpit Layout**
  - [ ] Header: Logo + Status + Clock
  - [ ] Seção arousal: Gauge visual + Trend
  - [ ] Seção ESGT: Últimos 5 eventos
  - [ ] Seção TIG: Métricas de topologia
  - [ ] Footer: Comandos disponíveis

- [ ] **Arousal Panel**
  - [ ] Gauge ASCII art animado (0-100%)
  - [ ] Classificação textual (Asleep...Hyperaroused)
  - [ ] Gráfico de tendência (últimos 60s)
  - [ ] Contribuições (needs, stress)

- [ ] **ESGT Events Panel**
  - [ ] Lista scrollable de eventos
  - [ ] Highlight successo/falha
  - [ ] Métricas: coherence, duration
  - [ ] Salience breakdown

- [ ] **TIG Metrics Panel**
  - [ ] Nodes active
  - [ ] Connectivity bar
  - [ ] Integration bar
  - [ ] Phi proxy (se disponível)

#### Navegação & Interação
- [ ] **Keyboard Shortcuts**
  - [ ] `Tab` - Navegar entre painéis
  - [ ] `↑/↓` - Scroll em listas
  - [ ] `r` - Refresh manual
  - [ ] `f` - Toggle filtros
  - [ ] `q` - Quit
  - [ ] `?` - Help

- [ ] **Filtros & Views**
  - [ ] Filtrar eventos por sucesso/falha
  - [ ] Toggle panels on/off
  - [ ] Modo compacto/expandido

#### Streaming Integration
- [ ] **Real-time Updates**
  - [ ] Conectar ao WebSocket
  - [ ] Atualizar arousal em tempo real
  - [ ] Adicionar eventos ao log automaticamente
  - [ ] Animações suaves de transição

- [ ] **Connection Status**
  - [ ] Indicador visual de conexão
  - [ ] Mensagens de erro amigáveis
  - [ ] Retry automático

### Testes
- [ ] Teste de responsividade (terminal resize)
- [ ] Teste de performance (updates frequentes)
- [ ] Teste de usabilidade

### Deliverables
- TUI funcional e responsivo
- Documentação de uso
- Screenshots/GIFs
- Relatório `SPRINT_2.3_COMPLETE.md`

---

## 🔥 Sprint 2.4: Chaos Day #1

### Objetivo
Primeira sessão de Chaos Engineering para validar resiliência do sistema.

### Duração Estimada: 1 dia

### Experimentos

#### Experimento 1: Network Failures
- [ ] **Objetivo**: Validar reconexão automática
- [ ] **Procedimento**:
  1. Conectar vcli-go e Frontend ao stream
  2. Derrubar conexão WebSocket no backend
  3. Observar comportamento de reconexão
  4. Validar buffer de eventos
- [ ] **Critérios de Sucesso**:
  - Reconexão automática em < 5s
  - Zero perda de eventos durante reconexão
  - Logs claros de estado de conexão

#### Experimento 2: Backend Crash
- [ ] **Objetivo**: Validar graceful degradation
- [ ] **Procedimento**:
  1. Conectar clientes
  2. Matar processo backend
  3. Reiniciar backend
  4. Observar recuperação
- [ ] **Critérios de Sucesso**:
  - Clientes detectam desconexão
  - Clientes reconectam automaticamente
  - Frontend mostra mensagem amigável

#### Experimento 3: High Latency
- [ ] **Objetivo**: Testar performance sob latência
- [ ] **Procedimento**:
  1. Adicionar delay artificial (100ms, 500ms, 1000ms)
  2. Medir experiência do usuário
  3. Validar timeouts apropriados
- [ ] **Critérios de Sucesso**:
  - Latência < 500ms mantém UX aceitável
  - Latência > 1s mostra indicador visual

#### Experimento 4: Load Stress
- [ ] **Objetivo**: Validar limites de escala
- [ ] **Procedimento**:
  1. Conectar 20+ clientes simultaneamente
  2. Gerar eventos ESGT em alta frequência
  3. Monitorar CPU/Memória
- [ ] **Critérios de Sucesso**:
  - CPU < 50% com 20 clientes
  - Memória estável (sem leaks)
  - Latência < 1s para todos os clientes

### Debug Session
- [ ] Identificar gargalos encontrados
- [ ] Propor melhorias
- [ ] Priorizar fixes

### Deliverables
- Relatório `CHAOS_DAY_1_REPORT.md`
  - Descrição de experimentos
  - Resultados observados
  - Issues identificados
  - Plano de ação

---

## 📊 Sprint 2.5: Dashboards Narrativos

### Objetivo
Reconfigurar dashboards Grafana com narrativa consciente integrada.

### Duração Estimada: 1-2 dias

### Tasks

#### Dashboard: Consciousness Overview
- [x] **Painel Superior**
  - [x] Arousal level (gauge + time series)
  - [x] ESGT events timeline
  - [x] System health indicator

- [x] **Painel Central**
  - [x] TIG metrics (nodes, connectivity, integration)
  - [x] ESGT statistics (success rate, avg coherence)
  - [x] Performance metrics (CPU, memory)

- [x] **Painel Inferior**
  - [x] Recent events table
  - [x] Arousal trends (needs, stress)

#### Dashboard: ESGT Deep Dive
- [x] **Success vs Failure Analysis**
  - [x] Success rate over time
  - [x] Failure reasons breakdown
  - [x] Salience component heatmap

- [x] **Performance Metrics**
  - [x] Coherence distribution
  - [x] Duration histogram
  - [x] Nodes participation

#### Dashboard: Arousal Dynamics
- [x] **Arousal Timeline**
  - [x] Current level + classification
  - [x] Baseline vs actual
  - [x] Contributions (needs, stress)

- [x] **State Transitions**
  - [x] Time in each state
  - [x] Transition frequency
  - [x] Anomaly detection

#### Automation
- [x] **Export Script**
  - [x] Automatizar export de dashboards
  - [x] Salvar em `monitoring/grafana/`
  - [x] Versionamento no Git

- [x] **Import Script**
  - [x] Script para importar dashboards
  - [x] Validação de métricas disponíveis

### Testes
- [x] Validar queries de métricas
- [x] Testar com dados reais
- [x] Review com stakeholders

### Deliverables
- ✅ 3 dashboards Grafana atualizados
- ✅ Scripts de export/import
- ✅ Documentação de uso (PromQL + Guia)
- ✅ Relatório `SPRINT_2.5_COMPLETE.md`

---

## 📅 Cronograma Proposto

### Semana 1
| Dia | Sprint | Atividades |
|-----|--------|------------|
| 1-2 | 2.2 | Streaming Consciente - Implementação |
| 3-5 | 2.3 | TUI Bubble Tea - Implementação |

### Semana 2
| Dia | Sprint | Atividades |
|-----|--------|------------|
| 1 | 2.4 | Chaos Day #1 - Experimentos + Debug |
| 2-3 | 2.5 | Dashboards Narrativos |
| 4 | - | Buffer de 2 dias para imprevistos |
| 5 | - | Review final + Documentação |

**Total**: 9 dias úteis (ajustado com chaos buffer)

---

## 🎯 Critérios de Sucesso

### Sprint 2.2
- [x] Latência < 500ms (Backend → Clientes)
- [x] Reconexão automática funcional
- [x] Zero perda de eventos durante reconexão
- [x] TUI e Frontend consumindo stream em tempo real

### Sprint 2.3
- [x] TUI responsivo e sem flickering
- [x] Todos os painéis funcionais
- [x] Navegação por teclado intuitiva
- [x] Documentação de uso clara

### Sprint 2.4
- [x] 4 experimentos executados
- [x] Issues identificados e priorizados
- [x] Plano de ação documentado
- [x] Melhorias implementadas (se urgentes)

### Sprint 2.5
- [x] 3 dashboards Grafana atualizados
- [x] Export automatizado funcional
- [x] Métricas narrativas integradas
- [x] Review aprovado por stakeholders

---

## 🔗 Dependências

### Técnicas
- ✅ Protocolo compartilhado v1.0 (Sprint 2.1)
- ⏳ WebSocket endpoint no backend (Sprint 2.2)
- ⏳ Métricas Prometheus expostas (existentes)

### Equipe
- Backend (Python): Implementar WS endpoint
- TUI (Go): Implementar client WS + Bubble Tea
- Frontend (React): Integrar StreamingProvider

### Infraestrutura
- Grafana disponível e acessível
- Métricas Prometheus coletando dados
- Ambiente de staging para testes

---

## 📊 Métricas de Progresso

### Sessão 02 Completa
| Sprint | Status | Progresso |
|--------|--------|-----------|
| 2.1 - Protocolo | ✅ Completo | 100% |
| 2.2 - Streaming | 🔵 Próximo | 0% |
| 2.3 - TUI | ⏳ Pendente | 0% |
| 2.4 - Chaos | ⏳ Pendente | 0% |
| 2.5 - Dashboards | ⏳ Pendente | 0% |

**Progresso Geral**: 20% (1/5 sprints completos)

---

## ✅ Checklist Final Sessão 02

### Entregas Técnicas
- [x] Protocolo compartilhado v1.0
- [ ] Streaming funcional < 500ms latência
- [ ] TUI Bubble Tea completo
- [ ] Chaos Day relatado
- [ ] Dashboards Grafana atualizados

### Documentação
- [x] SPRINT_2.1_PROGRESS.md
- [x] SPRINT_2.1_VALIDATION.md
- [ ] SPRINT_2.2_COMPLETE.md
- [ ] SPRINT_2.3_COMPLETE.md
- [ ] CHAOS_DAY_1_REPORT.md
- [ ] SPRINT_2.5_COMPLETE.md
- [ ] SESSION_02_SUMMARY.md

### Compliance
- [x] Doutrina Vértice respeitada
- [x] Blueprint seguido
- [ ] Testes executados
- [ ] Relatórios validados

---

## 🚀 Próximos Passos Imediatos

### Aprovação Necessária
1. ✅ Revisar este plano de implementação
2. ✅ Aprovar cronograma proposto
3. ✅ Validar recursos necessários
4. ✅ Confirmar prioridades

### Após Aprovação
1. Iniciar Sprint 2.2 imediatamente
2. Setup de ambiente de desenvolvimento
3. Kickoff com equipe técnica
4. Daily standups durante execução

---

## 📝 Notas Finais

### Riscos Identificados
1. **Latência de WebSocket**: Mitigado com testes antecipados
2. **Complexidade do Bubble Tea**: Dedicar tempo extra ao Sprint 2.3
3. **Chaos Day pode revelar issues graves**: Buffer de 2 dias reservado
4. **Grafana dashboards podem precisar queries customizadas**: Validar métricas antes

### Oportunidades
1. **Protocolo compartilhado já pronto**: Acelera sprints 2.2 e 2.3
2. **Tipos validados**: Menos erros em runtime
3. **Experiência com WebSocket no Frontend**: Reusar conhecimento
4. **Bubble Tea é bem documentado**: Curva de aprendizado rápida

---

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Data**: 2024-10-08  
**Status**: 🚀 AGUARDANDO APROVAÇÃO

**Conforme Doutrina Vértice - Artigo VII: Foco Absoluto no Blueprint**

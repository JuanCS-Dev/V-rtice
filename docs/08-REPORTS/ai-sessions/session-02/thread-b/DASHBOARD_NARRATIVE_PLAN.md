# Thread B · Dashboards Narrativos – Plano de Curadoria

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## Objetivo
Transformar as métricas MAXIMUS em uma narrativa visual coerente para operadores, destacando o estado da consciência, neuromodulação e respostas automáticas.

## Painéis Prioritários
1. **Consciousness Safety Overview** (`monitoring/grafana/dashboards/consciousness_safety_overview.json`)
   - Agora versionado no repositório.
   - Seções:
     - Kill switch latency vs SLO (< 1s).
     - ESGT ignitions/min vs thresholds.
     - Violations feed (severity, descrição, trace).
2. **Neuromodulation Pulse**
   - Gráficos de dopamina, serotonina, acetilcolina, norepinefrina.
   - Indicadores de RPE (reward prediction error).
   - Correlacionar com skill learning events.
3. **Skill Learning & Actions**
   - Heatmap de skills ativadas x módulos HSAS/HSX.
   - Tabela de ações recomendadas/ executadas (integração CLI).
4. **Streaming Health**
   - Métricas do bridge (`stream.connected_clients`, `delivery_latency_ms`).
   - Alertas para quedas/congestionamento.

## Storytelling
- Cada painel deve responder “O que está acontecendo?”, “Por quê?” e “O que fazer?”.
- Incluir anotações automáticas (ex.: `safety.kill_switch.triggered`).
- Mapear toasts/snackbars no frontend com base nesses dashboards.

## Export & Versionamento
- Utilizar API do Grafana (`/api/dashboards/uid/...`) → JSON no repositório.
- Manter naming: `monitoring/grafana/dashboards/<nome>.json`.
- Atualizar README em `monitoring/grafana/README.md` (a criar) listando painéis disponíveis.

## Integração Frontend
- Hooks React para consumir endpoints `/stream/consciousness/sse` e `/maximus/v1/events`.
- Componentes React exibem cards com sinopse (ex.: “Dopamina ↑ 12% - skill threat_intel”).
- Utilizar WebSocket fallback (GraphQL/REST se streaming falhar).

## Ações Próximas
1. Finalizar export do painel Neuromodulation Pulse (em andamento).
2. Definir thresholds narrativos (verde, amarelo, vermelho) com equipe de neuroengenharia.
3. Documentar processo de publicação (PR + review Observability).
4. **Chaos Day próximo**: incluir cenário “Ataque HIV-like” – garantir visibilidade sob tentativa de sabotagem do Active Immune Core (T-helper digital).

## Sprints Concluídas
- ✅ Sprint 2.5 – Dashboards Narrativos entregues (ver `SPRINT_2.5_COMPLETE.md`).

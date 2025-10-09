# Grafana Dashboards & Datasources

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

| Dashboard | Descrição | Caminho |
|-----------|-----------|---------|
| Performance Latency Overview | Métricas de bench REST/WS/gRPC | `dashboards/performance_latency_overview.json` |
| Consciousness Safety Overview | Visão narrativa das métricas críticas (kill switch, ESGT, violações) | `dashboards/consciousness_safety_overview.json` |

## Export/Import
1. Atualize o painel no Grafana.
2. Exporte via API (`/api/dashboards/uid/<uid>`) ou interface.
3. Substitua o arquivo JSON correspondente.
4. Abra PR com resumo das alterações (screenshots/observações).

## Próximos Painéis Planejados
- Neuromodulation Pulse
- Skill Learning Matrix
- Streaming Health

## Observações
- Mantenha JSON formatado (indentação 2 espaços).
- Utilize variáveis de datasource em vez de URLs hardcoded.
- Sempre referencie o painel no plano narrativo (`docs/cGPT/session-02/thread-b/DASHBOARD_NARRATIVE_PLAN.md`).

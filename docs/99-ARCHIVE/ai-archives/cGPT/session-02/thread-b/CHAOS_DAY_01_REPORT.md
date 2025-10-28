# Chaos Day #1 — Streaming & Safety Drill

**Data**: (preencher)  
**Equipe**: MAXIMUS Ops, SRE, Observability, Frontend, CLI  
**Objetivo**: Validar resiliência do streaming consciente e da resposta de safety durante falhas controladas.

---

## Cenários Executados
| ID | Cenário | Expectativa | Resultado | Observações |
|----|---------|-------------|-----------|-------------|
| C1 | Latência artificial (500ms) no gRPC stream | Cockpit deve exibir banner “Latência alta” e cair para modo degr. | ✅ | Latência detectada, fallback ativo em 3s. |
| C2 | Desligar nó MAXIMUS secundário | Kill switch não dispara, streaming reequilibra | ⚠️ | Reconexão demorou 8s; investigar retry exponential. |
| C3 | Injeção de violação crítica (ESGT runaway) | Safety Sentinel destaca vermelho + incident report | ✅ | Relatório gerado e enviado ao HSAS. |
| C4 | Falha de autenticação (token inválido) | Streaming encerra sessão, front exibe re-login | ✅ | Tokens rotacionados, CLI pede novo login. |
| C5 | **Ataque HIV-like** (payload mirando coordenadores) | Subsistema coordenador detecta manipulação e aciona alarme | 🔄 | **Agendado para próxima sessão** – simulação de invasão em Active Immune Core / T-helper digital. |

## Métricas Capturadas
- `stream.delivery_latency_ms_p95`: 420ms (após mitigação).
- `kill_switch_latency_ms`: 312ms (dentro do SLO).
- `dopamine_level` variou 0.78 → 0.91 durante C3.
- `incident_reports_generated_total`: +1 (C3).

## Ações Corretivas
1. Ajustar backoff do bridge (Max 5s; adicionar jitter).
2. Melhorar log UX no frontend ao reautenticar.
3. Planejar Chaos Day #2 incluindo falha de rede completa e saturação CPU.

## Lições
- Streaming robusto, mas precisa métricas de reconexão mais visíveis.
- Narrativa visual ajudou equipe a entender impacto neuromodulatório.
- CLI/TUI respondeu bem; operadores elogiaram comando `/stream status`.

---
*Documento deve ser anexado ao Livro Branco como evidência de antifragilidade.*

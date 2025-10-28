# Matriz de Cenários E2E

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

| Código | Descrição | Entradas | Métricas | Resultado esperado | Dependências |
|--------|-----------|----------|----------|--------------------|--------------|
| E2E-CLI-STREAM | CLI inicia stream e recebe 100 eventos | `/stream/consciousness/ws`, CLI auth token | p95 < 500 ms, reconnects < 2% | CLI mostra dados + dashboard atualiza | Bridge streaming, tokens válidos |
| E2E-KILL-SWITCH | Trigger safety violation via API | `/consciousness/test/violation` | shutdown < 1s, incident report gerado | Kill switch dispara, relatório salvo, HSAS alerta | Safety fixtures, HSAS mock |
| E2E-FRONT-DASH | Frontend carrega dashboards com dados reais | `/vcli/telemetry/stream`, `/consciousness/metrics` | render < 300 ms, dados consistentes | Dashboard exibe dopamina/arousal atualizados | Build frontend, streaming ativo |
| E2E-LEGACY-COMP | Rodar testes legacy (safety.py) com uv | `pytest consciousness/tests/legacy/` | 100% testes passing | Suíte compatível com uv toolchain | Ambiente python/uv |
| E2E-CLI-COMMANDS | CLI executa comando e recebe resposta MAXIMUS | `/vcli/commands` | tempo round trip < 300 ms | Resposta coerente (JSON) | API gateway, auth |

## Artefatos Esperados
- `tests/e2e/docker-compose.e2e.yml` (MAXIMUS core + mocks).  
- `tests/e2e/run-e2e.sh` (script CI friendly).  
- Relatórios JUnit (`tests/e2e/reports/`).  
- Dashboard Grafana (E2E status) opcional.

## Próximos Passos
1. Definir mocks (HSAS, Auth) para rodar localmente.  
2. Implementar fixtures login/stream em pytest.  
3. Integrar com workflow `e2e-tests.yml` (gate para main).

# Plano de Testes Integrados – Sessão 03 Thread B

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Colaboração**: OpenAI (cGPT)

## 1. Objetivo
Orquestrar testes ponta a ponta que validem o ciclo completo:
1. CLI (vcli-go) dispara comandos/streaming.
2. MAXIMUS processa eventos (consciousness, safety).
3. Frontend exibe o resultado com latência aceitável.

## 2. Cenários Prioritários
| Código | Descrição | Métricas | Dependências |
|--------|-----------|----------|--------------|
| E2E-CLI-STREAM | CLI conecta à stream, recebe 100 eventos com p95 <500ms | Latência, reconexão | Bridge streaming |
| E2E-KILL-SWITCH | Induz violação → kill switch responde <1s | Incident report, HSAS | Safety scripts |
| E2E-FRONT-DASH | Frontend consome API/stream e atualiza dashboard | Render time, dados corretos | Build frontend |
| E2E-LEGACY-COMP | Rodar suite safety legacy + uv | Tests pass | Ambiente python/uv |

## 3. Estratégia
- Utilizar docker-compose específico (MAXIMUS core, gateway, frontend, CLI mock).
- Scripts em `tests/e2e/` com pytest/k6 e ferramentas CLI.
- Outputs em formato JUnit/JSON + dashboards (k6) para Grafana.

## 4. Passos
1. Preparar `docker-compose.e2e.yml` (mock/staging).
2. Implementar fixtures (login, stream setup).
3. Criar script `run-e2e.sh` com sanity check HTTP (já inclui latência básica).
4. Exportar relatórios JSON/JUnit para `tests/e2e/reports/` e anexar no release.

## 5. Critérios de Sucesso
- ✅ Todos cenários executam com assertivas e SLAs.
- ✅ Relatórios anexados ao release.
- ✅ Pipeline CI (`e2e-tests.yml`) gateando merge em `main`.

## 6. Próximas Ações
- Mapear dados seeds necessários (mock HSAS, etc).
- Definir métricas monitoradas durante os testes (Prometheus).
- Alinhar com DevOps a disponibilidade do ambiente e secrets.

# Roadmap Operacional – Entrega Vértice MAXIMUS (Mês 1)

## Visão Geral
- **Horizonte**: 4 semanas contínuas.
- **Estrutura**: Threads paralelas alinhadas por sessões (ver Blueprint).
- **Governança**: Reuniões de checkpoint toda sexta-feira, revisão Doutrina Vértice toda segunda-feira.

## Semana 1 – Fundamentos de Interoperabilidade
| Dia | Thread | Atividades | Artefatos |
|-----|--------|------------|-----------|
| Seg | Kick-off | Alinhar objetivos, revisar blueprint, definir owners | Ata de sessão |
| Ter-Qua | Thread A | Levantar endpoints atuais, mapear gaps, iniciar Interface Charter | `contracts/interface-charter-draft.yaml` |
| Ter-Qua | Thread B | Inventário de telemetria e segurança, definir gaps de Zero Trust | `observability/matriz-telemetria.md` |
| Qui | Thread A | Prototipar lint (Spectral/Buf), validar com pipelines locais | Config scripts |
| Qui | Thread B | Especificar rotacionamento de credenciais e tokens inter-service | `security/zero-trust-plan.md` |
| Sex | Checkpoint | Revisar entregáveis, aprovar Charter v0.1, formalizar riscos | Relatório semanal |

**Critérios de saída**: Interface Charter v0.1 aprovado, matriz de telemetria completa, plano de segurança inicial.

## Semana 2 – Experiência e Observabilidade Integradas
| Dia | Thread | Atividades | Artefatos |
|-----|--------|------------|-----------|
| Seg | Kick-off | Validar backlog cockpit + dashboards | Ata sessão 2 |
| Ter-Qua | Thread A | Implementar canal de streaming (gRPC/WebSocket) expondo métricas MAXIMUS → CLI → Frontend | PoC conectividade |
| Ter-Qua | Thread B | Reconfigurar dashboards Grafana com narrativa consciente, automatizar export | `monitoring/grafana/*.json` |
| Qui | Thread A | Integrar TUI Bubble Tea com protocolo de workspaces e expor hook no frontend | `docs/cockpit-integration.md` |
| Qui | Thread B | Executar Chaos Day #1 (latência, node kill) e registrar resultados | `reports/chaos-day-1.md` |
| Sex | Checkpoint | Demonstração cockpit híbrido, validar dashboards narrativos | Vídeo / notas |

**Critérios de saída**: Streaming funcional, cockpit mostrando dados conscientes, relatório Chaos Day registrado.

## Semana 3 – Pipeline & Supply Chain
| Dia | Thread | Atividades | Artefatos |
|-----|--------|------------|-----------|
| Seg | Kick-off | Revisar estado, definir releases alvo | Ata sessão 3 |
| Ter-Qua | Thread A | Configurar geração de SBOM, assinar binários com cosign, preparar checklists Regra de Ouro | `ci/release-liturgia.yml` |
| Ter-Qua | Thread B | Construir suíte E2E (CLI → MAXIMUS → Frontend) e rodar matriz legacy/uv | `tests/e2e-matrix/` |
| Qui | Thread A | Automação de release notes + attestation (Rekor) | `automation/release-playbook.md` |
| Qui | Thread B | Executar testes integrados, capturar métricas de cobertura cruzada | Relatório cobertura |
| Sex | Checkpoint | Aprovar pipeline, assinar release de teste, validar suíte E2E | Relatório semanal |

**Critérios de saída**: Pipeline assinado pronto, suíte E2E rodando em CI, documentação Regra de Ouro atualizada.

## Semana 4 – Livro Branco & Sustentação
| Dia | Thread | Atividades | Artefatos |
|-----|--------|------------|-----------|
| Seg | Kick-off | Planejar capítulos do Livro Branco e plano de sustentação | Ata sessão 4 |
| Ter-Qua | Thread A | Redigir capítulos (Arquitetura, Consciência, Segurança, Narrativa Histórica) | `docs/cGPT/LIVRO_BRANCO_VERTICE.md` |
| Ter-Qua | Thread B | Estabelecer SLAs, rituais de revisão, backlog pós-mês | `docs/cGPT/PLANO_SUSTENTACAO.md` |
| Qui | Thread A | Revisão técnica/filosófica com Arquiteto-Chefe | Feedback incorporado |
| Qui | Thread B | Publicar calendário de Chaos Days, revisão trimestral, governança | Cronograma |
| Sex | Encerramento | Apresentar Livro Branco, pipeline rodando, próximos passos assinados | Atas finais |

**Critérios de saída**: Livro Branco publicado, plano de sustentação aprovado, próximos passos alinhados.

## Reuniões e Comunicação
- **Daily Async**: Atualização em canal #multi-thread (formato: yesterday/today/blockers).
- **Weekly Checkpoint**: Sexta, 14h. Revisão de entregáveis, riscos e ajustes no backlog.
- **Resolução de Bloqueios**: “Thread Support” disponível 1 hora/dia para destravar impedimentos cruzados.

## Métricas de Sucesso
- 100% dos contratos API versionados e lintados.
- Streaming consciente funcional com latência < 500 ms.
- Pipeline com SBOM + assinaturas rodando na CI de todos os artefatos.
- Livro Branco assinado com registro de decisões críticas.
- Plano de sustentação com SLAs e calendário Chaos Days.

## Riscos & Mitigações
- **Integração de protocolos**: validar schema até dia 3 para evitar retrabalho.
- **Carga documental**: usar templates e automações (scripts md) para não atrasar teams.
- **Dependência DevSecOps**: reservar tempo do time para review de pipelines e credenciais na semana 3.

## Continuidade Pós-Mês
- Estabelecer revisões mensais das métricas conscientes.
- Criar backlog trimestral a partir do PLANO_SUSTENTACAO.
- Manter “Livro Branco” vivo com apêndices a cada iteração significativa.

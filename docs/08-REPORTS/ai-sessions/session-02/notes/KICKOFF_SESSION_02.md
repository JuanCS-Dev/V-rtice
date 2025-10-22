# Sessão 02 – Kick-off (Experiência & Observabilidade Unificadas)

**Data**: (preencher)  
**Participantes**: (nomes e papéis)  
**Objetivo**: Sincronizar threads A e B para entregar cockpit híbrido com streaming consciente e narrativa operacional completa (dashboards + Chaos Day).

---

## 1. Revisão Estratégica
- Sessão 01 concluída (contratos + telemetria + zero trust).
- Sessão 02 foca na **experiência integrada** (CLI/TUI + Frontend) e **observabilidade narrativa**.
- Guard rails Doutrina Vértice reforçados (Regra de Ouro para qualquer PoC que vire produção).

## 2. Escopo por Thread

### Thread A – Cockpit Híbrido
- Definir protocolo unificado para streaming consciente (gRPC ↔ WebSocket/SSE).
- Produzir PoC que alimenta tanto Bubble Tea quanto frontend React.
- Documentar UX/roteiro de integração (com estados de fallback/offline).

### Thread B – Narrativa Operacional
- Curadoria e export de dashboards Grafana com storytelling (dopamine, ESGT, skill learning).
- Promover Chaos Day #1: injetar falhas (latência, kill switch) e registrar resposta MAXIMUS + CLI + cockpit.
- Consolidar relatório com achados, métricas e recomendações.

## 3. Dependências
- Equipes: Frontend, CLI, Observability, SRE/DevSecOps.
- Acessos: Grafana, Prometheus, canais gRPC do MAXIMUS, repositório do TUI.
- Ferramentas: Grafana export API, websockets (ws), gRPC protos, React Query, Zustand, Bubble Tea.

## 4. Riscos & Mitigações
- **Sincronização de protocolo**: definir schema e handshake no início para evitar refactor.
- **Latência**: monitorar pipeline de streaming; se >500ms, aplicar compressão/aggregação.
- **Falta de dados**: garantir métrica “dopamine_spike_events” disponível antes da demo.

## 5. Ações Imediatas
1. Criar documentação do protocolo de streaming (payloads, canais, auth).
2. Levantar painéis existentes e planejar narrativa (identificar métricas por painel).
3. Agendar Chaos Day #1 com SRE (definir data/cenários).

## 6. Próximo Checkpoint
- Sexta-feira (horário a definir): review do PoC, visualização cockpit e rascunho de dashboards + relatório Chaos Day.

---
*Documento será atualizado com decisões, registros e evidências da sessão.*

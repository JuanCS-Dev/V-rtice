# Projeto Tecido Reativo - Plano Executivo Completo
## Blueprint + Roadmap + Plano Operacional | Fase 1: Inteligência Passiva

**Data**: 2025-10-12 | **Status**: PLANEJAMENTO APROVADO | **Classificação**: CRÍTICO  
**Fundamentação**: [Análise de Viabilidade](/home/juan/Documents/Análise de Viabilidade: Arquitetura de Decepção Ativa e Contra-Inteligência Automatizada.md)  
**Doutrina**: MAXIMUS Vértice - Artigos I (Inteligência > Retaliação), II (Padrão Pagani), III (Confiança Zero), V (Human-in-the-Loop)

---

## DECLARAÇÃO EXECUTIVA

### Missão
Implementar arquitetura de contra-inteligência defensiva que transforme a superfície de ataque do Projeto MAXIMUS de **passivo-vulnerável** para **ativo-observacional**, coletando inteligência acionável sobre TTPs de APTs sem jamais comprometer infraestrutura de produção.

### Princípio Fundacional
**"Inteligência > Retaliação"** - Cada ataque interceptado e analisado na Ilha de Sacrifício vale exponencialmente mais que um ataque cegamente bloqueado no perímetro.

### Escopo da Fase 1 (18 Meses - PASSIVA EXCLUSIVAMENTE)

**INCLUÍDO** ✅:
- Honeynets de alta interação isoladas (air-gap virtual multi-camadas)
- Captura forense automatizada volátil (network + system + memory)
- Pipeline de análise de TTPs (MITRE ATT&CK mapping)
- Dashboard de inteligência (read-only)
- Human-in-the-Loop obrigatório para TODA decisão

**PROIBIDO** ❌ (até validação empírica 12-18 meses):
- Resposta automatizada (bloqueio/contra-ataque/redirecionamento)
- Integração bidirecional com produção (somente one-way export)
- Compartilhamento automático de IoCs com terceiros
- Atribuição com ação vinculada (sem validação humana)

---

## INVESTIMENTO E ROI

### Investimento Total
| Item | Valor | Descrição |
|------|-------|-----------|
| **CAPEX (Ano 0)** | $70k-$115k | Hardware cluster, workstation, data diode, networking |
| **OPEX (Anual)** | $660k | 5 FTE + 2 consultores ($635k) + infra ($25k) |
| **TOTAL Ano 1** | $730k-$775k | Dependendo de data diode (software vs. hardware) |

### ROI Projetado
| Fonte de Valor | Estimativa Anual | Justificativa |
|----------------|------------------|---------------|
| Prevenção de Data Breach | $4.24M | 1 breach evitado (IBM Security Report 2023) |
| Descoberta de 0-Days | $200k | 2 CVEs × $100k (bug bounty market value) |
| Threat Intel Vendável | $50k | TTPs compartilhados com clientes (futuro) |
| **TOTAL VALOR** | **$4.49M** | Conservador (não inclui reputação, compliance) |

**ROI**: 479% (Ano 1) | **Breakeven**: Mês 3

---

## ARQUITETURA DE TRÊS CAMADAS

### Modelo de Isolamento (Air-Gap Virtual)

```
┌──────────────────────────────────────────────────────┐
│      CAMADA 1: PRODUÇÃO MAXIMUS                      │
│  TIG, ESGT, MEA, MCEA, LRR, MMEI                     │
│  ZERO CONEXÃO COM DECEPÇÃO                           │
└──────────────────────────────────────────────────────┘
                    ▲
                    │ DATA DIODE (ONE-WAY)
                    │ • Hardware OU Software
                    │ • UDP sem ACK
                    │ • AES-256-GCM encryption
┌──────────────────────────────────────────────────────┐
│   CAMADA 2: WORKSTATION ANÁLISE (Air-Gapped)        │
│                                                      │
│  HUMAN-IN-THE-LOOP (Obrigatório):                   │
│  • SOC L1: Triagem (~30min/incidente)               │
│  • Threat Intel L2: Análise profunda (~4-8h/APT)    │
│  • Analista Sênior: Validação (~2h/atribuição)      │
│  • Comitê de Ética: Casos ambíguos                  │
│                                                      │
│  Tools: Wireshark, Ghidra, Volatility, YARA         │
│  Specs: 64GB RAM, 2TB SSD, RTX 3080                 │
└──────────────────────────────────────────────────────┘
                    ▲
                    │ SECURE ONE-WAY EXPORT
┌──────────────────────────────────────────────────────┐
│      CAMADA 3: ILHA DE SACRIFÍCIO (DMZ+++)           │
│                                                      │
│  Honeypots:                                          │
│  • Web App (Apache+PHP) - SQL Injection, LFI        │
│  • SSH Server (OpenSSH) - Weak credentials          │
│  • Database (MySQL) - Exposed port 3306             │
│  • API Moderna (FastAPI) - Broken Auth, SSRF        │
│  • IoT Simulado (MQTT) - No TLS, defaults           │
│                                                      │
│  Forensic Capture:                                   │
│  • TShark (network PCAPs)                           │
│  • eBPF (system calls)                              │
│  • LiME (memory dumps)                              │
│  • MITM proxy (HTTP/HTTPS)                          │
│                                                      │
│  Kill Switches: Auto-shutdown <10s (emergência)     │
└──────────────────────────────────────────────────────┘
                    ▲
               INTERNET (Exposed)
```

### Controles de Isolamento

**Network Segmentation**:
- Firewall: DROP all (default), ACCEPT somente data diode UDP
- Stealth mode: sem ICMP replies
- Log pivot attempts → trigger kill switch

**Virtualization Isolation**:
- KVM/QEMU + SELinux enforcing
- VMs isoladas, zero shared folders
- Snapshots 24h, network namespaces separados

**Application Sandboxing**:
- Seccomp-BPF (whitelist syscalls)
- AppArmor profiles custom
- UID/GID separation, chroot jails

**Kill Switches**:
```yaml
triggers_shutdown_automatico:
  - pivot_attempts: 1  # ZERO TOLERANCE
  - cpu_percent: >95%
  - network_out: >1Gbps
  - forensic_files_modified: 1
  
fases_shutdown:
  1_freeze_vms: "<3s (preservar estado)"
  2_snapshot_emergencia: "<5s"
  3_destroy_network: "<1s"
  4_log_imutavel: "<1s (WORM storage)"
  
total: "<10 segundos"
```

---

## MÉTRICAS DE VALIDAÇÃO (KPIs CRÍTICOS)

### Qualidade da Inteligência

**KPI-001: Taxa de TTPs Acionáveis**
- Definição: % de incidentes que geram ≥1 TTP mapeável (MITRE ATT&CK)
- Meta: ≥60% (6 meses) → ≥80% (12 meses)
- Método: Análise manual de relatórios L2

**KPI-002: Descoberta de 0-Days**
- Definição: CVEs inéditos identificados
- Meta: ≥2 por ano
- Validação: Verificação com NVD

**KPI-003: Tempo de Identificação de Malware**
- Definição: Tempo médio captura → identificação completa
- Meta: <24h para 90% dos casos

### Credibilidade da Decepção

**KPI-004: Taxa de Detecção Estimada**
- Definição: % de ataques que detectaram honeypot
- Sinais: Fingerprinting, disconnect <10s, anti-honeypot queries
- Meta: <15% (quanto menor, melhor)

**KPI-005: Profundidade de Engagement**
- Níveis: L1 (port scan) → L2 (enum) → L3 (exploitation) → L4 (post-exploitation)
- Meta: ≥40% L3, ≥15% L4

**KPI-006: Tempo Médio de Permanência**
- Definição: Duração média de sessão de ataque
- Meta: ≥15 minutos (indica engajamento profundo)

### Integridade de Segurança (CRÍTICO)

**KPI-007: Incidentes de Transbordamento**
- Definição: Tentativas de pivot para produção detectadas
- Meta: 0 (ZERO TOLERANCE)
- Validação: Firewall logs + IDS alerts

**KPI-008: Falsas Atribuições**
- Definição: Atribuições preliminares refutadas posteriormente
- Meta: <5%
- Método: Revisão sênior + threat intel externo

**KPI-009: Tempo de Resposta Kill Switch**
- Definição: Latência detecção → shutdown
- Meta: <10 segundos
- Teste: Simulação mensal (tabletop exercise)

---

## CRITÉRIOS DE GO/NO-GO PARA FASE 2

### Condições ABSOLUTAS (todas obrigatórias)

```yaml
1_seguranca:
  - KPI-007 = 0 por 12 meses consecutivos
  - Pentest externo passou (sem escape de isolamento)
  - Zero incidentes legais/regulatórios

2_qualidade:
  - KPI-001 ≥ 80% por 6 meses consecutivos
  - KPI-004 < 15% (credibilidade)
  - ≥50 TTPs únicos mapeados (MITRE ATT&CK)

3_governanca:
  - Aprovação unânime do Comitê de Ética
  - Documentação completa de incidentes
  - Auditoria de logs sem gaps

4_valor:
  - ≥2 CVEs descobertos
  - ROI positivo documentado
  - Threat intel usada para prevenir ≥1 ataque real
```

### Triggers de SUSPENSÃO (1 = freeze projeto)

```yaml
triggers_suspend:
  - ❌ Qualquer transbordamento para produção
  - ❌ Violação de LGPD/Lei 12.737/2012
  - ❌ Detecção de alimentação de dados falsos (subversão)
  - ❌ Perda de chave de criptografia forense
```

---

## ROADMAP DE IMPLEMENTAÇÃO

### Fase 0: Preparação (Mês 0)

**Semanas 1-2: Aprovação e Funding**
- [ ] Apresentação executiva para CISO/CTO/CEO
- [ ] Aprovação orçamentária ($730k-$775k)
- [ ] Definição de equipe (5 FTE + 2 consultores)
- [ ] Formação do Comitê de Ética

**Semanas 3-4: Aquisição de Infraestrutura**
- [ ] Procurement de hardware (cluster + workstation)
- [ ] Aquisição de data diode (Opção A: hardware $50k OU B: software $5k)
- [ ] Preparação física de datacenter (segmentação)
- [ ] Licenças de software

**Critérios de Sucesso Fase 0**:
- ✅ Orçamento aprovado
- ✅ Equipe confirmada (60%+)
- ✅ Hardware entregue
- ✅ Comitê de Ética reunido

---

### Fase 1: Fundação (Meses 1-3)

**Mês 1: Infraestrutura Base**

Semanas 1-2: Setup de Hypervisor
- [ ] Instalação KVM/QEMU + libvirt
- [ ] Configuração SELinux (enforcing)
- [ ] Criação de network namespaces isolados
- [ ] Setup de snapshots automáticos (cronjob 24h)

Semanas 3-4: Data Diode & Forensic Pipeline
- [ ] Instalação física do data diode
- [ ] Configuração de firewall triplo (se software diode)
- [ ] Implementação do ForensicExporter (Python)
- [ ] Teste de throughput (simular 1GB PCAPs)

**Deliverables Mês 1**:
- Cluster operacional (3 VMs de teste)
- Data diode funcional (one-way validated)
- Pipeline de exportação forense (encrypted)

**Mês 2: Primeiro Honeypot**

Semanas 1-2: SSH Honeypot (Cowrie)
- [ ] Deploy VM Ubuntu 22.04
- [ ] Instalação e configuração Cowrie
- [ ] Integração com TShark (PCAP capture)
- [ ] Configuração de weak credentials (isca)

Semanas 3-4: Validação End-to-End
- [ ] Ataque simulado interno (Hydra brute force)
- [ ] Verificação de captura e exportação
- [ ] Análise forense em workstation
- [ ] Teste de kill switch (pivot attempt simulado)

**Deliverables Mês 2**:
- SSH honeypot operacional
- Pipeline completo validado (ataque → captura → análise)
- Kill switch funcional (<10s shutdown)

**Mês 3: Workstation de Análise**

Semanas 1-2: Setup de Ferramentas
- [ ] Ubuntu 22.04 hardened (air-gapped)
- [ ] Wireshark, NetworkMiner, Volatility, Rekall
- [ ] Cuckoo Sandbox, Ghidra, YARA
- [ ] MITRE ATT&CK Navigator (offline)

Semanas 3-4: SOPs e Treinamento
- [ ] Escrever SOP completo (triagem → disseminação)
- [ ] Templates de relatórios STIX 2.1
- [ ] Checklist de validação de atribuição
- [ ] Treinamento de analistas (workshop 2 dias)

**Deliverables Mês 3**:
- Workstation 100% offline operacional
- SOPs documentados e revisados
- Analistas treinados (1 L1 + 1 L2 mínimo)

**Critérios de Sucesso Fase 1**:
- ✅ VMs criadas/destruídas <5min
- ✅ Data diode passa teste de reversão
- ✅ SSH honeypot recebe e loga ataques
- ✅ PCAPs exportados e analisáveis
- ✅ Kill switch <10s
- ✅ Equipe treinada

---

### Fase 2: Expansão (Meses 4-6)

**Mês 4: Honeypots Adicionais**

Semanas 1-2: Web Application Honeypot
- [ ] Apache 2.4 + PHP 7.2 + MySQL 5.7
- [ ] Vulnerabilidades: SQL Injection, LFI, XSS
- [ ] Curadoria: Git repo fake, logs antigos, arquivos .bak

Semanas 3-4: API Honeypot Moderna
- [ ] FastAPI + JWT + PostgreSQL
- [ ] Vulnerabilidades: Broken Auth, SSRF, Mass Assignment
- [ ] OpenAPI docs expostos (/docs)

**Deliverables Mês 4**:
- 3 honeypots operacionais (SSH, Web, API)
- Todos integrados ao pipeline forense
- Tráfego de background simulado (HoneyTrafficGenerator)

**Mês 5: Dashboard de Inteligência**

Semanas 1-2: Prometheus + Grafana
- [ ] Métricas: Conexões, IPs únicos, Top TTPs, Engagement
- [ ] Painéis: Executive, Operational, Quality

Semanas 3-4: Custom Exporters
- [ ] HoneypotMetricsExporter (Python → Prometheus)
- [ ] Alertas configurados (KPI-007 = trigger imediato)

**Deliverables Mês 5**:
- Dashboards acessíveis (read-only)
- Métricas atualizadas <5min latency
- Alertas críticos funcionais

**Mês 6: Primeiro Ciclo de Análise Real**

Semanas 1-4: Exposição Controlada
- [ ] Expor honeypots à internet (portas 22, 80, 443, 3306)
- [ ] Monitoramento 24/7 por SOC
- [ ] Triagem diária (L1) + análise profunda casos APT (L2)
- [ ] Validação sênior de atribuições (L3)

**Deliverables Mês 6**:
- Primeiro relatório mensal de inteligência
- Mapeamento de ≥10 TTPs únicos
- Identificação de ≥3 malware families
- Apresentação executiva de resultados

**Critérios de Sucesso Fase 2**:
- ✅ KPI-001 ≥ 50% (taxa TTPs acionáveis)
- ✅ KPI-004 < 20% (taxa de detecção aceitável)
- ✅ KPI-007 = 0 (zero transbordamentos)

---

### Fase 3: Otimização (Meses 7-12)

**Meses 7-8: Curadoria Avançada**
- Objetivo: Reduzir KPI-004 para <15%
- Táticas: Randomização, delays variáveis, "human touch"
- Deliverable: Scripts de curadoria automatizada

**Meses 9-10: Automação de Análise**
- Objetivo: Reduzir tempo triagem L1 em 50%
- Componente: AutomatedTriageEngine (YARA, ML classification)
- Deliverable: 70% incidentes triviais triados automaticamente

**Meses 11-12: Validação de Métricas**
- Objetivo: Avaliar Go/No-Go para Fase 2
- Checklist: Todas as condições absolutas
- Deliverables:
  - Relatório anual completo
  - Recomendação Go/No-Go
  - Apresentação executiva para board

**Decisão Final**:
- **GO** se TODAS as condições satisfeitas
- **NO-GO** se qualquer KPI crítico falhou
- **SUSPEND** se incidente catastrófico

---

### Fase 4: Fase 2 Condicional (Meses 13-18, SOMENTE SE GO)

**ATENÇÃO**: Esta fase SOMENTE executada se Fase 1 = 100% sucesso.

**Meses 13-15: Respostas Defensivas Automatizadas (Nível 1)**
- Ações permitidas: Bloqueio temporário IPs, rate limiting adaptativo
- Requisito: Human approval para ações além de bloqueio temporário

**Meses 16-17: Integração com MAXIMUS Core (Read-Only)**
- API de threat intel (TTPs recentes, IoCs)
- Fluxo: Ilha → MAXIMUS (não o inverso)

**Mês 18: Validação de Fase 2**
- Critérios: Zero falsos positivos, zero transbordamentos, ROI positivo

---

## PLANO OPERACIONAL

### Equipe (Headcount)

| Papel | FTE | Salário Anual | Responsabilidades |
|-------|-----|---------------|-------------------|
| Security Architect | 1 | $150k | Design e manutenção arquitetural |
| DevOps Engineer | 1 | $120k | Infra, honeypots, automação |
| SOC Analyst L1 | 2 | $180k (2×$90k) | Triagem 24/5 |
| Threat Intel Analyst L2 | 1 | $130k | Análise profunda, TTPs |
| Malware RE | 0.5 | $40k | Consultoria (payloads complexos) |
| Legal Advisor | 0.25 | $15k | Conformidade trimestral |
| **TOTAL** | **5.75 FTE** | **$635k** | |

### Rotinas Operacionais

**Daily (SOC L1)**:
- 08:00: Handoff matinal, revisar incidentes da noite
- 09:00-17:00: Triagem contínua (30min/incidente)
- 17:00: Handoff vespertino, escalações L2

**Weekly (DevOps Engineer)**:
- Segunda: Rotação de snapshots, atualização YARA
- Quarta: Análise KPI-004, ajustes de curadoria
- Sexta: Relatório semanal, prep on-call

**Monthly (Threat Intel Lead)**:
- Semana 1: Consolidação de TTPs, relatório STIX 2.1
- Semana 2-3: Análise profunda casos APT, RE de malware
- Semana 4: Refresh de honeypots, planning

**Quarterly (Comitê de Ética)**:
- Revisão de casos ambíguos
- Avaliação de compartilhamento externo
- Auditoria de conformidade LGPD/Lei 12.737

### Escalação de Incidentes

| Nível | Descrição | Resposta | SLA |
|-------|-----------|----------|-----|
| 1 - Trivial | Port scan | L1 apenas | <1h |
| 2 - Baixo | Brute force | L1 + relatório | <4h |
| 3 - Médio | Exploitation | L2 (profunda) | <24h |
| 4 - Alto | Post-exploitation | L2 + L3 | <48h |
| 5 - Crítico | APT-like | L2 + L3 + Comitê | <72h |

**Protocolo Nível 5 (APT)**:
1. L1 detecta comportamento APT (lateral movement, custom malware)
2. Escalação imediata: L2 + Security Architect + CISO
3. Freeze temporário (preservar evidências)
4. Análise profunda (L2 + Malware RE, 48h)
5. Validação sênior (Security Architect + CISO)
6. Comitê de Ética (se atribuição ambígua)

### Framework Ético e Legal

**Proibições Absolutas**:
- ❌ Retaliação ativa (hackback)
- ❌ Divulgação não autorizada de 0-days de terceiros
- ❌ Uso de dados para propósitos não-segurança
- ❌ Coleta excessiva de dados pessoais (LGPD Art. 6º)

**Obrigações Positivas**:
- ✅ Notificação a vítimas identificadas (após análise)
- ✅ Compartilhamento de IoCs com CERT.br (anonimizado)
- ✅ Transparência em auditorias regulatórias
- ✅ Disclosure responsável de 0-days

**Conformidade Legal (Brasil)**:

Lei nº 12.737/2012 ("Lei Carolina Dieckmann"):
- Interceptação de comunicações: ✅ LEGAL (sistema próprio)
- Análise de malware: ✅ LEGAL (Decreto 9.637/2018)

LGPD (Lei 13.709/2018):
- Incidentes com dados de terceiros → ANPD (72h)
- Base legal: Legítimo interesse (Art. 7º, IX)

**Comitê de Ética em Segurança**:
- Composição: 1 Advogado + 1 Pesquisador Sênior + 1 CISO
- Reuniões: Trimestrais + ad-hoc
- Escopo: Revisar casos ambíguos, aprovar compartilhamento externo

---

## CONTINGÊNCIAS OPERACIONAIS

### Perda de Analista Key
- Backup imediato: Promover L1 mais sênior (interino)
- Recrutamento: Nova contratação em 60 dias
- Transferência de conhecimento: Documentação + shadowing 2 semanas

### Falha de Hardware (Data Diode)
- Detecção: Heartbeat check (5min intervals)
- Resposta: Freeze honeypots, diagnóstico (30min)
- Recuperação: Restart serviços (1h) OU data diode backup (4h)

### Ataque Volumétrico (DDoS)
- Detecção: Prometheus alert (network_in_mbps > 1000)
- Resposta: Rate limiting agressivo (iptables)
- Se persistir: Shutdown temporário de honeypots específicos
- Pós-ataque: Análise se DDoS foi smoke screen para APT

---

## APROVAÇÕES OBRIGATÓRIAS

**Este plano será considerado APROVADO quando**:

- [ ] **CISO** - Assinatura: _______________ Data: ___/___/___
- [ ] **CTO** - Assinatura: _______________ Data: ___/___/___
- [ ] **CEO** - Assinatura: _______________ Data: ___/___/___
- [ ] **Legal Advisor** - Assinatura: _______________ Data: ___/___/___
- [ ] **Security Architect** - Assinatura: _______________ Data: ___/___/___
- [ ] **Comitê de Ética** - Aprovação unânime: [ ] SIM [ ] NÃO

---

## PRÉ-FLIGHT CHECKLIST (Antes de Go-Live)

**Infrastructure**:
- [ ] Todos honeypots respondem a ping interno
- [ ] Data diode passa teste de one-way (sem ACK)
- [ ] Snapshots automáticos (cron validado)
- [ ] Kill switches testados (tabletop exercise)

**People**:
- [ ] SOC L1 treinados (2+ analistas)
- [ ] Threat Intel L2 confirmado
- [ ] DevOps Engineer onboarded
- [ ] Comitê de Ética reunido (kick-off)

**Process**:
- [ ] SOPs escritos e revisados
- [ ] Templates de relatórios prontos (STIX 2.1)
- [ ] Protocolos de escalação documentados
- [ ] On-call rotation definida (24/5)

**Legal**:
- [ ] Aprovação Legal Advisor (LGPD + Lei 12.737)
- [ ] Documentação de consentimento
- [ ] Protocolo de notificação ANPD/PF

**Executive**:
- [ ] Sign-off CISO, CTO, CEO
- [ ] Orçamento aprovado (18 meses)
- [ ] Board informado

---

## PRÓXIMOS PASSOS IMEDIATOS

1. **Semana 1**: Apresentação executiva para board
2. **Semana 2**: Aprovação orçamentária
3. **Semana 3-4**: Procurement de hardware
4. **Semana 5**: Início de Sprint 1.1 (Setup Hypervisor)

---

## CONCLUSÃO: O FATOR HUMANO NO ELO

Este projeto não é apenas sobre tecnologia. É sobre:

1. **Human-in-the-Loop**: Autorização humana obrigatória para TODA ação fora da Ilha. Quem são esses humanos? Qual o treinamento? Como garantimos que não se tornem "rubber stamps"?

2. **Custo da Ilusão**: Manter a Ilha de Sacrifício crível exige curadoria meticulosa e contínua. Não é "configure e esqueça"; é jardinagem em campo minado.

3. **Métricas de Validação**: Antes de sonhar com Fase 2, precisamos PROVAR sucesso da Fase 1. Como mediremos "qualidade de inteligência"? Quantos TTPs de APTs precisamos identificar para validar?

**Este plano responde essas perguntas com clareza cirúrgica. Cada decisão arquitetural serve à missão: aprender com adversários sem se tornar um.**

---

**FIM DO PLANO EXECUTIVO COMPLETO**

*"A superfície de ataque não é uma fraqueza. É uma oportunidade de aprender."*  
— Doutrina Vértice, Princípio do Tecido Reativo

*"Inteligência sem ética é entropia. Ética sem inteligência é ingenuidade."*  
— Comitê de Ética MAXIMUS, Princípio Fundacional

---

**Versão**: 1.0 | **Data**: 2025-10-12  
**Autor**: MAXIMUS Security Research Team  
**Status**: AGUARDANDO APROVAÇÕES EXECUTIVAS

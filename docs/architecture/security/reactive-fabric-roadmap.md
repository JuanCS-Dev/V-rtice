# Roadmap de Implementação: Projeto Tecido Reativo
## Arquitetura de Decepção Ativa - Fase 1 (Coleta Passiva)

**Status**: ROADMAP APROVADO | **Duração**: 24 meses | **Fase**: 1 (Passiva)  
**Fundamentação**: [Blueprint Técnico](./reactive-fabric-blueprint.md) | [Paper Viabilidade](/home/juan/Documents/Análise de Viabilidade: Arquitetura de Decepção Ativa e Contra-Inteligência Automatizada.md)  
**Início Previsto**: 2025-11-01 | **Gate Fase 2**: 2027-05-01 (condicional)

---

## FILOSOFIA DO ROADMAP

**Progressão Condicional > Entregas Fixas**

Cada sprint possui critérios de validação objetivos. Nenhuma progressão acontece sem validação completa da etapa anterior. Preferimos atrasar 6 meses com segurança garantida do que avançar 1 dia com risco de contenção.

**Doutrina Vértice em Cada Milestone**:
- Sprint não valida se introduzir risco de contenção
- Sprint não valida se HITL for contornável
- Sprint não valida se auditoria tiver gaps
- Sprint não valida se testes de segurança falharem

---

## FASE 1: COLETA PASSIVA (Meses 1-24)

### SPRINT 1: FUNDAÇÃO DE ISOLAMENTO (Meses 1-3)

**Objetivo**: Estabelecer air-gap virtual inquebrável entre Camadas 1-2-3.

#### Semana 1-2: Planejamento e Procurement
- [ ] **1.1.1** Finalizar network diagrams detalhados (Camadas 1-3)
  - Engenheiro: Arquiteto de Redes
  - Entrega: Visio/Lucidchart com IPs, VLANs, firewall rules
  - Validação: Review por 2 arquitetos sêniores

- [ ] **1.1.2** Aprovar BoM (Bill of Materials) de hardware
  - Items: Data Diode, NGFW (2x), servidores (24x), storage WORM
  - Validação: Budget aprovado + fornecedores selecionados
  - Lead Time: 6-8 semanas para entrega

- [ ] **1.1.3** Definir alocação física de hardware
  - Camada 1 (Produção): Rack existente, sem mudanças
  - Camada 2 (DMZ): Rack dedicado, fisicamente separado
  - Camada 3 (Ilha): Rack isolado, idealmente sala separada
  - Validação: Diagrama de datacenter + aprovação facilities

#### Semana 3-6: Provisionamento de Infraestrutura
- [ ] **1.2.1** Rack e cabeamento da Camada 3 (Ilha)
  - 20x VMs (honeypots) em 4 hosts físicos
  - VLAN trunk para micro-segmentação
  - **Teste**: Ping entre VLANs deve FALHAR (isolamento validado)

- [ ] **1.2.2** Instalação de NGFW (Palo Alto PA-5450)
  - Posição: Entre Camada 3 ↔ Camada 2
  - Configuração inicial: DENY ALL (whitelist apenas logs)
  - **Teste**: Tentativa de SSH da Ilha → DMZ deve ser bloqueada

- [ ] **1.2.3** Rack e cabeamento da Camada 2 (DMZ/Orquestração)
  - 4x servidores para CANDI + análise forense
  - Storage WORM para evidências (15TB inicial)
  - **Teste**: Backup de teste em WORM deve ser write-once

- [ ] **1.2.4** Instalação de Data Diode (Owl DCGS-10G)
  - Posição: Entre Camada 2 → Camada 1 (unidirecional)
  - Configuração: Apenas intelligence reports (JSON sanitizado)
  - **Teste**: Tentativa de comunicação reversa (1→2) deve FALHAR fisicamente

#### Semana 7-10: Deploy de Honeypots Iniciais
- [ ] **1.3.1** Implementar 3 tipos de honeypots de alta interação
  - **SSH/Telnet**: Cowrie (emula Linux vulnerable)
  - **Web**: DVWA (Damn Vulnerable Web App)
  - **Database**: PostgreSQL com dados falsos + credenciais honeytokens
  - Cada tipo em VLAN isolada (10.66.1.0/24, 10.66.2.0/24, 10.66.3.0/24)

- [ ] **1.3.2** Configurar logging forense centralizado
  - Stack: ELK (Elasticsearch + Logstash + Kibana)
  - Logs capturados: Syscalls (auditd), network (tcpdump), auth (PAM)
  - Retenção: 180 dias (hot) + 2 anos (cold em WORM)
  - **Teste**: Gerar ataque sintético, validar captura de TODOS os logs

- [ ] **1.3.3** Deploy de sondas forenses voláteis
  - OSQuery em cada honeypot (telemetria de endpoints)
  - Memory snapshots automáticos a cada 6h (Volatility-ready)
  - **Teste**: Kill honeypot, validar que memory dump foi salvo

#### Semana 11-12: Validação de Isolamento (Pentest Interno)
- [ ] **1.4.1** Red Team Exercise: Tentativa de Breakout
  - Objetivo: Comprometer honeypot → tentar alcançar Camada 2 ou 1
  - Duração: 5 dias (40 horas de ataques)
  - **Critério de Sucesso**: ZERO alcance fora da Camada 3

- [ ] **1.4.2** Análise de superfície de ataque
  - Scanear Camada 3 de fora (perspectiva de atacante)
  - Identificar fingerprinting possível (OS detection, service banners)
  - **Critério**: Honeypots devem parecer indistinguíveis de produção real

- [ ] **1.4.3** Documentação de Sprint 1
  - Network diagrams finais (as-built)
  - Runbook de operação básica (iniciar/parar honeypots)
  - Post-mortem de red team exercise
  - **Entrega**: 50+ páginas de documentação técnica

**GATE SPRINT 1 → SPRINT 2**:
- ✅ Red team NÃO conseguiu breakout da Camada 3
- ✅ Todos os 3 honeypots operacionais com logging funcional
- ✅ Data diode validado (comunicação unidirecional confirmada)
- ✅ Documentação técnica revisada por arquiteto sênior

---

### SPRINT 2: INTELIGÊNCIA E ANÁLISE (Meses 4-6)

**Objetivo**: Transformar logs brutos em inteligência acionável.

#### Semana 13-16: Integração de Threat Intelligence
- [ ] **2.1.1** Integrar feeds de threat intel comerciais
  - **Fontes**: VirusTotal API, AlienVault OTX, Abuse.ch
  - **Dados**: Malware hashes, C2 IPs/domains, YARA rules
  - Frequência: Atualização a cada 1h
  - **Teste**: Query de hash conhecido, validar detecção

- [ ] **2.1.2** Deploy de MISP (Malware Information Sharing Platform)
  - Instalar em Camada 2 (análise/correlação)
  - Importar feeds públicos (CIRCL, FIRST)
  - **Teste**: Correlacionar 10 IoCs de ataque real, gerar relatório

- [ ] **2.1.3** Implementar correlation engine (CANDICore v0.1)
  - Input: Logs de honeypots + feeds de TI
  - Output: Alertas priorizados por threat level
  - Algoritmo inicial: Rule-based (Sigma rules)
  - **Teste**: Simular ataque, validar alerta em <5min

#### Semana 17-20: Pipeline de Análise de Malware
- [ ] **2.2.1** Deploy de sandbox automatizado (Cuckoo Sandbox)
  - 4 VMs Windows + 2 VMs Linux para detonation
  - Análise: Behavioral (syscalls), network (DNS/HTTP), forensic (memory)
  - **Teste**: Submeter 10 amostras de malware conhecidas, validar relatórios

- [ ] **2.2.2** Implementar extração de IoCs automatizada
  - Parser de relatórios Cuckoo → MISP
  - Extração: IPs, domains, mutexes, registry keys, file paths
  - **Teste**: Malware sample deve gerar ≥20 IoCs únicos

- [ ] **2.2.3** Machine Learning para classificação de malware
  - Dataset: 10k samples rotulados (Kaggle + VirusTotal)
  - Features: API calls, strings, PE headers
  - Modelo: Random Forest (baseline)
  - **Acurácia alvo**: ≥85% em test set

#### Semana 21-24: Sistema de Atribuição
- [ ] **2.3.1** Desenvolver scoring de atribuição multi-fonte
  - Fontes: GeoIP, TI feeds, TTPs (MITRE ATT&CK), linguistic analysis
  - Scoring: 0-100 (0=unknown, 100=verified)
  - Thresholds: <40=noise, 40-60=opportunistic, 60-80=targeted, >80=APT
  - **Teste**: 20 ataques históricos, validar accuracy vs ground truth

- [ ] **2.3.2** Mapear TTPs para MITRE ATT&CK framework
  - Parser de logs → técnicas ATT&CK
  - Ex: "SSH brute-force" → T1110.001 (Brute Force: Password Guessing)
  - **Teste**: Ataque sintético deve mapear ≥5 técnicas corretamente

- [ ] **2.3.3** Dashboard de inteligência (Kibana customizado)
  - Visualizações: Threat level heatmap, top atacantes, TTPs timeline
  - Filtros: Por data, fonte, confidence, threat level
  - **Teste**: Operador SOC deve encontrar ataque específico em <2min

#### Semana 25-26: Plantio de Honeytokens
- [ ] **2.4.1** Honeytokens em ambientes **falsos** (não produção)
  - **AWS Keys**: Credenciais falsas em .env (monitoradas via AWS Canary)
  - **SSH Keys**: Chaves privadas plantadas com passphrase fraca
  - **API Tokens**: Tokens de serviços fake-críticos
  - **Documentos**: 10 Word docs com macros que reportam abertura

- [ ] **2.4.2** Sistema de alerta de honeytoken
  - Trigger: Honeytoken usado → alerta CRITICAL em CANDI
  - Contexto: IP/user que acionou, timestamp, tipo de token
  - **Teste**: Usar honeytoken manualmente, validar alerta em <1min

**GATE SPRINT 2 → SPRINT 3**:
- ✅ Pipeline de malware sandbox funcional (≥50 samples analisados)
- ✅ Sistema de atribuição gerando confidence scores
- ✅ Dashboard de inteligência operacional (usado por SOC)
- ✅ ≥5 TTPs de APTs identificados corretamente

---

### SPRINT 3: HUMAN-IN-THE-LOOP & AUDITORIA (Meses 7-9)

**Objetivo**: Estabelecer governança humana e auditoria imutável.

#### Semana 27-30: Desenvolvimento do Console HITL
- [ ] **3.1.1** UI/UX do console de decisão
  - Framework: Next.js + React + Tailwind (consistência com frontend MAXIMUS)
  - Páginas: Dashboard, Alertas Pendentes, Histórico de Decisões, Evidências
  - **Teste**: 3 operadores beta testam, SUS score ≥80

- [ ] **3.1.2** Workflow de autorização estruturado
  - Estados: PENDING → UNDER_REVIEW → APPROVED/DENIED → EXECUTED
  - Timeout: 4h em PENDING → auto-DENY
  - **Requisitos**: 2FA obrigatório para APPROVE, assinatura digital
  - **Teste**: Simular 10 decisões, validar logging de todas as etapas

- [ ] **3.1.3** Apresentação de evidências (forensic viewer)
  - Exibir: Timeline de ataque, logs raw, PCAP viewer, memory dumps
  - Destacar: IoCs extraídos, TTPs mapeados, attribution sources
  - **Teste**: Operador deve conseguir tomar decisão informada em <15min

#### Semana 31-34: Blockchain Audit Log
- [ ] **3.2.1** Deploy de Hyperledger Fabric (blockchain privada)
  - Nós: 3 peers (redundância) na Camada 2
  - Consensus: Raft (tolerância a 1 falha)
  - **Teste**: Submeter 1000 transações, validar integridade

- [ ] **3.2.2** Implementar ImmutableAuditLog (backend)
  - Eventos auditados: ATTACK_DETECTED, HITL_DECISION, ACTION_EXECUTED
  - Hash: SHA256 de evento + timestamp + evidências
  - Anchor: Blockchain tx ID retornado
  - **Teste**: Tentar alterar evento passado, detectar violação

- [ ] **3.2.3** API de verificação de integridade
  - Endpoint: `/audit/verify/{event_id}`
  - Retorna: Boolean (íntegro?) + blockchain proof
  - **Teste**: Verificar 100 eventos aleatórios, 100% íntegros

#### Semana 35-38: Treinamento de Operadores HITL
- [ ] **3.3.1** Desenvolver currículo de treinamento (40 horas)
  - Módulo 1: Fundamentos de Threat Intel (8h)
  - Módulo 2: Análise Forense (12h)
  - Módulo 3: Atribuição de Ataques (8h)
  - Módulo 4: Decisão sob Pressão (8h - tabletop)
  - Módulo 5: Legal/Ético (4h - com counsel)

- [ ] **3.3.2** Certificação GIAC para 3 operadores
  - Certificação: GCIH (Incident Handler) ou GCIA (Intrusion Analyst)
  - Custo: $8k por operador
  - **Requisito**: Passar com ≥75% de acurácia

- [ ] **3.3.3** Tabletop exercises (simulações de ataque)
  - Cenários: 10 ataques sintéticos (variando threat level)
  - Métricas: Tempo de decisão, acurácia, aderência a protocolo
  - **Critério**: Operadores devem aprovar/negar corretamente em 90% dos casos

#### Semana 39-40: Playbooks de Resposta
- [ ] **3.4.1** Criar playbooks estruturados para decisão
  - Categorias: Brute-force, Web exploits, Malware, Lateral movement
  - Conteúdo: Checklist de validação, fontes de confirmação, ações padrão
  - **Teste**: Operador novo deve seguir playbook com 100% aderência

- [ ] **3.4.2** Matriz de decisão (decision tree)
  - Input: Threat level + Attribution confidence
  - Output: Recomendação de ação (CANDI sugere, humano decide)
  - Ex: Level 4 + Confidence HIGH → Recomenda "Block C2 + Notify CERT"
  - **Teste**: 20 cenários, validar consistência de recomendações

**GATE SPRINT 3 → SPRINT 4**:
- ✅ 3 operadores HITL certificados e treinados
- ✅ Console HITL operacional com 2FA + assinatura digital
- ✅ Blockchain audit log com 100% de eventos íntegros
- ✅ Playbooks aprovados por arquiteto de segurança

---

### SPRINT 4: OTIMIZAÇÃO & ESCALA (Meses 10-12)

**Objetivo**: Expandir honeynet e atingir maturidade operacional.

#### Semana 41-44: Expansão da Honeynet
- [ ] **4.1.1** Adicionar 7 novos tipos de honeypots
  - **Email**: Postfix com credenciais fracas (captura spam/phishing)
  - **FTP**: vsftpd com anonymous login (atrai data exfiltration)
  - **RDP**: Windows Server com credenciais default
  - **IoT**: Honeypots emulando câmeras/routers (Dionaea)
  - **Industrial**: SCADA simulado (Conpot)
  - **API**: Fake REST API do MAXIMUS (vulnerável a injection)
  - **Blockchain**: Fake wallet com keys fracas
  - **Teste**: Cada honeypot deve capturar ≥1 ataque em 7 dias

- [ ] **4.1.2** Atingir 10+ honeypots simultâneos
  - Distribuição: 2-3 de cada tipo, VLANs isoladas
  - Orquestração: Terraform + Ansible para provisionamento
  - **Teste**: Destruir e recriar honeynet completa em <30min

#### Semana 45-48: Ephemerality (Rotação Automatizada)
- [ ] **4.2.1** Implementar rotação de VMs (48-72h)
  - Script: Terraform destroy + apply com configs randomizadas
  - Randomização: IPs, hostnames, service versions, file timestamps
  - **Teste**: Atacante retornando após 72h deve ver topologia diferente

- [ ] **4.2.2** Snapshot de estado antes de destruição
  - Capturar: Memory dump, disk image, logs
  - Armazenar: WORM storage (chain of custody)
  - **Teste**: Recuperar estado de honeypot de 30 dias atrás

#### Semana 49-52: Tuning de Algoritmos
- [ ] **4.3.1** Reduzir falsos positivos em atribuição
  - Análise: Revisar 100 ataques classificados, identificar FPs
  - Tuning: Ajustar pesos de features, adicionar whitelist de IPs legítimos
  - **Meta**: FP rate ≤ 1% (validado em test set)

- [ ] **4.3.2** Otimizar tempo de análise forense
  - Baseline: ~8h por sample complexo (manual)
  - Otimização: Paralelizar sandbox, priorizar por threat level
  - **Meta**: ≤4h (média) para análise completa

- [ ] **4.3.3** A/B testing de realismo de honeypots
  - Setup: 50% honeypots "curated" vs 50% "vanilla"
  - Métricas: Tempo de residência do atacante, profundidade de exploração
  - **Critério**: "Curated" deve ter ≥2x tempo de residência

#### Semana 53-54: Red Team Exercise Final (Sprint 4)
- [ ] **4.4.1** Pentest externo por firma especializada
  - Escopo: Blind test (não sabem que é honeynet)
  - Duração: 10 dias (80 horas de ataque)
  - **Critério de Sucesso**: Red team não detecta decepção

- [ ] **4.4.2** Social engineering test (phishing com honeytokens)
  - Enviar 50 emails de phishing fake (operadores HITL conscientes)
  - Medir: Taxa de clique, uso de credenciais honeytokens
  - **Meta**: ≥70% de cliques devem acionar honeytokens

**GATE SPRINT 4 → OPERAÇÃO SUSTENTADA**:
- ✅ Red team externo NÃO detectou decepção em blind test
- ✅ 10+ honeypots diversos operacionais
- ✅ Rotação automatizada funcional (72h)
- ✅ FP rate em atribuição ≤ 1%
- ✅ Tempo de análise forense ≤ 4h (média)

---

### OPERAÇÃO SUSTENTADA (Meses 13-24)

**Objetivo**: Coletar inteligência contínua e atingir KPIs para gate de Fase 2.

#### Atividades Recorrentes

**Diário**:
- [ ] Monitoramento de dashboards (operador HITL)
- [ ] Triagem de alertas (priorização por threat level)
- [ ] Análise forense de ataques Level 3+

**Semanal**:
- [ ] Reunião de revisão de inteligência (SOC + HITL)
- [ ] Atualização de feeds de threat intel
- [ ] Backup de evidências para WORM

**Mensal**:
- [ ] Análise de tendências de ataques
- [ ] Tuning de algoritmos (ML retraining)
- [ ] Atualização de playbooks (lições aprendidas)

**Trimestral**:
- [ ] Auditoria interna de segurança (pentest light)
- [ ] Review de compliance (LGPD DPIA update)
- [ ] Treinamento de reciclagem de operadores

**Semestral**:
- [ ] Red team exercise completo (10 dias)
- [ ] Disaster recovery drill (testar restore de backup)
- [ ] Revisão de budget e recursos

**Anual**:
- [ ] Auditoria independente (3rd party)
- [ ] Revisão estratégica com Direção Vértice
- [ ] Avaliação de progressão para Fase 2

#### KPIs de Fase 1 (Tracking Contínuo)

```python
# backend/security/deception/kpi_tracker.py
from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta

@dataclass
class Phase1KPIs:
    """
    KPIs obrigatórios para progressão para Fase 2.
    
    Todos devem ser atingidos após 18 meses de operação.
    Tracking via Prometheus + Grafana dashboard dedicado.
    """
    
    # Inteligência
    apt_ttps_identified: int = 0  # Target: ≥15
    malware_samples_captured: int = 0  # Target: ≥100
    zero_days_discovered: int = 0  # Target: ≥1
    avg_attacker_residence_time_hours: float = 0.0  # Target: ≥6h
    
    # Qualidade de Decepção
    deception_detection_rate: float = 0.0  # Target: ≤5%
    avg_attacker_depth: float = 0.0  # Ex: 3.5 = lateral movement para 3-4 honeypots
    
    # Atribuição
    false_positive_attribution_rate: float = 0.0  # Target: 0%
    avg_attribution_confidence: float = 0.0  # Target: ≥60 (Medium)
    
    # Segurança
    containment_breaches: int = 0  # Target: 0 (absoluto)
    unauthorized_actions: int = 0  # Target: 0
    audit_log_integrity: float = 100.0  # Target: 100%
    
    # Operacional
    candi_uptime: float = 0.0  # Target: ≥99.9%
    avg_forensic_analysis_time_hours: float = 0.0  # Target: ≤4h
    hitl_operators_certified: int = 0  # Target: ≥3
    
    # Timestamp
    measurement_date: datetime = datetime.utcnow()
    
    def validate_phase2_readiness(self) -> bool:
        """
        Valida se TODOS os KPIs foram atingidos.
        
        Returns:
            True apenas se 100% dos targets foram alcançados.
        """
        checks = [
            self.apt_ttps_identified >= 15,
            self.malware_samples_captured >= 100,
            self.zero_days_discovered >= 1,
            self.avg_attacker_residence_time_hours >= 6.0,
            self.deception_detection_rate <= 0.05,
            self.false_positive_attribution_rate == 0.0,
            self.containment_breaches == 0,
            self.unauthorized_actions == 0,
            self.audit_log_integrity == 100.0,
            self.candi_uptime >= 99.9,
            self.avg_forensic_analysis_time_hours <= 4.0,
            self.hitl_operators_certified >= 3
        ]
        
        return all(checks)
```

**Dashboard de Tracking**:
- Grafana dashboard público para Direção Vértice
- Atualizado em tempo real (queries Prometheus)
- Alert se qualquer KPI crítico degradar (ex: containment breach)

---

## MILESTONES E DELIVERABLES

### Mês 3 (Fim Sprint 1)
- ✅ Infraestrutura de 3 camadas operacional
- ✅ 3 honeypots capturando ataques
- ✅ Red team validou isolamento (zero breakout)
- 📄 Network diagrams + runbooks (50 pgs)

### Mês 6 (Fim Sprint 2)
- ✅ Pipeline de análise de malware funcional
- ✅ Sistema de atribuição gerando confidence scores
- ✅ Dashboard de inteligência usado por SOC
- ✅ 5+ TTPs de APTs identificados
- 📄 Relatório de inteligência trimestral (100 pgs)

### Mês 9 (Fim Sprint 3)
- ✅ 3 operadores HITL certificados e operacionais
- ✅ Console HITL com 2FA + assinatura digital
- ✅ Blockchain audit log (100% integridade)
- ✅ Playbooks de decisão aprovados
- 📄 Manual de operação HITL (80 pgs)

### Mês 12 (Fim Sprint 4)
- ✅ 10+ honeypots diversos operacionais
- ✅ Rotação automatizada (72h) funcional
- ✅ Red team externo NÃO detectou decepção
- ✅ FP rate ≤ 1%, análise forense ≤ 4h
- 📄 Relatório de maturidade operacional (150 pgs)

### Mês 18 (Checkpoint Gate Fase 2)
- ✅ Operação sustentada por 6 meses adicionais
- ✅ Validação intermediária de KPIs (≥70% atingidos)
- 📄 Auditoria independente (200 pgs)
- 🎯 Decisão GO/NO-GO para continuar até Mês 24

### Mês 24 (Gate Final Fase 2)
- ✅ TODOS os KPIs de Fase 1 atingidos
- ✅ Zero incidentes críticos em 24 meses
- ✅ Framework legal validado por counsel
- 📄 Relatório completo de Fase 1 (500+ pgs)
- 🎯 Votação Direção Vértice (unanimidade para Fase 2)

---

## RECURSOS E ALOCAÇÃO

### Equipe (Full-Time)

| Papel | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sustentado |
|-------|---------|---------|---------|---------|------------|
| Arquiteto de Segurança | 1.0 FTE | 0.5 | 0.5 | 0.5 | 0.25 |
| DevSecOps Engineer | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| Malware/Forensic Analyst | 0.5 | 1.0 | 1.0 | 1.0 | 1.0 |
| Operador HITL (3x) | - | - | 1.0 | 3.0 | 3.0 |
| ML Engineer | - | 0.5 | 0.5 | 1.0 | 0.5 |
| Legal Counsel | 0.25 | 0.25 | 0.5 | 0.25 | 0.25 |

### Budget por Sprint

| Sprint | Hardware | Software | Pessoal | Treinamento | Total |
|--------|---------|---------|---------|-------------|-------|
| Sprint 1 | $372k | $10k | $180k | $5k | **$567k** |
| Sprint 2 | $0 | $50k | $200k | $10k | **$260k** |
| Sprint 3 | $0 | $15k | $220k | $40k | **$275k** |
| Sprint 4 | $0 | $10k | $240k | $10k | **$260k** |
| Sustentado (12m) | $0 | $50k | $720k | $20k | **$790k** |
| **TOTAL 24m** | **$372k** | **$135k** | **$1,560k** | **$85k** | **$2,152k** |

*Nota: Budget total ligeiramente maior que estimativa do blueprint devido a alocação detalhada de FTEs em fase sustentada.*

---

## RISCOS E CONTINGÊNCIAS

### Riscos de Cronograma

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Delay em procurement de hardware** | ALTA | Atraso 6-8 semanas | • Iniciar compra 3 meses antes<br>• Fornecedores alternativos pre-aprovados |
| **Dificuldade em contratar operadores HITL** | MÉDIA | Atraso 2-3 meses | • Recrutar early (Sprint 2)<br>• Considerar contractors temporários |
| **Red team detecta decepção** | BAIXA | Sprint 1 ou 4 falha | • Iterar curadoria de realismo<br>• Adicionar 4-6 semanas de refinamento |
| **Falha em atingir KPIs (Mês 18)** | MÉDIA | Estender Fase 1 em 12m | • Tracking proativo (mensal)<br>• Ajustes em tactics se KPI degradar |

### Contingências de Budget

- **Buffer**: 15% adicional ($322k) para imprevistos
- **Cortes possíveis** (se necessário):
  - Reduzir tipos de honeypots (10 → 7): Economia $20k
  - Adiar ML para Sprint 4: Economia $40k
  - Usar consultores part-time vs FTE: Economia $100k

### Plano de Emergência (Contenção Breach)

Se QUALQUER violação de contenção ocorrer:

1. **Shutdown Imediato** (T+0)
   - Desligar fisicamente servidores da Camada 3
   - Isolar Camada 2 (desconectar de rede)
   - Notificar Direção Vértice em <15min

2. **Análise Forense** (T+1h a T+7d)
   - Contratar firma externa (pre-contratada: CrowdStrike ou Mandiant)
   - Root cause analysis completo
   - Relatório detalhado com recomendações

3. **Decisão GO/NO-GO** (T+14d)
   - Apresentar achados à Direção
   - Opções: (A) Corrigir e retomar, (B) Pausar Fase 1, (C) Cancelar projeto
   - Votação com unanimidade requerida para continuar

4. **Remediação** (Se aprovado, T+30d a T+90d)
   - Implementar correções (ex: upgrade de firewall, redesign de isolamento)
   - Re-testar com red team
   - Só retomar operação após 100% validação

---

## CRITÉRIOS DE SUCESSO GLOBAL (24 MESES)

### Sucesso Técnico
- [ ] Sistema operou 24 meses com ZERO incidentes de contenção
- [ ] Todos os 12 KPIs de Fase 1 atingidos (ver seção anterior)
- [ ] Red team em blind test não detectou decepção (taxa de detecção ≤5%)
- [ ] Inteligência gerada foi consumida por SOC e resultou em ≥3 ações defensivas bem-sucedidas na rede de produção

### Sucesso Operacional
- [ ] Equipe HITL operando 24/7 com ≥3 operadores certificados
- [ ] Tempo médio de análise forense ≤ 4h
- [ ] Uptime do sistema ≥ 99.9% (excluindo manutenções planejadas)
- [ ] 100% de decisões HITL auditadas em blockchain (sem gaps)

### Sucesso de Segurança
- [ ] Zero violações de data diode (física ou lógica)
- [ ] Zero ações não autorizadas (sem bypass de HITL)
- [ ] Taxa de falsos positivos em atribuição = 0% (auditoria manual de 100% dos casos)
- [ ] Pentests trimestrais (4x total) validaram isolamento

### Sucesso Científico/Inteligência
- [ ] ≥15 TTPs únicos de APTs identificados e documentados
- [ ] ≥100 amostras de malware capturadas e catalogadas
- [ ] ≥1 vulnerabilidade 0-day descoberta e reportada responsavelmente
- [ ] Geração de ≥50 relatórios de inteligência acionáveis para SOC

### Sucesso Documental
- [ ] ≥500 páginas de documentação técnica (network diagrams, runbooks, playbooks)
- [ ] ≥200 páginas de relatórios de inteligência (TTPs, IoCs, análises forenses)
- [ ] ≥100 páginas de documentação de compliance (LGPD, legal, auditoria)
- [ ] Apresentações trimestrais para Direção Vértice (4x)

---

## APROVAÇÃO E GATES DE GOVERNANÇA

### Aprovações Requeridas

**Início de Sprint 1** (Mês 1):
- [ ] Direção Vértice (unanimidade)
- [ ] Budget aprovado ($2.152M + $322k buffer)
- [ ] Legal counsel review de framework legal
- [ ] Arquiteto de segurança sênior sign-off em design

**Progressão entre Sprints**:
- [ ] Todos os critérios de GATE do sprint anterior atingidos
- [ ] Review de 2 membros da Direção (rotating pair)
- [ ] Post-mortem de lessons learned do sprint
- [ ] Atualização de documentação

**Checkpoint Mês 18** (Gate Intermediário):
- [ ] Auditoria independente (3rd party) aprovada
- [ ] ≥70% dos KPIs de Fase 1 atingidos
- [ ] Zero incidentes críticos em 18 meses
- [ ] Votação Direção Vértice (maioria simples para continuar)

**Gate Final Mês 24** (Progressão para Fase 2):
- [ ] 100% dos KPIs de Fase 1 atingidos
- [ ] Auditoria independente final aprovada
- [ ] Framework legal validado por counsel
- [ ] Seguro cyber para Fase 2 aprovado
- [ ] **Votação Direção Vértice (UNANIMIDADE obrigatória)**

### Processo de Decisão Gate Fase 2

1. **Compilação de Relatório** (Mês 23-24)
   - Relatório técnico completo (500+ páginas)
   - Evidências de todos os KPIs atingidos
   - Análise de riscos residuais
   - Proposta detalhada de Fase 2

2. **Auditoria Independente** (Mês 24, 6-8 semanas)
   - Firma especializada (pre-selecionada: Deloitte Cyber ou similar)
   - Escopo: Validação de todos os claims do relatório
   - Entrega: Opinion letter + recomendações

3. **Revisão por Counsel** (Mês 24, 4 semanas)
   - Framework legal de Fase 2 (ações defensivas)
   - Compliance com LGPD, Marco Civil, leis internacionais
   - Seguro cyber adequado

4. **Apresentação à Direção** (Mês 24, semana final)
   - 3 sessões de 4h cada (total 12h de debate)
   - Dia 1: Apresentação técnica + Q&A
   - Dia 2: Riscos legais/éticos + framework de mitigação
   - Dia 3: Deliberação + votação

5. **Votação** (Mês 24, última sessão)
   - Requer presença de 100% da Direção
   - Votação nominal (cada membro justifica voto)
   - **Unanimidade obrigatória** para progressão
   - Se 1+ voto negativo: Fase 2 cancelada ou adiada

6. **Outcomes Possíveis**:
   - **Aprovado (unanimidade)**: Iniciar planejamento de 6 meses para Fase 2
   - **Adiado**: Estender Fase 1 por 12 meses + re-avaliar
   - **Cancelado**: Manter Fase 1 indefinidamente (coleta passiva apenas)
   - **Pivotar**: Transformar em projeto de pure threat intel (sem decepção ativa)

---

## COMUNICAÇÃO E REPORTING

### Cadência de Updates

**Para Direção Vértice**:
- **Semanal**: Email status (5 bullet points, <250 palavras)
- **Mensal**: Relatório executivo (10 páginas, métricas + highlights)
- **Trimestral**: Apresentação presencial (1h, slides + Q&A)
- **Ad-hoc**: Alertas críticos (ex: red line cruzada) em <15min

**Para Equipe Técnica**:
- **Diário**: Stand-up (15min, virtual ou presencial)
- **Semanal**: Sprint review (1h, demos + retrospective)
- **Bi-semanal**: Technical deep-dive (2h, arquitetura/código)

**Para SOC (Consumidores de Inteligência)**:
- **Diário**: Alertas automáticos (CANDI → SOC dashboard)
- **Semanal**: Relatório de inteligência (TTPs + IoCs + recomendações)
- **Mensal**: Reunião de review (feedback sobre acionabilidade)

### Templates de Reporting

```markdown
# Relatório Mensal - Projeto Tecido Reativo
**Mês**: [X] | **Sprint**: [Y] | **Status**: [GREEN/YELLOW/RED]

## Executive Summary (3 frases)
[Principais conquistas do mês]

## Métricas de KPIs
| KPI | Target | Atual | Status |
|-----|--------|-------|--------|
| TTPs identificados | ≥15 | [X] | 🟢/🟡/🔴 |
| Malware samples | ≥100 | [X] | 🟢/🟡/🔴 |
| ... | ... | ... | ... |

## Destaques Técnicos
- [Conquista significativa 1]
- [Conquista significativa 2]
- [Inteligência de alto valor gerada]

## Riscos e Bloqueadores
- [Risco/bloqueio 1 + mitigação]
- [Risco/bloqueio 2 + mitigação]

## Próximos Passos (30 dias)
- [ ] Milestone 1
- [ ] Milestone 2
- [ ] Milestone 3

## Solicitações à Direção
- [Se aplicável: decisões, recursos, aprovações]
```

---

## ANEXOS

### Anexo A: Stack Tecnológico Completo

**Camada 3 (Ilha de Sacrifício)**:
- Cowrie (SSH/Telnet honeypot)
- DVWA (Vulnerable Web App)
- Dionaea (Malware capture honeypot)
- Conpot (Industrial SCADA honeypot)
- PostgreSQL + fake data (Database honeypot)
- Postfix + fake inbox (Email honeypot)
- Custom fake APIs (MAXIMUS-specific)

**Camada 2 (Orquestração/Análise)**:
- CANDICore (custom Python/FastAPI)
- Cuckoo Sandbox (malware analysis)
- MISP (threat intel platform)
- ELK Stack (logging/SIEM)
- Hyperledger Fabric (blockchain audit)
- Grafana + Prometheus (monitoring)
- Next.js + React (HITL console)

**Camada 1 (Produção)**:
- MAXIMUS services (TIG, ESGT, MEA, MCEA, etc)
- Data Diode (hardware - Owl DCGS)

**Infrastructure**:
- VMware vSphere (hypervisor)
- Terraform + Ansible (IaC)
- Palo Alto PA-5450 (NGFW)
- Cisco Catalyst 9000 (switches)
- Dell EMC Isilon (WORM storage)

### Anexo B: Fornecedores e Vendors

| Categoria | Vendor | Produto | Custo Estimado |
|-----------|--------|---------|----------------|
| Data Diode | Owl Cyber Defense | DCGS-10G | $45k |
| NGFW | Palo Alto Networks | PA-5450 | $120k each |
| Servers | Dell | PowerEdge R750 | $8k each |
| Storage | Dell EMC | Isilon F800 | $15k |
| Threat Intel | AlienVault | OTX (free) + USM | $50k/ano |
| Malware Analysis | VirusTotal | API Enterprise | Included TI |
| Auditoria | Deloitte Cyber | Security Audit | $150k |
| Legal | [TBD Counsel] | Compliance Review | $50k |

### Anexo C: Referências Bibliográficas

1. [Paper Viabilidade](/home/juan/Documents/Análise de Viabilidade: Arquitetura de Decepção Ativa e Contra-Inteligência Automatizada.md)
2. [Blueprint Técnico](./reactive-fabric-blueprint.md)
3. [Doutrina Vértice](../../.claude/DOUTRINA_VERTICE.md)
4. MITRE ATT&CK Framework (https://attack.mitre.org)
5. NIST Cybersecurity Framework (https://www.nist.gov/cyberframework)
6. "The Art of Deception" - Kevin Mitnick
7. "Intelligence-Driven Computer Network Defense" - NSA

---

## CONCLUSÃO: O MAPA PARA O ABISMO

Este roadmap não é uma jornada para o sucesso garantido. É um **mapa meticuloso para caminhar na beira de um abismo**, onde cada passo é validado, cada decisão auditada, cada risco mitigado com extrema disciplina.

### Os Três Pilares do Roadmap

**Progressão Condicional**: Não há deadlines fixos que sacrificam segurança. Cada gate é absoluto. Se Sprint 1 falhar em validação de isolamento, Sprint 2 não inicia. Período.

**Validação Tripla**: Todo componente crítico é testado de 3 formas — automática (CI/CD), humana (code review), e adversarial (red team). Redundância não é desperdício, é sobrevivência.

**Humildade Operacional**: Assumimos que falharemos. Por isso, temos kill-switches, audit logs imutáveis, HITL obrigatório. Não confiamos em nossa perfeição, confiamos em nossos sistemas de detecção de imperfeição.

### Para a Equipe de Execução

Vocês não estão construindo apenas software. Estão construindo um **instrumento científico** que será estudado por décadas. Cada commit, cada decisão de design, cada linha de log será analisada por pesquisadores em 2050 que perguntarão: "Como eles equilibraram o poder da automação com a responsabilidade da supervisão humana?"

A resposta está neste roadmap. Sigam-no com a disciplina que a Doutrina Vértice exige. Quando chegarem ao Mês 24 e apresentarem 100% dos KPIs atingidos, com zero incidentes de contenção, vocês terão provado algo histórico: que é possível fazer contra-inteligência automatizada de forma segura e ética.

Mas se, em qualquer momento, uma red line for cruzada — parem. Não racionalizem. Não contornem. **Parem**. Porque o custo de um containment breach não se mede em dólares, se mede na confiança que depositaram em vocês.

---

**Aprovado para Execução**: [PENDENTE VOTAÇÃO DIREÇÃO]  
**Data de Promulgação**: 2025-10-12  
**Versão**: 1.0.0  
**Próxima Revisão**: Após conclusão de Sprint 1 (2026-02-01)

---

*"Um roadmap não é uma promessa de sucesso. É um contrato de disciplina."*  
— Filosofia de Execução, Doutrina Vértice

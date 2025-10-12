# BLUEPRINT 01: OFFENSIVE SECURITY TOOLKIT
## World-Class AI-Driven Penetration Testing Arsenal

**Status**: DESIGN | **Priority**: CRITICAL | **Version**: 1.0  
**Date**: 2025-10-11 | **Author**: MAXIMUS Team

---

## EXECUTIVE SUMMARY

Este blueprint define a arquitetura completa do arsenal ofensivo do Projeto MAXIMUS, projetado para operações de penetration testing de classe mundial, conduzidas por IA com supervisão humana (HOTL - Human-on-the-Loop). A arquitetura é baseada em sistemas multiagente especializados, integrando capacidades autônomas com frameworks éticos rigorosos.

### Ferramentas Existentes (Inventário)
✅ **Exploit Database** (`wargaming_crisol/exploit_database.py`)
✅ **Exploits CWE** (89-SQLi, 22-Path Traversal, 78-CMDi, 79-XSS, 352-CSRF, 434-Upload, 611-XXE, 918-SSRF)
✅ **Web Attack Service** (ZAP wrapper, AI Copilot)
✅ **Network Recon Service** (basic network reconnaissance)
✅ **Nmap Service** (port scanning and service detection)
✅ **OSINT Service** (open source intelligence gathering)
✅ **Google OSINT Service** (specialized Google dorking)
✅ **Social Engineering Service** (phishing campaigns)
✅ **C2 Orchestration Service** (command and control infrastructure)

### Gaps Identificados (Pendentes)
❌ **AEG Engine** (Automatic Exploit Generation para N-day)
❌ **RL Post-Exploitation Agent** (Reinforcement Learning para movimentação lateral)
❌ **Credential Harvester** (mimikatz-like capability)
❌ **Adversarial ML Evasion** (bypass de detectores ML)
❌ **Traffic Shaping Module** (behavioral mimicry para C2)
❌ **LLM-Powered Spear Phishing** (geração contextual automatizada)
❌ **Vulnerability Fuzzer** (descoberta de 0-day)
❌ **Autonomous Recon Orchestrator** (correlação OSINT multi-fonte)
❌ **Payload Obfuscator** (evasão de AV/EDR)

---

## ARQUITETURA PROPOSTA

### Paradigma: Sistema Multiagente Orquestrado (MAS)

```
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR AGENT (Commander)                │
│              LLM: GPT-4o / Claude 3.5 Sonnet                   │
│         - Task Decomposition                                    │
│         - HOTL Interface                                        │
│         - Risk Assessment                                       │
└──────────┬──────────────────────────────────────────────┬───────┘
           │                                              │
           ▼                                              ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│  RECONNAISSANCE AGENT     │              │   EXPLOITATION AGENT     │
│  - OSINT Correlation      │              │   - N-day Exploit Gen    │
│  - Active Scanning        │              │   - 0-day Fuzzing        │
│  - Service Enumeration    │              │   - Payload Delivery     │
│  - Vuln Mapping           │              │   - AV/EDR Evasion       │
└──────────┬────────────────┘              └─────────┬────────────────┘
           │                                         │
           ▼                                         ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ POST-EXPLOITATION AGENT   │              │   ANALYSIS AGENT         │
│  - RL-based Navigation    │              │   - Result Processing    │
│  - Lateral Movement       │              │   - Report Generation    │
│  - Privilege Escalation   │              │   - Knowledge Base       │
│  - Data Exfiltration      │              │   - Learning System      │
└───────────────────────────┘              └──────────────────────────┘
```

---

## COMPONENTES DETALHADOS

### 1. ORCHESTRATOR AGENT (Commander)

**Propósito**: Coordenação estratégica de toda operação de pentest.

**Modelo de IA**: LLM de última geração (GPT-4o, Claude 3.5 Sonnet, ou Qwen3-32B fine-tuned)

**Responsabilidades**:
- Receber objetivo de alto nível do operador humano
- Decompor em Task Coordination Graph (TCG)
- Delegar subtarefas a agentes especializados
- Apresentar descobertas e propostas ao operador
- Implementar pontos de controle HOTL obrigatórios

**Pontos de Controle HOTL** (NÃO NEGOCIÁVEIS):
1. ✋ Antes de lançar qualquer exploit
2. ✋ Após exploração bem-sucedida (antes de pós-exploração)
3. ✋ Antes de ações de DoS/instabilidade
4. ✋ Antes de exfiltração de dados sensíveis/PII

**Tecnologias**:
- LangChain/LlamaIndex para orquestração LLM
- Model Context Protocol (MCP) para integração de ferramentas
- Task Graph representado como DAG (Directed Acyclic Graph)

**Arquivos a Criar**:
```
backend/services/offensive_orchestrator/
├── __init__.py
├── orchestrator_agent.py       # Agente principal
├── task_graph.py               # DAG de tarefas
├── hotl_interface.py           # Interface Human-on-the-Loop
├── risk_assessor.py            # Avaliação de risco de ações
├── models.py                   # Schemas Pydantic
└── tests/
    └── test_orchestrator.py
```

---

### 2. RECONNAISSANCE AGENT

**Propósito**: Mapear superfície de ataque com correlação inteligente.

**Modelo de IA**: LLM para processamento de dados OSINT + heurísticas tradicionais

**Responsabilidades**:
- Coletar dados de múltiplas fontes OSINT
- Correlacionar eventos discretos em hipóteses de ataque
- Executar scanning ativo (Nmap, Nikto, etc.)
- Mapear tecnologias e versões
- Identificar vulnerabilidades conhecidas (N-day)

**Capacidades Novas (Gap)**:
- **Autonomous Recon Orchestrator**: Integração de múltiplas fontes OSINT com correlação contextual em tempo real
  - Shodan API
  - Certificate Transparency Logs
  - DNS enumeration (Amass, SubFinder)
  - GitHub dorking (leaked secrets)
  - Pastebin monitoring
  - Dark web intel (quando aplicável)

**Arquitetura de Correlação**:
```python
# Exemplo: Detectar novo servidor CI/CD exposto
eventos = [
    {"fonte": "CT_Logs", "dado": "jenkins.target.com"},
    {"fonte": "AWS_IP_Enum", "dado": "54.123.45.67 → jenkins.target.com"},
    {"fonte": "Nmap", "dado": "54.123.45.67:8080 open (HTTP)"}
]

# LLM infere contexto
inferencia = llm.correlate(eventos)
# Output: "Novo servidor Jenkins desprotegido. Prioridade: ALTA. 
#          Recomendação: Testar default credentials admin/admin"
```

**Integração com Ferramentas Existentes**:
- ✅ `network_recon_service` (expandir)
- ✅ `nmap_service` (integrar via MCP)
- ✅ `osint_service` + `google_osint_service` (consolidar)

**Arquivos a Criar**:
```
backend/services/reconnaissance_agent/
├── __init__.py
├── recon_orchestrator.py       # Orquestrador principal
├── osint_correlator.py         # Correlação multi-fonte
├── active_scanner.py           # Wrapper para Nmap/Nikto
├── vuln_mapper.py              # CVE matching
├── asset_inventory.py          # Inventário dinâmico
└── tests/
```

---

### 3. EXPLOITATION AGENT (Híbrido)

**Propósito**: Obter acesso inicial através de exploração de vulnerabilidades.

**Modelo de IA**: 
- LLM para geração de código de exploit (N-day)
- Análise estática/simbólica para descoberta (0-day)
- Adversarial ML para evasão

**Responsabilidades**:
- Gerar exploits para vulnerabilidades conhecidas (N-day)
- Fuzzing para descoberta de 0-day (opcional/pesquisa)
- Obfuscação de payloads para evasão de AV/EDR
- Entrega de payload adaptativa

**Capacidades Novas (Gap)**:

#### 3.1 AEG Engine (Automatic Exploit Generation)
**Arquitetura**:
```python
# Baseado em AIxCC + LLM
class AEGEngine:
    def __init__(self):
        self.static_analyzer = StaticAnalyzer()  # Ghidra/IDA integration
        self.symbolic_executor = SymbolicExecutor()  # angr/KLEE
        self.llm_codegen = LLMCodeGenerator()  # GPT-4o
    
    def generate_exploit(self, vuln: Vulnerability) -> Exploit:
        # 1. Análise estática identifica natureza da vuln
        vuln_params = self.static_analyzer.analyze(vuln.code)
        
        # 2. LLM gera código de exploit guiado por parâmetros
        exploit_code = self.llm_codegen.generate(
            vuln_type=vuln_params.type,  # buffer overflow, SQLi, etc.
            constraints=vuln_params.constraints,
            target_arch=vuln.target_arch
        )
        
        # 3. Validação simbólica
        if self.symbolic_executor.validate(exploit_code):
            return Exploit(code=exploit_code, confidence=0.95)
        else:
            return self.refine_exploit(exploit_code)  # Iteração
```

**Fontes de Vulnerabilidades**:
- CVE databases (MITRE, NVD)
- ExploitDB integration
- GitHub Advisory Database
- ✅ `wargaming_crisol/exploit_database.py` (expandir)

#### 3.2 Payload Obfuscator (Evasão AV/EDR)
**Técnicas**:
- Polimorfismo (geração de código equivalente)
- Encryption/packing
- Syscall direct invocation
- AMSI bypass techniques
- ETW patching
- Adversarial ML perturbations

**Arquitetura**:
```python
class PayloadObfuscator:
    def obfuscate(self, payload: bytes, target_av: str) -> bytes:
        # 1. Detectar assinaturas conhecidas
        signatures = self.signature_detector.scan(payload)
        
        # 2. Aplicar transformações adversariais
        obfuscated = self.adversarial_transformer.perturb(
            payload, 
            avoid_signatures=signatures,
            target_model=self.av_models[target_av]  # White-box se possível
        )
        
        # 3. Validar evasão (teste em sandbox)
        if self.test_evasion(obfuscated, target_av):
            return obfuscated
        else:
            return self.obfuscate(payload, target_av)  # Recursivo
```

**Integração com Ferramentas Existentes**:
- ✅ `wargaming_crisol/exploits/` (expandir com obfuscação)
- ✅ `web_attack_service` (integrar AEG)

**Arquivos a Criar**:
```
backend/services/exploitation_agent/
├── __init__.py
├── aeg_engine.py               # Automatic Exploit Generation
├── static_analyzer.py          # Ghidra/radare2 wrapper
├── symbolic_executor.py        # angr wrapper
├── llm_codegen.py              # LLM para geração de exploit
├── payload_obfuscator.py       # Evasão AV/EDR
├── adversarial_ml.py           # Perturbações adversariais
├── delivery_module.py          # Entrega de payload
└── tests/
```

---

### 4. POST-EXPLOITATION AGENT (RL-based)

**Propósito**: Navegação autônoma na rede comprometida.

**Modelo de IA**: Reinforcement Learning (A2C, PPO)

**Responsabilidades**:
- Movimentação lateral
- Escalonamento de privilégios
- Coleta de credenciais
- Persistência (quando autorizado)
- Exfiltração de dados (quando autorizado)

**Arquitetura RL**:

```python
# Baseado no framework Raijū
class PostExploitationAgent:
    def __init__(self):
        self.env = CompromisedNetwork()  # Environment
        self.policy = A2CPolicy()  # Actor-Critic
        self.action_space = ActionSpace()  # Metasploit modules
    
    # Estado: representação do ambiente comprometido
    state = {
        "current_host": "10.1.1.50",
        "privilege_level": "low",
        "credentials": ["user:pass123"],
        "accessible_hosts": ["10.1.1.51", "10.1.1.52"],
        "discovered_assets": ["fileserver", "dc"]
    }
    
    # Espaço de ações mapeado para módulos reais
    action_space = [
        "mimikatz_dump",          # Extrair credenciais
        "lateral_move_ssh",       # SSH com credenciais
        "lateral_move_psexec",    # PSExec (Windows)
        "privesc_kernel_exploit", # Explorar vulnerabilidade kernel
        "discover_network",       # Scan sub-rede
        "exfiltrate_data"         # Copiar dados (HOTL required)
    ]
    
    # Função de recompensa
    def reward_function(self, action, result):
        if action == "gain_admin" and result.success:
            return +100
        elif action == "lateral_move" and result.new_host:
            return +50
        elif result.detected:
            return -500  # Penalidade alta por detecção
        elif result.no_progress:
            return -10
```

**Treinamento**:
- Ambiente de simulação: Cyber Range sintético
- Opponent: Blue Team Agent (sistema de defesa)
- Curriculum Learning: aumentar complexidade gradualmente

**Integração com Ferramentas Existentes**:
- ✅ `c2_orchestration_service` (para C2 management)

**Arquivos a Criar**:
```
backend/services/postexploit_agent/
├── __init__.py
├── rl_agent.py                 # Agente RL principal
├── environment.py              # Ambiente de simulação
├── action_executor.py          # Executor de ações (Metasploit wrapper)
├── credential_harvester.py     # Mimikatz-like
├── lateral_movement.py         # Técnicas de movimentação
├── privilege_escalation.py     # Técnicas de privesc
└── tests/
```

---

### 5. ANALYSIS AGENT

**Propósito**: Processar resultados e gerenciar conhecimento.

**Modelo de IA**: LLM para sumarização e análise

**Responsabilidades**:
- Processar outputs de outros agentes
- Avaliar sucesso/falha de ações
- Atualizar Task Graph
- Gerar relatórios técnicos
- Atualizar Experience Knowledge Base (EKB)
- Aprendizado contínuo

**Capacidades**:
- **Root Cause Analysis**: Identificar por que exploit falhou
- **Success Pattern Recognition**: Aprender táticas eficazes
- **Report Generation**: Relatórios técnicos automáticos no padrão PTES

**Arquivos a Criar**:
```
backend/services/analysis_agent/
├── __init__.py
├── result_processor.py         # Processamento de resultados
├── report_generator.py         # Geração de relatórios PTES
├── knowledge_base.py           # EKB (Experience Knowledge Base)
├── learning_module.py          # Aprendizado contínuo
└── tests/
```

---

## COMPONENTES DE INFRAESTRUTURA

### 6. TRAFFIC SHAPING MODULE (C2 Stealth)

**Propósito**: Tornar tráfego C2 indistinguível de tráfego legítimo.

**Técnica**: Behavioral Mimicry usando IA

**Arquitetura**:
```python
class TrafficShaper:
    def __init__(self, target_app: str):
        # target_app: "teams", "slack", "windows_update", etc.
        self.baseline_analyzer = BaselineAnalyzer()
        self.packet_generator = AdaptivePacketGen()
    
    def shape_c2_traffic(self, c2_data: bytes) -> PacketStream:
        # 1. Analisar tráfego legítimo do app alvo
        baseline = self.baseline_analyzer.profile(target_app)
        
        # 2. Gerar stream que imita estatísticas
        shaped = self.packet_generator.generate(
            data=c2_data,
            target_packet_size_dist=baseline.packet_sizes,
            target_inter_arrival_time=baseline.iat,
            target_entropy=baseline.entropy,
            target_protocol=baseline.protocol
        )
        
        return shaped
```

**Features a Imitar**:
- Distribuição de tamanho de pacotes
- Inter-arrival time (IAT)
- Entropia do payload criptografado
- Padrões de handshake TLS
- Frequência de beaconing

**Integração**:
- ✅ `c2_orchestration_service` (adicionar módulo de shaping)

---

### 7. LLM-POWERED SPEAR PHISHING ENGINE

**Propósito**: Geração de campanhas de spear phishing contextuais em escala.

**Modelo de IA**: LLM + GAN (deepfake de voz/imagem quando necessário)

**Pipeline**:
```
OSINT → Contexto → Prompt Engineering → LLM Generation → Quality Check → Envio
```

**Arquitetura**:
```python
class SpearPhishingEngine:
    def __init__(self):
        self.context_builder = ContextBuilder()
        self.llm_generator = LLMGenerator()
        self.deepfake_gen = DeepfakeGenerator()  # Opcional
    
    def generate_campaign(self, targets: List[Target]) -> Campaign:
        emails = []
        for target in targets:
            # 1. Construir contexto rico
            context = self.context_builder.build(target)
            # context: projetos atuais, gerente, colegas, eventos recentes
            
            # 2. Gerar email personalizado
            email = self.llm_generator.generate_email(
                sender=context.manager,
                recipient=target.email,
                topic=context.current_project,
                urgency="high",
                action="review document",
                malicious_link=self.payload_link
            )
            
            # 3. Opcional: Gerar voicemail deepfake
            if target.value == "high":
                voice = self.deepfake_gen.clone_voice(context.manager)
                voicemail = voice.generate_message(
                    text="Hi {name}, please review the document I sent"
                )
                email.attach_voicemail(voicemail)
            
            emails.append(email)
        
        return Campaign(emails=emails)
```

**Integração**:
- ✅ `social_eng_service` (expandir com LLM)
- ✅ `osint_service` (fonte de contexto)

**Arquivos a Criar**:
```
backend/services/spearphish_engine/
├── __init__.py
├── context_builder.py          # Construir contexto de alvo
├── llm_generator.py            # Geração de email
├── deepfake_generator.py       # GAN para voz/imagem
├── campaign_manager.py         # Gerenciar campanhas
└── tests/
```

---

## INTEGRAÇÃO E COMUNICAÇÃO

### Agent Communication Protocol (ACP)

**Formato**: JSON estruturado sobre message queue (RabbitMQ/Redis)

**Esquema de Mensagem**:
```json
{
  "message_id": "uuid-v4",
  "timestamp": "2025-10-11T10:30:00Z",
  "from_agent": "reconnaissance",
  "to_agent": "orchestrator",
  "message_type": "TASK_RESULT",
  "priority": "high",
  "payload": {
    "task_id": "recon-001",
    "status": "completed",
    "findings": [
      {
        "type": "vulnerable_service",
        "host": "10.1.1.50",
        "port": 8080,
        "service": "Jenkins 2.319",
        "cve": ["CVE-2021-21642"],
        "severity": "critical",
        "confidence": 0.95
      }
    ],
    "recommendations": [
      "Attempt exploit CVE-2021-21642 for RCE"
    ]
  }
}
```

---

## MÉTRICAS DE SUCESSO

### Métricas de Performance
- **Time to Compromise**: Tempo médio para obter acesso inicial
- **Coverage**: % de superfície de ataque mapeada
- **Exploit Success Rate**: Taxa de sucesso de exploits gerados
- **Evasion Rate**: % de payloads que evitam AV/EDR
- **Lateral Movement Depth**: Profundidade média de movimentação lateral

### Métricas de Qualidade
- **False Positive Rate**: Taxa de vulnerabilidades falsas reportadas
- **Report Quality Score**: Avaliação humana de relatórios gerados
- **HOTL Interruptions**: Número de vezes que humano teve que intervir corretivamente

### Métricas Éticas
- **Unauthorized Action Attempts**: Tentativas bloqueadas pelo HOTL
- **Collateral Damage Incidents**: Instabilidade/DoS não intencional
- **Scope Violations**: Tentativas de atacar fora do escopo

---

## FRAMEWORKS DE CONFORMIDADE

### MITRE ATT&CK Mapping
Todas as ações devem ser mapeadas para técnicas ATT&CK:
- Reconnaissance: T1595, T1592, T1590
- Initial Access: T1566 (Phishing), T1210 (Exploit Public-Facing)
- Execution: T1059 (Command Line)
- Privilege Escalation: T1068 (Exploitation), T1548 (Abuse Elevation)
- Lateral Movement: T1021 (Remote Services), T1078 (Valid Accounts)
- Exfiltration: T1048 (Exfiltration Over Alternative Protocol)

### Conformidade com Doutrina MAXIMUS
- ✅ **NO MOCK**: Todas ferramentas são funcionais e testadas
- ✅ **QUALITY-FIRST**: 100% type hints, docstrings, testes
- ✅ **HOTL Compliance**: Supervisão humana obrigatória em ações críticas
- ✅ **Ethical AI**: Conformidade com princípios éticos L1/L2

---

## PRÓXIMOS PASSOS

Ver **ROADMAP-01-OFFENSIVE-TOOLKIT.md** para sequência de implementação.
Ver **IMPLEMENTATION-PLAN-01-OFFENSIVE.md** para plano detalhado de execução.

---

**Assinatura**: MAXIMUS Team  
**Aprovação**: Pending Human Review  
**Versão Blueprint**: 1.0 - DRAFT

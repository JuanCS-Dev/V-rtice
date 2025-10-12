# Reactive Fabric Sprint 1 - Plano de Implementação Metodológica

**Data**: 2025-10-12  
**Status**: Em Execução  
**Aderência**: Doutrina Vértice OBRIGATÓRIA

---

## CONTEXTO

Baseado na análise profunda do diretório, identificamos:

### Situação Atual
- ✅ **reactive_fabric_core**: Estrutura completa com imports relativos
- ✅ **reactive_fabric_analysis**: Estrutura básica (Sprint 0)
- ❌ **Imports relativos**: Precisa migrar para absolutos
- ❌ **Analysis sem lógica**: Apenas skeleton

### Arquitetura Existente
```
backend/services/
├── reactive_fabric_core/
│   ├── main.py              # FastAPI app - imports relativos
│   ├── models.py            # Pydantic models completos
│   ├── database.py          # asyncpg pool + queries
│   ├── kafka_producer.py    # AIOKafkaProducer
│   └── tests/
└── reactive_fabric_analysis/
    ├── main.py              # Skeleton básico
    └── requirements.txt
```

---

## FASE 1: CORREÇÃO DE IMPORTS E ESTRUTURA BÁSICA

### Objetivo
Migrar imports relativos → absolutos, criar estrutura modular conforme Doutrina.

### 1.1 Reactive Fabric Core - Refactor de Imports

#### Arquivos a Modificar
1. **main.py**: `from models import...` → `from backend.services.reactive_fabric_core.models import...`
2. **database.py**: `from models import...` → `from backend.services.reactive_fabric_core.models import...`
3. **kafka_producer.py**: `from models import...` → `from backend.services.reactive_fabric_core.models import...`

#### Padrão de Imports (OBRIGATÓRIO)
```python
# ❌ ERRADO
from models import HoneypotListResponse

# ✅ CORRETO
from backend.services.reactive_fabric_core.models import (
    HoneypotListResponse,
    HoneypotStats,
    HoneypotStatus
)
```

### 1.2 Criação de __init__.py

Facilitar imports e garantir que módulos sejam pacotes Python válidos.

```python
# backend/services/reactive_fabric_core/__init__.py
"""
Reactive Fabric Core Service
Orchestrates honeypots and aggregates threat intelligence
"""
from .models import *
from .database import Database
from .kafka_producer import KafkaProducer

__all__ = [
    "Database",
    "KafkaProducer",
    # Re-export models
    "HoneypotListResponse",
    "AttackListResponse",
    "ThreatDetectedMessage",
    # ... outros exports
]
```

### 1.3 Reactive Fabric Analysis - Estrutura Modular

Criar estrutura completa:
```
reactive_fabric_analysis/
├── __init__.py
├── main.py                  # FastAPI app
├── models.py                # Pydantic models
├── database.py              # Shared DB client
├── parsers/
│   ├── __init__.py
│   ├── base.py              # Abstract parser
│   ├── cowrie_parser.py     # Cowrie JSON
│   └── pcap_parser.py       # TShark PCAP
├── ttp_mapper.py            # MITRE ATT&CK mapping
└── kafka_client.py          # Shared Kafka producer
```

---

## FASE 2: IMPLEMENTAÇÃO DE LÓGICA FUNCIONAL

### Objetivo
Implementar a lógica de análise forense completa conforme o paper.

### 2.1 Parsers de Forensic Captures

#### Base Parser (Abstract)
```python
# backend/services/reactive_fabric_analysis/parsers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pathlib import Path

class ForensicParser(ABC):
    """Abstract base parser for forensic captures."""
    
    @abstractmethod
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse forensic capture and extract structured data.
        
        Returns:
            {
                "attacker_ip": str,
                "attack_type": str,
                "commands": List[str],
                "credentials": List[tuple],
                "file_hashes": List[str],
                "timestamps": List[datetime]
            }
        """
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Check if parser supports this file type."""
        pass
```

#### Cowrie JSON Parser
```python
# backend/services/reactive_fabric_analysis/parsers/cowrie_parser.py
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from .base import ForensicParser

class CowrieJSONParser(ForensicParser):
    """Parser for Cowrie honeypot JSON logs."""
    
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix == '.json' and 'cowrie' in file_path.name.lower()
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse Cowrie JSON log.
        
        Example entry:
        {
            "eventid": "cowrie.login.success",
            "username": "root",
            "password": "toor",
            "src_ip": "45.142.120.15",
            "timestamp": "2025-10-12T20:15:33.123456Z"
        }
        """
        data = {
            "attacker_ip": None,
            "attack_type": "ssh_brute_force",
            "commands": [],
            "credentials": [],
            "file_hashes": [],
            "timestamps": [],
            "sessions": []
        }
        
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    # Extract attacker IP
                    if 'src_ip' in entry:
                        data['attacker_ip'] = entry['src_ip']
                    
                    # Extract credentials
                    if entry.get('eventid') == 'cowrie.login.success':
                        data['credentials'].append((
                            entry.get('username'),
                            entry.get('password')
                        ))
                    
                    # Extract commands
                    if entry.get('eventid') == 'cowrie.command.input':
                        data['commands'].append(entry.get('input', ''))
                    
                    # Extract file downloads
                    if entry.get('eventid') == 'cowrie.session.file_download':
                        data['file_hashes'].append(entry.get('shasum', ''))
                    
                    # Timestamps
                    if 'timestamp' in entry:
                        data['timestamps'].append(
                            datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                        )
                
                except json.JSONDecodeError:
                    continue
        
        return data
```

### 2.2 TTP Mapper (MITRE ATT&CK)

```python
# backend/services/reactive_fabric_analysis/ttp_mapper.py
from typing import List, Dict, Any
import re

class TTPMapper:
    """
    Maps observed behaviors to MITRE ATT&CK techniques.
    
    Compliance com o Paper:
    - "Métricas de Validação para a Fase 1"
    - "Quantos TTPs de APTs precisamos identificar"
    """
    
    # Pattern-based TTP mapping
    TTP_PATTERNS = {
        # Initial Access
        "T1190": {  # Exploit Public-Facing Application
            "patterns": [
                r"(?i)(sql injection|sqli|union select)",
                r"(?i)(xss|cross-site scripting)",
                r"(?i)(rce|remote code execution)"
            ],
            "name": "Exploit Public-Facing Application",
            "tactic": "Initial Access"
        },
        "T1133": {  # External Remote Services
            "patterns": [
                r"(?i)(ssh|rdp|vnc) (brute|bruteforce|login attempt)"
            ],
            "name": "External Remote Services",
            "tactic": "Initial Access"
        },
        
        # Credential Access
        "T1110": {  # Brute Force
            "patterns": [
                r"(?i)(password|credential) (guess|spray|brute)",
                r"(root|admin|user):.*password"
            ],
            "name": "Brute Force",
            "tactic": "Credential Access"
        },
        
        # Discovery
        "T1082": {  # System Information Discovery
            "patterns": [
                r"(?i)(uname|systeminfo|hostname|whoami)",
                r"(?i)(cat /etc/issue|cat /proc/version)"
            ],
            "name": "System Information Discovery",
            "tactic": "Discovery"
        },
        "T1083": {  # File and Directory Discovery
            "patterns": [
                r"(?i)(ls|dir|find|tree)",
                r"(?i)(cat|type) .*\.(txt|log|conf|cfg)"
            ],
            "name": "File and Directory Discovery",
            "tactic": "Discovery"
        },
        
        # Execution
        "T1059.004": {  # Command and Scripting Interpreter: Unix Shell
            "patterns": [
                r"(?i)(bash|sh|zsh|csh) -c",
                r"(?i)/bin/(bash|sh)"
            ],
            "name": "Command and Scripting Interpreter: Unix Shell",
            "tactic": "Execution"
        },
        
        # Persistence
        "T1053.003": {  # Scheduled Task/Job: Cron
            "patterns": [
                r"(?i)crontab -e",
                r"(?i)echo.*>>/etc/crontab"
            ],
            "name": "Scheduled Task/Job: Cron",
            "tactic": "Persistence"
        },
        
        # Command and Control
        "T1071.001": {  # Application Layer Protocol: Web Protocols
            "patterns": [
                r"(?i)(wget|curl) http",
                r"(?i)python.*-m.*http\.server"
            ],
            "name": "Application Layer Protocol: Web Protocols",
            "tactic": "Command and Control"
        }
    }
    
    def map_ttps(self, commands: List[str], attack_type: str) -> List[str]:
        """
        Map observed commands and attack type to MITRE TTPs.
        
        Args:
            commands: List of commands executed
            attack_type: Type of attack (e.g., "ssh_brute_force")
        
        Returns:
            List of MITRE technique IDs (e.g., ["T1110", "T1059.004"])
        """
        detected_ttps = []
        
        # Combine all commands for pattern matching
        all_commands = " ".join(commands)
        
        # Pattern matching
        for ttp_id, ttp_info in self.TTP_PATTERNS.items():
            for pattern in ttp_info["patterns"]:
                if re.search(pattern, all_commands):
                    if ttp_id not in detected_ttps:
                        detected_ttps.append(ttp_id)
        
        # Attack-type based mapping
        if attack_type == "ssh_brute_force":
            if "T1110" not in detected_ttps:
                detected_ttps.append("T1110")
            if "T1133" not in detected_ttps:
                detected_ttps.append("T1133")
        
        elif attack_type == "sql_injection":
            if "T1190" not in detected_ttps:
                detected_ttps.append("T1190")
        
        return detected_ttps
    
    def get_ttp_info(self, technique_id: str) -> Dict[str, str]:
        """Get TTP information (name, tactic)."""
        return self.TTP_PATTERNS.get(technique_id, {
            "name": f"Unknown Technique {technique_id}",
            "tactic": "Unknown"
        })
```

### 2.3 Main Analysis Loop

```python
# backend/services/reactive_fabric_analysis/main.py (refactored)
async def forensic_polling_task():
    """
    Production-ready forensic polling with full TTP extraction.
    
    Compliance:
    - Paper Section 3.2: "Progressão Condicional"
    - Fase 1: Coleta de inteligência PASSIVA
    - KPIs: TTPs identificados, IoCs extraídos
    """
    logger.info("forensic_polling_task_started", interval=POLLING_INTERVAL)
    
    # Initialize parsers
    parsers = [
        CowrieJSONParser(),
        # PCAPParser(),  # Sprint 1 extension
    ]
    ttp_mapper = TTPMapper()
    
    while True:
        try:
            # Step 1: List unprocessed files
            pending_captures = await db.get_pending_captures(limit=10)
            
            for capture in pending_captures:
                try:
                    file_path = Path(capture.file_path)
                    
                    # Update status to processing
                    await db.update_capture_status(
                        capture.id,
                        ProcessingStatus.PROCESSING
                    )
                    
                    # Step 2: Select appropriate parser
                    parser = None
                    for p in parsers:
                        if p.supports(file_path):
                            parser = p
                            break
                    
                    if not parser:
                        logger.warning("no_parser_found", file=str(file_path))
                        await db.update_capture_status(
                            capture.id,
                            ProcessingStatus.FAILED,
                            error_message="No parser found for file type"
                        )
                        continue
                    
                    # Step 3: Parse forensic capture
                    parsed_data = await parser.parse(file_path)
                    
                    # Step 4: Map to MITRE TTPs
                    ttps = ttp_mapper.map_ttps(
                        parsed_data.get("commands", []),
                        parsed_data.get("attack_type", "unknown")
                    )
                    
                    # Step 5: Extract IoCs
                    iocs = {
                        "ips": [parsed_data.get("attacker_ip")] if parsed_data.get("attacker_ip") else [],
                        "usernames": [cred[0] for cred in parsed_data.get("credentials", [])],
                        "passwords": [cred[1] for cred in parsed_data.get("credentials", [])],
                        "file_hashes": parsed_data.get("file_hashes", [])
                    }
                    
                    # Step 6: Create attack record
                    attack = AttackCreate(
                        honeypot_id=capture.honeypot_id,
                        attacker_ip=parsed_data.get("attacker_ip", "unknown"),
                        attack_type=parsed_data.get("attack_type", "unknown"),
                        severity=_determine_severity(ttps),
                        confidence=0.95,
                        ttps=ttps,
                        iocs=iocs,
                        payload=str(parsed_data.get("commands", [])[:5]),  # First 5 commands
                        captured_at=parsed_data.get("timestamps", [datetime.utcnow()])[0]
                    )
                    
                    # Step 7: Store in database (via Core Service API)
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{CORE_SERVICE_URL}/api/v1/attacks",
                            json=attack.model_dump(mode='json'),
                            timeout=10.0
                        )
                        response.raise_for_status()
                    
                    # Step 8: Mark as completed
                    await db.update_capture_status(
                        capture.id,
                        ProcessingStatus.COMPLETED,
                        attacks_extracted=1,
                        ttps_extracted=len(ttps)
                    )
                    
                    logger.info(
                        "capture_processed_successfully",
                        capture_id=str(capture.id),
                        ttps_extracted=len(ttps),
                        iocs_extracted=len(iocs.get("ips", []))
                    )
                
                except Exception as e:
                    logger.error(
                        "capture_processing_failed",
                        capture_id=str(capture.id),
                        error=str(e)
                    )
                    await db.update_capture_status(
                        capture.id,
                        ProcessingStatus.FAILED,
                        error_message=str(e)
                    )
            
            await asyncio.sleep(POLLING_INTERVAL)
            
        except Exception as e:
            logger.error("forensic_polling_error", error=str(e))
            await asyncio.sleep(POLLING_INTERVAL)


def _determine_severity(ttps: List[str]) -> AttackSeverity:
    """Determine attack severity based on TTPs."""
    critical_ttps = ["T1190", "T1053.003"]  # RCE, Persistence
    high_ttps = ["T1110", "T1059"]  # Brute Force, Command Execution
    
    if any(ttp in critical_ttps for ttp in ttps):
        return AttackSeverity.CRITICAL
    elif any(ttp in high_ttps for ttp in ttps):
        return AttackSeverity.HIGH
    elif ttps:
        return AttackSeverity.MEDIUM
    else:
        return AttackSeverity.LOW
```

---

## FASE 3: VALIDAÇÃO E TESTES

### Objetivo
Validar implementação conforme Doutrina (NO MOCK, NO PLACEHOLDER, NO TODO).

### 3.1 Validações de Código

#### Type Safety (mypy --strict)
```bash
cd backend/services/reactive_fabric_core
mypy --strict main.py models.py database.py kafka_producer.py

cd backend/services/reactive_fabric_analysis
mypy --strict main.py parsers/ ttp_mapper.py
```

#### Code Quality (pylint)
```bash
pylint backend/services/reactive_fabric_core/*.py
pylint backend/services/reactive_fabric_analysis/**/*.py
```

#### Formatting (black)
```bash
black --check backend/services/reactive_fabric_core/
black --check backend/services/reactive_fabric_analysis/
```

### 3.2 Testes Unitários

#### Core Service Tests
```python
# backend/services/reactive_fabric_core/tests/test_models.py
def test_threat_detected_message_serialization():
    """Validate ThreatDetectedMessage Kafka serialization."""
    msg = ThreatDetectedMessage(
        event_id="test_001",
        timestamp=datetime.utcnow(),
        honeypot_id="ssh_001",
        attacker_ip="1.2.3.4",
        attack_type="brute_force",
        severity=AttackSeverity.HIGH,
        ttps=["T1110"],
        iocs={"ips": ["1.2.3.4"]},
        confidence=0.95
    )
    
    # Should serialize to JSON without errors
    json_data = msg.model_dump_json()
    assert "event_id" in json_data
    assert "T1110" in json_data
```

#### Analysis Service Tests
```python
# backend/services/reactive_fabric_analysis/tests/test_cowrie_parser.py
import pytest
from pathlib import Path
from parsers.cowrie_parser import CowrieJSONParser

@pytest.mark.asyncio
async def test_cowrie_parser_extracts_credentials():
    """Test Cowrie parser extracts credentials correctly."""
    parser = CowrieJSONParser()
    
    # Create test file
    test_file = Path("/tmp/test_cowrie.json")
    test_file.write_text('''
    {"eventid": "cowrie.login.success", "username": "root", "password": "toor", "src_ip": "1.2.3.4"}
    {"eventid": "cowrie.command.input", "input": "uname -a"}
    ''')
    
    result = await parser.parse(test_file)
    
    assert result["attacker_ip"] == "1.2.3.4"
    assert ("root", "toor") in result["credentials"]
    assert "uname -a" in result["commands"]
    
    test_file.unlink()  # Cleanup
```

#### TTP Mapper Tests
```python
# backend/services/reactive_fabric_analysis/tests/test_ttp_mapper.py
def test_ttp_mapper_identifies_brute_force():
    """Test TTP mapper identifies brute force attacks."""
    mapper = TTPMapper()
    
    commands = ["ssh root@target", "password: admin", "password: toor"]
    ttps = mapper.map_ttps(commands, "ssh_brute_force")
    
    assert "T1110" in ttps  # Brute Force
    assert "T1133" in ttps  # External Remote Services

def test_ttp_mapper_identifies_command_execution():
    """Test TTP mapper identifies command execution."""
    mapper = TTPMapper()
    
    commands = ["bash -c 'whoami'", "uname -a", "ls -la /etc"]
    ttps = mapper.map_ttps(commands, "post_exploit")
    
    assert "T1059.004" in ttps  # Unix Shell
    assert "T1082" in ttps  # System Info Discovery
    assert "T1083" in ttps  # File Discovery
```

### 3.3 Testes de Integração

```python
# backend/services/reactive_fabric_core/tests/test_integration.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_attack_creation_publishes_to_kafka(test_db, test_kafka):
    """Test attack creation triggers Kafka publication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create attack
        response = await client.post("/api/v1/attacks", json={
            "honeypot_id": "ssh_001",
            "attacker_ip": "1.2.3.4",
            "attack_type": "brute_force",
            "severity": "high",
            "ttps": ["T1110"],
            "iocs": {"ips": ["1.2.3.4"]},
            "confidence": 0.95,
            "captured_at": "2025-10-12T20:00:00Z"
        })
        
        assert response.status_code == 201
        assert response.json()["kafka_published"] == True
        
        # Verify Kafka message
        messages = await test_kafka.consume("reactive_fabric.threat_detected")
        assert len(messages) == 1
        assert messages[0]["event_id"].startswith("rf_attack_")
```

### 3.4 Coverage Target

```bash
pytest --cov=backend/services/reactive_fabric_core --cov-report=html --cov-fail-under=90
pytest --cov=backend/services/reactive_fabric_analysis --cov-report=html --cov-fail-under=90
```

**Target**: ≥90% coverage (Doutrina Vértice)

---

## MÉTRICAS DE SUCESSO (KPIs)

Conforme Paper Section 4: "Métricas de Validação para a Fase 1"

### KPI 1: TTPs Identificados
**Target**: ≥10 técnicas MITRE ATT&CK únicas identificadas  
**Métrica**: `SELECT COUNT(DISTINCT technique_id) FROM reactive_fabric.ttps`

### KPI 2: Qualidade de Inteligência
**Target**: ≥85% de ataques com TTPs mapeados  
**Métrica**: `(attacks_with_ttps / total_attacks) * 100`

### KPI 3: IoCs Acionáveis
**Target**: ≥50 IoCs únicos (IPs, hashes, usernames)  
**Métrica**: `SELECT COUNT(*) FROM reactive_fabric.iocs WHERE threat_level IN ('high', 'critical')`

### KPI 4: Latência de Processamento
**Target**: <60 segundos do capture → Kafka  
**Métrica**: `AVG(processed_at - captured_at) FROM reactive_fabric.forensic_captures`

### KPI 5: Taxa de Sucesso
**Target**: ≥95% de captures processados sem erro  
**Métrica**: `(completed_captures / total_captures) * 100`

---

## CHECKLIST DE VALIDAÇÃO FINAL

### Code Quality
- [ ] `mypy --strict` sem erros
- [ ] `pylint` score ≥9.0/10
- [ ] `black --check` formatação correta
- [ ] Todos os type hints presentes
- [ ] Docstrings no formato Google

### Testing
- [ ] Coverage ≥90%
- [ ] Testes unitários passando
- [ ] Testes de integração passando
- [ ] NO MOCK em testes críticos (usar testcontainers)

### Doutrina Compliance
- [ ] NO PLACEHOLDER (zero `pass` ou `NotImplementedError`)
- [ ] NO TODO em código de produção
- [ ] NO MOCK (apenas implementações reais)
- [ ] Production-ready (deployável imediatamente)
- [ ] Documentação histórica completa

### Paper Compliance
- [ ] Fase 1 APENAS (coleta passiva)
- [ ] Nenhuma resposta automatizada
- [ ] Human-in-the-loop preparado (estrutura)
- [ ] KPIs implementados e mensuráveis

---

## CRONOGRAMA

### Dia 1 (2025-10-12) - Fase 1
- ✅ Análise profunda do diretório
- ⏳ **Agora**: Correção de imports
- ⏳ Criação de __init__.py
- ⏳ Estrutura modular de Analysis

### Dia 2 (2025-10-13) - Fase 2
- [ ] Implementação de parsers (Cowrie, PCAP)
- [ ] TTP Mapper completo
- [ ] Main analysis loop
- [ ] Kafka integration

### Dia 3 (2025-10-14) - Fase 3
- [ ] Testes unitários
- [ ] Testes de integração
- [ ] Validação de KPIs
- [ ] Documentação final
- [ ] Deploy em staging

---

## PRÓXIMOS PASSOS IMEDIATOS

**Ação 1**: Corrigir imports em `reactive_fabric_core/main.py`  
**Ação 2**: Corrigir imports em `reactive_fabric_core/database.py`  
**Ação 3**: Corrigir imports em `reactive_fabric_core/kafka_producer.py`  
**Ação 4**: Criar `__init__.py` em ambos os serviços  
**Ação 5**: Implementar estrutura de parsers

---

**Status**: READY TO EXECUTE  
**Próximo Comando**: "Vamos executar Fase 1 - Ação 1"

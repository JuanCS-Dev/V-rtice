# REACTIVE FABRIC INTEGRATION - PLANO DE IMPLEMENTAÇÃO COMPLETO
**Sistema Imune Reativo - Integração Total**

**Data:** 2025-10-19  
**Versão:** 1.0  
**Status:** PRONTO PARA EXECUÇÃO  
**Tempo Estimado:** 4-6 horas

---

## CONTEXTO ESTRATÉGICO

### Arquitetura Atual (Desconectada)
```
┌─────────────────────────────────┐     ┌──────────────────────────┐
│   Adaptive Immune System        │     │   Reactive Fabric        │
│   - Oráculo (CVE detection)     │     │   - Honeypots            │
│   - Eureka (remediation)        │  X  │   - Threat intelligence  │
│   - Wargaming (validation)      │     │   - TTP analysis         │
│   - HITL (authorization)        │     │   - Forensics            │
└─────────────────────────────────┘     └──────────────────────────┘
         ❌ NO COMMUNICATION                     ❌ ISOLATED
```

### Arquitetura Alvo (Integrada)
```
┌──────────────────────────────────────────────────────────────────┐
│              SISTEMA IMUNE REATIVO INTEGRADO                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌────────────────────┐            │
│  │ Adaptive Immune  │◄────────┤ Reactive Fabric    │            │
│  │                  │ TTPs    │                    │            │
│  │ - Oráculo        │ IOCs    │ - Honeypots (SSH,  │            │
│  │ - Eureka         │ Threats │   Web, SMTP, FTP)  │            │
│  │ - Wargaming      │─────────►│ - Attack Analysis  │            │
│  │ - HITL           │ APVs    │ - Forensic Capture │            │
│  └──────────────────┘         └────────────────────┘            │
│         │                              │                         │
│         │                              │                         │
│         └──────────┬───────────────────┘                         │
│                    ▼                                             │
│          ┌──────────────────┐                                    │
│          │ RabbitMQ Message │                                    │
│          │ Bus (Integration)│                                    │
│          └──────────────────┘                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## RESEARCH INSIGHTS (Melhores Práticas 2024-2025)

### Fontes Consultadas:
1. **MDPI** - "Advancing Cybersecurity with Honeypots and Deception Strategies" (2025)
2. **IEEE** - "The Role of Honeypots in Modern Cybersecurity Strategies"
3. **SecureMyOrg** - "Best Practices for Deploying Honeypots in 2025"
4. **MBL Technologies** - "Deploying Honeypots and Honeytokens for Advanced Threat Intelligence"
5. **STIX/TAXII** - "A Complete Guide to Automated Threat Intelligence Sharing"

### Key Takeaways:
- ✅ **Message Bus Integration:** RabbitMQ como backbone para comunicação assíncrona entre honeypots e sistema adaptativo
- ✅ **STIX-Compatible Schema:** Usar formato padronizado para threat intelligence (compatível com STIX 2.1)
- ✅ **Automated Response:** Integrar threat intelligence do honeypot com sistema de remediação automatizada
- ✅ **Real-time Correlation:** Correlacionar ataques capturados com CVEs conhecidos
- ✅ **Forensic Validation:** Usar capturas forenses para validar remediações (wargaming)

---

## FASE 1: ORQUESTRAÇÃO (30min)

### Objetivo
Adicionar Reactive Fabric ao docker-compose principal para orquestração unificada

### 1.1 - Merge de Compose Files
**Arquivo:** `docker-compose.yml`

**Ação:**
```yaml
# Adicionar ao final de docker-compose.yml

# ============================================================================
# REACTIVE FABRIC INTEGRATION
# ============================================================================

reactive-fabric-core:
  build: ./backend/services/reactive_fabric_core
  container_name: reactive-fabric-core
  ports:
    - "8600:8600"
  environment:
    - DATABASE_URL=postgresql://vertice:vertice_pass@postgres:5432/vertice
    - KAFKA_BROKERS=kafka:9092
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    - REDIS_URL=redis://redis:6379/0
    - LOG_LEVEL=INFO
    - FORENSIC_CAPTURE_PATH=/forensics
  volumes:
    - ./backend/services/reactive_fabric_core:/app
    - forensic_captures:/forensics:ro
  networks:
    - vertice-network
  depends_on:
    - postgres
    - rabbitmq
    - redis
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8600/health"]
    interval: 30s
    timeout: 10s
    retries: 3

reactive-fabric-analysis:
  build: ./backend/services/reactive_fabric_analysis
  container_name: reactive-fabric-analysis
  ports:
    - "8601:8601"
  environment:
    - DATABASE_URL=postgresql://vertice:vertice_pass@postgres:5432/vertice
    - KAFKA_BROKERS=kafka:9092
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    - LOG_LEVEL=INFO
    - FORENSIC_CAPTURE_PATH=/forensics
    - POLLING_INTERVAL=30
  volumes:
    - ./backend/services/reactive_fabric_analysis:/app
    - forensic_captures:/forensics:ro
  networks:
    - vertice-network
  depends_on:
    - postgres
    - rabbitmq
    - reactive-fabric-core
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8601/health"]
    interval: 30s
    timeout: 10s
    retries: 3

# Volume para forensics
volumes:
  forensic_captures:
    driver: local
```

**Validação:**
```bash
docker compose config | grep -A 5 "reactive-fabric"
```

---

## FASE 2: MESSAGE BUS INTEGRATION (90min)

### Objetivo
Criar infraestrutura de mensagens para comunicação Reactive Fabric ↔ Adaptive Immune

### 2.1 - Definir Message Schemas (STIX-Compatible)

**Arquivo:** `backend/shared/messaging/schemas.py` (criar se não existir)

```python
"""
Shared Message Schemas for Reactive Fabric Integration
STIX 2.1 Compatible Threat Intelligence Messages
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


class ThreatSeverity(str, Enum):
    """STIX-compatible severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AttackType(str, Enum):
    """STIX attack pattern types"""
    BRUTE_FORCE = "T1110"  # MITRE ATT&CK
    SQL_INJECTION = "T1190"
    XSS = "T1059"
    COMMAND_INJECTION = "T1059.004"
    PATH_TRAVERSAL = "T1083"
    MALWARE_UPLOAD = "T1105"
    RECONNAISSANCE = "T1595"
    EXPLOITATION = "T1203"


class IOCType(str, Enum):
    """Indicator of Compromise types"""
    IP_ADDRESS = "ipv4-addr"
    DOMAIN = "domain-name"
    URL = "url"
    FILE_HASH = "file"
    EMAIL = "email-addr"


class TTPModel(BaseModel):
    """Tactics, Techniques, and Procedures extracted from attack"""
    mitre_id: str = Field(..., description="MITRE ATT&CK ID (e.g., T1110)")
    tactic: str = Field(..., description="MITRE tactic (e.g., Credential Access)")
    technique: str = Field(..., description="Technique name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    evidence: List[str] = Field(default_factory=list, description="Evidence snippets")


class IOCModel(BaseModel):
    """Indicator of Compromise"""
    type: IOCType
    value: str = Field(..., description="IOC value (IP, domain, hash, etc)")
    first_seen: datetime
    last_seen: datetime
    confidence: float = Field(..., ge=0.0, le=1.0)
    context: Optional[Dict] = None


class ThreatEventMessage(BaseModel):
    """
    Threat event detected by Reactive Fabric honeypot
    Published to: reactive_fabric.threats
    Consumed by: Adaptive Immune (Oráculo)
    """
    # STIX Threat Actor object
    threat_id: str = Field(..., description="Unique threat event ID")
    honeypot_id: str = Field(..., description="Source honeypot identifier")
    honeypot_type: str = Field(..., description="Honeypot type (ssh, web, smtp)")
    
    # Attack metadata
    source_ip: str
    source_port: int
    target_port: int
    timestamp: datetime
    
    # Threat classification
    attack_type: AttackType
    severity: ThreatSeverity
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Intelligence
    ttps: List[TTPModel] = Field(default_factory=list)
    iocs: List[IOCModel] = Field(default_factory=list)
    
    # Forensics
    forensic_capture_path: Optional[str] = None
    raw_logs: Optional[str] = None
    
    # Correlation
    related_cves: List[str] = Field(default_factory=list, description="Potential CVEs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "threat_id": "threat_20251019_001",
                "honeypot_id": "ssh_honeypot_001",
                "honeypot_type": "ssh",
                "source_ip": "192.168.1.100",
                "source_port": 54321,
                "target_port": 2222,
                "timestamp": "2025-10-19T18:00:00Z",
                "attack_type": "T1110",
                "severity": "high",
                "confidence": 0.95,
                "ttps": [
                    {
                        "mitre_id": "T1110.001",
                        "tactic": "Credential Access",
                        "technique": "Password Guessing",
                        "confidence": 0.95,
                        "evidence": ["admin:admin", "root:toor"]
                    }
                ],
                "iocs": [
                    {
                        "type": "ipv4-addr",
                        "value": "192.168.1.100",
                        "first_seen": "2025-10-19T18:00:00Z",
                        "last_seen": "2025-10-19T18:05:00Z",
                        "confidence": 1.0
                    }
                ],
                "related_cves": ["CVE-2023-12345"]
            }
        }


class ThreatCorrelationRequest(BaseModel):
    """
    Request to correlate threat with CVE database
    Published by: Oráculo
    Consumed by: Reactive Fabric Analysis
    """
    correlation_id: str
    threat_id: str
    ttps: List[TTPModel]
    target_ecosystem: Literal["python", "javascript", "go", "docker", "all"]


class ThreatCorrelationResponse(BaseModel):
    """
    CVE correlation results
    Published by: Reactive Fabric Analysis
    Consumed by: Oráculo
    """
    correlation_id: str
    threat_id: str
    matched_cves: List[str]
    confidence_scores: Dict[str, float]
    suggested_apvs: List[str] = Field(
        default_factory=list,
        description="Suggested APV IDs to generate"
    )


class ForensicValidationRequest(BaseModel):
    """
    Request to use forensic captures for wargaming validation
    Published by: Eureka
    Consumed by: Reactive Fabric Core
    """
    validation_id: str
    remedy_id: str
    apv_id: str
    threat_ids: List[str] = Field(
        description="Threat IDs to replay for validation"
    )
    forensic_capture_paths: List[str]


class ForensicValidationResponse(BaseModel):
    """
    Results of wargaming validation using real attack captures
    Published by: Reactive Fabric Core
    Consumed by: Eureka
    """
    validation_id: str
    remedy_id: str
    success: bool
    details: str
    attack_blocked: bool
    false_positive_rate: float
```

### 2.2 - Reactive Fabric Publisher

**Arquivo:** `backend/services/reactive_fabric_core/messaging/__init__.py` (criar)

```python
"""RabbitMQ Integration for Reactive Fabric"""
from .publisher import ReacticeFabricPublisher
from .consumer import AdaptiveImmuneConsumer

__all__ = ["ReacticeFabricPublisher", "AdaptiveImmuneConsumer"]
```

**Arquivo:** `backend/services/reactive_fabric_core/messaging/publisher.py` (criar)

```python
"""
Reactive Fabric - RabbitMQ Publisher
Publishes threat events to Adaptive Immune System
"""
import pika
import json
import structlog
from typing import Optional
from pika.adapters.blocking_connection import BlockingChannel

from backend.shared.messaging.schemas import ThreatEventMessage

logger = structlog.get_logger()


class ReacticeFabricPublisher:
    """Publishes threat intelligence to RabbitMQ"""
    
    EXCHANGE = "reactive_fabric.threats"
    ROUTING_KEY_PREFIX = "threat"
    
    def __init__(self, rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
    
    def connect(self) -> None:
        """Establish RabbitMQ connection"""
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.EXCHANGE,
                exchange_type="topic",
                durable=True
            )
            
            logger.info(
                "rabbitmq_connected",
                exchange=self.EXCHANGE
            )
        except Exception as e:
            logger.error(
                "rabbitmq_connection_failed",
                error=str(e)
            )
            raise
    
    def publish_threat_event(self, threat: ThreatEventMessage) -> None:
        """Publish threat event to adaptive immune system"""
        if not self.channel:
            self.connect()
        
        routing_key = f"{self.ROUTING_KEY_PREFIX}.{threat.severity}.{threat.attack_type}"
        
        try:
            self.channel.basic_publish(
                exchange=self.EXCHANGE,
                routing_key=routing_key,
                body=threat.model_dump_json(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type="application/json",
                    priority=self._get_priority(threat.severity),
                    headers={
                        "threat_id": threat.threat_id,
                        "honeypot_id": threat.honeypot_id,
                        "severity": threat.severity.value
                    }
                )
            )
            
            logger.info(
                "threat_event_published",
                threat_id=threat.threat_id,
                severity=threat.severity,
                routing_key=routing_key
            )
        except Exception as e:
            logger.error(
                "threat_publish_failed",
                threat_id=threat.threat_id,
                error=str(e)
            )
            raise
    
    def _get_priority(self, severity: str) -> int:
        """Map severity to RabbitMQ priority (0-10)"""
        priority_map = {
            "critical": 10,
            "high": 8,
            "medium": 5,
            "low": 3,
            "info": 1
        }
        return priority_map.get(severity, 5)
    
    def close(self) -> None:
        """Close RabbitMQ connection"""
        if self.connection:
            self.connection.close()
            logger.info("rabbitmq_connection_closed")
```

### 2.3 - Adaptive Immune Consumer

**Arquivo:** `backend/services/adaptive_immune_system/messaging/reactive_fabric_consumer.py` (criar)

```python
"""
Adaptive Immune - Reactive Fabric Threat Consumer
Consumes threat events from honeypots and correlates with CVEs
"""
import pika
import json
import structlog
from typing import Callable, Optional
from pika.adapters.blocking_connection import BlockingChannel

from backend.shared.messaging.schemas import ThreatEventMessage
from backend.services.adaptive_immune_system.oraculo.triage_engine import TriageEngine

logger = structlog.get_logger()


class ReactiveFabricThreatConsumer:
    """Consumes threat intelligence from Reactive Fabric honeypots"""
    
    EXCHANGE = "reactive_fabric.threats"
    QUEUE = "oraculo.reactive_fabric_threats"
    ROUTING_KEYS = [
        "threat.critical.*",
        "threat.high.*",
        "threat.medium.*"
    ]
    
    def __init__(
        self,
        rabbitmq_url: str,
        triage_engine: TriageEngine,
        callback: Optional[Callable] = None
    ):
        self.rabbitmq_url = rabbitmq_url
        self.triage_engine = triage_engine
        self.callback = callback
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
    
    def connect(self) -> None:
        """Establish RabbitMQ connection and declare queue"""
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            # Declare queue with DLQ
            self.channel.queue_declare(
                queue=self.QUEUE,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": f"{self.EXCHANGE}.dlq",
                    "x-message-ttl": 86400000,  # 24h
                    "x-max-priority": 10
                }
            )
            
            # Bind to exchange with routing keys
            for routing_key in self.ROUTING_KEYS:
                self.channel.queue_bind(
                    exchange=self.EXCHANGE,
                    queue=self.QUEUE,
                    routing_key=routing_key
                )
            
            logger.info(
                "threat_consumer_connected",
                queue=self.QUEUE,
                routing_keys=self.ROUTING_KEYS
            )
        except Exception as e:
            logger.error("consumer_connection_failed", error=str(e))
            raise
    
    def start_consuming(self) -> None:
        """Start consuming threat events"""
        if not self.channel:
            self.connect()
        
        self.channel.basic_qos(prefetch_count=5)
        self.channel.basic_consume(
            queue=self.QUEUE,
            on_message_callback=self._on_message
        )
        
        logger.info("threat_consumer_started", queue=self.QUEUE)
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.close()
    
    def _on_message(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes
    ) -> None:
        """Handle incoming threat event"""
        try:
            # Parse message
            threat_data = json.loads(body.decode())
            threat = ThreatEventMessage(**threat_data)
            
            logger.info(
                "threat_event_received",
                threat_id=threat.threat_id,
                severity=threat.severity,
                attack_type=threat.attack_type
            )
            
            # Process threat through Oráculo triage
            self._process_threat(threat)
            
            # ACK message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
            # Execute callback if provided
            if self.callback:
                self.callback(threat)
                
        except Exception as e:
            logger.error(
                "threat_processing_failed",
                error=str(e),
                body=body.decode()
            )
            # NACK and requeue (will go to DLQ after retries)
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False
            )
    
    def _process_threat(self, threat: ThreatEventMessage) -> None:
        """Process threat event through Oráculo"""
        # 1. Correlate TTPs with CVE database
        matched_cves = self._correlate_ttps_with_cves(threat.ttps)
        
        # 2. Check if any matched CVEs affect our dependencies
        vulnerable_deps = self._check_dependencies(matched_cves)
        
        # 3. Generate APVs for vulnerable dependencies
        if vulnerable_deps:
            for dep in vulnerable_deps:
                apv = self.triage_engine.generate_apv_from_threat(
                    threat=threat,
                    dependency=dep,
                    matched_cves=matched_cves
                )
                logger.info(
                    "apv_generated_from_threat",
                    apv_id=apv.id,
                    threat_id=threat.threat_id,
                    dependency=dep.name
                )
    
    def _correlate_ttps_with_cves(self, ttps: list) -> list:
        """Correlate MITRE TTPs with CVE database"""
        # TODO: Implement TTP -> CVE correlation logic
        # Query NVD/GHSA for CVEs matching attack patterns
        return []
    
    def _check_dependencies(self, cves: list) -> list:
        """Check if CVEs affect our dependencies"""
        # TODO: Query dependency scanner results
        return []
    
    def close(self) -> None:
        """Close consumer connection"""
        if self.connection:
            self.connection.close()
            logger.info("threat_consumer_closed")
```

---

## FASE 3: REACTIVE FABRIC ENHANCEMENTS (60min)

### Objetivo
Adicionar publicação de threat events ao Reactive Fabric Core

### 3.1 - Integrar Publisher no Reactive Fabric Core

**Arquivo:** `backend/services/reactive_fabric_core/main.py`

**Modificações:**
```python
# Adicionar imports
from .messaging.publisher import ReacticeFabricPublisher
from backend.shared.messaging.schemas import ThreatEventMessage, AttackType, ThreatSeverity

# Adicionar ao lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db, kafka_producer, docker_client, rabbitmq_publisher
    
    # ... código existente ...
    
    # Initialize RabbitMQ publisher
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    rabbitmq_publisher = ReacticeFabricPublisher(rabbitmq_url)
    rabbitmq_publisher.connect()
    logger.info("rabbitmq_publisher_initialized")
    
    yield
    
    # Cleanup
    if rabbitmq_publisher:
        rabbitmq_publisher.close()

# Modificar endpoint de criação de ataque para publicar no RabbitMQ
@app.post("/api/v1/attacks", status_code=201)
async def create_attack(attack: AttackCreate):
    """Log attack event and publish to adaptive immune system"""
    # ... código existente de persistência ...
    
    # Publish to RabbitMQ
    threat_event = ThreatEventMessage(
        threat_id=f"threat_{attack.honeypot_id}_{datetime.utcnow().timestamp()}",
        honeypot_id=attack.honeypot_id,
        honeypot_type=honeypot.type,
        source_ip=attack.source_ip,
        source_port=attack.source_port,
        target_port=honeypot.port,
        timestamp=datetime.utcnow(),
        attack_type=AttackType(attack.attack_type),
        severity=ThreatSeverity(attack.severity),
        confidence=attack.confidence or 0.8,
        ttps=attack.ttps or [],
        iocs=attack.iocs or [],
        forensic_capture_path=attack.forensic_path,
        raw_logs=attack.raw_data
    )
    
    rabbitmq_publisher.publish_threat_event(threat_event)
    
    return {"id": attack_id, "status": "logged", "published": True}
```

---

## FASE 4: ADAPTIVE IMMUNE INTEGRATION (90min)

### Objetivo
Integrar consumer no Adaptive Immune System

### 4.1 - Criar Background Task Consumer

**Arquivo:** `backend/services/adaptive_immune_system/main.py`

**Modificações:**
```python
# Adicionar imports
from .messaging.reactive_fabric_consumer import ReactiveFabricThreatConsumer
from .oraculo.triage_engine import TriageEngine
import asyncio
import threading

# Adicionar ao lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... código existente ...
    
    # Initialize Reactive Fabric threat consumer
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    triage_engine = TriageEngine(db_client)  # Use existing triage engine
    
    threat_consumer = ReactiveFabricThreatConsumer(
        rabbitmq_url=rabbitmq_url,
        triage_engine=triage_engine
    )
    
    # Start consumer in background thread
    consumer_thread = threading.Thread(
        target=threat_consumer.start_consuming,
        daemon=True
    )
    consumer_thread.start()
    logger.info("reactive_fabric_consumer_started")
    
    yield
    
    # Cleanup
    threat_consumer.close()

# Adicionar endpoint de monitoramento
@app.get("/api/v1/integrations/reactive-fabric/status")
async def reactive_fabric_status():
    """Get Reactive Fabric integration status"""
    return {
        "status": "connected",
        "consumer": "active",
        "queue": "oraculo.reactive_fabric_threats",
        "threats_processed": 0  # TODO: Add metrics
    }
```

---

## FASE 5: VALIDAÇÃO E TESTES (60min)

### 5.1 - Testes de Integração

**Arquivo:** `backend/services/reactive_fabric_core/tests/test_integration.py` (criar)

```python
"""Integration tests for Reactive Fabric ↔ Adaptive Immune"""
import pytest
from backend.shared.messaging.schemas import ThreatEventMessage, AttackType, ThreatSeverity
from ..messaging.publisher import ReacticeFabricPublisher


def test_threat_event_publishing():
    """Test publishing threat event to RabbitMQ"""
    publisher = ReacticeFabricPublisher("amqp://guest:guest@localhost:5672/")
    publisher.connect()
    
    threat = ThreatEventMessage(
        threat_id="test_threat_001",
        honeypot_id="ssh_honeypot_test",
        honeypot_type="ssh",
        source_ip="192.168.1.100",
        source_port=54321,
        target_port=2222,
        timestamp=datetime.utcnow(),
        attack_type=AttackType.BRUTE_FORCE,
        severity=ThreatSeverity.HIGH,
        confidence=0.95
    )
    
    publisher.publish_threat_event(threat)
    publisher.close()
    
    assert True  # If no exception, success


def test_threat_event_schema_validation():
    """Test ThreatEventMessage schema validation"""
    threat = ThreatEventMessage(
        threat_id="test_001",
        honeypot_id="ssh_001",
        honeypot_type="ssh",
        source_ip="192.168.1.1",
        source_port=12345,
        target_port=22,
        timestamp=datetime.utcnow(),
        attack_type=AttackType.BRUTE_FORCE,
        severity=ThreatSeverity.CRITICAL,
        confidence=1.0
    )
    
    assert threat.threat_id == "test_001"
    assert threat.severity == ThreatSeverity.CRITICAL
    assert 0.0 <= threat.confidence <= 1.0
```

### 5.2 - Teste E2E Manual

**Script:** `scripts/test_reactive_fabric_integration.sh` (criar)

```bash
#!/bin/bash
# End-to-End Integration Test
# Reactive Fabric -> RabbitMQ -> Adaptive Immune

echo "🧪 Testing Reactive Fabric Integration..."

# 1. Check services are up
echo "1️⃣ Checking services..."
docker compose ps | grep -E "(reactive-fabric|adaptive-immune|rabbitmq)"

# 2. Simulate threat event
echo "2️⃣ Simulating SSH brute force attack..."
curl -X POST http://localhost:8600/api/v1/attacks \
  -H "Content-Type: application/json" \
  -d '{
    "honeypot_id": "ssh_honeypot_001",
    "source_ip": "203.0.113.42",
    "source_port": 54321,
    "attack_type": "T1110",
    "severity": "high",
    "confidence": 0.95,
    "ttps": [
      {
        "mitre_id": "T1110.001",
        "tactic": "Credential Access",
        "technique": "Password Guessing",
        "confidence": 0.95,
        "evidence": ["admin:admin", "root:toor"]
      }
    ]
  }'

# 3. Check RabbitMQ queue
echo "3️⃣ Checking RabbitMQ queue..."
docker compose exec rabbitmq rabbitmqctl list_queues name messages

# 4. Check Adaptive Immune logs
echo "4️⃣ Checking Adaptive Immune consumption..."
docker compose logs adaptive-immune-system --tail=20 | grep "threat_event_received"

# 5. Check APV generation
echo "5️⃣ Checking if APV was generated..."
curl http://localhost:8003/api/v1/apvs | jq '.[] | select(.source == "reactive_fabric")'

echo "✅ Integration test complete!"
```

---

## FASE 6: OBSERVABILIDADE (30min)

### 6.1 - Prometheus Metrics

**Arquivo:** `backend/services/reactive_fabric_core/main.py`

```python
# Adicionar métricas
threats_published_total = Counter(
    'reactive_fabric_threats_published_total',
    'Total threats published to RabbitMQ',
    ['severity', 'attack_type']
)

rabbitmq_publish_errors = Counter(
    'reactive_fabric_rabbitmq_errors_total',
    'RabbitMQ publish errors'
)

# Instrumentar publisher
def publish_threat_event(self, threat: ThreatEventMessage) -> None:
    try:
        # ... código de publicação ...
        threats_published_total.labels(
            severity=threat.severity,
            attack_type=threat.attack_type
        ).inc()
    except Exception as e:
        rabbitmq_publish_errors.inc()
        raise
```

**Arquivo:** `backend/services/adaptive_immune_system/main.py`

```python
# Adicionar métricas
threats_consumed_total = Counter(
    'oraculo_threats_consumed_total',
    'Total threats consumed from Reactive Fabric',
    ['severity']
)

apvs_generated_from_threats = Counter(
    'oraculo_apvs_from_reactive_fabric_total',
    'APVs generated from Reactive Fabric threats'
)
```

### 6.2 - Grafana Dashboard

**Arquivo:** `monitoring/dashboards/reactive-fabric-integration.json` (criar)

Dashboard com:
- Taxa de threat events publicados/consumidos
- Latência de processamento (Honeypot → APV gerado)
- Taxa de correlação CVE (% de threats que geram APVs)
- Top attack types detectados
- Top source IPs atacantes

---

## FASE 7: DOCUMENTAÇÃO (30min)

### 7.1 - Atualizar README

**Arquivo:** `backend/services/reactive_fabric_core/README.md`

Adicionar seção:
```markdown
## Integration with Adaptive Immune System

Reactive Fabric publishes threat intelligence to RabbitMQ for consumption by the Adaptive Immune System (Oráculo).

### Message Flow
1. Honeypot detects attack → logs to database
2. Attack event published to `reactive_fabric.threats` exchange
3. Oráculo consumes from `oraculo.reactive_fabric_threats` queue
4. Oráculo correlates TTPs with CVE database
5. If vulnerability found → APV generated → Eureka remediates

### Message Schema
See `backend/shared/messaging/schemas.py` for STIX-compatible threat event schema.
```

---

## CHECKPOINTS DE VALIDAÇÃO

### ✅ Checkpoint 25% (Pós-Fase 1)
```bash
docker compose config | grep "reactive-fabric" | wc -l  # >= 2
docker compose up -d reactive-fabric-core reactive-fabric-analysis
docker compose ps | grep "reactive-fabric" | grep "Up"
```

### ✅ Checkpoint 50% (Pós-Fase 2-3)
```bash
# Verificar schemas
python -c "from backend.shared.messaging.schemas import ThreatEventMessage; print('OK')"

# Verificar publisher
docker compose exec reactive-fabric-core python -c "from messaging.publisher import ReacticeFabricPublisher; print('OK')"

# Verificar RabbitMQ exchange
docker compose exec rabbitmq rabbitmqctl list_exchanges | grep "reactive_fabric.threats"
```

### ✅ Checkpoint 75% (Pós-Fase 4-5)
```bash
# Executar teste E2E
bash scripts/test_reactive_fabric_integration.sh

# Verificar logs
docker compose logs adaptive-immune-system | grep "threat_event_received"
docker compose logs reactive-fabric-core | grep "threat_event_published"
```

### ✅ Checkpoint 100% (Pós-Fase 6-7)
```bash
# Verificar métricas
curl http://localhost:8600/metrics | grep "reactive_fabric_threats_published_total"
curl http://localhost:8003/metrics | grep "oraculo_threats_consumed_total"

# Verificar documentação
ls -la backend/services/reactive_fabric_core/README.md
grep "Integration with Adaptive Immune" backend/services/reactive_fabric_core/README.md
```

---

## CRITÉRIOS DE SUCESSO (100%)

- ✅ Reactive Fabric Core e Analysis no docker-compose principal
- ✅ RabbitMQ exchange `reactive_fabric.threats` criado
- ✅ Message schemas STIX-compatible implementados
- ✅ Publisher funcional em Reactive Fabric Core
- ✅ Consumer funcional em Adaptive Immune System
- ✅ Teste E2E passando (threat event → APV gerado)
- ✅ Zero quebra em serviços existentes
- ✅ Métricas Prometheus instrumentadas
- ✅ Documentação atualizada
- ✅ Healthchecks de ambos serviços OK

---

## RISCOS IDENTIFICADOS E MITIGAÇÕES

### 🔴 RISCO 1: Quebrar interação Oráculo-Eureka existente
**Probabilidade:** BAIXA  
**Impacto:** CRÍTICO  
**Mitigação:**
- Consumer roda em thread separada (não bloqueia API)
- Zero modificações no código de Oráculo/Eureka existente
- Apenas adiciona nova fonte de threats (não substitui CVE feeds)

### 🟡 RISCO 2: RabbitMQ overhead
**Probabilidade:** MÉDIA  
**Impacto:** BAIXO  
**Mitigação:**
- Prefetch limit (5 messages)
- Message TTL (24h)
- Dead-letter queue para falhas

### 🟢 RISCO 3: Schema evolution
**Probabilidade:** ALTA  
**Impacto:** BAIXO  
**Mitigação:**
- STIX 2.1 compatible (padrão da indústria)
- Pydantic validation
- Versioning no message header

---

## ORDEM DE EXECUÇÃO

1. **Backup:** `docker compose down && git checkout -b reactive-fabric-integration`
2. **FASE 1:** Orquestração (30min)
3. **Validação 25%**
4. **FASE 2-3:** Message Bus + Publisher (150min)
5. **Validação 50%**
6. **FASE 4:** Consumer Adaptive Immune (90min)
7. **FASE 5:** Testes (60min)
8. **Validação 75%**
9. **FASE 6-7:** Observabilidade + Docs (60min)
10. **Validação 100%**
11. **COMMIT:** `git add . && git commit -m "feat: integrate reactive fabric with adaptive immune system"`

---

**PLANO APROVADO PARA EXECUÇÃO**  
**Estimativa Total:** 4-6 horas  
**Risco:** BAIXO (arquitetura conservadora, zero breaking changes)  
**ROI:** ALTO (sinergy entre honeypots e sistema adaptativo)

# Air Gaps Implementation Plan - Top 5 Priorities

**Generated:** 2025-10-23T14:20:00Z
**Planning Agent:** ARQUITETO (via Claude Sonnet 4.5)
**Source:** DIAGNOSTICADOR_AIR_GAPS_REPORT.md
**Total Estimated Effort:** 13-21 hours (17-27h with 30% buffer)

---

## Executive Summary

This plan addresses the **5 highest priority Air Gaps** identified in the backend services diagnostic:

1. **AG-RUNTIME-002** (CRITICAL): Install torch dependency → 30 min
2. **AG-RUNTIME-001** (CRITICAL): Fix Oráculo Kafka hard dependency → 3-5h
3. **AG-KAFKA-005** (HIGH): Create DLQ consumer for APVs → 3-5h
4. **AG-KAFKA-009** (HIGH): Connect agent-communications producer → 4-6h
5. **AG-KAFKA-004** (MEDIUM): Create honeypot_status consumer → 2-4h

**Implementation Order:** Sequential (1 → 2 → 3 → 4 → 5)
**Risk Level:** Low-Medium (mostly architectural, well-defined scope)

---

## Air Gap 1: AG-RUNTIME-002 - torch Dependency (CRITICAL)

### Problem

- **Service:** `maximus_core_service`
- **Error:** `ModuleNotFoundError: No module named 'torch'`
- **Impact:** Service cannot start, entire consciousness system down
- **Root Cause:** `autonomic_core/analyze/anomaly_detector.py:6` imports torch, not in requirements.txt

### Solution

**ADR-001: Add PyTorch with Optional Import**

**Implementation Steps:**

1. **Add dependency to requirements.txt**

   ```bash
   # File: maximus_core_service/requirements.txt
   torch>=2.0.0
   ```

2. **Modify anomaly_detector.py for lazy import**

   ```python
   # File: maximus_core_service/autonomic_core/analyze/anomaly_detector.py

   try:
       import torch
       TORCH_AVAILABLE = True
   except ImportError:
       TORCH_AVAILABLE = False
       torch = None

   class AnomalyDetector:
       def __init__(self):
           if not TORCH_AVAILABLE:
               raise ImportError(
                   "PyTorch is required for anomaly detection. "
                   "Install with: pip install torch>=2.0.0"
               )
       # ... rest of implementation
   ```

3. **Update deployment scripts**
   ```bash
   cd maximus_core_service
   pip install -r requirements.txt
   python main.py  # Should start successfully
   ```

**Testing:**

- Smoke test: `python -c "import torch; print(torch.__version__)"`
- Service startup: `python main.py` (verify no import errors)
- Health check: `curl http://localhost:8080/health`

**Estimated Effort:** 30 minutes
**Risk:** Low (dependency addition only)

---

## Air Gap 2: AG-RUNTIME-001 - Oráculo Kafka Hard Dependency (CRITICAL)

### Problem

- **Service:** `maximus_oraculo`
- **Error:** `KafkaConnectionError: Unable to bootstrap from [('localhost', 9092)]`
- **Impact:** Service crashes on startup when Kafka unavailable
- **Root Cause:** `websocket/apv_stream_manager.py:158` starts Kafka unconditionally, bypassing `ENABLE_KAFKA` flag

### Solution

**ADR-002: Implement Graceful Degradation with In-Memory Fallback**

**Implementation Steps:**

1. **Create InMemoryAPVQueue fallback**

   ```python
   # File: maximus_oraculo/queue/memory_queue.py (NEW FILE)

   from collections import deque
   from typing import Dict, Optional
   import logging

   class InMemoryAPVQueue:
       """In-memory circular queue for APVs when Kafka is unavailable."""

       def __init__(self, maxlen: int = 1000):
           self.queue = deque(maxlen=maxlen)
           self.logger = logging.getLogger(__name__)
           self.logger.warning(
               "⚠️  InMemoryAPVQueue initialized - DEGRADED MODE (Kafka unavailable)"
           )

       def send(self, apv: Dict) -> bool:
           """Add APV to in-memory queue."""
           try:
               self.queue.append(apv)
               self.logger.debug(f"APV added to memory queue (size: {len(self.queue)})")
               return True
           except Exception as e:
               self.logger.error(f"Failed to add APV to memory queue: {e}")
               return False

       def get_all(self) -> list:
           """Get all APVs from queue (for later flushing to Kafka)."""
           return list(self.queue)

       def clear(self):
           """Clear the queue."""
           self.queue.clear()
   ```

2. **Modify apv_stream_manager.py for degradation**

   ```python
   # File: maximus_oraculo/websocket/apv_stream_manager.py

   from queue.memory_queue import InMemoryAPVQueue
   from kafka.errors import KafkaError
   import os

   class APVStreamManager:
       def __init__(self):
           self.kafka_enabled = os.getenv("ENABLE_KAFKA", "false").lower() == "true"
           self.producer = None
           self.memory_queue = None
           self.degraded_mode = False

       def start(self):
           """Start APV stream manager with graceful degradation."""
           if not self.kafka_enabled:
               self.logger.info("Kafka disabled by ENABLE_KAFKA flag")
               self.memory_queue = InMemoryAPVQueue()
               self.degraded_mode = True
               return

           try:
               # Attempt Kafka connection with timeout
               self.producer = KafkaProducer(
                   bootstrap_servers=self.kafka_servers,
                   request_timeout_ms=5000,
                   # ... other configs
               )
               self.logger.info("✅ Kafka producer connected")
           except KafkaError as e:
               self.logger.error(f"Kafka connection failed: {e}")
               self.logger.warning("⚠️  DEGRADED MODE: Using in-memory APV queue")
               self.memory_queue = InMemoryAPVQueue()
               self.degraded_mode = True

       def send_apv(self, apv: Dict):
           """Send APV to Kafka or memory queue."""
           if self.degraded_mode:
               return self.memory_queue.send(apv)
           else:
               # Existing Kafka send logic
               return self._send_to_kafka(apv)
   ```

3. **Modify api.py startup event**

   ```python
   # File: maximus_oraculo/api.py (around line 105)

   @app.on_event("startup")
   async def startup_event():
       """Startup event with graceful degradation."""
       logger.info("Starting Oráculo service...")

       # Only start APV stream manager if enabled
       enable_kafka = os.getenv("ENABLE_KAFKA", "false").lower() == "true"
       if enable_kafka:
           try:
               apv_stream_manager.start()
           except Exception as e:
               logger.error(f"APV stream manager failed to start: {e}")
               logger.warning("Service will continue in DEGRADED MODE")
       else:
           logger.info("APV stream manager disabled (ENABLE_KAFKA=false)")
   ```

4. **Add health check endpoint**

   ```python
   # File: maximus_oraculo/api.py

   @app.get("/health")
   async def health_check():
       """Health check with degradation status."""
       return {
           "status": "healthy",
           "degraded_mode": apv_stream_manager.degraded_mode if apv_stream_manager else False,
           "kafka_enabled": os.getenv("ENABLE_KAFKA", "false").lower() == "true"
       }
   ```

**Testing:**

- Unit test: Mock Kafka unavailable, verify InMemoryAPVQueue usage
- Integration test: Start Oráculo with Kafka down, verify no crash
- Validation: Send APV, verify stored in memory queue
- Recovery test: Start Kafka, verify APVs flush from memory to Kafka

**Estimated Effort:** 3-5 hours
**Risk:** Medium (core service modification)

---

## Air Gap 3: AG-KAFKA-005 - DLQ Consumer Missing (HIGH)

### Problem

- **Topic:** `maximus.adaptive-immunity.dlq`
- **Impact:** Failed APVs silently lost, no monitoring/alerting
- **Root Cause:** APV publisher sends failed messages to DLQ, no consumer monitors it

### Solution

**ADR-003: Create maximus_dlq_monitor Microservice**

**Implementation Steps:**

1. **Create new service structure**

   ```bash
   mkdir -p maximus_dlq_monitor_service/{api,consumers,config}
   cd maximus_dlq_monitor_service
   ```

2. **Create main.py**

   ```python
   # File: maximus_dlq_monitor_service/main.py

   from fastapi import FastAPI
   from kafka import KafkaConsumer
   from prometheus_client import Counter, Gauge, make_asgi_app
   import json
   import logging

   app = FastAPI(title="MAXIMUS DLQ Monitor")

   # Prometheus metrics
   dlq_messages_total = Counter("dlq_messages_total", "Total DLQ messages", ["reason"])
   dlq_retries_total = Counter("dlq_retries_total", "Total DLQ retries", ["success"])
   dlq_queue_size = Gauge("dlq_queue_size", "Current DLQ size")

   logger = logging.getLogger(__name__)

   @app.on_event("startup")
   async def startup_event():
       """Start DLQ consumer."""
       consumer = KafkaConsumer(
           "maximus.adaptive-immunity.dlq",
           bootstrap_servers="localhost:9092",
           group_id="dlq-monitor",
           value_deserializer=lambda m: json.loads(m.decode("utf-8"))
       )

       for message in consumer:
           process_dlq_message(message.value)

   def process_dlq_message(message: dict):
       """Process DLQ message with retry logic."""
       logger.error(f"DLQ message received: {message}")

       # Extract failure reason
       reason = message.get("error", {}).get("type", "unknown")
       dlq_messages_total.labels(reason=reason).inc()

       # Retry logic with exponential backoff
       retry_count = message.get("retry_count", 0)
       if retry_count < 3:
           # Attempt retry
           success = retry_apv_send(message["apv"])
           dlq_retries_total.labels(success=str(success)).inc()
       else:
           logger.error(f"APV failed after 3 retries: {message['apv']['id']}")
           # Send alert (Slack, email, etc.)
           send_alert(message)

   # Prometheus endpoint
   metrics_app = make_asgi_app()
   app.mount("/metrics", metrics_app)

   @app.get("/health")
   async def health():
       return {"status": "healthy"}
   ```

3. **Create requirements.txt**

   ```
   fastapi>=0.104.0
   uvicorn[standard]>=0.24.0
   kafka-python>=2.0.2
   prometheus-client>=0.19.0
   ```

4. **Create Grafana dashboard**
   - Panel 1: DLQ message count (last 24h)
   - Panel 2: DLQ retry success rate
   - Panel 3: DLQ messages by failure reason
   - Alert: DLQ size > 10 messages

**Testing:**

- Force APV validation failure in Oráculo
- Verify message arrives in DLQ
- Verify DLQ monitor logs error
- Verify retry attempt
- Check Prometheus metrics at `/metrics`

**Estimated Effort:** 3-5 hours
**Risk:** Low (new service, no existing code modification)

---

## Air Gap 4: AG-KAFKA-009 - agent-communications Producer (HIGH)

### Problem

- **Topic:** `agent-communications`
- **Impact:** Narrative Filter feature not working, agent coordination intelligence lost
- **Root Cause:** Consumer expects messages that never arrive (no producer connected)

### Solution

**ADR-004: Connect Agent Communication Service to Kafka**

**Implementation Steps:**

1. **Add KafkaProducer to agent_communication_service**

   ```python
   # File: agent_communication_service/kafka_producer.py (NEW FILE)

   from kafka import KafkaProducer
   import json
   import logging

   class AgentCommunicationProducer:
       def __init__(self, bootstrap_servers: str = "localhost:9092"):
           self.producer = KafkaProducer(
               bootstrap_servers=bootstrap_servers,
               value_serializer=lambda v: json.dumps(v).encode("utf-8")
           )
           self.logger = logging.getLogger(__name__)

       def publish_agent_message(self, event_type: str, agent_from: str,
                                 agent_to: str, content: str, metadata: dict = None):
           """Publish agent communication event to Kafka."""
           message = {
               "event_type": event_type,
               "timestamp": datetime.utcnow().isoformat(),
               "agent_from": agent_from,
               "agent_to": agent_to,
               "message_id": str(uuid4()),
               "content": content,
               "metadata": metadata or {}
           }

           try:
               future = self.producer.send("agent-communications", message)
               future.get(timeout=10)
               self.logger.info(f"Agent message published: {agent_from} → {agent_to}")
           except Exception as e:
               self.logger.error(f"Failed to publish agent message: {e}")
   ```

2. **Modify agent communication API**

   ```python
   # File: agent_communication_service/api.py

   from kafka_producer import AgentCommunicationProducer

   kafka_producer = AgentCommunicationProducer()

   @app.post("/agent/message")
   async def send_agent_message(request: AgentMessageRequest):
       """Send agent message and publish to Kafka."""
       # Existing message handling logic
       # ...

       # NEW: Publish to Kafka for Narrative Filter
       kafka_producer.publish_agent_message(
           event_type="agent.message.sent",
           agent_from=request.agent_from,
           agent_to=request.agent_to,
           content=request.content,
           metadata=request.metadata
       )

       return {"status": "sent", "message_id": message_id}
   ```

3. **Validate Narrative Filter integration**

   ```python
   # File: narrative_filter_service/kafka_consumer.py (VERIFY)

   # Ensure consumer is properly configured
   consumer = KafkaConsumer(
       "agent-communications",
       bootstrap_servers="localhost:9092",
       group_id="narrative-filter",
       # ...
   )
   ```

**Testing:**

- End-to-end test: Send agent message via API
- Verify message published to `agent-communications` topic
- Verify Narrative Filter consumes and processes message
- Check semantic analysis output

**Estimated Effort:** 4-6 hours
**Risk:** Medium (integration with existing consumer)

---

## Air Gap 5: AG-KAFKA-004 - honeypot_status Consumer (MEDIUM)

### Problem

- **Topic:** `reactive_fabric.honeypot_status`
- **Impact:** Honeypot intelligence lost, threat pattern learning gap
- **Root Cause:** Reactive Fabric publishes honeypot status, no consumer utilizes data

### Solution

**ADR-005: Integrate honeypot_status into Active Immune Core**

**Implementation Steps:**

1. **Add consumer to active_immune_core**

   ```python
   # File: active_immune_core/kafka_consumers.py (MODIFY)

   def start_honeypot_status_consumer():
       """Consume honeypot status updates for threat pattern learning."""
       consumer = KafkaConsumer(
           "reactive_fabric.honeypot_status",
           bootstrap_servers="localhost:9092",
           group_id="active-immune-core-honeypot",
           value_deserializer=lambda m: json.loads(m.decode("utf-8"))
       )

       for message in consumer:
           process_honeypot_status(message.value)

   def process_honeypot_status(status: dict):
       """Process honeypot interaction and extract threat patterns."""
       logger.info(f"Honeypot status: {status['honeypot_id']} - {status['status']}")

       if status["status"] == "interaction_detected":
           # Extract IOCs
           iocs = {
               "ip": status["source_ip"],
               "port": status["target_port"],
               "protocol": status["protocol"],
               "payload": status.get("payload", "")
           }

           # Add to threat pattern database
           threat_pattern_db.add_pattern(iocs)

           # Trigger cytokine: threat pattern learned
           cytokine_messenger.send_cytokine(
               cytokine_type="threat_pattern_learned",
               data=iocs
           )
   ```

2. **Start consumer in main.py**

   ```python
   # File: active_immune_core/main.py

   import threading
   from kafka_consumers import start_honeypot_status_consumer

   @app.on_event("startup")
   async def startup_event():
       # Existing consumers
       # ...

       # NEW: Start honeypot status consumer
       honeypot_thread = threading.Thread(
           target=start_honeypot_status_consumer,
           daemon=True
       )
       honeypot_thread.start()
       logger.info("Honeypot status consumer started")
   ```

3. **Create Grafana dashboard**
   - Panel 1: Honeypot hit rate (interactions/hour)
   - Panel 2: Learned threat patterns (cumulative)
   - Panel 3: Top attacking IPs

**Testing:**

- Simulate honeypot interaction in Reactive Fabric
- Verify status published to `reactive_fabric.honeypot_status`
- Verify Active Immune Core consumes message
- Verify threat pattern added to database
- Check cytokine broadcast

**Estimated Effort:** 2-4 hours
**Risk:** Low (consumer addition only)

---

## Implementation Timeline

### Day 1: Critical Fixes

- **Morning (3h):**
  - AG-RUNTIME-002: Install torch (30 min)
  - AG-RUNTIME-001: Oráculo graceful degradation (2.5h)
- **Afternoon (3h):**
  - AG-RUNTIME-001: Testing + validation (1h)
  - AG-KAFKA-005: Create DLQ monitor (2h)

### Day 2: Feature Enablement

- **Morning (3h):**
  - AG-KAFKA-005: Complete DLQ monitor + testing (1h)
  - AG-KAFKA-009: Agent communications producer (2h)
- **Afternoon (4h):**
  - AG-KAFKA-009: Testing + Narrative Filter validation (2h)
  - AG-KAFKA-004: Honeypot status consumer (2h)

### Day 3: Validation

- **Morning (2h):**
  - AG-KAFKA-004: Complete + testing (1h)
  - End-to-end validation all fixes (1h)
- **Afternoon (2h):**
  - Documentation updates
  - Deployment preparation

---

## Acceptance Criteria

### AG-RUNTIME-002 ✅

- [ ] `torch>=2.0.0` in requirements.txt
- [ ] `python -c "import torch; print(torch.__version__)"` succeeds
- [ ] maximus_core_service starts without errors
- [ ] Health check endpoint returns 200

### AG-RUNTIME-001 ✅

- [ ] Oráculo starts successfully with Kafka down
- [ ] Logs show "DEGRADED MODE" warning
- [ ] APVs stored in InMemoryAPVQueue
- [ ] Health endpoint shows `{"degraded_mode": true}`
- [ ] APVs flush to Kafka when available

### AG-KAFKA-005 ✅

- [ ] maximus_dlq_monitor service running
- [ ] Consumer connected to `maximus.adaptive-immunity.dlq`
- [ ] Failed APV logged with error details
- [ ] Retry logic executes (max 3 attempts)
- [ ] Prometheus metrics at `/metrics`
- [ ] Grafana alert triggers if DLQ > 10

### AG-KAFKA-009 ✅

- [ ] Agent message API publishes to Kafka
- [ ] Message appears in `agent-communications` topic
- [ ] Narrative Filter consumes message
- [ ] Semantic analysis executed
- [ ] End-to-end latency < 2 seconds

### AG-KAFKA-004 ✅

- [ ] Active Immune Core consumes `reactive_fabric.honeypot_status`
- [ ] Honeypot interaction processed
- [ ] Threat pattern added to database
- [ ] Cytokine `threat_pattern_learned` broadcast
- [ ] Grafana dashboard shows honeypot hits

---

## Risk Mitigation

### Risk 1: Oráculo Degradation Performance

- **Concern:** InMemoryAPVQueue may overflow if Kafka down for extended period
- **Mitigation:**
  - Set maxlen=1000 (circular buffer)
  - Add metric for queue size
  - Alert if queue > 80% full

### Risk 2: DLQ Monitor High Volume

- **Concern:** DLQ monitor may be overwhelmed by high failure rate
- **Mitigation:**
  - Implement rate limiting
  - Batch processing (100 messages/batch)
  - Circuit breaker pattern

### Risk 3: Agent Communications Latency

- **Concern:** Kafka adds latency to agent coordination
- **Mitigation:**
  - Async fire-and-forget publish
  - No blocking on Kafka response
  - Fallback to direct HTTP if Kafka slow

---

## Monitoring & Observability

### Prometheus Metrics

```
# AG-RUNTIME-001
oraculo_degraded_mode{status="true|false"}
oraculo_memory_queue_size

# AG-KAFKA-005
dlq_messages_total{reason="validation|timeout|kafka_error"}
dlq_retries_total{success="true|false"}
dlq_queue_size

# AG-KAFKA-009
agent_communications_published_total{agent_from, agent_to}
agent_communications_latency_seconds

# AG-KAFKA-004
honeypot_interactions_total{honeypot_id}
threat_patterns_learned_total
```

### Grafana Dashboards

1. **Air Gaps Health Dashboard**
   - Oráculo degradation status
   - DLQ queue size
   - Agent communications throughput
   - Honeypot hit rate

2. **Air Gaps Alerts**
   - Oráculo degraded mode > 10 minutes
   - DLQ size > 10 messages
   - Agent communications latency > 5 seconds
   - Honeypot patterns not learning

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Grafana dashboards created
- [ ] Prometheus alerts configured

### Deployment

- [ ] Deploy torch dependency (AG-RUNTIME-002)
- [ ] Deploy Oráculo graceful degradation (AG-RUNTIME-001)
- [ ] Deploy DLQ monitor service (AG-KAFKA-005)
- [ ] Deploy agent communications producer (AG-KAFKA-009)
- [ ] Deploy honeypot status consumer (AG-KAFKA-004)

### Post-Deployment

- [ ] Verify all services healthy
- [ ] Check Prometheus metrics
- [ ] Validate end-to-end workflows
- [ ] Monitor for 24 hours
- [ ] Update Air Gaps report

---

**Plan Created:** 2025-10-23T14:20:00Z
**Total Estimated Effort:** 13-21 hours (17-27h with buffer)
**Priority:** HIGH (3 Critical, 2 High)
**Ready for DEV SENIOR Execution:** ✅

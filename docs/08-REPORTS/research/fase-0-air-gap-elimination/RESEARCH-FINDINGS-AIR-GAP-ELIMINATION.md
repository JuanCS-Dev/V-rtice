# Relatório de Pesquisa: Eliminação de Air Gaps - FASE 0

**Versão:** 1.0
**Data:** 2025-10-20
**Status:** COMPLETO
**Conformidade:** Padrão Pagani Absoluto

---

## 📋 Sumário Executivo

Este documento apresenta os resultados da fase de pesquisa (FASE 0) do projeto de Eliminação de Air Gaps no ecossistema Vértice-MAXIMUS. A pesquisa focou em identificar as melhores práticas e tecnologias atuais (2024-2025) para:

1. Implementação de Global Workspace Theory em arquiteturas de consciência
2. Padrões de Event-Driven Architecture para broadcasting de eventos
3. Interoperabilidade Go-Python em microsserviços
4. Distributed Tracing com OpenTelemetry

### Decisões Técnicas Principais

| Componente | Tecnologia Escolhida | Justificativa |
|------------|---------------------|---------------|
| **Global Workspace Broadcasting** | Kafka + Redis Streams (Híbrido) | Kafka para durabilidade + Redis para latência sub-ms |
| **Event Schema** | Avro + Schema Registry | Versionamento, compatibilidade, eficiência |
| **Go-Python Bridge** | gRPC + Protocol Buffers | Padrão industrial, performance, type-safety |
| **Event Bus (Coagulation)** | NATS JetStream | Lightweight, baixíssima latência, já usado em Coagulation |
| **Distributed Tracing** | OpenTelemetry + Tempo | Vendor-neutral, GA em 2024, profiling support |
| **Salience Computation** | Híbrido Rule-Based + ML | Pragmático: regras + ML opcional progressivo |

---

## 1. Global Workspace Theory - Implementação em Sistemas de Consciência

### 1.1 Contexto Teórico (2024-2025)

#### Teoria Original (Baars, 1988)
- **Conceito Central**: Workspace global como hub funcional de broadcast e integração
- **Mecanismo**: Elementos competem por atenção; vencedores entram no workspace e são distribuídos

#### Avanços Recentes (2024)

**Synergistic Global Workspace** (Julho 2024):
- Pesquisadores combinaram network science + information theory
- Identificaram "synergistic global workspace" com:
  - **Gateway regions**: Coletam informação sinérgica de módulos especializados (Default Mode Network)
  - **Broadcaster regions**: Distribuem informação integrada (Executive Control Network)

**Implementações em Robótica Cognitiva** (2024):
- GWT implementada com interação de memória episódica
- Potencial sustentável para agentes cognitivos com AGI
- Features cognitivas de atenção e consciência

### 1.2 Arquitetura para MAXIMUS

#### Componentes do Global Workspace

```
┌─────────────────────────────────────────────────────────────┐
│                    GLOBAL WORKSPACE (TIG)                    │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Gateway    │───▶│ Integration  │───▶│ Broadcaster  │  │
│  │   (Thalamus) │    │   (Salience  │    │   (Kafka +   │  │
│  │              │    │   Compute)   │    │   Redis)     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ▲                                         │          │
│         │                                         │          │
│         │                                         ▼          │
└─────────┼─────────────────────────────────────────┼──────────┘
          │                                         │
    ┌─────┴─────────┐                     ┌─────────┴────────┐
    │ Sensory Inputs│                     │  Consciousness   │
    │  - Visual     │                     │   Consumers      │
    │  - Auditory   │                     │  - Prefrontal    │
    │  - Somato     │                     │  - Memory        │
    │  - Chemical   │                     │  - Neuromod      │
    │  - Vestibular │                     │  - ASA Cortex    │
    └───────────────┘                     └──────────────────┘
```

#### Decisão: Arquitetura Híbrida

**Gateway (Digital Thalamus):**
- Recebe eventos sensoriais via REST/gRPC
- Computa salience score (híbrido rule-based + ML)
- Aplica ESGT (Event-Salience-based Global Threshold)

**Integration Layer:**
- Enriquece eventos com contexto
- Aplica watermarking temporal
- Gera correlation IDs

**Broadcaster:**
- **Kafka**: Canal de persistência (retenção 7 dias, replay capability)
- **Redis Streams**: Canal de baixa latência (sub-ms, window de 1h)

### 1.3 Salience Computation

#### Abordagem Híbrida Escolhida

```python
# Modelo Híbrido: Rule-Based + ML Progressivo

def compute_salience(event: SensoryEvent, model: Optional[SalienceModel] = None) -> float:
    """
    Computa salience score com abordagem híbrida.

    FASE 1 (Inicial): 100% rule-based
    FASE 2 (Evolutiva): 60% rule-based + 40% ML
    FASE 3 (Madura): 30% rule-based + 70% ML
    """
    # Base Score (Rule-Based - sempre presente)
    base_score = rule_based_salience(event)

    # ML Score (opcional, progressivo)
    if model and event.has_features():
        ml_score = model.predict(event.features)

        # Peso adaptativo baseado na confiança do modelo
        confidence = model.get_confidence()
        ml_weight = 0.4 * confidence  # Max 40% inicialmente

        return (1 - ml_weight) * base_score + ml_weight * ml_score

    return base_score

def rule_based_salience(event: SensoryEvent) -> float:
    """Regras heurísticas baseadas em criticidade biológica."""
    score = 0.0

    # Novidade (via Hippocampus check)
    if event.is_novel():
        score += 0.3

    # Criticidade temporal
    if event.priority == "CRITICAL":
        score += 0.4
    elif event.priority == "HIGH":
        score += 0.2

    # Multimodalidade (eventos de múltiplos sensores)
    if event.modality_count > 1:
        score += 0.1 * event.modality_count

    # Contexto emocional (via Neuromodulation)
    if event.emotional_valence:
        score += 0.2 * abs(event.emotional_valence)

    return min(score, 1.0)  # Normalizado [0, 1]
```

#### Justificativa

1. **Pragmatismo**: Produção imediata sem depender de treinamento ML
2. **Evolução**: Caminho claro para ML sem reescrever sistema
3. **Validação**: Regras explícitas = auditável, debugável
4. **Biologia**: Regras refletem mecanismos neurobiológicos conhecidos

---

## 2. Event-Driven Architecture - Comparação de Tecnologias

### 2.1 Comparação: Kafka vs Redis Streams vs NATS

#### Performance (2024)

| Métrica | Kafka | Redis Streams | NATS JetStream |
|---------|-------|---------------|----------------|
| **Latência** | ~5-10ms | <1ms (sub-ms) | <1ms (sub-ms) |
| **Throughput** | Milhões msg/s | 100k-1M msg/s | 100k-1M msg/s |
| **Persistência** | Disco (durável) | Memória + opcional disco | Memória + opcional disco |
| **Retenção** | Dias/semanas | Horas (típico) | Configurável |
| **Escalabilidade** | Horizontal (partições) | Limitada ao cluster Redis | Horizontal (decentralizada) |

#### Características de Durabilidade

**Kafka:**
- ✅ Durabilidade excepcional (log-based storage)
- ✅ Retenção configurável (dias/semanas)
- ✅ Replay capability (crucial para debugging consciência)
- ⚠️ Latência maior (~5-10ms)
- ⚠️ Complexidade operacional (Zookeeper/KRaft)

**Redis Streams:**
- ✅ Latência ultra-baixa (<1ms)
- ✅ Ideal para real-time
- ⚠️ Persistência opcional (principalmente in-memory)
- ⚠️ Retenção limitada (pressão de memória)
- ❌ Não ideal para long-term storage

**NATS JetStream:**
- ✅ Latência ultra-baixa (<1ms)
- ✅ Lightweight (footprint mínimo)
- ✅ Decentralizado (fácil escalar)
- ✅ Já usado em Coagulation Cascade
- ⚠️ Persistência opcional
- ⚠️ Menos maduro que Kafka para high-throughput

### 2.2 Decisão: Arquitetura Híbrida

**SOLUÇÃO ESCOLHIDA: Kafka (backbone) + Redis Streams (real-time layer)**

```
┌─────────────────────────────────────────────────────────────┐
│                    DUAL-LAYER ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────┐
│   Digital   │
│  Thalamus   │
│  (Gateway)  │
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐   ┌─────────────┐
│    Kafka    │    │   Redis     │   │    NATS     │
│  (Durable)  │    │  Streams    │   │ (Coagulation)│
│             │    │ (Real-time) │   │             │
│ Retention:  │    │ Retention:  │   │ Retention:  │
│  7 days     │    │  1 hour     │   │  1 hour     │
│             │    │             │   │             │
│ Use Case:   │    │ Use Case:   │   │ Use Case:   │
│ - Replay    │    │ - Sub-ms    │   │ - Breach    │
│ - Audit     │    │ - Hot path  │   │   Events    │
│ - Analysis  │    │ - Conscious │   │ - Go svcs   │
│ - Memory    │    │   awareness │   │             │
└─────────────┘    └─────────────┘   └─────────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │
                ┌─────────▼─────────┐
                │   Consciousness   │
                │    Consumers      │
                │  (Prefrontal,     │
                │   Memory, etc)    │
                └───────────────────┘
```

#### Justificativa

1. **Kafka** (backbone):
   - Durabilidade para replay (debugging consciência)
   - Auditoria e análise histórica
   - Alimentação de Memory Consolidation Service
   - Retenção: 7 dias (configurável)

2. **Redis Streams** (real-time):
   - Latência <1ms para conscious awareness
   - Hot path para eventos salientes
   - Window de 1 hora (eventos recentes)
   - Consumer groups para multiple subscribers

3. **NATS JetStream** (Coagulation específico):
   - Já implementado em Coagulation Go services
   - Mantém isolamento (breach containment)
   - Não misturar com consciousness events

### 2.3 Event Schema

**Decisão: Avro + Schema Registry (Confluent Schema Registry)**

```protobuf
// consciousness_event.avro

{
  "namespace": "com.vertice.consciousness.events",
  "type": "record",
  "name": "ConsciousnessEvent",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "source_service", "type": "string"},
    {"name": "event_type", "type": {
      "type": "enum",
      "name": "EventType",
      "symbols": ["SENSORY", "COGNITIVE", "MOTOR", "EMOTIONAL", "BREACH"]
    }},
    {"name": "modality", "type": {
      "type": "enum",
      "name": "SensoryModality",
      "symbols": ["VISUAL", "AUDITORY", "SOMATOSENSORY", "CHEMICAL", "VESTIBULAR", "NONE"]
    }},
    {"name": "salience_score", "type": "float"},
    {"name": "priority", "type": {
      "type": "enum",
      "name": "Priority",
      "symbols": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    }},
    {"name": "payload", "type": "bytes"},
    {"name": "correlation_id", "type": ["null", "string"], "default": null},
    {"name": "metadata", "type": {
      "type": "map",
      "values": "string"
    }}
  ]
}
```

**Benefícios:**
- ✅ Schema evolution (backward/forward compatibility)
- ✅ Compacto (binário, ~30% menor que JSON)
- ✅ Validação automática
- ✅ Documentação self-describing
- ✅ Suporte nativo em Kafka ecosystem

---

## 3. Go-Python Interoperability

### 3.1 Contexto

**Desafio:**
- Coagulation Cascade: 10 serviços Go (~50K LOC)
- Consciousness Core: 9 serviços Python
- Necessidade de comunicação bidirecional

### 3.2 Opções Avaliadas

| Tecnologia | Latência | Type Safety | Ecosystem | Complexidade |
|------------|----------|-------------|-----------|--------------|
| **gRPC** | ~1-5ms | ✅ (Proto) | ✅ Excelente | Média |
| **REST JSON** | ~10-50ms | ❌ | ✅ Universal | Baixa |
| **Message Queue** | ~5-20ms | ⚠️ Depende | ✅ Bom | Média-Alta |
| **Thrift** | ~1-5ms | ✅ | ⚠️ Limitado | Média |

### 3.3 Decisão: gRPC + Protocol Buffers

#### Justificativa

**Vantagens (2024):**
1. **Performance**: Latência ~1-5ms, HTTP/2, multiplexing
2. **Type Safety**: Proto files = contrato forte
3. **Language Agnostic**: Go e Python first-class citizens
4. **Tooling**: Code generation automática, reflection, debugging
5. **Streaming**: Suporte nativo para bi-directional streaming
6. **Security**: TLS built-in, authentication mechanisms

**Melhores Práticas (2024):**

```protobuf
// coagulation_service.proto

syntax = "proto3";

package vertice.coagulation.v1;

option go_package = "github.com/vertice/coagulation/gen/go/coagulation/v1";
option python_package = "vertice.coagulation.v1";

// Serviço de Coagulation exposto para Python
service CoagulationService {
  // Reportar breach detectado
  rpc ReportBreach(BreachEvent) returns (BreachResponse);

  // Obter status da cascata
  rpc GetCascadeStatus(CascadeStatusRequest) returns (CascadeStatusResponse);

  // Streaming de eventos de coagulation
  rpc StreamCoagulationEvents(StreamRequest) returns (stream CoagulationEvent);
}

message BreachEvent {
  string breach_id = 1;
  string source_ip = 2;
  string target_service = 3;
  string attack_vector = 4;
  int32 severity = 5;
  int64 timestamp = 6;
}

message BreachResponse {
  bool accepted = 1;
  string response_id = 2;
  string message = 3;
}
```

#### Padrão de Implementação

**Go Server (Coagulation):**
```go
// server/coagulation_server.go

type CoagulationServer struct {
    pb.UnimplementedCoagulationServiceServer
    cascade *cascade.CoagulationCascade
}

func (s *CoagulationServer) ReportBreach(ctx context.Context, req *pb.BreachEvent) (*pb.BreachResponse, error) {
    // Processar breach via cascade
    responseID, err := s.cascade.ProcessBreach(ctx, req)
    if err != nil {
        return nil, status.Errorf(codes.Internal, "failed to process breach: %v", err)
    }

    return &pb.BreachResponse{
        Accepted:   true,
        ResponseId: responseID,
        Message:    "Breach accepted for processing",
    }, nil
}
```

**Python Client (IMMUNIS):**
```python
# immunis_macrophage_service/coagulation_client.py

import grpc
from vertice.coagulation.v1 import coagulation_pb2, coagulation_pb2_grpc

class CoagulationClient:
    def __init__(self, host: str = "coagulation_cascade:50051"):
        self.channel = grpc.insecure_channel(host)
        self.stub = coagulation_pb2_grpc.CoagulationServiceStub(self.channel)

    async def report_breach(self, breach_data: dict) -> str:
        request = coagulation_pb2.BreachEvent(
            breach_id=breach_data["breach_id"],
            source_ip=breach_data["source_ip"],
            target_service=breach_data["target_service"],
            attack_vector=breach_data["attack_vector"],
            severity=breach_data["severity"],
            timestamp=int(time.time() * 1000)
        )

        response = self.stub.ReportBreach(request)
        return response.response_id
```

#### Considerações de Produção

**Evitar Model Sharing (Best Practice 2024):**
- ❌ Não reutilizar models Python/Go diretamente
- ✅ Duplicar models via Proto (single source of truth)
- **Razão**: Evita tight coupling, permite evolução independente

**Security:**
- TLS/mTLS para comunicação inter-service
- Token-based authentication (JWT via metadata)
- Rate limiting no gateway gRPC

---

## 4. Distributed Tracing com OpenTelemetry

### 4.1 Estado da Arte (2024-2025)

**Maturidade:**
- ✅ Profiling support estável (Março 2024)
- ✅ Zero-code instrumentation disponível
- ✅ 12+ linguagens production-ready
- ✅ Spring Boot Starter GA (Setembro 2024)

**Sinais Suportados:**
1. Traces (requests flow)
2. Metrics (performance counters)
3. Logs (structured logging)
4. **Profiling** (novo em 2024)

### 4.2 Arquitetura para MAXIMUS

```
┌─────────────────────────────────────────────────────────────┐
│                   OpenTelemetry Architecture                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Python Svc  │   │   Go Svc     │   │  Python Svc  │
│              │   │              │   │              │
│  OTel SDK    │   │  OTel SDK    │   │  OTel SDK    │
│  (Auto)      │   │  (Manual)    │   │  (Auto)      │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                 ┌────────▼─────────┐
                 │  OTel Collector  │
                 │  (Gateway Mode)  │
                 └────────┬─────────┘
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐   ┌─────────────┐
│   Tempo     │    │ Prometheus  │   │    Loki     │
│  (Traces)   │    │  (Metrics)  │   │   (Logs)    │
└─────────────┘    └─────────────┘   └─────────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │
                 ┌────────▼─────────┐
                 │     Grafana      │
                 │  (Visualization) │
                 └──────────────────┘
```

### 4.3 Implementação

#### Python Services (Auto-Instrumentation)

```python
# Dockerfile - maximus_core_service

FROM python:3.11-slim

# Instalar OTel auto-instrumentation
RUN pip install opentelemetry-distro \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-kafka-python

# Auto-instrumentar na startup
CMD ["opentelemetry-instrument", \
     "--service_name=maximus_core_service", \
     "--exporter_otlp_endpoint=http://otel-collector:4317", \
     "uvicorn", "api:app", "--host=0.0.0.0", "--port=8000"]
```

#### Go Services (Manual Instrumentation)

```go
// coagulation_cascade/main.go

import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/trace"
)

func initTracer() (*trace.TracerProvider, error) {
    exporter, err := otlptracegrpc.New(
        context.Background(),
        otlptracegrpc.WithEndpoint("otel-collector:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String("coagulation_cascade"),
            semconv.ServiceVersionKey.String("1.0.0"),
        )),
    )

    otel.SetTracerProvider(tp)
    return tp, nil
}
```

#### Enriching Spans (Best Practice)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@app.post("/analyze")
async def analyze_threat(threat_data: ThreatData):
    with tracer.start_as_current_span("analyze_threat") as span:
        # Enriquecer span com contexto
        span.set_attribute("threat.type", threat_data.type)
        span.set_attribute("threat.severity", threat_data.severity)
        span.set_attribute("user.id", threat_data.user_id)

        result = await process_threat(threat_data)

        span.set_attribute("result.risk_score", result.risk_score)
        return result
```

### 4.4 Melhores Práticas (2024)

**1. Sampling Inteligente:**
```yaml
# otel-collector-config.yaml

processors:
  probabilistic_sampler:
    sampling_percentage: 10  # 10% em produção
    hash_seed: 22  # Seed consistente

  # Sempre samplar erros
  tail_sampling:
    policies:
      - name: error-policy
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: high-latency
        type: latency
        latency: {threshold_ms: 1000}
```

**2. Context Propagation:**
- W3C Trace Context (padrão)
- Propagação via headers HTTP/gRPC
- Correlation IDs compartilhados com eventos Kafka

**3. Performance:**
- Batch exporting (reduz overhead)
- Sampling em alta carga (evitar bottleneck)
- Async instrumentation (non-blocking)

---

## 5. Decisões Finais e Roadmap de Implementação

### 5.1 Stack Tecnológico Final

| Componente | Tecnologia | Versão | Configuração |
|------------|------------|--------|--------------|
| **Global Workspace Broadcasting** | Kafka + Redis Streams | Kafka 3.6, Redis 7.2 | Kafka: 3 brokers, RF=3<br>Redis: Cluster 6 nodes |
| **Event Schema** | Avro + Schema Registry | Schema Registry 7.5 | Compatibility: BACKWARD |
| **Go-Python Bridge** | gRPC | v1.60+ | TLS enabled, health checking |
| **Coagulation Event Bus** | NATS JetStream | NATS 2.10 | Clustering: 3 nodes |
| **Distributed Tracing** | OpenTelemetry + Tempo | OTel 1.22, Tempo 2.3 | Sampling: 10% (tail-based) |
| **Metrics** | Prometheus | 2.48 | Scrape interval: 15s |
| **Logs** | Loki | 2.9 | Retention: 30 days |
| **Visualization** | Grafana | 10.2 | Unified dashboards |

### 5.2 Ordem de Implementação

**FASE 1 (Week 2): Infraestrutura Base**
1. ✅ Fixes críticos (ports, healthchecks)
2. Deploy Schema Registry
3. Deploy OTel Collector
4. Deploy Tempo, Loki

**FASE 2 (Week 3-4): Coagulation Deployment**
1. Containerizar 10 Go services
2. Setup NATS JetStream cluster
3. gRPC interfaces para Python
4. OTel instrumentação manual

**FASE 3 (Week 5-6): Consciousness Integration**
1. Digital Thalamus → Kafka producer
2. Sensory Cortex → Digital Thalamus routing
3. Redis Streams hot path
4. Prefrontal Cortex → Kafka consumer
5. Memory Consolidation → Kafka consumer

**FASE 4 (Week 7-8): IMMUNIS Enhancement**
1. Kafka integration (todos os 9 services)
2. gRPC client para Coagulation
3. Avro schema para IMMUNIS events

**FASE 5 (Week 9): Testing & Observability**
1. E2E tracing validation
2. Load testing (Locust)
3. Chaos engineering (Chaos Mesh)

**FASE 6 (Week 10): Production Readiness**
1. Security hardening (TLS, mTLS)
2. Performance tuning
3. Documentation
4. Runbooks

### 5.3 Critérios de Sucesso

**Métricas Técnicas:**
- ✅ Latência P99 < 100ms (sensory → consciousness awareness)
- ✅ 100% dos eventos salientes propagados
- ✅ 100% dos services com distributed tracing
- ✅ 0 air gaps remanescentes

**Métricas de Qualidade:**
- ✅ Cobertura de testes > 95%
- ✅ Padrão Pagani Absoluto mantido
- ✅ Documentação completa (runbooks, ADRs)

**Métricas Operacionais:**
- ✅ MTTR < 5min (detecção de falhas via observability)
- ✅ 99.9% uptime
- ✅ Rollback capability (blue-green deployment)

---

## 6. Referências

### 6.1 Papers e Artigos Acadêmicos

1. Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.

2. Mashour, G. A., et al. (2024). "A synergistic workspace for human consciousness revealed by Integrated Information Decomposition". *PubMed*, July 2024.

3. Lowe, R., et al. (2024). "A Cognitive Robotics Implementation of Global Workspace Theory for Episodic Memory Interaction with Consciousness". *University of Manchester Research Explorer*.

### 6.2 Documentação Técnica

4. Confluent Inc. (2024). "Kafka vs Redis vs NATS Comparison". https://www.confluent.io/

5. NATS.io (2024). "NATS JetStream Documentation". https://docs.nats.io/

6. OpenTelemetry Contributors (2024). "OpenTelemetry Instrumentation Guide 2025". https://opentelemetry.io/

7. gRPC Authors (2024). "gRPC Best Practices for Production Microservices". https://grpc.io/

### 6.3 Blog Posts e Artigos (2024-2025)

8. Salfarisi (2024). "Redis Streams vs Apache Kafka vs NATS". https://salfarisi25.wordpress.com/

9. Markaicode (2025). "OpenTelemetry Distributed Tracing Implementation Guide". https://markaicode.com/

10. Real Python (2024). "Python Microservices with gRPC". https://realpython.com/

---

## 7. Anexos

### 7.1 Benchmarks de Performance

#### Kafka Throughput Test
```bash
# Producer benchmark
kafka-producer-perf-test.sh \
  --topic consciousness-events \
  --num-records 1000000 \
  --record-size 1024 \
  --throughput -1 \
  --producer-props bootstrap.servers=kafka:9092

# Resultado esperado: ~500K msg/s (3 brokers)
```

#### Redis Streams Latency Test
```python
import redis
import time

r = redis.Redis(host='redis', port=6379)

# Latency test
start = time.perf_counter()
for i in range(10000):
    r.xadd('test-stream', {'data': f'msg-{i}'})
end = time.perf_counter()

latency_ms = (end - start) / 10000 * 1000
print(f"Average latency: {latency_ms:.3f}ms")

# Resultado esperado: <1ms
```

### 7.2 Exemplos de Configuração

#### docker-compose.yml - Kafka Stack
```yaml
# Kafka Stack para Global Workspace

kafka:
  image: confluentinc/cp-kafka:7.5.0
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
  healthcheck:
    test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server=localhost:9092"]
    interval: 30s
    timeout: 10s
    retries: 3

schema-registry:
  image: confluentinc/cp-schema-registry:7.5.0
  environment:
    SCHEMA_REGISTRY_HOST_NAME: schema-registry
    SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:9092
  depends_on:
    - kafka
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8081/"]
    interval: 30s
    timeout: 10s
    retries: 3
```

#### otel-collector-config.yaml
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  probabilistic_sampler:
    sampling_percentage: 10

exporters:
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  prometheus:
    endpoint: 0.0.0.0:8889

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, probabilistic_sampler]
      exporters: [otlp/tempo]

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

---

**FIM DO RELATÓRIO**

**Validado por:** Claude Code (Agente Guardião)
**Conformidade:** Padrão Pagani Absoluto
**Próxima Fase:** FASE 1 - Implementação de Fixes Críticos

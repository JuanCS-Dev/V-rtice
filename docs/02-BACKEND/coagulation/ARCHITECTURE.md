# Architecture - Coagulation Protocol

**See main blueprint**: [COAGULATION_CASCADE_BLUEPRINT.md](../../COAGULATION_CASCADE_BLUEPRINT.md)

This document provides quick reference to architecture decisions specific to this implementation.

---

## Component Mapping

### Biological → Computational

| Biological | Computational | Location |
|-----------|---------------|----------|
| Fator Tecidual | IoC Comparator | `detection/extrinsic_pathway/tissue_factor.go` |
| Colágeno Exposto | Anomaly Detector | `detection/intrinsic_pathway/collagen_sensor.go` |
| Plaquetas | Autonomous Agents | `platelet_agent/agent.go` |
| Factor VIIa | Trigger Dispatcher | `cascade/factor_viia_service.go` |
| Trombina | Policy Generator | `cascade/thrombin_burst.go` |
| Fibrina | Quarantine Rules | `cascade/fibrin_mesh.go` |
| Protein C/S | Context-Aware Inhibitor | `regulation/protein_c_service.go` |
| Antitrombina | Global Damper | `regulation/antithrombin_service.go` |

---

## Data Flow

```
Breach Event
     ↓
Platelet Agent Detection
     ↓
Signal to Detection Layer (gRPC)
     ↓
Via Extrínseca OR Via Intrínseca
     ↓
Factor VIIa Validation
     ↓
Cascade Activation (Factor Xa → Thrombin)
     ↓
Policy Generation (1 → 1000+ rules)
     ↓
Fibrin Mesh Application (eBPF/Calico)
     ↓
Protein C/S Regulation
     ↓
Quarantine Stabilized
```

---

## Technology Choices

- **Language**: Go 1.21+ (performance, concurrency primitives)
- **Communication**: gRPC + NATS JetStream (sub-ms latency)
- **Enforcement**: eBPF via Cilium/Calico (kernel-level, zero overhead)
- **ML**: Python microservices for Via Intrínseca (scikit-learn, PyTorch)
- **Orchestration**: Kubernetes 1.28+
- **Monitoring**: Prometheus + Grafana + Jaeger

---

## Deployment Model

### Development
- Docker Compose for local testing
- Mock NATS for unit tests
- Synthetic breach events

### Staging
- Kubernetes cluster (minikube/kind)
- Real NATS JetStream
- Red Team adversarial tests

### Production
- Multi-node K8s cluster
- Distributed NATS
- Canary deployment (5% → 100%)

---

## Performance Targets

| Metric | Target | How Measured |
|--------|--------|--------------|
| Detection Latency | <100ms | Prometheus histogram (breach → trigger) |
| Containment Latency | <1s | Prometheus histogram (trigger → quarantine) |
| Agent Overhead | <5% CPU | cAdvisor metrics |
| Amplification Ratio | >1000x | Rules generated / triggers |
| False Positive Rate | <1% | Manual review + LRR feedback |

---

## Security Considerations

1. **Agent Compromise**: Agents sign all messages with mTLS
2. **Event Bus Tampering**: NATS with authentication + encryption
3. **Regulation Bypass**: Protein C/S runs in separate trust domain
4. **Cascade DoS**: Antithrombin circuit breaker + rate limiting

---

## Future Enhancements

- **Adaptive Thresholds**: LRR-driven threshold tuning
- **Multi-Cluster**: Federated coagulation across clusters
- **Hardware Acceleration**: eBPF XDP for 10Gbps+ environments
- **Quantum-Resistant**: Post-quantum cryptography for gRPC

---

**Last Updated**: 2025-10-10 (Phase 0)

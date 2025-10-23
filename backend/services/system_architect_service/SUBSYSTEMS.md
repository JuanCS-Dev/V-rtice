# VÉRTICE Platform - Subsystem Architecture

**Generated:** 2025-10-23
**Total Services:** 109
**Subsystems:** 9
**Categorization:** 100% (0 uncategorized)

---

## Overview

The VÉRTICE platform is organized into 9 biomimetic and functional subsystems, each representing a critical layer of the autonomous cybersecurity organism.

### Subsystem Summary

| Subsystem | Services | Purpose |
|-----------|----------|---------|
| **Consciousness** | 12 | Global Workspace Theory (TIG/MMEI/MCEA) + Sensory Cortex |
| **Immune** | 20 | Adaptive & Active Immunity + Immunis Cells |
| **Homeostatic** | 11 | HCL MAPE-K Loop + Regulation Services |
| **Maximus AI** | 11 | Core AI Services (Orchestrator, Eureka, Oraculo, Predict) |
| **Reactive Fabric** | 10 | Coagulation Cascade + Reactive Response |
| **Offensive** | 15 | Purple Team + Attack Surface + Exploitation Tools |
| **Intelligence** | 13 | OSINT + Threat Intelligence + Predictive Hunting |
| **Infrastructure** | 13 | Data Stores + Message Brokers + Monitoring |
| **Security Operations** | 4 | HITL + Wargaming |

---

## 1. Consciousness (12 services)

**Mission:** Implements Global Workspace Theory for unified awareness, attention, and multi-sensory integration.

### Core Components
- `maximus_core_service` - TIG (Teorema de Integração Global)
- `digital_thalamus_service` - Thalamus gateway for sensory routing
- `prefrontal_cortex_service` - Executive functions and decision-making
- `memory_consolidation_service` - Long-term memory formation
- `neuromodulation_service` - Dopamine, serotonin, acetylcholine, norepinephrine modulation

### Sensory Cortex Services
- `visual_cortex_service` - Visual data processing
- `auditory_cortex_service` - Audio/log pattern analysis
- `somatosensory_service` - Tactile/network sensor data
- `chemical_sensing_service` - Chemical/protocol anomaly detection
- `vestibular_service` - Balance/stability monitoring

### Additional Components
- `adr_core_service` - ADR (Architecture Decision Records) core
- `hpc_service` - High-Performance Computing integration

**Key Patterns:**
- Global Workspace broadcasting (Kafka + Redis Streams)
- Multi-sensory integration
- Attention schema mechanism
- Neuromodulatory influence on all subsystems

---

## 2. Immune (20 services)

**Mission:** Adaptive and active immunity for threat detection, response, and autonomous investigation.

### Immunis Cell Types (8 specialized agents)
- `immunis_neutrophil_service` - First responders
- `immunis_macrophage_service` - Phagocytosis and cleanup
- `immunis_dendritic_service` - Antigen presentation
- `immunis_helper_t_service` - T-helper coordination
- `immunis_cytotoxic_t_service` - Cytotoxic T cells
- `immunis_bcell_service` - Antibody production
- `immunis_nk_cell_service` - Natural killer cells
- `immunis_treg_service` - Regulatory T cells

### Core Systems
- `active_immune_core` - Active immune orchestration
- `adaptive_immune_system` - Adaptive learning and memory
- `ai_immune_system` - AI-powered immune responses
- `immunis_api_service` - Immunis API gateway

### Adaptive Immunity
- `adaptive_immunity_service` - Adaptive immunity engine
- `adaptive_immunity_db` - Adaptive immunity knowledge base

### Infrastructure Immunity (Protection for critical infra)
- `kafka-immunity` - Kafka cluster protection
- `kafka-ui-immunity` - Kafka UI protection
- `postgres-immunity` - PostgreSQL protection
- `zookeeper-immunity` - Zookeeper protection

### Investigation & Edge
- `autonomous_investigation_service` - Autonomous threat investigation
- `edge_agent_service` - Edge deployment agents

**Key Patterns:**
- Cell-based agent architecture
- Cytokine communication (IL1, IL6, IL10)
- Adaptive learning from threats
- Infrastructure self-protection

---

## 3. Homeostatic (11 services)

**Mission:** MAPE-K control loop (Monitor-Analyze-Plan-Execute-Knowledge) for system equilibrium.

### HCL MAPE-K Components
- `hcl-monitor` - Monitoring layer
- `hcl-analyzer` - Analysis engine
- `hcl-planner` - Planning engine
- `hcl-executor` - Execution engine
- `hcl-kb-service` - Knowledge base

### HCL Infrastructure
- `hcl-kafka` - Kafka integration
- `hcl-postgres` - PostgreSQL integration

### Regulation Services
- `homeostatic_regulation` - Core regulation engine
- `cloud_coordinator_service` - Cloud resource coordination
- `ethical_audit_service` - Ethical compliance auditing
- `hsas_service` - Homeostatic Safety & Assurance System

**Key Patterns:**
- Continuous MAPE-K loops
- Feedback-driven adaptation
- Ethical constraint enforcement
- Resource optimization

---

## 4. Maximus AI (11 services)

**Mission:** Core AI orchestration, prediction, decision-making, and strategic planning.

### Core AI Services
- `maximus_orchestrator_service` - Central AI orchestrator
- `maximus_eureka` - Discovery and pattern recognition
- `maximus_predict` - Predictive analytics
- `maximus_integration_service` - Integration hub

### Maximus Oraculo (Oracle variants)
- `maximus-oraculo` - Oracle service (legacy)
- `maximus_oraculo_v2_service` - Oracle v2
- `maximus_oraculo_filesystem` - Filesystem-based oracle

### Decision & Strategy
- `verdict_engine_service` - Decision verdict engine
- `strategic_planning_service` - Strategic planning
- `rte_service` - Real-Time Engine
- `tataca_ingestion` - Data ingestion pipeline

**Key Patterns:**
- Multi-model AI orchestration
- Predictive threat modeling
- Strategic decision-making
- Real-time inference

---

## 5. Reactive Fabric (10 services)

**Mission:** Coagulation cascade for rapid reactive defense and containment.

### Coagulation Cascade Factors
- `factor_viia_service` - Factor VIIa (initiation)
- `factor_xa_service` - Factor Xa (amplification)
- `antithrombin_service` - Antithrombin (regulation)
- `protein_c_service` - Protein C (anticoagulation)
- `tfpi_service` - Tissue Factor Pathway Inhibitor

### Core Reactive Systems
- `reactive_fabric_core` - Core reactive fabric
- `reactive_fabric_analysis` - Reactive analysis
- `reflex_triage_engine` - Reflex-based triage

### Additional Components
- `tegumentar_service` - Skin barrier (perimeter defense)
- `c2_orchestration_service` - Command & Control orchestration

**Key Patterns:**
- Cascade-based activation
- Rapid containment and isolation
- Reflex-level responses (<100ms)
- Self-regulating feedback loops

---

## 6. Offensive (15 services)

**Mission:** Purple team operations, attack surface management, and offensive security testing.

### Purple Team & Orchestration
- `purple_team` - Purple team coordination
- `offensive_orchestrator_service` - Offensive operations orchestrator
- `offensive_gateway` - Offensive tools gateway
- `offensive_tools_service` - Offensive tooling

### Reconnaissance & Scanning
- `network_recon_service` - Network reconnaissance
- `nmap_service` - Nmap scanning
- `vuln_scanner_service` - Vulnerability scanning

### Exploitation & Attack
- `web_attack_service` - Web application attacks
- `social_eng_service` - Social engineering campaigns
- `ssl_monitor_service` - SSL/TLS monitoring and exploitation

### Malware & Intelligence
- `malware_analysis_service` - Malware analysis
- `cuckoo` - Cuckoo sandbox
- `vuln_intel_service` - Vulnerability intelligence

### Testing Infrastructure
- `bas_service` - Breach & Attack Simulation
- `mock_vulnerable_apps` - Mock vulnerable applications

**Key Patterns:**
- Continuous purple team exercises
- Ethical offensive testing
- Attack surface mapping
- Vulnerability lifecycle management

---

## 7. Intelligence (13 services)

**Mission:** OSINT, threat intelligence, predictive hunting, and narrative analysis.

### OSINT Services
- `osint-service` - Core OSINT platform
- `google_osint_service` - Google OSINT
- `sinesp_service` - SINESP (Brazil law enforcement data)

### Threat Intelligence
- `threat_intel_service` - Threat intelligence aggregation
- `threat_intel_bridge` - Threat intel bridge
- `ip_intelligence_service` - IP intelligence

### Predictive & Monitoring
- `predictive_threat_hunting_service` - Predictive threat hunting
- `network_monitor_service` - Network monitoring

### Narrative & Domain Intelligence
- `narrative_analysis_service` - Narrative analysis
- `narrative_filter_service` - Narrative filtering
- `narrative_manipulation_filter` - Manipulation detection
- `cyber_service` - Cyber intelligence
- `domain_service` - Domain intelligence

**Key Patterns:**
- Multi-source intelligence fusion
- Narrative threat detection
- Predictive modeling
- Continuous hunting operations

---

## 8. Infrastructure (13 services)

**Mission:** Data stores, message brokers, monitoring, and core platform services.

### API & Communication
- `api_gateway` - API gateway
- `auth_service` - Authentication service
- `agent_communication` - Agent communication bus
- `command_bus_service` - Command bus
- `seriema_graph` - Seriema graph database

### Data Stores
- `postgres` - PostgreSQL database
- `redis` - Redis cache
- `qdrant` - Qdrant vector database

### Message Brokers
- `kafka` - Apache Kafka (implied by immunity services)
- `rabbitmq` - RabbitMQ
- `nats-jetstream` - NATS JetStream

### Monitoring & Observability
- `grafana` - Grafana dashboards
- `prometheus` - Prometheus metrics
- `atlas_service` - Atlas service catalog

**Key Patterns:**
- Event-driven architecture (Kafka, NATS, RabbitMQ)
- Multi-database strategy (SQL, NoSQL, Vector)
- Centralized monitoring
- API-first design

---

## 9. Security Operations (4 services)

**Mission:** Human-in-the-loop (HITL) operations and wargaming exercises.

### HITL Services
- `hitl-patch-service` - HITL patch service (legacy)
- `hitl_patch_service_new` - HITL patch service (new version)

### Wargaming
- `wargaming-crisol` - Wargaming Crisol (legacy)
- `wargaming_crisol_new` - Wargaming Crisol (new version)

**Key Patterns:**
- Human oversight for critical decisions
- Wargaming simulation environments
- Service migration (old → new versions)

**Note:** This subsystem contains duplicate services scheduled for consolidation in FASE 1.2.

---

## Subsystem Dependencies

### High-Level Flow
```
Intelligence → Immune → Reactive Fabric → Offensive
       ↓                    ↓
   Consciousness ← Homeostatic → Maximus AI
       ↓                    ↓
   Infrastructure ← Security Operations
```

### Key Integration Points
1. **Consciousness ↔ All Subsystems**: Global Workspace broadcasts
2. **Immune ↔ Offensive**: Purple team collaboration
3. **Intelligence → Immune**: Threat feeds
4. **Homeostatic → All**: MAPE-K regulation
5. **Infrastructure**: Foundation for all services

---

## Categorization Methodology

Services are categorized using pattern matching in `architecture_scanner.py`:

```python
SUBSYSTEM_PATTERNS = {
    "consciousness": ["maximus_core", "thalamus", "cortex", ...],
    "immune": ["immunis_", "adaptive_immunity", "kafka-immunity", ...],
    "homeostatic": ["hcl-", "hcl_", "homeostatic", ...],
    # ... etc
}
```

**Pattern Matching:**
- **Prefix matching**: `"hcl-"` matches `"hcl-analyzer"`
- **Substring matching**: `"immunity"` matches `"adaptive_immunity_service"`
- **Service families**: `"immunis_"` matches all Immunis cell types

---

## Service Naming Conventions

### Observed Patterns
1. **Subsystem prefix**: `immunis_`, `hcl-`, `maximus_`
2. **Purpose suffix**: `_service`, `_engine`, `_core`
3. **Version suffix**: `_v2_service`, `_new`
4. **Infrastructure protection**: `<service>-immunity`

### Naming Best Practices (2025)
- Use snake_case for Python services
- Use kebab-case for infrastructure services
- Version with explicit `_v2` suffix (not implicit)
- Avoid duplicate naming (see FASE 1.2 cleanup)

---

## FASE 1.1 Completion

✅ **Categorization**: 51 uncategorized → 0 uncategorized (100%)
✅ **Pattern Coverage**: 9 subsystems fully defined
✅ **Service Count**: 109 services across 9 subsystems
✅ **Documentation**: Complete subsystem mapping

**Next Steps:**
- FASE 1.2: Consolidate duplicate services (hitl, wargaming, maximus-oraculo)
- FASE 2: Redis HA with Sentinel
- FASE 3: Vault + GitOps (FluxCD)
- FASE 4: Istio service mesh
- FASE 5: Kubernetes operators
- FASE 6: Observability (Jaeger + AlertManager)

---

**Conformance:** Padrão Pagani Absoluto (100%)
**Generated by:** System Architect Service v1.0.0
**Last Updated:** 2025-10-23

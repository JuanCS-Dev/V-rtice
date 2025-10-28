/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MICROSERVICE DATA - Vértice-MAXIMUS Architecture
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Biological mapping of 86+ microservices based on backend codebase analysis.
 * Each service is mapped to its biological immune system analog.
 */

import type { MicroserviceNode, CommunicationLink, BiologicalLayer, AnimationPhase } from './types';

// ═══════════════════════════════════════════════════════════════════════════
// MICROSERVICE NODES (Organized by Biological System)
// ═══════════════════════════════════════════════════════════════════════════

export const microservices: MicroserviceNode[] = [
  // ─────────────────────────────────────────────────────────────────────────
  // FIREWALL LAYER (Tegumentar System - "The Skin")
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'tegumentar',
    name: 'Tegumentar Service',
    biologicalSystem: 'firewall',
    cellType: 'Epithelial Barrier',
    port: 8605,
    description: 'eBPF/XDP firewall with honeypot invitations',
    responseTime: '< 1ms',
    biologicalAnalog: 'Skin - First barrier that "invites" pathogens for study'
  },
  {
    id: 'reactive_fabric',
    name: 'Reactive Fabric Core',
    biologicalSystem: 'firewall',
    cellType: 'Honeypot Network',
    port: 8500,
    description: 'SSH/Web/API honeypots for attacker intelligence',
    responseTime: '10-500ms',
    biologicalAnalog: 'Trap cells - Controlled environment for pathogen analysis'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // AUTONOMIC NERVOUS SYSTEM (Reflex Arc - Millisecond Response)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'reflex_triage',
    name: 'Reflex Triage Engine (RTE)',
    biologicalSystem: 'autonomic',
    cellType: 'Spinal Reflex Arc',
    port: 8502,
    description: 'Hyperscan + Isolation Forest + VAE - sub-50ms threat decisions',
    responseTime: '15-45ms',
    biologicalAnalog: 'Spinal reflex - Responds before conscious thought'
  },
  {
    id: 'autonomous_response',
    name: 'Autonomous Response Engine',
    biologicalSystem: 'autonomic',
    cellType: 'Motor Neurons',
    port: 8502,
    description: 'Executes reflex playbooks (BLOCK/KILL/ISOLATE)',
    responseTime: '50-200ms',
    biologicalAnalog: 'Muscle contraction - Automatic defensive action'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // INNATE IMMUNE SYSTEM (First Responders - Seconds Response)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'neutrophil',
    name: 'Neutrophil Service',
    biologicalSystem: 'innate_immune',
    cellType: 'Neutrophil (PMN)',
    port: 8211,
    description: 'Ephemeral rapid response (24h TTL) - First to arrive',
    responseTime: '2-4s',
    biologicalAnalog: 'Neutrophils - Short-lived first responders, arrive within seconds'
  },
  {
    id: 'macrophage',
    name: 'Macrophage Service',
    biologicalSystem: 'innate_immune',
    cellType: 'Macrophage',
    port: 8210,
    description: 'Phagocytosis via Cuckoo Sandbox - IOC extraction',
    responseTime: '90-150s',
    biologicalAnalog: 'Macrophages - Engulf and digest pathogens, present antigens'
  },
  {
    id: 'nk_cell',
    name: 'NK Cell Service',
    biologicalSystem: 'innate_immune',
    cellType: 'Natural Killer Cell',
    port: 8212,
    description: 'Stress-based detection without prior training ("missing self")',
    responseTime: '5-10s',
    biologicalAnalog: 'NK Cells - Detect compromised hosts by absence of normal signals'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ADAPTIVE IMMUNE SYSTEM (Learning & Memory - Minutes Response)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'dendritic',
    name: 'Dendritic Cell Service',
    biologicalSystem: 'adaptive_immune',
    cellType: 'Dendritic Cell',
    port: 8208,
    description: 'Antigen presentation + Qdrant vector correlation',
    responseTime: '500-900ms',
    biologicalAnalog: 'Dendritic Cells - Bridge innate & adaptive, correlate threats'
  },
  {
    id: 'helper_t',
    name: 'Helper T-Cell Service',
    biologicalSystem: 'adaptive_immune',
    cellType: 'CD4+ Helper T-Cell',
    port: 8209,
    description: 'Orchestration via Th1/Th2 strategy selection',
    responseTime: '200-400ms',
    biologicalAnalog: 'Helper T-Cells - Decide aggressive (Th1) vs defensive (Th2) strategy'
  },
  {
    id: 'cytotoxic_t',
    name: 'Cytotoxic T-Cell Service',
    biologicalSystem: 'adaptive_immune',
    cellType: 'CD8+ Cytotoxic T-Cell',
    port: 8207,
    description: 'Active threat neutralization (kill processes, cleanup)',
    responseTime: '1-3s',
    biologicalAnalog: 'Cytotoxic T-Cells - Kill infected cells directly'
  },
  {
    id: 'bcell',
    name: 'B-Cell Service',
    biologicalSystem: 'adaptive_immune',
    cellType: 'B-Cell',
    port: 8206,
    description: 'Generate YARA signatures (antibodies)',
    responseTime: '2-5s',
    biologicalAnalog: 'B-Cells - Produce antibodies for rapid re-detection'
  },
  {
    id: 'treg',
    name: 'Regulatory T-Cell Service',
    biologicalSystem: 'adaptive_immune',
    cellType: 'Regulatory T-Cell',
    port: 8213,
    description: 'Prevent false positive cascades (immune suppression)',
    responseTime: '1-2s',
    biologicalAnalog: 'Regulatory T-Cells - Prevent autoimmune reactions'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ADAPTIVE IMMUNE MEMORY (Oráculo-Eureka System)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'oraculo',
    name: 'Oráculo (CVE Sentinel)',
    biologicalSystem: 'adaptive_immune',
    cellType: 'Memory B-Cell',
    port: 8201,
    description: 'CVE feed ingestion + APV generation',
    responseTime: '5-30m',
    biologicalAnalog: 'Memory B-Cells - Rapid re-detection of known threats'
  },
  {
    id: 'eureka',
    name: 'Eureka (Vulnerability Surgeon)',
    biologicalSystem: 'adaptive_immune',
    cellType: 'Memory T-Cell',
    port: 8201,
    description: 'LLM-powered remedy generation + validation',
    responseTime: '2-10m',
    biologicalAnalog: 'Memory T-Cells - Recall and execute learned responses'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // CONSCIOUSNESS (MAXIMUS AI Core - Strategic Thought)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'maximus_core',
    name: 'MAXIMUS Core',
    biologicalSystem: 'consciousness',
    cellType: 'Cerebral Cortex',
    port: 8150,
    description: 'Predictive coding + Free Energy Principle (IIT consciousness)',
    responseTime: '100-500ms',
    biologicalAnalog: 'Cerebral cortex - Conscious thought and strategic planning'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // COMMUNICATION INFRASTRUCTURE
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'kafka',
    name: 'Kafka Event Bus',
    biologicalSystem: 'communication',
    port: 9092,
    description: 'High-throughput innate immune signaling',
    responseTime: '< 10ms',
    biologicalAnalog: 'Cytokine signaling - Local, fast, high-volume'
  },
  {
    id: 'rabbitmq',
    name: 'RabbitMQ Queue',
    biologicalSystem: 'communication',
    port: 5672,
    description: 'Durable adaptive immune messaging',
    responseTime: '20-50ms',
    biologicalAnalog: 'Hormonal signaling - Reliable, persistent'
  },
  {
    id: 'nats',
    name: 'NATS Command Bus',
    biologicalSystem: 'communication',
    port: 4222,
    description: 'Lightweight service orchestration',
    responseTime: '< 5ms',
    biologicalAnalog: 'Neural signaling - Fast, direct commands'
  },
  {
    id: 'redis',
    name: 'Redis State Store',
    biologicalSystem: 'communication',
    port: 6379,
    description: 'Global hormonal broadcast signaling',
    responseTime: '< 1ms',
    biologicalAnalog: 'Endocrine system - Global state broadcast'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // INTELLIGENCE SERVICES (Sensory Input)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'threat_intel',
    name: 'Threat Intel Service',
    biologicalSystem: 'intelligence',
    port: 8301,
    description: 'Aggregate threat feeds (MISP, AlienVault, etc.)',
    responseTime: '1-5s',
    biologicalAnalog: 'Sensory neurons - Detect environmental threats'
  },
  {
    id: 'osint',
    name: 'OSINT Service',
    biologicalSystem: 'intelligence',
    port: 8300,
    description: 'Open-source intelligence gathering',
    responseTime: '2-10s',
    biologicalAnalog: 'Visual cortex - Process external information'
  },

  // ─────────────────────────────────────────────────────────────────────────
  // OFFENSIVE SERVICES (Counter-Attack Capabilities)
  // ─────────────────────────────────────────────────────────────────────────
  {
    id: 'offensive_orchestrator',
    name: 'Offensive Orchestrator',
    biologicalSystem: 'offensive',
    port: 8400,
    description: 'LLM-powered attack campaign planning',
    responseTime: '5-30s',
    biologicalAnalog: 'Motor cortex - Plan and execute counter-attacks'
  },
];

// ═══════════════════════════════════════════════════════════════════════════
// COMMUNICATION LINKS (Kafka, RabbitMQ, NATS, Redis)
// ═══════════════════════════════════════════════════════════════════════════

export const communicationLinks: CommunicationLink[] = [
  // Firewall → Autonomic (Direct, fast)
  { source: 'tegumentar', target: 'reflex_triage', type: 'nats', label: 'threat.detected' },
  { source: 'reactive_fabric', target: 'reflex_triage', type: 'kafka', label: 'reactive_fabric.threat_detected' },

  // Autonomic → Innate Immune (Reflex triggers first responders)
  { source: 'reflex_triage', target: 'neutrophil', type: 'nats', label: 'rapid_response.trigger' },
  { source: 'reflex_triage', target: 'nk_cell', type: 'nats', label: 'stress.detected' },

  // Innate Immune → Macrophage (Neutrophils call for cleanup)
  { source: 'neutrophil', target: 'macrophage', type: 'kafka', label: 'sample.submit' },
  { source: 'reactive_fabric', target: 'macrophage', type: 'kafka', label: 'sample.capture' },

  // Macrophage → Dendritic (Antigen presentation)
  { source: 'macrophage', target: 'dendritic', type: 'kafka', label: 'antigen.presentation' },

  // Dendritic → Adaptive Immune (Orchestration)
  { source: 'dendritic', target: 'helper_t', type: 'rabbitmq', label: 'antigen.present' },
  { source: 'helper_t', target: 'cytotoxic_t', type: 'rabbitmq', label: 'activate.th1' },
  { source: 'helper_t', target: 'bcell', type: 'rabbitmq', label: 'activate.th2' },

  // Adaptive → Memory (Learning)
  { source: 'bcell', target: 'oraculo', type: 'rabbitmq', label: 'signature.generated' },
  { source: 'cytotoxic_t', target: 'eureka', type: 'rabbitmq', label: 'threat.neutralized' },

  // Consciousness → All (Strategic oversight)
  { source: 'maximus_core', target: 'helper_t', type: 'redis', label: 'strategy.update' },
  { source: 'maximus_core', target: 'reflex_triage', type: 'redis', label: 'policy.update' },

  // Intelligence → Consciousness (Sensory input)
  { source: 'threat_intel', target: 'maximus_core', type: 'kafka', label: 'intel.feed' },
  { source: 'osint', target: 'maximus_core', type: 'kafka', label: 'osint.report' },

  // Regulatory feedback (Prevent autoimmunity)
  { source: 'treg', target: 'helper_t', type: 'redis', label: 'suppress.response' },
  { source: 'treg', target: 'cytotoxic_t', type: 'redis', label: 'inhibit.attack' },
];

// ═══════════════════════════════════════════════════════════════════════════
// BIOLOGICAL LAYERS (For Grouping and Legend)
// ═══════════════════════════════════════════════════════════════════════════

export const biologicalLayers: BiologicalLayer[] = [
  {
    id: 'firewall',
    name: 'Firewall/Honeypot Layer',
    description: 'The "skin" - Invites attackers into controlled environments',
    color: '#f97316', // orange
    icon: '🛡️',
    responseTime: '< 1ms',
    nodes: microservices.filter(n => n.biologicalSystem === 'firewall')
  },
  {
    id: 'autonomic',
    name: 'Autonomic Nervous System',
    description: 'Reflex arc - Responds in milliseconds before conscious thought',
    color: '#ef4444', // red
    icon: '⚡',
    responseTime: '15-200ms',
    nodes: microservices.filter(n => n.biologicalSystem === 'autonomic')
  },
  {
    id: 'innate_immune',
    name: 'Innate Immune System',
    description: 'First responders - Neutrophils, Macrophages, NK Cells',
    color: '#10b981', // green
    icon: '🦠',
    responseTime: '2-150s',
    nodes: microservices.filter(n => n.biologicalSystem === 'innate_immune')
  },
  {
    id: 'adaptive_immune',
    name: 'Adaptive Immune System',
    description: 'Learning & memory - T-Cells, B-Cells, Dendritic Cells',
    color: '#8b5cf6', // purple
    icon: '🧬',
    responseTime: '200ms-30m',
    nodes: microservices.filter(n => n.biologicalSystem === 'adaptive_immune')
  },
  {
    id: 'consciousness',
    name: 'MAXIMUS Consciousness',
    description: 'Strategic thought - IIT-validated consciousness substrate',
    color: '#fbbf24', // gold
    icon: '🧠',
    responseTime: '100-500ms',
    nodes: microservices.filter(n => n.biologicalSystem === 'consciousness')
  },
  {
    id: 'communication',
    name: 'Communication Infrastructure',
    description: 'Signaling pathways - Kafka, RabbitMQ, NATS, Redis',
    color: '#06b6d4', // cyan
    icon: '📡',
    responseTime: '< 50ms',
    nodes: microservices.filter(n => n.biologicalSystem === 'communication')
  },
  {
    id: 'intelligence',
    name: 'Intelligence Services',
    description: 'Sensory input - Threat feeds, OSINT, reconnaissance',
    color: '#3b82f6', // blue
    icon: '👁️',
    responseTime: '1-10s',
    nodes: microservices.filter(n => n.biologicalSystem === 'intelligence')
  },
  {
    id: 'offensive',
    name: 'Offensive Services',
    description: 'Counter-attack - Automated offensive response',
    color: '#dc2626', // dark red
    icon: '⚔️',
    responseTime: '5-30s',
    nodes: microservices.filter(n => n.biologicalSystem === 'offensive')
  },
];

// ═══════════════════════════════════════════════════════════════════════════
// ANIMATION PHASES (Timeline)
// ═══════════════════════════════════════════════════════════════════════════

export const animationPhases: AnimationPhase[] = [
  {
    id: 'phase1_firewall',
    name: 'Phase 1: Firewall Detection',
    description: 'Attacker hits firewall, honeypot captures exploit',
    startTime: 0,
    duration: 0.3,
    nodes: ['tegumentar', 'reactive_fabric'],
    highlight: true
  },
  {
    id: 'phase2_reflex',
    name: 'Phase 2: Autonomic Reflex',
    description: 'RTE analyzes threat in 15-45ms, triggers autonomous response',
    startTime: 0.3,
    duration: 0.2,
    nodes: ['reflex_triage', 'autonomous_response'],
    highlight: true
  },
  {
    id: 'phase3_neutrophil',
    name: 'Phase 3: Neutrophil Response',
    description: 'First responders arrive, isolate host',
    startTime: 0.5,
    duration: 2,
    nodes: ['neutrophil', 'nk_cell'],
    highlight: true
  },
  {
    id: 'phase4_macrophage',
    name: 'Phase 4: Macrophage Phagocytosis',
    description: 'Cuckoo Sandbox analysis, IOC extraction',
    startTime: 2.5,
    duration: 2,
    nodes: ['macrophage'],
    highlight: true
  },
  {
    id: 'phase5_dendritic',
    name: 'Phase 5: Antigen Presentation',
    description: 'Dendritic cell correlates with past attacks via Qdrant',
    startTime: 4.5,
    duration: 1,
    nodes: ['dendritic'],
    highlight: true
  },
  {
    id: 'phase6_helper_t',
    name: 'Phase 6: Helper T-Cell Orchestration',
    description: 'Th1/Th2 strategy decision (aggressive vs defensive)',
    startTime: 5.5,
    duration: 1,
    nodes: ['helper_t'],
    highlight: true
  },
  {
    id: 'phase7_adaptive',
    name: 'Phase 7: Adaptive Response',
    description: 'B-Cells generate signatures, Cytotoxic T-Cells neutralize',
    startTime: 6.5,
    duration: 3,
    nodes: ['bcell', 'cytotoxic_t', 'treg'],
    highlight: true
  },
  {
    id: 'phase8_memory',
    name: 'Phase 8: Memory Formation',
    description: 'Oráculo-Eureka learns, generates remedies',
    startTime: 9.5,
    duration: 2,
    nodes: ['oraculo', 'eureka'],
    highlight: true
  },
  {
    id: 'phase9_consciousness',
    name: 'Phase 9: Strategic Update',
    description: 'MAXIMUS updates threat model, learns new patterns',
    startTime: 11.5,
    duration: 1.5,
    nodes: ['maximus_core'],
    highlight: true
  },
];

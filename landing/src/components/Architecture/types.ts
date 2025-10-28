/**
 * ═══════════════════════════════════════════════════════════════════════════
 * TYPE DEFINITIONS - Biological Architecture Flowchart
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * TypeScript interfaces for the animated biological architecture diagram.
 * Maps Vértice-MAXIMUS microservices to biological immune system analogs.
 */

export type BiologicalSystemType =
  | 'firewall'           // Tegumentar (skin barrier)
  | 'autonomic'          // Reflex Triage Engine
  | 'innate_immune'      // Neutrophils, Macrophages, NK Cells
  | 'adaptive_immune'    // T-Cells, B-Cells, Dendritic Cells
  | 'consciousness'      // MAXIMUS AI Core
  | 'communication'      // Kafka, RabbitMQ, NATS, Redis
  | 'intelligence'       // OSINT, Threat Intel
  | 'offensive'          // Red Team Services
  | 'sensory';           // Sensory Services

export type CommunicationType =
  | 'kafka'      // High-throughput event streaming (red)
  | 'rabbitmq'   // Durable messaging (blue)
  | 'nats'       // Fast command bus (green)
  | 'redis';     // Hormonal signaling (purple)

export interface MicroserviceNode {
  id: string;
  name: string;
  biologicalSystem: BiologicalSystemType;
  cellType?: string;              // e.g., "Neutrophil", "Macrophage", "T-Cell"
  port: number;
  description: string;
  responseTime: string;           // e.g., "5ms", "2s", "5m"
  biologicalAnalog: string;       // Human-readable biological function
}

export interface CommunicationLink {
  source: string;                 // Source node ID
  target: string;                 // Target node ID
  type: CommunicationType;
  label?: string;                 // e.g., "antigen.presentation", "threat.detected"
  bidirectional?: boolean;
}

export interface BiologicalLayer {
  id: BiologicalSystemType;
  name: string;
  description: string;
  color: string;                  // Hex color for visual grouping
  icon: string;                   // Emoji icon
  responseTime: string;           // Typical response time for this layer
  nodes: MicroserviceNode[];
}

export interface AnimationPhase {
  id: string;
  name: string;
  description: string;
  startTime: number;              // Seconds from animation start
  duration: number;               // Duration in seconds
  nodes: string[];                // Node IDs involved in this phase
  highlight: boolean;             // Whether to highlight these nodes
}

export interface FlowchartState {
  isPlaying: boolean;
  currentPhase: number;
  speed: number;                  // 0.5x, 1x, 2x, 5x
  selectedNode: string | null;
  hoveredNode: string | null;
}

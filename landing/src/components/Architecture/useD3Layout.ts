/**
 * ═══════════════════════════════════════════════════════════════════════════
 * useD3Layout Hook - Force-Directed Layout
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Uses D3's force simulation to organize microservices spatially.
 * Groups nodes by biological system for organic clustering.
 */

import { useEffect, useRef, useState } from 'react';
import {
  forceSimulation,
  forceCenter,
  forceLink,
  forceManyBody,
  forceCollide,
  type Simulation,
  type SimulationNodeDatum,
  type SimulationLinkDatum
} from 'd3-force';
import type { MicroserviceNode, CommunicationLink, BiologicalSystemType } from './types';

export interface LayoutNode extends SimulationNodeDatum {
  id: string;
  name: string;
  biologicalSystem: BiologicalSystemType;
  cellType?: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface LayoutLink extends SimulationLinkDatum<LayoutNode> {
  source: string | LayoutNode;
  target: string | LayoutNode;
  type: string;
}

interface UseD3LayoutProps {
  nodes: MicroserviceNode[];
  links: CommunicationLink[];
  width: number;
  height: number;
}

interface UseD3LayoutReturn {
  layoutNodes: LayoutNode[];
  layoutLinks: LayoutLink[];
  isStable: boolean;
}

export function useD3Layout({
  nodes,
  links,
  width,
  height
}: UseD3LayoutProps): UseD3LayoutReturn {
  const [layoutNodes, setLayoutNodes] = useState<LayoutNode[]>([]);
  const [layoutLinks, setLayoutLinks] = useState<LayoutLink[]>([]);
  const [isStable, setIsStable] = useState(false);
  const simulationRef = useRef<Simulation<LayoutNode, LayoutLink> | null>(null);

  useEffect(() => {
    // Convert microservice nodes to layout nodes
    const d3Nodes: LayoutNode[] = nodes.map(node => ({
      id: node.id,
      name: node.name,
      biologicalSystem: node.biologicalSystem,
      cellType: node.cellType,
      x: width / 2,
      y: height / 2
    }));

    // Convert communication links to layout links
    const d3Links: LayoutLink[] = links.map(link => ({
      source: link.source,
      target: link.target,
      type: link.type
    }));

    // Create force simulation
    const simulation = forceSimulation<LayoutNode>(d3Nodes)
      // Attraction to center
      .force('center', forceCenter(width / 2, height / 2))

      // Links between nodes
      .force('link', forceLink<LayoutNode, LayoutLink>(d3Links)
        .id((d: LayoutNode) => d.id)
        .distance(150)
        .strength(0.3)
      )

      // Repulsion between nodes
      .force('charge', forceManyBody()
        .strength(-300)
        .distanceMax(400)
      )

      // Prevent node overlap
      .force('collision', forceCollide<LayoutNode>()
        .radius(60)
        .strength(0.7)
      )

      // Group by biological system (cluster force)
      .force('cluster', forceCluster<LayoutNode>()
        .centers((d: LayoutNode) => getClusterCenter(d.biologicalSystem, width, height))
        .strength(0.2)
      );

    // Update state on each tick
    simulation.on('tick', () => {
      setLayoutNodes([...d3Nodes]);
      setLayoutLinks([...d3Links]);
    });

    // Mark as stable after simulation settles
    simulation.on('end', () => {
      setIsStable(true);
    });

    simulationRef.current = simulation;

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [nodes, links, width, height]);

  return { layoutNodes, layoutLinks, isStable };
}

// ═══════════════════════════════════════════════════════════════════════════
// CLUSTER FORCE (Group nodes by biological system)
// ═══════════════════════════════════════════════════════════════════════════

interface ClusterForce<NodeType extends SimulationNodeDatum> {
  (alpha: number): void;
  initialize?: (nodes: NodeType[]) => void;
  centers: (accessor: (node: NodeType) => { x: number; y: number }) => ClusterForce<NodeType>;
  strength: (strength: number) => ClusterForce<NodeType>;
}

function forceCluster<NodeType extends SimulationNodeDatum>(): ClusterForce<NodeType> {
  let nodes: NodeType[];
  let centersAccessor: (node: NodeType) => { x: number; y: number };
  let strength = 0.1;

  function force(alpha: number) {
    for (let i = 0, n = nodes.length; i < n; ++i) {
      const node = nodes[i] as any;
      const center = centersAccessor(node);
      node.vx += (center.x - node.x) * strength * alpha;
      node.vy += (center.y - node.y) * strength * alpha;
    }
  }

  force.initialize = function(_: NodeType[]) {
    nodes = _;
  };

  force.centers = function(accessor: (node: NodeType) => { x: number; y: number }) {
    centersAccessor = accessor;
    return force;
  };

  force.strength = function(s: number) {
    strength = s;
    return force;
  };

  return force;
}

// ═══════════════════════════════════════════════════════════════════════════
// CLUSTER CENTER POSITIONS (Radial arrangement)
// ═══════════════════════════════════════════════════════════════════════════

function getClusterCenter(
  biologicalSystem: BiologicalSystemType,
  width: number,
  height: number
): { x: number; y: number } {
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.35;

  // Map biological systems to radial positions (like a clock)
  const systemPositions: Record<BiologicalSystemType, number> = {
    'firewall': 0,           // 12 o'clock (top)
    'autonomic': Math.PI / 4,    // 1:30 (top-right)
    'innate_immune': Math.PI / 2,    // 3 o'clock (right)
    'adaptive_immune': (3 * Math.PI) / 4, // 4:30 (bottom-right)
    'consciousness': Math.PI,          // 6 o'clock (bottom)
    'communication': (5 * Math.PI) / 4, // 7:30 (bottom-left)
    'intelligence': (3 * Math.PI) / 2,  // 9 o'clock (left)
    'offensive': (7 * Math.PI) / 4,     // 10:30 (top-left)
    'sensory': 0                        // Default to top
  };

  const angle = systemPositions[biologicalSystem] || 0;

  return {
    x: centerX + radius * Math.cos(angle - Math.PI / 2), // -PI/2 to start at top
    y: centerY + radius * Math.sin(angle - Math.PI / 2)
  };
}

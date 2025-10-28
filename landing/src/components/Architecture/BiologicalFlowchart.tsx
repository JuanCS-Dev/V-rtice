/**
 * ═══════════════════════════════════════════════════════════════════════════
 * BIOLOGICAL FLOWCHART - Vértice-MAXIMUS Architecture Visualization
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Interactive animated flowchart showing the biological immune system cascade.
 * Demonstrates how Vértice-MAXIMUS responds to threats from milliseconds to hours.
 *
 * Technology: GSAP + D3.js hybrid approach
 * - D3: Spatial layout via force simulation
 * - GSAP: Timeline-based animations for immune cascade
 */

import { useRef, useState, useEffect } from 'react';
import { microservices, communicationLinks, animationPhases, biologicalLayers } from './MicroserviceData';
import { useD3Layout } from './useD3Layout';
import { useGSAPTimeline } from './useGSAPTimeline';
import type { FlowchartState } from './types';
import './BiologicalFlowchart.css';

const CANVAS_WIDTH = 1200;
const CANVAS_HEIGHT = 800;

export default function BiologicalFlowchart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [flowchartState, setFlowchartState] = useState<FlowchartState>({
    isPlaying: false,
    currentPhase: 0,
    speed: 1,
    selectedNode: null,
    hoveredNode: null
  });

  // D3 Layout (spatial organization)
  const { layoutNodes, layoutLinks, isStable } = useD3Layout({
    nodes: microservices,
    links: communicationLinks,
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT
  });

  // GSAP Timeline (animations)
  const { timeline, play, pause, restart, setSpeed, currentPhase } = useGSAPTimeline({
    phases: animationPhases,
    containerRef: svgRef,
    isLayoutStable: isStable,
    speed: flowchartState.speed
  });

  // Update current phase
  useEffect(() => {
    setFlowchartState(prev => ({ ...prev, currentPhase }));
  }, [currentPhase]);

  // Handle play/pause
  const handlePlayPause = () => {
    if (flowchartState.isPlaying) {
      pause();
    } else {
      play();
    }
    setFlowchartState(prev => ({ ...prev, isPlaying: !prev.isPlaying }));
  };

  // Handle restart
  const handleRestart = () => {
    restart();
    setFlowchartState(prev => ({ ...prev, isPlaying: true, currentPhase: 0 }));
  };

  // Handle speed change
  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed);
    setFlowchartState(prev => ({ ...prev, speed: newSpeed }));
  };

  // Handle node click
  const handleNodeClick = (nodeId: string) => {
    setFlowchartState(prev => ({
      ...prev,
      selectedNode: prev.selectedNode === nodeId ? null : nodeId
    }));
  };

  // Handle node hover
  const handleNodeHover = (nodeId: string | null) => {
    setFlowchartState(prev => ({ ...prev, hoveredNode: nodeId }));
  };

  // Get link color based on communication type
  const getLinkColor = (type: string): string => {
    const colors = {
      kafka: '#ef4444',    // red
      rabbitmq: '#3b82f6', // blue
      nats: '#10b981',     // green
      redis: '#a855f7'     // purple
    };
    return colors[type as keyof typeof colors] || '#6b7280';
  };

  // Get node color based on biological system
  const getNodeColor = (system: string): string => {
    const layer = biologicalLayers.find(l => l.id === system);
    return layer?.color || '#6b7280';
  };

  return (
    <div className="biological-flowchart-container">
      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* CONTROLS */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <div className="flowchart-controls">
        <button
          className="control-btn play-pause"
          onClick={handlePlayPause}
          aria-label={flowchartState.isPlaying ? 'Pause animation' : 'Play animation'}
        >
          {flowchartState.isPlaying ? '⏸️ Pause' : '▶️ Play'}
        </button>

        <button
          className="control-btn restart"
          onClick={handleRestart}
          aria-label="Restart animation"
        >
          🔄 Restart
        </button>

        <div className="speed-controls">
          <span className="speed-label">Speed:</span>
          {[0.5, 1, 2, 5].map(speed => (
            <button
              key={speed}
              className={`speed-btn ${flowchartState.speed === speed ? 'active' : ''}`}
              onClick={() => handleSpeedChange(speed)}
              aria-label={`${speed}x speed`}
            >
              {speed}x
            </button>
          ))}
        </div>

        <div className="phase-indicator">
          <span className="phase-label">Phase:</span>
          <span className="phase-name">
            {animationPhases[flowchartState.currentPhase]?.name || 'Ready'}
          </span>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* SVG CANVAS */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <svg
        ref={svgRef}
        className="flowchart-svg"
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
        style={{ opacity: isStable ? 1 : 0.3 }}
      >
        {/* Gradient definitions */}
        <defs>
          <radialGradient id="node-gradient">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.9" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0.4" />
          </radialGradient>

          {/* Arrow markers for links */}
          <marker
            id="arrow-kafka"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
          </marker>
          <marker
            id="arrow-rabbitmq"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
          </marker>
          <marker
            id="arrow-nats"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
          </marker>
          <marker
            id="arrow-redis"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#a855f7" />
          </marker>
        </defs>

        {/* Background grid */}
        <g className="grid" opacity="0.1">
          {Array.from({ length: 20 }).map((_, i) => (
            <line
              key={`h-${i}`}
              x1="0"
              y1={i * 40}
              x2={CANVAS_WIDTH}
              y2={i * 40}
              stroke="#ffffff"
              strokeWidth="0.5"
            />
          ))}
          {Array.from({ length: 30 }).map((_, i) => (
            <line
              key={`v-${i}`}
              x1={i * 40}
              y1="0"
              x2={i * 40}
              y2={CANVAS_HEIGHT}
              stroke="#ffffff"
              strokeWidth="0.5"
            />
          ))}
        </g>

        {/* Links (communication paths) */}
        <g className="links">
          {layoutLinks.map((link, index) => {
            const source = typeof link.source === 'object' ? link.source : null;
            const target = typeof link.target === 'object' ? link.target : null;
            if (!source || !target || !source.x || !source.y || !target.x || !target.y) return null;

            return (
              <g key={index}>
                <line
                  className={`link link-${link.type}`}
                  data-source={typeof link.source === 'object' ? link.source.id : link.source}
                  data-target={typeof link.target === 'object' ? link.target.id : link.target}
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={getLinkColor(link.type)}
                  strokeWidth="2"
                  strokeOpacity="0.3"
                  markerEnd={`url(#arrow-${link.type})`}
                />
                {/* Particle placeholder (animated via GSAP) */}
                <circle
                  className={`particle particle-${typeof link.target === 'object' ? link.target.id : link.target}`}
                  cx={source.x}
                  cy={source.y}
                  r="4"
                  fill={getLinkColor(link.type)}
                  opacity="0"
                />
              </g>
            );
          })}
        </g>

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* ATACANTES (Emojis) */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <g className="attackers">
          {/* Grupo de atacantes - posicionados no topo */}
          <g className="attacker-group" transform={`translate(${CANVAS_WIDTH / 2}, 50)`}>
            {/* Vírus 1 */}
            <g className="attacker-virus-1" transform="translate(-80, 0)">
              <text fontSize="32" textAnchor="middle">🦠</text>
              <text fontSize="10" textAnchor="middle" dy="25" fill="#ef4444" fontWeight="bold">Vírus</text>
            </g>

            {/* Malware 1 */}
            <g className="attacker-malware-1" transform="translate(-40, 0)">
              <text fontSize="32" textAnchor="middle">🐛</text>
              <text fontSize="10" textAnchor="middle" dy="25" fill="#dc2626" fontWeight="bold">Malware</text>
            </g>

            {/* Ransomware */}
            <g className="attacker-ransomware" transform="translate(0, 0)">
              <text fontSize="32" textAnchor="middle">🔐</text>
              <text fontSize="10" textAnchor="middle" dy="25" fill="#b91c1c" fontWeight="bold">Ransom</text>
            </g>

            {/* Trojan */}
            <g className="attacker-trojan" transform="translate(40, 0)">
              <text fontSize="32" textAnchor="middle">🎭</text>
              <text fontSize="10" textAnchor="middle" dy="25" fill="#991b1b" fontWeight="bold">Trojan</text>
            </g>

            {/* Worm */}
            <g className="attacker-worm" transform="translate(80, 0)">
              <text fontSize="32" textAnchor="middle">🪱</text>
              <text fontSize="10" textAnchor="middle" dy="25" fill="#7f1d1d" fontWeight="bold">Worm</text>
            </g>
          </g>

          {/* Efeitos de explosão (aparecem quando atacantes são destruídos) */}
          <g className="explosion-effects">
            <g className="explosion-1" transform={`translate(${CANVAS_WIDTH / 2 - 80}, 200)`} opacity="0">
              <text fontSize="40" textAnchor="middle">💥</text>
            </g>
            <g className="explosion-2" transform={`translate(${CANVAS_WIDTH / 2 - 40}, 200)`} opacity="0">
              <text fontSize="40" textAnchor="middle">💥</text>
            </g>
            <g className="explosion-3" transform={`translate(${CANVAS_WIDTH / 2}, 350)`} opacity="0">
              <text fontSize="40" textAnchor="middle">💥</text>
            </g>
            <g className="explosion-4" transform={`translate(${CANVAS_WIDTH / 2 + 40}, 350)`} opacity="0">
              <text fontSize="40" textAnchor="middle">💥</text>
            </g>
          </g>

          {/* Escudo de bloqueio */}
          <g className="shield-effect" transform={`translate(${CANVAS_WIDTH / 2}, 150)`} opacity="0">
            <text fontSize="50" textAnchor="middle">🛡️</text>
          </g>
        </g>

        {/* Nodes (microservices) */}
        <g className="nodes">
          {layoutNodes.map((node) => {
            const isSelected = flowchartState.selectedNode === node.id;
            const isHovered = flowchartState.hoveredNode === node.id;
            const radius = isSelected ? 35 : isHovered ? 30 : 25;

            return (
              <g
                key={node.id}
                className="node-group"
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => handleNodeClick(node.id)}
                onMouseEnter={() => handleNodeHover(node.id)}
                onMouseLeave={() => handleNodeHover(null)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  className={`node node-${node.biologicalSystem}`}
                  data-id={node.id}
                  data-system={node.biologicalSystem}
                  r={radius}
                  fill={getNodeColor(node.biologicalSystem)}
                  fillOpacity="0.3"
                  stroke={getNodeColor(node.biologicalSystem)}
                  strokeWidth="2"
                />

                {/* Node label */}
                <text
                  className="node-label"
                  textAnchor="middle"
                  dy="-35"
                  fill="#ffffff"
                  fontSize="10"
                  fontWeight="bold"
                  opacity={isHovered || isSelected ? "1" : "0"}
                >
                  {node.cellType || node.name}
                </text>

                {/* Dendritic rays (for Qdrant visualization) */}
                {node.id === 'dendritic' && (
                  <g className="dendritic-rays">
                    {Array.from({ length: 8 }).map((_, i) => (
                      <line
                        key={i}
                        x1="0"
                        y1="0"
                        x2={Math.cos((i * Math.PI) / 4) * 40}
                        y2={Math.sin((i * Math.PI) / 4) * 40}
                        stroke="#8b5cf6"
                        strokeWidth="2"
                        opacity="0"
                      />
                    ))}
                  </g>
                )}

                {/* Antibody particles (for B-Cell) */}
                {node.id === 'bcell' && (
                  <g className="antibody-particles">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <circle
                        key={i}
                        className="antibody-particle"
                        cx="0"
                        cy="0"
                        r="3"
                        fill="#c084fc"
                        opacity="0"
                      />
                    ))}
                  </g>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* LEGEND */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <div className="flowchart-legend">
        <h3 className="legend-title">Biological Systems</h3>
        <div className="legend-items">
          {biologicalLayers.map((layer) => (
            <div key={layer.id} className="legend-item">
              <div
                className="legend-color"
                style={{ backgroundColor: layer.color }}
              />
              <div className="legend-info">
                <span className="legend-icon">{layer.icon}</span>
                <span className="legend-name">{layer.name}</span>
                <span className="legend-response-time">({layer.responseTime})</span>
              </div>
            </div>
          ))}
        </div>

        <h3 className="legend-title" style={{ marginTop: '2rem' }}>Communication</h3>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-line" style={{ backgroundColor: '#ef4444' }} />
            <span>Kafka (High-throughput)</span>
          </div>
          <div className="legend-item">
            <div className="legend-line" style={{ backgroundColor: '#3b82f6' }} />
            <span>RabbitMQ (Durable)</span>
          </div>
          <div className="legend-item">
            <div className="legend-line" style={{ backgroundColor: '#10b981' }} />
            <span>NATS (Fast commands)</span>
          </div>
          <div className="legend-item">
            <div className="legend-line" style={{ backgroundColor: '#a855f7' }} />
            <span>Redis (Global state)</span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* NODE DETAILS PANEL */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      {flowchartState.selectedNode && (
        <div className="node-details-panel">
          {(() => {
            const node = microservices.find(n => n.id === flowchartState.selectedNode);
            if (!node) return null;

            return (
              <>
                <button
                  className="close-btn"
                  onClick={() => setFlowchartState(prev => ({ ...prev, selectedNode: null }))}
                  aria-label="Close details"
                >
                  ✕
                </button>
                <h3 className="node-title">{node.name}</h3>
                <div className="node-detail">
                  <strong>Cell Type:</strong> {node.cellType || 'N/A'}
                </div>
                <div className="node-detail">
                  <strong>Port:</strong> {node.port}
                </div>
                <div className="node-detail">
                  <strong>Response Time:</strong> {node.responseTime}
                </div>
                <div className="node-detail">
                  <strong>Description:</strong>
                  <p>{node.description}</p>
                </div>
                <div className="node-detail">
                  <strong>Biological Analog:</strong>
                  <p>{node.biologicalAnalog}</p>
                </div>
              </>
            );
          })()}
        </div>
      )}

      {/* Loading state */}
      {!isStable && (
        <div className="loading-overlay">
          <div className="loading-spinner" />
          <p>Organizing biological systems...</p>
        </div>
      )}
    </div>
  );
}

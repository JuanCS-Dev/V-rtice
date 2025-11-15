/**
 * RelationshipGraph - Alliance Network Visualization
 * Simple force-directed graph without external dependencies
 * 
 * @version 1.0.0
 */

import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import styles from './RelationshipGraph.module.css';

export const RelationshipGraph = ({ graphData = { nodes: [], edges: [] } }) => {
  const { t } = useTranslation();
  const canvasRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = canvas.offsetHeight;

    const nodes = graphData.nodes.map(node => ({
      ...node,
      x: Math.random() * width,
      y: Math.random() * height,
      vx: 0,
      vy: 0
    }));

    const edges = graphData.edges;

    const render = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
      ctx.fillRect(0, 0, width, height);

      // Draw edges
      edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);
        if (!source || !target) return;

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = `rgba(239, 68, 68, ${edge.strength || 0.5})`;
        ctx.lineWidth = (edge.strength || 0.5) * 3;
        ctx.stroke();
      });

      // Draw nodes
      nodes.forEach(node => {
        const radius = 8 + (node.threat_level || 0) * 5;
        
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = node.status === 'ACTIVE' ? '#ef4444' : '#6b7280';
        ctx.fill();
        
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.font = '10px "Courier New"';
        ctx.textAlign = 'center';
        ctx.fillText(node.label || node.id.slice(0, 8), node.x, node.y + radius + 12);
      });

      // Simple physics
      nodes.forEach(node => {
        node.vx *= 0.95;
        node.vy *= 0.95;
        
        // Center attraction
        node.vx += (width / 2 - node.x) * 0.001;
        node.vy += (height / 2 - node.y) * 0.001;

        node.x += node.vx;
        node.y += node.vy;

        // Bounds
        if (node.x < 20) node.x = 20;
        if (node.x > width - 20) node.x = width - 20;
        if (node.y < 20) node.y = 20;
        if (node.y > height - 20) node.y = height - 20;
      });

      animationRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [graphData]);

  return (
    <div className={styles.relationshipGraph}>
      <div className={styles.graphHeader}>
        <h3>
          <span>🕸️</span>
          {t('cockpit.graph.title', 'Rede de Alianças')}
        </h3>
        <div className={styles.graphStats}>
          <span>{graphData.nodes.length} agentes</span>
          <span>{graphData.edges.length} conexões</span>
        </div>
      </div>
      <canvas 
        ref={canvasRef} 
        className={styles.graphCanvas}
      />
    </div>
  );
};

RelationshipGraph.propTypes = {
  graphData: PropTypes.shape({
    nodes: PropTypes.array,
    edges: PropTypes.array
  })
};

// defaultProps migrated to default parameters (React 18 compatible)

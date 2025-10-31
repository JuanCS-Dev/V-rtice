/**
 * CognitiveMapViewer - Visualização de Mapa Cognitivo (D3.js)
 * ============================================================
 *
 * Renderiza o grafo Neo4j como force-directed graph usando D3.js.
 *
 * Features:
 * - Nodes = Páginas web mapeadas
 * - Edges = Links/navegações entre páginas
 * - Color coding por domínio
 * - Size baseado em número de elementos aprendidos
 * - Zoom + Pan
 * - Tooltip on hover
 * - Click para detalhes
 */

import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import styles from "./CognitiveMapViewer.module.css";

export const CognitiveMapViewer = ({ graph, isLoading }) => {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Update dimensions on mount and resize
  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current) {
        const container = svgRef.current.parentElement;
        setDimensions({
          width: container.clientWidth,
          height: container.clientHeight,
        });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // Render D3 graph
  useEffect(() => {
    if (!graph || !graph.nodes || !graph.edges || dimensions.width === 0)
      return;

    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);

    // Clear previous content
    svg.selectAll("*").remove();

    // Create main group with zoom behavior
    const g = svg.append("g");

    const zoom = d3
      .zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3
      .forceSimulation(graph.nodes)
      .force(
        "link",
        d3
          .forceLink(graph.edges)
          .id((d) => d.id)
          .distance(100),
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force(
        "collision",
        d3.forceCollide().radius((d) => (d.elements || 0) / 2 + 20),
      );

    // Color scale by domain
    const domains = [...new Set(graph.nodes.map((n) => n.domain))];
    const colorScale = d3
      .scaleOrdinal()
      .domain(domains)
      .range(d3.schemeCategory10);

    // Draw links
    const link = g
      .append("g")
      .selectAll("line")
      .data(graph.edges)
      .enter()
      .append("line")
      .attr("class", styles.link)
      .attr("stroke", "#666")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.6);

    // Draw nodes
    const node = g
      .append("g")
      .selectAll("circle")
      .data(graph.nodes)
      .enter()
      .append("circle")
      .attr("class", styles.node)
      .attr("r", (d) => Math.max(5, Math.min(20, (d.elements || 0) / 5 + 5)))
      .attr("fill", (d) => colorScale(d.domain))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("cursor", "pointer")
      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended),
      )
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
      })
      .on("mouseover", function (event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", (d) =>
            Math.max(7, Math.min(25, (d.elements || 0) / 5 + 8)),
          )
          .attr("stroke-width", 3);
      })
      .on("mouseout", function (event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", (d) =>
            Math.max(5, Math.min(20, (d.elements || 0) / 5 + 5)),
          )
          .attr("stroke-width", 2);
      });

    // Add labels
    const label = g
      .append("g")
      .selectAll("text")
      .data(graph.nodes)
      .enter()
      .append("text")
      .attr("class", styles.label)
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("font-size", "10px")
      .attr("fill", "#fff")
      .text((d) => d.label || d.url?.substring(0, 20) || "Unknown");

    // Tick function
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);

      label.attr("x", (d) => d.x).attr("y", (d) => d.y + 30);
    });

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [graph, dimensions]);

  const handleCloseDetails = () => {
    setSelectedNode(null);
  };

  // Empty state
  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon}>🧠</div>
        <h3>Cognitive Map vazio</h3>
        <p>
          Nenhuma página foi mapeada ainda. Crie uma sessão de browser para
          começar.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.viewer}>
      <div className={styles.graphContainer}>
        <svg ref={svgRef} className={styles.svg} width="100%" height="100%" />

        {/* Instructions */}
        <div className={styles.instructions}>
          <p>
            🖱️ Arraste para mover • 🔍 Scroll para zoom • 👆 Clique no nó para
            detalhes
          </p>
        </div>

        {/* Legend */}
        <div className={styles.legend}>
          <h4>Legenda</h4>
          <div className={styles.legendItem}>
            <div
              className={styles.legendCircle}
              style={{ width: "10px" }}
            ></div>
            <span>Poucas interações</span>
          </div>
          <div className={styles.legendItem}>
            <div
              className={styles.legendCircle}
              style={{ width: "20px" }}
            ></div>
            <span>Muitas interações</span>
          </div>
        </div>
      </div>

      {/* Node Details Panel */}
      {selectedNode && (
        <div className={styles.detailsPanel}>
          <div className={styles.detailsHeader}>
            <h3>📄 Detalhes da Página</h3>
            <button
              className={styles.closeButton}
              onClick={handleCloseDetails}
              aria-label="Fechar detalhes"
            >
              ✕
            </button>
          </div>

          <div className={styles.detailsContent}>
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>URL:</span>
              <span className={styles.detailValue}>{selectedNode.url}</span>
            </div>

            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>Domínio:</span>
              <span className={styles.detailValue}>{selectedNode.domain}</span>
            </div>

            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>Elementos Aprendidos:</span>
              <span className={styles.detailValue}>
                {selectedNode.elements || 0}
              </span>
            </div>

            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>Visitado em:</span>
              <span className={styles.detailValue}>
                {selectedNode.visited_at
                  ? new Date(selectedNode.visited_at).toLocaleString("pt-BR")
                  : "N/A"}
              </span>
            </div>

            {selectedNode.title && (
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Título:</span>
                <span className={styles.detailValue}>{selectedNode.title}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CognitiveMapViewer;

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * DISTRIBUTED TOPOLOGY WIDGET - FASE 10 Distributed Organism
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza topologia do organismo distribuído:
 * - Edge Agents Status
 * - Global Metrics
 * - Network Topology
 * - Load Distribution
 */

import logger from "@/utils/logger";
import React, { useState, useEffect } from "react";
import { getGlobalMetrics, getTopology } from "../../../api/maximusAI";
import "./DistributedTopologyWidget.css";

export const DistributedTopologyWidget = () => {
  const [activeView, setActiveView] = useState("topology");
  const [loading, setLoading] = useState(false);
  const [topology, setTopology] = useState(null);
  const [globalMetrics, setGlobalMetrics] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchTopology = async () => {
    setLoading(true);
    try {
      const result = await getTopology();
      setTopology(result);
    } catch (error) {
      logger.error("Topology fetch failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGlobalMetrics = async () => {
    try {
      const result = await getGlobalMetrics(60);
      setGlobalMetrics(result);
    } catch (error) {
      logger.error("Metrics fetch failed:", error);
    }
  };

  useEffect(() => {
    if (activeView === "topology") {
      fetchTopology();
    } else if (activeView === "metrics") {
      fetchGlobalMetrics();
    }
  }, [activeView]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      if (activeView === "topology") {
        fetchTopology();
      } else if (activeView === "metrics") {
        fetchGlobalMetrics();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [autoRefresh, activeView]);

  const getHealthClass = (health) => {
    switch (health) {
      case "healthy":
        return "bg-success";
      case "degraded":
        return "bg-warning";
      case "unhealthy":
        return "bg-critical";
      default:
        return "bg-low";
    }
  };

  return (
    <div className="distributed-topology-widget">
      <div className="widget-header">
        <h3>🌐 Distributed Organism</h3>
        <div className="header-controls">
          <span className="badge fase10">FASE 10</span>
          <label className="refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
        </div>
      </div>

      <div className="view-selector">
        <button
          className={`view-btn ${activeView === "topology" ? "active" : ""}`}
          onClick={() => setActiveView("topology")}
        >
          📊 Topology
        </button>
        <button
          className={`view-btn ${activeView === "metrics" ? "active" : ""}`}
          onClick={() => setActiveView("metrics")}
        >
          📈 Global Metrics
        </button>
      </div>

      {activeView === "topology" && (
        <div className="topology-view">
          {loading && <div className="loading">Loading topology...</div>}

          {topology && !loading && (
            <>
              <div className="topology-summary">
                <div className="summary-card">
                  <span className="summary-label">Total Agents</span>
                  <span className="summary-value">
                    {topology.agent_count || 0}
                  </span>
                </div>
                <div className="summary-card">
                  <span className="summary-label">Healthy</span>
                  <span className="summary-value healthy">
                    {topology.healthy_count || 0}
                  </span>
                </div>
                <div className="summary-card">
                  <span className="summary-label">Regions</span>
                  <span className="summary-value">
                    {topology.regions?.length || 0}
                  </span>
                </div>
              </div>

              <div className="agents-grid">
                {topology.agents?.length > 0 ? (
                  topology.agents.map((agent, idx) => (
                    <div key={idx} className="agent-card">
                      <div className="agent-header">
                        <span className="agent-id">
                          {agent.id || `agent-${idx}`}
                        </span>
                        <span
                          className={`health-indicator ${getHealthClass(agent.health)}`}
                        />
                      </div>
                      <div className="agent-info">
                        <div className="info-row">
                          <span className="info-label">Location:</span>
                          <span className="info-value">
                            {agent.location || "Unknown"}
                          </span>
                        </div>
                        <div className="info-row">
                          <span className="info-label">Buffer:</span>
                          <span className="info-value">
                            {agent.buffer_utilization || 0}%
                          </span>
                        </div>
                        <div className="info-row">
                          <span className="info-label">Events/s:</span>
                          <span className="info-value">
                            {agent.events_per_second || 0}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="no-agents">No agents available</p>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {activeView === "metrics" && (
        <div className="metrics-view">
          {globalMetrics && (
            <>
              <div className="metric-card primary">
                <span className="metric-label">Global Throughput</span>
                <span className="metric-value">
                  {globalMetrics.events_per_second || 0}
                  <span className="metric-unit">events/s</span>
                </span>
              </div>

              <div className="metrics-grid">
                <div className="metric-card">
                  <span className="metric-label">Avg Compression</span>
                  <span className="metric-value">
                    {((globalMetrics.avg_compression_ratio || 0) * 100).toFixed(
                      1,
                    )}
                    %
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">P95 Latency</span>
                  <span className="metric-value">
                    {globalMetrics.p95_latency_ms || 0}
                    <span className="metric-unit">ms</span>
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Total Events</span>
                  <span className="metric-value">
                    {(globalMetrics.total_events || 0).toLocaleString()}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Data Transferred</span>
                  <span className="metric-value">
                    {((globalMetrics.total_bytes || 0) / 1024 / 1024).toFixed(
                      2,
                    )}
                    <span className="metric-unit">MB</span>
                  </span>
                </div>
              </div>
            </>
          )}

          {!globalMetrics && (
            <div className="placeholder">
              <p>Loading global metrics...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

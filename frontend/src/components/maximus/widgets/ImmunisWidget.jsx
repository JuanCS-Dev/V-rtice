/**
 * ═══════════════════════════════════════════════════════════════════════════
 * IMMUNIS WIDGET - Digital Immune System
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza o sistema imunológico digital completo:
 * - IMUNIDADE INATA: Neutrófilos, Macrófagos, NK Cells
 * - IMUNIDADE ADAPTATIVA: Células Dendríticas, Helper T, Cytotoxic T, B Cells
 * - CITOCINAS: Sinais de comunicação inter-celular
 * - ANTICORPOS: Biblioteca de defesas específicas
 * - MEMÓRIA IMUNOLÓGICA: Células de memória para respostas rápidas
 */

import logger from "@/utils/logger";
import React, { useState, useEffect } from "react";
import { API_ENDPOINTS } from "@/config/api";
import { formatDate } from "@/utils/dateHelpers";
import "./ImmunisWidget.css";

export const ImmunisWidget = ({ systemHealth: _systemHealth }) => {
  const [innateStatus, setInnateStatus] = useState(null);
  const [adaptiveStatus, setAdaptiveStatus] = useState(null);
  const [cytokineActivity, setCytokineActivity] = useState(null);
  const [antibodies, setAntibodies] = useState([]);
  const [memoryCells, setMemoryCells] = useState([]);
  const [selectedView, setSelectedView] = useState("overview"); // 'overview', 'innate', 'adaptive', 'cytokines', 'antibodies', 'memory'
  const [loading, setLoading] = useState(true);

  // Fetch innate immunity status
  useEffect(() => {
    const fetchInnate = async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.innate}/status`);
        if (response.ok) {
          const data = await response.json();
          setInnateStatus(data);
        }
      } catch (error) {
        logger.error("Failed to fetch innate status:", error);
      }
    };

    fetchInnate();
    const interval = setInterval(fetchInnate, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch adaptive immunity status
  useEffect(() => {
    const fetchAdaptive = async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.adaptive}/status`);
        if (response.ok) {
          const data = await response.json();
          setAdaptiveStatus(data);
          setLoading(false);
        }
      } catch (error) {
        logger.error("Failed to fetch adaptive status:", error);
      }
    };

    fetchAdaptive();
    const interval = setInterval(fetchAdaptive, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch cytokine activity
  useEffect(() => {
    const fetchCytokines = async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.cytokines}/signals`);
        if (response.ok) {
          const data = await response.json();
          setCytokineActivity(data);
        }
      } catch (error) {
        logger.error("Failed to fetch cytokine activity:", error);
      }
    };

    fetchCytokines();
    const interval = setInterval(fetchCytokines, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch antibodies
  useEffect(() => {
    const fetchAntibodies = async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.antibody}/library`);
        if (response.ok) {
          const data = await response.json();
          setAntibodies(data.antibodies || []);
        }
      } catch (error) {
        logger.error("Failed to fetch antibodies:", error);
      }
    };

    fetchAntibodies();
    const interval = setInterval(fetchAntibodies, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch memory cells
  useEffect(() => {
    const fetchMemory = async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.memory}/cells`);
        if (response.ok) {
          const data = await response.json();
          setMemoryCells(data.memory_cells || []);
        }
      } catch (error) {
        logger.error("Failed to fetch memory cells:", error);
      }
    };

    fetchMemory();
    const interval = setInterval(fetchMemory, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="immunis-loading">
        <div className="loading-spinner"></div>
        <p>Loading immune system data...</p>
      </div>
    );
  }

  const renderOverview = () => {
    const inflammationLevel = cytokineActivity?.inflammation_level || 0;
    const totalEliminations = innateStatus?.total_pathogens_eliminated || 0;

    return (
      <div className="immunis-overview">
        {/* System Health Gauge */}
        <div className="immune-health-section">
          <h3 className="section-title">🦠 Immune System Health</h3>
          <div className="health-gauge-container">
            <svg className="health-gauge" viewBox="0 0 200 120">
              <path
                className="gauge-background"
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="#1f2937"
                strokeWidth="20"
              />
              <path
                className="gauge-fill"
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke={
                  inflammationLevel < 0.3
                    ? "#10b981"
                    : inflammationLevel < 0.7
                      ? "#f59e0b"
                      : "#ef4444"
                }
                strokeWidth="20"
                strokeDasharray={`${(1 - inflammationLevel) * 251.2} 251.2`}
                strokeLinecap="round"
              />
              <text
                x="100"
                y="90"
                className="gauge-text"
                textAnchor="middle"
                fontSize="28"
                fill="#fff"
              >
                {((1 - inflammationLevel) * 100).toFixed(0)}%
              </text>
              <text
                x="100"
                y="110"
                className="gauge-label"
                textAnchor="middle"
                fontSize="10"
                fill="#9ca3af"
              >
                HEALTH (LOW INFLAMMATION)
              </text>
            </svg>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="immune-stats-grid">
          <div className="immune-stat-card">
            <div className="stat-icon">🛡️</div>
            <div className="stat-info">
              <div className="stat-value">{totalEliminations}</div>
              <div className="stat-label">Pathogens Eliminated</div>
            </div>
          </div>

          <div className="immune-stat-card">
            <div className="stat-icon">🔬</div>
            <div className="stat-info">
              <div className="stat-value">{antibodies.length}</div>
              <div className="stat-label">Antibodies</div>
            </div>
          </div>

          <div className="immune-stat-card">
            <div className="stat-icon">💾</div>
            <div className="stat-info">
              <div className="stat-value">{memoryCells.length}</div>
              <div className="stat-label">Memory Cells</div>
            </div>
          </div>

          <div className="immune-stat-card">
            <div className="stat-icon">📡</div>
            <div className="stat-info">
              <div className="stat-value">
                {cytokineActivity?.active_signals?.length || 0}
              </div>
              <div className="stat-label">Active Signals</div>
            </div>
          </div>
        </div>

        {/* Innate vs Adaptive */}
        <div className="immunity-comparison">
          <div className="immunity-column innate-column">
            <h4 className="column-title">🛡️ INNATE IMMUNITY</h4>
            <div className="cell-types">
              <div className="cell-type-item">
                <span className="cell-icon">⚪</span>
                <span className="cell-name">Neutrophils</span>
                <span className="cell-status">Active</span>
              </div>
              <div className="cell-type-item">
                <span className="cell-icon">🔴</span>
                <span className="cell-name">Macrophages</span>
                <span className="cell-status">Active</span>
              </div>
              <div className="cell-type-item">
                <span className="cell-icon">⚡</span>
                <span className="cell-name">NK Cells</span>
                <span className="cell-status">Active</span>
              </div>
            </div>
            <button
              onClick={() => setSelectedView("innate")}
              className="btn-view-details"
            >
              View Details →
            </button>
          </div>

          <div className="immunity-column adaptive-column">
            <h4 className="column-title">🧬 ADAPTIVE IMMUNITY</h4>
            <div className="cell-types">
              <div className="cell-type-item">
                <span className="cell-icon">🌳</span>
                <span className="cell-name">Dendritic Cells</span>
                <span className="cell-status">Active</span>
              </div>
              <div className="cell-type-item">
                <span className="cell-icon">🔵</span>
                <span className="cell-name">Helper T Cells</span>
                <span className="cell-status">Active</span>
              </div>
              <div className="cell-type-item">
                <span className="cell-icon">🟣</span>
                <span className="cell-name">Cytotoxic T Cells</span>
                <span className="cell-status">Active</span>
              </div>
              <div className="cell-type-item">
                <span className="cell-icon">🟢</span>
                <span className="cell-name">B Cells</span>
                <span className="cell-status">Active</span>
              </div>
            </div>
            <button
              onClick={() => setSelectedView("adaptive")}
              className="btn-view-details"
            >
              View Details →
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderInnate = () => (
    <div className="innate-view">
      <h3 className="section-title">🛡️ Innate Immunity Status</h3>
      {innateStatus && (
        <>
          <div className="innate-stats">
            <div className="stat-card">
              <strong>Total Threats Detected:</strong>
              <span>{innateStatus.total_threats_detected}</span>
            </div>
            <div className="stat-card">
              <strong>Pathogens Eliminated:</strong>
              <span>{innateStatus.total_pathogens_eliminated}</span>
            </div>
            <div className="stat-card">
              <strong>Avg Response Time:</strong>
              <span>{innateStatus.average_response_time.toFixed(2)}ms</span>
            </div>
          </div>

          <div className="cell-details-grid">
            <div className="cell-detail-card">
              <h4 className="cell-name">⚪ Neutrophils</h4>
              <div className="cell-stats">
                <div>
                  Activations:{" "}
                  {innateStatus.neutrophils?.total_activations || 0}
                </div>
                <div>
                  Eliminations:{" "}
                  {innateStatus.neutrophils?.successful_eliminations || 0}
                </div>
              </div>
            </div>

            <div className="cell-detail-card">
              <h4 className="cell-name">🔴 Macrophages</h4>
              <div className="cell-stats">
                <div>
                  Phagocytosis:{" "}
                  {innateStatus.macrophages?.total_phagocytosis || 0}
                </div>
                <div>
                  Success:{" "}
                  {innateStatus.macrophages?.successful_phagocytosis || 0}
                </div>
              </div>
            </div>

            <div className="cell-detail-card">
              <h4 className="cell-name">⚡ NK Cells</h4>
              <div className="cell-stats">
                <div>
                  Total Kills: {innateStatus.nk_cells?.total_kills || 0}
                </div>
                <div>
                  Successful: {innateStatus.nk_cells?.successful_kills || 0}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderAdaptive = () => (
    <div className="adaptive-view">
      <h3 className="section-title">🧬 Adaptive Immunity Status</h3>
      {adaptiveStatus && (
        <>
          <div className="adaptive-stats">
            <div className="stat-card">
              <strong>Antibodies Produced:</strong>
              <span>{adaptiveStatus.antibodies_produced}</span>
            </div>
            <div className="stat-card">
              <strong>Memory Cells:</strong>
              <span>{adaptiveStatus.memory_cells_count}</span>
            </div>
            <div className="stat-card">
              <strong>Antigen Repertoire:</strong>
              <span>{adaptiveStatus.antigen_repertoire_size}</span>
            </div>
          </div>

          <div className="cell-details-grid">
            <div className="cell-detail-card">
              <h4 className="cell-name">🌳 Dendritic Cells</h4>
              <div className="cell-stats">
                <p>Professional antigen presenting cells</p>
              </div>
            </div>

            <div className="cell-detail-card">
              <h4 className="cell-name">🔵 Helper T Cells</h4>
              <div className="cell-stats">
                <p>Coordinate adaptive immune response</p>
              </div>
            </div>

            <div className="cell-detail-card">
              <h4 className="cell-name">🟣 Cytotoxic T Cells</h4>
              <div className="cell-stats">
                <p>Kill infected or compromised cells</p>
              </div>
            </div>

            <div className="cell-detail-card">
              <h4 className="cell-name">🟢 B Cells</h4>
              <div className="cell-stats">
                <p>Produce specific antibodies</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderCytokines = () => (
    <div className="cytokines-view">
      <h3 className="section-title">📡 Cytokine Signaling</h3>
      {cytokineActivity && (
        <>
          <div className="cytokine-stats">
            <div className="stat-card">
              <strong>Active Signals:</strong>
              <span>{cytokineActivity.active_signals.length}</span>
            </div>
            <div className="stat-card">
              <strong>Total Signals:</strong>
              <span>{cytokineActivity.total_signals}</span>
            </div>
            <div className="stat-card">
              <strong>Inflammation Level:</strong>
              <span
                className={
                  cytokineActivity.inflammation_level > 0.7
                    ? "inflammation-high"
                    : "inflammation-low"
                }
              >
                {(cytokineActivity.inflammation_level * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="cytokine-signals-list">
            {cytokineActivity.active_signals.slice(0, 10).map((signal, idx) => (
              <div key={idx} className="cytokine-signal-item">
                <div className="signal-type">{signal.cytokine_type}</div>
                <div className="signal-path">
                  {signal.source_cell} → {signal.target_cells.join(", ")}
                </div>
                <div className="signal-effect">{signal.effect}</div>
                <div className="signal-concentration">
                  Conc: {signal.concentration.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );

  const renderAntibodies = () => (
    <div className="antibodies-view">
      <h3 className="section-title">
        🔬 Antibody Library ({antibodies.length})
      </h3>
      <div className="antibodies-grid">
        {antibodies.slice(0, 12).map((antibody) => (
          <div key={antibody.antibody_id} className="antibody-card">
            <div className="antibody-header">
              <span className="antibody-class">{antibody.antibody_class}</span>
              <span className="antibody-affinity">
                Affinity: {(antibody.affinity * 100).toFixed(0)}%
              </span>
            </div>
            <div className="antibody-body">
              <div className="antibody-target">
                Target: {antibody.antigen_target}
              </div>
              <div className="antibody-stats">
                <span>Conc: {antibody.concentration.toFixed(2)}</span>
                <span>Half-life: {antibody.half_life_hours.toFixed(1)}h</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMemory = () => (
    <div className="memory-view">
      <h3 className="section-title">💾 Memory Cells ({memoryCells.length})</h3>
      <div className="memory-cells-list">
        {memoryCells.map((cell) => (
          <div key={cell.cell_id} className="memory-cell-card">
            <div className="memory-header">
              <span className="cell-type">{cell.cell_type}</span>
              <span className="activation-count">
                Activations: {cell.activation_count}
              </span>
            </div>
            <div className="memory-body">
              <div className="antigen-specificity">
                Antigen: {cell.antigen_specificity}
              </div>
              <div className="memory-dates">
                Created:{" "}
                {formatDate(cell.created_at, { dateStyle: "short" }, "N/A")}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderActiveView = () => {
    switch (selectedView) {
      case "innate":
        return renderInnate();
      case "adaptive":
        return renderAdaptive();
      case "cytokines":
        return renderCytokines();
      case "antibodies":
        return renderAntibodies();
      case "memory":
        return renderMemory();
      default:
        return renderOverview();
    }
  };

  return (
    <div className="immunis-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <h2 className="widget-title">🦠 Immunis - Digital Immune System</h2>
          <p className="widget-subtitle">Innate + Adaptive Immunity</p>
        </div>
      </div>

      {/* View Navigation */}
      <div className="view-navigation">
        {[
          { id: "overview", name: "Overview", icon: "📊" },
          { id: "innate", name: "Innate", icon: "🛡️" },
          { id: "adaptive", name: "Adaptive", icon: "🧬" },
          { id: "cytokines", name: "Cytokines", icon: "📡" },
          { id: "antibodies", name: "Antibodies", icon: "🔬" },
          { id: "memory", name: "Memory", icon: "💾" },
        ].map((view) => (
          <button
            key={view.id}
            onClick={() => setSelectedView(view.id)}
            className={`view-tab ${selectedView === view.id ? "active" : ""}`}
          >
            <span className="view-icon">{view.icon}</span>
            <span className="view-name">{view.name}</span>
          </button>
        ))}
      </div>

      {/* Active View Content */}
      <div className="view-content">{renderActiveView()}</div>

      {/* Biological Inspiration */}
      <div className="bio-inspiration">
        <h3 className="bio-title">🧠 Biological Inspiration</h3>
        <p>
          <strong>Innate Immunity:</strong> First-line defense (Neutrophils,
          Macrophages, NK Cells) - fast, non-specific response to threats.
        </p>
        <p>
          <strong>Adaptive Immunity:</strong> Learned defense (T Cells, B Cells)
          - slow but specific, creates memory for future encounters.
        </p>
        <p>
          <strong>Cytokines:</strong> Communication molecules that coordinate
          immune response between cells.
        </p>
      </div>
    </div>
  );
};

export default ImmunisWidget;

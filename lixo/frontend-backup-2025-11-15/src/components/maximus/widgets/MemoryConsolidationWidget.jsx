import { API_ENDPOINTS } from "@/config/api";
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MEMORY CONSOLIDATION WIDGET - Hippocampal Replay Engine
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza o sistema de consolidação de memória:
 * - SLEEP/WAKE Modes
 * - Experience Replay Buffer
 * - Prioritized Experience Replay
 * - Consolidation Statistics
 */

import logger from "@/utils/logger";
import React, { useState, useEffect } from "react";
import "./MemoryConsolidationWidget.css";

export const MemoryConsolidationWidget = ({ systemHealth: _systemHealth }) => {
  const [currentMode, setCurrentMode] = useState("WAKE");
  const [bufferStats, setBufferStats] = useState({
    current_size: 0,
    capacity: 10000,
    utilization_percent: 0,
    total_experiences_added: 0,
    total_samples_drawn: 0,
    prioritized_replay_enabled: true,
  });
  const [consolidationStats, setConsolidationStats] = useState({
    total_consolidations: 0,
    sleep_consolidations: 0,
    wake_consolidations: 0,
    total_experiences_consolidated: 0,
    average_batch_size: 0,
    uptime_hours: 0,
  });
  const [loading, setLoading] = useState(true);

  // Fetch buffer stats
  useEffect(() => {
    const fetchBufferStats = async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.buffer}/stats`);
        if (response.ok) {
          const data = await response.json();
          setBufferStats(data);
        }
      } catch (error) {
        logger.error("Failed to fetch buffer stats:", error);
      }
    };

    fetchBufferStats();
    const interval = setInterval(fetchBufferStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch consolidation stats
  useEffect(() => {
    const fetchConsolidationStats = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.stats);
        if (response.ok) {
          const data = await response.json();
          setConsolidationStats(data);
          setCurrentMode(data.current_mode);
          setLoading(false);
        }
      } catch (error) {
        logger.error("Failed to fetch consolidation stats:", error);
      }
    };

    fetchConsolidationStats();
    const interval = setInterval(fetchConsolidationStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleMode = async (targetMode) => {
    try {
      const endpoint =
        targetMode === "SLEEP" ? API_ENDPOINTS.sleep : API_ENDPOINTS.wake;
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        const data = await response.json();
        logger.debug(`Mode transition:`, data);
        setCurrentMode(data.new_mode);
      }
    } catch (error) {
      logger.error(`Failed to switch to ${targetMode}:`, error);
    }
  };

  const triggerConsolidation = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.consolidate, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          batch_size: 64,
          strategy: "prioritized",
        }),
      });

      if (response.ok) {
        const data = await response.json();
        logger.debug("Manual consolidation:", data);
      }
    } catch (error) {
      logger.error("Failed to trigger consolidation:", error);
    }
  };

  if (loading) {
    return (
      <div className="memory-loading">
        <div className="loading-spinner"></div>
        <p>Loading memory consolidation data...</p>
      </div>
    );
  }

  return (
    <div className="memory-consolidation-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <h2 className="widget-title">💾 Memory Consolidation Engine</h2>
          <p className="widget-subtitle">
            Hippocampal Replay - Experience Consolidation
          </p>
        </div>
        <div className="header-right">
          <div className={`mode-badge ${currentMode.toLowerCase()}`}>
            {currentMode === "SLEEP" ? "😴" : "👁️"} {currentMode} MODE
          </div>
        </div>
      </div>

      {/* Mode Controls */}
      <div className="mode-controls">
        <button
          onClick={() => toggleMode("WAKE")}
          className={`btn-mode ${currentMode === "WAKE" ? "active" : ""}`}
          disabled={currentMode === "WAKE"}
        >
          👁️ WAKE Mode
          <span className="mode-desc">Continuous consolidation</span>
        </button>
        <button
          onClick={() => toggleMode("SLEEP")}
          className={`btn-mode ${currentMode === "SLEEP" ? "active" : ""}`}
          disabled={currentMode === "SLEEP"}
        >
          😴 SLEEP Mode
          <span className="mode-desc">Deep replay</span>
        </button>
        <button onClick={triggerConsolidation} className="btn-consolidate">
          ⚡ Trigger Consolidation
          <span className="mode-desc">Manual batch processing</span>
        </button>
      </div>

      {/* Buffer Status */}
      <div className="buffer-section">
        <h3 className="section-title">📦 Experience Replay Buffer</h3>
        <div className="buffer-stats-grid">
          <div className="buffer-stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-info">
              <div className="stat-value">
                {bufferStats.current_size.toLocaleString()}
              </div>
              <div className="stat-label">Experiences Stored</div>
            </div>
          </div>

          <div className="buffer-stat-card">
            <div className="stat-icon">💽</div>
            <div className="stat-info">
              <div className="stat-value">
                {bufferStats.capacity.toLocaleString()}
              </div>
              <div className="stat-label">Buffer Capacity</div>
            </div>
          </div>

          <div className="buffer-stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-info">
              <div className="stat-value">
                {bufferStats.utilization_percent.toFixed(1)}%
              </div>
              <div className="stat-label">Utilization</div>
            </div>
          </div>

          <div className="buffer-stat-card">
            <div className="stat-icon">🔄</div>
            <div className="stat-info">
              <div className="stat-value">
                {bufferStats.total_samples_drawn.toLocaleString()}
              </div>
              <div className="stat-label">Samples Drawn</div>
            </div>
          </div>
        </div>

        {/* Buffer Utilization Bar */}
        <div className="buffer-utilization">
          <div className="utilization-header">
            <span>Buffer Utilization</span>
            <span>{bufferStats.utilization_percent.toFixed(1)}%</span>
          </div>
          <div className="utilization-bar">
            <div
              className="utilization-fill"
              style={{
                width: `${bufferStats.utilization_percent}%`,
                backgroundColor:
                  bufferStats.utilization_percent > 90
                    ? "#ef4444"
                    : bufferStats.utilization_percent > 70
                      ? "#f59e0b"
                      : "#10b981",
              }}
            ></div>
          </div>
          <div className="utilization-labels">
            <span>0</span>
            <span>{bufferStats.capacity.toLocaleString()} experiences</span>
          </div>
        </div>

        {/* Prioritized Replay Status */}
        {bufferStats.prioritized_replay_enabled &&
          bufferStats.priority_stats && (
            <div className="priority-stats">
              <h4 className="priority-title">🎯 Prioritized Replay Enabled</h4>
              <div className="priority-grid">
                <div className="priority-item">
                  <span className="priority-label">Min Priority:</span>
                  <span className="priority-value">
                    {bufferStats.priority_stats.min_priority.toFixed(4)}
                  </span>
                </div>
                <div className="priority-item">
                  <span className="priority-label">Max Priority:</span>
                  <span className="priority-value">
                    {bufferStats.priority_stats.max_priority.toFixed(4)}
                  </span>
                </div>
                <div className="priority-item">
                  <span className="priority-label">Mean Priority:</span>
                  <span className="priority-value">
                    {bufferStats.priority_stats.mean_priority.toFixed(4)}
                  </span>
                </div>
                <div className="priority-item">
                  <span className="priority-label">Std Dev:</span>
                  <span className="priority-value">
                    {bufferStats.priority_stats.std_priority.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>
          )}
      </div>

      {/* Consolidation Statistics */}
      <div className="consolidation-section">
        <h3 className="section-title">🔄 Consolidation Statistics</h3>
        <div className="consolidation-grid">
          <div className="consolidation-card">
            <div className="card-header">
              <span className="card-icon">📊</span>
              <span className="card-title">Total Consolidations</span>
            </div>
            <div className="card-value">
              {consolidationStats.total_consolidations.toLocaleString()}
            </div>
            <div className="card-breakdown">
              <div className="breakdown-item">
                <span className="breakdown-label">😴 Sleep:</span>
                <span className="breakdown-value">
                  {consolidationStats.sleep_consolidations}
                </span>
              </div>
              <div className="breakdown-item">
                <span className="breakdown-label">👁️ Wake:</span>
                <span className="breakdown-value">
                  {consolidationStats.wake_consolidations}
                </span>
              </div>
            </div>
          </div>

          <div className="consolidation-card">
            <div className="card-header">
              <span className="card-icon">💡</span>
              <span className="card-title">Experiences Consolidated</span>
            </div>
            <div className="card-value">
              {consolidationStats.total_experiences_consolidated.toLocaleString()}
            </div>
            <div className="card-detail">
              Avg batch size: {consolidationStats.average_batch_size.toFixed(1)}
            </div>
          </div>

          <div className="consolidation-card">
            <div className="card-header">
              <span className="card-icon">⏱️</span>
              <span className="card-title">System Uptime</span>
            </div>
            <div className="card-value">
              {consolidationStats.uptime_hours.toFixed(1)}h
            </div>
            <div className="card-detail">Current mode: {currentMode}</div>
          </div>
        </div>
      </div>

      {/* Mode Comparison */}
      <div className="mode-comparison">
        <h3 className="section-title">🔀 Sleep vs Wake Comparison</h3>
        <div className="comparison-chart">
          <div className="comparison-row">
            <div className="comparison-label">Sleep Consolidations</div>
            <div className="comparison-bar-container">
              <div
                className="comparison-bar sleep-bar"
                style={{
                  width: `${(consolidationStats.sleep_consolidations / Math.max(consolidationStats.total_consolidations, 1)) * 100}%`,
                }}
              >
                <span className="bar-value">
                  {consolidationStats.sleep_consolidations}
                </span>
              </div>
            </div>
          </div>
          <div className="comparison-row">
            <div className="comparison-label">Wake Consolidations</div>
            <div className="comparison-bar-container">
              <div
                className="comparison-bar wake-bar"
                style={{
                  width: `${(consolidationStats.wake_consolidations / Math.max(consolidationStats.total_consolidations, 1)) * 100}%`,
                }}
              >
                <span className="bar-value">
                  {consolidationStats.wake_consolidations}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Biological Inspiration */}
      <div className="bio-inspiration">
        <h3 className="bio-title">🧠 Biological Inspiration</h3>
        <div className="bio-content">
          <p>
            <strong>Hippocampal Replay:</strong> During sleep, the hippocampus
            replays experiences in compressed time, transferring memories to the
            cortex for long-term storage. This prevents catastrophic forgetting
            and strengthens important experiences through prioritized replay.
          </p>
          <p>
            <strong>Sleep Modes:</strong> Deep sleep (slow-wave sleep) is when
            most memory consolidation occurs, while wake consolidation handles
            recent experiences in real-time.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MemoryConsolidationWidget;

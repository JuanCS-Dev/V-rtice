/**
 * ═══════════════════════════════════════════════════════════════════════════
 * IMMUNE ENHANCEMENT WIDGET - FASE 9 Immune Enhancement
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza sistema de immune enhancement:
 * - False Positive Suppression (Regulatory T-Cells)
 * - Tolerance Learning
 * - Memory Consolidation (STM → LTM)
 * - Antibody Repertoire
 */

import logger from "@/utils/logger";
import React, { useState } from "react";
import {
  suppressFalsePositives,
  consolidateMemory,
  queryLongTermMemory,
} from "../../../api/maximusAI";
import "./ImmuneEnhancementWidget.css";

export const ImmuneEnhancementWidget = () => {
  const [activeTab, setActiveTab] = useState("fp-suppression");
  const [loading, setLoading] = useState(false);
  const [fpResults, setFpResults] = useState(null);
  const [consolidationResults, setConsolidationResults] = useState(null);
  const [ltmResults, setLtmResults] = useState(null);
  const [ltmQuery, setLtmQuery] = useState("ransomware campaigns");
  const [alertsInput, setAlertsInput] = useState("");
  const [inputError, setInputError] = useState(null);

  const runFPSuppression = async () => {
    setLoading(true);
    setInputError(null);
    try {
      // Parse alerts from user input (JSON format expected)
      if (!alertsInput.trim()) {
        throw new Error("Please provide alerts in JSON format");
      }

      const alerts = JSON.parse(alertsInput);

      if (!Array.isArray(alerts) || alerts.length === 0) {
        throw new Error("Alerts must be a non-empty array");
      }

      const result = await suppressFalsePositives(alerts, 0.7);
      setFpResults(result);
    } catch (error) {
      setInputError(error.message);
      logger.error("FP suppression failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const runConsolidation = async () => {
    setLoading(true);
    try {
      const result = await consolidateMemory({
        manual: true,
        threshold: 0.7,
      });
      setConsolidationResults(result);
    } catch (error) {
      logger.error("Memory consolidation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const runLTMQuery = async () => {
    setLoading(true);
    try {
      const result = await queryLongTermMemory(ltmQuery, {
        limit: 5,
        minImportance: 0.7,
      });
      setLtmResults(result);
    } catch (error) {
      logger.error("LTM query failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="immune-enhancement-widget">
      <div className="widget-header">
        <h3>🛡️ Immune Enhancement</h3>
        <span className="badge fase9">FASE 9</span>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === "fp-suppression" ? "active" : ""}`}
          onClick={() => setActiveTab("fp-suppression")}
        >
          FP Suppression
        </button>
        <button
          className={`tab ${activeTab === "consolidation" ? "active" : ""}`}
          onClick={() => setActiveTab("consolidation")}
        >
          Memory STM → LTM
        </button>
        <button
          className={`tab ${activeTab === "ltm-query" ? "active" : ""}`}
          onClick={() => setActiveTab("ltm-query")}
        >
          LTM Query
        </button>
      </div>

      {activeTab === "fp-suppression" && (
        <div className="tab-content">
          <p className="description">
            Regulatory T-Cells suppress false positive alerts through tolerance
            learning
          </p>

          <div className="input-section">
            <label
              htmlFor="alerts-input"
              style={{
                display: "block",
                marginBottom: "8px",
                fontWeight: "bold",
              }}
            >
              Alerts (JSON Array):
            </label>
            {/* Boris Cherny Standard - GAP #76 FIX: Add maxLength validation */}
            <textarea
              id="alerts-input"
              value={alertsInput}
              onChange={(e) => setAlertsInput(e.target.value)}
              placeholder='[{"id": "alert_001", "severity": "high", "entity": "192.168.1.10", "type": "port_scan"}]'
              rows={6}
              maxLength={5000}
              style={{
                width: "100%",
                padding: "10px",
                fontFamily: "monospace",
                fontSize: "12px",
                borderRadius: "4px",
                border: "1px solid var(--border-color, #333)",
                backgroundColor: "var(--bg-dark, #1a1a1a)",
                color: "var(--text-color, #fff)",
                marginBottom: "12px",
              }}
            />
            {inputError && (
              <div
                className="text-critical"
                style={{ marginBottom: "12px", fontSize: "14px" }}
              >
                ⚠️ {inputError}
              </div>
            )}
          </div>

          <button
            className="action-btn"
            onClick={runFPSuppression}
            disabled={loading || !alertsInput.trim()}
          >
            {loading ? "⏳ Evaluating..." : "🔬 Suppress False Positives"}
          </button>

          {fpResults && (
            <div className="results">
              <div className="stat-card">
                <span className="stat-label">Alerts Evaluated</span>
                <span className="stat-value">
                  {fpResults.total_alerts || 0}
                </span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Suppressed</span>
                <span className="stat-value suppressed">
                  {fpResults.suppressed_count || 0}
                </span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Avg Tolerance Score</span>
                <span className="stat-value">
                  {((fpResults.avg_tolerance_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "consolidation" && (
        <div className="tab-content">
          <p className="description">
            Trigger memory consolidation cycle (STM → LTM) with pattern
            extraction
          </p>
          <button
            className="action-btn"
            onClick={runConsolidation}
            disabled={loading}
          >
            {loading ? "⏳ Consolidating..." : "💾 Run Consolidation"}
          </button>

          {consolidationResults && (
            <div className="results">
              <div className="stat-card">
                <span className="stat-label">Patterns Extracted</span>
                <span className="stat-value">
                  {consolidationResults.patterns_count || 0}
                </span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Memories Created</span>
                <span className="stat-value">
                  {consolidationResults.ltm_entries_created || 0}
                </span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Consolidation Time</span>
                <span className="stat-value">
                  {consolidationResults.duration_ms || 0}ms
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "ltm-query" && (
        <div className="tab-content">
          <p className="description">
            Query long-term immunological memory for patterns and attack chains
          </p>
          <div className="query-input">
            <input
              type="text"
              value={ltmQuery}
              onChange={(e) => setLtmQuery(e.target.value)}
              placeholder="Enter search query..."
            />
            <button
              className="action-btn"
              onClick={runLTMQuery}
              disabled={loading || !ltmQuery}
            >
              {loading ? "⏳ Searching..." : "🔍 Search LTM"}
            </button>
          </div>

          {ltmResults && (
            <div className="ltm-memories">
              {ltmResults.memories?.length > 0 ? (
                ltmResults.memories.map((memory, idx) => (
                  <div key={idx} className="memory-item">
                    <div className="memory-header">
                      <span className="memory-type">
                        {memory.pattern_type || "Unknown"}
                      </span>
                      <span className="importance">
                        {((memory.importance || 0) * 100).toFixed(0)}%
                        importance
                      </span>
                    </div>
                    <p className="memory-content">
                      {memory.description || "No description"}
                    </p>
                  </div>
                ))
              ) : (
                <p className="no-memories">No memories found</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

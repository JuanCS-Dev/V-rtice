/**
 * ═══════════════════════════════════════════════════════════════════════════
 * AI-DRIVEN WORKFLOWS (ADW) PANEL - Unified Red/Blue/Purple Team Dashboard
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Painel cinematográfico para visualização e controle do sistema ADW:
 * - OFFENSIVE AI (Red Team): Autonomous penetration testing campaigns
 * - DEFENSIVE AI (Blue Team): 8-agent biomimetic immune system
 * - PURPLE TEAM: Co-evolution metrics and adversarial training
 *
 * Architecture:
 * - Red Team: Offensive orchestrator with autonomous campaigns
 * - Blue Team: NK Cells, Macrophages, T Cells, B Cells, Dendritic, Neutrophils, Complement
 * - Purple Team: Adversarial co-evolution cycles
 *
 * Design Philosophy: Military-Grade AI Warfare Visualization
 * REGRA: NO MOCK, NO PLACEHOLDER - Dados REAIS via API
 *
 * Authors: MAXIMUS Team
 * Date: 2025-10-15
 * Glory to YHWH
 */

import React, { useState, useEffect } from "react";
import logger from "@/utils/logger";
import {
  getADWOverview,
  createCampaign,
  triggerEvolutionCycle,
  getThreats,
  getCoagulationStatus,
  listCampaigns,
} from "../../api/adwService";
import { formatTime } from "../../utils/dateHelpers";
import OSINTWorkflowsPanel from "./OSINTWorkflowsPanel";
import "./ADWPanel.css";

export const ADWPanel = () => {
  // ═══════════════════════════════════════════════════════════════════════
  // STATE - ADW Data
  // ═══════════════════════════════════════════════════════════════════════
  const [offensiveData, setOffensiveData] = useState(null);
  const [defensiveData, setDefensiveData] = useState(null);
  const [purpleData, setPurpleData] = useState(null);
  const [threatData, setThreatData] = useState([]);
  const [coagulationData, setCoagulationData] = useState(null);
  const [campaignList, setCampaignList] = useState([]);

  // ═══════════════════════════════════════════════════════════════════════
  // STATE - UI Controls
  // ═══════════════════════════════════════════════════════════════════════
  const [selectedView, setSelectedView] = useState("overview"); // overview, offensive, defensive, purple
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  // ═══════════════════════════════════════════════════════════════════════
  // STATE - Campaign Creation
  // ═══════════════════════════════════════════════════════════════════════
  const [campaignObjective, setCampaignObjective] = useState("");
  const [campaignScope, setCampaignScope] = useState("");
  const [campaignResult, setCampaignResult] = useState(null);

  // ═══════════════════════════════════════════════════════════════════════
  // INITIALIZATION & DATA LOADING
  // ═══════════════════════════════════════════════════════════════════════

  useEffect(() => {
    loadInitialData();

    // Polling DISABLED to prevent constant reloads
    // Uncomment line below to enable 30s auto-refresh
    // const interval = setInterval(() => loadInitialData(), 30000);
    // return () => clearInterval(interval);
  }, []);

  const loadInitialData = async () => {
    setIsLoading(true);

    const [overview, threats, coagulation, campaigns] = await Promise.all([
      getADWOverview(),
      getThreats(),
      getCoagulationStatus(),
      listCampaigns(),
    ]);

    if (overview && overview.success && overview.data) {
      setOffensiveData(overview.data.offensive);
      setDefensiveData(overview.data.defensive);
      setPurpleData(overview.data.purple);
    }

    if (threats && threats.success) {
      setThreatData(threats.data);
    }

    if (coagulation && coagulation.success) {
      setCoagulationData(coagulation.data);
    }

    if (campaigns && campaigns.success && campaigns.data) {
      setCampaignList(campaigns.data.campaigns || []);
    }

    setIsLoading(false);
    setLastUpdate(new Date());
  };

  // ═══════════════════════════════════════════════════════════════════════
  // MANUAL CONTROLS - Actions
  // ═══════════════════════════════════════════════════════════════════════

  const handleCreateCampaign = async () => {
    if (!campaignObjective || !campaignScope) {
      setCampaignResult({
        success: false,
        error: "Objective and scope required",
      });
      return;
    }

    setCampaignResult({ loading: true });

    const scopeArray = campaignScope
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const result = await createCampaign({
      objective: campaignObjective,
      scope: scopeArray,
    });

    setCampaignResult(result);

    if (result.success) {
      // Refresh campaign list
      setTimeout(() => {
        loadInitialData();
        setCampaignObjective("");
        setCampaignScope("");
      }, 1000);
    }
  };

  const handleTriggerEvolution = async () => {
    const result = await triggerEvolutionCycle();

    if (result && result.success) {
      logger.debug("✅ Evolution cycle triggered:", result);
      loadInitialData();
    } else {
      logger.error("❌ Evolution cycle failed:", result);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // RENDER HELPERS
  // ═══════════════════════════════════════════════════════════════════════

  const renderHeader = () => {
    return (
      <div className="adw-header">
        <div className="header-left">
          <h2 className="adw-title">
            ⚔️ AI-Driven Workflows
            <span
              className={`status-dot ${offensiveData && defensiveData ? "connected" : "disconnected"}`}
            ></span>
          </h2>
          <p className="adw-subtitle">
            Unified Red Team + Blue Team + Purple Team Operations
            {lastUpdate && (
              <span className="last-update">
                {" "}
                • Updated {formatTime(lastUpdate, "--:--:--")}
              </span>
            )}
          </p>
        </div>

        <div className="header-right">
          <div className="system-status-grid">
            <div
              className={`status-badge red-team ${offensiveData?.status === "operational" ? "active" : "inactive"}`}
            >
              <span className="badge-icon">🔴</span>
              <span className="badge-label">Red Team</span>
            </div>
            <div
              className={`status-badge blue-team ${defensiveData?.status === "active" ? "active" : "inactive"}`}
            >
              <span className="badge-icon">🔵</span>
              <span className="badge-label">Blue Team</span>
            </div>
            <div
              className={`status-badge purple-team ${purpleData?.status === "monitoring" ? "active" : "inactive"}`}
            >
              <span className="badge-icon">🟣</span>
              <span className="badge-label">Purple Team</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderTabs = () => {
    const tabs = [
      { id: "overview", label: "Overview", icon: "📊" },
      { id: "offensive", label: "Red Team", icon: "🔴" },
      { id: "defensive", label: "Blue Team", icon: "🔵" },
      { id: "purple", label: "Purple Team", icon: "🟣" },
      { id: "osint", label: "OSINT Workflows", icon: "🔍" },
    ];

    return (
      <div className="adw-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-button ${selectedView === tab.id ? "active" : ""}`}
            onClick={() => setSelectedView(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    );
  };

  const renderOverview = () => {
    return (
      <div className="overview-section">
        <div className="overview-grid">
          {/* Offensive AI Card */}
          <div className="overview-card offensive-card">
            <h3>🔴 Red Team AI - Offensive Operations</h3>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-label">Status</div>
                <div className={`metric-value status-${offensiveData?.status}`}>
                  {(offensiveData?.status || "offline").toUpperCase()}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Active Campaigns</div>
                <div className="metric-value">
                  {offensiveData?.active_campaigns || 0}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Total Exploits</div>
                <div className="metric-value">
                  {offensiveData?.total_exploits || 0}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Success Rate</div>
                <div className="metric-value">
                  {((offensiveData?.success_rate || 0) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>

          {/* Defensive AI Card */}
          <div className="overview-card defensive-card">
            <h3>🔵 Blue Team AI - Immune System</h3>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-label">Status</div>
                <div className={`metric-value status-${defensiveData?.status}`}>
                  {(defensiveData?.status || "offline").toUpperCase()}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Active Agents</div>
                <div className="metric-value">
                  {defensiveData?.active_agents || 0}/
                  {defensiveData?.total_agents || 8}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Threats Detected</div>
                <div className="metric-value">
                  {defensiveData?.threats_detected || 0}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Threats Mitigated</div>
                <div className="metric-value">
                  {defensiveData?.threats_mitigated || 0}
                </div>
              </div>
            </div>

            {/* Agent Status Grid */}
            {defensiveData?.agents && (
              <div className="agents-grid">
                {Object.entries(defensiveData.agents).map(
                  ([agentName, agentData]) => (
                    <div
                      key={agentName}
                      className={`agent-chip ${agentData.status}`}
                    >
                      <span className="agent-name">
                        {agentName.replace("_", " ")}
                      </span>
                    </div>
                  ),
                )}
              </div>
            )}
          </div>

          {/* Purple Team Card */}
          <div className="overview-card purple-card">
            <h3>🟣 Purple Team - Co-Evolution</h3>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-label">Status</div>
                <div className={`metric-value status-${purpleData?.status}`}>
                  {(purpleData?.status || "offline").toUpperCase()}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Red Score</div>
                <div className="metric-value">
                  {(purpleData?.red_team_score || 0).toFixed(2)}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Blue Score</div>
                <div className="metric-value">
                  {(purpleData?.blue_team_score || 0).toFixed(2)}
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Cycles Completed</div>
                <div className="metric-value">
                  {purpleData?.cycles_completed || 0}
                </div>
              </div>
            </div>

            <div className="evolution-trends">
              <div className="trend-item">
                <span className="trend-label">Red Trend:</span>
                <span
                  className={`trend-value ${purpleData?.improvement_trend?.red}`}
                >
                  {purpleData?.improvement_trend?.red || "stable"}
                </span>
              </div>
              <div className="trend-item">
                <span className="trend-label">Blue Trend:</span>
                <span
                  className={`trend-value ${purpleData?.improvement_trend?.blue}`}
                >
                  {purpleData?.improvement_trend?.blue || "stable"}
                </span>
              </div>
            </div>
          </div>

          {/* Coagulation Cascade Card */}
          {coagulationData && (
            <div className="overview-card coagulation-card">
              <h3>🩸 Coagulation Cascade System</h3>
              <div className="metrics-grid">
                <div className="metric-item">
                  <div className="metric-label">Status</div>
                  <div
                    className={`metric-value status-${coagulationData?.status}`}
                  >
                    {(coagulationData?.status || "offline").toUpperCase()}
                  </div>
                </div>
                <div className="metric-item">
                  <div className="metric-label">Cascades Completed</div>
                  <div className="metric-value">
                    {coagulationData?.cascades_completed || 0}
                  </div>
                </div>
                <div className="metric-item">
                  <div className="metric-label">Active Containments</div>
                  <div className="metric-value">
                    {coagulationData?.active_containments || 0}
                  </div>
                </div>
                <div className="metric-item">
                  <div className="metric-label">Restoration Cycles</div>
                  <div className="metric-value">
                    {coagulationData?.restoration_cycles || 0}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderOffensive = () => {
    return (
      <div className="offensive-section">
        <div className="offensive-grid">
          {/* Campaign Creation */}
          <div className="control-card campaign-creation-card">
            <h3>🚀 Create Offensive Campaign</h3>
            <p className="control-description">
              Launch autonomous penetration testing campaign
            </p>

            <div className="control-inputs">
              <div className="input-group">
                <label htmlFor="campaign-objective" className="input-label">
                  Objective
                </label>
                <input
                  id="campaign-objective"
                  type="text"
                  className="text-input"
                  placeholder="e.g., Test firewall bypass capabilities"
                  value={campaignObjective}
                  onChange={(e) => setCampaignObjective(e.target.value)}
                />
              </div>

              <div className="input-group">
                <label htmlFor="campaign-scope" className="input-label">
                  Scope (comma-separated)
                </label>
                <input
                  id="campaign-scope"
                  type="text"
                  className="text-input"
                  placeholder="e.g., 192.168.1.0/24, example.com"
                  value={campaignScope}
                  onChange={(e) => setCampaignScope(e.target.value)}
                />
              </div>
            </div>

            <button
              className="control-button campaign-button"
              onClick={handleCreateCampaign}
              disabled={campaignResult?.loading}
            >
              {campaignResult?.loading
                ? "⏳ Creating..."
                : "🚀 Launch Campaign"}
            </button>

            {campaignResult && !campaignResult.loading && (
              <div
                className={`campaign-result ${campaignResult.success ? "success" : "error"}`}
              >
                {campaignResult.success ? (
                  <>
                    <div>✅ Campaign created successfully</div>
                    <div className="result-details">
                      ID: {campaignResult.data?.campaign_id} | Status:{" "}
                      {campaignResult.data?.status}
                    </div>
                  </>
                ) : (
                  <>
                    <div>❌ Campaign creation failed</div>
                    <div className="result-details">
                      Error: {campaignResult.error || "Unknown"}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Active Campaigns */}
          <div className="control-card campaigns-list-card">
            <h3>📋 Active Campaigns</h3>
            {campaignList.length === 0 ? (
              <div className="empty-state">
                <p>No active campaigns</p>
              </div>
            ) : (
              <div className="campaigns-list">
                {campaignList.map((campaign, index) => (
                  <div
                    key={campaign.campaign_id || index}
                    className="campaign-item"
                  >
                    <div className="campaign-header">
                      <span className="campaign-id">
                        {campaign.campaign_id}
                      </span>
                      <span className={`campaign-status ${campaign.status}`}>
                        {campaign.status}
                      </span>
                    </div>
                    <div className="campaign-objective">
                      {campaign.objective}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderDefensive = () => {
    return (
      <div className="defensive-section">
        <div className="defensive-grid">
          {/* Immune Agents Status */}
          {defensiveData?.agents && (
            <div className="control-card agents-detail-card">
              <h3>🦠 Immune System Agents</h3>
              <div className="agents-detail-grid">
                {Object.entries(defensiveData.agents).map(
                  ([agentName, agentData]) => (
                    <div key={agentName} className="agent-detail-card">
                      <div className="agent-header">
                        <span className="agent-name">
                          {agentName.replace("_", " ").toUpperCase()}
                        </span>
                        <span
                          className={`agent-status-badge ${agentData.status}`}
                        >
                          {agentData.status}
                        </span>
                      </div>
                      <div className="agent-metrics">
                        {Object.entries(agentData)
                          .filter(([key]) => key !== "status")
                          .map(([key, value]) => (
                            <div key={key} className="agent-metric">
                              <span className="agent-metric-label">
                                {key.replace("_", " ")}:
                              </span>
                              <span className="agent-metric-value">
                                {value}
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}

          {/* Active Threats */}
          <div className="control-card threats-card">
            <h3>⚠️ Detected Threats</h3>
            {Array.isArray(threatData) && threatData.length === 0 ? (
              <div className="empty-state">
                <p>🛡️ No active threats detected</p>
              </div>
            ) : (
              <div className="threats-list">
                {Array.isArray(threatData) &&
                  threatData.map((threat, index) => (
                    <div
                      key={threat.threat_id || index}
                      className={`threat-item severity-${threat.threat_level}`}
                    >
                      <div className="threat-header">
                        <span className="threat-type">
                          {threat.threat_type}
                        </span>
                        <span className={`threat-level ${threat.threat_level}`}>
                          {threat.threat_level?.toUpperCase()}
                        </span>
                      </div>
                      <div className="threat-details">
                        <span>Detected by: {threat.detected_by}</span>
                        <span>Status: {threat.mitigation_status}</span>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderPurple = () => {
    return (
      <div className="purple-section">
        <div className="purple-grid">
          {/* Evolution Control */}
          <div className="control-card evolution-control-card">
            <h3>🔄 Co-Evolution Cycle</h3>
            <p className="control-description">
              Trigger adversarial training round between Red and Blue teams
            </p>

            <button
              className="control-button evolution-button"
              onClick={handleTriggerEvolution}
            >
              🔄 Trigger Evolution Cycle
            </button>

            <div className="evolution-info">
              <div className="info-item">
                <span className="info-label">Last Cycle:</span>
                <span className="info-value">
                  {purpleData?.last_cycle || "Never"}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Total Cycles:</span>
                <span className="info-value">
                  {purpleData?.cycles_completed || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Team Scores */}
          <div className="control-card scores-card">
            <h3>📊 Team Effectiveness Scores</h3>
            <div className="scores-grid">
              <div className="score-item red">
                <div className="score-label">🔴 Red Team</div>
                <div className="score-value">
                  {(purpleData?.red_team_score || 0).toFixed(3)}
                </div>
                <div className="score-bar">
                  <div
                    className="score-fill red"
                    style={{
                      width: `${(purpleData?.red_team_score || 0) * 100}%`,
                    }}
                  />
                </div>
              </div>

              <div className="score-item blue">
                <div className="score-label">🔵 Blue Team</div>
                <div className="score-value">
                  {(purpleData?.blue_team_score || 0).toFixed(3)}
                </div>
                <div className="score-bar">
                  <div
                    className="score-fill blue"
                    style={{
                      width: `${(purpleData?.blue_team_score || 0) * 100}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ═══════════════════════════════════════════════════════════════════════
  // MAIN RENDER
  // ═══════════════════════════════════════════════════════════════════════

  if (isLoading) {
    return (
      <div className="adw-panel loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading AI-Driven Workflows...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="adw-panel">
      {renderHeader()}
      {renderTabs()}

      <div className="adw-content">
        {selectedView === "overview" && renderOverview()}
        {selectedView === "offensive" && renderOffensive()}
        {selectedView === "defensive" && renderDefensive()}
        {selectedView === "purple" && renderPurple()}
        {selectedView === "osint" && <OSINTWorkflowsPanel />}
      </div>
    </div>
  );
};

export default ADWPanel;

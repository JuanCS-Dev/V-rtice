import { API_ENDPOINTS } from "@/config/api";
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * STRATEGIC PLANNING WIDGET - Digital Prefrontal Cortex
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza o módulo de planejamento estratégico:
 * - POLÍTICAS DE SEGURANÇA: Adaptive policy management
 * - ALOCAÇÃO DE RECURSOS: Budget, compute, personnel
 * - AVALIAÇÃO DE RISCOS: Threat modeling
 * - APROVAÇÕES: High-impact action workflows
 * - PLANOS ESTRATÉGICOS: Long-term planning
 */

import logger from "@/utils/logger";
import React, { useState, useEffect } from "react";
import { formatDate, formatDateTime } from "@/utils/dateHelpers";
import "./StrategicPlanningWidget.css";

export const StrategicPlanningWidget = ({ systemHealth: _systemHealth }) => {
  const [activePolicies, setActivePolicies] = useState([]);
  const [resources, setResources] = useState([]);
  const [risks, setRisks] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [strategicPlans, setStrategicPlans] = useState([]);
  const [selectedView, setSelectedView] = useState("overview"); // 'overview', 'policies', 'resources', 'risks', 'approvals', 'plans'
  const [loading, setLoading] = useState(true);

  // Fetch policies
  useEffect(() => {
    const fetchPolicies = async () => {
      try {
        const response = await fetch(
          `${API_ENDPOINTS.policies}?active_only=true`,
        );
        if (response.ok) {
          const data = await response.json();
          setActivePolicies(data.policies || []);
        }
      } catch (error) {
        logger.error("Failed to fetch policies:", error);
      }
    };

    fetchPolicies();
    const interval = setInterval(fetchPolicies, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch resources
  useEffect(() => {
    const fetchResources = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.resources);
        if (response.ok) {
          const data = await response.json();
          setResources(data.allocations || []);
        }
      } catch (error) {
        logger.error("Failed to fetch resources:", error);
      }
    };

    fetchResources();
    const interval = setInterval(fetchResources, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch risks
  useEffect(() => {
    const fetchRisks = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.risks);
        if (response.ok) {
          const data = await response.json();
          setRisks(data.risks || []);
          setLoading(false);
        }
      } catch (error) {
        logger.error("Failed to fetch risks:", error);
      }
    };

    fetchRisks();
    const interval = setInterval(fetchRisks, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch approvals
  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        const response = await fetch(
          `${API_ENDPOINTS.approvals}?status_filter=pending`,
        );
        if (response.ok) {
          const data = await response.json();
          setPendingApprovals(data.approvals || []);
        }
      } catch (error) {
        logger.error("Failed to fetch approvals:", error);
      }
    };

    fetchApprovals();
    const interval = setInterval(fetchApprovals, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch plans
  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.plans);
        if (response.ok) {
          const data = await response.json();
          setStrategicPlans(data.plans || []);
        }
      } catch (error) {
        logger.error("Failed to fetch plans:", error);
      }
    };

    fetchPlans();
    const interval = setInterval(fetchPlans, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="planning-loading">
        <div className="loading-spinner"></div>
        <p>Loading strategic planning data...</p>
      </div>
    );
  }

  const getRiskLevelClass = (level) => {
    const classes = {
      critical: "border-critical",
      high: "border-high",
      medium: "border-info",
      low: "border-success",
      minimal: "border-low",
    };
    return classes[level.toLowerCase()] || "border-low";
  };

  const getRiskLevelBgClass = (level) => {
    const classes = {
      critical: "bg-critical",
      high: "bg-high",
      medium: "bg-info",
      low: "bg-success",
      minimal: "bg-low",
    };
    return classes[level.toLowerCase()] || "bg-low";
  };

  const renderOverview = () => {
    const criticalRisks = risks.filter(
      (r) => r.risk_level === "critical",
    ).length;
    const highRisks = risks.filter((r) => r.risk_level === "high").length;

    return (
      <div className="planning-overview">
        {/* Summary Cards */}
        <div className="overview-grid">
          <div className="overview-card policies-card">
            <div className="card-icon">📋</div>
            <div className="card-content">
              <div className="card-value">{activePolicies.length}</div>
              <div className="card-label">Active Policies</div>
            </div>
            <button
              onClick={() => setSelectedView("policies")}
              className="card-action"
            >
              View →
            </button>
          </div>

          <div className="overview-card resources-card">
            <div className="card-icon">💰</div>
            <div className="card-content">
              <div className="card-value">{resources.length}</div>
              <div className="card-label">Resource Allocations</div>
            </div>
            <button
              onClick={() => setSelectedView("resources")}
              className="card-action"
            >
              View →
            </button>
          </div>

          <div className="overview-card risks-card">
            <div className="card-icon">⚠️</div>
            <div className="card-content">
              <div className="card-value">{criticalRisks + highRisks}</div>
              <div className="card-label">Critical/High Risks</div>
            </div>
            <button
              onClick={() => setSelectedView("risks")}
              className="card-action"
            >
              View →
            </button>
          </div>

          <div className="overview-card approvals-card">
            <div className="card-icon">✅</div>
            <div className="card-content">
              <div className="card-value">{pendingApprovals.length}</div>
              <div className="card-label">Pending Approvals</div>
            </div>
            <button
              onClick={() => setSelectedView("approvals")}
              className="card-action"
            >
              View →
            </button>
          </div>

          <div className="overview-card plans-card">
            <div className="card-icon">🗺️</div>
            <div className="card-content">
              <div className="card-value">{strategicPlans.length}</div>
              <div className="card-label">Strategic Plans</div>
            </div>
            <button
              onClick={() => setSelectedView("plans")}
              className="card-action"
            >
              View →
            </button>
          </div>
        </div>

        {/* Recent Risks */}
        <div className="recent-risks">
          <h3 className="section-title">⚠️ Top Risks</h3>
          <div className="risks-list">
            {risks.slice(0, 5).map((risk) => (
              <div
                key={risk.risk_id}
                className={`risk-item ${getRiskLevelClass(risk.risk_level)}`}
              >
                <div className="risk-header">
                  <span className="risk-type">{risk.threat_type}</span>
                  <span
                    className={`risk-level-badge ${getRiskLevelBgClass(risk.risk_level)}`}
                  >
                    {risk.risk_level.toUpperCase()}
                  </span>
                </div>
                <div className="risk-score">
                  Risk Score: {risk.risk_score.toFixed(2)}
                </div>
                <div className="risk-metrics">
                  <span>
                    Probability: {(risk.probability * 100).toFixed(0)}%
                  </span>
                  <span>Impact: {risk.impact.toFixed(1)}/10</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderPolicies = () => (
    <div className="policies-view">
      <h3 className="section-title">
        📋 Active Security Policies ({activePolicies.length})
      </h3>
      <div className="policies-list">
        {activePolicies.map((policy) => (
          <div key={policy.policy_id} className="policy-card">
            <div className="policy-header">
              <h4 className="policy-name">{policy.name}</h4>
              <span className="policy-enforcement">
                {policy.enforcement_level}
              </span>
            </div>
            <p className="policy-description">{policy.description}</p>
            <div className="policy-footer">
              <span className="policy-version">v{policy.version}</span>
              <span className="policy-priority">
                Priority: {policy.priority}/10
              </span>
              <span className="policy-updated">
                Updated:{" "}
                {formatDate(policy.updated_at, { dateStyle: "short" }, "N/A")}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderResources = () => (
    <div className="resources-view">
      <h3 className="section-title">
        💰 Resource Allocations ({resources.length})
      </h3>
      <div className="resources-list">
        {resources.map((resource) => (
          <div key={resource.allocation_id} className="resource-card">
            <div className="resource-header">
              <span className="resource-type-badge">
                {resource.resource_type}
              </span>
              <span className="resource-priority">
                Priority {resource.priority}
              </span>
            </div>
            <div className="resource-body">
              <div className="resource-allocation">
                <strong>
                  {resource.amount} {resource.unit}
                </strong>{" "}
                → {resource.allocated_to}
              </div>
              <div className="resource-utilization">
                Utilization: {(resource.utilization * 100).toFixed(1)}%
              </div>
              <div className="resource-dates">
                {formatDate(resource.start_date, { dateStyle: "short" }, "N/A")}{" "}
                -
                {resource.end_date
                  ? formatDate(resource.end_date, { dateStyle: "short" }, "N/A")
                  : "Ongoing"}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderRisks = () => (
    <div className="risks-view">
      <h3 className="section-title">⚠️ Risk Assessments ({risks.length})</h3>
      <div className="risks-grid">
        {risks.map((risk) => (
          <div
            key={risk.risk_id}
            className={`risk-card ${getRiskLevelClass(risk.risk_level)}`}
          >
            <div className="risk-card-header">
              <h4 className="risk-threat-type">{risk.threat_type}</h4>
              <span
                className={`risk-level-badge ${getRiskLevelBgClass(risk.risk_level)}`}
              >
                {risk.risk_level.toUpperCase()}
              </span>
            </div>
            <div className="risk-card-body">
              <div className="risk-metrics-grid">
                <div className="risk-metric">
                  <span className="metric-label">Risk Score:</span>
                  <span className="metric-value">
                    {risk.risk_score.toFixed(2)}
                  </span>
                </div>
                <div className="risk-metric">
                  <span className="metric-label">Probability:</span>
                  <span className="metric-value">
                    {(risk.probability * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="risk-metric">
                  <span className="metric-label">Impact:</span>
                  <span className="metric-value">
                    {risk.impact.toFixed(1)}/10
                  </span>
                </div>
              </div>
              {risk.mitigation_plan && risk.mitigation_plan.length > 0 && (
                <div className="risk-mitigation">
                  <strong>Mitigation:</strong>
                  <ul>
                    {risk.mitigation_plan.slice(0, 3).map((plan, idx) => (
                      <li key={idx}>{plan}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderApprovals = () => (
    <div className="approvals-view">
      <h3 className="section-title">
        ✅ Pending Approvals ({pendingApprovals.length})
      </h3>
      {pendingApprovals.length > 0 ? (
        <div className="approvals-list">
          {pendingApprovals.map((approval) => (
            <div key={approval.action_id} className="approval-card">
              <div className="approval-header">
                <span className="approval-type">{approval.action_type}</span>
                <span className="approval-status">{approval.status}</span>
              </div>
              <div className="approval-body">
                <p className="approval-description">{approval.description}</p>
                <div className="approval-details">
                  <span>Requester: {approval.requester}</span>
                  <span>Risk: {approval.risk_level}</span>
                  <span>
                    Level: {approval.current_level + 1}/
                    {approval.approval_levels.length}
                  </span>
                </div>
                <div className="approval-submitted">
                  Submitted:{" "}
                  {new Date(approval.submitted_at).toLocaleString("pt-BR")}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="approvals-empty">
          <p>✅ No pending approvals</p>
        </div>
      )}
    </div>
  );

  const renderPlans = () => (
    <div className="plans-view">
      <h3 className="section-title">
        🗺️ Strategic Plans ({strategicPlans.length})
      </h3>
      <div className="plans-list">
        {strategicPlans.map((plan) => (
          <div key={plan.plan_id} className="plan-card">
            <div className="plan-header">
              <h4 className="plan-name">{plan.name}</h4>
              <span className="plan-status">{plan.status}</span>
            </div>
            <p className="plan-description">{plan.description}</p>
            <div className="plan-details">
              <div className="plan-horizon">
                Horizon: {plan.horizon_days} days
              </div>
              <div className="plan-objectives">
                <strong>Objectives:</strong>
                <ul>
                  {plan.objectives.slice(0, 3).map((obj, idx) => (
                    <li key={idx}>{obj}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderActiveView = () => {
    switch (selectedView) {
      case "policies":
        return renderPolicies();
      case "resources":
        return renderResources();
      case "risks":
        return renderRisks();
      case "approvals":
        return renderApprovals();
      case "plans":
        return renderPlans();
      default:
        return renderOverview();
    }
  };

  return (
    <div className="strategic-planning-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <h2 className="widget-title">📋 Strategic Planning Module</h2>
          <p className="widget-subtitle">
            Córtex Pré-frontal Digital - Executive Function
          </p>
        </div>
      </div>

      {/* View Navigation */}
      <div className="view-navigation">
        {[
          { id: "overview", name: "Overview", icon: "📊" },
          { id: "policies", name: "Policies", icon: "📋" },
          { id: "resources", name: "Resources", icon: "💰" },
          { id: "risks", name: "Risks", icon: "⚠️" },
          { id: "approvals", name: "Approvals", icon: "✅" },
          { id: "plans", name: "Plans", icon: "🗺️" },
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
          <strong>Dorsolateral Prefrontal Cortex (DLPFC):</strong> Executive
          function, strategic planning, working memory, risk assessment,
          inhibitory control, and long-term goal-directed behavior. The DLPFC is
          the "CEO of the brain", coordinating complex decision-making and
          strategic thinking.
        </p>
      </div>
    </div>
  );
};

export default StrategicPlanningWidget;

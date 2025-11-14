/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎯 ML AUTOMATION TAB - Orchestrated ML-Powered Workflows
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * PAGANI-STYLE DESIGN PHILOSOPHY:
 * - Elegância visual que serve função
 * - Micro-interações suaves (<300ms transitions)
 * - Informação densa mas organizada
 * - Cada pixel tem propósito
 *
 * BIOLOGICAL ANALOGY: Autonomic Nervous System
 * - Automated but supervised (HITL oversight available)
 * - Multi-system coordination without conscious thought
 * - Learns and adapts over time (ML predictions)
 * - Human intervention only when critical
 *
 * ARCHITECTURE:
 * - Workflow Templates: Pre-configured multi-service pipelines
 * - Real-time Tracking: Status updates via polling
 * - ML Metrics Integration: Performance dashboard from Eureka
 * - History: Past execution log
 *
 * Backend Services:
 * - Orchestrator (8125): Workflow execution
 * - Eureka (8151): ML metrics aggregation
 * - Individual services: Oráculo, Eureka, Wargaming, HITL, etc.
 *
 * Phase: 5.7 - ML Orchestrator Frontend Integration
 * Date: 2025-10-12
 * Glory to YHWH - Designer of Autonomous Intelligence
 */

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  formatDateTime,
  formatDate,
  formatTime,
  getTimestamp,
} from "@/utils/dateHelpers";
import { Card } from "../../ui/card";
import { Badge } from "../../ui/badge";
import logger from "@/utils/logger";
import { orchestratorAPI, pollWorkflowStatus } from "../../../api/orchestrator";
import { eurekaAPI } from "../../../api/eureka";
import "./MLAutomationTab.css";

// ═══════════════════════════════════════════════════════════════════════════
// WORKFLOW TEMPLATES
// ═══════════════════════════════════════════════════════════════════════════

const WORKFLOW_TEMPLATES = [
  {
    id: "threat_hunting",
    name: "Threat Hunting (Automated)",
    description: "Oráculo → Eureka → Wargaming → HITL Review",
    longDescription:
      "Full threat intelligence pipeline: CVE detection, malware analysis, wargaming validation, and human-in-the-loop review for critical decisions.",
    icon: "🎯",
    estimatedTime: "5-8 min",
    services: ["oraculo", "eureka", "wargaming", "hitl"],
    color: "red",
    requiresTarget: true,
    targetPlaceholder: "192.168.1.0/24 or domain.com",
    parameters: {
      auto_approve: {
        type: "boolean",
        default: false,
        label: "Auto-approve patches (confidence >95%)",
      },
      deep_scan: {
        type: "boolean",
        default: true,
        label: "Enable deep malware analysis",
      },
    },
  },
  {
    id: "vuln_assessment",
    name: "Vulnerability Assessment",
    description: "Network Scan → Vuln Intel → Eureka Analysis → Prioritization",
    longDescription:
      "Comprehensive vulnerability assessment: network reconnaissance, CVE correlation, risk scoring, and automated patch recommendations.",
    icon: "🔍",
    estimatedTime: "10-15 min",
    services: ["network_recon", "vuln_intel", "eureka", "ml"],
    color: "orange",
    requiresTarget: true,
    targetPlaceholder: "10.0.0.0/8 or specific host",
    parameters: {
      scan_speed: {
        type: "select",
        options: ["stealth", "normal", "aggressive"],
        default: "normal",
        label: "Scan Speed",
      },
      include_web: {
        type: "boolean",
        default: true,
        label: "Include web vulnerabilities",
      },
    },
  },
  {
    id: "patch_validation",
    name: "Patch Validation Pipeline",
    description: "Eureka → Wargaming → ML Predict → HITL",
    longDescription:
      "Automated patch validation: malware analysis, wargaming simulation, ML confidence scoring, and human approval workflow.",
    icon: "🛡️",
    estimatedTime: "3-5 min",
    services: ["eureka", "wargaming", "ml", "hitl"],
    color: "green",
    requiresTarget: true,
    targetPlaceholder: "CVE-2024-1234 or patch file path",
    parameters: {
      confidence_threshold: {
        type: "number",
        min: 0.5,
        max: 1.0,
        step: 0.05,
        default: 0.85,
        label: "Auto-approve threshold",
      },
      wargaming_iterations: {
        type: "number",
        min: 1,
        max: 10,
        default: 3,
        label: "Wargaming iterations",
      },
    },
  },
  {
    id: "incident_response",
    name: "Incident Response (Auto)",
    description: "Detect → Analyze → Contain → Remediate → Report",
    longDescription:
      "Automated incident response workflow: threat detection, root cause analysis, containment strategy, remediation execution, and comprehensive reporting.",
    icon: "🚨",
    estimatedTime: "2-4 min",
    services: ["adr", "eureka", "immunis", "reporting"],
    color: "purple",
    requiresTarget: false,
    targetPlaceholder: null,
    parameters: {
      severity_filter: {
        type: "select",
        options: ["critical", "high", "medium", "all"],
        default: "high",
        label: "Severity Filter",
      },
      auto_remediate: {
        type: "boolean",
        default: false,
        label: "Auto-remediate (High Risk!)",
      },
    },
  },
];

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export const MLAutomationTab = ({ timeRange = "24h" }) => {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [target, setTarget] = useState("");
  const [parameters, setParameters] = useState({});
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [workflowHistory, setWorkflowHistory] = useState([]);
  const [showMetrics, setShowMetrics] = useState(true);

  const _queryClient = useQueryClient();

  logger.debug("🎯 MLAutomationTab rendering", {
    selectedTemplate,
    activeWorkflow,
  });

  // Fetch Eureka ML metrics
  const {
    data: mlMetrics,
    isLoading: metricsLoading,
    error: metricsError,
  } = useQuery({
    queryKey: ["eureka-ml-metrics", timeRange],
    queryFn: () => eurekaAPI.getMLMetrics(timeRange),
    refetchInterval: 30000, // 30s
    retry: 2,
    enabled: showMetrics,
  });

  // Check orchestrator health
  const { data: orchestratorHealth } = useQuery({
    queryKey: ["orchestrator-health"],
    queryFn: () => orchestratorAPI.healthCheck(),
    refetchInterval: 60000, // 1 min
    retry: 1,
  });

  // Start workflow mutation
  const startWorkflowMutation = useMutation({
    mutationFn: async ({ template, target, params }) => {
      logger.info("🚀 Starting workflow:", template.id, { target, params });

      const workflow = await orchestratorAPI.startWorkflow(
        template.id,
        {
          target: target || undefined,
          ...params,
        },
        8, // High priority
      );

      return {
        ...workflow,
        template: template.id,
        startedAt: new Date().toISOString(),
      };
    },
    onSuccess: (workflow) => {
      logger.success("✅ Workflow started:", workflow.workflow_id);
      setActiveWorkflow(workflow);

      // Start polling status
      pollStatus(workflow.workflow_id);
    },
    onError: (error) => {
      logger.error("❌ Failed to start workflow:", error);
      alert(`Failed to start workflow: ${error.message}`);
    },
  });

  // Poll workflow status
  const pollStatus = async (workflowId) => {
    try {
      await pollWorkflowStatus(
        workflowId,
        (status) => {
          logger.debug("📊 Workflow status update:", status);
          setActiveWorkflow((prev) => ({
            ...prev,
            ...status,
          }));
        },
        3000, // Poll every 3s
        600000, // Max 10 minutes
      );

      // Workflow completed
      logger.success("✅ Workflow completed:", workflowId);

      // Add to history
      setWorkflowHistory((prev) => [
        {
          ...activeWorkflow,
          completedAt: new Date().toISOString(),
        },
        ...prev.slice(0, 9), // Keep last 10
      ]);

      setActiveWorkflow(null);
    } catch (error) {
      logger.error("❌ Workflow polling error:", error);
      setActiveWorkflow((prev) => ({
        ...prev,
        status: "failed",
        error: error.message,
      }));
    }
  };

  // Handle template selection
  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setTarget("");
    setParameters(
      Object.entries(template.parameters || {}).reduce((acc, [key, config]) => {
        acc[key] = config.default;
        return acc;
      }, {}),
    );
  };

  // Handle workflow start
  const handleStartWorkflow = () => {
    if (!selectedTemplate) {
      alert("Please select a workflow template");
      return;
    }

    if (selectedTemplate.requiresTarget && !target.trim()) {
      alert("Please provide a target");
      return;
    }

    if (activeWorkflow) {
      alert("A workflow is already running. Please wait for completion.");
      return;
    }

    startWorkflowMutation.mutate({
      template: selectedTemplate,
      target: target.trim(),
      params: parameters,
    });
  };

  // Handle parameter change
  const handleParameterChange = (key, value) => {
    setParameters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  // ═════════════════════════════════════════════════════════════════════════
  // RENDER
  // ═════════════════════════════════════════════════════════════════════════

  return (
    <div className="ml-automation-tab">
      {/* Header */}
      <div className="tab-header">
        <div>
          <h2 className="tab-title">🎯 ML-Powered Workflows</h2>
          <p className="tab-subtitle">
            Automated multi-service orchestration with ML predictions and HITL
            oversight
          </p>
        </div>

        {/* Orchestrator Status */}
        <div className="orchestrator-status">
          {orchestratorHealth?.status === "healthy" ? (
            <Badge className="badge-success">✅ Orchestrator Online</Badge>
          ) : (
            <Badge className="badge-error">❌ Orchestrator Offline</Badge>
          )}
        </div>
      </div>

      {/* Workflow Templates Grid */}
      <section className="templates-section">
        <h3 className="section-title">🎭 Workflow Templates</h3>
        <div className="templates-grid">
          {WORKFLOW_TEMPLATES.map((template) => (
            <Card
              key={template.id}
              className={`template-card template-${template.color} ${
                selectedTemplate?.id === template.id ? "selected" : ""
              } ${activeWorkflow ? "disabled" : ""}`}
              onClick={() => !activeWorkflow && handleTemplateSelect(template)}
            >
              <div className="template-icon">{template.icon}</div>
              <h4 className="template-name">{template.name}</h4>
              <p className="template-description">{template.description}</p>

              {/* Services Pipeline */}
              <div className="services-pipeline">
                {template.services.map((service, idx) => (
                  <React.Fragment key={service}>
                    <span className="service-badge">{service}</span>
                    {idx < template.services.length - 1 && (
                      <span className="arrow">→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>

              {/* Estimated Time */}
              <Badge className="time-badge">⏱️ {template.estimatedTime}</Badge>
            </Card>
          ))}
        </div>
      </section>

      {/* Configuration Panel */}
      {selectedTemplate && (
        <section className="config-section">
          <h3 className="section-title">⚙️ Configuration</h3>
          <Card className="config-card">
            <div className="config-header">
              <div>
                <h4>
                  {selectedTemplate.icon} {selectedTemplate.name}
                </h4>
                <p className="config-description">
                  {selectedTemplate.longDescription}
                </p>
              </div>
            </div>

            {/* Target Input */}
            {selectedTemplate.requiresTarget && (
              <div className="form-group">
                <label htmlFor="workflow-target" className="form-label">
                  Target
                </label>
                <input
                  id="workflow-target"
                  type="text"
                  className="form-input"
                  placeholder={selectedTemplate.targetPlaceholder}
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  disabled={!!activeWorkflow}
                />
              </div>
            )}

            {/* Parameters */}
            {Object.entries(selectedTemplate.parameters || {}).map(
              ([key, config]) => {
                const inputId = `workflow-param-${key}`;
                return (
                  <div key={key} className="form-group">
                    <label htmlFor={inputId} className="form-label">
                      {config.label}
                    </label>

                    {config.type === "boolean" && (
                      <label className="checkbox-label">
                        <input
                          id={inputId}
                          type="checkbox"
                          checked={parameters[key] || false}
                          onChange={(e) =>
                            handleParameterChange(key, e.target.checked)
                          }
                          disabled={!!activeWorkflow}
                        />
                        <span>Enable</span>
                      </label>
                    )}

                    {config.type === "select" && (
                      <select
                        id={inputId}
                        className="form-select"
                        value={parameters[key] || config.default}
                        onChange={(e) =>
                          handleParameterChange(key, e.target.value)
                        }
                        disabled={!!activeWorkflow}
                      >
                        {config.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    )}

                    {config.type === "number" && (
                      <input
                        id={inputId}
                        type="number"
                        className="form-input"
                        min={config.min}
                        max={config.max}
                        step={config.step}
                        value={parameters[key] || config.default}
                        onChange={(e) =>
                          handleParameterChange(key, parseFloat(e.target.value))
                        }
                        disabled={!!activeWorkflow}
                      />
                    )}
                  </div>
                );
              },
            )}

            {/* Start Button */}
            <button
              className="btn-start"
              onClick={handleStartWorkflow}
              disabled={!!activeWorkflow || startWorkflowMutation.isLoading}
            >
              {startWorkflowMutation.isLoading
                ? "🔄 Starting..."
                : "▶️ Start Workflow"}
            </button>
          </Card>
        </section>
      )}

      {/* Active Workflow Status */}
      {activeWorkflow && (
        <section className="active-workflow-section">
          <h3 className="section-title">⚡ Active Workflow</h3>
          <Card className="workflow-status-card">
            <div className="status-header">
              <h4>
                {
                  WORKFLOW_TEMPLATES.find(
                    (t) => t.id === activeWorkflow.template,
                  )?.name
                }
              </h4>
              <Badge className={`status-badge status-${activeWorkflow.status}`}>
                {activeWorkflow.status}
              </Badge>
            </div>

            {/* Progress Bar */}
            <div className="progress-container">
              <div
                className="progress-bar"
                style={{ width: `${(activeWorkflow.progress || 0) * 100}%` }}
              />
              <span className="progress-text">
                {((activeWorkflow.progress || 0) * 100).toFixed(0)}%
              </span>
            </div>

            {/* Current Step */}
            {activeWorkflow.current_step && (
              <div className="current-step">
                <span className="step-label">Current Step:</span>
                <span className="step-value">
                  {activeWorkflow.current_step}
                </span>
              </div>
            )}

            {/* Error */}
            {activeWorkflow.error && (
              <div className="error-message">
                <span className="error-icon">❌</span>
                <span>{activeWorkflow.error}</span>
              </div>
            )}
          </Card>
        </section>
      )}

      {/* ML Metrics (from Eureka) */}
      {showMetrics && !metricsLoading && !metricsError && mlMetrics && (
        <section className="metrics-section">
          <div className="section-header-with-toggle">
            <h3 className="section-title">📊 ML Performance Metrics</h3>
            <button
              className="btn-toggle"
              onClick={() => setShowMetrics(false)}
            >
              Hide
            </button>
          </div>

          <div className="metrics-grid">
            {/* Usage Breakdown */}
            <Card className="metric-card">
              <h4 className="metric-title">🔮 ML vs Wargaming</h4>
              <div className="metric-value-large">
                {mlMetrics.usage_breakdown.ml_usage_rate.toFixed(1)}%
              </div>
              <div className="metric-label">ML Usage Rate</div>
              <div className="metric-details">
                <span>ML: {mlMetrics.usage_breakdown.ml_count}</span>
                <span>
                  Wargaming: {mlMetrics.usage_breakdown.wargaming_count}
                </span>
              </div>
            </Card>

            {/* Confidence */}
            <Card className="metric-card">
              <h4 className="metric-title">🎯 Avg Confidence</h4>
              <div className="metric-value-large">
                {(mlMetrics.avg_confidence * 100).toFixed(1)}%
              </div>
              <div className="metric-label">
                Trend: {mlMetrics.confidence_trend > 0 ? "📈" : "📉"}{" "}
                {mlMetrics.confidence_trend.toFixed(1)}%
              </div>
            </Card>

            {/* Time Savings */}
            <Card className="metric-card">
              <h4 className="metric-title">⚡ Time Savings</h4>
              <div className="metric-value-large">
                {mlMetrics.time_savings_percent.toFixed(0)}%
              </div>
              <div className="metric-label">
                {(mlMetrics.time_savings_absolute_minutes / 60).toFixed(1)}h
                saved
              </div>
            </Card>

            {/* Accuracy */}
            <Card className="metric-card">
              <h4 className="metric-title">🎲 Accuracy</h4>
              <div className="metric-value-large">
                {(
                  ((mlMetrics.confusion_matrix.true_positive +
                    mlMetrics.confusion_matrix.true_negative) /
                    (mlMetrics.confusion_matrix.true_positive +
                      mlMetrics.confusion_matrix.false_positive +
                      mlMetrics.confusion_matrix.false_negative +
                      mlMetrics.confusion_matrix.true_negative)) *
                  100
                ).toFixed(1)}
                %
              </div>
              <div className="metric-label">Confusion Matrix</div>
            </Card>
          </div>
        </section>
      )}

      {metricsError && (
        <div className="metrics-error">
          ⚠️ Failed to load ML metrics: {metricsError.message}
        </div>
      )}

      {/* Workflow History */}
      {workflowHistory.length > 0 && (
        <section className="history-section">
          <h3 className="section-title">📜 Recent Workflows</h3>
          <div className="history-list">
            {workflowHistory.map((workflow, idx) => (
              <Card key={idx} className="history-card">
                <div className="history-header">
                  <span className="history-template">
                    {
                      WORKFLOW_TEMPLATES.find((t) => t.id === workflow.template)
                        ?.icon
                    }{" "}
                    {
                      WORKFLOW_TEMPLATES.find((t) => t.id === workflow.template)
                        ?.name
                    }
                  </span>
                  <Badge className={`status-badge status-${workflow.status}`}>
                    {workflow.status}
                  </Badge>
                </div>
                <div className="history-time">
                  {formatDateTime(workflow.startedAt)}
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default MLAutomationTab;

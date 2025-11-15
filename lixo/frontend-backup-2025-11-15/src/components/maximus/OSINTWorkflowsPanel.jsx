/**
 * ═══════════════════════════════════════════════════════════════════════════
 * OSINT WORKFLOWS PANEL - AI-Driven Intelligence Gathering
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Unified interface for 3 OSINT workflows:
 * 1. Attack Surface Mapping 🎯 - Network recon + vulnerability correlation
 * 2. Credential Intelligence 🔑 - Breach data + dark web + username enumeration
 * 3. Deep Target Profiling 👤 - Social media + EXIF + behavioral patterns
 *
 * Authors: MAXIMUS Team
 * Date: 2025-10-15
 * Glory to YHWH
 */

import React, { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";
import {
  executeAttackSurfaceWorkflow,
  executeCredentialIntelWorkflow,
  executeTargetProfilingWorkflow,
  getWorkflowStatus,
  getWorkflowReport,
} from "@/api/adwService";
import logger from "@/utils/logger";
import "./OSINTWorkflowsPanel.css";

// Workflow types
const WORKFLOW_TYPES = {
  ATTACK_SURFACE: "attack_surface",
  CREDENTIAL_INTEL: "credential_intel",
  TARGET_PROFILE: "target_profile",
};

// Workflow status
const WORKFLOW_STATUS = {
  PENDING: "pending",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
};

// Risk/Exposure levels
const RISK_LEVELS = {
  CRITICAL: { value: "critical", color: "#ff0000", threshold: 70 },
  HIGH: { value: "high", color: "#ff4444", threshold: 50 },
  MEDIUM: { value: "medium", color: "#ff9944", threshold: 30 },
  LOW: { value: "low", color: "#ffcc44", threshold: 10 },
  INFO: { value: "info", color: "#44ff44", threshold: 0 },
};

/**
 * Main OSINT Workflows Panel Component
 */
export const OSINTWorkflowsPanel = () => {
  // Selected workflow type
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);

  // Form states
  const [attackSurfaceForm, setAttackSurfaceForm] = useState({
    domain: "",
    include_subdomains: true,
    port_range: "",
    scan_depth: "standard",
  });

  const [credentialIntelForm, setCredentialIntelForm] = useState({
    email: "",
    username: "",
    phone: "",
    include_darkweb: true,
    include_dorking: true,
    include_social: true,
  });

  const [targetProfileForm, setTargetProfileForm] = useState({
    username: "",
    email: "",
    phone: "",
    name: "",
    location: "",
    image_url: "",
    include_social: true,
    include_images: true,
  });

  // Execution state
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentWorkflowId, setCurrentWorkflowId] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [workflowReport, setWorkflowReport] = useState(null);

  // Validation errors
  const [validationErrors, setValidationErrors] = useState({});

  // Workflow history (from localStorage)
  const [workflowHistory, setWorkflowHistory] = useState([]);

  // Load workflow history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem("osint_workflow_history");
    if (savedHistory) {
      try {
        setWorkflowHistory(JSON.parse(savedHistory));
      } catch (error) {
        logger.error("Error loading workflow history:", error);
      }
    }
  }, []);

  // Save workflow history to localStorage
  const saveWorkflowHistory = useCallback(
    (workflow) => {
      const newHistory = [workflow, ...workflowHistory].slice(0, 50); // Keep last 50
      setWorkflowHistory(newHistory);
      localStorage.setItem(
        "osint_workflow_history",
        JSON.stringify(newHistory),
      );
    },
    [workflowHistory],
  );

  // Poll workflow status
  useEffect(() => {
    // Only poll if we have a workflow ID and it's currently executing
    if (!currentWorkflowId || !isExecuting) return;

    const POLL_INTERVAL = 5000; // 5 seconds (more reasonable than 2s)
    const MAX_POLLS = 60; // Timeout after 5 minutes
    let pollCount = 0;

    const interval = setInterval(async () => {
      pollCount++;

      // Timeout protection
      if (pollCount > MAX_POLLS) {
        clearInterval(interval);
        logger.error("Workflow polling timeout after 5 minutes");
        setIsExecuting(false);
        return;
      }

      try {
        const statusResponse = await getWorkflowStatus(currentWorkflowId);

        if (statusResponse.success) {
          const newStatus = statusResponse.data;
          setWorkflowStatus(newStatus);

          // If completed, fetch report and stop polling
          if (newStatus.status === WORKFLOW_STATUS.COMPLETED) {
            clearInterval(interval);
            const reportResponse = await getWorkflowReport(currentWorkflowId);

            if (reportResponse.success) {
              setWorkflowReport(reportResponse.data);
              setIsExecuting(false);

              // Save to history
              saveWorkflowHistory({
                workflow_id: currentWorkflowId,
                workflow_type: selectedWorkflow,
                status: WORKFLOW_STATUS.COMPLETED,
                executed_at: new Date().toISOString(),
                report: reportResponse.data,
              });
            }
          } else if (newStatus.status === WORKFLOW_STATUS.FAILED) {
            clearInterval(interval);
            setIsExecuting(false);
          }
        }
      } catch (error) {
        logger.error("Error polling workflow status:", error);
      }
    }, POLL_INTERVAL);

    // Cleanup on unmount or dependency change
    return () => {
      clearInterval(interval);
      logger.debug("Workflow polling stopped");
    };
  }, [currentWorkflowId, isExecuting, selectedWorkflow, saveWorkflowHistory]);

  // Validation functions
  const validateDomain = (domain) => {
    const domainRegex = /^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$/i;
    return domainRegex.test(domain);
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePhone = (phone) => {
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    return phoneRegex.test(phone.replace(/[-\s]/g, ""));
  };

  const validateURL = (url) => {
    const urlRegex = /^https?:\/\/.+/;
    return urlRegex.test(url);
  };

  // Validate Attack Surface form
  const validateAttackSurfaceForm = () => {
    const errors = {};

    if (!attackSurfaceForm.domain) {
      errors.domain = "Domain is required";
    } else if (!validateDomain(attackSurfaceForm.domain)) {
      errors.domain = "Invalid domain format";
    }

    if (attackSurfaceForm.port_range) {
      // Simple validation for port range (e.g., "80,443" or "1-1000")
      const portRangeRegex = /^(\d+(-\d+)?)(,\d+(-\d+)?)*$/;
      if (!portRangeRegex.test(attackSurfaceForm.port_range)) {
        errors.port_range =
          'Invalid port range format (e.g., "80,443" or "1-1000")';
      }
    }

    return errors;
  };

  // Validate Credential Intel form
  const validateCredentialIntelForm = () => {
    const errors = {};

    if (!credentialIntelForm.email && !credentialIntelForm.username) {
      errors.general = "Either email or username is required";
    }

    if (
      credentialIntelForm.email &&
      !validateEmail(credentialIntelForm.email)
    ) {
      errors.email = "Invalid email format";
    }

    if (
      credentialIntelForm.phone &&
      !validatePhone(credentialIntelForm.phone)
    ) {
      errors.phone = "Invalid phone format (e.g., +1-555-1234)";
    }

    return errors;
  };

  // Validate Target Profile form
  const validateTargetProfileForm = () => {
    const errors = {};

    if (
      !targetProfileForm.username &&
      !targetProfileForm.email &&
      !targetProfileForm.name
    ) {
      errors.general = "At least one of username, email, or name is required";
    }

    if (targetProfileForm.email && !validateEmail(targetProfileForm.email)) {
      errors.email = "Invalid email format";
    }

    if (targetProfileForm.phone && !validatePhone(targetProfileForm.phone)) {
      errors.phone = "Invalid phone format";
    }

    if (
      targetProfileForm.image_url &&
      !validateURL(targetProfileForm.image_url)
    ) {
      errors.image_url = "Invalid URL format";
    }

    return errors;
  };

  // Execute Attack Surface workflow
  const executeAttackSurface = async () => {
    const errors = validateAttackSurfaceForm();
    setValidationErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    setIsExecuting(true);
    setWorkflowReport(null);

    const response = await executeAttackSurfaceWorkflow(
      attackSurfaceForm.domain,
      {
        include_subdomains: attackSurfaceForm.include_subdomains,
        port_range: attackSurfaceForm.port_range || null,
        scan_depth: attackSurfaceForm.scan_depth,
      },
    );

    if (response.success) {
      setCurrentWorkflowId(response.data.workflow_id);
      setWorkflowStatus({
        status: WORKFLOW_STATUS.RUNNING,
        workflow_id: response.data.workflow_id,
      });
      logger.info(
        "Attack Surface workflow started:",
        response.data.workflow_id,
      );
    } else {
      setIsExecuting(false);
      setValidationErrors({ general: response.error });
      logger.error("Attack Surface workflow failed:", response.error);
    }
  };

  // Execute Credential Intel workflow
  const executeCredentialIntel = async () => {
    const errors = validateCredentialIntelForm();
    setValidationErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    setIsExecuting(true);
    setWorkflowReport(null);

    const response = await executeCredentialIntelWorkflow(credentialIntelForm);

    if (response.success) {
      setCurrentWorkflowId(response.data.workflow_id);
      setWorkflowStatus({
        status: WORKFLOW_STATUS.RUNNING,
        workflow_id: response.data.workflow_id,
      });
      logger.info(
        "Credential Intel workflow started:",
        response.data.workflow_id,
      );
    } else {
      setIsExecuting(false);
      setValidationErrors({ general: response.error });
      logger.error("Credential Intel workflow failed:", response.error);
    }
  };

  // Execute Target Profile workflow
  const executeTargetProfile = async () => {
    const errors = validateTargetProfileForm();
    setValidationErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    setIsExecuting(true);
    setWorkflowReport(null);

    const response = await executeTargetProfilingWorkflow(targetProfileForm);

    if (response.success) {
      setCurrentWorkflowId(response.data.workflow_id);
      setWorkflowStatus({
        status: WORKFLOW_STATUS.RUNNING,
        workflow_id: response.data.workflow_id,
      });
      logger.info(
        "Target Profile workflow started:",
        response.data.workflow_id,
      );
    } else {
      setIsExecuting(false);
      setValidationErrors({ general: response.error });
      logger.error("Target Profile workflow failed:", response.error);
    }
  };

  // Execute workflow based on selected type
  const executeWorkflow = () => {
    switch (selectedWorkflow) {
      case WORKFLOW_TYPES.ATTACK_SURFACE:
        executeAttackSurface();
        break;
      case WORKFLOW_TYPES.CREDENTIAL_INTEL:
        executeCredentialIntel();
        break;
      case WORKFLOW_TYPES.TARGET_PROFILE:
        executeTargetProfile();
        break;
      default:
        break;
    }
  };

  // Reset workflow
  const resetWorkflow = () => {
    setSelectedWorkflow(null);
    setIsExecuting(false);
    setCurrentWorkflowId(null);
    setWorkflowStatus(null);
    setWorkflowReport(null);
    setValidationErrors({});
  };

  // Export report as JSON
  const exportReportJSON = () => {
    if (!workflowReport) return;

    const dataStr = JSON.stringify(workflowReport, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `osint_workflow_${currentWorkflowId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Get risk level from score
  const getRiskLevel = (score) => {
    if (score >= RISK_LEVELS.CRITICAL.threshold) return RISK_LEVELS.CRITICAL;
    if (score >= RISK_LEVELS.HIGH.threshold) return RISK_LEVELS.HIGH;
    if (score >= RISK_LEVELS.MEDIUM.threshold) return RISK_LEVELS.MEDIUM;
    if (score >= RISK_LEVELS.LOW.threshold) return RISK_LEVELS.LOW;
    return RISK_LEVELS.INFO;
  };

  // Render workflow selector
  const renderWorkflowSelector = () => (
    <div className="osint-workflow-selector">
      <h2 className="osint-title">Select OSINT Workflow</h2>
      <div className="osint-workflow-cards">
        <div
          className={`osint-workflow-card attack-surface ${selectedWorkflow === WORKFLOW_TYPES.ATTACK_SURFACE ? "selected" : ""}`}
          onClick={() => setSelectedWorkflow(WORKFLOW_TYPES.ATTACK_SURFACE)}
          onKeyDown={(e) =>
            e.key === "Enter" &&
            setSelectedWorkflow(WORKFLOW_TYPES.ATTACK_SURFACE)
          }
          role="button"
          tabIndex={0}
        >
          <div className="osint-workflow-icon">🎯</div>
          <h3>Attack Surface Mapping</h3>
          <p>Network recon + vulnerability correlation</p>
          <div className="osint-workflow-features">
            <span>Subdomain Enumeration</span>
            <span>Port Scanning</span>
            <span>CVE Correlation</span>
            <span>Nuclei Scanning</span>
          </div>
        </div>

        <div
          className={`osint-workflow-card credential-intel ${selectedWorkflow === WORKFLOW_TYPES.CREDENTIAL_INTEL ? "selected" : ""}`}
          onClick={() => setSelectedWorkflow(WORKFLOW_TYPES.CREDENTIAL_INTEL)}
          onKeyDown={(e) =>
            e.key === "Enter" &&
            setSelectedWorkflow(WORKFLOW_TYPES.CREDENTIAL_INTEL)
          }
          role="button"
          tabIndex={0}
        >
          <div className="osint-workflow-icon">🔑</div>
          <h3>Credential Intelligence</h3>
          <p>Breach data + dark web + username enumeration</p>
          <div className="osint-workflow-features">
            <span>HIBP Breach Search</span>
            <span>Dark Web Monitoring</span>
            <span>Google Dorking</span>
            <span>Username Enumeration</span>
          </div>
        </div>

        <div
          className={`osint-workflow-card target-profile ${selectedWorkflow === WORKFLOW_TYPES.TARGET_PROFILE ? "selected" : ""}`}
          onClick={() => setSelectedWorkflow(WORKFLOW_TYPES.TARGET_PROFILE)}
          onKeyDown={(e) =>
            e.key === "Enter" &&
            setSelectedWorkflow(WORKFLOW_TYPES.TARGET_PROFILE)
          }
          role="button"
          tabIndex={0}
        >
          <div className="osint-workflow-icon">👤</div>
          <h3>Deep Target Profiling</h3>
          <p>Social media + EXIF + behavioral patterns</p>
          <div className="osint-workflow-features">
            <span>Social Media Scraping</span>
            <span>Image EXIF Analysis</span>
            <span>Pattern Detection</span>
            <span>SE Vulnerability</span>
          </div>
        </div>
      </div>
    </div>
  );

  // Render Attack Surface form
  const renderAttackSurfaceForm = () => (
    <div className="osint-input-form">
      <h3>Attack Surface Mapping Configuration</h3>

      <div className="osint-form-group">
        <label htmlFor="domain">Target Domain *</label>
        <input
          id="domain"
          type="text"
          value={attackSurfaceForm.domain}
          onChange={(e) =>
            setAttackSurfaceForm({
              ...attackSurfaceForm,
              domain: e.target.value,
            })
          }
          placeholder="example.com"
          className={validationErrors.domain ? "error" : ""}
        />
        {validationErrors.domain && (
          <span className="error-message">{validationErrors.domain}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="include-subdomains">
          <input
            id="include-subdomains"
            type="checkbox"
            checked={attackSurfaceForm.include_subdomains}
            onChange={(e) =>
              setAttackSurfaceForm({
                ...attackSurfaceForm,
                include_subdomains: e.target.checked,
              })
            }
          />
          Include Subdomain Enumeration
        </label>
      </div>

      <div className="osint-form-group">
        <label htmlFor="port-range">Port Range (optional)</label>
        <input
          id="port-range"
          type="text"
          value={attackSurfaceForm.port_range}
          onChange={(e) =>
            setAttackSurfaceForm({
              ...attackSurfaceForm,
              port_range: e.target.value,
            })
          }
          placeholder="1-1000 or 80,443,8080"
          className={validationErrors.port_range ? "error" : ""}
        />
        {validationErrors.port_range && (
          <span className="error-message">{validationErrors.port_range}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="scan-depth">Scan Depth</label>
        <select
          id="scan-depth"
          value={attackSurfaceForm.scan_depth}
          onChange={(e) =>
            setAttackSurfaceForm({
              ...attackSurfaceForm,
              scan_depth: e.target.value,
            })
          }
        >
          <option value="quick">Quick (Fast scan, basic checks)</option>
          <option value="standard">Standard (Balanced speed/coverage)</option>
          <option value="deep">Deep (Includes Nuclei scanning)</option>
        </select>
      </div>

      {validationErrors.general && (
        <div className="osint-error-general">{validationErrors.general}</div>
      )}

      <button
        className="osint-execute-button"
        onClick={executeWorkflow}
        disabled={isExecuting}
      >
        {isExecuting ? "Executing..." : "Execute Workflow"}
      </button>
    </div>
  );

  // Render Credential Intel form
  const renderCredentialIntelForm = () => (
    <div className="osint-input-form">
      <h3>Credential Intelligence Configuration</h3>

      <div className="osint-form-group">
        <label htmlFor="email">Email Address</label>
        <input
          id="email"
          type="email"
          value={credentialIntelForm.email}
          onChange={(e) =>
            setCredentialIntelForm({
              ...credentialIntelForm,
              email: e.target.value,
            })
          }
          placeholder="user@example.com"
          className={validationErrors.email ? "error" : ""}
        />
        {validationErrors.email && (
          <span className="error-message">{validationErrors.email}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          value={credentialIntelForm.username}
          onChange={(e) =>
            setCredentialIntelForm({
              ...credentialIntelForm,
              username: e.target.value,
            })
          }
          placeholder="johndoe"
          className={validationErrors.username ? "error" : ""}
        />
        {validationErrors.username && (
          <span className="error-message">{validationErrors.username}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="phone">Phone Number (optional)</label>
        <input
          id="phone"
          type="text"
          value={credentialIntelForm.phone}
          onChange={(e) =>
            setCredentialIntelForm({
              ...credentialIntelForm,
              phone: e.target.value,
            })
          }
          placeholder="+1-555-1234"
          className={validationErrors.phone ? "error" : ""}
        />
        {validationErrors.phone && (
          <span className="error-message">{validationErrors.phone}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="include-darkweb">
          <input
            id="include-darkweb"
            type="checkbox"
            checked={credentialIntelForm.include_darkweb}
            onChange={(e) =>
              setCredentialIntelForm({
                ...credentialIntelForm,
                include_darkweb: e.target.checked,
              })
            }
          />
          Include Dark Web Monitoring
        </label>
      </div>

      <div className="osint-form-group">
        <label htmlFor="include-dorking">
          <input
            id="include-dorking"
            type="checkbox"
            checked={credentialIntelForm.include_dorking}
            onChange={(e) =>
              setCredentialIntelForm({
                ...credentialIntelForm,
                include_dorking: e.target.checked,
              })
            }
          />
          Include Google Dorking
        </label>
      </div>

      <div className="osint-form-group">
        <label htmlFor="include-social">
          <input
            id="include-social"
            type="checkbox"
            checked={credentialIntelForm.include_social}
            onChange={(e) =>
              setCredentialIntelForm({
                ...credentialIntelForm,
                include_social: e.target.checked,
              })
            }
          />
          Include Social Media Discovery
        </label>
      </div>

      {validationErrors.general && (
        <div className="osint-error-general">{validationErrors.general}</div>
      )}

      <button
        className="osint-execute-button"
        onClick={executeWorkflow}
        disabled={isExecuting}
      >
        {isExecuting ? "Executing..." : "Execute Workflow"}
      </button>
    </div>
  );

  // Render Target Profile form
  const renderTargetProfileForm = () => (
    <div className="osint-input-form">
      <h3>Deep Target Profiling Configuration</h3>

      <div className="osint-form-group">
        <label htmlFor="profile-username">Username</label>
        <input
          id="profile-username"
          type="text"
          value={targetProfileForm.username}
          onChange={(e) =>
            setTargetProfileForm({
              ...targetProfileForm,
              username: e.target.value,
            })
          }
          placeholder="johndoe"
        />
      </div>

      <div className="osint-form-group">
        <label htmlFor="profile-email">Email Address</label>
        <input
          id="profile-email"
          type="email"
          value={targetProfileForm.email}
          onChange={(e) =>
            setTargetProfileForm({
              ...targetProfileForm,
              email: e.target.value,
            })
          }
          placeholder="john@example.com"
          className={validationErrors.email ? "error" : ""}
        />
        {validationErrors.email && (
          <span className="error-message">{validationErrors.email}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="profile-phone">Phone Number</label>
        <input
          id="profile-phone"
          type="text"
          value={targetProfileForm.phone}
          onChange={(e) =>
            setTargetProfileForm({
              ...targetProfileForm,
              phone: e.target.value,
            })
          }
          placeholder="+1-555-1234"
          className={validationErrors.phone ? "error" : ""}
        />
        {validationErrors.phone && (
          <span className="error-message">{validationErrors.phone}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="profile-name">Full Name</label>
        <input
          id="profile-name"
          type="text"
          value={targetProfileForm.name}
          onChange={(e) =>
            setTargetProfileForm({ ...targetProfileForm, name: e.target.value })
          }
          placeholder="John Doe"
        />
      </div>

      <div className="osint-form-group">
        <label htmlFor="profile-location">Location</label>
        <input
          id="profile-location"
          type="text"
          value={targetProfileForm.location}
          onChange={(e) =>
            setTargetProfileForm({
              ...targetProfileForm,
              location: e.target.value,
            })
          }
          placeholder="San Francisco, CA"
        />
      </div>

      <div className="osint-form-group">
        <label htmlFor="profile-image-url">Profile Image URL</label>
        <input
          id="profile-image-url"
          type="text"
          value={targetProfileForm.image_url}
          onChange={(e) =>
            setTargetProfileForm({
              ...targetProfileForm,
              image_url: e.target.value,
            })
          }
          placeholder="https://example.com/profile.jpg"
          className={validationErrors.image_url ? "error" : ""}
        />
        {validationErrors.image_url && (
          <span className="error-message">{validationErrors.image_url}</span>
        )}
      </div>

      <div className="osint-form-group">
        <label htmlFor="profile-include-social">
          <input
            id="profile-include-social"
            type="checkbox"
            checked={targetProfileForm.include_social}
            onChange={(e) =>
              setTargetProfileForm({
                ...targetProfileForm,
                include_social: e.target.checked,
              })
            }
          />
          Include Social Media Scraping
        </label>
      </div>

      <div className="osint-form-group">
        <label htmlFor="profile-include-images">
          <input
            id="profile-include-images"
            type="checkbox"
            checked={targetProfileForm.include_images}
            onChange={(e) =>
              setTargetProfileForm({
                ...targetProfileForm,
                include_images: e.target.checked,
              })
            }
          />
          Include Image EXIF Analysis
        </label>
      </div>

      {validationErrors.general && (
        <div className="osint-error-general">{validationErrors.general}</div>
      )}

      <button
        className="osint-execute-button"
        onClick={executeWorkflow}
        disabled={isExecuting}
      >
        {isExecuting ? "Executing..." : "Execute Workflow"}
      </button>
    </div>
  );

  // Render workflow form based on selected type
  const renderWorkflowForm = () => {
    switch (selectedWorkflow) {
      case WORKFLOW_TYPES.ATTACK_SURFACE:
        return renderAttackSurfaceForm();
      case WORKFLOW_TYPES.CREDENTIAL_INTEL:
        return renderCredentialIntelForm();
      case WORKFLOW_TYPES.TARGET_PROFILE:
        return renderTargetProfileForm();
      default:
        return null;
    }
  };

  // Render status tracker
  const renderStatusTracker = () => {
    if (!workflowStatus || workflowStatus.status === WORKFLOW_STATUS.PENDING) {
      return null;
    }

    return (
      <div className="osint-status-tracker">
        <h3>Workflow Execution Status</h3>
        <div className="osint-status-info">
          <span className="osint-status-label">Workflow ID:</span>
          <span className="osint-status-value">{currentWorkflowId}</span>
        </div>
        <div className="osint-status-info">
          <span className="osint-status-label">Status:</span>
          <span className={`osint-status-badge ${workflowStatus.status}`}>
            {workflowStatus.status.toUpperCase()}
          </span>
        </div>
        {workflowStatus.status === WORKFLOW_STATUS.RUNNING && (
          <div className="osint-status-spinner">
            <div className="spinner"></div>
            <span>Executing workflow phases...</span>
          </div>
        )}
      </div>
    );
  };

  // Render results viewer
  const renderResultsViewer = () => {
    if (!workflowReport) {
      return null;
    }

    const score =
      workflowReport.risk_score ||
      workflowReport.exposure_score ||
      workflowReport.se_score ||
      0;

    const riskLevel = getRiskLevel(score);

    return (
      <div className="osint-results-viewer">
        <div className="osint-results-header">
          <h3>Workflow Report</h3>
          <button className="osint-export-button" onClick={exportReportJSON}>
            Export JSON
          </button>
          <button className="osint-reset-button" onClick={resetWorkflow}>
            New Workflow
          </button>
        </div>

        {/* Executive Summary */}
        <div className="osint-executive-summary">
          <div className="osint-score-gauge">
            <div
              className="osint-gauge-fill"
              style={{
                background: `conic-gradient(${riskLevel.color} ${score}%, #1a1a1a ${score}%)`,
              }}
            >
              <div className="osint-gauge-inner">
                <span className="osint-score-value">{score.toFixed(1)}</span>
                <span className="osint-score-label">
                  {workflowReport.risk_score !== undefined && "Risk Score"}
                  {workflowReport.exposure_score !== undefined &&
                    "Exposure Score"}
                  {workflowReport.se_score !== undefined && "SE Vulnerability"}
                </span>
              </div>
            </div>
          </div>
          <div className="osint-summary-stats">
            <div className="osint-stat">
              <span className="osint-stat-value">
                {workflowReport.findings?.length || 0}
              </span>
              <span className="osint-stat-label">Total Findings</span>
            </div>
            {workflowReport.breach_count !== undefined && (
              <div className="osint-stat">
                <span className="osint-stat-value">
                  {workflowReport.breach_count}
                </span>
                <span className="osint-stat-label">Breaches</span>
              </div>
            )}
            {workflowReport.platform_presence && (
              <div className="osint-stat">
                <span className="osint-stat-value">
                  {workflowReport.platform_presence.length}
                </span>
                <span className="osint-stat-label">Platforms</span>
              </div>
            )}
          </div>
        </div>

        {/* AI Analysis Section - MAXIMUS AI Insights */}
        {workflowReport.ai_analysis && (
          <div className="osint-ai-analysis-section">
            <h4>🤖 MAXIMUS AI Analysis</h4>

            {workflowReport.ai_analysis.error ? (
              <div className="osint-ai-error">
                <p>⚠️ AI Analysis unavailable</p>
                <small>{workflowReport.ai_analysis.fallback}</small>
              </div>
            ) : (
              <>
                {/* Risk Assessment */}
                {workflowReport.ai_analysis.risk_score !== undefined && (
                  <div className="osint-ai-risk">
                    <span className="osint-ai-label">AI Risk Assessment:</span>
                    <span
                      className={`osint-ai-risk-badge ${workflowReport.ai_analysis.risk_level || "medium"}`}
                    >
                      {workflowReport.ai_analysis.risk_level?.toUpperCase() ||
                        "ANALYZING"}
                    </span>
                  </div>
                )}

                {/* Key Findings */}
                {workflowReport.ai_analysis.critical_insights && (
                  <div className="osint-ai-insights">
                    <h5>🔍 Key Findings</h5>
                    <ul className="osint-ai-insights-list">
                      {workflowReport.ai_analysis.critical_insights.map(
                        (insight, idx) => (
                          <li key={idx}>{insight}</li>
                        ),
                      )}
                    </ul>
                  </div>
                )}

                {/* Attack Vectors */}
                {workflowReport.ai_analysis.attack_vectors && (
                  <div className="osint-ai-vectors">
                    <h5>🎯 Identified Attack Vectors</h5>
                    <ul className="osint-ai-vectors-list">
                      {workflowReport.ai_analysis.attack_vectors.map(
                        (vector, idx) => (
                          <li key={idx}>{vector}</li>
                        ),
                      )}
                    </ul>
                  </div>
                )}

                {/* AI Recommendations */}
                {workflowReport.ai_analysis.recommendations && (
                  <div className="osint-ai-recommendations">
                    <h5>💡 AI Recommendations</h5>
                    <ul className="osint-ai-recommendations-list">
                      {workflowReport.ai_analysis.recommendations.map(
                        (rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ),
                      )}
                    </ul>
                  </div>
                )}

                {/* Executive Summary */}
                {workflowReport.ai_analysis.executive_summary && (
                  <div className="osint-ai-summary">
                    <h5>📋 Executive Summary</h5>
                    <p>{workflowReport.ai_analysis.executive_summary}</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Findings Table */}
        {workflowReport.findings && workflowReport.findings.length > 0 && (
          <div className="osint-findings-section">
            <h4>Findings ({workflowReport.findings.length})</h4>
            <div className="osint-findings-table">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Target</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {workflowReport.findings
                    .slice(0, 10)
                    .map((finding, index) => (
                      <tr key={index}>
                        <td>{finding.finding_type || finding.type}</td>
                        <td>
                          <span
                            className={`severity-badge ${finding.severity}`}
                          >
                            {finding.severity}
                          </span>
                        </td>
                        <td>{finding.target}</td>
                        <td className="finding-details">
                          {JSON.stringify(finding.details).substring(0, 100)}...
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
              {workflowReport.findings.length > 10 && (
                <p className="osint-findings-more">
                  +{workflowReport.findings.length - 10} more findings (export
                  JSON for full report)
                </p>
              )}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {workflowReport.recommendations &&
          workflowReport.recommendations.length > 0 && (
            <div className="osint-recommendations-section">
              <h4>Recommendations ({workflowReport.recommendations.length})</h4>
              <ul className="osint-recommendations-list">
                {workflowReport.recommendations.map((rec, index) => (
                  <li key={index} className="osint-recommendation-item">
                    <span className="osint-recommendation-number">
                      {index + 1}
                    </span>
                    <span className="osint-recommendation-text">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
      </div>
    );
  };

  return (
    <div className="osint-workflows-panel">
      {!selectedWorkflow && renderWorkflowSelector()}
      {selectedWorkflow && !workflowReport && (
        <div className="osint-workflow-execution">
          <button className="osint-back-button" onClick={resetWorkflow}>
            ← Back to Workflow Selection
          </button>
          {renderWorkflowForm()}
          {renderStatusTracker()}
        </div>
      )}
      {workflowReport && renderResultsViewer()}
    </div>
  );
};

OSINTWorkflowsPanel.propTypes = {};

export default OSINTWorkflowsPanel;

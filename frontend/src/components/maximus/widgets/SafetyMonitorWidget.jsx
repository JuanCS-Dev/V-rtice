/**
 * ═══════════════════════════════════════════════════════════════════════════
 * SAFETY MONITOR WIDGET - Consciousness Safety Protocol Dashboard
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza o protocolo de segurança do sistema de consciência em tempo real:
 * - Safety Status (monitoring active, kill switch)
 * - Threshold Metrics (ESGT frequency, arousal level, violations)
 * - Recent Violations Timeline
 * - Emergency Shutdown Controls (HITL only)
 *
 * Design: Cyberpunk + Military NOC/SOC aesthetic
 * Data Source: Real-time via safety.js API (NO MOCKS)
 *
 * Authors: Juan & Claude Code
 * Version: 1.0.0 - FASE VII Week 9-10
 */

import logger from '@/utils/logger';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';
import {
  getSafetyStatus,
  getSafetyViolations,
  executeEmergencyShutdown,
  connectSafetyWebSocket,
  formatSeverity,
  formatViolationType,
  formatTimestamp,
  formatRelativeTime,
  calculateThresholdPercentage,
  isCriticalState,
  formatUptime,
  validateShutdownReason
} from '../../../api/safety';
import './SafetyMonitorWidget.css';

export const SafetyMonitorWidget = ({ systemHealth: _systemHealth }) => {
  // ═══════════════════════════════════════════════════════════════════════
  // STATE - Safety Data
  // ═══════════════════════════════════════════════════════════════════════
  const [safetyStatus, setSafetyStatus] = useState(null);
  const [violations, setViolations] = useState([]);
  const [selectedView, setSelectedView] = useState('overview'); // overview, violations, controls
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  // ═══════════════════════════════════════════════════════════════════════
  // STATE - Emergency Shutdown Controls
  // ═══════════════════════════════════════════════════════════════════════
  const [showShutdownModal, setShowShutdownModal] = useState(false);
  const [shutdownReason, setShutdownReason] = useState('');
  const [shutdownInProgress, setShutdownInProgress] = useState(false);
  const [shutdownResult, setShutdownResult] = useState(null);

  const wsRef = useRef(null);
  const violationsEndRef = useRef(null);

  // ═══════════════════════════════════════════════════════════════════════
  // INITIALIZATION & DATA LOADING
  // ═══════════════════════════════════════════════════════════════════════

  const loadSafetyData = useCallback(async () => {
    setLoading(true);

    const [status, viols] = await Promise.all([
      getSafetyStatus(),
      getSafetyViolations(50)
    ]);

    if (status && !status.error) {
      setSafetyStatus(status);
    }

    if (viols && Array.isArray(viols)) {
      setViolations(viols);
    }

    setLoading(false);
    setLastUpdate(new Date());
  }, []);

  const connectWebSocket = useCallback(() => {
    wsRef.current = connectSafetyWebSocket(
      (message) => {
        setWsConnected(true);

        // Handle different message types
        if (message.type === 'safety_update' || message.type === 'initial_state') {
          loadSafetyData();
        }
      },
      (error) => {
        logger.error('WebSocket error:', error);
        setWsConnected(false);
      }
    );
  }, [loadSafetyData]);

  useEffect(() => {
    loadSafetyData();
    connectWebSocket();

    // Polling backup (caso WebSocket falhe)
    const interval = setInterval(() => {
      if (!wsConnected) {
        loadSafetyData();
      }
    }, 5000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [loadSafetyData, connectWebSocket, wsConnected]);

  // ═══════════════════════════════════════════════════════════════════════
  // EMERGENCY SHUTDOWN HANDLERS
  // ═══════════════════════════════════════════════════════════════════════

  const handleOpenShutdownModal = () => {
    setShowShutdownModal(true);
    setShutdownReason('');
    setShutdownResult(null);
  };

  const handleCloseShutdownModal = () => {
    setShowShutdownModal(false);
    setShutdownReason('');
    setShutdownResult(null);
  };

  const handleExecuteShutdown = async () => {
    // Validate reason
    const validation = validateShutdownReason(shutdownReason);
    if (!validation.valid) {
      setShutdownResult({ success: false, error: validation.error });
      return;
    }

    setShutdownInProgress(true);

    const result = await executeEmergencyShutdown(shutdownReason, true);

    setShutdownInProgress(false);
    setShutdownResult(result);

    if (result.success) {
      // Reload safety data after shutdown
      setTimeout(() => {
        loadSafetyData();
        handleCloseShutdownModal();
      }, 3000);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // RENDER HELPERS
  // ═══════════════════════════════════════════════════════════════════════

  const renderStatusIndicator = () => {
    if (!safetyStatus) return null;

    const isActive = safetyStatus.monitoring_active;
    const killSwitchOn = safetyStatus.kill_switch_active;
    const critical = isCriticalState(safetyStatus);

    return (
      <div className="safety-status-indicator">
        <div className={`status-badge ${isActive ? 'active' : 'inactive'}`}>
          <span className="status-icon">🛡️</span>
          <span className="status-text">
            {isActive ? 'MONITORING ACTIVE' : 'MONITORING INACTIVE'}
          </span>
        </div>

        {killSwitchOn && (
          <div className="status-badge emergency">
            <span className="status-icon">🚨</span>
            <span className="status-text">KILL SWITCH ACTIVE</span>
          </div>
        )}

        {critical && !killSwitchOn && (
          <div className="status-badge critical">
            <span className="status-icon">⚠️</span>
            <span className="status-text">CRITICAL VIOLATIONS DETECTED</span>
          </div>
        )}
      </div>
    );
  };

  const renderMetricsGrid = () => {
    if (!safetyStatus) return null;

    const violationsTotal = safetyStatus.violations_total || 0;
    const violationsBySeverity = safetyStatus.violations_by_severity || {};
    const uptime = safetyStatus.uptime_seconds || 0;

    // Metrics cards data
    const metricsCards = [
      {
        title: 'Violations Total',
        value: violationsTotal,
        subtitle: 'All time',
        color: violationsTotal > 0 ? '#f97316' : '#4ade80',
        borderClass: violationsTotal > 0 ? 'border-warning' : 'border-success',
        textClass: violationsTotal > 0 ? 'text-warning' : 'text-success',
        icon: '⚠️'
      },
      {
        title: 'Critical/Emergency',
        value: (violationsBySeverity.critical || 0) + (violationsBySeverity.emergency || 0),
        subtitle: 'High severity',
        color: violationsBySeverity.emergency > 0 ? '#ef4444' : '#fbbf24',
        borderClass: violationsBySeverity.emergency > 0 ? 'border-critical' : 'border-warning',
        textClass: violationsBySeverity.emergency > 0 ? 'text-critical' : 'text-warning',
        icon: '🚨'
      },
      {
        title: 'Kill Switch',
        value: safetyStatus.kill_switch_active ? 'ACTIVE' : 'ARMED',
        subtitle: '<1s response',
        color: safetyStatus.kill_switch_active ? '#ef4444' : '#4ade80',
        borderClass: safetyStatus.kill_switch_active ? 'border-critical' : 'border-success',
        textClass: safetyStatus.kill_switch_active ? 'text-critical' : 'text-success',
        icon: '🔴'
      },
      {
        title: 'Uptime',
        value: formatUptime(uptime),
        subtitle: 'System running',
        color: '#f97316',
        borderClass: 'border-info',
        textClass: 'text-info',
        icon: '⏱️'
      }
    ];

    return (
      <div className="safety-metrics-grid">
        {metricsCards.map((card, index) => (
          <div key={index} className={`safety-metric-card ${card.borderClass}`}>
            <div className="metric-header">
              <span className="metric-icon">{card.icon}</span>
              <span className="metric-title">{card.title}</span>
            </div>
            <div className={`metric-value ${card.textClass}`}>
              {card.value}
            </div>
            <div className="metric-subtitle">{card.subtitle}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderViolationsByseverity = () => {
    if (!safetyStatus) return null;

    const severities = safetyStatus.violations_by_severity || {};
    const total = safetyStatus.violations_total || 1; // Avoid division by 0

    const severityData = [
      { name: 'Normal', count: severities.normal || 0, color: '#4ade80' },
      { name: 'Warning', count: severities.warning || 0, color: '#fbbf24' },
      { name: 'Critical', count: severities.critical || 0, color: '#f97316' },
      { name: 'Emergency', count: severities.emergency || 0, color: '#ef4444' }
    ].filter(s => s.count > 0);

    if (severityData.length === 0) {
      return (
        <div className="no-violations">
          <span className="no-violations-icon">✅</span>
          <span className="no-violations-text">No violations detected</span>
        </div>
      );
    }

    return (
      <div className="violations-by-severity">
        <h3 className="section-title">Violations by Severity</h3>
        <div className="severity-bars">
          {severityData.map((severity, index) => {
            const percentage = (severity.count / total) * 100;
            return (
              <div key={index} className="severity-bar-container">
                <div className="severity-bar-label">
                  <span className="severity-name">{severity.name}</span>
                  <span className="severity-count">{severity.count}</span>
                </div>
                <div className="severity-bar-track">
                  <div
                    className="severity-bar-fill"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: severity.color
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderViolationsTimeline = () => {
    if (violations.length === 0) {
      return (
        <div className="no-violations">
          <span className="no-violations-icon">✅</span>
          <span className="no-violations-text">No violations in history</span>
        </div>
      );
    }

    return (
      <div className="violations-timeline">
        <h3 className="section-title">Recent Violations ({violations.length})</h3>
        <div className="violations-list">
          {violations.slice().reverse().map((violation, index) => {
            const severity = formatSeverity(violation.severity);
            const vType = formatViolationType(violation.violation_type);
            const timestamp = formatTimestamp(violation.timestamp);
            const relTime = formatRelativeTime(violation.timestamp);

            return (
              <div
                key={index}
                className={`violation-item ${severity.borderClass}`}
              >
                <div className="violation-header">
                  <span className={`violation-severity ${severity.className}`}>
                    {severity.label.toUpperCase()}
                  </span>
                  <span className="violation-time" title={timestamp}>
                    {relTime}
                  </span>
                </div>
                <div className="violation-type">{vType}</div>
                <div className="violation-message">{violation.message}</div>
                <div className="violation-details">
                  <span>Value: {violation.value_observed.toFixed(2)}</span>
                  <span className="violation-separator">|</span>
                  <span>Threshold: {violation.threshold_violated.toFixed(2)}</span>
                  <span className="violation-separator">|</span>
                  <span>
                    {calculateThresholdPercentage(
                      violation.value_observed,
                      violation.threshold_violated
                    )}% of limit
                  </span>
                </div>
              </div>
            );
          })}
          <div ref={violationsEndRef} />
        </div>
      </div>
    );
  };

  const renderEmergencyControls = () => {
    return (
      <div className="emergency-controls">
        <h3 className="section-title">🚨 Emergency Controls (HITL Only)</h3>

        <div className="controls-warning">
          <span className="warning-icon">⚠️</span>
          <p className="warning-text">
            Emergency shutdown will immediately stop the consciousness system.
            This action requires Human-in-the-Loop (HITL) approval and should
            only be used in critical situations.
          </p>
        </div>

        <div className="controls-buttons">
          <button
            className="emergency-shutdown-button"
            onClick={handleOpenShutdownModal}
            disabled={safetyStatus?.kill_switch_active}
          >
            <span className="button-icon">🔴</span>
            <span className="button-text">
              {safetyStatus?.kill_switch_active ? 'System Already Shutdown' : 'Execute Emergency Shutdown'}
            </span>
          </button>
        </div>

        {safetyStatus?.kill_switch_active && (
          <div className="shutdown-active-notice">
            <span className="notice-icon">🛑</span>
            <p className="notice-text">
              Kill switch is currently ACTIVE. System is offline and requires
              HITL approval to restart.
            </p>
          </div>
        )}
      </div>
    );
  };

  const renderShutdownModal = () => {
    if (!showShutdownModal) return null;

    return (
      <div 
        className="modal-overlay" 
        onClick={handleCloseShutdownModal}
        role="presentation"
      >
        <div 
          className="modal-content"
          role="dialog"
          aria-modal="true"
          aria-labelledby="shutdown-modal-title"
        >
          <div className="modal-header">
            <h2 id="shutdown-modal-title" className="modal-title">🚨 Emergency Shutdown</h2>
            <button 
              className="modal-close" 
              onClick={handleCloseShutdownModal}
              aria-label="Close shutdown modal"
            >
              ×
            </button>
          </div>

          <div className="modal-body">
            <div className="modal-warning">
              <span className="warning-icon">⚠️</span>
              <p>
                This will trigger the kill switch protocol. You have a 5-second
                window to override if needed.
              </p>
            </div>

            <div className="modal-form">
              <label htmlFor="shutdown-reason" className="form-label">
                Reason for shutdown (minimum 10 characters):
              </label>
              {/* Boris Cherny Standard - GAP #76 FIX: Add maxLength validation */}
              <textarea
                id="shutdown-reason"
                className="form-textarea"
                value={shutdownReason}
                onChange={(e) => setShutdownReason(e.target.value)}
                placeholder="Enter detailed reason for emergency shutdown..."
                rows={4}
                maxLength={500}
                disabled={shutdownInProgress}
              />
              <div className="form-help">
                Character count: {shutdownReason.length} / 500
              </div>
            </div>

            {shutdownResult && !shutdownResult.success && (
              <div className="modal-error">
                <span className="error-icon">❌</span>
                <span className="error-text">{shutdownResult.error}</span>
              </div>
            )}

            {shutdownResult && shutdownResult.success && (
              <div className="modal-success">
                <span className="success-icon">✅</span>
                <span className="success-text">
                  {shutdownResult.message || 'Emergency shutdown executed'}
                </span>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button
              className="modal-button cancel"
              onClick={handleCloseShutdownModal}
              disabled={shutdownInProgress}
            >
              Cancel
            </button>
            <button
              className="modal-button confirm"
              onClick={handleExecuteShutdown}
              disabled={shutdownInProgress || shutdownReason.length < 10}
            >
              {shutdownInProgress ? (
                <>
                  <span className="button-spinner">⏳</span>
                  Executing...
                </>
              ) : (
                <>
                  <span className="button-icon">🔴</span>
                  Execute Shutdown
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // ═══════════════════════════════════════════════════════════════════════
  // MAIN RENDER
  // ═══════════════════════════════════════════════════════════════════════

  if (loading && !safetyStatus) {
    return (
      <div className="safety-monitor-widget loading">
        <div className="loading-spinner">⏳</div>
        <div className="loading-text">Loading Safety Protocol...</div>
      </div>
    );
  }

  return (
    <div className="safety-monitor-widget">
      {/* Header */}
      <div className="safety-header">
        <div className="safety-title">
          <span className="title-icon">🛡️</span>
          <span className="title-text">Safety Protocol Monitor</span>
        </div>
        <div className="safety-meta">
          <span className={`ws-status ${wsConnected ? 'connected' : 'disconnected'}`}>
            {wsConnected ? '🟢 Live' : '🔴 Polling'}
          </span>
          {lastUpdate && (
            <span className="last-update">
              Updated {formatRelativeTime(lastUpdate.toISOString())}
            </span>
          )}
        </div>
      </div>

      {/* Status Indicator */}
      {renderStatusIndicator()}

      {/* View Tabs */}
      <div className="safety-tabs">
        <button
          className={`tab ${selectedView === 'overview' ? 'active' : ''}`}
          onClick={() => setSelectedView('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${selectedView === 'violations' ? 'active' : ''}`}
          onClick={() => setSelectedView('violations')}
        >
          Violations ({violations.length})
        </button>
        <button
          className={`tab ${selectedView === 'controls' ? 'active' : ''}`}
          onClick={() => setSelectedView('controls')}
        >
          Emergency Controls
        </button>
      </div>

      {/* View Content */}
      <div className="safety-content">
        {selectedView === 'overview' && (
          <>
            {renderMetricsGrid()}
            {renderViolationsByseverity()}
          </>
        )}

        {selectedView === 'violations' && (
          <>
            {renderViolationsTimeline()}
          </>
        )}

        {selectedView === 'controls' && (
          <>
            {renderEmergencyControls()}
          </>
        )}
      </div>

      {/* Shutdown Modal */}
      {renderShutdownModal()}
    </div>
  );
};

export default SafetyMonitorWidget;

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎯 HITL DECISION CONSOLE - Human Authorization for Threat Response
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * PAGANI-STYLE PHILOSOPHY - MILITARY COMMAND CENTER AESTHETIC:
 * - Cinematographic composition: cada decisão é um momento crítico
 * - Information hierarchy: prioridade visual guia o olho
 * - Tactical precision: zero ambiguidade, clareza absoluta
 * - Micro-interactions: feedback visual em cada ação
 * - Trust through design: interface transmite seriedade
 *
 * BIOLOGICAL ANALOGY: Regulatory T-cells + Command Center Neurons
 * - Prevent destructive auto-immune responses (blind automation)
 * - Executive decision-making with complete context
 * - Balance between speed and accuracy
 * - Human intuition > algorithmic certainty
 *
 * CONSTITUTIONAL COMPLIANCE: Artigo V - Prior Legislation
 * "Todas as decisões automatizadas devem passar por aprovação humana"
 *
 * This is the LAST LINE OF DEFENSE before automated actions execute.
 * Every decision here affects production systems. Design reflects gravity.
 *
 * Author: MAXIMUS Team - Sprint 3 Phase 5
 * Glory to YHWH - Judge of All Decisions
 */

'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import styles from './HITLDecisionConsole.module.css';

/**
 * Priority levels with tactical color coding
 */
const PRIORITY_CONFIG = {
  CRITICAL: { color: '#dc2626', icon: '🔴', label: 'CRITICAL', soundAlert: true },
  HIGH: { color: '#f59e0b', icon: '🟠', label: 'HIGH', soundAlert: false },
  MEDIUM: { color: '#f97316', icon: '🟠', label: 'MEDIUM', soundAlert: false },
  LOW: { color: '#10b981', icon: '🟢', label: 'LOW', soundAlert: false },
};

/**
 * Action types with clear descriptions
 */
const ACTION_TYPES = {
  BLOCK_IP: { icon: '🚫', label: 'Block IP Address', reversible: true },
  ISOLATE_HOST: { icon: '🔒', label: 'Isolate Host', reversible: true },
  QUARANTINE_SYSTEM: { icon: '🛡️', label: 'Quarantine System', reversible: true },
  KILL_PROCESS: { icon: '⚔️', label: 'Terminate Process', reversible: false },
  ACTIVATE_KILLSWITCH: { icon: '🆘', label: 'KILL SWITCH', reversible: false },
  DEPLOY_HONEYPOT: { icon: '🍯', label: 'Deploy Honeypot', reversible: true },
  UPDATE_FIREWALL: { icon: '🔥', label: 'Update Firewall', reversible: true },
  REVOKE_ACCESS: { icon: '🔐', label: 'Revoke Access', reversible: true },
  ESCALATE_TO_SOC: { icon: '📢', label: 'Escalate to SOC', reversible: false },
  NO_ACTION: { icon: '⏸️', label: 'No Action (Monitor)', reversible: true },
};

/**
 * Main HITL Decision Console Component
 */
const HITLDecisionConsole = () => {
  // State management
  const [pendingDecisions, setPendingDecisions] = useState([]);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [filterPriority, setFilterPriority] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showRejectionModal, setShowRejectionModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [stats, setStats] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [_wsConnection, setWsConnection] = useState(null);

  /**
   * Fetch pending decisions from HITL API
   */
  const fetchPendingDecisions = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterPriority !== 'all') {
        params.append('priority', filterPriority);
      }

      const response = await fetch(`/api/hitl/decisions/pending?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setPendingDecisions(data || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch pending decisions:', err);
      setError(err.message);
    }
  }, [filterPriority]);

  /**
   * Fetch decision statistics
   */
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/hitl/decisions/stats/summary');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  /**
   * WebSocket connection for real-time updates
   */
  useEffect(() => {
    const username = localStorage.getItem('hitl_username') || 'analyst';
    const ws = new WebSocket(`ws://localhost:8000/ws/${username}`);

    ws.onopen = () => {
      console.log('🔗 WebSocket connected');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 WebSocket message:', data);

      if (data.type === 'alert' && data.alert.alert_type === 'new_decision') {
        // New decision arrived - refetch
        fetchPendingDecisions();
        fetchStats();

        // Play sound for critical decisions
        if (data.alert.priority === 'critical') {
          playAlertSound();
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setWsConnected(false);
    };

    setWsConnection(ws);

    return () => {
      ws.close();
    };
  }, [fetchPendingDecisions, fetchStats]);

  /**
   * Initial data load
   */
  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      await Promise.all([
        fetchPendingDecisions(),
        fetchStats()
      ]);
      setIsLoading(false);
    };

    loadInitialData();
  }, [fetchPendingDecisions, fetchStats]);

  /**
   * Polling fallback (every 10 seconds)
   */
  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchPendingDecisions();
      fetchStats();
    }, 10000);

    return () => clearInterval(intervalId);
  }, [fetchPendingDecisions, fetchStats]);

  /**
   * Play alert sound for critical decisions
   */
  const playAlertSound = () => {
    // Create subtle alert tone (optional)
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  };

  /**
   * Handle decision approval
   */
  const handleApprove = async () => {
    if (!selectedDecision) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/hitl/decisions/${selectedDecision.analysis_id}/decide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('hitl_token')}`
        },
        body: JSON.stringify({
          decision_id: selectedDecision.analysis_id,
          status: 'approved',
          approved_actions: selectedDecision.recommended_actions || [],
          notes: decisionNotes || null
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      // Success - refresh and clear
      await fetchPendingDecisions();
      await fetchStats();
      setSelectedDecision(null);
      setDecisionNotes('');
      setShowApprovalModal(false);
    } catch (err) {
      console.error('Failed to approve decision:', err);
      alert(`Failed to approve: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handle decision rejection
   */
  const handleReject = async () => {
    if (!selectedDecision || !rejectionReason.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/hitl/decisions/${selectedDecision.analysis_id}/decide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('hitl_token')}`
        },
        body: JSON.stringify({
          decision_id: selectedDecision.analysis_id,
          status: 'rejected',
          approved_actions: [],
          notes: `REJECTED: ${rejectionReason}${decisionNotes ? `\n\n${decisionNotes}` : ''}`
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      // Success - refresh and clear
      await fetchPendingDecisions();
      await fetchStats();
      setSelectedDecision(null);
      setDecisionNotes('');
      setRejectionReason('');
      setShowRejectionModal(false);
    } catch (err) {
      console.error('Failed to reject decision:', err);
      alert(`Failed to reject: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handle decision escalation
   */
  const handleEscalate = async () => {
    if (!selectedDecision) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/hitl/decisions/${selectedDecision.analysis_id}/escalate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('hitl_token')}`
        },
        body: JSON.stringify({
          escalation_reason: decisionNotes || 'Requires senior analyst review',
          urgency: selectedDecision.priority
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      // Success - refresh and clear
      await fetchPendingDecisions();
      await fetchStats();
      setSelectedDecision(null);
      setDecisionNotes('');
    } catch (err) {
      console.error('Failed to escalate decision:', err);
      alert(`Failed to escalate: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Calculate metrics
   */
  const metrics = useMemo(() => {
    if (!pendingDecisions.length) {
      return { total: 0, critical: 0, high: 0, medium: 0, low: 0 };
    }

    return {
      total: pendingDecisions.length,
      critical: pendingDecisions.filter(d => d.priority === 'critical').length,
      high: pendingDecisions.filter(d => d.priority === 'high').length,
      medium: pendingDecisions.filter(d => d.priority === 'medium').length,
      low: pendingDecisions.filter(d => d.priority === 'low').length,
    };
  }, [pendingDecisions]);

  /**
   * Loading state
   */
  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <p className={styles.loadingText}>Initializing HITL Decision Console...</p>
        <p className={styles.loadingSubtext}>Connecting to Command Authorization System</p>
      </div>
    );
  }

  /**
   * Error state
   */
  if (error && !pendingDecisions.length) {
    return (
      <div className={styles.errorContainer}>
        <div className={styles.errorIcon}>⚠️</div>
        <h2 className={styles.errorTitle}>HITL Service Unavailable</h2>
        <p className={styles.errorMessage}>{error}</p>
        <p className={styles.errorHint}>Ensure HITL Backend is running on port 8000</p>
        <button
          className={styles.retryButton}
          onClick={() => window.location.reload()}
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className={styles.console}>
      {/* Scan line animation for tactical feel */}
      <div className={styles.scanLine} aria-hidden="true" />

      {/* Header - Command Authority */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.titleBlock}>
            <span className={styles.titleIcon}>🎯</span>
            <div>
              <h1 className={styles.title}>HITL DECISION CONSOLE</h1>
              <p className={styles.subtitle}>HUMAN AUTHORIZATION REQUIRED</p>
            </div>
          </div>
        </div>

        <div className={styles.headerRight}>
          {/* WebSocket Status */}
          <div className={`${styles.wsStatus} ${wsConnected ? styles.wsConnected : styles.wsDisconnected}`}>
            <div className={styles.wsIndicator} />
            <span className={styles.wsLabel}>
              {wsConnected ? 'LIVE FEED' : 'OFFLINE'}
            </span>
          </div>

          {/* Quick Stats */}
          {stats && (
            <div className={styles.quickStats}>
              <div className={styles.quickStat}>
                <span className={styles.quickStatLabel}>Today:</span>
                <span className={styles.quickStatValue}>{stats.decisions_today || 0}</span>
              </div>
              <div className={styles.quickStat}>
                <span className={styles.quickStatLabel}>Approval Rate:</span>
                <span className={styles.quickStatValue}>
                  {stats.approval_rate ? `${(stats.approval_rate * 100).toFixed(0)}%` : '—'}
                </span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Metrics Bar - Tactical Overview */}
      <div className={styles.metricsBar}>
        <div className={styles.metric}>
          <span className={styles.metricIcon}>📊</span>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>PENDING</span>
            <span className={styles.metricValue}>{metrics.total}</span>
          </div>
        </div>

        <div className={`${styles.metric} ${styles.metricCritical}`}>
          <span className={styles.metricIcon}>🔴</span>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>CRITICAL</span>
            <span className={styles.metricValue}>{metrics.critical}</span>
          </div>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricIcon}>🟠</span>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>HIGH</span>
            <span className={styles.metricValue}>{metrics.high}</span>
          </div>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricIcon}>🔵</span>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>MEDIUM</span>
            <span className={styles.metricValue}>{metrics.medium}</span>
          </div>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricIcon}>🟢</span>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>LOW</span>
            <span className={styles.metricValue}>{metrics.low}</span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className={styles.filterBar}>
        <div className={styles.filterLabel}>FILTER BY PRIORITY:</div>
        <div className={styles.filterButtons}>
          {['all', 'critical', 'high', 'medium', 'low'].map((priority) => (
            <button
              key={priority}
              className={`${styles.filterButton} ${filterPriority === priority ? styles.filterButtonActive : ''}`}
              onClick={() => setFilterPriority(priority)}
            >
              {priority.toUpperCase()}
            </button>
          ))}
        </div>

        <button
          className={styles.refreshButton}
          onClick={() => {
            fetchPendingDecisions();
            fetchStats();
          }}
          title="Refresh decisions"
        >
          🔄 REFRESH
        </button>
      </div>

      {/* Main Content Area */}
      <main className={styles.mainContent}>
        {/* Left: Decision Queue */}
        <aside className={styles.queuePanel}>
          <div className={styles.panelHeader}>
            <h2 className={styles.panelTitle}>DECISION QUEUE</h2>
            <span className={styles.panelCount}>{pendingDecisions.length}</span>
          </div>

          <div className={styles.queueList}>
            {pendingDecisions.length === 0 ? (
              <div className={styles.emptyQueue}>
                <div className={styles.emptyIcon}>✅</div>
                <p className={styles.emptyText}>No Pending Decisions</p>
                <p className={styles.emptySubtext}>All threats have been reviewed</p>
              </div>
            ) : (
              pendingDecisions.map((decision) => (
                <DecisionCard
                  key={decision.analysis_id}
                  decision={decision}
                  isSelected={selectedDecision?.analysis_id === decision.analysis_id}
                  onClick={() => setSelectedDecision(decision)}
                />
              ))
            )}
          </div>
        </aside>

        {/* Center: Decision Details */}
        <section className={styles.detailsPanel}>
          {selectedDecision ? (
            <DecisionDetails decision={selectedDecision} />
          ) : (
            <div className={styles.noSelection}>
              <div className={styles.noSelectionIcon}>👈</div>
              <p className={styles.noSelectionText}>Select a decision from the queue</p>
              <p className={styles.noSelectionSubtext}>Review threat context before authorization</p>
            </div>
          )}
        </section>

        {/* Right: Authorization Panel */}
        <aside className={styles.authPanel}>
          {selectedDecision ? (
            <AuthorizationPanel
              decision={selectedDecision}
              notes={decisionNotes}
              onNotesChange={setDecisionNotes}
              onApprove={() => setShowApprovalModal(true)}
              onReject={() => setShowRejectionModal(true)}
              onEscalate={handleEscalate}
              isSubmitting={isSubmitting}
            />
          ) : (
            <div className={styles.authPanelEmpty}>
              <div className={styles.authPanelEmptyIcon}>🔐</div>
              <p className={styles.authPanelEmptyText}>Authorization Required</p>
              <p className={styles.authPanelEmptySubtext}>Select a decision to authorize</p>
            </div>
          )}
        </aside>
      </main>

      {/* Approval Confirmation Modal */}
      {showApprovalModal && selectedDecision && (
        <ApprovalModal
          decision={selectedDecision}
          notes={decisionNotes}
          onConfirm={handleApprove}
          onCancel={() => setShowApprovalModal(false)}
          isSubmitting={isSubmitting}
        />
      )}

      {/* Rejection Modal */}
      {showRejectionModal && selectedDecision && (
        <RejectionModal
          decision={selectedDecision}
          reason={rejectionReason}
          onReasonChange={setRejectionReason}
          onConfirm={handleReject}
          onCancel={() => {
            setShowRejectionModal(false);
            setRejectionReason('');
          }}
          isSubmitting={isSubmitting}
        />
      )}
    </div>
  );
};

/**
 * Decision Card Component - Queue item
 */
const DecisionCard = ({ decision, isSelected, onClick }) => {
  const priorityConfig = PRIORITY_CONFIG[decision.priority?.toUpperCase()] || PRIORITY_CONFIG.MEDIUM;
  const age = calculateAge(decision.created_at);

  return (
    <div
      className={`${styles.decisionCard} ${isSelected ? styles.decisionCardSelected : ''}`}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}
      role="button"
      tabIndex={0}
      style={{ borderLeftColor: priorityConfig.color }}
    >
      <div className={styles.cardHeader}>
        <span className={styles.cardPriority} style={{ color: priorityConfig.color }}>
          {priorityConfig.icon} {priorityConfig.label}
        </span>
        <span className={styles.cardAge}>{age}</span>
      </div>

      <div className={styles.cardBody}>
        <div className={styles.cardTitle}>
          {decision.incident_id || decision.analysis_id}
        </div>
        <div className={styles.cardThreat}>
          {decision.threat_level} - {decision.attributed_actor || 'Unknown Actor'}
        </div>
        <div className={styles.cardSource}>
          {decision.source_ip}
        </div>
      </div>

      <div className={styles.cardFooter}>
        <span className={styles.cardActions}>
          {decision.recommended_actions?.length || 0} actions
        </span>
        <span className={styles.cardConfidence}>
          {decision.confidence ? `${decision.confidence.toFixed(1)}% confidence` : '—'}
        </span>
      </div>
    </div>
  );
};

/**
 * Decision Details Component - Center panel
 */
const DecisionDetails = ({ decision }) => {
  return (
    <div className={styles.details}>
      <div className={styles.detailsHeader}>
        <h2 className={styles.detailsTitle}>THREAT ANALYSIS</h2>
        <span className={styles.detailsId}>{decision.analysis_id}</span>
      </div>

      {/* Threat Overview */}
      <section className={styles.detailsSection}>
        <h3 className={styles.sectionTitle}>Threat Overview</h3>
        <div className={styles.detailsGrid}>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Incident ID:</span>
            <span className={styles.detailValue}>{decision.incident_id || '—'}</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Threat Level:</span>
            <span className={`${styles.detailValue} ${styles.detailThreat}`}>
              {decision.threat_level}
            </span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Source IP:</span>
            <span className={styles.detailValue}>{decision.source_ip}</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Attribution:</span>
            <span className={styles.detailValue}>
              {decision.attributed_actor || 'Unknown'}
              {decision.confidence && ` (${decision.confidence.toFixed(1)}%)`}
            </span>
          </div>
        </div>
      </section>

      {/* IOCs */}
      {decision.iocs && decision.iocs.length > 0 && (
        <section className={styles.detailsSection}>
          <h3 className={styles.sectionTitle}>Indicators of Compromise (IOCs)</h3>
          <div className={styles.iocList}>
            {decision.iocs.map((ioc, idx) => (
              <div key={idx} className={styles.iocItem}>
                <code className={styles.iocCode}>{ioc}</code>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* TTPs */}
      {decision.ttps && decision.ttps.length > 0 && (
        <section className={styles.detailsSection}>
          <h3 className={styles.sectionTitle}>Tactics, Techniques & Procedures (MITRE ATT&CK)</h3>
          <div className={styles.ttpList}>
            {decision.ttps.map((ttp, idx) => (
              <div key={idx} className={styles.ttpItem}>
                <span className={styles.ttpCode}>{ttp}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recommended Actions */}
      {decision.recommended_actions && decision.recommended_actions.length > 0 && (
        <section className={styles.detailsSection}>
          <h3 className={styles.sectionTitle}>Recommended Actions</h3>
          <div className={styles.actionsList}>
            {decision.recommended_actions.map((action, idx) => (
              <div key={idx} className={styles.actionItem}>
                {action}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Forensic Summary */}
      {decision.forensic_summary && (
        <section className={styles.detailsSection}>
          <h3 className={styles.sectionTitle}>Forensic Summary</h3>
          <div className={styles.forensicSummary}>
            {decision.forensic_summary}
          </div>
        </section>
      )}
    </div>
  );
};

/**
 * Authorization Panel Component - Right panel
 */
const AuthorizationPanel = ({
  decision: _decision,
  notes,
  onNotesChange,
  onApprove,
  onReject,
  onEscalate,
  isSubmitting
}) => {
  return (
    <div className={styles.authContent}>
      <div className={styles.authHeader}>
        <h2 className={styles.authTitle}>AUTHORIZATION</h2>
        <span className={styles.authSubtitle}>Executive Decision Required</span>
      </div>

      {/* Notes */}
      <div className={styles.authNotes}>
        <label htmlFor="decision-notes-textarea" className={styles.notesLabel}>Decision Notes (Optional):</label>
        <textarea
          id="decision-notes-textarea"
          className={styles.notesTextarea}
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          placeholder="Add context for audit trail..."
          rows={4}
          disabled={isSubmitting}
        />
      </div>

      {/* Action Buttons */}
      <div className={styles.authActions}>
        <button
          className={`${styles.authButton} ${styles.authButtonApprove}`}
          onClick={onApprove}
          disabled={isSubmitting}
        >
          <span className={styles.buttonIcon}>✓</span>
          <span className={styles.buttonText}>APPROVE</span>
        </button>

        <button
          className={`${styles.authButton} ${styles.authButtonReject}`}
          onClick={onReject}
          disabled={isSubmitting}
        >
          <span className={styles.buttonIcon}>✗</span>
          <span className={styles.buttonText}>REJECT</span>
        </button>

        <button
          className={`${styles.authButton} ${styles.authButtonEscalate}`}
          onClick={onEscalate}
          disabled={isSubmitting}
        >
          <span className={styles.buttonIcon}>⬆️</span>
          <span className={styles.buttonText}>ESCALATE</span>
        </button>
      </div>

      {/* Warning */}
      <div className={styles.authWarning}>
        <div className={styles.warningIcon}>⚠️</div>
        <p className={styles.warningText}>
          This decision will trigger automated response actions in production systems.
          All actions are logged and audited.
        </p>
      </div>
    </div>
  );
};

/**
 * Approval Confirmation Modal
 */
const ApprovalModal = ({ decision, notes, onConfirm, onCancel, isSubmitting }) => {
  return (
    <div
      className={styles.modalOverlay}
      onClick={onCancel}
      onKeyDown={(e) => { if (e.key === 'Escape') onCancel(); }}
      role="presentation"
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
      >
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>⚠️ CONFIRM APPROVAL</h2>
        </div>

        <div className={styles.modalBody}>
          <p className={styles.modalText}>
            You are about to <strong>APPROVE</strong> the following response actions:
          </p>

          <div className={styles.modalActionsList}>
            {decision.recommended_actions?.map((action, idx) => (
              <div key={idx} className={styles.modalActionItem}>
                ✓ {action}
              </div>
            ))}
          </div>

          <p className={styles.modalWarning}>
            These actions will execute <strong>immediately</strong> and affect production systems.
          </p>

          {notes && (
            <div className={styles.modalNotes}>
              <strong>Notes:</strong> {notes}
            </div>
          )}
        </div>

        <div className={styles.modalFooter}>
          <button
            className={`${styles.modalButton} ${styles.modalButtonCancel}`}
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            className={`${styles.modalButton} ${styles.modalButtonConfirm}`}
            onClick={onConfirm}
            disabled={isSubmitting}
          >
            {isSubmitting ? '⏳ Approving...' : '✓ CONFIRM APPROVAL'}
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Rejection Modal
 */
const RejectionModal = ({ decision: _decision, reason, onReasonChange, onConfirm, onCancel, isSubmitting }) => {
  return (
    <div
      className={styles.modalOverlay}
      onClick={onCancel}
      onKeyDown={(e) => { if (e.key === 'Escape') onCancel(); }}
      role="presentation"
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
      >
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>✗ REJECT DECISION</h2>
        </div>

        <div className={styles.modalBody}>
          <p className={styles.modalText}>
            Please provide a reason for rejecting this decision (required for audit trail):
          </p>

          <textarea
            className={styles.modalTextarea}
            value={reason}
            onChange={(e) => onReasonChange(e.target.value)}
            placeholder="Reason for rejection (e.g., 'False positive', 'Insufficient evidence', 'Alternative approach preferred')..."
            rows={4}
            // eslint-disable-next-line jsx-a11y/no-autofocus
            autoFocus
            disabled={isSubmitting}
          />

          <p className={styles.modalWarning}>
            Rejection will <strong>prevent all automated actions</strong> and require manual investigation.
          </p>
        </div>

        <div className={styles.modalFooter}>
          <button
            className={`${styles.modalButton} ${styles.modalButtonCancel}`}
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            className={`${styles.modalButton} ${styles.modalButtonConfirm} ${styles.modalButtonReject}`}
            onClick={onConfirm}
            disabled={!reason.trim() || isSubmitting}
          >
            {isSubmitting ? '⏳ Rejecting...' : '✗ CONFIRM REJECTION'}
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Utility: Calculate age in human-readable format
 */
function calculateAge(timestamp) {
  if (!timestamp) return '—';

  const now = new Date();
  const created = new Date(timestamp);
  const diffMs = now - created;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default HITLDecisionConsole;

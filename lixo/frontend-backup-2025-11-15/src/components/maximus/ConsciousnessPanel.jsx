/**
import logger from '@/utils/logger';
 * ═══════════════════════════════════════════════════════════════════════════
 * CONSCIOUSNESS MONITORING PANEL - Real-time Artificial Consciousness
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Painel de monitoramento em tempo real do sistema de consciência artificial.
 * Features:
 * - ESGT (Emergent Synchronous Global Thalamocortical) event stream
 * - Arousal level monitoring (MCEA)
 * - TIG (Thalamocortical Information Gateway) topology metrics
 * - Manual consciousness control
 *
 * Design Philosophy: Consciousness as Observable Phenomenon
 * Stream via API Gateway (`/stream/consciousness/{sse,ws}`)
 * REGRA: NO MOCK, NO PLACEHOLDER - Dados REAIS via WebSocket + API
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import {
  getConsciousnessState,
  getESGTEvents,
  getArousalState,
  getConsciousnessMetrics,
  triggerESGT,
  adjustArousal,
  formatArousalLevel,
  formatEventTime
} from '../../api/consciousness';
import { SafetyMonitorWidget } from './widgets/SafetyMonitorWidget';
import { useConsciousnessStream } from '../../hooks/useConsciousnessStream';
import './ConsciousnessPanel.css';

export const ConsciousnessPanel = ({ aiStatus, setAiStatus }) => {
  // ═══════════════════════════════════════════════════════════════════════
  // STATE - Consciousness Data
  // ═══════════════════════════════════════════════════════════════════════
  const [consciousnessState, setConsciousnessState] = useState(null);
  const [esgtEvents, setESGTEvents] = useState([]);
  const [arousalState, setArousalState] = useState(null);
  const [tigMetrics, setTigMetrics] = useState({});
  const [_esgtMetrics, setESGTMetrics] = useState({});

  // ═══════════════════════════════════════════════════════════════════════
  // STATE - UI Controls
  // ═══════════════════════════════════════════════════════════════════════
  const [selectedView, setSelectedView] = useState('overview'); // overview, events, control
  const [isLoading, setIsLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState({ connected: false, type: 'idle' });
  const [lastUpdate, setLastUpdate] = useState(null);

  // ═══════════════════════════════════════════════════════════════════════
  // STATE - Manual Controls
  // ═══════════════════════════════════════════════════════════════════════
  const [novelty, setNovelty] = useState(0.75);
  const [relevance, setRelevance] = useState(0.80);
  const [urgency, setUrgency] = useState(0.70);
  const [arousalDelta, setArousalDelta] = useState(0.0);
  const [arousalDuration, setArousalDuration] = useState(5.0);
  const [triggerResult, setTriggerResult] = useState(null);

  const eventsEndRef = useRef(null);

  // ═══════════════════════════════════════════════════════════════════════
  // WEBSOCKET CONNECTION
  // ═══════════════════════════════════════════════════════════════════════

  const handleStreamMessage = useCallback((message) => {
    setLastUpdate(new Date());

    switch (message.type) {
      case 'initial_state':
        logger.debug('🧠 Initial consciousness state received:', message);
        break;

      case 'esgt_event':
        logger.debug('⚡ ESGT event received:', message.event);
        addNewEvent(message.event);
        break;

      case 'arousal_change':
        logger.debug('🌅 Arousal change received:', message);
        setArousalState(prev => ({
          ...prev,
          arousal: message.arousal,
          level: message.level
        }));
        break;

      case 'heartbeat':
        // Keepalive OK
        break;

      case 'pong':
        // Ping response OK
        break;

      default:
        logger.debug('📨 Unknown stream message:', message);
    }
  }, []);

  const handleStreamError = useCallback((error) => {
    logger.error('❌ Consciousness stream error:', error);
  }, []);

  const { connectionType, isConnected } = useConsciousnessStream({
    enabled: true,
    onMessage: handleStreamMessage,
    onError: handleStreamError
  });

  useEffect(() => {
    setStreamStatus({ connected: !!isConnected && connectionType !== 'idle', type: connectionType });
  }, [connectionType, isConnected]);

  const addNewEvent = (event) => {
    setESGTEvents(prev => {
      const newEvents = [event, ...prev];
      return newEvents.slice(0, 100); // Keep last 100 events
    });

    // Auto-scroll to new event
    setTimeout(() => {
      eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // ═══════════════════════════════════════════════════════════════════════
  // INITIALIZATION & DATA LOADING
  // ═══════════════════════════════════════════════════════════════════════

  useEffect(() => {
    loadInitialData();
    // Polling de backup (caso stream falhe)
    const interval = setInterval(() => {
      if (!isConnected) {
        loadInitialData();
      }
    }, 5000);

    return () => {
      clearInterval(interval);
    };
  }, [isConnected]);

  const loadInitialData = async () => {
    setIsLoading(true);

    const [state, events, arousal, metrics] = await Promise.all([
      getConsciousnessState(),
      getESGTEvents(20),
      getArousalState(),
      getConsciousnessMetrics()
    ]);

    if (state && !state.error) {
      setConsciousnessState(state);
    }

    if (events && Array.isArray(events)) {
      setESGTEvents(events);
    }

    if (arousal && !arousal.error) {
      setArousalState(arousal);
    }

    if (metrics && !metrics.error) {
      setTigMetrics(metrics.tig || {});
      setESGTMetrics(metrics.esgt || {});
    }

    setIsLoading(false);
    setLastUpdate(new Date());
  };

  // ═══════════════════════════════════════════════════════════════════════
  // MANUAL CONTROLS - Actions
  // ═══════════════════════════════════════════════════════════════════════

  const handleTriggerESGT = async () => {
    setTriggerResult({ loading: true });

    const result = await triggerESGT({
      novelty,
      relevance,
      urgency,
      context: { source: 'manual_dashboard_trigger' }
    });

    setTriggerResult(result);

    // Refresh events list
    setTimeout(() => {
      loadInitialData();
    }, 500);
  };

  const handleAdjustArousal = async () => {
    const result = await adjustArousal(arousalDelta, arousalDuration, 'dashboard_manual');

    if (result && !result.error) {
      // Update will come via WebSocket
      logger.debug('✅ Arousal adjustment requested:', result);
    } else {
      logger.error('❌ Arousal adjustment failed:', result);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // RENDER HELPERS
  // ═══════════════════════════════════════════════════════════════════════

  const renderHeader = () => {
    const arousalInfo = formatArousalLevel(arousalState?.level || 'UNKNOWN');

    return (
      <div className="consciousness-header">
        <div className="header-left">
          <h2 className="consciousness-title">
            🧠 Consciousness Monitor
            <span className={`status-dot ${streamStatus.connected ? 'connected' : 'disconnected'}`}></span>
          </h2>
          <p className="consciousness-subtitle">
            Real-time artificial consciousness state
            {lastUpdate && <span className="last-update"> • Updated {formatEventTime(lastUpdate.toISOString())}</span>}
          </p>
        </div>

        <div className="header-right">
          <div className={`arousal-badge ${arousalInfo.borderClass}`}>
            <span className="arousal-emoji">{arousalInfo.emoji}</span>
            <div className="arousal-info">
              <div className="arousal-label">{arousalInfo.label}</div>
              <div className="arousal-value">{(arousalState?.arousal || 0).toFixed(2)}</div>
            </div>
          </div>

          {consciousnessState && (
            <div className="system-health">
              <span className={`health-indicator ${consciousnessState.system_health?.toLowerCase()}`}>
                {consciousnessState.system_health}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderTabs = () => {
    const tabs = [
      { id: 'overview', label: 'Overview', icon: '📊' },
      { id: 'events', label: 'ESGT Events', icon: '⚡' },
      { id: 'control', label: 'Control Panel', icon: '🎛️' },
      { id: 'safety', label: 'Safety Protocol', icon: '🛡️' }
    ];

    return (
      <div className="consciousness-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${selectedView === tab.id ? 'active' : ''}`}
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
          {/* Arousal Gauge */}
          <div className="overview-card arousal-card">
            <h3>🌅 Arousal Level (MCEA)</h3>
            <div className="arousal-gauge-container">
              <ResponsiveContainer width="100%" height={200}>
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius="60%"
                  outerRadius="90%"
                  barSize={20}
                  data={[{
                    name: 'Arousal',
                    value: (arousalState?.arousal || 0) * 100,
                    fill: formatArousalLevel(arousalState?.level).color
                  }]}
                  startAngle={180}
                  endAngle={0}
                >
                  <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                  <RadialBar dataKey="value" cornerRadius={10} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="gauge-center-label">
                <div className="gauge-value">{(arousalState?.arousal || 0).toFixed(2)}</div>
                <div className="gauge-label">{formatArousalLevel(arousalState?.level).label}</div>
              </div>
            </div>
            <div className="arousal-breakdown">
              <div className="breakdown-item">
                <span className="breakdown-label">Baseline:</span>
                <span className="breakdown-value">{(arousalState?.baseline || 0).toFixed(2)}</span>
              </div>
              <div className="breakdown-item">
                <span className="breakdown-label">Needs:</span>
                <span className="breakdown-value">+{(arousalState?.need_contribution || 0).toFixed(2)}</span>
              </div>
              <div className="breakdown-item">
                <span className="breakdown-label">Stress:</span>
                <span className="breakdown-value">+{(arousalState?.stress_contribution || 0).toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* TIG Fabric Metrics */}
          <div className="overview-card tig-card">
            <h3>🕸️ TIG Fabric Topology</h3>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-label">Nodes</div>
                <div className="metric-value">{tigMetrics.node_count || 0}</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">ECI</div>
                <div className="metric-value">{tigMetrics.eci?.toFixed(3) || 'N/A'}</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Clustering</div>
                <div className="metric-value">{tigMetrics.clustering?.toFixed(3) || 'N/A'}</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Path Length</div>
                <div className="metric-value">{tigMetrics.path_length?.toFixed(2) || 'N/A'}</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Connectivity</div>
                <div className="metric-value">{tigMetrics.algebraic_connectivity?.toFixed(3) || 'N/A'}</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Density</div>
                <div className="metric-value">{tigMetrics.density?.toFixed(3) || 'N/A'}</div>
              </div>
            </div>
            <div className="topology-visual">
              <div className="hexagon-grid">
                {Array.from({ length: 25 }).map((_, i) => (
                  <div
                    key={i}
                    className="hexagon"
                    style={{
                      animationDelay: `${i * 0.05}s`,
                      opacity: 0.3 + (tigMetrics.density || 0.25)
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* ESGT Statistics */}
          <div className="overview-card esgt-stats-card">
            <h3>⚡ ESGT Statistics</h3>
            <div className="stats-list">
              <div className="stat-row">
                <span className="stat-label">Total Events:</span>
                <span className="stat-value">{esgtEvents.length}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Success Rate:</span>
                <span className="stat-value success">
                  {esgtEvents.length > 0
                    ? `${((esgtEvents.filter(e => e.success).length / esgtEvents.length) * 100).toFixed(1)}%`
                    : 'N/A'}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Avg Coherence:</span>
                <span className="stat-value">
                  {esgtEvents.length > 0 && esgtEvents.some(e => e.coherence !== null && e.coherence !== undefined)
                    ? esgtEvents.filter(e => e.coherence !== null && e.coherence !== undefined)
                        .reduce((sum, e) => sum + e.coherence, 0) / esgtEvents.filter(e => e.coherence !== null && e.coherence !== undefined).length
                        .toFixed(3)
                    : 'N/A'}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Avg Duration:</span>
                <span className="stat-value">
                  {esgtEvents.length > 0 && esgtEvents.some(e => e.duration_ms !== null && e.duration_ms !== undefined)
                    ? `${(esgtEvents.filter(e => e.duration_ms !== null && e.duration_ms !== undefined)
                        .reduce((sum, e) => sum + e.duration_ms, 0) / esgtEvents.filter(e => e.duration_ms !== null && e.duration_ms !== undefined).length).toFixed(1)} ms`
                    : 'N/A'}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">WebSocket:</span>
                <span className={`stat-value ${streamStatus.connected ? 'success' : 'error'}`}>
                  {streamStatus.connected ? `🟢 Connected (${streamStatus.type.toUpperCase()})` : '🔴 Disconnected'}
                </span>
              </div>
            </div>
          </div>

          {/* Recent Event */}
          {esgtEvents.length > 0 && (
            <div className="overview-card recent-event-card">
              <h3>🕐 Latest ESGT Event</h3>
              {renderEventCard(esgtEvents[0], true)}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderEvents = () => {
    return (
      <div className="events-section">
        <div className="events-header">
          <h3>⚡ ESGT Ignition Events Timeline</h3>
          <div className="events-stats">
            <span className="events-count">{esgtEvents.length} events</span>
            <span className="events-success">
              {esgtEvents.filter(e => e.success).length} successful
            </span>
          </div>
        </div>

        <div className="events-timeline">
          {esgtEvents.length === 0 ? (
            <div className="events-empty">
              <p>No ESGT events recorded yet.</p>
              <p>Use the Control Panel to trigger a manual ignition.</p>
            </div>
          ) : (
            esgtEvents.map((event, index) => (
              <div key={event.event_id || index} ref={index === 0 ? eventsEndRef : null}>
                {renderEventCard(event)}
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const renderEventCard = (event, isCompact = false) => {
    return (
      <div className={`esgt-event-card ${event.success ? 'success' : 'failed'} ${isCompact ? 'compact' : ''}`}>
        <div className="event-header">
          <span className={`event-status ${event.success ? 'success' : 'failed'}`}>
            {event.success ? '✅ SUCCESS' : '❌ FAILED'}
          </span>
          <span className="event-id">{event.event_id}</span>
          <span className="event-time">{formatEventTime(event.timestamp)}</span>
        </div>

        <div className="event-body">
          <div className="event-metrics">
            <div className="event-metric">
              <span className="metric-label">Coherence:</span>
              <span className="metric-value">
                {event.coherence !== null && event.coherence !== undefined ? event.coherence.toFixed(3) : 'N/A'}
              </span>
            </div>
            <div className="event-metric">
              <span className="metric-label">Duration:</span>
              <span className="metric-value">
                {event.duration_ms !== null && event.duration_ms !== undefined ? `${event.duration_ms.toFixed(1)} ms` : 'N/A'}
              </span>
            </div>
            <div className="event-metric">
              <span className="metric-label">Nodes:</span>
              <span className="metric-value">{event.nodes_participating || 0}</span>
            </div>
          </div>

          {!isCompact && event.salience && (
            <div className="event-salience">
              <div className="salience-bar">
                <span className="salience-label">N</span>
                <div className="salience-fill" style={{ width: `${(event.salience.novelty || 0) * 100}%` }}></div>
                <span className="salience-value">{(event.salience.novelty || 0).toFixed(2)}</span>
              </div>
              <div className="salience-bar">
                <span className="salience-label">R</span>
                <div className="salience-fill" style={{ width: `${(event.salience.relevance || 0) * 100}%` }}></div>
                <span className="salience-value">{(event.salience.relevance || 0).toFixed(2)}</span>
              </div>
              <div className="salience-bar">
                <span className="salience-label">U</span>
                <div className="salience-fill" style={{ width: `${(event.salience.urgency || 0) * 100}%` }}></div>
                <span className="salience-value">{(event.salience.urgency || 0).toFixed(2)}</span>
              </div>
            </div>
          )}

          {!event.success && event.reason && (
            <div className="event-reason">
              <strong>Reason:</strong> {event.reason}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderControl = () => {
    return (
      <div className="control-section">
        <div className="control-grid">
          {/* ESGT Manual Trigger */}
          <div className="control-card esgt-trigger-card">
            <h3>⚡ Manual ESGT Ignition</h3>
            <p className="control-description">
              Trigger a conscious access event by specifying salience components.
            </p>

            <div className="control-inputs">
              <div className="slider-group">
                <label>
                  <span className="slider-label">Novelty</span>
                  <span className="slider-value">{novelty.toFixed(2)}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={novelty}
                  onChange={(e) => setNovelty(parseFloat(e.target.value))}
                  className="slider novelty"
                />
              </div>

              <div className="slider-group">
                <label>
                  <span className="slider-label">Relevance</span>
                  <span className="slider-value">{relevance.toFixed(2)}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={relevance}
                  onChange={(e) => setRelevance(parseFloat(e.target.value))}
                  className="slider relevance"
                />
              </div>

              <div className="slider-group">
                <label>
                  <span className="slider-label">Urgency</span>
                  <span className="slider-value">{urgency.toFixed(2)}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={urgency}
                  onChange={(e) => setUrgency(parseFloat(e.target.value))}
                  className="slider urgency"
                />
              </div>
            </div>

            <button
              className="control-button trigger-button"
              onClick={handleTriggerESGT}
              disabled={triggerResult?.loading}
            >
              {triggerResult?.loading ? '⏳ Triggering...' : '⚡ Trigger ESGT Ignition'}
            </button>

            {triggerResult && !triggerResult.loading && (
              <div className={`trigger-result ${triggerResult.success ? 'success' : 'error'}`}>
                {triggerResult.success ? (
                  <>
                    <div>✅ Ignition {triggerResult.success ? 'succeeded' : 'failed'}</div>
                    <div className="result-details">
                      Event ID: {triggerResult.event_id} |
                      Coherence: {triggerResult.coherence?.toFixed(3) || 'N/A'} |
                      Duration: {triggerResult.duration_ms?.toFixed(1) || 'N/A'} ms
                    </div>
                  </>
                ) : (
                  <>
                    <div>❌ Ignition failed</div>
                    <div className="result-details">
                      Reason: {triggerResult.reason || triggerResult.error || 'Unknown'}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Arousal Adjustment */}
          <div className="control-card arousal-adjust-card">
            <h3>🌅 Arousal Modulation</h3>
            <p className="control-description">
              Adjust global excitability level (MCEA arousal controller).
            </p>

            <div className="control-inputs">
              <div className="slider-group">
                <label>
                  <span className="slider-label">Delta</span>
                  <span className="slider-value">{arousalDelta >= 0 ? '+' : ''}{arousalDelta.toFixed(2)}</span>
                </label>
                <input
                  type="range"
                  min="-0.5"
                  max="0.5"
                  step="0.05"
                  value={arousalDelta}
                  onChange={(e) => setArousalDelta(parseFloat(e.target.value))}
                  className="slider arousal-delta"
                />
              </div>

              <div className="slider-group">
                <label>
                  <span className="slider-label">Duration</span>
                  <span className="slider-value">{arousalDuration.toFixed(1)}s</span>
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="60"
                  step="0.5"
                  value={arousalDuration}
                  onChange={(e) => setArousalDuration(parseFloat(e.target.value))}
                  className="slider duration"
                />
              </div>
            </div>

            <button
              className="control-button arousal-button"
              onClick={handleAdjustArousal}
            >
              🌅 Adjust Arousal
            </button>

            <div className="arousal-preview">
              <div className="preview-label">Current:</div>
              <div className="preview-value">{(arousalState?.arousal || 0).toFixed(2)}</div>
              <div className="preview-arrow">→</div>
              <div className="preview-label">Target:</div>
              <div className="preview-value">
                {Math.max(0, Math.min(1, (arousalState?.arousal || 0) + arousalDelta)).toFixed(2)}
              </div>
            </div>
          </div>

          {/* System Information */}
          <div className="control-card info-card">
            <h3>ℹ️ System Information</h3>
            <div className="info-list">
              <div className="info-item">
                <span className="info-label">ESGT Active:</span>
                <span className={`info-value ${consciousnessState?.esgt_active ? 'active' : 'inactive'}`}>
                  {consciousnessState?.esgt_active ? '🟢 Yes' : '🔴 No'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Total Events:</span>
                <span className="info-value">{consciousnessState?.recent_events_count || 0}</span>
              </div>
              <div className="info-item">
                <span className="info-label">System Health:</span>
                <span className={`info-value ${consciousnessState?.system_health?.toLowerCase()}`}>
                  {consciousnessState?.system_health || 'Unknown'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">WebSocket:</span>
                <span className={`info-value ${streamStatus.connected ? 'success' : 'error'}`}>
                  {streamStatus.connected ? `🟢 Connected (${streamStatus.type.toUpperCase()})` : '🔴 Disconnected'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Last Update:</span>
                <span className="info-value">
                  {lastUpdate ? formatEventTime(lastUpdate.toISOString()) : 'Never'}
                </span>
              </div>
            </div>

            <button className="control-button refresh-button" onClick={loadInitialData}>
              🔄 Refresh Data
            </button>
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
      <div className="consciousness-panel loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading consciousness system...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="consciousness-panel">
      {renderHeader()}
      {renderTabs()}

      <div className="consciousness-content">
        {selectedView === 'overview' && renderOverview()}
        {selectedView === 'events' && renderEvents()}
        {selectedView === 'control' && renderControl()}
        {selectedView === 'safety' && <SafetyMonitorWidget systemHealth={consciousnessState?.system_health} />}
      </div>
    </div>
  );
};

export default ConsciousnessPanel;

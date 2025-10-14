/**
import logger from '@/utils/logger';
 * ═══════════════════════════════════════════════════════════════════════════
 * NEUROMODULATION WIDGET - Digital Neurotransmitters
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza os 4 neuromoduladores digitais:
 * - DOPAMINA: Reward Prediction Error → Learning Rate
 * - SEROTONINA: Exploration vs Exploitation → Epsilon
 * - ACETILCOLINA: Attention Gain → Novelty Response
 * - NORADRENALINA: Urgency → Temperature Control
 */

import React, { useState, useEffect } from 'react';
import './NeuromodulationWidget.css';

export const NeuromodulationWidget = ({ systemHealth: _systemHealth }) => {
  const [modulators, setModulators] = useState({
    dopamine: { current_value: 0.001, baseline: 0.001, min_value: 0.0001, max_value: 0.01, update_count: 0 },
    serotonin: { current_value: 0.1, baseline: 0.1, min_value: 0.01, max_value: 0.5, update_count: 0 },
    acetylcholine: { current_value: 1.0, baseline: 1.0, min_value: 0.5, max_value: 3.0, update_count: 0 },
    noradrenaline: { current_value: 1.0, baseline: 1.0, min_value: 0.1, max_value: 2.0, update_count: 0 }
  });
  const [systemState, setSystemState] = useState('BALANCED');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch neuromodulation stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8001/stats');
        if (response.ok) {
          const data = await response.json();
          setModulators({
            dopamine: data.dopamine,
            serotonin: data.serotonin,
            acetylcholine: data.acetylcholine,
            noradrenaline: data.noradrenaline
          });
          setSystemState(data.system_state);
          setLoading(false);
        }
      } catch (error) {
        logger.error('Failed to fetch neuromodulation stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Every 5s
    return () => clearInterval(interval);
  }, []);

  // Fetch history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('http://localhost:8001/history?limit=50');
        if (response.ok) {
          const data = await response.json();
          setHistory(data.records || []);
        }
      } catch (error) {
        logger.error('Failed to fetch history:', error);
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 10000); // Every 10s
    return () => clearInterval(interval);
  }, []);

  const getModulatorPercentage = (modulator) => {
    const { current_value, min_value, max_value } = modulator;
    return ((current_value - min_value) / (max_value - min_value)) * 100;
  };

  const getModulatorColor = (percentage) => {
    if (percentage < 30) return '#f97316'; // Orange - Low
    if (percentage < 70) return '#10b981'; // Green - Normal
    return '#ef4444'; // Red - High
  };

  const resetModulator = async (modulatorName) => {
    try {
      const response = await fetch('http://localhost:8001/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modulator: modulatorName })
      });

      if (response.ok) {
        const data = await response.json();
        logger.debug(`Reset ${modulatorName}:`, data);
      }
    } catch (error) {
      logger.error(`Failed to reset ${modulatorName}:`, error);
    }
  };

  if (loading) {
    return (
      <div className="neuromod-loading">
        <div className="loading-spinner"></div>
        <p>Loading neuromodulatory data...</p>
      </div>
    );
  }

  return (
    <div className="neuromodulation-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <h2 className="widget-title">🧬 Neuromodulatory Control System</h2>
          <p className="widget-subtitle">Digital Neurotransmitters - Real-time Modulation</p>
        </div>
        <div className="header-right">
          <div className="system-state-badge" data-state={systemState.toLowerCase()}>
            {systemState}
          </div>
        </div>
      </div>

      {/* Modulators Grid */}
      <div className="modulators-grid">
        {/* Dopamine */}
        <div className="modulator-card dopamine-card">
          <div className="modulator-header">
            <div className="modulator-icon">💊</div>
            <div className="modulator-info">
              <h3 className="modulator-name">DOPAMINA</h3>
              <p className="modulator-role">Learning Rate Control</p>
            </div>
          </div>

          <div className="modulator-value">
            <span className="value-current">{modulators.dopamine.current_value.toFixed(4)}</span>
            <span className="value-unit">α (learning rate)</span>
          </div>

          <div className="modulator-bar">
            <div
              className="bar-fill"
              style={{
                width: `${getModulatorPercentage(modulators.dopamine)}%`,
                backgroundColor: getModulatorColor(getModulatorPercentage(modulators.dopamine))
              }}
            ></div>
          </div>

          <div className="modulator-stats">
            <div className="stat-item">
              <span className="stat-label">Baseline:</span>
              <span className="stat-value">{modulators.dopamine.baseline.toFixed(4)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Range:</span>
              <span className="stat-value">
                {modulators.dopamine.min_value.toFixed(4)} - {modulators.dopamine.max_value.toFixed(4)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Updates:</span>
              <span className="stat-value">{modulators.dopamine.update_count}</span>
            </div>
          </div>

          <button onClick={() => resetModulator('dopamine')} className="btn-reset">
            Reset to Baseline
          </button>
        </div>

        {/* Serotonin */}
        <div className="modulator-card serotonin-card">
          <div className="modulator-header">
            <div className="modulator-icon">🔵</div>
            <div className="modulator-info">
              <h3 className="modulator-name">SEROTONINA</h3>
              <p className="modulator-role">Exploration Control</p>
            </div>
          </div>

          <div className="modulator-value">
            <span className="value-current">{modulators.serotonin.current_value.toFixed(3)}</span>
            <span className="value-unit">ε (exploration rate)</span>
          </div>

          <div className="modulator-bar">
            <div
              className="bar-fill"
              style={{
                width: `${getModulatorPercentage(modulators.serotonin)}%`,
                backgroundColor: getModulatorColor(getModulatorPercentage(modulators.serotonin))
              }}
            ></div>
          </div>

          <div className="modulator-stats">
            <div className="stat-item">
              <span className="stat-label">Baseline:</span>
              <span className="stat-value">{modulators.serotonin.baseline.toFixed(3)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Range:</span>
              <span className="stat-value">
                {modulators.serotonin.min_value.toFixed(3)} - {modulators.serotonin.max_value.toFixed(3)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Updates:</span>
              <span className="stat-value">{modulators.serotonin.update_count}</span>
            </div>
          </div>

          <button onClick={() => resetModulator('serotonin')} className="btn-reset">
            Reset to Baseline
          </button>
        </div>

        {/* Acetylcholine */}
        <div className="modulator-card acetylcholine-card">
          <div className="modulator-header">
            <div className="modulator-icon">👁️</div>
            <div className="modulator-info">
              <h3 className="modulator-name">ACETILCOLINA</h3>
              <p className="modulator-role">Attention Gain</p>
            </div>
          </div>

          <div className="modulator-value">
            <span className="value-current">{modulators.acetylcholine.current_value.toFixed(2)}</span>
            <span className="value-unit">gain (attention)</span>
          </div>

          <div className="modulator-bar">
            <div
              className="bar-fill"
              style={{
                width: `${getModulatorPercentage(modulators.acetylcholine)}%`,
                backgroundColor: getModulatorColor(getModulatorPercentage(modulators.acetylcholine))
              }}
            ></div>
          </div>

          <div className="modulator-stats">
            <div className="stat-item">
              <span className="stat-label">Baseline:</span>
              <span className="stat-value">{modulators.acetylcholine.baseline.toFixed(2)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Range:</span>
              <span className="stat-value">
                {modulators.acetylcholine.min_value.toFixed(2)} - {modulators.acetylcholine.max_value.toFixed(2)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Updates:</span>
              <span className="stat-value">{modulators.acetylcholine.update_count}</span>
            </div>
          </div>

          <button onClick={() => resetModulator('acetylcholine')} className="btn-reset">
            Reset to Baseline
          </button>
        </div>

        {/* Noradrenaline */}
        <div className="modulator-card noradrenaline-card">
          <div className="modulator-header">
            <div className="modulator-icon">⚡</div>
            <div className="modulator-info">
              <h3 className="modulator-name">NORADRENALINA</h3>
              <p className="modulator-role">Urgency / Temperature</p>
            </div>
          </div>

          <div className="modulator-value">
            <span className="value-current">{modulators.noradrenaline.current_value.toFixed(2)}</span>
            <span className="value-unit">τ (temperature)</span>
          </div>

          <div className="modulator-bar">
            <div
              className="bar-fill"
              style={{
                width: `${getModulatorPercentage(modulators.noradrenaline)}%`,
                backgroundColor: getModulatorColor(getModulatorPercentage(modulators.noradrenaline))
              }}
            ></div>
          </div>

          <div className="modulator-stats">
            <div className="stat-item">
              <span className="stat-label">Baseline:</span>
              <span className="stat-value">{modulators.noradrenaline.baseline.toFixed(2)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Range:</span>
              <span className="stat-value">
                {modulators.noradrenaline.min_value.toFixed(2)} - {modulators.noradrenaline.max_value.toFixed(2)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Updates:</span>
              <span className="stat-value">{modulators.noradrenaline.update_count}</span>
            </div>
          </div>

          <button onClick={() => resetModulator('noradrenaline')} className="btn-reset">
            Reset to Baseline
          </button>
        </div>
      </div>

      {/* Modulation History Chart */}
      <div className="modulation-history">
        <h3 className="history-title">📊 Modulation History (Last 50 Updates)</h3>
        <div className="history-chart">
          {history.length > 0 ? (
            <div className="chart-container">
              <div className="chart-legend">
                <span className="legend-item legend-dopamine">Learning Rate</span>
                <span className="legend-item legend-serotonin">Exploration Rate</span>
                <span className="legend-item legend-acetylcholine">Attention Gain</span>
                <span className="legend-item legend-noradrenaline">Temperature</span>
              </div>
              <div className="chart-grid">
                {history.slice(-20).map((record, idx) => (
                  <div key={idx} className="chart-bar-group">
                    <div
                      className="chart-bar bar-dopamine"
                      style={{
                        height: `${(record.learning_rate / 0.01) * 100}%`,
                        minHeight: '2px'
                      }}
                      title={`LR: ${record.learning_rate.toFixed(4)}`}
                    ></div>
                    <div
                      className="chart-bar bar-serotonin"
                      style={{
                        height: `${(record.exploration_rate / 0.5) * 100}%`,
                        minHeight: '2px'
                      }}
                      title={`ε: ${record.exploration_rate.toFixed(3)}`}
                    ></div>
                    <div
                      className="chart-bar bar-acetylcholine"
                      style={{
                        height: `${(record.attention_gain / 3.0) * 100}%`,
                        minHeight: '2px'
                      }}
                      title={`Gain: ${record.attention_gain.toFixed(2)}`}
                    ></div>
                    <div
                      className="chart-bar bar-noradrenaline"
                      style={{
                        height: `${(record.temperature / 2.0) * 100}%`,
                        minHeight: '2px'
                      }}
                      title={`τ: ${record.temperature.toFixed(2)}`}
                    ></div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="chart-empty">
              <p>⏳ No modulation history available yet...</p>
            </div>
          )}
        </div>
      </div>

      {/* Biological Inspiration */}
      <div className="bio-inspiration">
        <h3 className="bio-title">🧠 Biological Inspiration</h3>
        <div className="bio-grid">
          <div className="bio-card">
            <strong>Dopamina (VTA):</strong> Ventral Tegmental Area - Reward Prediction Error signals modulate synaptic plasticity
          </div>
          <div className="bio-card">
            <strong>Serotonina (DRN):</strong> Dorsal Raphe Nucleus - Balances exploration vs exploitation behavior
          </div>
          <div className="bio-card">
            <strong>Acetilcolina (NBM):</strong> Nucleus Basalis of Meynert - Attention and novelty-driven learning
          </div>
          <div className="bio-card">
            <strong>Noradrenalina (LC):</strong> Locus Coeruleus - Arousal, urgency, and threat response
          </div>
        </div>
      </div>
    </div>
  );
};

export default NeuromodulationWidget;

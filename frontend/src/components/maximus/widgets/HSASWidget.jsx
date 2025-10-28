import { API_ENDPOINTS } from '@/config/api';
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * HSAS WIDGET - Hybrid Skill Acquisition System
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza o sistema híbrido de aprendizado:
 * - SKILLS ADQUIRIDAS: Model-free + Model-based
 * - SKILL PRIMITIVES: Building blocks de ações
 * - LEARNING STATISTICS: Arbitragem híbrida
 * - IMITATION LEARNING: Aprendizado por demonstração
 */

import logger from '@/utils/logger';
import React, { useState, useEffect } from 'react';
import './HSASWidget.css';

export const HSASWidget = ({ systemHealth: _systemHealth }) => {
  const [learningMode, setLearningMode] = useState('hybrid');
  const [skills, setSkills] = useState([]);
  const [primitives, setPrimitives] = useState([]);
  const [learningStats, setLearningStats] = useState({
    total_transitions: 0,
    model_free_usage_count: 0,
    model_based_usage_count: 0,
    imitation_demonstrations: 0,
    average_reward: 0,
    success_rate: 0,
    exploration_rate: 0
  });
  const [loading, setLoading] = useState(true);

  // Fetch skills
  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.skills);
        if (response.ok) {
          const data = await response.json();
          setSkills(data.skills || []);
        }
      } catch (error) {
        logger.error('Failed to fetch skills:', error);
      }
    };

    fetchSkills();
    const interval = setInterval(fetchSkills, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch primitives
  useEffect(() => {
    const fetchPrimitives = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.primitives);
        if (response.ok) {
          const data = await response.json();
          setPrimitives(data.primitives || []);
        }
      } catch (error) {
        logger.error('Failed to fetch primitives:', error);
      }
    };

    fetchPrimitives();
    const interval = setInterval(fetchPrimitives, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch learning stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.stats);
        if (response.ok) {
          const data = await response.json();
          setLearningStats(data);
          setLearningMode(data.learning_mode);
          setLoading(false);
        }
      } catch (error) {
        logger.error('Failed to fetch learning stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const changeLearningMode = async (mode) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.mode}?mode=${mode}`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        logger.debug('Mode changed:', data);
        setLearningMode(data.new_mode);
      }
    } catch (error) {
      logger.error('Failed to change mode:', error);
    }
  };

  if (loading) {
    return (
      <div className="hsas-loading">
        <div className="loading-spinner"></div>
        <p>Loading HSAS data...</p>
      </div>
    );
  }

  const totalUsage = learningStats.model_free_usage_count + learningStats.model_based_usage_count;
  const modelFreePercentage = totalUsage > 0 ? (learningStats.model_free_usage_count / totalUsage) * 100 : 50;
  const modelBasedPercentage = totalUsage > 0 ? (learningStats.model_based_usage_count / totalUsage) * 100 : 50;

  return (
    <div className="hsas-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <h2 className="widget-title">🎯 Hybrid Skill Acquisition System</h2>
          <p className="widget-subtitle">Model-Free + Model-Based RL + Imitation Learning</p>
        </div>
        <div className="header-right">
          <div className="learning-mode-badge" data-mode={learningMode}>
            {learningMode.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Learning Mode Controls */}
      <div className="mode-controls">
        <button
          onClick={() => changeLearningMode('model_free')}
          className={`btn-mode ${learningMode === 'model_free' ? 'active' : ''}`}
        >
          🏃 Model-Free
          <span className="mode-desc">Fast, habitual (Basal Ganglia)</span>
        </button>
        <button
          onClick={() => changeLearningMode('model_based')}
          className={`btn-mode ${learningMode === 'model_based' ? 'active' : ''}`}
        >
          🧠 Model-Based
          <span className="mode-desc">Deliberative, planning (Cerebellum)</span>
        </button>
        <button
          onClick={() => changeLearningMode('hybrid')}
          className={`btn-mode ${learningMode === 'hybrid' ? 'active' : ''}`}
        >
          ⚡ Hybrid
          <span className="mode-desc">Automatic arbitration</span>
        </button>
        <button
          onClick={() => changeLearningMode('imitation')}
          className={`btn-mode ${learningMode === 'imitation' ? 'active' : ''}`}
        >
          👤 Imitation
          <span className="mode-desc">Learning from demonstrations</span>
        </button>
      </div>

      {/* Learning Statistics */}
      <div className="learning-stats-section">
        <h3 className="section-title">📊 Learning Statistics</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">🔄</div>
            <div className="stat-info">
              <div className="stat-value">{learningStats.total_transitions.toLocaleString()}</div>
              <div className="stat-label">Total Transitions</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⭐</div>
            <div className="stat-info">
              <div className="stat-value">{learningStats.average_reward.toFixed(2)}</div>
              <div className="stat-label">Average Reward</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-info">
              <div className="stat-value">{(learningStats.success_rate * 100).toFixed(1)}%</div>
              <div className="stat-label">Success Rate</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🔍</div>
            <div className="stat-info">
              <div className="stat-value">{(learningStats.exploration_rate * 100).toFixed(1)}%</div>
              <div className="stat-label">Exploration Rate</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">👤</div>
            <div className="stat-info">
              <div className="stat-value">{learningStats.imitation_demonstrations}</div>
              <div className="stat-label">Demonstrations</div>
            </div>
          </div>
        </div>
      </div>

      {/* Model-Free vs Model-Based Usage */}
      <div className="arbitration-section">
        <h3 className="section-title">🔀 Arbitration: Model-Free vs Model-Based</h3>
        <div className="arbitration-chart">
          <div className="arbitration-bar">
            <div
              className="bar-segment model-free-segment"
              style={{ width: `${modelFreePercentage}%` }}
            >
              <span className="segment-label">
                {modelFreePercentage > 15 ? 'Model-Free' : ''} {learningStats.model_free_usage_count}
              </span>
            </div>
            <div
              className="bar-segment model-based-segment"
              style={{ width: `${modelBasedPercentage}%` }}
            >
              <span className="segment-label">
                {modelBasedPercentage > 15 ? 'Model-Based' : ''} {learningStats.model_based_usage_count}
              </span>
            </div>
          </div>
          <div className="arbitration-legend">
            <div className="legend-item">
              <span className="legend-color model-free-color"></span>
              <span className="legend-text">Model-Free: {modelFreePercentage.toFixed(1)}% (habitual, fast)</span>
            </div>
            <div className="legend-item">
              <span className="legend-color model-based-color"></span>
              <span className="legend-text">Model-Based: {modelBasedPercentage.toFixed(1)}% (deliberative, careful)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Acquired Skills */}
      <div className="skills-section">
        <h3 className="section-title">🎯 Acquired Skills ({skills.length})</h3>
        {skills.length > 0 ? (
          <div className="skills-grid">
            {skills.slice(0, 6).map(skill => (
              <div key={skill.skill_id} className="skill-card">
                <div className="skill-header">
                  <span className="skill-type-badge">{skill.skill_type}</span>
                  <span className="skill-mode-badge">{skill.learning_mode}</span>
                </div>
                <div className="skill-body">
                  <div className="skill-id">{skill.skill_id}</div>
                  <div className="skill-stats">
                    <div className="skill-stat">
                      <span className="skill-stat-label">Success Rate:</span>
                      <span className="skill-stat-value">{(skill.success_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div className="skill-stat">
                      <span className="skill-stat-label">Executions:</span>
                      <span className="skill-stat-value">{skill.execution_count}</span>
                    </div>
                  </div>
                  {skill.last_executed && (
                    <div className="skill-last-executed">
                      Last: {new Date(skill.last_executed).toLocaleString('pt-BR')}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="skills-empty">
            <p>⏳ No skills acquired yet. Start training the system!</p>
          </div>
        )}
        {skills.length > 6 && (
          <div className="skills-footer">
            <span>+{skills.length - 6} more skills...</span>
          </div>
        )}
      </div>

      {/* Skill Primitives */}
      <div className="primitives-section">
        <h3 className="section-title">🧩 Skill Primitives ({primitives.length})</h3>
        {primitives.length > 0 ? (
          <div className="primitives-grid">
            {primitives.map(primitive => (
              <div key={primitive.primitive_id} className="primitive-card">
                <div className="primitive-header">
                  <span className="primitive-icon">🧩</span>
                  <div className="primitive-info">
                    <h4 className="primitive-name">{primitive.primitive_id}</h4>
                    <span className="primitive-type">{primitive.primitive_type}</span>
                  </div>
                </div>
                <div className="primitive-body">
                  <p className="primitive-description">{primitive.description}</p>
                  <div className="primitive-stats">
                    <div className="primitive-stat">
                      <span className="stat-icon">✅</span>
                      <span className="stat-text">{(primitive.success_rate * 100).toFixed(0)}% success</span>
                    </div>
                    <div className="primitive-stat">
                      <span className="stat-icon">🔄</span>
                      <span className="stat-text">{primitive.execution_count} executions</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="primitives-empty">
            <p>⏳ Loading skill primitives...</p>
          </div>
        )}
      </div>

      {/* Biological Inspiration */}
      <div className="bio-inspiration">
        <h3 className="bio-title">🧠 Biological Inspiration</h3>
        <div className="bio-grid">
          <div className="bio-card">
            <strong>Basal Ganglia (Model-Free):</strong> Fast, habitual responses learned through trial and error.
            Used when uncertainty is low and speed is critical.
          </div>
          <div className="bio-card">
            <strong>Cerebellum (Model-Based):</strong> Deliberative planning using internal world model.
            Used when uncertainty is high and careful planning is needed.
          </div>
          <div className="bio-card">
            <strong>Motor Cortex (Primitives):</strong> Library of basic action building blocks that can be composed
            into complex behaviors.
          </div>
          <div className="bio-card">
            <strong>Arbitration System:</strong> Prefrontal cortex decides between habitual (model-free) and
            deliberative (model-based) control based on uncertainty.
          </div>
        </div>
      </div>
    </div>
  );
};

export default HSASWidget;

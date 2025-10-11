/**
import logger from '@/utils/logger';
 * ═══════════════════════════════════════════════════════════════════════════
 * WORKFLOWS PANEL - AI-Driven Automated Workflows
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Orquestração de workflows multi-serviço guiados por AI.
 *
 * Workflows Predefinidos:
 * - Full Security Assessment
 * - OSINT Investigation
 * - Purple Team Exercise
 * - Custom Workflow Builder
 */

import React, { useState, useEffect } from 'react';
import {
  aiFullAssessment,
  aiOSINTInvestigation,
  aiPurpleTeamExercise,
  orchestrateWorkflow
} from '../../api/maximusAI';
import './WorkflowsPanel.css';

export const WorkflowsPanel = ({ aiStatus, setAiStatus }) => {
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [workflowResults, setWorkflowResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);

  // Workflow configurations
  const [target, setTarget] = useState('');
  const [workflowType, setWorkflowType] = useState('full_assessment');
  const [options, setOptions] = useState({});

  // Predefined workflows
  const workflows = [
    {
      id: 'full_assessment',
      name: 'Full Security Assessment',
      icon: '📊',
      description: 'Comprehensive security scan: Network Recon → Vuln Intel → Web Attack → Threat Intel',
      color: 'cyan',
      targetType: 'network',
      placeholder: '192.168.1.0/24'
    },
    {
      id: 'osint_investigation',
      name: 'OSINT Investigation',
      icon: '🔍',
      description: 'Deep OSINT: Breach Data → Social Media → Domain Correlation → Threat Check',
      color: 'purple',
      targetType: 'identifier',
      placeholder: 'email@example.com or domain.com'
    },
    {
      id: 'purple_team',
      name: 'Purple Team Exercise',
      icon: '⚔️',
      description: 'MITRE ATT&CK Simulation → SIEM Correlation → Coverage Analysis → Gap ID',
      color: 'orange',
      targetType: 'technique',
      placeholder: 'T1059.001'
    },
    {
      id: 'threat_hunting',
      name: 'Threat Hunting',
      icon: '🎯',
      description: 'IP Intel → Malware Analysis → Threat Correlation → IOC Extraction',
      color: 'red',
      targetType: 'ip_or_hash',
      placeholder: '8.8.8.8 or hash'
    },
    {
      id: 'web_recon',
      name: 'Web Reconnaissance',
      icon: '🌐',
      description: 'Domain Analysis → Subdomain Discovery → Web Crawling → Vuln Scan',
      color: 'green',
      targetType: 'url',
      placeholder: 'https://example.com'
    },
    {
      id: 'custom',
      name: 'Custom Workflow',
      icon: '🧬',
      description: 'Build your own multi-service workflow',
      color: 'blue',
      targetType: 'custom',
      placeholder: 'Configure steps manually'
    }
  ];

  const currentWorkflow = workflows.find(w => w.id === workflowType);

  // Execute workflow
  const executeWorkflow = async () => {
    if (!target && workflowType !== 'custom') {
      alert('Please provide a target');
      return;
    }

    setIsRunning(true);
    setActiveWorkflow({
      id: Date.now(),
      type: workflowType,
      target,
      status: 'running',
      startTime: new Date().toISOString(),
      steps: []
    });

    try {
      let result;

      switch (workflowType) {
        case 'full_assessment':
          result = await aiFullAssessment(target, options);
          break;

        case 'osint_investigation':
          result = await aiOSINTInvestigation(target, options.type || 'email');
          break;

        case 'purple_team':
          result = await aiPurpleTeamExercise(target, options.targetHost || '10.0.0.1', options.telemetrySources || []);
          break;

        case 'threat_hunting':
        case 'web_recon':
        case 'custom':
          result = await orchestrateWorkflow({
            type: workflowType,
            target,
            ...options
          });
          break;

        default:
          throw new Error('Unknown workflow type');
      }

      if (result.success) {
        const completedWorkflow = {
          id: Date.now(),
          type: workflowType,
          target,
          status: 'completed',
          startTime: activeWorkflow.startTime,
          endTime: new Date().toISOString(),
          result: result,
          steps: result.steps || []
        };

        setWorkflowResults(prev => [completedWorkflow, ...prev].slice(0, 10));
        setActiveWorkflow(null);
      } else {
        throw new Error(result.error || 'Workflow failed');
      }
    } catch (error) {
      logger.error('Workflow execution error:', error);
      setActiveWorkflow({
        ...activeWorkflow,
        status: 'failed',
        error: error.message
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="workflows-panel">
      {/* Header */}
      <div className="workflows-header">
        <div>
          <h2 className="workflows-title">🧬 AI-DRIVEN WORKFLOWS</h2>
          <p className="workflows-subtitle">Multi-Service Orchestration with Real-Time AI Guidance</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="workflows-content">
        {/* Workflow Selector */}
        <div className="workflow-selector">
          <h3 className="section-title">Select Workflow</h3>
          <div className="workflows-grid">
            {workflows.map(workflow => (
              <button
                key={workflow.id}
                className={`workflow-card workflow-${workflow.color} ${workflowType === workflow.id ? 'active' : ''}`}
                onClick={() => setWorkflowType(workflow.id)}
                disabled={isRunning}
              >
                <div className="workflow-icon">{workflow.icon}</div>
                <div className="workflow-info">
                  <div className="workflow-name">{workflow.name}</div>
                  <div className="workflow-desc">{workflow.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Configuration */}
        <div className="workflow-config">
          <h3 className="section-title">Configuration</h3>

          <div className="config-form">
            <div className="form-group">
              <label className="form-label">Target</label>
              <input
                type="text"
                className="form-input"
                placeholder={currentWorkflow?.placeholder || 'Enter target...'}
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                disabled={isRunning}
              />
              <span className="form-hint">Type: {currentWorkflow?.targetType || 'various'}</span>
            </div>

            {workflowType === 'full_assessment' && (
              <div className="form-group">
                <label className="form-label">Scan Type</label>
                <select
                  className="form-select"
                  value={options.scanType || 'quick'}
                  onChange={(e) => setOptions({ ...options, scanType: e.target.value })}
                  disabled={isRunning}
                >
                  <option value="quick">Quick Scan</option>
                  <option value="full">Full Scan</option>
                  <option value="stealth">Stealth Scan</option>
                  <option value="aggressive">Aggressive Scan</option>
                </select>
              </div>
            )}

            {workflowType === 'osint_investigation' && (
              <div className="form-group">
                <label className="form-label">Target Type</label>
                <select
                  className="form-select"
                  value={options.type || 'email'}
                  onChange={(e) => setOptions({ ...options, type: e.target.value })}
                  disabled={isRunning}
                >
                  <option value="email">Email</option>
                  <option value="domain">Domain</option>
                  <option value="username">Username</option>
                  <option value="phone">Phone Number</option>
                </select>
              </div>
            )}

            {workflowType === 'purple_team' && (
              <>
                <div className="form-group">
                  <label className="form-label">Target Host</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="10.0.0.1"
                    value={options.targetHost || ''}
                    onChange={(e) => setOptions({ ...options, targetHost: e.target.value })}
                    disabled={isRunning}
                  />
                </div>
              </>
            )}
          </div>

          <button
            className="btn-execute"
            onClick={executeWorkflow}
            disabled={isRunning || !target}
          >
            {isRunning ? '⏳ Running Workflow...' : '🚀 Execute Workflow'}
          </button>
        </div>

        {/* Active Workflow */}
        {activeWorkflow && (
          <div className="active-workflow">
            <h3 className="section-title">Active Workflow</h3>
            <div className="workflow-execution">
              <div className="execution-header">
                <span className="execution-type">{workflows.find(w => w.id === activeWorkflow.type)?.name}</span>
                <span className={`execution-status status-${activeWorkflow.status}`}>
                  {activeWorkflow.status.toUpperCase()}
                </span>
              </div>

              <div className="execution-target">
                <span className="target-label">Target:</span>
                <span className="target-value">{activeWorkflow.target}</span>
              </div>

              {activeWorkflow.status === 'running' && (
                <div className="execution-progress">
                  <div className="progress-spinner"></div>
                  <p>AI is orchestrating services...</p>
                </div>
              )}

              {activeWorkflow.error && (
                <div className="execution-error">
                  <span className="error-icon">⚠️</span>
                  <span className="error-message">{activeWorkflow.error}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Results History */}
        {workflowResults.length > 0 && (
          <div className="workflow-results">
            <h3 className="section-title">Recent Executions</h3>
            <div className="results-list">
              {workflowResults.map((result, idx) => (
                <div key={result.id} className="result-card">
                  <div className="result-header">
                    <div>
                      <span className="result-type">{workflows.find(w => w.id === result.type)?.icon} {workflows.find(w => w.id === result.type)?.name}</span>
                      <span className="result-target">{result.target}</span>
                    </div>
                    <span className={`result-status status-${result.status}`}>
                      {result.status}
                    </span>
                  </div>

                  <div className="result-meta">
                    <span className="result-time">
                      {new Date(result.startTime).toLocaleString('pt-BR')}
                    </span>
                    {result.steps && result.steps.length > 0 && (
                      <span className="result-steps">
                        {result.steps.length} steps completed
                      </span>
                    )}
                  </div>

                  {result.result && result.result.summary && (
                    <div className="result-summary">
                      {result.result.summary}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowsPanel;

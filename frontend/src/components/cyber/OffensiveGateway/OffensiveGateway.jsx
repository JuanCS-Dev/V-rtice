import React, { useState, useEffect } from 'react';
import logger from '@/utils/logger';
import * as offensiveServices from '../../../api/offensiveServices';

/**
 * OffensiveGateway - Unified Orchestration Layer
 * Workflows multi-servi�o, attack chains, RBAC
 */
export const OffensiveGateway = () => {
  const [activeTab, setActiveTab] = useState('workflows');
  const [workflows, setWorkflows] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const tabs = ['workflows', 'executions', 'builder'];

  const handleTabKeyDown = (e) => {
    const currentIndex = tabs.indexOf(activeTab);

    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % tabs.length;
      setActiveTab(tabs[nextIndex]);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      setActiveTab(tabs[prevIndex]);
    } else if (e.key === 'Home') {
      e.preventDefault();
      setActiveTab(tabs[0]);
    } else if (e.key === 'End') {
      e.preventDefault();
      setActiveTab(tabs[tabs.length - 1]);
    }
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    setIsLoading(true);
    try {
      const result = await offensiveServices.listWorkflows();
      if (result.success) {
        setWorkflows(result.workflows || []);
      }
    } catch (error) {
      logger.error('Failed to load workflows:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const executeWorkflow = async (workflowId) => {
    try {
      const result = await offensiveServices.executeWorkflow(workflowId, {});
      if (result.success) {
        setExecutions(prev => [result, ...prev]);
        setActiveTab('executions');
      }
    } catch (error) {
      logger.error('Workflow execution failed:', error);
    }
  };

  const predefinedWorkflows = [
    {
      id: 'full-recon',
      name: 'Full Reconnaissance',
      icon: '🔍',
      desc: 'Network scan → Service detection → Vuln correlation',
      steps: 4,
      color: 'cyan',
    },
    {
      id: 'web-pentest',
      name: 'Web Penetration Test',
      icon: '🎯',
      desc: 'Web scan → OWASP Top 10 → Exploit search',
      steps: 3,
      color: 'orange',
    },
    {
      id: 'attack-chain',
      name: 'Full Attack Chain',
      icon: '⚡',
      desc: 'Recon → Exploit → C2 Session → Post-exploitation',
      steps: 6,
      color: 'red',
    },
    {
      id: 'red-team',
      name: 'Purple Team Exercise',
      icon: '🟣',
      desc: 'BAS simulation → Detection correlation → Report',
      steps: 5,
      color: 'purple',
    },
  ];

  return (
    <article
      className="h-full flex flex-col bg-black/20 backdrop-blur-sm"

      aria-labelledby="offensive-gateway-title"
      data-maximus-tool="offensive-gateway"
      data-maximus-category="offensive"
      data-maximus-status={isLoading ? 'loading' : 'ready'}>

      {/* Header */}
      <header
        className="border-b border-red-400/30 p-4 bg-gradient-to-r from-red-900/20 to-orange-900/20"
        data-maximus-section="tool-header">
        <div className="flex items-center justify-between">
          <div>
            <h2
              id="offensive-gateway-title"
              className="text-2xl font-bold text-red-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl" aria-hidden="true">⚔️</span>
              OFFENSIVE GATEWAY
            </h2>
            <p className="text-red-400/60 text-sm mt-1">
              Unified Orchestration | Multi-Service Workflows | Attack Chains | Port 8037
            </p>
          </div>

          <div className="flex gap-4">
            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">WORKFLOWS</div>
              <div className="text-2xl font-bold text-red-400">{workflows.length || predefinedWorkflows.length}</div>
            </div>
            <div className="bg-black/50 border border-green-400/30 rounded px-4 py-2">
              <div className="text-green-400 text-xs">EXECUTIONS</div>
              <div className="text-2xl font-bold text-green-400">{executions.length}</div>
            </div>
            <div className="bg-black/50 border border-orange-400/30 rounded px-4 py-2">
              <div className="text-orange-400 text-xs">ACTIVE</div>
              <div className="text-2xl font-bold text-orange-400">
                {executions.filter(e => e.status === 'running').length}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <nav
          className="flex gap-2 mt-4"
          role="tablist"
          aria-label="Offensive gateway views"
          data-maximus-section="tab-navigation">
          <button
            id="workflows-tab"
            role="tab"
            aria-selected={activeTab === 'workflows'}
            aria-controls="workflows-panel"
            tabIndex={activeTab === 'workflows' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('workflows')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'workflows'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="workflows">
            WORKFLOWS
          </button>

          <button
            id="executions-tab"
            role="tab"
            aria-selected={activeTab === 'executions'}
            aria-controls="executions-panel"
            tabIndex={activeTab === 'executions' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('executions')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'executions'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="executions">
            EXECUTIONS
          </button>

          <button
            id="builder-tab"
            role="tab"
            aria-selected={activeTab === 'builder'}
            aria-controls="builder-panel"
            tabIndex={activeTab === 'builder' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('builder')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'builder'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="builder">
            BUILDER
          </button>
        </nav>
      </header>

      {/* Content */}
      <section
        className="flex-1 overflow-auto p-6"

        aria-label="Offensive gateway content"
        data-maximus-section="content">

        {activeTab === 'workflows' && (
          <div id="workflows-panel" role="tabpanel" aria-labelledby="workflows-tab" tabIndex={0} className="max-w-6xl mx-auto">
            <div className="mb-6">
              <h3 className="text-red-400 font-bold text-xl mb-4 flex items-center gap-2">
                <span>�</span>
                PREDEFINED WORKFLOWS
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {predefinedWorkflows.map(workflow => (
                  <div
                    key={workflow.id}
                    className={`bg-gradient-to-br from-${workflow.color}-900/20 to-black/20 border-2 border-${workflow.color}-400/30 rounded-lg p-6 hover:border-${workflow.color}-400 transition-all cursor-pointer group`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-4xl">{workflow.icon}</span>
                        <div>
                          <h4 className={`text-${workflow.color}-400 font-bold text-lg`}>
                            {workflow.name}
                          </h4>
                          <p className={`text-${workflow.color}-400/60 text-sm`}>
                            {workflow.desc}
                          </p>
                        </div>
                      </div>
                      <div className={`px-3 py-1 bg-${workflow.color}-400/20 border border-${workflow.color}-400/40 rounded text-${workflow.color}-400 text-sm font-bold`}>
                        {workflow.steps} STEPS
                      </div>
                    </div>

                    <button
                      onClick={() => executeWorkflow(workflow.id)}
                      className={`w-full py-3 bg-gradient-to-r from-${workflow.color}-600 to-${workflow.color}-700 text-white font-bold rounded-lg hover:from-${workflow.color}-500 hover:to-${workflow.color}-600 transition-all shadow-lg`}
                    >
                      =� EXECUTE WORKFLOW
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Custom Workflows */}
            {workflows.length > 0 && (
              <div>
                <h3 className="text-red-400 font-bold text-xl mb-4 flex items-center gap-2">
                  <span>�</span>
                  CUSTOM WORKFLOWS
                </h3>
                <div className="space-y-3">
                  {workflows.map((workflow, idx) => (
                    <div
                      key={idx}
                      className="bg-gradient-to-r from-red-900/20 to-orange-900/20 border border-red-400/30 rounded-lg p-4 hover:border-red-400 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-red-400 font-bold">{workflow.name}</h4>
                          <p className="text-red-400/60 text-sm">{workflow.description}</p>
                        </div>
                        <button
                          onClick={() => executeWorkflow(workflow.id)}
                          className="px-6 py-2 bg-red-600 text-white font-bold rounded hover:bg-red-500 transition-all"
                        >
                          RUN
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'executions' && (
          <div id="executions-panel" role="tabpanel" aria-labelledby="executions-tab" tabIndex={0} className="max-w-6xl mx-auto space-y-4">
            {executions.length === 0 ? (
              <div className="text-center py-20">
                <div className="text-6xl mb-4 opacity-50">�</div>
                <div className="text-red-400/50 text-xl font-bold">No Executions Yet</div>
                <div className="text-red-400/30 text-sm mt-2">
                  Execute a workflow to see results here
                </div>
              </div>
            ) : (
              executions.map((execution, idx) => (
                <div
                  key={idx}
                  className={`border-2 rounded-lg p-6 ${
                    execution.status === 'running'
                      ? 'border-orange-400/50 bg-gradient-to-r from-orange-900/20 to-red-900/20'
                      : execution.status === 'completed'
                      ? 'border-green-400/50 bg-gradient-to-r from-green-900/20 to-orange-900/20'
                      : 'border-red-400/50 bg-gradient-to-r from-red-900/20 to-pink-900/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">
                          {execution.status === 'running' ? '�' : execution.status === 'completed' ? '' : 'L'}
                        </span>
                        <div>
                          <h4 className={`font-bold text-lg ${
                            execution.status === 'running' ? 'text-orange-400' :
                            execution.status === 'completed' ? 'text-green-400' : 'text-red-400'
                          }`}>
                            Execution #{execution.execution_id?.slice(0, 8)}
                          </h4>
                          <p className="text-sm opacity-70">
                            Workflow: {execution.workflow_name || execution.workflow_id}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className={`px-4 py-2 rounded font-bold ${
                      execution.status === 'running' ? 'bg-orange-400/20 text-orange-400 animate-pulse' :
                      execution.status === 'completed' ? 'bg-green-400/20 text-green-400' :
                      'bg-red-400/20 text-red-400'
                    }`}>
                      {execution.status.toUpperCase()}
                    </div>
                  </div>

                  {/* Progress */}
                  {execution.status === 'running' && execution.current_step && (
                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span>Step {execution.current_step} of {execution.total_steps}</span>
                        <span>{Math.floor((execution.current_step / execution.total_steps) * 100)}%</span>
                      </div>
                      <div className="w-full bg-black/50 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-orange-400 to-red-400 h-2 rounded-full transition-all"
                          style={{ width: `${(execution.current_step / execution.total_steps) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Results Summary */}
                  {execution.results && (
                    <div className="grid grid-cols-4 gap-3 mt-4">
                      <div className="bg-black/50 border border-red-400/30 rounded p-3 text-center">
                        <div className="text-red-400 text-xl font-bold">{execution.results.hosts_scanned || 0}</div>
                        <div className="text-red-400/60 text-xs">Hosts Scanned</div>
                      </div>
                      <div className="bg-black/50 border border-orange-400/30 rounded p-3 text-center">
                        <div className="text-orange-400 text-xl font-bold">{execution.results.vulns_found || 0}</div>
                        <div className="text-orange-400/60 text-xs">Vulns Found</div>
                      </div>
                      <div className="bg-black/50 border border-red-400/30 rounded p-3 text-center">
                        <div className="text-red-400 text-xl font-bold">{execution.results.exploits || 0}</div>
                        <div className="text-red-400/60 text-xs">Exploits</div>
                      </div>
                      <div className="bg-black/50 border border-green-400/30 rounded p-3 text-center">
                        <div className="text-green-400 text-xl font-bold">{execution.results.duration || '--'}</div>
                        <div className="text-green-400/60 text-xs">Duration</div>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'builder' && (
          <div id="builder-panel" role="tabpanel" aria-labelledby="builder-tab" tabIndex={0} className="max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-400/30 rounded-lg p-8 text-center">
              <div className="text-6xl mb-4">='</div>
              <h3 className="text-red-400 font-bold text-2xl mb-4">
                Workflow Builder
              </h3>
              <p className="text-red-400/60 mb-6">
                Visual workflow builder for creating custom multi-service attack chains
              </p>
              <button className="px-8 py-3 bg-gradient-to-r from-red-600 to-orange-600 text-white font-bold rounded-lg hover:from-red-500 hover:to-orange-500 transition-all shadow-lg">
                =� LAUNCH BUILDER (COMING SOON)
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Footer */}
      <footer
        className="border-t border-red-400/30 bg-black/50 p-3"
        role="contentinfo"
        data-maximus-section="status-bar">
        <div className="flex justify-between text-xs text-red-400/60">
          <div className="flex gap-4">
            <span role="status" aria-live="polite">STATUS: {isLoading ? '=� LOADING' : '=� READY'}</span>
            <span>SERVICES: 6 Connected</span>
            <span>RBAC: Enabled</span>
          </div>
          <div>OFFENSIVE GATEWAY v3.0 | ORCHESTRATION ENGINE</div>
        </div>
      </footer>
    </article>
  );
};

export default OffensiveGateway;

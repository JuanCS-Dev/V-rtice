import React, { useState } from 'react';
import { SessionManager } from './components/SessionManager';
import { AttackChains } from './components/AttackChains';
import { useC2 } from './hooks/useC2';

/**
 * C2 ORCHESTRATION - Command & Control Orchestration Tool
 *
 * Gerencia sessões Cobalt Strike/Metasploit, executa comandos, attack chains
 * Visual: Matrix-style com sessões ativas e comandos em tempo real
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="c2-orchestration"
 * - <header> for tool header with stats
 * - <nav> for tab navigation with ARIA tablist pattern
 * - <section> for content area (sessions/chains/console)
 * - <footer> for status bar
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="c2-orchestration"
 * - Navigate tabs via role="tablist" and aria-selected
 * - Monitor execution via data-maximus-status="executing"
 * - Access active sessions via semantic structure
 *
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */
export const C2Orchestration = () => {
  const [activeTab, setActiveTab] = useState('sessions'); // 'sessions' | 'chains' | 'console'
  const {
    sessions = [],
    activeSessions = [],
    attackChains = [],
    isExecuting,
    createSession,
    executeCommand,
    passSession,
    executeChain,
    refreshSessions,
  } = useC2();

  const tabs = ['sessions', 'chains', 'console'];

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

  const [sessionConfig, setSessionConfig] = useState({
    framework: 'metasploit', // 'metasploit' | 'cobalt_strike'
    targetHost: '',
    payload: 'windows/meterpreter/reverse_https',
    lhost: '',
    lport: '4444',
  });

  return (
    <article
      className="h-full flex flex-col bg-black/20 backdrop-blur-sm"
      aria-labelledby="c2-orchestration-title"
      data-maximus-tool="c2-orchestration"
      data-maximus-category="offensive"
      data-maximus-status={isExecuting ? 'executing' : 'ready'}>

      {/* Header */}
      <header
        className="border-b border-red-400/30 p-4 bg-gradient-to-r from-red-900/20 to-orange-900/20"
        data-maximus-section="tool-header">
        <div className="flex items-center justify-between">
          <div>
            <h2
              id="c2-orchestration-title"
              className="text-2xl font-bold text-red-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl" aria-hidden="true">🎯</span>
              C2 ORCHESTRATION
            </h2>
            <p className="text-red-400/60 text-sm mt-1">
              Cobalt Strike + Metasploit Integration | Session Passing | Attack Chains | Port 8035
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Stats Cards */}
            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">ACTIVE SESSIONS</div>
              <div className="text-2xl font-bold text-red-400 animate-pulse">
                {activeSessions.length}
              </div>
            </div>

            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">COBALT STRIKE</div>
              <div className="text-2xl font-bold text-red-400">
                {sessions.filter(session => session?.framework === 'cobalt_strike').length}
              </div>
            </div>

            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">METASPLOIT</div>
              <div className="text-2xl font-bold text-red-400">
                {sessions.filter(session => session?.framework === 'metasploit').length}
              </div>
            </div>

            <div className="bg-black/50 border border-orange-400/30 rounded px-4 py-2">
              <div className="text-orange-400 text-xs">ATTACK CHAINS</div>
              <div className="text-2xl font-bold text-orange-400">
                {attackChains.length}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav
          className="flex gap-2 mt-4"
          role="tablist"
          aria-label="C2 orchestration views"
          data-maximus-section="tab-navigation">
          <button
            id="sessions-tab"
            role="tab"
            aria-selected={activeTab === 'sessions'}
            aria-controls="sessions-panel"
            tabIndex={activeTab === 'sessions' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('sessions')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'sessions'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="sessions">
            <span aria-hidden="true">🎮</span> SESSIONS
          </button>

          <button
            id="chains-tab"
            role="tab"
            aria-selected={activeTab === 'chains'}
            aria-controls="chains-panel"
            tabIndex={activeTab === 'chains' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('chains')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'chains'
                ? 'bg-orange-400/20 text-orange-400 border-b-2 border-orange-400'
                : 'bg-black/30 text-orange-400/50 hover:text-orange-400'
            }`}
            data-maximus-tab="chains">
            <span aria-hidden="true">⛓️</span> ATTACK CHAINS
          </button>

          <button
            id="console-tab"
            role="tab"
            aria-selected={activeTab === 'console'}
            aria-controls="console-panel"
            tabIndex={activeTab === 'console' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('console')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'console'
                ? 'bg-green-400/20 text-green-400 border-b-2 border-green-400'
                : 'bg-black/30 text-green-400/50 hover:text-green-400'
            }`}
            data-maximus-tab="console">
            <span aria-hidden="true">💻</span> CONSOLE
          </button>

          <button
            onClick={refreshSessions}
            className="ml-auto px-4 py-2 bg-black/30 text-red-400/70 hover:text-red-400 rounded-t border border-red-400/30 hover:border-red-400 transition-all"
          >
            <span aria-hidden="true">🔄</span> REFRESH
          </button>
        </nav>
      </header>

      {/* Content Area */}
      <section
        className="flex-1 overflow-auto p-6 custom-scrollbar"
        aria-label="C2 orchestration content"
        data-maximus-section="content">

        {activeTab === 'sessions' && (
          <div id="sessions-panel" role="tabpanel" aria-labelledby="sessions-tab" tabIndex={0}>
            <SessionManager
            sessions={sessions}
            activeSessions={activeSessions}
            sessionConfig={sessionConfig}
            setSessionConfig={setSessionConfig}
            onCreateSession={createSession}
            onExecuteCommand={executeCommand}
            onPassSession={passSession}
            isExecuting={isExecuting}
          />
          </div>
        )}

        {activeTab === 'chains' && (
          <div id="chains-panel" role="tabpanel" aria-labelledby="chains-tab" tabIndex={0}>
            <AttackChains
            chains={attackChains}
            onExecuteChain={executeChain}
            isExecuting={isExecuting}
          />
          </div>
        )}

        {activeTab === 'console' && (
          <div id="console-panel" role="tabpanel" aria-labelledby="console-tab" tabIndex={0} className="max-w-6xl mx-auto">
            <div className="bg-black border-2 border-green-400/30 rounded-lg p-4 font-mono">
              <div className="text-green-400 mb-4">
                <span className="text-green-400/60">root@maximus-c2:~#</span> _
              </div>
              <div className="h-96 overflow-y-auto space-y-1 text-green-400/80 text-sm">
                <div>[*] C2 Console initialized...</div>
                <div>[*] Waiting for commands...</div>
                <div className="text-green-400/40">Type 'help' for available commands</div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Footer */}
      <footer
        className="border-t border-red-400/30 bg-black/50 p-3"
        role="contentinfo"
        data-maximus-section="status-bar">
        <div className="flex justify-between items-center text-xs text-red-400/60">
          <div className="flex gap-4">
            <span role="status" aria-live="polite">STATUS: {isExecuting ? '🔴 EXECUTING' : '🟢 READY'}</span>
            <span>FRAMEWORKS: Cobalt Strike v4.9 | Metasploit v6.3</span>
            <span>MODE: ORCHESTRATION</span>
          </div>
          <div>
            C2 ORCHESTRATION v3.0 | MAXIMUS AI KILL CHAIN
          </div>
        </div>
      </footer>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(239, 68, 68, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(239, 68, 68, 0.5);
        }
      `}</style>
    </article>
  );
};

export default C2Orchestration;

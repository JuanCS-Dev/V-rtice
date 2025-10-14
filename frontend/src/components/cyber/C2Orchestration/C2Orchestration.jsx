import React, { useState } from 'react';
import { SessionManager } from './components/SessionManager';
import { AttackChains } from './components/AttackChains';
import { useC2 } from './hooks/useC2';

/**
 * C2Orchestration - Command & Control Orchestration Widget
 *
 * Gerencia sessões Cobalt Strike/Metasploit, executa comandos, attack chains
 * Visual: Matrix-style com sessões ativas e comandos em tempo real
 */
export const C2Orchestration = () => {
  const [activeTab, setActiveTab] = useState('sessions'); // 'sessions' | 'chains' | 'console'
  const {
    sessions,
    activeSessions,
    attackChains,
    isExecuting,
    createSession,
    executeCommand,
    passSession,
    executeChain,
    refreshSessions,
  } = useC2();

  const [sessionConfig, setSessionConfig] = useState({
    framework: 'metasploit', // 'metasploit' | 'cobalt_strike'
    targetHost: '',
    payload: 'windows/meterpreter/reverse_https',
    lhost: '',
    lport: '4444',
  });

  return (
    <div className="h-full flex flex-col bg-black/20 backdrop-blur-sm">
      {/* Header */}
      <div className="border-b border-red-400/30 p-4 bg-gradient-to-r from-red-900/20 to-orange-900/20">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-red-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl">🎯</span>
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
                {sessions.filter(s => s.framework === 'cobalt_strike').length}
              </div>
            </div>

            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">METASPLOIT</div>
              <div className="text-2xl font-bold text-red-400">
                {sessions.filter(s => s.framework === 'metasploit').length}
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
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('sessions')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'sessions'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
          >
            🎮 SESSIONS
          </button>

          <button
            onClick={() => setActiveTab('chains')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'chains'
                ? 'bg-orange-400/20 text-orange-400 border-b-2 border-orange-400'
                : 'bg-black/30 text-orange-400/50 hover:text-orange-400'
            }`}
          >
            ⛓️ ATTACK CHAINS
          </button>

          <button
            onClick={() => setActiveTab('console')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'console'
                ? 'bg-green-400/20 text-green-400 border-b-2 border-green-400'
                : 'bg-black/30 text-green-400/50 hover:text-green-400'
            }`}
          >
            💻 CONSOLE
          </button>

          <button
            onClick={refreshSessions}
            className="ml-auto px-4 py-2 bg-black/30 text-red-400/70 hover:text-red-400 rounded-t border border-red-400/30 hover:border-red-400 transition-all"
          >
            🔄 REFRESH
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6 custom-scrollbar">
        {activeTab === 'sessions' && (
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
        )}

        {activeTab === 'chains' && (
          <AttackChains
            chains={attackChains}
            onExecuteChain={executeChain}
            isExecuting={isExecuting}
          />
        )}

        {activeTab === 'console' && (
          <div className="max-w-6xl mx-auto">
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
      </div>

      {/* Footer */}
      <div className="border-t border-red-400/30 bg-black/50 p-3">
        <div className="flex justify-between items-center text-xs text-red-400/60">
          <div className="flex gap-4">
            <span>STATUS: {isExecuting ? '🔴 EXECUTING' : '🟢 READY'}</span>
            <span>FRAMEWORKS: Cobalt Strike v4.9 | Metasploit v6.3</span>
            <span>MODE: ORCHESTRATION</span>
          </div>
          <div>
            C2 ORCHESTRATION v3.0 | MAXIMUS AI KILL CHAIN
          </div>
        </div>
      </div>

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
    </div>
  );
};

export default C2Orchestration;

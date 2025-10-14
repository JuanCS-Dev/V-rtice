import React, { useState } from 'react';

/**
 * SessionManager - Gerenciamento de sessões C2
 */
export const SessionManager = ({
  activeSessions,
  sessionConfig,
  setSessionConfig,
  onCreateSession,
  onExecuteCommand,
  onPassSession,
  isExecuting,
}) => {
  const [selectedSession, setSelectedSession] = useState(null);
  const [command, setCommand] = useState('');

  const handleCreateSession = async () => {
    const result = await onCreateSession(
      sessionConfig.framework,
      sessionConfig.targetHost,
      sessionConfig.payload,
      {
        lhost: sessionConfig.lhost,
        lport: sessionConfig.lport,
      }
    );

    if (result.success) {
      setSessionConfig({ ...sessionConfig, targetHost: '', lhost: '', lport: '4444' });
    }
  };

  const handleExecuteCommand = async () => {
    if (!selectedSession || !command.trim()) return;

    await onExecuteCommand(selectedSession.session_id, command, []);
    setCommand('');
  };

  const frameworks = [
    { id: 'metasploit', name: 'Metasploit', icon: '🎯', color: 'cyan' },
    { id: 'cobalt_strike', name: 'Cobalt Strike', icon: '🔴', color: 'red' },
  ];

  const commonPayloads = {
    metasploit: [
      'windows/meterpreter/reverse_https',
      'windows/meterpreter/reverse_tcp',
      'linux/x64/meterpreter/reverse_tcp',
      'python/meterpreter/reverse_tcp',
    ],
    cobalt_strike: [
      'windows/beacon_https',
      'windows/beacon_dns',
      'windows/beacon_smb',
    ],
  };

  const commonCommands = [
    { cmd: 'sysinfo', desc: 'System information', icon: '📊' },
    { cmd: 'getuid', desc: 'Current user', icon: '👤' },
    { cmd: 'ps', desc: 'Process list', icon: '⚙️' },
    { cmd: 'shell', desc: 'Interactive shell', icon: '💻' },
    { cmd: 'hashdump', desc: 'Dump hashes', icon: '🔑' },
    { cmd: 'screenshot', desc: 'Capture screen', icon: '📸' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Create Session */}
      <div className="lg:col-span-1 space-y-4">
        <div className="bg-gradient-to-br from-red-900/30 to-orange-900/30 border-2 border-red-400/40 rounded-lg p-6">
          <h3 className="text-red-400 font-bold text-lg mb-4 flex items-center gap-2">
            <span className="text-2xl">🎮</span>
            CREATE SESSION
          </h3>

          <div className="space-y-4">
            {/* Framework Selection */}
            <div>
              <span className="text-red-400/60 text-xs mb-2 block">FRAMEWORK</span>
              <div className="flex gap-2">
                {frameworks.map(fw => (
                  <button
                    key={fw.id}
                    onClick={() => setSessionConfig({ ...sessionConfig, framework: fw.id })}
                    className={`
                      flex-1 p-3 rounded border-2 transition-all
                      ${sessionConfig.framework === fw.id
                        ? `bg-${fw.color}-400/20 border-${fw.color}-400`
                        : 'bg-black/30 border-red-400/20 hover:border-red-400'
                      }
                    `}
                  >
                    <div className="text-2xl mb-1">{fw.icon}</div>
                    <div className={`text-xs font-bold ${sessionConfig.framework === fw.id ? `text-${fw.color}-400` : 'text-red-400/60'}`}>
                      {fw.name}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Target Host */}
            <div>
              <label htmlFor="input-target-host-rpu34" className="text-red-400/60 text-xs mb-2 block">TARGET HOST</label>
<input id="input-target-host-rpu34"
                type="text"
                value={sessionConfig.targetHost}
                onChange={(e) => setSessionConfig({ ...sessionConfig, targetHost: e.target.value })}
                placeholder="192.168.1.100"
                className="w-full bg-black/30 border border-red-400/30 rounded px-3 py-2 text-red-400 font-mono focus:outline-none focus:border-red-400 transition-all"
              />
            </div>

            {/* Payload */}
            <div>
              <label htmlFor="select-payload-izf64" className="text-red-400/60 text-xs mb-2 block">PAYLOAD</label>
<select id="select-payload-izf64"
                value={sessionConfig.payload}
                onChange={(e) => setSessionConfig({ ...sessionConfig, payload: e.target.value })}
                className="w-full bg-black/30 border border-red-400/30 rounded px-3 py-2 text-red-400 text-sm focus:outline-none focus:border-red-400 transition-all"
              >
                {commonPayloads[sessionConfig.framework].map((payload, idx) => (
                  <option key={idx} value={payload}>{payload}</option>
                ))}
              </select>
            </div>

            {/* LHOST / LPORT */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label htmlFor="input-lhost-v0xnz" className="text-red-400/60 text-xs mb-2 block">LHOST</label>
<input id="input-lhost-v0xnz"
                  type="text"
                  value={sessionConfig.lhost}
                  onChange={(e) => setSessionConfig({ ...sessionConfig, lhost: e.target.value })}
                  placeholder="10.0.0.1"
                  className="w-full bg-black/30 border border-red-400/30 rounded px-3 py-2 text-red-400 font-mono text-sm focus:outline-none focus:border-red-400 transition-all"
                />
              </div>
              <div>
                <label htmlFor="input-lport-l3muc" className="text-red-400/60 text-xs mb-2 block">LPORT</label>
<input id="input-lport-l3muc"
                  type="text"
                  value={sessionConfig.lport}
                  onChange={(e) => setSessionConfig({ ...sessionConfig, lport: e.target.value })}
                  placeholder="4444"
                  className="w-full bg-black/30 border border-red-400/30 rounded px-3 py-2 text-red-400 font-mono text-sm focus:outline-none focus:border-red-400 transition-all"
                />
              </div>
            </div>

            {/* Create Button */}
            <button
              onClick={handleCreateSession}
              disabled={isExecuting || !sessionConfig.targetHost || !sessionConfig.lhost}
              className="w-full py-3 bg-gradient-to-r from-red-600 to-orange-600 text-white font-bold rounded hover:from-red-500 hover:to-orange-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-400/20"
            >
              {isExecuting ? '⚙️ CREATING...' : '🚀 CREATE SESSION'}
            </button>
          </div>
        </div>
      </div>

      {/* Center: Active Sessions */}
      <div className="lg:col-span-2 space-y-4">
        <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-400/30 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-red-400 font-bold text-lg flex items-center gap-2">
              <span className="text-2xl">⚡</span>
              ACTIVE SESSIONS
            </h3>
            <div className="bg-black/50 border border-red-400/30 rounded px-3 py-1">
              <span className="text-red-400 font-bold">{activeSessions.length}</span>
              <span className="text-red-400/60 text-xs ml-1">active</span>
            </div>
          </div>

          {activeSessions.length > 0 ? (
            <div className="space-y-3">
              {activeSessions.map((session, idx) => {
                const isSelected = selectedSession?.session_id === session.session_id;
                const frameworkColor = session.framework === 'cobalt_strike' ? 'red' : 'cyan';

                return (
                  <div
                    key={idx}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedSession(session)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        setSelectedSession(session);
                      }
                    }}
                    className={`
                      bg-gradient-to-r from-${frameworkColor}-900/20 to-orange-900/20
                      border-2 border-${frameworkColor}-400/30 rounded-lg p-4
                      hover:border-${frameworkColor}-400 transition-all cursor-pointer
                      ${isSelected ? `ring-2 ring-${frameworkColor}-400/50` : ''}
                    `}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl animate-pulse">
                          {session.framework === 'cobalt_strike' ? '🔴' : '🎯'}
                        </span>
                        <div>
                          <div className={`text-${frameworkColor}-400 font-bold font-mono`}>
                            {session.host || session.target_host}
                          </div>
                          <div className={`text-${frameworkColor}-400/60 text-xs`}>
                            {session.framework.toUpperCase()} • Session {session.session_id}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {session.framework === 'metasploit' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onPassSession(session.session_id, 'cobalt_strike');
                            }}
                            className="px-3 py-1 bg-red-400/20 border border-red-400/40 rounded text-red-400 text-xs font-bold hover:bg-red-400/30 transition-all"
                          >
                            → CS
                          </button>
                        )}
                        {session.framework === 'cobalt_strike' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onPassSession(session.session_id, 'metasploit');
                            }}
                            className="px-3 py-1 bg-red-400/20 border border-red-400/40 rounded text-red-400 text-xs font-bold hover:bg-red-400/30 transition-all"
                          >
                            → MSF
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Session Info */}
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="bg-black/30 border border-red-400/20 rounded px-2 py-1">
                        <span className="text-red-400/60">OS:</span>
                        <span className="text-red-400 ml-1">{session.os || 'Unknown'}</span>
                      </div>
                      <div className="bg-black/30 border border-red-400/20 rounded px-2 py-1">
                        <span className="text-red-400/60">User:</span>
                        <span className="text-red-400 ml-1">{session.user || 'N/A'}</span>
                      </div>
                      <div className="bg-black/30 border border-red-400/20 rounded px-2 py-1">
                        <span className="text-red-400/60">Uptime:</span>
                        <span className="text-red-400 ml-1">{session.uptime || '00:00'}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-20">
              <div className="text-6xl mb-4 opacity-50">🎯</div>
              <div className="text-red-400/50 text-xl font-bold">No Active Sessions</div>
              <div className="text-red-400/30 text-sm mt-2">Create a new session to get started</div>
            </div>
          )}
        </div>

        {/* Command Execution */}
        {selectedSession && (
          <div className="bg-gradient-to-br from-green-900/20 to-orange-900/20 border border-green-400/30 rounded-lg p-6">
            <h3 className="text-green-400 font-bold text-lg mb-4 flex items-center gap-2">
              <span className="text-2xl">💻</span>
              EXECUTE COMMAND
            </h3>

            <div className="space-y-3">
              {/* Quick Commands */}
              <div className="grid grid-cols-3 gap-2">
                {commonCommands.map((cmd, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCommand(cmd.cmd)}
                    className="p-2 bg-black/30 border border-green-400/20 rounded hover:border-green-400 transition-all text-left"
                  >
                    <div className="text-lg mb-1">{cmd.icon}</div>
                    <div className="text-green-400 text-xs font-bold">{cmd.cmd}</div>
                    <div className="text-green-400/50 text-xs">{cmd.desc}</div>
                  </button>
                ))}
              </div>

              {/* Command Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleExecuteCommand()}
                  placeholder="Enter command..."
                  className="flex-1 bg-black/50 border border-green-400/30 rounded px-4 py-2 text-green-400 font-mono focus:outline-none focus:border-green-400 transition-all"
                />
                <button
                  onClick={handleExecuteCommand}
                  disabled={!command.trim()}
                  className="px-6 py-2 bg-gradient-to-r from-green-600 to-orange-600 text-white font-bold rounded hover:from-green-500 hover:to-orange-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  EXECUTE
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionManager;

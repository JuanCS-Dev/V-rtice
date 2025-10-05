import React from 'react';

/**
 * AttackMatrix - MITRE ATT&CK Matrix interativa
 */
export const AttackMatrix = ({
  tactics,
  techniques,
  selectedTactic,
  onSelectTactic,
  simulationConfig,
  setSimulationConfig,
  onRunSimulation,
  isSimulating,
  simulations,
}) => {
  const handleRunSimulation = async () => {
    await onRunSimulation(
      simulationConfig.techniqueId,
      simulationConfig.targetHost,
      simulationConfig.platform,
      simulationConfig.params
    );
  };

  // Mock techniques for demonstration
  const getTechniquesForTactic = (tacticId) => {
    const mockTechniques = {
      'TA0001': [
        { id: 'T1190', name: 'Exploit Public-Facing Application', severity: 'high' },
        { id: 'T1133', name: 'External Remote Services', severity: 'medium' },
        { id: 'T1566', name: 'Phishing', severity: 'high' },
        { id: 'T1078', name: 'Valid Accounts', severity: 'high' },
      ],
      'TA0002': [
        { id: 'T1059', name: 'Command and Scripting Interpreter', severity: 'high' },
        { id: 'T1203', name: 'Exploitation for Client Execution', severity: 'high' },
        { id: 'T1053', name: 'Scheduled Task/Job', severity: 'medium' },
        { id: 'T1569', name: 'System Services', severity: 'medium' },
      ],
      'TA0003': [
        { id: 'T1547', name: 'Boot or Logon Autostart Execution', severity: 'medium' },
        { id: 'T1053', name: 'Scheduled Task/Job', severity: 'medium' },
        { id: 'T1136', name: 'Create Account', severity: 'high' },
        { id: 'T1543', name: 'Create or Modify System Process', severity: 'high' },
      ],
      'TA0004': [
        { id: 'T1068', name: 'Exploitation for Privilege Escalation', severity: 'critical' },
        { id: 'T1134', name: 'Access Token Manipulation', severity: 'high' },
        { id: 'T1548', name: 'Abuse Elevation Control Mechanism', severity: 'high' },
      ],
      'TA0005': [
        { id: 'T1055', name: 'Process Injection', severity: 'high' },
        { id: 'T1140', name: 'Deobfuscate/Decode Files or Information', severity: 'medium' },
        { id: 'T1562', name: 'Impair Defenses', severity: 'critical' },
        { id: 'T1070', name: 'Indicator Removal', severity: 'high' },
      ],
      'TA0006': [
        { id: 'T1003', name: 'OS Credential Dumping', severity: 'critical' },
        { id: 'T1110', name: 'Brute Force', severity: 'high' },
        { id: 'T1555', name: 'Credentials from Password Stores', severity: 'high' },
        { id: 'T1056', name: 'Input Capture', severity: 'high' },
      ],
    };

    return mockTechniques[tacticId] || [];
  };

  const tacticTechniques = selectedTactic ? getTechniquesForTactic(selectedTactic.id) : [];

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'red',
      high: 'orange',
      medium: 'yellow',
      low: 'blue',
    };
    return colors[severity] || 'gray';
  };

  const platforms = [
    { id: 'windows', name: 'Windows', icon: '🪟' },
    { id: 'linux', name: 'Linux', icon: '🐧' },
    { id: 'macos', name: 'macOS', icon: '🍎' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Tactics Selection */}
      <div className="space-y-4">
        <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border-2 border-purple-400/40 rounded-lg p-6">
          <h3 className="text-purple-400 font-bold text-lg mb-4 flex items-center gap-2">
            <span className="text-2xl">🎯</span>
            MITRE ATT&CK TACTICS
          </h3>

          <div className="space-y-2">
            {tactics.map((tactic, idx) => {
              const isSelected = selectedTactic?.id === tactic.id;
              const color = tactic.color;

              return (
                <button
                  key={idx}
                  onClick={() => onSelectTactic(tactic)}
                  className={`
                    w-full p-3 rounded-lg border-2 transition-all text-left
                    ${isSelected
                      ? `bg-${color}-400/20 border-${color}-400`
                      : 'bg-black/30 border-purple-400/20 hover:border-purple-400'
                    }
                  `}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{tactic.icon}</span>
                    <div className="flex-1">
                      <div className={`font-bold text-sm ${isSelected ? `text-${color}-400` : 'text-purple-400/80'}`}>
                        {tactic.name}
                      </div>
                      <div className="text-purple-400/50 text-xs font-mono">
                        {tactic.id}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Center: Techniques & Simulation Config */}
      <div className="lg:col-span-2 space-y-4">
        {selectedTactic ? (
          <>
            {/* Techniques List */}
            <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 border border-purple-400/30 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-purple-400 font-bold text-lg flex items-center gap-2">
                  <span className="text-2xl">{selectedTactic.icon}</span>
                  {selectedTactic.name} Techniques
                </h3>
                <div className="bg-black/50 border border-purple-400/30 rounded px-3 py-1">
                  <span className="text-purple-400 font-bold">{tacticTechniques.length}</span>
                  <span className="text-purple-400/60 text-xs ml-1">techniques</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {tacticTechniques.map((technique, idx) => {
                  const color = getSeverityColor(technique.severity);
                  const isSelected = simulationConfig.techniqueId === technique.id;
                  const wasSimulated = simulations.some(s => s.technique_id === technique.id);

                  return (
                    <div
                      key={idx}
                      onClick={() => setSimulationConfig({ ...simulationConfig, techniqueId: technique.id })}
                      className={`
                        bg-gradient-to-r from-${color}-900/20 to-${color}-900/10
                        border-2 border-${color}-400/30 rounded-lg p-4
                        hover:border-${color}-400 transition-all cursor-pointer
                        ${isSelected ? `ring-2 ring-${color}-400/50` : ''}
                      `}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className={`text-${color}-400 font-bold font-mono text-sm mb-1`}>
                            {technique.id}
                          </div>
                          <div className={`text-${color}-400/80 text-xs`}>
                            {technique.name}
                          </div>
                        </div>
                        {wasSimulated && (
                          <span className="text-green-400 text-xl" title="Already simulated">
                            ✓
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-purple-400/20">
                        <span className={`px-2 py-1 bg-${color}-400/10 border border-${color}-400/30 rounded text-${color}-400 text-xs font-bold`}>
                          {technique.severity.toUpperCase()}
                        </span>
                        {isSelected && (
                          <span className="text-purple-400/60 text-xs">
                            Click to deselect
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Simulation Configuration */}
            {simulationConfig.techniqueId && (
              <div className="bg-gradient-to-br from-cyan-900/20 to-blue-900/20 border-2 border-cyan-400/30 rounded-lg p-6">
                <h3 className="text-cyan-400 font-bold text-lg mb-4 flex items-center gap-2">
                  <span className="text-2xl">⚙️</span>
                  SIMULATION CONFIGURATION
                </h3>

                <div className="space-y-4">
                  {/* Target Host */}
                  <div>
                    <label className="text-cyan-400/60 text-xs mb-2 block">TARGET HOST</label>
                    <input
                      type="text"
                      value={simulationConfig.targetHost}
                      onChange={(e) => setSimulationConfig({ ...simulationConfig, targetHost: e.target.value })}
                      placeholder="192.168.1.100"
                      className="w-full bg-black/30 border border-cyan-400/30 rounded px-4 py-2 text-cyan-400 font-mono focus:outline-none focus:border-cyan-400 transition-all"
                      disabled={isSimulating}
                    />
                  </div>

                  {/* Platform */}
                  <div>
                    <label className="text-cyan-400/60 text-xs mb-2 block">PLATFORM</label>
                    <div className="grid grid-cols-3 gap-2">
                      {platforms.map(platform => (
                        <button
                          key={platform.id}
                          onClick={() => setSimulationConfig({ ...simulationConfig, platform: platform.id })}
                          disabled={isSimulating}
                          className={`
                            p-3 rounded border-2 transition-all
                            ${simulationConfig.platform === platform.id
                              ? 'bg-cyan-400/20 border-cyan-400'
                              : 'bg-black/30 border-cyan-400/20 hover:border-cyan-400'
                            }
                            ${isSimulating ? 'opacity-50 cursor-not-allowed' : ''}
                          `}
                        >
                          <div className="text-2xl mb-1">{platform.icon}</div>
                          <div className={`text-xs font-bold ${simulationConfig.platform === platform.id ? 'text-cyan-400' : 'text-cyan-400/60'}`}>
                            {platform.name}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Run Simulation */}
                  <button
                    onClick={handleRunSimulation}
                    disabled={isSimulating || !simulationConfig.targetHost}
                    className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-lg rounded-lg hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-2xl shadow-purple-400/30 flex items-center justify-center gap-3"
                  >
                    {isSimulating ? (
                      <>
                        <span className="animate-spin text-2xl">⚙️</span>
                        SIMULATION IN PROGRESS...
                      </>
                    ) : (
                      <>
                        <span className="text-2xl">🚀</span>
                        RUN ATTACK SIMULATION
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-50">🎯</div>
            <div className="text-purple-400/50 text-xl font-bold">
              Select a Tactic
            </div>
            <div className="text-purple-400/30 text-sm mt-2">
              Choose a MITRE ATT&CK tactic to view available techniques
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AttackMatrix;

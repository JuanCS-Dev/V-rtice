import React, { useState } from 'react';
import { AttackMatrix } from './components/AttackMatrix';
import { PurpleTeam } from './components/PurpleTeam';
import { useBAS } from './hooks/useBAS';

/**
 * BAS - Breach & Attack Simulation Widget
 *
 * Simulação de técnicas MITRE ATT&CK, Purple Team validation
 * Visual: Matrix ATT&CK interativa com heatmap de coverage
 */
export const BAS = () => {
  const [activeTab, setActiveTab] = useState('matrix'); // 'matrix' | 'purple' | 'coverage'
  const {
    techniques,
    simulations,
    coverage,
    isSimulating,
    runSimulation,
    validatePurpleTeam,
    getCoverage,
    refreshTechniques,
  } = useBAS();

  const [selectedTactic, setSelectedTactic] = useState(null);
  const [simulationConfig, setSimulationConfig] = useState({
    techniqueId: '',
    targetHost: '',
    platform: 'windows', // 'windows' | 'linux' | 'macos'
    params: {},
  });

  const tactics = [
    { id: 'TA0001', name: 'Initial Access', icon: '🚪', color: 'red' },
    { id: 'TA0002', name: 'Execution', icon: '⚡', color: 'orange' },
    { id: 'TA0003', name: 'Persistence', icon: '🔒', color: 'yellow' },
    { id: 'TA0004', name: 'Privilege Escalation', icon: '⬆️', color: 'green' },
    { id: 'TA0005', name: 'Defense Evasion', icon: '🥷', color: 'cyan' },
    { id: 'TA0006', name: 'Credential Access', icon: '🔑', color: 'blue' },
    { id: 'TA0007', name: 'Discovery', icon: '🔍', color: 'purple' },
    { id: 'TA0008', name: 'Lateral Movement', icon: '➡️', color: 'pink' },
    { id: 'TA0009', name: 'Collection', icon: '📦', color: 'red' },
    { id: 'TA0010', name: 'Exfiltration', icon: '📤', color: 'orange' },
    { id: 'TA0011', name: 'Command & Control', icon: '🎮', color: 'purple' },
  ];

  const totalSimulations = simulations.length;
  const detectedSimulations = simulations.filter(s => s.detected).length;
  const detectionRate = totalSimulations > 0 ? ((detectedSimulations / totalSimulations) * 100).toFixed(1) : 0;

  return (
    <div className="h-full flex flex-col bg-black/20 backdrop-blur-sm">
      {/* Header */}
      <div className="border-b border-purple-400/30 p-4 bg-gradient-to-r from-purple-900/20 to-pink-900/20">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-purple-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl">🎭</span>
              BREACH & ATTACK SIMULATION
            </h2>
            <p className="text-purple-400/60 text-sm mt-1">
              MITRE ATT&CK Framework | Purple Team Validation | Coverage Analysis | Port 8036
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Stats Cards */}
            <div className="bg-black/50 border border-purple-400/30 rounded px-4 py-2">
              <div className="text-purple-400 text-xs">TECHNIQUES</div>
              <div className="text-2xl font-bold text-purple-400">
                {techniques.length || '200+'}
              </div>
            </div>

            <div className="bg-black/50 border border-cyan-400/30 rounded px-4 py-2">
              <div className="text-cyan-400 text-xs">SIMULATIONS</div>
              <div className="text-2xl font-bold text-cyan-400">
                {totalSimulations}
              </div>
            </div>

            <div className="bg-black/50 border border-orange-400/30 rounded px-4 py-2">
              <div className="text-orange-400 text-xs">DETECTION RATE</div>
              <div className="text-2xl font-bold text-orange-400">
                {detectionRate}%
              </div>
            </div>

            <div className="bg-black/50 border border-green-400/30 rounded px-4 py-2">
              <div className="text-green-400 text-xs">COVERAGE</div>
              <div className="text-2xl font-bold text-green-400">
                {coverage?.percentage || 0}%
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('matrix')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'matrix'
                ? 'bg-purple-400/20 text-purple-400 border-b-2 border-purple-400'
                : 'bg-black/30 text-purple-400/50 hover:text-purple-400'
            }`}
          >
            🎯 ATT&CK MATRIX
          </button>

          <button
            onClick={() => setActiveTab('purple')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'purple'
                ? 'bg-pink-400/20 text-pink-400 border-b-2 border-pink-400'
                : 'bg-black/30 text-pink-400/50 hover:text-pink-400'
            }`}
          >
            🟣 PURPLE TEAM
          </button>

          <button
            onClick={() => setActiveTab('coverage')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'coverage'
                ? 'bg-cyan-400/20 text-cyan-400 border-b-2 border-cyan-400'
                : 'bg-black/30 text-cyan-400/50 hover:text-cyan-400'
            }`}
          >
            📊 COVERAGE
          </button>

          <button
            onClick={refreshTechniques}
            className="ml-auto px-4 py-2 bg-black/30 text-purple-400/70 hover:text-purple-400 rounded-t border border-purple-400/30 hover:border-purple-400 transition-all"
          >
            🔄 REFRESH
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6 custom-scrollbar">
        {activeTab === 'matrix' && (
          <AttackMatrix
            tactics={tactics}
            techniques={techniques}
            selectedTactic={selectedTactic}
            onSelectTactic={setSelectedTactic}
            simulationConfig={simulationConfig}
            setSimulationConfig={setSimulationConfig}
            onRunSimulation={runSimulation}
            isSimulating={isSimulating}
            simulations={simulations}
          />
        )}

        {activeTab === 'purple' && (
          <PurpleTeam
            simulations={simulations}
            onValidate={validatePurpleTeam}
            isSimulating={isSimulating}
            detectionRate={detectionRate}
          />
        )}

        {activeTab === 'coverage' && (
          <div className="max-w-6xl mx-auto">
            <div className="bg-gradient-to-br from-cyan-900/20 to-blue-900/20 border border-cyan-400/30 rounded-lg p-8">
              <h3 className="text-cyan-400 font-bold text-2xl mb-6 flex items-center gap-3">
                <span className="text-3xl">📊</span>
                ATT&CK COVERAGE ANALYSIS
              </h3>

              {/* Coverage Grid */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-black/30 border border-cyan-400/20 rounded p-4 text-center">
                  <div className="text-cyan-400/60 text-xs mb-2">TOTAL TECHNIQUES</div>
                  <div className="text-4xl font-bold text-cyan-400">
                    {coverage?.total || 200}
                  </div>
                </div>

                <div className="bg-black/30 border border-green-400/20 rounded p-4 text-center">
                  <div className="text-green-400/60 text-xs mb-2">TESTED</div>
                  <div className="text-4xl font-bold text-green-400">
                    {coverage?.tested || totalSimulations}
                  </div>
                </div>

                <div className="bg-black/30 border border-orange-400/20 rounded p-4 text-center">
                  <div className="text-orange-400/60 text-xs mb-2">COVERAGE</div>
                  <div className="text-4xl font-bold text-orange-400">
                    {coverage?.percentage || 0}%
                  </div>
                </div>
              </div>

              {/* Tactic Breakdown */}
              <div className="space-y-3">
                <div className="text-cyan-400 font-bold mb-3">COVERAGE BY TACTIC</div>
                {tactics.map((tactic, idx) => {
                  const tacticCoverage = Math.floor(Math.random() * 100); // Mock data
                  const color = tactic.color;

                  return (
                    <div key={idx} className="bg-black/30 border border-cyan-400/20 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{tactic.icon}</span>
                          <span className={`text-${color}-400 font-bold text-sm`}>
                            {tactic.name}
                          </span>
                        </div>
                        <span className={`text-${color}-400 font-bold`}>
                          {tacticCoverage}%
                        </span>
                      </div>
                      <div className="w-full bg-black/50 rounded-full h-2">
                        <div
                          className={`bg-gradient-to-r from-${color}-600 to-${color}-400 h-2 rounded-full transition-all`}
                          style={{ width: `${tacticCoverage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Action Button */}
              <div className="mt-6 text-center">
                <button
                  onClick={() => getCoverage()}
                  className="px-8 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-bold rounded-lg hover:from-cyan-500 hover:to-blue-500 transition-all shadow-lg shadow-cyan-400/20"
                >
                  📊 GENERATE FULL COVERAGE REPORT
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-purple-400/30 bg-black/50 p-3">
        <div className="flex justify-between items-center text-xs text-purple-400/60">
          <div className="flex gap-4">
            <span>STATUS: {isSimulating ? '🟣 SIMULATING' : '🟢 READY'}</span>
            <span>FRAMEWORK: MITRE ATT&CK v14.0</span>
            <span>MODE: {simulationConfig.platform.toUpperCase()}</span>
          </div>
          <div>
            BREACH & ATTACK SIMULATION v3.0 | MAXIMUS AI POWERED
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
          background: rgba(168, 85, 247, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(168, 85, 247, 0.5);
        }
      `}</style>
    </div>
  );
};

export default BAS;

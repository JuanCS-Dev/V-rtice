import React, { useState } from 'react';

/**
 * PurpleTeam - Purple Team Validation
 */
export const PurpleTeam = ({ simulations, onValidate, isSimulating, detectionRate }) => {
  const [selectedSimulation, setSelectedSimulation] = useState(null);
  const [telemetrySources, setTelemetrySources] = useState({
    siem: true,
    edr: true,
    nids: false,
    firewall: false,
  });

  const handleValidate = async (simulation) => {
    const sources = Object.keys(telemetrySources).filter(key => telemetrySources[key]);
    await onValidate(simulation.simulation_id, sources);
  };

  const sources = [
    { id: 'siem', name: 'SIEM', icon: '🔍', color: 'cyan', description: 'Security Information & Event Management' },
    { id: 'edr', name: 'EDR', icon: '🛡️', color: 'green', description: 'Endpoint Detection & Response' },
    { id: 'nids', name: 'NIDS', icon: '🌐', color: 'orange', description: 'Network Intrusion Detection System' },
    { id: 'firewall', name: 'Firewall', icon: '🔥', color: 'red', description: 'Network Firewall Logs' },
  ];

  const getDetectionStatus = (detected) => {
    if (detected === true) return { icon: '✅', text: 'DETECTED', color: 'green' };
    if (detected === false) return { icon: '❌', text: 'MISSED', color: 'red' };
    return { icon: '⏳', text: 'PENDING', color: 'yellow' };
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Purple Team Overview */}
      <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 border border-purple-400/30 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-purple-400 font-bold text-2xl flex items-center gap-3">
              <span className="text-3xl">🟣</span>
              PURPLE TEAM VALIDATION
            </h3>
            <p className="text-purple-400/60 text-sm mt-1">
              Correlate attack simulations with defensive telemetry
            </p>
          </div>

          <div className="text-right">
            <div className="text-purple-400/60 text-xs mb-1">OVERALL DETECTION RATE</div>
            <div className="text-5xl font-bold text-purple-400">
              {detectionRate}%
            </div>
          </div>
        </div>

        {/* Detection Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-black/30 border border-purple-400/20 rounded p-4 text-center">
            <div className="text-purple-400/60 text-xs mb-2">TOTAL SIMULATIONS</div>
            <div className="text-3xl font-bold text-purple-400">
              {simulations.length}
            </div>
          </div>

          <div className="bg-black/30 border border-green-400/20 rounded p-4 text-center">
            <div className="text-green-400/60 text-xs mb-2">DETECTED</div>
            <div className="text-3xl font-bold text-green-400">
              {simulations.filter(s => s.detected === true).length}
            </div>
          </div>

          <div className="bg-black/30 border border-red-400/20 rounded p-4 text-center">
            <div className="text-red-400/60 text-xs mb-2">MISSED</div>
            <div className="text-3xl font-bold text-red-400">
              {simulations.filter(s => s.detected === false).length}
            </div>
          </div>

          <div className="bg-black/30 border border-yellow-400/20 rounded p-4 text-center">
            <div className="text-yellow-400/60 text-xs mb-2">PENDING</div>
            <div className="text-3xl font-bold text-yellow-400">
              {simulations.filter(s => s.detected === undefined).length}
            </div>
          </div>
        </div>
      </div>

      {/* Telemetry Sources */}
      <div className="bg-gradient-to-br from-cyan-900/20 to-blue-900/20 border border-cyan-400/30 rounded-lg p-6">
        <h3 className="text-cyan-400 font-bold text-lg mb-4 flex items-center gap-2">
          <span className="text-2xl">🔍</span>
          TELEMETRY SOURCES
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {sources.map(source => (
            <label
              key={source.id}
              className={`
                flex items-center gap-3 p-4 rounded-lg border-2 transition-all cursor-pointer
                ${telemetrySources[source.id]
                  ? `bg-${source.color}-400/20 border-${source.color}-400`
                  : 'bg-black/30 border-cyan-400/20 hover:border-cyan-400'
                }
              `}
            >
              <input
                type="checkbox"
                checked={telemetrySources[source.id]}
                onChange={(e) => setTelemetrySources({ ...telemetrySources, [source.id]: e.target.checked })}
                className="hidden"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">{source.icon}</span>
                  <div className={`font-bold ${telemetrySources[source.id] ? `text-${source.color}-400` : 'text-cyan-400/60'}`}>
                    {source.name}
                  </div>
                </div>
                <div className={`text-xs ${telemetrySources[source.id] ? `text-${source.color}-400/70` : 'text-cyan-400/40'}`}>
                  {source.description}
                </div>
              </div>
              {telemetrySources[source.id] && (
                <span className="text-green-400 text-xl">✓</span>
              )}
            </label>
          ))}
        </div>
      </div>

      {/* Simulations List */}
      <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 border border-purple-400/30 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-purple-400 font-bold text-lg flex items-center gap-2">
            <span className="text-2xl">📊</span>
            SIMULATION RESULTS
          </h3>
        </div>

        {simulations.length > 0 ? (
          <div className="space-y-3">
            {simulations.map((simulation, idx) => {
              const detectionStatus = getDetectionStatus(simulation.detected);
              const isExpanded = selectedSimulation === idx;

              return (
                <div
                  key={idx}
                  role="button"
                  tabIndex={0}
                  onClick={() => setSelectedSimulation(isExpanded ? null : idx)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      setSelectedSimulation(isExpanded ? null : idx);
                    }
                  }}
                  className={`
                    bg-gradient-to-r from-${detectionStatus.color}-900/20 to-${detectionStatus.color}-900/10
                    border-2 border-${detectionStatus.color}-400/30 rounded-lg p-4
                    hover:border-${detectionStatus.color}-400 transition-all cursor-pointer
                  `}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3 flex-1">
                      <span className="text-2xl">{detectionStatus.icon}</span>
                      <div className="flex-1">
                        <div className={`text-${detectionStatus.color}-400 font-bold font-mono`}>
                          {simulation.technique_id || `SIM-${idx + 1}`}
                        </div>
                        <div className={`text-${detectionStatus.color}-400/60 text-xs`}>
                          {simulation.technique_name || simulation.description || 'Attack Simulation'}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className={`px-3 py-1 bg-${detectionStatus.color}-400/20 border border-${detectionStatus.color}-400 rounded`}>
                        <span className={`text-${detectionStatus.color}-400 font-bold text-sm`}>
                          {detectionStatus.text}
                        </span>
                      </div>

                      {simulation.detected === undefined && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleValidate(simulation);
                          }}
                          disabled={isSimulating}
                          className="px-4 py-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-xs rounded hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50"
                        >
                          VALIDATE
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="bg-black/30 border border-purple-400/20 rounded px-2 py-1">
                      <span className="text-purple-400/60">Target:</span>
                      <span className="text-purple-400 ml-1">{simulation.target_host || 'N/A'}</span>
                    </div>
                    <div className="bg-black/30 border border-purple-400/20 rounded px-2 py-1">
                      <span className="text-purple-400/60">Platform:</span>
                      <span className="text-purple-400 ml-1">{simulation.platform || 'N/A'}</span>
                    </div>
                    <div className="bg-black/30 border border-purple-400/20 rounded px-2 py-1">
                      <span className="text-purple-400/60">Status:</span>
                      <span className="text-purple-400 ml-1">{simulation.status || 'completed'}</span>
                    </div>
                    <div className="bg-black/30 border border-purple-400/20 rounded px-2 py-1">
                      <span className="text-purple-400/60">Time:</span>
                      <span className="text-purple-400 ml-1">{simulation.timestamp || 'N/A'}</span>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && simulation.telemetry && (
                    <div className="mt-4 pt-4 border-t border-purple-400/20 space-y-2">
                      <div className="text-purple-400/60 text-xs font-bold mb-2">TELEMETRY CORRELATION</div>
                      {Object.entries(simulation.telemetry).map(([source, data], telIdx) => (
                        <div key={telIdx} className="bg-black/30 border border-purple-400/20 rounded p-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="text-purple-400 font-bold text-sm">{source.toUpperCase()}</div>
                            <span className={`text-xs ${data.detected ? 'text-green-400' : 'text-red-400'}`}>
                              {data.detected ? '✅ Detected' : '❌ Not Detected'}
                            </span>
                          </div>
                          {data.logs && (
                            <div className="text-purple-400/70 text-xs font-mono">
                              {data.logs}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Expand Indicator */}
                  <div className="text-purple-400/50 text-xs text-center mt-3">
                    {isExpanded ? '▲ Click to collapse' : '▼ Click for details'}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-50">🟣</div>
            <div className="text-purple-400/50 text-xl font-bold">
              No Simulations Yet
            </div>
            <div className="text-purple-400/30 text-sm mt-2">
              Run attack simulations to validate detection capabilities
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PurpleTeam;

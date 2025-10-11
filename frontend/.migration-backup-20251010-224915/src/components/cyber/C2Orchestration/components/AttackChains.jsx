import React, { useState } from 'react';

/**
 * AttackChains - Kill Chain Automation
 */
export const AttackChains = ({ chains, onExecuteChain, isExecuting }) => {
  const [selectedChain, setSelectedChain] = useState(null);
  const [customChain, setCustomChain] = useState({
    name: '',
    description: '',
    steps: [],
  });

  const predefinedChains = [
    {
      id: 'recon_to_shell',
      name: 'Recon → Shell',
      icon: '🔍→💻',
      color: 'cyan',
      description: 'Network reconnaissance followed by exploitation',
      steps: [
        { phase: 'Reconnaissance', action: 'Network scan', tool: 'Nmap' },
        { phase: 'Weaponization', action: 'Generate payload', tool: 'Metasploit' },
        { phase: 'Delivery', action: 'Deploy exploit', tool: 'Custom' },
        { phase: 'Exploitation', action: 'Execute payload', tool: 'Metasploit' },
        { phase: 'Installation', action: 'Establish persistence', tool: 'Meterpreter' },
      ],
      tactics: ['TA0001', 'TA0002', 'TA0003', 'TA0004'],
    },
    {
      id: 'priv_esc_lateral',
      name: 'Privilege Escalation → Lateral Movement',
      icon: '⬆️→➡️',
      color: 'orange',
      description: 'Escalate privileges and move laterally through network',
      steps: [
        { phase: 'Privilege Escalation', action: 'Exploit vulnerability', tool: 'MSF' },
        { phase: 'Credential Access', action: 'Dump credentials', tool: 'Mimikatz' },
        { phase: 'Lateral Movement', action: 'Pass-the-hash', tool: 'CrackMapExec' },
        { phase: 'Collection', action: 'Gather data', tool: 'Custom' },
      ],
      tactics: ['TA0004', 'TA0006', 'TA0008', 'TA0009'],
    },
    {
      id: 'data_exfil',
      name: 'Data Exfiltration Chain',
      icon: '📦→🌐',
      color: 'red',
      description: 'Complete data exfiltration workflow',
      steps: [
        { phase: 'Discovery', action: 'Enumerate files', tool: 'PowerShell' },
        { phase: 'Collection', action: 'Archive sensitive data', tool: '7zip' },
        { phase: 'Exfiltration', action: 'Transfer over C2', tool: 'Cobalt Strike' },
        { phase: 'Command & Control', action: 'Maintain connection', tool: 'DNS Tunnel' },
      ],
      tactics: ['TA0007', 'TA0009', 'TA0010', 'TA0011'],
    },
    {
      id: 'full_kill_chain',
      name: 'Full Kill Chain',
      icon: '⚔️',
      color: 'purple',
      description: 'Complete attack lifecycle from recon to exfil',
      steps: [
        { phase: 'Reconnaissance', action: 'Target enumeration', tool: 'Multiple' },
        { phase: 'Weaponization', action: 'Prepare exploit', tool: 'Metasploit' },
        { phase: 'Delivery', action: 'Social engineering', tool: 'Phishing' },
        { phase: 'Exploitation', action: 'Initial access', tool: 'Custom' },
        { phase: 'Installation', action: 'Backdoor deployment', tool: 'Cobalt Strike' },
        { phase: 'Command & Control', action: 'C2 channel', tool: 'HTTPS' },
        { phase: 'Actions on Objectives', action: 'Data exfiltration', tool: 'DNScat2' },
      ],
      tactics: ['TA0043', 'TA0001', 'TA0002', 'TA0003', 'TA0004', 'TA0011', 'TA0010'],
    },
  ];

  const allChains = [...predefinedChains, ...chains];

  const handleExecuteChain = async (chain) => {
    await onExecuteChain({
      name: chain.name,
      steps: chain.steps,
      tactics: chain.tactics,
    });
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-400/30 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-orange-400 font-bold text-2xl flex items-center gap-3">
              <span className="text-3xl">⛓️</span>
              ATTACK CHAIN AUTOMATION
            </h3>
            <p className="text-orange-400/60 text-sm mt-1">
              Automated kill chain execution following MITRE ATT&CK framework
            </p>
          </div>
          <div className="bg-black/50 border border-orange-400/30 rounded px-4 py-2">
            <span className="text-orange-400 font-bold">{allChains.length}</span>
            <span className="text-orange-400/60 text-sm ml-1">chains</span>
          </div>
        </div>
      </div>

      {/* Attack Chains Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {allChains.map((chain, idx) => {
          const color = chain.color || 'orange';
          const isSelected = selectedChain?.id === chain.id;

          return (
            <div
              key={idx}
              onClick={() => setSelectedChain(selectedChain?.id === chain.id ? null : chain)}
              className={`
                bg-gradient-to-br from-${color}-900/20 to-${color}-900/10
                border-2 border-${color}-400/30 rounded-lg p-6
                hover:border-${color}-400 transition-all cursor-pointer
                ${isSelected ? `ring-2 ring-${color}-400/50` : ''}
              `}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-4xl">{chain.icon}</span>
                  <div>
                    <div className={`text-${color}-400 font-bold text-lg`}>
                      {chain.name}
                    </div>
                    <div className={`text-${color}-400/60 text-xs`}>
                      {chain.steps.length} steps
                    </div>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleExecuteChain(chain);
                  }}
                  disabled={isExecuting}
                  className={`px-4 py-2 bg-gradient-to-r from-${color}-600 to-red-600 text-white font-bold text-sm rounded hover:from-${color}-500 hover:to-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg`}
                >
                  {isExecuting ? '⚙️' : '🚀'} EXECUTE
                </button>
              </div>

              {/* Description */}
              <p className={`text-${color}-400/70 text-sm mb-4`}>
                {chain.description}
              </p>

              {/* MITRE Tactics */}
              {chain.tactics && chain.tactics.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-4">
                  {chain.tactics.map((tactic, tacticIdx) => (
                    <span
                      key={tacticIdx}
                      className={`px-2 py-1 bg-${color}-400/10 border border-${color}-400/30 rounded text-${color}-400 text-xs font-mono`}
                    >
                      {tactic}
                    </span>
                  ))}
                </div>
              )}

              {/* Steps (Expanded) */}
              {isSelected && (
                <div className="mt-4 pt-4 border-t border-orange-400/20 space-y-2">
                  {chain.steps.map((step, stepIdx) => (
                    <div
                      key={stepIdx}
                      className={`bg-black/30 border border-${color}-400/20 rounded p-3`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className={`text-${color}-400 font-bold text-sm`}>
                          {stepIdx + 1}. {step.phase}
                        </div>
                        <div className={`text-${color}-400/60 text-xs font-mono`}>
                          {step.tool}
                        </div>
                      </div>
                      <div className={`text-${color}-400/70 text-xs`}>
                        {step.action}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Expand Indicator */}
              <div className={`text-${color}-400/50 text-xs text-center mt-3`}>
                {isSelected ? '▲ Click to collapse' : '▼ Click to expand'}
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Custom Chain */}
      <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 border-2 border-purple-400/30 rounded-lg p-6">
        <h3 className="text-purple-400 font-bold text-lg mb-4 flex items-center gap-2">
          <span className="text-2xl">🔧</span>
          CREATE CUSTOM ATTACK CHAIN
        </h3>

        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Chain name..."
            value={customChain.name}
            onChange={(e) => setCustomChain({ ...customChain, name: e.target.value })}
            className="bg-black/30 border border-purple-400/30 rounded px-4 py-2 text-purple-400 placeholder-purple-400/30 focus:outline-none focus:border-purple-400 transition-all"
          />
          <button
            disabled={!customChain.name}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            CREATE CHAIN
          </button>
        </div>

        <div className="mt-4 text-center text-purple-400/50 text-sm">
          Custom chain builder coming soon...
        </div>
      </div>
    </div>
  );
};

export default AttackChains;

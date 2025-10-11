import React from 'react';

/**
 * ScanForm - Formulário de configuração de scan
 */
export const ScanForm = ({ config, onChange, onSubmit, isScanning }) => {
  const handleChange = (field, value) => {
    onChange({ ...config, [field]: value });
  };

  const scanTypes = [
    {
      id: 'quick',
      name: 'Quick Scan',
      desc: 'Top 1000 ports | ~30s',
      icon: '⚡',
      color: 'cyan',
    },
    {
      id: 'full',
      name: 'Full Scan',
      desc: 'All 65535 ports | ~5min',
      icon: '🔥',
      color: 'orange',
    },
    {
      id: 'stealth',
      name: 'Stealth Scan',
      desc: 'SYN scan + evasion | ~2min',
      icon: '👻',
      color: 'purple',
    },
    {
      id: 'aggressive',
      name: 'Aggressive',
      desc: 'OS + Service detection | ~3min',
      icon: '💥',
      color: 'red',
    },
  ];

  const portPresets = [
    { label: 'Top 100', value: '1-100' },
    { label: 'Top 1000', value: '1-1000' },
    { label: 'All Ports', value: '1-65535' },
    { label: 'Web Ports', value: '80,443,8000,8080,8443' },
    { label: 'Database', value: '1433,3306,5432,27017' },
    { label: 'Custom', value: 'custom' },
  ];

  return (
    <div className="space-y-6">
      {/* Target Input */}
      <div className="bg-gradient-to-br from-cyan-900/20 to-blue-900/20 border border-cyan-400/30 rounded-lg p-6">
        <label htmlFor="recon-target-input" className="block text-cyan-400 font-bold mb-3 text-sm tracking-wider">
          🎯 TARGET
        </label>
        <input
          id="recon-target-input"
          type="text"
          value={config.target}
          onChange={(e) => handleChange('target', e.target.value)}
          placeholder="192.168.1.0/24, 10.0.0.1, example.com"
          className="w-full bg-black/50 border border-cyan-400/30 rounded px-4 py-3 text-cyan-400 font-mono focus:outline-none focus:border-cyan-400 transition-all"
          disabled={isScanning}
        />
        <p className="text-cyan-400/50 text-xs mt-2">
          IP, CIDR range, or hostname
        </p>
      </div>

      {/* Scan Type Selection */}
      <div>
        <label htmlFor="scan-type-buttons" className="block text-cyan-400 font-bold mb-3 text-sm tracking-wider">
          ⚙️ SCAN TYPE
        </label>
        <div id="scan-type-buttons" className="grid grid-cols-2 gap-4" role="group" aria-label="Scan type selection">
          {scanTypes.map((type) => (
            <button
              key={type.id}
              onClick={() => handleChange('scanType', type.id)}
              disabled={isScanning}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${
                  config.scanType === type.id
                    ? `border-${type.color}-400 bg-${type.color}-400/20`
                    : 'border-gray-600/30 bg-black/30 hover:border-gray-500'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{type.icon}</span>
                <span className={`font-bold ${config.scanType === type.id ? `text-${type.color}-400` : 'text-gray-400'}`}>
                  {type.name}
                </span>
              </div>
              <p className={`text-xs ${config.scanType === type.id ? `text-${type.color}-400/70` : 'text-gray-500'}`}>
                {type.desc}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Port Configuration */}
      <div>
        <label className="block text-cyan-400 font-bold mb-3 text-sm tracking-wider">
          🔌 PORT RANGE
        </label>
        <div className="flex gap-2 mb-3">
          {portPresets.map((preset) => (
            <button
              key={preset.label}
              onClick={() => {
                if (preset.value !== 'custom') {
                  handleChange('ports', preset.value);
                }
              }}
              disabled={isScanning}
              className={`
                px-4 py-2 rounded text-sm font-bold transition-all
                ${
                  config.ports === preset.value
                    ? 'bg-cyan-400/20 text-cyan-400 border border-cyan-400'
                    : 'bg-black/30 text-cyan-400/50 border border-cyan-400/20 hover:text-cyan-400'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {preset.label}
            </button>
          ))}
        </div>

        <input
          type="text"
          value={config.ports}
          onChange={(e) => handleChange('ports', e.target.value)}
          placeholder="1-1000, 8000-9000, 80,443"
          className="w-full bg-black/50 border border-cyan-400/30 rounded px-4 py-2 text-cyan-400 font-mono text-sm focus:outline-none focus:border-cyan-400 transition-all"
          disabled={isScanning}
        />
      </div>

      {/* Advanced Options */}
      <div className="bg-black/30 border border-cyan-400/20 rounded-lg p-4">
        <label className="block text-cyan-400/70 font-bold mb-3 text-xs tracking-wider">
          🔧 ADVANCED OPTIONS
        </label>
        <div className="grid grid-cols-2 gap-4">
          <label className="flex items-center gap-2 text-cyan-400/70 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={config.serviceDetection}
              onChange={(e) => handleChange('serviceDetection', e.target.checked)}
              disabled={isScanning}
              className="w-4 h-4 accent-cyan-400"
            />
            Service Detection
          </label>

          <label className="flex items-center gap-2 text-cyan-400/70 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={config.osDetection}
              onChange={(e) => handleChange('osDetection', e.target.checked)}
              disabled={isScanning}
              className="w-4 h-4 accent-cyan-400"
            />
            OS Detection
          </label>
        </div>
      </div>

      {/* Submit Button */}
      <button
        onClick={onSubmit}
        disabled={isScanning || !config.target}
        className={`
          w-full py-4 rounded-lg font-bold text-lg tracking-wider transition-all
          ${
            isScanning
              ? 'bg-orange-400/20 text-orange-400 border-2 border-orange-400 cursor-wait'
              : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white border-2 border-cyan-400 hover:border-cyan-300'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
          shadow-lg shadow-cyan-400/20
        `}
      >
        {isScanning ? (
          <span className="flex items-center justify-center gap-3">
            <span className="animate-spin">⚙️</span>
            SCANNING IN PROGRESS...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-3">
            <span>🚀</span>
            LAUNCH SCAN
          </span>
        )}
      </button>

      {!config.target && (
        <p className="text-center text-cyan-400/50 text-sm">
          Enter a target to begin reconnaissance
        </p>
      )}
    </div>
  );
};

export default ScanForm;

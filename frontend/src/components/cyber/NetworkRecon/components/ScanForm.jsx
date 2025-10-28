/**
 * NETWORK RECON SCAN FORM - Semantic Form with Radio Group for Scan Types
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with onSubmit handler
 * - role="radiogroup" for scan type buttons
 * - role="radio" + aria-checked for custom radio buttons
 * - <fieldset> for port presets and advanced options
 * - aria-live for loading status
 * - All emojis in aria-hidden spans
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Radio group with proper ARIA
 * - Checkbox inputs properly labeled
 * - Loading status announced
 * - Keyboard accessible
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';

export const ScanForm = ({ config, onChange, onSubmit, isScanning }) => {
  const handleChange = (field, value) => {
    onChange({ ...config, [field]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (config.target && !isScanning) {
      onSubmit();
    }
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
    <form onSubmit={handleSubmit} aria-label="Network reconnaissance scan configuration" className="space-y-6">
      {/* Target Input */}
      <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-400/30 rounded-lg p-6">
        <label htmlFor="recon-target-input" className="block text-red-400 font-bold mb-3 text-sm tracking-wider">
          <span aria-hidden="true">🎯</span> TARGET
        </label>
        <input
          id="recon-target-input"
          type="text"
          value={config.target}
          onChange={(e) => handleChange('target', e.target.value)}
          placeholder="192.168.1.0/24, 10.0.0.1, example.com"
          className="w-full bg-black/50 border border-red-400/30 rounded px-4 py-3 text-red-400 font-mono focus:outline-none focus:border-red-400 transition-all"
          disabled={isScanning}
          aria-required="true"
          aria-describedby="target-hint"
        />
        <p id="target-hint" className="text-red-400/50 text-xs mt-2">
          IP, CIDR range, or hostname
        </p>
      </div>

      {/* Scan Type Selection */}
      <fieldset>
        <legend className="block text-red-400 font-bold mb-3 text-sm tracking-wider">
          <span aria-hidden="true">⚙️</span> SCAN TYPE
        </legend>
        <div role="radiogroup" aria-label="Scan type selection" className="grid grid-cols-2 gap-4">
          {scanTypes.map((type) => (
            <button
              key={type.id}
              type="button"
              role="radio"
              aria-checked={config.scanType === type.id}
              aria-label={`${type.name}: ${type.desc}`}
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
                <span className="text-2xl" aria-hidden="true">{type.icon}</span>
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
      </fieldset>

      {/* Port Configuration */}
      <fieldset>
        <legend className="block text-red-400 font-bold mb-3 text-sm tracking-wider">
          <span aria-hidden="true">🔌</span> PORT RANGE
        </legend>
        <div className="flex gap-2 mb-3" role="group" aria-label="Port range presets">
          {portPresets.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => {
                if (preset.value !== 'custom') {
                  handleChange('ports', preset.value);
                }
              }}
              disabled={isScanning}
              aria-label={`Set port range to ${preset.label}`}
              className={`
                px-4 py-2 rounded text-sm font-bold transition-all
                ${
                  config.ports === preset.value
                    ? 'bg-red-400/20 text-red-400 border border-red-400'
                    : 'bg-black/30 text-red-400/50 border border-red-400/20 hover:text-red-400'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {preset.label}
            </button>
          ))}
        </div>

        <label htmlFor="port-input" className="sr-only">
          Custom port range
        </label>
        <input
          id="port-input"
          type="text"
          value={config.ports}
          onChange={(e) => handleChange('ports', e.target.value)}
          placeholder="1-1000, 8000-9000, 80,443"
          className="w-full bg-black/50 border border-red-400/30 rounded px-4 py-2 text-red-400 font-mono text-sm focus:outline-none focus:border-red-400 transition-all"
          disabled={isScanning}
        />
      </fieldset>

      {/* Advanced Options */}
      <fieldset className="bg-black/30 border border-red-400/20 rounded-lg p-4">
        <legend className="block text-red-400/70 font-bold mb-3 text-xs tracking-wider">
          <span aria-hidden="true">🔧</span> ADVANCED OPTIONS
        </legend>
        <div className="grid grid-cols-2 gap-4">
          <label htmlFor="service-detection-checkbox" className="flex items-center gap-2 text-red-400/70 text-sm cursor-pointer">
            <input
              id="service-detection-checkbox"
              type="checkbox"
              checked={config.serviceDetection}
              onChange={(e) => handleChange('serviceDetection', e.target.checked)}
              disabled={isScanning}
              className="w-4 h-4 accent-red-400"
            />
            Service Detection
          </label>

          <label htmlFor="os-detection-checkbox" className="flex items-center gap-2 text-red-400/70 text-sm cursor-pointer">
            <input
              id="os-detection-checkbox"
              type="checkbox"
              checked={config.osDetection}
              onChange={(e) => handleChange('osDetection', e.target.checked)}
              disabled={isScanning}
              className="w-4 h-4 accent-red-400"
            />
            OS Detection
          </label>
        </div>
      </fieldset>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isScanning || !config.target}
        aria-label={isScanning ? "Scan in progress" : "Launch reconnaissance scan"}
        className={`
          w-full py-4 rounded-lg font-bold text-lg tracking-wider transition-all
          ${
            isScanning
              ? 'bg-orange-400/20 text-orange-400 border-2 border-orange-400 cursor-wait'
              : 'bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white border-2 border-red-400 hover:border-red-300'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
          shadow-lg shadow-red-400/20
        `}
      >
        {isScanning ? (
          <span className="flex items-center justify-center gap-3">
            <span className="animate-spin" aria-hidden="true">⚙️</span>
            SCANNING IN PROGRESS...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-3">
            <span aria-hidden="true">🚀</span>
            LAUNCH SCAN
          </span>
        )}
      </button>

      {isScanning && (
        <div className="sr-only" role="status" aria-live="polite">
          Network reconnaissance scan in progress...
        </div>
      )}

      {!config.target && (
        <p className="text-center text-red-400/50 text-sm">
          Enter a target to begin reconnaissance
        </p>
      )}
    </form>
  );
};

export default ScanForm;

/**
 * WEB ATTACK SCAN FORM - Semantic Form with Profile Selection and Attack Tests
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with onSubmit handler
 * - role="radiogroup" for scan profile buttons
 * - Checkbox inputs with explicit labels
 * - <fieldset> for grouped sections
 * - aria-live for loading status
 * - All emojis in aria-hidden spans
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Scan profiles use radio group pattern
 * - Test checkboxes properly labeled
 * - Loading status announced
 * - Keyboard accessible
 * - Security warning visible
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';

export const ScanForm = ({ config, onChange, onSubmit, isScanning }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const updateConfig = (field, value) => {
    onChange({ ...config, [field]: value });
  };

  const updateTests = (test, value) => {
    onChange({
      ...config,
      tests: { ...config.tests, [test]: value },
    });
  };

  const scanProfiles = [
    { id: 'quick', name: 'Quick Scan', icon: '⚡', time: '~5 min', description: 'Basic OWASP checks' },
    { id: 'full', name: 'Full Scan', icon: '🔥', time: '~30 min', description: 'Complete security audit' },
    { id: 'stealth', name: 'Stealth Scan', icon: '🥷', time: '~60 min', description: 'Low & slow detection' },
  ];

  const testTypes = [
    { id: 'sqli', name: 'SQL Injection', icon: '💉', color: 'red' },
    { id: 'xss', name: 'Cross-Site Scripting', icon: '🔗', color: 'orange' },
    { id: 'ssrf', name: 'Server-Side Request Forgery', icon: '🌐', color: 'yellow' },
    { id: 'lfi', name: 'Local File Inclusion', icon: '📁', color: 'purple' },
    { id: 'rce', name: 'Remote Code Execution', icon: '💻', color: 'red' },
    { id: 'xxe', name: 'XML External Entity', icon: '📄', color: 'orange' },
  ];

  return (
    <form onSubmit={handleSubmit} aria-label="Web attack scan configuration" className="space-y-6">
      {/* Target URL */}
      <div className="bg-gradient-to-br from-orange-900/20 to-red-900/20 border-2 border-orange-400/30 rounded-lg p-6">
        <label htmlFor="web-attack-url" className="block mb-3">
          <span className="text-orange-400 font-bold text-sm flex items-center gap-2 mb-2">
            <span className="text-xl" aria-hidden="true">🎯</span>
            TARGET URL
          </span>
          <input
            id="web-attack-url"
            type="url"
            value={config.url}
            onChange={(e) => updateConfig('url', e.target.value)}
            placeholder="https://target.com"
            className="w-full bg-black/30 border-2 border-orange-400/30 rounded-lg px-4 py-3 text-orange-400 font-mono text-lg focus:outline-none focus:border-orange-400 transition-all placeholder-orange-400/30"
            required
            disabled={isScanning}
            aria-required="true"
          />
        </label>
      </div>

      {/* Scan Profile */}
      <fieldset className="bg-gradient-to-br from-orange-900/20 to-red-900/20 border-2 border-orange-400/30 rounded-lg p-6">
        <legend className="text-orange-400 font-bold text-sm flex items-center gap-2 mb-4">
          <span className="text-xl" aria-hidden="true">⚙️</span>
          SCAN PROFILE
        </legend>

        <div role="radiogroup" aria-label="Scan profile selection" className="grid grid-cols-3 gap-4">
          {scanProfiles.map(profile => (
            <button
              key={profile.id}
              type="button"
              role="radio"
              aria-checked={config.scanProfile === profile.id}
              aria-label={`${profile.name}: ${profile.description}, takes approximately ${profile.time}`}
              onClick={() => updateConfig('scanProfile', profile.id)}
              disabled={isScanning}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${config.scanProfile === profile.id
                  ? 'bg-orange-400/20 border-orange-400'
                  : 'bg-black/30 border-orange-400/20 hover:border-orange-400'
                }
                ${isScanning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="text-3xl mb-2" aria-hidden="true">{profile.icon}</div>
              <div className="text-orange-400 font-bold mb-1">{profile.name}</div>
              <div className="text-orange-400/60 text-xs mb-2">{profile.time}</div>
              <div className="text-orange-400/50 text-xs">{profile.description}</div>
            </button>
          ))}
        </div>
      </fieldset>

      {/* Test Selection */}
      <fieldset className="bg-gradient-to-br from-orange-900/20 to-red-900/20 border-2 border-orange-400/30 rounded-lg p-6">
        <legend className="text-orange-400 font-bold text-sm flex items-center gap-2 mb-4">
          <span className="text-xl" aria-hidden="true">🔬</span>
          ATTACK TESTS
        </legend>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3" role="group" aria-label="Attack test selection">
          {testTypes.map(test => (
            <label
              key={test.id}
              htmlFor={`test-${test.id}`}
              className={`
                flex items-center gap-3 p-3 rounded-lg border-2 transition-all cursor-pointer
                ${config.tests[test.id]
                  ? `bg-${test.color}-400/20 border-${test.color}-400`
                  : 'bg-black/30 border-orange-400/20 hover:border-orange-400'
                }
                ${isScanning ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input
                id={`test-${test.id}`}
                type="checkbox"
                checked={config.tests[test.id]}
                onChange={(e) => updateTests(test.id, e.target.checked)}
                disabled={isScanning}
                className="sr-only"
              />
              <span className="text-2xl" aria-hidden="true">{test.icon}</span>
              <div className="flex-1">
                <div className={`font-bold text-sm ${config.tests[test.id] ? `text-${test.color}-400` : 'text-orange-400/60'}`}>
                  {test.name}
                </div>
              </div>
              {config.tests[test.id] && (
                <span className="text-green-400 text-xl" aria-hidden="true">✓</span>
              )}
            </label>
          ))}
        </div>
      </fieldset>

      {/* Authentication (Optional) */}
      <fieldset className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border-2 border-red-400/30 rounded-lg p-6">
        <legend className="text-red-400 font-bold text-sm flex items-center gap-2 mb-4">
          <span className="text-xl" aria-hidden="true">🔐</span>
          AUTHENTICATION (Optional)
        </legend>

        <div className="grid grid-cols-2 gap-4">
          <label htmlFor="web-attack-username" className="sr-only">
            Username
          </label>
          <input
            id="web-attack-username"
            type="text"
            placeholder="Username"
            className="bg-black/30 border border-red-400/30 rounded px-4 py-2 text-red-400 placeholder-red-400/30 focus:outline-none focus:border-red-400 transition-all"
            disabled={isScanning}
          />

          <label htmlFor="web-attack-password" className="sr-only">
            Password
          </label>
          <input
            id="web-attack-password"
            type="password"
            placeholder="Password"
            className="bg-black/30 border border-red-400/30 rounded px-4 py-2 text-red-400 placeholder-red-400/30 focus:outline-none focus:border-red-400 transition-all"
            disabled={isScanning}
          />
        </div>
      </fieldset>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isScanning || !config.url}
        aria-label={isScanning ? "Web attack scan in progress" : "Launch web attack scan"}
        className="w-full py-4 bg-gradient-to-r from-orange-600 to-red-600 text-white font-bold text-xl rounded-lg hover:from-orange-500 hover:to-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-2xl shadow-orange-400/30 flex items-center justify-center gap-3"
      >
        {isScanning ? (
          <>
            <span className="animate-spin text-2xl" aria-hidden="true">⚙️</span>
            SCANNING IN PROGRESS...
          </>
        ) : (
          <>
            <span className="text-2xl" aria-hidden="true">🚀</span>
            LAUNCH WEB ATTACK SCAN
          </>
        )}
      </button>

      {isScanning && (
        <div className="sr-only" role="status" aria-live="polite">
          Web attack scan in progress...
        </div>
      )}

      {/* Warning */}
      <div className="bg-yellow-900/20 border border-yellow-400/30 rounded-lg p-4" role="alert">
        <div className="flex items-start gap-3">
          <span className="text-2xl" aria-hidden="true">⚠️</span>
          <div className="flex-1">
            <div className="text-yellow-400 font-bold text-sm mb-1">LEGAL WARNING</div>
            <div className="text-yellow-400/70 text-xs">
              Only scan systems you have explicit authorization to test. Unauthorized security testing is illegal and unethical.
            </div>
          </div>
        </div>
      </div>
    </form>
  );
};

export default ScanForm;

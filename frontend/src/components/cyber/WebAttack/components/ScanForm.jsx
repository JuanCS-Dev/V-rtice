import React from 'react';

/**
 * ScanForm - Formulário de configuração de scan web
 */
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
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Target URL */}
      <div className="bg-gradient-to-br from-orange-900/20 to-red-900/20 border-2 border-orange-400/30 rounded-lg p-6">
        <label className="block mb-3">
          <span className="text-orange-400 font-bold text-sm flex items-center gap-2 mb-2">
            <span className="text-xl">🎯</span>
            TARGET URL
          </span>
          <input
            type="url"
            value={config.url}
            onChange={(e) => updateConfig('url', e.target.value)}
            placeholder="https://target.com"
            className="w-full bg-black/30 border-2 border-orange-400/30 rounded-lg px-4 py-3 text-orange-400 font-mono text-lg focus:outline-none focus:border-orange-400 transition-all placeholder-orange-400/30"
            required
            disabled={isScanning}
          />
        </label>
      </div>

      {/* Scan Profile */}
      <div className="bg-gradient-to-br from-orange-900/20 to-red-900/20 border-2 border-orange-400/30 rounded-lg p-6">
        <div className="text-orange-400 font-bold text-sm flex items-center gap-2 mb-4">
          <span className="text-xl">⚙️</span>
          SCAN PROFILE
        </div>

        <div className="grid grid-cols-3 gap-4">
          {scanProfiles.map(profile => (
            <button
              key={profile.id}
              type="button"
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
              <div className="text-3xl mb-2">{profile.icon}</div>
              <div className="text-orange-400 font-bold mb-1">{profile.name}</div>
              <div className="text-orange-400/60 text-xs mb-2">{profile.time}</div>
              <div className="text-orange-400/50 text-xs">{profile.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Test Selection */}
      <div className="bg-gradient-to-br from-orange-900/20 to-red-900/20 border-2 border-orange-400/30 rounded-lg p-6">
        <div className="text-orange-400 font-bold text-sm flex items-center gap-2 mb-4">
          <span className="text-xl">🔬</span>
          ATTACK TESTS
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {testTypes.map(test => (
            <label
              key={test.id}
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
                type="checkbox"
                checked={config.tests[test.id]}
                onChange={(e) => updateTests(test.id, e.target.checked)}
                disabled={isScanning}
                className="hidden"
              />
              <span className="text-2xl">{test.icon}</span>
              <div className="flex-1">
                <div className={`font-bold text-sm ${config.tests[test.id] ? `text-${test.color}-400` : 'text-orange-400/60'}`}>
                  {test.name}
                </div>
              </div>
              {config.tests[test.id] && (
                <span className="text-green-400 text-xl">✓</span>
              )}
            </label>
          ))}
        </div>
      </div>

      {/* Authentication (Optional) */}
      <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border-2 border-red-400/30 rounded-lg p-6">
        <div className="text-red-400 font-bold text-sm flex items-center gap-2 mb-4">
          <span className="text-xl">🔐</span>
          AUTHENTICATION (Optional)
        </div>

        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Username"
            className="bg-black/30 border border-red-400/30 rounded px-4 py-2 text-red-400 placeholder-red-400/30 focus:outline-none focus:border-red-400 transition-all"
            disabled={isScanning}
          />
          <input
            type="password"
            placeholder="Password"
            className="bg-black/30 border border-red-400/30 rounded px-4 py-2 text-red-400 placeholder-red-400/30 focus:outline-none focus:border-red-400 transition-all"
            disabled={isScanning}
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isScanning || !config.url}
        className="w-full py-4 bg-gradient-to-r from-orange-600 to-red-600 text-white font-bold text-xl rounded-lg hover:from-orange-500 hover:to-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-2xl shadow-orange-400/30 flex items-center justify-center gap-3"
      >
        {isScanning ? (
          <>
            <span className="animate-spin text-2xl">⚙️</span>
            SCANNING IN PROGRESS...
          </>
        ) : (
          <>
            <span className="text-2xl">🚀</span>
            LAUNCH WEB ATTACK SCAN
          </>
        )}
      </button>

      {/* Warning */}
      <div className="bg-yellow-900/20 border border-yellow-400/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚠️</span>
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

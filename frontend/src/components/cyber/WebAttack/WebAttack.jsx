import React, { useState } from 'react';
import { ScanForm } from './components/ScanForm';
import { ScanResults } from './components/ScanResults';
import { useWebAttack } from './hooks/useWebAttack';

/**
 * WebAttack - Web Attack Surface Widget
 *
 * Scan de superfície web: OWASP Top 10, SQLi, XSS, SSRF, etc
 * Visual: Terminal de ataque com resultados em tempo real
 */
export const WebAttack = () => {
  const [activeTab, setActiveTab] = useState('scan'); // 'scan' | 'results' | 'history'
  const {
    currentScan: _currentScan,
    scans,
    isScanning,
    scanResults,
    startScan,
    runTest: _runTest,
    getReport,
  } = useWebAttack();

  const [scanConfig, setScanConfig] = useState({
    url: '',
    scanProfile: 'full', // 'quick' | 'full' | 'stealth'
    tests: {
      sqli: true,
      xss: true,
      ssrf: true,
      lfi: true,
      rce: true,
      xxe: true,
    },
    authConfig: null,
  });

  const handleStartScan = async () => {
    const result = await startScan(
      scanConfig.url,
      scanConfig.scanProfile,
      scanConfig.authConfig
    );

    if (result.success) {
      setActiveTab('results');
    }
  };

  return (
    <div className="h-full flex flex-col bg-black/20 backdrop-blur-sm">
      {/* Header */}
      <div className="border-b border-orange-400/30 p-4 bg-gradient-to-r from-orange-900/20 to-red-900/20">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-orange-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl">🌐</span>
              WEB ATTACK SURFACE
            </h2>
            <p className="text-orange-400/60 text-sm mt-1">
              OWASP Top 10 | SQLi | XSS | SSRF | RCE Detection | Port 8034
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Stats Cards */}
            <div className="bg-black/50 border border-orange-400/30 rounded px-4 py-2">
              <div className="text-orange-400 text-xs">ACTIVE SCANS</div>
              <div className="text-2xl font-bold text-orange-400">
                {scans.filter(s => s.status === 'running').length}
              </div>
            </div>

            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">VULNS FOUND</div>
              <div className="text-2xl font-bold text-red-400">
                {scanResults?.vulnerabilities?.length || 0}
              </div>
            </div>

            <div className="bg-black/50 border border-yellow-400/30 rounded px-4 py-2">
              <div className="text-yellow-400 text-xs">CRITICAL</div>
              <div className="text-2xl font-bold text-yellow-400">
                {scanResults?.vulnerabilities?.filter(v => v.severity === 'CRITICAL').length || 0}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('scan')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'scan'
                ? 'bg-orange-400/20 text-orange-400 border-b-2 border-orange-400'
                : 'bg-black/30 text-orange-400/50 hover:text-orange-400'
            }`}
          >
            🎯 NEW SCAN
          </button>

          <button
            onClick={() => setActiveTab('results')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'results'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
          >
            📊 RESULTS
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'history'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
          >
            📚 HISTORY
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6 custom-scrollbar">
        {activeTab === 'scan' && (
          <div className="max-w-4xl mx-auto">
            <ScanForm
              config={scanConfig}
              onChange={setScanConfig}
              onSubmit={handleStartScan}
              isScanning={isScanning}
            />
          </div>
        )}

        {activeTab === 'results' && (
          <div className="max-w-6xl mx-auto">
            {scanResults ? (
              <ScanResults results={scanResults} />
            ) : (
              <div className="text-center py-20">
                <div className="text-6xl mb-4 opacity-50">🌐</div>
                <div className="text-orange-400/50 text-xl font-bold">
                  No Scan Results
                </div>
                <div className="text-orange-400/30 text-sm mt-2">
                  Start a new scan to see results here
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="max-w-6xl mx-auto space-y-4">
            {scans.length > 0 ? (
              scans.map((scan, idx) => (
                <div
                  key={idx}
                  onClick={() => getReport(scan.scan_id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      getReport(scan.scan_id);
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-label={`View scan report for ${scan.url}`}
                  className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-400/30 rounded-lg p-4 hover:border-orange-400 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-mono font-bold text-orange-400 text-lg">
                        {scan.url}
                      </div>
                      <div className="text-orange-400/60 text-sm">
                        {scan.started_at} • Profile: {scan.scan_profile}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={`px-4 py-2 rounded ${
                        scan.status === 'completed' ? 'bg-green-400/20 text-green-400' :
                        scan.status === 'running' ? 'bg-orange-400/20 text-orange-400 animate-pulse' :
                        'bg-red-400/20 text-red-400'
                      }`}>
                        {scan.status.toUpperCase()}
                      </div>
                      {scan.vulnerabilities_found > 0 && (
                        <div className="bg-red-400/20 border border-red-400 rounded px-3 py-1">
                          <span className="text-red-400 font-bold">{scan.vulnerabilities_found}</span>
                          <span className="text-red-400/60 text-sm ml-1">vulns</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-20">
                <div className="text-6xl mb-4 opacity-50">📚</div>
                <div className="text-orange-400/50 text-xl font-bold">
                  No Scan History
                </div>
                <div className="text-orange-400/30 text-sm mt-2">
                  Your scan history will appear here
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-orange-400/30 bg-black/50 p-3">
        <div className="flex justify-between items-center text-xs text-orange-400/60">
          <div className="flex gap-4">
            <span>STATUS: {isScanning ? '🟠 SCANNING' : '🟢 READY'}</span>
            <span>ENGINE: ZAP Proxy + Custom Modules</span>
            <span>MODE: {scanConfig.scanProfile.toUpperCase()}</span>
          </div>
          <div>
            WEB ATTACK SURFACE v3.0 | MAXIMUS AI INTEGRATION
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
          background: rgba(251, 146, 60, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(251, 146, 60, 0.5);
        }
      `}</style>
    </div>
  );
};

export default WebAttack;

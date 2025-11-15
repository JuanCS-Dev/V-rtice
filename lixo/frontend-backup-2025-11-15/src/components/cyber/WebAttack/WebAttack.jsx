import React, { useState } from "react";
import { ScanForm } from "./components/ScanForm";
import { ScanResults } from "./components/ScanResults";
import { useWebAttack } from "./hooks/useWebAttack";

/**
 * WEB ATTACK - Web Attack Surface Tool
 *
 * Scan de superfície web: OWASP Top 10, SQLi, XSS, SSRF, etc
 * Visual: Terminal de ataque com resultados em tempo real
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="web-attack"
 * - <header> for tool header with stats
 * - <nav> for tab navigation with ARIA tablist pattern
 * - <section> for content area (scan/results/history)
 * - <footer> for status bar
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="web-attack"
 * - Navigate tabs via role="tablist" and aria-selected
 * - Monitor scan status via data-maximus-status="scanning"
 * - Access scan results via semantic structure
 *
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */
export const WebAttack = () => {
  const [activeTab, setActiveTab] = useState("scan"); // 'scan' | 'results' | 'history'
  const {
    currentScan: _currentScan,
    scans,
    isScanning,
    scanResults,
    startScan,
    runTest: _runTest,
    getReport,
  } = useWebAttack();

  const tabs = ["scan", "results", "history"];

  const handleTabKeyDown = (e) => {
    const currentIndex = tabs.indexOf(activeTab);

    if (e.key === "ArrowRight") {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % tabs.length;
      setActiveTab(tabs[nextIndex]);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      setActiveTab(tabs[prevIndex]);
    } else if (e.key === "Home") {
      e.preventDefault();
      setActiveTab(tabs[0]);
    } else if (e.key === "End") {
      e.preventDefault();
      setActiveTab(tabs[tabs.length - 1]);
    }
  };

  const [scanConfig, setScanConfig] = useState({
    url: "",
    scanProfile: "full", // 'quick' | 'full' | 'stealth'
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
      scanConfig.authConfig,
    );

    if (result.success) {
      setActiveTab("results");
    }
  };

  return (
    <article
      className="h-full flex flex-col bg-black/20 backdrop-blur-sm"
      aria-labelledby="web-attack-title"
      data-maximus-tool="web-attack"
      data-maximus-category="offensive"
      data-maximus-status={isScanning ? "scanning" : "ready"}
    >
      {/* Header */}
      <header
        className="border-b border-orange-400/30 p-4 bg-gradient-to-r from-orange-900/20 to-red-900/20"
        data-maximus-section="tool-header"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2
              id="web-attack-title"
              className="text-2xl font-bold text-orange-400 tracking-wider flex items-center gap-3"
            >
              <span className="text-3xl" aria-hidden="true">
                🌐
              </span>
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
                {scans.filter((s) => s.status === "running").length}
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
                {scanResults?.vulnerabilities?.filter(
                  (v) => v.severity === "CRITICAL",
                ).length || 0}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav
          className="flex gap-2 mt-4"
          role="tablist"
          aria-label="Web attack views"
          data-maximus-section="tab-navigation"
        >
          <button
            id="scan-tab"
            role="tab"
            aria-selected={activeTab === "scan"}
            aria-controls="scan-panel"
            tabIndex={activeTab === "scan" ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab("scan")}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === "scan"
                ? "bg-orange-400/20 text-orange-400 border-b-2 border-orange-400"
                : "bg-black/30 text-orange-400/50 hover:text-orange-400"
            }`}
            data-maximus-tab="scan"
          >
            <span aria-hidden="true">🎯</span> NEW SCAN
          </button>

          <button
            id="results-tab"
            role="tab"
            aria-selected={activeTab === "results"}
            aria-controls="results-panel"
            tabIndex={activeTab === "results" ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab("results")}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === "results"
                ? "bg-red-400/20 text-red-400 border-b-2 border-red-400"
                : "bg-black/30 text-red-400/50 hover:text-red-400"
            }`}
            data-maximus-tab="results"
          >
            <span aria-hidden="true">📊</span> RESULTS
          </button>

          <button
            id="history-tab"
            role="tab"
            aria-selected={activeTab === "history"}
            aria-controls="history-panel"
            tabIndex={activeTab === "history" ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab("history")}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === "history"
                ? "bg-red-400/20 text-red-400 border-b-2 border-red-400"
                : "bg-black/30 text-red-400/50 hover:text-red-400"
            }`}
            data-maximus-tab="history"
          >
            <span aria-hidden="true">📚</span> HISTORY
          </button>
        </nav>
      </header>

      {/* Content Area */}
      <section
        className="flex-1 overflow-auto p-6 custom-scrollbar"
        aria-label="Web attack content"
        data-maximus-section="content"
      >
        {activeTab === "scan" && (
          <div
            id="scan-panel"
            role="tabpanel"
            aria-labelledby="scan-tab"
            tabIndex={0}
            className="max-w-4xl mx-auto"
          >
            <ScanForm
              config={scanConfig}
              onChange={setScanConfig}
              onSubmit={handleStartScan}
              isScanning={isScanning}
            />
          </div>
        )}

        {activeTab === "results" && (
          <div
            id="results-panel"
            role="tabpanel"
            aria-labelledby="results-tab"
            tabIndex={0}
            className="max-w-6xl mx-auto"
          >
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

        {activeTab === "history" && (
          <div
            id="history-panel"
            role="tabpanel"
            aria-labelledby="history-tab"
            tabIndex={0}
            className="max-w-6xl mx-auto space-y-4"
          >
            {scans.length > 0 ? (
              scans.map((scan, idx) => (
                <div
                  key={idx}
                  onClick={() => getReport(scan.scan_id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
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
                      <div
                        className={`px-4 py-2 rounded ${
                          scan.status === "completed"
                            ? "bg-green-400/20 text-green-400"
                            : scan.status === "running"
                              ? "bg-orange-400/20 text-orange-400 animate-pulse"
                              : "bg-red-400/20 text-red-400"
                        }`}
                      >
                        {scan.status.toUpperCase()}
                      </div>
                      {scan.vulnerabilities_found > 0 && (
                        <div className="bg-red-400/20 border border-red-400 rounded px-3 py-1">
                          <span className="text-red-400 font-bold">
                            {scan.vulnerabilities_found}
                          </span>
                          <span className="text-red-400/60 text-sm ml-1">
                            vulns
                          </span>
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
      </section>

      {/* Footer */}
      <footer
        className="border-t border-orange-400/30 bg-black/50 p-3"
        role="contentinfo"
        data-maximus-section="status-bar"
      >
        <div className="flex justify-between items-center text-xs text-orange-400/60">
          <div className="flex gap-4">
            <span role="status" aria-live="polite">
              STATUS: {isScanning ? "🟠 SCANNING" : "🟢 READY"}
            </span>
            <span>ENGINE: ZAP Proxy + Custom Modules</span>
            <span>MODE: {scanConfig.scanProfile.toUpperCase()}</span>
          </div>
          <div>WEB ATTACK SURFACE v3.0 | MAXIMUS AI INTEGRATION</div>
        </div>
      </footer>

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
    </article>
  );
};

export default WebAttack;

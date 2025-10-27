import React, { useState, useEffect } from 'react';
import { ScanForm } from './components/ScanForm';
import { ScanResults } from './components/ScanResults';
import { ActiveScans } from './components/ActiveScans';
import { ScanHistory } from './components/ScanHistory';
import { useNetworkRecon } from './hooks/useNetworkRecon';
import { AskMaximusButton } from '../../shared/AskMaximusButton';

/**
 * NETWORK RECON - Network Reconnaissance Tool
 *
 * Varredura de rede com Masscan + Nmap + Service Detection
 * Visual: Hacker cinematográfico com animações de scan em tempo real
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="network-recon"
 * - <header> for tool header with stats
 * - <nav> for tab navigation with ARIA tablist pattern
 * - <section> for content area (scan/active/history)
 * - <footer> for status bar
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="network-recon"
 * - Navigate tabs via role="tablist" and aria-selected
 * - Monitor active scans via data-maximus-status="scanning"
 * - Access scan results via semantic structure
 *
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */
export const NetworkRecon = () => {
  const [activeTab, setActiveTab] = useState('scan'); // 'scan' | 'active' | 'history'
  const {
    scans,
    activeScans,
    currentScan,
    isScanning,
    startScan,
    getScanDetails,
    refreshScans,
  } = useNetworkRecon();

  const [scanConfig, setScanConfig] = useState({
    target: '',
    scanType: 'quick',
    ports: '1-1000',
    serviceDetection: true,
    osDetection: false,
  });

  const tabs = ['scan', 'active', 'history'];

  const handleTabKeyDown = (e) => {
    const currentIndex = tabs.indexOf(activeTab);

    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % tabs.length;
      setActiveTab(tabs[nextIndex]);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      setActiveTab(tabs[prevIndex]);
    } else if (e.key === 'Home') {
      e.preventDefault();
      setActiveTab(tabs[0]);
    } else if (e.key === 'End') {
      e.preventDefault();
      setActiveTab(tabs[tabs.length - 1]);
    }
  };

  const handleStartScan = async () => {
    const result = await startScan(
      scanConfig.target,
      scanConfig.scanType,
      scanConfig.ports
    );

    if (result.success) {
      setActiveTab('active');
    }
  };

  return (
    <article
      className="h-full flex flex-col bg-black/20 backdrop-blur-sm"
      role="article"
      aria-labelledby="network-recon-title"
      data-maximus-tool="network-recon"
      data-maximus-category="offensive"
      data-maximus-status={isScanning ? 'scanning' : 'ready'}>

      {/* Header */}
      <header
        className="border-b border-red-400/30 p-4 bg-gradient-to-r from-red-900/20 to-orange-900/20"
        data-maximus-section="tool-header">
        <div className="flex items-center justify-between">
          <div>
            <h2
              id="network-recon-title"
              className="text-2xl font-bold text-red-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl" aria-hidden="true">🔍</span>
              NETWORK RECONNAISSANCE
            </h2>
            <p className="text-red-400/60 text-sm mt-1">
              Masscan + Nmap + Service Detection | Port 8032
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Ask Maximus AI Button */}
            <AskMaximusButton
              context={{
                type: 'network_scan',
                currentScan: currentScan,
                scans: scans.slice(0, 3),
                activeScans: activeScans
              }}
              prompt={currentScan ? `Analyze these network scan results and suggest next actions` : null}
              size="medium"
              variant="secondary"
            />

            {/* Stats Cards */}
            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">ACTIVE SCANS</div>
              <div className="text-2xl font-bold text-red-400">
                {activeScans.length}
              </div>
            </div>

            <div className="bg-black/50 border border-green-400/30 rounded px-4 py-2">
              <div className="text-green-400 text-xs">COMPLETED</div>
              <div className="text-2xl font-bold text-green-400">
                {scans.filter(s => s.status === 'completed').length}
              </div>
            </div>

            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">TOTAL HOSTS</div>
              <div className="text-2xl font-bold text-red-400">
                {scans.reduce((acc, s) => acc + (s.hosts_found || 0), 0)}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav
          className="flex gap-2 mt-4"
          role="tablist"
          aria-label="Network recon views"
          data-maximus-section="tab-navigation">
          <button
            id="scan-tab"
            role="tab"
            aria-selected={activeTab === 'scan'}
            aria-controls="scan-panel"
            tabIndex={activeTab === 'scan' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('scan')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'scan'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="scan">
            <span aria-hidden="true">🎯</span> NEW SCAN
          </button>

          <button
            id="active-tab"
            role="tab"
            aria-selected={activeTab === 'active'}
            aria-controls="active-panel"
            tabIndex={activeTab === 'active' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('active')}
            className={`px-6 py-2 rounded-t font-bold transition-all relative ${
              activeTab === 'active'
                ? 'bg-orange-400/20 text-orange-400 border-b-2 border-orange-400'
                : 'bg-black/30 text-orange-400/50 hover:text-orange-400'
            }`}
            data-maximus-tab="active">
            <span aria-hidden="true">⚡</span> ACTIVE SCANS
            {activeScans.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-orange-400 text-black text-xs rounded-full w-5 h-5 flex items-center justify-center animate-pulse" aria-label={`${activeScans.length} active scans`}>
                {activeScans.length}
              </span>
            )}
          </button>

          <button
            id="history-tab"
            role="tab"
            aria-selected={activeTab === 'history'}
            aria-controls="history-panel"
            tabIndex={activeTab === 'history' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('history')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'history'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="history">
            <span aria-hidden="true">📚</span> HISTORY
          </button>

          <button
            onClick={refreshScans}
            className="ml-auto px-4 py-2 bg-black/30 text-red-400/70 hover:text-red-400 rounded-t border border-red-400/30 hover:border-red-400 transition-all"
          >
            <span aria-hidden="true">🔄</span> REFRESH
          </button>
        </nav>
      </header>

      {/* Content Area */}
      <section
        className="flex-1 overflow-auto p-6 custom-scrollbar"
        role="region"
        aria-label="Scan content"
        data-maximus-section="content">
        {activeTab === 'scan' && (
          <div id="scan-panel" role="tabpanel" aria-labelledby="scan-tab" tabIndex={0} className="max-w-4xl mx-auto">
            <ScanForm
              config={scanConfig}
              onChange={setScanConfig}
              onSubmit={handleStartScan}
              isScanning={isScanning}
            />

            {currentScan && (
              <div className="mt-6">
                <ScanResults scan={currentScan} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'active' && (
          <div id="active-panel" role="tabpanel" aria-labelledby="active-tab" tabIndex={0}>
            <ActiveScans
              scans={activeScans}
              onSelectScan={getScanDetails}
            />
          </div>
        )}

        {activeTab === 'history' && (
          <div id="history-panel" role="tabpanel" aria-labelledby="history-tab" tabIndex={0}>
            <ScanHistory
              scans={scans.filter(s => s.status === 'completed' || s.status === 'failed')}
              onSelectScan={getScanDetails}
            />
          </div>
        )}
      </section>

      {/* Footer */}
      <footer
        className="border-t border-red-400/30 bg-black/50 p-3"
        role="contentinfo"
        data-maximus-section="status-bar">
        <div className="flex justify-between items-center text-xs text-red-400/60">
          <div className="flex gap-4">
            <span role="status" aria-live="polite">STATUS: {isScanning ? '🟢 SCANNING' : '🔵 READY'}</span>
            <span>ENGINE: Masscan v1.3.2 + Nmap v7.94</span>
            <span>MODE: {scanConfig.scanType.toUpperCase()}</span>
          </div>
          <div>
            NETWORK RECON TOOLKIT v3.0 | MAXIMUS AI INTEGRATION
          </div>
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
          background: rgba(34, 211, 238, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(34, 211, 238, 0.5);
        }
      `}</style>
    </article>
  );
};

export default NetworkRecon;

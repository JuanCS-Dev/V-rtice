import React, { useState } from 'react';
import { SearchForm } from './components/SearchForm';
import { CVEDetails } from './components/CVEDetails';
import { VulnerabilityList } from './components/VulnerabilityList';
import { ExploitDatabase } from './components/ExploitDatabase';
import { useVulnIntel } from './hooks/useVulnIntel';

/**
 * VULN INTEL - Vulnerability Intelligence Tool
 *
 * Busca CVEs, exploits disponíveis, correlação com scans
 * Visual: Database de ameaças com cards impactantes
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="vuln-intel"
 * - <header> for tool header with stats
 * - <nav> for tab navigation with ARIA tablist pattern
 * - <section> for content area (search/exploits/correlation)
 * - <footer> for status bar
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="vuln-intel"
 * - Navigate tabs via role="tablist" and aria-selected
 * - Monitor search status via data-maximus-status
 * - Access CVE details via semantic structure
 *
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */
export const VulnIntel = () => {
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'exploits' | 'correlation'
  const {
    currentCVE,
    vulnerabilities,
    exploits,
    isLoading,
    searchCVE,
    searchVulns,
    getExploits,
    correlateWithScan,
  } = useVulnIntel();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('cve'); // 'cve' | 'product' | 'vendor'

  const tabs = ['search', 'exploits', 'correlation'];

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

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    if (searchType === 'cve') {
      await searchCVE(searchQuery.trim());
      setActiveTab('search');
    } else {
      await searchVulns(searchQuery.trim(), { type: searchType });
      setActiveTab('search');
    }
  };

  return (
    <article
      className="h-full flex flex-col bg-black/20 backdrop-blur-sm"
      role="article"
      aria-labelledby="vuln-intel-title"
      data-maximus-tool="vuln-intel"
      data-maximus-category="offensive"
      data-maximus-status={isLoading ? 'searching' : 'ready'}>

      {/* Header */}
      <header
        className="border-b border-red-400/30 p-4 bg-gradient-to-r from-red-900/20 to-pink-900/20"
        data-maximus-section="tool-header">
        <div className="flex items-center justify-between">
          <div>
            <h2
              id="vuln-intel-title"
              className="text-2xl font-bold text-red-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl" aria-hidden="true">🔐</span>
              VULNERABILITY INTELLIGENCE
            </h2>
            <p className="text-red-400/60 text-sm mt-1">
              CVE Database + Exploit Search + Correlation Engine | Port 8033
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Stats Cards */}
            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">CVE DATABASE</div>
              <div className="text-2xl font-bold text-red-400">
                240K+
              </div>
            </div>

            <div className="bg-black/50 border border-red-400/30 rounded px-4 py-2">
              <div className="text-red-400 text-xs">EXPLOITS</div>
              <div className="text-2xl font-bold text-red-400">
                {exploits.length || '52K+'}
              </div>
            </div>

            <div className="bg-black/50 border border-orange-400/30 rounded px-4 py-2">
              <div className="text-orange-400 text-xs">CRITICAL</div>
              <div className="text-2xl font-bold text-orange-400">
                {vulnerabilities.filter(v => v.severity === 'CRITICAL').length}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav
          className="flex gap-2 mt-4"
          role="tablist"
          aria-label="Vulnerability intelligence views"
          data-maximus-section="tab-navigation">
          <button
            id="search-tab"
            role="tab"
            aria-selected={activeTab === 'search'}
            aria-controls="search-panel"
            tabIndex={activeTab === 'search' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('search')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'search'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="search">
            <span aria-hidden="true">🔍</span> CVE SEARCH
          </button>

          <button
            id="exploits-tab"
            role="tab"
            aria-selected={activeTab === 'exploits'}
            aria-controls="exploits-panel"
            tabIndex={activeTab === 'exploits' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('exploits')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'exploits'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="exploits">
            <span aria-hidden="true">💥</span> EXPLOIT DB
          </button>

          <button
            id="correlation-tab"
            role="tab"
            aria-selected={activeTab === 'correlation'}
            aria-controls="correlation-panel"
            tabIndex={activeTab === 'correlation' ? 0 : -1}
            onKeyDown={handleTabKeyDown}
            onClick={() => setActiveTab('correlation')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'correlation'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
            data-maximus-tab="correlation">
            <span aria-hidden="true">🎯</span> CORRELATION
          </button>
        </nav>
      </header>

      {/* Content Area */}
      <section
        className="flex-1 overflow-auto p-6 custom-scrollbar"
        role="region"
        aria-label="Vulnerability intelligence content"
        data-maximus-section="content">

        {activeTab === 'search' && (
          <div id="search-panel" role="tabpanel" aria-labelledby="search-tab" tabIndex={0} className="max-w-6xl mx-auto space-y-6">
            <SearchForm
              query={searchQuery}
              setQuery={setSearchQuery}
              searchType={searchType}
              setSearchType={setSearchType}
              onSearch={handleSearch}
              isLoading={isLoading}
            />

            {currentCVE && <CVEDetails cve={currentCVE} onGetExploits={getExploits} />}

            {vulnerabilities.length > 0 && (
              <VulnerabilityList vulnerabilities={vulnerabilities} onSelect={searchCVE} />
            )}

            {!currentCVE && vulnerabilities.length === 0 && !isLoading && (
              <div className="text-center py-20">
                <div className="text-6xl mb-4 opacity-50">🔐</div>
                <div className="text-red-400/50 text-xl font-bold">
                  Search CVE Database
                </div>
                <div className="text-red-400/30 text-sm mt-2">
                  Enter a CVE ID, product name, or vendor to begin
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'exploits' && (
          <div id="exploits-panel" role="tabpanel" aria-labelledby="exploits-tab" tabIndex={0}>
            <ExploitDatabase
              exploits={exploits}
              onSearch={getExploits}
              isLoading={isLoading}
            />
          </div>
        )}

        {activeTab === 'correlation' && (
          <div id="correlation-panel" role="tabpanel" aria-labelledby="correlation-tab" tabIndex={0} className="max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-400/30 rounded-lg p-8 text-center">
              <div className="text-6xl mb-4">🎯</div>
              <h3 className="text-red-400 font-bold text-2xl mb-4">
                Scan Correlation Engine
              </h3>
              <p className="text-red-400/60 mb-6">
                Correlate discovered services from network scans with known vulnerabilities
              </p>
              <button
                onClick={() => correlateWithScan('latest')}
                className="px-8 py-3 bg-gradient-to-r from-red-600 to-orange-600 text-white font-bold rounded-lg hover:from-red-500 hover:to-orange-500 transition-all shadow-lg shadow-red-400/20"
              >
                Correlate Latest Scan
              </button>
            </div>
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
            <span role="status" aria-live="polite">STATUS: {isLoading ? '🟡 SEARCHING' : '🟢 READY'}</span>
            <span>SOURCES: NVD, MITRE, ExploitDB, GitHub</span>
            <span>LAST UPDATE: Real-time</span>
          </div>
          <div>
            VULNERABILITY INTELLIGENCE v3.0 | MAXIMUS AI POWERED
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
          background: rgba(168, 85, 247, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(168, 85, 247, 0.5);
        }
      `}</style>
    </article>
  );
};

export default VulnIntel;

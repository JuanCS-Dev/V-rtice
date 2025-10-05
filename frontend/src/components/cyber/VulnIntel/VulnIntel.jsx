import React, { useState } from 'react';
import { SearchForm } from './components/SearchForm';
import { CVEDetails } from './components/CVEDetails';
import { VulnerabilityList } from './components/VulnerabilityList';
import { ExploitDatabase } from './components/ExploitDatabase';
import { useVulnIntel } from './hooks/useVulnIntel';

/**
 * VulnIntel - Vulnerability Intelligence Widget
 *
 * Busca CVEs, exploits disponíveis, correlação com scans
 * Visual: Database de ameaças com cards impactantes
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
    <div className="h-full flex flex-col bg-black/20 backdrop-blur-sm">
      {/* Header */}
      <div className="border-b border-purple-400/30 p-4 bg-gradient-to-r from-purple-900/20 to-pink-900/20">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-purple-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl">🔐</span>
              VULNERABILITY INTELLIGENCE
            </h2>
            <p className="text-purple-400/60 text-sm mt-1">
              CVE Database + Exploit Search + Correlation Engine | Port 8033
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Stats Cards */}
            <div className="bg-black/50 border border-purple-400/30 rounded px-4 py-2">
              <div className="text-purple-400 text-xs">CVE DATABASE</div>
              <div className="text-2xl font-bold text-purple-400">
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
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'search'
                ? 'bg-purple-400/20 text-purple-400 border-b-2 border-purple-400'
                : 'bg-black/30 text-purple-400/50 hover:text-purple-400'
            }`}
          >
            🔍 CVE SEARCH
          </button>

          <button
            onClick={() => setActiveTab('exploits')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'exploits'
                ? 'bg-red-400/20 text-red-400 border-b-2 border-red-400'
                : 'bg-black/30 text-red-400/50 hover:text-red-400'
            }`}
          >
            💥 EXPLOIT DB
          </button>

          <button
            onClick={() => setActiveTab('correlation')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'correlation'
                ? 'bg-cyan-400/20 text-cyan-400 border-b-2 border-cyan-400'
                : 'bg-black/30 text-cyan-400/50 hover:text-cyan-400'
            }`}
          >
            🎯 CORRELATION
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6 custom-scrollbar">
        {activeTab === 'search' && (
          <div className="max-w-6xl mx-auto space-y-6">
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
                <div className="text-purple-400/50 text-xl font-bold">
                  Search CVE Database
                </div>
                <div className="text-purple-400/30 text-sm mt-2">
                  Enter a CVE ID, product name, or vendor to begin
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'exploits' && (
          <ExploitDatabase
            exploits={exploits}
            onSearch={getExploits}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'correlation' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-cyan-900/20 to-blue-900/20 border border-cyan-400/30 rounded-lg p-8 text-center">
              <div className="text-6xl mb-4">🎯</div>
              <h3 className="text-cyan-400 font-bold text-2xl mb-4">
                Scan Correlation Engine
              </h3>
              <p className="text-cyan-400/60 mb-6">
                Correlate discovered services from network scans with known vulnerabilities
              </p>
              <button
                onClick={() => correlateWithScan('latest')}
                className="px-8 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-bold rounded-lg hover:from-cyan-500 hover:to-blue-500 transition-all shadow-lg shadow-cyan-400/20"
              >
                Correlate Latest Scan
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-purple-400/30 bg-black/50 p-3">
        <div className="flex justify-between items-center text-xs text-purple-400/60">
          <div className="flex gap-4">
            <span>STATUS: {isLoading ? '🟡 SEARCHING' : '🟢 READY'}</span>
            <span>SOURCES: NVD, MITRE, ExploitDB, GitHub</span>
            <span>LAST UPDATE: Real-time</span>
          </div>
          <div>
            VULNERABILITY INTELLIGENCE v3.0 | MAXIMUS AI POWERED
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
          background: rgba(168, 85, 247, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(168, 85, 247, 0.5);
        }
      `}</style>
    </div>
  );
};

export default VulnIntel;

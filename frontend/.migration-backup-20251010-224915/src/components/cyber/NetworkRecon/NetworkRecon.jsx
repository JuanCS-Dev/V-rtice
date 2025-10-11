import React, { useState, useEffect } from 'react';
import { ScanForm } from './components/ScanForm';
import { ScanResults } from './components/ScanResults';
import { ActiveScans } from './components/ActiveScans';
import { ScanHistory } from './components/ScanHistory';
import { useNetworkRecon } from './hooks/useNetworkRecon';
import { AskMaximusButton } from '../../shared/AskMaximusButton';

/**
 * NetworkRecon - Network Reconnaissance Widget
 *
 * Varredura de rede com Masscan + Nmap + Service Detection
 * Visual: Hacker cinematográfico com animações de scan em tempo real
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
    <div className="h-full flex flex-col bg-black/20 backdrop-blur-sm">
      {/* Header */}
      <div className="border-b border-cyan-400/30 p-4 bg-gradient-to-r from-cyan-900/20 to-blue-900/20">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-cyan-400 tracking-wider flex items-center gap-3">
              <span className="text-3xl">🔍</span>
              NETWORK RECONNAISSANCE
            </h2>
            <p className="text-cyan-400/60 text-sm mt-1">
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
            <div className="bg-black/50 border border-cyan-400/30 rounded px-4 py-2">
              <div className="text-cyan-400 text-xs">ACTIVE SCANS</div>
              <div className="text-2xl font-bold text-cyan-400">
                {activeScans.length}
              </div>
            </div>

            <div className="bg-black/50 border border-green-400/30 rounded px-4 py-2">
              <div className="text-green-400 text-xs">COMPLETED</div>
              <div className="text-2xl font-bold text-green-400">
                {scans.filter(s => s.status === 'completed').length}
              </div>
            </div>

            <div className="bg-black/50 border border-purple-400/30 rounded px-4 py-2">
              <div className="text-purple-400 text-xs">TOTAL HOSTS</div>
              <div className="text-2xl font-bold text-purple-400">
                {scans.reduce((acc, s) => acc + (s.hosts_found || 0), 0)}
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
                ? 'bg-cyan-400/20 text-cyan-400 border-b-2 border-cyan-400'
                : 'bg-black/30 text-cyan-400/50 hover:text-cyan-400'
            }`}
          >
            🎯 NEW SCAN
          </button>

          <button
            onClick={() => setActiveTab('active')}
            className={`px-6 py-2 rounded-t font-bold transition-all relative ${
              activeTab === 'active'
                ? 'bg-orange-400/20 text-orange-400 border-b-2 border-orange-400'
                : 'bg-black/30 text-orange-400/50 hover:text-orange-400'
            }`}
          >
            ⚡ ACTIVE SCANS
            {activeScans.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-orange-400 text-black text-xs rounded-full w-5 h-5 flex items-center justify-center animate-pulse">
                {activeScans.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`px-6 py-2 rounded-t font-bold transition-all ${
              activeTab === 'history'
                ? 'bg-purple-400/20 text-purple-400 border-b-2 border-purple-400'
                : 'bg-black/30 text-purple-400/50 hover:text-purple-400'
            }`}
          >
            📚 HISTORY
          </button>

          <button
            onClick={refreshScans}
            className="ml-auto px-4 py-2 bg-black/30 text-cyan-400/70 hover:text-cyan-400 rounded-t border border-cyan-400/30 hover:border-cyan-400 transition-all"
          >
            🔄 REFRESH
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

            {currentScan && (
              <div className="mt-6">
                <ScanResults scan={currentScan} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'active' && (
          <ActiveScans
            scans={activeScans}
            onSelectScan={getScanDetails}
          />
        )}

        {activeTab === 'history' && (
          <ScanHistory
            scans={scans.filter(s => s.status === 'completed' || s.status === 'failed')}
            onSelectScan={getScanDetails}
          />
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-cyan-400/30 bg-black/50 p-3">
        <div className="flex justify-between items-center text-xs text-cyan-400/60">
          <div className="flex gap-4">
            <span>STATUS: {isScanning ? '🟢 SCANNING' : '🔵 READY'}</span>
            <span>ENGINE: Masscan v1.3.2 + Nmap v7.94</span>
            <span>MODE: {scanConfig.scanType.toUpperCase()}</span>
          </div>
          <div>
            NETWORK RECON TOOLKIT v3.0 | MAXIMUS AI INTEGRATION
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
          background: rgba(34, 211, 238, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(34, 211, 238, 0.5);
        }
      `}</style>
    </div>
  );
};

export default NetworkRecon;

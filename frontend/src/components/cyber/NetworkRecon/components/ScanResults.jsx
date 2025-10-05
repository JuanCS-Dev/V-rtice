import React, { useState } from 'react';

/**
 * ScanResults - Exibe resultados de scan em tempo real
 */
export const ScanResults = ({ scan }) => {
  const [expandedHost, setExpandedHost] = useState(null);

  if (!scan) return null;

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-400 border-green-400';
      case 'running':
        return 'text-orange-400 border-orange-400 animate-pulse';
      case 'failed':
        return 'text-red-400 border-red-400';
      default:
        return 'text-cyan-400 border-cyan-400';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-400 bg-red-400/20 border-red-400';
      case 'high':
        return 'text-orange-400 bg-orange-400/20 border-orange-400';
      case 'medium':
        return 'text-yellow-400 bg-yellow-400/20 border-yellow-400';
      case 'low':
        return 'text-blue-400 bg-blue-400/20 border-blue-400';
      default:
        return 'text-cyan-400 bg-cyan-400/20 border-cyan-400';
    }
  };

  return (
    <div className="space-y-4">
      {/* Scan Header */}
      <div className={`border-2 rounded-lg p-4 bg-black/30 ${getStatusColor(scan.status)}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">
                {scan.status === 'completed' ? '✅' : scan.status === 'running' ? '⚡' : '❌'}
              </span>
              <div>
                <h3 className="font-bold text-lg">
                  Scan #{scan.scan_id?.slice(0, 8) || 'N/A'}
                </h3>
                <p className="text-sm opacity-70">
                  Target: {scan.target || 'Unknown'}
                </p>
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-sm opacity-70">Status</div>
            <div className="text-xl font-bold uppercase">
              {scan.status}
            </div>
          </div>
        </div>

        {/* Progress Bar (if running) */}
        {scan.status === 'running' && scan.progress !== undefined && (
          <div className="mt-4">
            <div className="flex justify-between text-xs mb-1">
              <span>Progress</span>
              <span>{scan.progress}%</span>
            </div>
            <div className="w-full bg-black/50 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-cyan-400 to-blue-400 h-2 rounded-full transition-all duration-300"
                style={{ width: `${scan.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div className="bg-black/50 rounded p-3 text-center">
            <div className="text-2xl font-bold">{scan.hosts_found || 0}</div>
            <div className="text-xs opacity-70">Hosts Found</div>
          </div>
          <div className="bg-black/50 rounded p-3 text-center">
            <div className="text-2xl font-bold">{scan.open_ports || 0}</div>
            <div className="text-xs opacity-70">Open Ports</div>
          </div>
          <div className="bg-black/50 rounded p-3 text-center">
            <div className="text-2xl font-bold">{scan.services_detected || 0}</div>
            <div className="text-xs opacity-70">Services</div>
          </div>
          <div className="bg-black/50 rounded p-3 text-center">
            <div className="text-2xl font-bold">
              {scan.duration ? `${Math.floor(scan.duration)}s` : '--'}
            </div>
            <div className="text-xs opacity-70">Duration</div>
          </div>
        </div>
      </div>

      {/* Hosts Results */}
      {scan.hosts && scan.hosts.length > 0 && (
        <div>
          <h4 className="text-cyan-400 font-bold mb-3 flex items-center gap-2">
            <span>🖥️</span>
            DISCOVERED HOSTS ({scan.hosts.length})
          </h4>

          <div className="space-y-2">
            {scan.hosts.map((host, idx) => (
              <div
                key={idx}
                className="border border-cyan-400/30 rounded-lg bg-black/20 overflow-hidden"
              >
                {/* Host Header */}
                <button
                  onClick={() => setExpandedHost(expandedHost === idx ? null : idx)}
                  className="w-full p-4 flex items-center justify-between hover:bg-cyan-400/5 transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">
                      {host.status === 'up' ? '🟢' : '🔴'}
                    </div>
                    <div className="text-left">
                      <div className="font-bold text-cyan-400 font-mono">
                        {host.ip || host.hostname}
                      </div>
                      {host.hostname && host.ip && (
                        <div className="text-xs text-cyan-400/50 font-mono">
                          {host.ip}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-sm text-cyan-400/70">
                        {host.open_ports?.length || 0} open ports
                      </div>
                      {host.os_guess && (
                        <div className="text-xs text-cyan-400/50">
                          {host.os_guess}
                        </div>
                      )}
                    </div>
                    <div className="text-cyan-400 text-xl">
                      {expandedHost === idx ? '▼' : '▶'}
                    </div>
                  </div>
                </button>

                {/* Expanded Host Details */}
                {expandedHost === idx && host.open_ports && (
                  <div className="border-t border-cyan-400/30 bg-black/30 p-4">
                    <h5 className="text-cyan-400 font-bold text-sm mb-3">
                      OPEN PORTS & SERVICES
                    </h5>
                    <div className="space-y-2">
                      {host.open_ports.map((port, portIdx) => (
                        <div
                          key={portIdx}
                          className="bg-black/50 border border-cyan-400/20 rounded p-3 flex items-center justify-between"
                        >
                          <div className="flex items-center gap-4">
                            <div className="font-mono font-bold text-cyan-400">
                              {port.port}/{port.protocol}
                            </div>
                            <div className="text-cyan-400/70">
                              {port.service || 'unknown'}
                            </div>
                            {port.version && (
                              <div className="text-cyan-400/50 text-sm">
                                v{port.version}
                              </div>
                            )}
                          </div>

                          {port.vulnerability_score && (
                            <div className={`px-3 py-1 rounded text-xs font-bold border ${getSeverityColor(port.severity)}`}>
                              VULN SCORE: {port.vulnerability_score}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Additional Info */}
                    {(host.mac_address || host.vendor) && (
                      <div className="mt-4 pt-4 border-t border-cyan-400/20">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          {host.mac_address && (
                            <div>
                              <span className="text-cyan-400/50">MAC: </span>
                              <span className="text-cyan-400 font-mono">
                                {host.mac_address}
                              </span>
                            </div>
                          )}
                          {host.vendor && (
                            <div>
                              <span className="text-cyan-400/50">Vendor: </span>
                              <span className="text-cyan-400">
                                {host.vendor}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {scan.status === 'completed' && (!scan.hosts || scan.hosts.length === 0) && (
        <div className="border border-yellow-400/30 rounded-lg p-6 bg-yellow-400/5 text-center">
          <div className="text-4xl mb-3">⚠️</div>
          <div className="text-yellow-400 font-bold">No Hosts Found</div>
          <div className="text-yellow-400/60 text-sm mt-2">
            The target network did not respond or no open ports were detected.
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanResults;

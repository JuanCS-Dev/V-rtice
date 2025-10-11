import React, { useState } from 'react';

/**
 * ScanHistory - Histórico de scans completos
 */
export const ScanHistory = ({ scans, onSelectScan }) => {
  const [filter, setFilter] = useState('all'); // 'all' | 'completed' | 'failed'
  const [sortBy, setSortBy] = useState('date'); // 'date' | 'hosts' | 'duration'

  if (scans.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-6xl mb-4 opacity-50">📚</div>
          <div className="text-purple-400/50 text-xl font-bold">No Scan History</div>
          <div className="text-purple-400/30 text-sm mt-2">
            Completed scans will appear here
          </div>
        </div>
      </div>
    );
  }

  const filteredScans = scans.filter(scan => {
    if (filter === 'all') return true;
    return scan.status === filter;
  });

  const sortedScans = [...filteredScans].sort((a, b) => {
    switch (sortBy) {
      case 'date':
        return new Date(b.completed_at || b.started_at) - new Date(a.completed_at || a.started_at);
      case 'hosts':
        return (b.hosts_found || 0) - (a.hosts_found || 0);
      case 'duration':
        return (b.duration || 0) - (a.duration || 0);
      default:
        return 0;
    }
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded font-bold text-sm transition-all ${
              filter === 'all'
                ? 'bg-purple-400/20 text-purple-400 border border-purple-400'
                : 'bg-black/30 text-purple-400/50 border border-purple-400/20 hover:text-purple-400'
            }`}
          >
            All ({scans.length})
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-4 py-2 rounded font-bold text-sm transition-all ${
              filter === 'completed'
                ? 'bg-green-400/20 text-green-400 border border-green-400'
                : 'bg-black/30 text-green-400/50 border border-green-400/20 hover:text-green-400'
            }`}
          >
            Completed ({scans.filter(s => s.status === 'completed').length})
          </button>
          <button
            onClick={() => setFilter('failed')}
            className={`px-4 py-2 rounded font-bold text-sm transition-all ${
              filter === 'failed'
                ? 'bg-red-400/20 text-red-400 border border-red-400'
                : 'bg-black/30 text-red-400/50 border border-red-400/20 hover:text-red-400'
            }`}
          >
            Failed ({scans.filter(s => s.status === 'failed').length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-purple-400/70 text-sm">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-black/50 border border-purple-400/30 rounded px-3 py-2 text-purple-400 text-sm font-bold focus:outline-none focus:border-purple-400"
          >
            <option value="date">Date</option>
            <option value="hosts">Hosts Found</option>
            <option value="duration">Duration</option>
          </select>
        </div>
      </div>

      {/* Scan List */}
      <div className="space-y-3">
        {sortedScans.map((scan) => (
          <div
            key={scan.scan_id}
            role="button"
            tabIndex={0}
            onClick={() => onSelectScan(scan.scan_id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onSelectScan(scan.scan_id);
              }
            }}
            className={`
              border rounded-lg p-4 cursor-pointer transition-all hover:shadow-lg
              ${
                scan.status === 'completed'
                  ? 'border-green-400/30 bg-green-400/5 hover:border-green-400'
                  : 'border-red-400/30 bg-red-400/5 hover:border-red-400'
              }
            `}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-3xl">
                  {scan.status === 'completed' ? '✅' : '❌'}
                </div>
                <div>
                  <div className="font-bold text-lg">
                    <span className={scan.status === 'completed' ? 'text-green-400' : 'text-red-400'}>
                      {scan.target}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 font-mono">
                    {new Date(scan.completed_at || scan.started_at).toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6">
                {/* Stats */}
                <div className="flex gap-4 text-sm">
                  <div className="text-center">
                    <div className={`font-bold ${scan.status === 'completed' ? 'text-green-400' : 'text-red-400'}`}>
                      {scan.hosts_found || 0}
                    </div>
                    <div className="text-gray-500 text-xs">Hosts</div>
                  </div>
                  <div className="text-center">
                    <div className={`font-bold ${scan.status === 'completed' ? 'text-green-400' : 'text-red-400'}`}>
                      {scan.open_ports || 0}
                    </div>
                    <div className="text-gray-500 text-xs">Ports</div>
                  </div>
                  <div className="text-center">
                    <div className={`font-bold ${scan.status === 'completed' ? 'text-green-400' : 'text-red-400'}`}>
                      {scan.duration ? `${Math.floor(scan.duration)}s` : '--'}
                    </div>
                    <div className="text-gray-500 text-xs">Duration</div>
                  </div>
                </div>

                {/* View Button */}
                <button
                  className={`
                    px-4 py-2 rounded font-bold text-sm border transition-all
                    ${
                      scan.status === 'completed'
                        ? 'border-green-400 text-green-400 hover:bg-green-400/10'
                        : 'border-red-400 text-red-400 hover:bg-red-400/10'
                    }
                  `}
                >
                  VIEW
                </button>
              </div>
            </div>

            {/* Error message for failed scans */}
            {scan.status === 'failed' && scan.error && (
              <div className="mt-3 pt-3 border-t border-red-400/30">
                <div className="text-red-400/70 text-sm">
                  <span className="font-bold">Error: </span>
                  {scan.error}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredScans.length === 0 && (
        <div className="text-center py-12">
          <div className="text-4xl mb-3 opacity-50">🔍</div>
          <div className="text-purple-400/50">
            No scans found with filter: <span className="font-bold">{filter}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanHistory;

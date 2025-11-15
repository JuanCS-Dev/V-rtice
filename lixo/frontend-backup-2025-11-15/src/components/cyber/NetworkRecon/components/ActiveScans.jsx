import React from "react";
import {
  formatDateTime,
  formatDate,
  formatTime,
  getTimestamp,
} from "@/utils/dateHelpers";

/**
 * ActiveScans - Lista de scans em andamento
 */
export const ActiveScans = ({ scans, onSelectScan }) => {
  if (scans.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-6xl mb-4 opacity-50">⚡</div>
          <div className="text-red-400/50 text-xl font-bold">
            No Active Scans
          </div>
          <div className="text-red-400/30 text-sm mt-2">
            Start a new scan to see real-time progress here
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="space-y-4"
      role="region"
      aria-live="polite"
      aria-atomic="false"
    >
      <div className="text-orange-400 font-bold mb-4 flex items-center gap-2">
        <span className="text-2xl animate-pulse" aria-hidden="true">
          ⚡
        </span>
        <span>ACTIVE SCANS ({scans.length})</span>
      </div>

      {scans.map((scan) => (
        <div
          key={scan.scan_id}
          role="button"
          tabIndex={0}
          className="border-2 border-orange-400/50 rounded-lg p-6 bg-gradient-to-br from-orange-900/10 to-red-900/10 cursor-pointer hover:border-orange-400 transition-all"
          onClick={() => onSelectScan(scan.scan_id)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              onSelectScan(scan.scan_id);
            }
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center gap-3">
                <span className="text-2xl animate-spin">⚙️</span>
                <div>
                  <h3 className="text-orange-400 font-bold text-lg">
                    {scan.target || "Unknown Target"}
                  </h3>
                  <p className="text-orange-400/60 text-sm font-mono">
                    ID: {scan.scan_id?.slice(0, 12)}...
                  </p>
                </div>
              </div>
            </div>

            <div className="text-right">
              <div className="text-orange-400/60 text-xs">Status</div>
              <div className="text-orange-400 font-bold text-xl animate-pulse">
                {scan.status?.toUpperCase() || "RUNNING"}
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          {scan.progress !== undefined && (
            <div>
              <div className="flex justify-between text-xs text-orange-400/70 mb-2">
                <span>Scanning Progress</span>
                <span>{scan.progress}%</span>
              </div>
              <div className="w-full bg-black/50 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-orange-400 to-red-400 h-3 rounded-full transition-all duration-500 relative"
                  style={{ width: `${scan.progress}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse" />
                </div>
              </div>
            </div>
          )}

          {/* Live Stats */}
          <div className="grid grid-cols-4 gap-3 mt-4">
            <div className="bg-black/50 border border-orange-400/30 rounded p-3 text-center">
              <div className="text-orange-400 text-xl font-bold">
                {scan.hosts_found || 0}
              </div>
              <div className="text-orange-400/60 text-xs">Hosts</div>
            </div>
            <div className="bg-black/50 border border-orange-400/30 rounded p-3 text-center">
              <div className="text-orange-400 text-xl font-bold">
                {scan.open_ports || 0}
              </div>
              <div className="text-orange-400/60 text-xs">Ports</div>
            </div>
            <div className="bg-black/50 border border-orange-400/30 rounded p-3 text-center">
              <div className="text-orange-400 text-xl font-bold">
                {scan.services_detected || 0}
              </div>
              <div className="text-orange-400/60 text-xs">Services</div>
            </div>
            <div className="bg-black/50 border border-orange-400/30 rounded p-3 text-center">
              <div className="text-orange-400 text-xl font-bold">
                {scan.elapsed_time || "--"}
              </div>
              <div className="text-orange-400/60 text-xs">Elapsed</div>
            </div>
          </div>

          {/* Started At */}
          <div className="mt-4 text-center text-orange-400/50 text-xs">
            Started: {formatDateTime(scan.started_at)}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ActiveScans;

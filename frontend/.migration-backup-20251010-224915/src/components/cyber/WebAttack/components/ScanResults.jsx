import React, { useState } from 'react';

/**
 * ScanResults - Resultados do scan de web attack
 */
export const ScanResults = ({ results }) => {
  const [selectedVuln, setSelectedVuln] = useState(null);

  if (!results) return null;

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: 'red',
      HIGH: 'orange',
      MEDIUM: 'yellow',
      LOW: 'blue',
      INFO: 'gray',
    };
    return colors[severity] || 'gray';
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      CRITICAL: '🔴',
      HIGH: '🟠',
      MEDIUM: '🟡',
      LOW: '🔵',
      INFO: '⚪',
    };
    return icons[severity] || '⚪';
  };

  const getVulnTypeIcon = (type) => {
    const icons = {
      sqli: '💉',
      xss: '🔗',
      ssrf: '🌐',
      lfi: '📁',
      rce: '💻',
      xxe: '📄',
      csrf: '🔄',
      idor: '🔑',
    };
    return icons[type?.toLowerCase()] || '🔧';
  };

  const vulnerabilities = results.vulnerabilities || [];
  const stats = results.stats || {};

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-red-900/30 to-orange-900/30 border-2 border-red-400/40 rounded-lg p-4">
          <div className="text-red-400/60 text-xs mb-1">CRITICAL</div>
          <div className="text-4xl font-bold text-red-400">
            {vulnerabilities.filter(v => v.severity === 'CRITICAL').length}
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-900/30 to-yellow-900/30 border-2 border-orange-400/40 rounded-lg p-4">
          <div className="text-orange-400/60 text-xs mb-1">HIGH</div>
          <div className="text-4xl font-bold text-orange-400">
            {vulnerabilities.filter(v => v.severity === 'HIGH').length}
          </div>
        </div>

        <div className="bg-gradient-to-br from-yellow-900/30 to-blue-900/30 border-2 border-yellow-400/40 rounded-lg p-4">
          <div className="text-yellow-400/60 text-xs mb-1">MEDIUM</div>
          <div className="text-4xl font-bold text-yellow-400">
            {vulnerabilities.filter(v => v.severity === 'MEDIUM').length}
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-900/30 to-gray-900/30 border-2 border-blue-400/40 rounded-lg p-4">
          <div className="text-blue-400/60 text-xs mb-1">LOW / INFO</div>
          <div className="text-4xl font-bold text-blue-400">
            {vulnerabilities.filter(v => v.severity === 'LOW' || v.severity === 'INFO').length}
          </div>
        </div>
      </div>

      {/* Scan Metadata */}
      <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-400/30 rounded-lg p-4">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="text-orange-400/60 text-xs mb-1">TARGET</div>
            <div className="text-orange-400 font-mono text-sm">{results.url || 'N/A'}</div>
          </div>
          <div>
            <div className="text-orange-400/60 text-xs mb-1">SCAN TIME</div>
            <div className="text-orange-400 font-bold">{results.scan_time || stats.scan_time || 'N/A'}</div>
          </div>
          <div>
            <div className="text-orange-400/60 text-xs mb-1">REQUESTS</div>
            <div className="text-orange-400 font-bold">{results.total_requests || stats.total_requests || 0}</div>
          </div>
          <div>
            <div className="text-orange-400/60 text-xs mb-1">PROFILE</div>
            <div className="text-orange-400 font-bold">{results.scan_profile?.toUpperCase() || 'FULL'}</div>
          </div>
        </div>
      </div>

      {/* Vulnerabilities List */}
      {vulnerabilities.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-orange-400 flex items-center gap-2">
              <span className="text-2xl">🔍</span>
              VULNERABILITIES DETECTED
            </h3>
            <div className="bg-black/50 border border-orange-400/30 rounded px-4 py-2">
              <span className="text-orange-400 font-bold">{vulnerabilities.length}</span>
              <span className="text-orange-400/60 text-sm ml-1">total</span>
            </div>
          </div>

          {vulnerabilities.map((vuln, idx) => {
            const severity = vuln.severity || 'INFO';
            const color = getSeverityColor(severity);
            const icon = getSeverityIcon(severity);
            const typeIcon = getVulnTypeIcon(vuln.type);

            return (
              <div
                key={idx}
                onClick={() => setSelectedVuln(selectedVuln === idx ? null : idx)}
                className={`
                  bg-gradient-to-r from-${color}-900/20 to-${color}-900/10 border-2 border-${color}-400/30
                  rounded-lg p-4 hover:border-${color}-400 transition-all cursor-pointer
                  ${selectedVuln === idx ? 'ring-2 ring-' + color + '-400/50' : ''}
                `}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-3 flex-1">
                    <span className="text-3xl">{typeIcon}</span>
                    <div className="flex-1">
                      <div className={`text-${color}-400 font-bold text-lg mb-1`}>
                        {vuln.title || vuln.name || 'Vulnerability Detected'}
                      </div>
                      <div className="text-orange-400/60 text-sm">
                        {vuln.url || vuln.location || 'N/A'}
                      </div>
                    </div>
                  </div>

                  <div className={`flex items-center gap-2 px-3 py-1 bg-${color}-400/20 border border-${color}-400 rounded-full`}>
                    <span>{icon}</span>
                    <span className={`text-${color}-400 font-bold text-sm`}>
                      {severity}
                    </span>
                  </div>
                </div>

                {/* Description */}
                <p className={`text-${color}-400/70 text-sm mb-3`}>
                  {vuln.description || 'No description available'}
                </p>

                {/* Expanded Details */}
                {selectedVuln === idx && (
                  <div className="mt-4 pt-4 border-t border-orange-400/20 space-y-3">
                    {/* Evidence */}
                    {vuln.evidence && (
                      <div className="bg-black/50 border border-orange-400/20 rounded p-3">
                        <div className="text-orange-400/60 text-xs font-bold mb-2">EVIDENCE</div>
                        <pre className="text-orange-400 text-xs font-mono overflow-x-auto">
                          {vuln.evidence}
                        </pre>
                      </div>
                    )}

                    {/* Payload */}
                    {vuln.payload && (
                      <div className="bg-black/50 border border-red-400/20 rounded p-3">
                        <div className="text-red-400/60 text-xs font-bold mb-2">PAYLOAD</div>
                        <pre className="text-red-400 text-xs font-mono overflow-x-auto">
                          {vuln.payload}
                        </pre>
                      </div>
                    )}

                    {/* Remediation */}
                    {vuln.remediation && (
                      <div className="bg-black/50 border border-green-400/20 rounded p-3">
                        <div className="text-green-400/60 text-xs font-bold mb-2">REMEDIATION</div>
                        <p className="text-green-400/80 text-sm">
                          {vuln.remediation}
                        </p>
                      </div>
                    )}

                    {/* References */}
                    {vuln.references && vuln.references.length > 0 && (
                      <div className="bg-black/50 border border-cyan-400/20 rounded p-3">
                        <div className="text-cyan-400/60 text-xs font-bold mb-2">REFERENCES</div>
                        <div className="space-y-1">
                          {vuln.references.map((ref, refIdx) => (
                            <a
                              key={refIdx}
                              href={ref}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block text-cyan-400/80 text-xs hover:text-cyan-400 transition-all"
                            >
                              {ref}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Expand Toggle */}
                <div className={`text-${color}-400/50 text-xs text-center mt-3`}>
                  {selectedVuln === idx ? '▲ Click to collapse' : '▼ Click for details'}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-20">
          <div className="text-6xl mb-4 opacity-50">✅</div>
          <div className="text-green-400 text-xl font-bold">
            No Vulnerabilities Detected
          </div>
          <div className="text-green-400/60 text-sm mt-2">
            The target appears to be secure against tested attacks
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanResults;

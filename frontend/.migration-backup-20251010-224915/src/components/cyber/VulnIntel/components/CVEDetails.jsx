import React from 'react';

/**
 * CVEDetails - Detalhes completos de uma CVE
 */
export const CVEDetails = ({ cve, onGetExploits }) => {
  if (!cve) return null;

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: 'red',
      HIGH: 'orange',
      MEDIUM: 'yellow',
      LOW: 'blue',
      NONE: 'gray',
    };
    return colors[severity] || 'gray';
  };

  const severityColor = getSeverityColor(cve.severity);
  const cvssScore = cve.cvss_score || cve.base_score || 0;

  return (
    <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border-2 border-purple-400/40 rounded-lg overflow-hidden shadow-2xl shadow-purple-400/20">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 p-6 border-b border-purple-400/30">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-4 mb-2">
              <h3 className="text-3xl font-bold text-purple-400 font-mono tracking-wider">
                {cve.cve_id || cve.id}
              </h3>
              <div className={`px-4 py-1 bg-${severityColor}-400/20 border-2 border-${severityColor}-400 rounded-full flex items-center gap-2 animate-pulse`}>
                <span className={`text-${severityColor}-400 font-bold text-sm`}>
                  {cve.severity || 'UNKNOWN'}
                </span>
              </div>
            </div>
            <p className="text-purple-400/80 text-lg">
              {cve.description || cve.summary || 'No description available'}
            </p>
          </div>

          {/* CVSS Score */}
          <div className="ml-6 bg-black/50 border-2 border-purple-400/40 rounded-lg p-4 text-center min-w-[120px]">
            <div className="text-purple-400/60 text-xs font-bold mb-1">CVSS SCORE</div>
            <div className={`text-4xl font-bold text-${severityColor}-400`}>
              {cvssScore.toFixed(1)}
            </div>
            <div className="text-purple-400/40 text-xs mt-1">/ 10.0</div>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-6 space-y-6">
        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-black/30 border border-purple-400/20 rounded p-3">
            <div className="text-purple-400/60 text-xs mb-1">PUBLISHED</div>
            <div className="text-purple-400 font-bold text-sm">
              {cve.published_date || cve.published || 'N/A'}
            </div>
          </div>

          <div className="bg-black/30 border border-purple-400/20 rounded p-3">
            <div className="text-purple-400/60 text-xs mb-1">LAST MODIFIED</div>
            <div className="text-purple-400 font-bold text-sm">
              {cve.modified_date || cve.last_modified || 'N/A'}
            </div>
          </div>

          <div className="bg-black/30 border border-purple-400/20 rounded p-3">
            <div className="text-purple-400/60 text-xs mb-1">ATTACK VECTOR</div>
            <div className="text-purple-400 font-bold text-sm">
              {cve.attack_vector || cve.access?.vector || 'N/A'}
            </div>
          </div>

          <div className="bg-black/30 border border-purple-400/20 rounded p-3">
            <div className="text-purple-400/60 text-xs mb-1">ATTACK COMPLEXITY</div>
            <div className="text-purple-400 font-bold text-sm">
              {cve.attack_complexity || cve.access?.complexity || 'N/A'}
            </div>
          </div>
        </div>

        {/* CWE Information */}
        {(cve.cwe_id || cve.cwe) && (
          <div className="bg-gradient-to-r from-cyan-900/20 to-blue-900/20 border border-cyan-400/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">🎯</span>
              <h4 className="text-cyan-400 font-bold">WEAKNESS TYPE</h4>
            </div>
            <div className="font-mono text-cyan-400/80">
              {cve.cwe_id || cve.cwe}
            </div>
          </div>
        )}

        {/* Affected Products */}
        {(cve.affected_products || cve.vulnerable_products) && (
          <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-400/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">📦</span>
              <h4 className="text-orange-400 font-bold">AFFECTED PRODUCTS</h4>
            </div>
            <div className="space-y-2">
              {(cve.affected_products || cve.vulnerable_products || []).map((product, idx) => (
                <div
                  key={idx}
                  className="bg-black/30 border border-orange-400/20 rounded px-3 py-2 text-orange-400/80 font-mono text-sm"
                >
                  {typeof product === 'string' ? product : `${product.vendor} ${product.product} ${product.version || ''}`}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* References */}
        {cve.references && cve.references.length > 0 && (
          <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 border border-purple-400/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">🔗</span>
              <h4 className="text-purple-400 font-bold">REFERENCES</h4>
            </div>
            <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
              {cve.references.map((ref, idx) => (
                <a
                  key={idx}
                  href={typeof ref === 'string' ? ref : ref.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block bg-black/30 border border-purple-400/20 rounded px-3 py-2 text-purple-400/80 text-sm hover:border-purple-400 hover:text-purple-400 transition-all"
                >
                  {typeof ref === 'string' ? ref : ref.url}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Action Button */}
        <div className="flex justify-center pt-4">
          <button
            onClick={() => onGetExploits(cve.cve_id || cve.id)}
            className="px-8 py-4 bg-gradient-to-r from-red-600 to-orange-600 text-white font-bold text-lg rounded-lg hover:from-red-500 hover:to-orange-500 transition-all shadow-lg shadow-red-400/30 flex items-center gap-3"
          >
            <span className="text-2xl">💥</span>
            SEARCH AVAILABLE EXPLOITS
          </button>
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(168, 85, 247, 0.3);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(168, 85, 247, 0.5);
        }
      `}</style>
    </div>
  );
};

export default CVEDetails;

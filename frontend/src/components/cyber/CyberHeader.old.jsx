// /home/juan/vertice-dev/frontend/src/components/cyber/CyberHeader.jsx

import React from 'react';

const CyberHeader = ({ currentTime, setCurrentView, activeModule, setActiveModule }) => {
  const modules = [
    { id: 'overview', name: 'OVERVIEW', icon: '🛡️' },
    { id: 'aurora', name: 'AURORA AI HUB', icon: '🤖', isAI: true },
    { id: 'exploits', name: 'CVE EXPLOITS', icon: '🐛', isWorldClass: true },
    { id: 'domain', name: 'DOMAIN INTEL', icon: '🌐' },
    { id: 'ip', name: 'IP ANALYSIS', icon: '🎯' },
    { id: 'network', name: 'NET MONITOR', icon: '📡' },
    { id: 'nmap', name: 'NMAP SCAN', icon: '⚡' },
    { id: 'threats', name: 'THREAT MAP', icon: '🗺️' },
    { id: 'vulnscan', name: 'VULN SCANNER', icon: '💥', isOffensive: true },
    { id: 'socialeng', name: 'SOCIAL ENG', icon: '🎭', isOffensive: true }
  ];

  return (
    <header className="relative border-b border-cyan-400/30 bg-black/50 backdrop-blur-sm">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 border-2 border-cyan-400 rounded-lg flex items-center justify-center bg-cyan-400/10">
            <span className="text-cyan-400 font-bold text-xl">C</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-cyan-400 tracking-wider">
              CYBER SECURITY OPS
            </h1>
            <p className="text-cyan-400/70 text-sm tracking-widest">CENTRO DE OPERAÇÕES DIGITAIS</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setCurrentView('operator')}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-black font-bold px-4 py-2 rounded-lg transition-all duration-300 tracking-wider text-sm"
          >
            ← VOLTAR VÉRTICE
          </button>
          
          <div className="text-right">
            <div className="text-cyan-400 font-bold text-lg">
              {currentTime.toLocaleTimeString()}
            </div>
            <div className="text-cyan-400/70 text-sm">
              {currentTime.toLocaleDateString('pt-BR')}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Modules */}
      <div className="px-4 py-2 bg-black/30">
        <div className="flex flex-wrap gap-2 justify-center items-center">
          {modules.map((module) => (
            <button
              key={module.id}
              onClick={() => setActiveModule(module.id)}
              className={`px-3 py-1.5 rounded font-medium text-xs transition-all ${
                activeModule === module.id
                  ? module.isAI
                    ? 'bg-gradient-to-r from-black via-green-900/40 to-green-700/60 text-gray-200 border border-green-700/30'
                    : module.isWorldClass
                      ? 'bg-gradient-to-r from-cyan-900/40 to-purple-900/40 text-gray-200 border border-cyan-400/50'
                      : module.isOffensive
                        ? 'bg-red-950/30 text-red-400 border border-red-900/50'
                        : 'bg-cyan-950/30 text-cyan-400 border border-cyan-900/50'
                  : module.isAI
                    ? 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-green-700/30'
                    : module.isWorldClass
                      ? 'bg-black/30 text-cyan-400/70 border border-gray-700 hover:border-cyan-400/50'
                      : module.isOffensive
                        ? 'bg-black/30 text-red-400/70 border border-gray-700 hover:border-red-900/30'
                        : 'bg-black/30 text-gray-400 border border-gray-700 hover:border-cyan-900/30'
              }`}
            >
              <span className="mr-1.5 text-[10px]">{module.icon}</span>
              {module.name}
              {module.isOffensive && <span className="ml-1.5 text-[10px]">⚠️</span>}
              {module.isWorldClass && <span className="ml-1.5 text-[10px]">⭐</span>}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};

export default CyberHeader;

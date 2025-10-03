import React from 'react';

const OSINTHeader = ({ currentTime, setCurrentView, activeModule, setActiveModule }) => {
  const modules = [
    { id: 'overview', name: 'OVERVIEW', icon: '🛡️' },
    { id: 'aurora', name: 'MAXIMUS AI', icon: '🧠', isAI: true },
    { id: 'socialmedia', name: 'SOCIAL MEDIA', icon: '🔎', isWorldClass: true },
    { id: 'breachdata', name: 'BREACH DATA', icon: '💾', isWorldClass: true },
    { id: 'username', name: 'USERNAME', icon: '👤' },
    { id: 'email', name: 'EMAIL', icon: '📧' },
    { id: 'phone', name: 'PHONE', icon: '📱' },
    { id: 'social', name: 'SOCIAL', icon: '🌐' },
    { id: 'google', name: 'GOOGLE OSINT', icon: '🌎' },
    { id: 'darkweb', name: 'DARK WEB', icon: '🌑' },
    { id: 'reports', name: 'REPORTS', icon: '📊' }
  ];

  return (
    <header className="relative border-b border-purple-400/30 bg-black/50 backdrop-blur-sm">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 border-2 border-purple-400 rounded-lg flex items-center justify-center bg-purple-400/10">
            <span className="text-purple-400 font-bold text-xl">🔍</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-purple-400 tracking-wider">
              OSINT INTELLIGENCE
            </h1>
            <p className="text-purple-400/70 text-sm tracking-widest">MAXIMUS AI POWERED • ADVANCED THREAT HUNTING</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={() => setCurrentView('main')}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-black font-bold px-4 py-2 rounded-lg transition-all duration-300 tracking-wider text-sm"
          >
            ← VOLTAR VÉRTICE
          </button>

          <div className="text-right">
            <div className="text-purple-400 font-bold text-lg">
              {currentTime.toLocaleTimeString()}
            </div>
            <div className="text-purple-400/70 text-sm">
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
                      ? 'bg-gradient-to-r from-purple-900/40 to-pink-900/40 text-gray-200 border border-purple-400/50'
                      : 'bg-blue-950/30 text-blue-400 border border-blue-900/50'
                  : module.isAI
                    ? 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:border-green-700/30'
                    : module.isWorldClass
                      ? 'bg-black/30 text-purple-400/70 border border-gray-700 hover:border-purple-400/50'
                      : 'bg-black/30 text-gray-400 border border-gray-700 hover:border-blue-900/30'
              }`}
            >
              <span className="mr-1.5 text-[10px]">{module.icon}</span>
              {module.name}
              {module.isWorldClass && <span className="ml-1.5 text-[10px]">⭐</span>}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};

export default OSINTHeader;
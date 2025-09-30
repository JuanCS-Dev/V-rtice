import React from 'react';

const OSINTHeader = ({ currentTime, setCurrentView, activeModule, setActiveModule }) => {
  const modules = [
    { id: 'overview', name: 'OVERVIEW', icon: '🛡️' },
    { id: 'aurora', name: 'AURORA AI', icon: '🧠', isAI: true },
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
            <p className="text-purple-400/70 text-sm tracking-widest">AURORA AI POWERED • ADVANCED THREAT HUNTING</p>
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

      {/* Navigation Modules - AI FIRST */}
      <div className="p-4 bg-gradient-to-r from-purple-900/20 to-blue-900/20">
        <div className="flex flex-col space-y-3">
          {/* AI MODULE - DESTAQUE ESPECIAL */}
          <div className="flex justify-center">
            <button
              onClick={() => setActiveModule('aurora')}
              className={`px-8 py-4 rounded-xl font-bold text-base tracking-wider transition-all duration-300 transform hover:scale-105 ${
                activeModule === 'aurora'
                  ? 'bg-gradient-to-r from-purple-600 via-pink-600 to-purple-600 text-white shadow-2xl shadow-purple-500/50 animate-pulse'
                  : 'bg-gradient-to-r from-purple-900/40 via-pink-900/40 to-purple-900/40 text-purple-300 border-2 border-purple-500/50 hover:border-purple-400'
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-3xl">🧠</span>
                <div className="text-left">
                  <div className="text-lg font-extrabold">AURORA AI BRAIN</div>
                  <div className="text-xs opacity-90">Investigação Autônoma • Deep Learning</div>
                </div>
                <span className="text-2xl animate-pulse">✨</span>
              </div>
            </button>
          </div>

          {/* OUTROS MÓDULOS */}
          <div className="flex flex-wrap gap-2 justify-center">
            {modules.filter(m => !m.isAI).map((module) => (
              <button
                key={module.id}
                onClick={() => setActiveModule(module.id)}
                className={`px-3 py-2 rounded-lg font-bold text-xs tracking-wider transition-all duration-300 ${
                  activeModule === module.id
                    ? 'bg-purple-400/20 text-purple-400 border border-purple-400/50'
                    : 'bg-black/30 text-purple-400/70 border border-purple-400/20 hover:bg-purple-400/10 hover:text-purple-400'
                }`}
              >
                <span className="mr-1">{module.icon}</span>
                {module.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
};

export default OSINTHeader;
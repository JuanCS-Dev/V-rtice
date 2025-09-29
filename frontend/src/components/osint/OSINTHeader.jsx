import React from 'react';

const OSINTHeader = ({ currentTime, setCurrentView, activeModule, setActiveModule }) => {
  const modules = [
    { id: 'overview', name: 'OVERVIEW', icon: '🛡️' },
    { id: 'aurora', name: 'AURORA AI', icon: '🧠' },
    { id: 'username', name: 'USERNAME', icon: '👤' },
    { id: 'email', name: 'EMAIL', icon: '📧' },
    { id: 'phone', name: 'PHONE', icon: '📱' },
    { id: 'social', name: 'SOCIAL', icon: '🌐' },
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

      {/* Navigation Modules */}
      <div className="p-4 bg-gradient-to-r from-purple-900/20 to-blue-900/20">
        <div className="flex space-x-2">
          {modules.map((module) => (
            <button
              key={module.id}
              onClick={() => setActiveModule(module.id)}
              className={`px-4 py-2 rounded-lg font-bold text-xs tracking-wider transition-all duration-300 ${
                activeModule === module.id
                  ? 'bg-purple-400/20 text-purple-400 border border-purple-400/50'
                  : 'bg-black/30 text-purple-400/70 border border-purple-400/20 hover:bg-purple-400/10 hover:text-purple-400'
              }`}
            >
              <span className="mr-2">{module.icon}</span>
              {module.name}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};

export default OSINTHeader;
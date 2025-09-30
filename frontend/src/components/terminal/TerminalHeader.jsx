import React from 'react';

const TerminalHeader = ({
  user,
  theme,
  onThemeChange,
  isFullscreen,
  onToggleFullscreen,
  themes,
  setCurrentView
}) => {
  const modules = [
    { id: 'terminal', name: 'TERMINAL', icon: '⚡' },
    { id: 'system', name: 'SYSTEM', icon: '🖥️' },
    { id: 'logs', name: 'LOGS', icon: '📋' },
    { id: 'network', name: 'NETWORK', icon: '🌐' },
    { id: 'processes', name: 'PROCESSES', icon: '⚙️' },
    { id: 'resources', name: 'RESOURCES', icon: '📊' }
  ];

  return (
    <header className="relative border-b border-green-400/30 bg-black/50 backdrop-blur-sm">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 border-2 border-green-400 rounded-lg flex items-center justify-center bg-green-400/10">
            <span className="text-green-400 font-bold text-xl">⚡</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-green-400 tracking-wider">
              VÉRTICE TERMINAL
            </h1>
            <p className="text-green-400/70 text-sm tracking-widest">CENTRO DE COMANDO E CONTROLE</p>
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
            <div className="text-green-400 font-bold text-lg">
              {new Date().toLocaleTimeString()}
            </div>
            <div className="text-green-400/70 text-sm">
              {new Date().toLocaleDateString('pt-BR')}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Modules */}
      <div className="p-4 bg-gradient-to-r from-green-900/20 to-emerald-900/20">
        <div className="flex justify-between items-center">
          <div className="flex space-x-2">
            {modules.map((module) => (
              <button
                key={module.id}
                className="px-4 py-2 rounded-lg font-bold text-xs tracking-wider transition-all duration-300 bg-black/30 text-green-400/70 border border-green-400/20 hover:bg-green-400/10 hover:text-green-400"
              >
                <span className="mr-2">{module.icon}</span>
                {module.name}
              </button>
            ))}
          </div>

          {/* Terminal Controls */}
          <div className="flex items-center space-x-4">
            {/* Theme Selector */}
            <div className="flex items-center space-x-2">
              <span className="text-green-400/70 text-xs">THEME:</span>
              <select
                value={theme}
                onChange={(e) => onThemeChange(e.target.value)}
                className="bg-black/70 border border-green-400/50 text-green-400 px-2 py-1 rounded text-xs focus:outline-none focus:border-green-400"
              >
                {Object.keys(themes).map(themeName => (
                  <option key={themeName} value={themeName}>
                    {themeName.charAt(0).toUpperCase() + themeName.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Status indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-green-400/70 text-xs">ONLINE</span>
            </div>

            {/* User info */}
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-green-400/70">USER:</span>
              <span className="text-green-400">{user?.email?.split('@')[0]}</span>
            </div>

            {/* Fullscreen toggle */}
            <button
              onClick={onToggleFullscreen}
              className="p-2 rounded hover:bg-green-400/10 text-green-400/70 hover:text-green-400 transition-colors border border-green-400/20"
              title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            >
              {isFullscreen ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5m11 0L20.5 9M15 9h4.5M15 9V4.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5m11 0L20.5 15M15 15h4.5M15 15v4.5" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TerminalHeader;
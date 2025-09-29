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
  return (
    <div className="h-12 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-4">
      {/* Left side - Terminal info */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
        </div>
        <div className="flex items-center space-x-2 text-sm">
          <span className="text-cyan-400 font-bold">VÉRTICE</span>
          <span className="text-gray-500">|</span>
          <span className="text-green-400">Terminal Dashboard</span>
        </div>

        {/* Botão Voltar */}
        <button
          onClick={() => setCurrentView && setCurrentView('main')}
          className="flex items-center space-x-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 hover:text-white transition-colors"
          title="Voltar ao Dashboard Principal"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Voltar</span>
        </button>
      </div>

      {/* Center - Status indicators */}
      <div className="flex items-center space-x-6 text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-gray-300">Connected</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-gray-400">Services:</span>
          <span className="text-green-400">Online</span>
        </div>
      </div>

      {/* Right side - Controls */}
      <div className="flex items-center space-x-4">
        {/* Theme Selector */}
        <select
          value={theme}
          onChange={(e) => onThemeChange(e.target.value)}
          className="bg-gray-800 text-green-400 border border-gray-600 rounded px-2 py-1 text-xs focus:outline-none focus:border-green-400"
        >
          {Object.keys(themes).map(themeName => (
            <option key={themeName} value={themeName}>
              {themeName.charAt(0).toUpperCase() + themeName.slice(1)}
            </option>
          ))}
        </select>

        {/* User info */}
        <div className="flex items-center space-x-2 text-xs">
          <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
          <span className="text-gray-300">{user?.email?.split('@')[0]}</span>
        </div>

        {/* Fullscreen toggle */}
        <button
          onClick={onToggleFullscreen}
          className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
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
  );
};

export default TerminalHeader;
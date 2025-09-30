import React, { useState, useRef, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import TerminalEmulator from './TerminalEmulator';
import TerminalHeader from './TerminalHeader';

const TerminalDashboard = ({ setCurrentView }) => {
  const { user } = useContext(AuthContext);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [terminalTheme, setTerminalTheme] = useState('matrix');
  const containerRef = useRef(null);

  const themes = {
    matrix: {
      background: '#000000',
      foreground: '#00ff41',
      cursor: '#00ff41',
      selection: 'rgba(0, 255, 65, 0.3)'
    },
    hacker: {
      background: '#0d1117',
      foreground: '#00d4aa',
      cursor: '#00d4aa',
      selection: 'rgba(0, 212, 170, 0.3)'
    },
    cyberpunk: {
      background: '#1a0d2e',
      foreground: '#e94560',
      cursor: '#e94560',
      selection: 'rgba(233, 69, 96, 0.3)'
    },
    classic: {
      background: '#000000',
      foreground: '#ffffff',
      cursor: '#ffffff',
      selection: 'rgba(255, 255, 255, 0.3)'
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div
      ref={containerRef}
      className={`
        ${isFullscreen ? 'fixed inset-0 z-50' : 'h-screen w-screen'}
        bg-black text-green-400 font-mono flex flex-col
      `}
      style={{
        backgroundColor: themes[terminalTheme].background,
        color: themes[terminalTheme].foreground,
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <TerminalHeader
        user={user}
        theme={terminalTheme}
        onThemeChange={setTerminalTheme}
        isFullscreen={isFullscreen}
        onToggleFullscreen={toggleFullscreen}
        themes={themes}
        setCurrentView={setCurrentView}
      />

      {/* Main Terminal Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <TerminalEmulator
          theme={themes[terminalTheme]}
          isFullscreen={isFullscreen}
        />
      </div>

      {/* Footer Bar */}
      <div className="h-6 bg-gray-900 border-t border-gray-700 flex items-center justify-between px-4 text-xs flex-shrink-0">
        <div className="flex items-center space-x-4">
          <span className="text-green-400">●</span>
          <span>Vértice CLI v2.0</span>
          <span className="text-gray-500">|</span>
          <span>Sessão ativa: {new Date().toLocaleTimeString()}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-gray-400">Theme:</span>
          <span className="text-cyan-400">{terminalTheme}</span>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">User:</span>
          <span className="text-yellow-400">{user?.email}</span>
        </div>
      </div>
    </div>
  );
};

export default TerminalDashboard;
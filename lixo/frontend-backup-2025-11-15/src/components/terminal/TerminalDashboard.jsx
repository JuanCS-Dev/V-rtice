import React, { useState, useRef, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import { DashboardFooter } from '../shared/DashboardFooter';
import TerminalEmulator from './TerminalEmulator';
import TerminalHeader from './TerminalHeader';
import styles from './TerminalDashboard.module.css';

// GAP #59 FIX: Move themes object outside component to prevent recreation on every render
// Boris Cherny Standard: Object recreation causes unnecessary child re-renders
const TERMINAL_THEMES = {
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

const TerminalDashboard = ({ setCurrentView }) => {
  const { user } = useContext(AuthContext);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [terminalTheme, setTerminalTheme] = useState('matrix');
  const containerRef = useRef(null);

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
      className={`${styles.container} ${isFullscreen ? styles.fullscreen : ''}`}
      style={{
        backgroundColor: TERMINAL_THEMES[terminalTheme].background,
        color: TERMINAL_THEMES[terminalTheme].foreground,
      }}
    >
      {/* Header */}
      <TerminalHeader
        user={user}
        theme={terminalTheme}
        onThemeChange={setTerminalTheme}
        isFullscreen={isFullscreen}
        onToggleFullscreen={toggleFullscreen}
        themes={TERMINAL_THEMES}
        setCurrentView={setCurrentView}
      />

      {/* Main Terminal Area */}
      <div className={styles.mainArea}>
        <TerminalEmulator
          theme={TERMINAL_THEMES[terminalTheme]}
          isFullscreen={isFullscreen}
        />
      </div>

      {/* Footer Bar */}
      <DashboardFooter
        moduleName="VÉRTICE CLI"
        classification="CONFIDENCIAL"
        statusItems={[
          { label: 'SESSION', value: 'ACTIVE', online: true },
          { label: 'THEME', value: terminalTheme.toUpperCase(), online: true },
          { label: 'USER', value: user?.email || 'GUEST', online: true }
        ]}
        metricsItems={[
          { label: 'VERSION', value: 'v2.0' }
        ]}
        showTimestamp={true}
      />
    </div>
  );
};

export default TerminalDashboard;
import React, { useState, useRef, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import TerminalEmulator from './TerminalEmulator';
import TerminalHeader from './TerminalHeader';
import styles from './TerminalDashboard.module.css';

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
      className={`${styles.container} ${isFullscreen ? styles.fullscreen : ''}`}
      style={{
        backgroundColor: themes[terminalTheme].background,
        color: themes[terminalTheme].foreground,
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
      <div className={styles.mainArea}>
        <TerminalEmulator
          theme={themes[terminalTheme]}
          isFullscreen={isFullscreen}
        />
      </div>

      {/* Footer Bar */}
      <div className={styles.footer}>
        <div className={styles.footerLeft}>
          <span className={styles.statusDot}></span>
          <span>Vértice CLI v2.0</span>
          <span className={styles.separator}>|</span>
          <span>Sessão ativa: {new Date().toLocaleTimeString()}</span>
        </div>
        <div className={styles.footerRight}>
          <span className={styles.label}>Theme:</span>
          <span className={styles.value}>{terminalTheme}</span>
          <span className={styles.separator}>|</span>
          <span className={styles.label}>User:</span>
          <span className={styles.valueYellow}>{user?.email || 'guest'}</span>
        </div>
      </div>
    </div>
  );
};

export default TerminalDashboard;
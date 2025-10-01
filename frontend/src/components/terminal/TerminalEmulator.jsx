import React, { useEffect, useRef, useContext, useCallback } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { SearchAddon } from '@xterm/addon-search';
import { AuthContext } from '../../contexts/AuthContext';
import { useTerminalHistory } from './hooks/useTerminalHistory';
import { useCommandProcessor } from './hooks/useCommandProcessor';
import { useTerminalInput } from './hooks/useTerminalInput';
import TerminalDisplay from './components/TerminalDisplay';
import '@xterm/xterm/css/xterm.css';

const ASCII_BANNER = `
\x1b[38;2;0;255;255m  VÉRTICE CLI v2.0\x1b[0m
`;

const TerminalEmulator = ({ theme, isFullscreen }) => {
  const terminalRef = useRef(null);
  const terminal = useRef(null);
  const fitAddon = useRef(null);
  const { user } = useContext(AuthContext);

  const getPrompt = useCallback(() => {
    const userName = user?.email?.split('@')[0] || 'user';
    const currentPath = '~'; // This can be moved to a state later
    return `\r\n\x1b[1;32m${userName}@vertice\x1b[0m:\x1b[1;34m${currentPath}\x1b[0m$ `;
  }, [user]);

  const commandHistoryHook = useTerminalHistory();
  const commandProcessorHook = useCommandProcessor(terminal);
  const { handleTerminalInput } = useTerminalInput(terminal, commandHistoryHook, commandProcessorHook, getPrompt());

  useEffect(() => {
    const term = new Terminal({
      cursorBlink: true,
      fontFamily: '"Fira Code", monospace',
      fontSize: 14,
      theme: theme,
      allowTransparency: true,
    });

    fitAddon.current = new FitAddon();
    term.loadAddon(fitAddon.current);
    term.loadAddon(new WebLinksAddon());
    term.loadAddon(new SearchAddon());

    terminal.current = term;

    if (terminalRef.current) {
      term.open(terminalRef.current);
      fitAddon.current.fit();
      term.write(ASCII_BANNER);
      commandProcessorHook.showMainMenu();
      term.write(getPrompt());
    }

    term.onData(handleTerminalInput);

    return () => {
      term.dispose();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  useEffect(() => {
    if (terminal.current) {
      terminal.current.options.theme = theme;
    }
  }, [theme]);

  useEffect(() => {
    if (fitAddon.current) {
      // Debounce fit to avoid race conditions
      setTimeout(() => fitAddon.current.fit(), 150);
    }
  }, [isFullscreen]);

  return <TerminalDisplay ref={terminalRef} />;
};

export default TerminalEmulator;

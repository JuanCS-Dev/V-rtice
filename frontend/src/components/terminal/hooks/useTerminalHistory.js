import { useState, useCallback } from 'react';

/**
 * Manages the command history for the terminal.
 */
export const useTerminalHistory = () => {
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  const addCommandToHistory = useCallback((command) => {
    if (command.trim()) {
      setCommandHistory(prev => [command.trim(), ...prev].slice(0, 100)); // Limit history size
      setHistoryIndex(-1);
    }
  }, []);

  const getPreviousCommand = useCallback(() => {
    if (commandHistory.length === 0) return null;
    const newIndex = historyIndex === -1 ? 0 : Math.min(commandHistory.length - 1, historyIndex + 1);
    setHistoryIndex(newIndex);
    return commandHistory[newIndex];
  }, [commandHistory, historyIndex]);

  const getNextCommand = useCallback(() => {
    if (historyIndex < 0) return null;
    const newIndex = Math.max(-1, historyIndex - 1);
    setHistoryIndex(newIndex);
    return newIndex === -1 ? '' : commandHistory[newIndex];
  }, [commandHistory, historyIndex]);

  const resetHistoryIndex = useCallback(() => {
    setHistoryIndex(-1);
  }, []);

  return {
    commandHistory,
    addCommandToHistory,
    getPreviousCommand,
    getNextCommand,
    resetHistoryIndex
  };
};

export default useTerminalHistory;

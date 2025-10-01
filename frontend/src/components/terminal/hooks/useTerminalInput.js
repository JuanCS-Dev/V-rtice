import { useRef, useCallback } from 'react';

/**
 * Manages user input, including special keys and history navigation.
 */
export const useTerminalInput = (terminal, commandHistoryHook, commandProcessorHook, prompt) => {
  const { getPreviousCommand, getNextCommand, resetHistoryIndex } = commandHistoryHook;
  const { processCommand } = commandProcessorHook;
  const currentCommand = useRef('');

  const handleTerminalInput = useCallback((data) => {
    const term = terminal.current;
    if (!term) return;

    switch (data) {
      case '\r': // Enter
        processCommand(currentCommand.current, () => term.write(prompt));
        currentCommand.current = '';
        resetHistoryIndex();
        break;

      case '\u007F': // Backspace
        if (currentCommand.current.length > 0) {
          currentCommand.current = currentCommand.current.slice(0, -1);
          term.write('\b \b');
        }
        break;

      case '\u001b[A': { // Arrow Up
        const prevCommand = getPreviousCommand();
        if (prevCommand !== null) {
          currentCommand.current = prevCommand;
          term.write(`\r\x1b[K${prompt}${currentCommand.current}`);
        }
        break;
      }

      case '\u001b[B': { // Arrow Down
        const nextCommand = getNextCommand();
        if (nextCommand !== null) {
          currentCommand.current = nextCommand;
          term.write(`\r\x1b[K${prompt}${currentCommand.current}`);
        }
        break;
      }

      case '\u0003': // Ctrl+C
        term.write('^C');
        currentCommand.current = '';
        resetHistoryIndex();
        term.write(`\r\n${prompt}`);
        break;

      default:
        if (data >= ' ' || data === '\t') {
          currentCommand.current += data;
          term.write(data);
        }
        break;
    }
  }, [terminal, getPreviousCommand, getNextCommand, resetHistoryIndex, processCommand, prompt]);

  return { handleTerminalInput };
};

export default useTerminalInput;

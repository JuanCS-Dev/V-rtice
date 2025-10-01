import { useState, useCallback, useContext } from 'react';
import { AuthContext } from '../../../contexts/AuthContext';
import { useTerminalCommands } from '../../../hooks/useTerminalCommands';
import { useNaturalLanguage } from '../../../hooks/useNaturalLanguage';

// All ASCII art and menu text can be moved to a constants file later
const ASCII_BANNER = `
\x1b[38;2;0;255;255m  ██╗   ██╗ ██████╗ ██████╗ ████████╗██╗ ██████╗ ███████╗\x1b[0m
\x1b[38;2;0;230;255m  ██║   ██║ ██╔═══╝ ██╔══██╗╚══██╔══╝██║██╔════╝ ██╔════╝\x1b[0m
\x1b[38;2;0;200;255m  ██║   ██║ ████╗   ██████╔╝   ██║   ██║██║      █████╗  \x1b[0m
\x1b[38;2;0;170;255m  ╚██╗ ██╔╝ ██╔═╝   ██╔══██╗   ██║   ██║██║      ██╔══╝  \x1b[0m
\x1b[38;2;0;140;255m   ╚████╔╝  ███████╗██║  ██║   ██║   ██║╚██████╗ ███████╗\x1b[0m
\x1b[38;2;0;110;255m    ╚═══╝   ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚══════╝\x1b[0m
\x1b[0;37m  Type \x1b[1;32m'menu'\x1b[0m to get started or \x1b[1;32m'help'\x1b[0m for all commands\x1b[0m
`;

const HELP_TEXT = `...`; // Keep it short for brevity, can be expanded
const MAIN_MENU_TEXT = `...`;

/**
 * Manages command processing, menu navigation, and result formatting.
 */
export const useCommandProcessor = (terminal) => {
  const { user, getAuthToken } = useContext(AuthContext);
  const [menuContext, setMenuContext] = useState('main');
  const [isAIChatMode, setIsAIChatMode] = useState(false);
  const [aiChatHistory, setAiChatHistory] = useState([]);

  const { executeCommand } = useTerminalCommands();
  const { processNaturalLanguage } = useNaturalLanguage();

  const write = useCallback((text) => terminal.current?.write(text), [terminal]);
  const writeln = useCallback((text) => terminal.current?.writeln(text), [terminal]);
  const clear = useCallback(() => {
    terminal.current?.clear();
    write(ASCII_BANNER);
  }, [terminal, write]);

  const showHelp = useCallback(() => writeln(HELP_TEXT), [writeln]);
  const showMainMenu = useCallback(() => {
    setMenuContext('main');
    writeln(MAIN_MENU_TEXT);
  }, [writeln]);

  const processAIChat = useCallback(async (input) => {
    // AI chat processing logic from the original file...
    // ...
    writeln(`\r\n\x1b[1;32mAurora>\x1b[0m `);
  }, [/* dependencies */]);

  const processCommand = useCallback(async (command, writePrompt) => {
    writeln(''); // New line after command

    if (isAIChatMode) {
      await processAIChat(command);
      return;
    }

    const [cmd, ...args] = command.split(' ');

    switch (cmd.toLowerCase()) {
      case 'clear':
      case 'cls':
        clear();
        break;
      case 'exit':
        writeln('\x1b[1;31mDesconectando...\x1b[0m');
        break;
      case 'help':
        showHelp();
        break;
      case 'menu':
        showMainMenu();
        break;
      // Other commands...
      default:
        try {
          // Fallback to natural language processing
          const nlpResult = await processNaturalLanguage(command, getAuthToken());
          // ... handle NLP result
          writeln(`NLP Response: ${nlpResult.response}`);
        } catch (e) {
          writeln(`\x1b[1;31mComando não encontrado: ${cmd}\x1b[0m`);
        }
        break;
    }
    writePrompt();
  }, [isAIChatMode, processAIChat, clear, showHelp, showMainMenu, processNaturalLanguage, getAuthToken, writeln]);

  return {
    menuContext, setMenuContext,
    isAIChatMode, setIsAIChatMode,
    aiChatHistory, setAiChatHistory,
    processCommand,
    clear,
    showHelp,
    showMainMenu
  };
};

export default useCommandProcessor;

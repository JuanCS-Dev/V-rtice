import { useState, useCallback, useContext } from "react";
import { AuthContext } from "../../../contexts/AuthContext";
import { useTerminalCommands } from "../../../hooks/useTerminalCommands";
import { useNaturalLanguage } from "../../../hooks/useNaturalLanguage";

// All ASCII art and menu text can be moved to a constants file later
const ASCII_BANNER = `
\x1b[1;32m██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗\x1b[0m
\x1b[1;32m██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝\x1b[0m
\x1b[1;36m██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗\x1b[0m
\x1b[1;36m╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝\x1b[0m
\x1b[1;34m ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗\x1b[0m
\x1b[1;34m  ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝\x1b[0m

\x1b[1;37m        ◈ PROJETO VÉRTICE - CLI v2.0 ◈\x1b[0m
\x1b[0;36m🚀 IA-Powered Security & Intelligence Platform\x1b[0m
\x1b[0;37mType \x1b[1;32m'menu'\x1b[0m to get started or \x1b[1;32m'help'\x1b[0m for all commands\x1b[0m
`;

const HELP_TEXT = `
\x1b[1;36m╔════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║               VÉRTICE CLI - COMANDOS DISPONÍVEIS           ║\x1b[0m
\x1b[1;36m╚════════════════════════════════════════════════════════════╝\x1b[0m

\x1b[1;33m📋 NAVEGAÇÃO:\x1b[0m
  \x1b[1;32mmenu\x1b[0m      - Exibe o menu principal
  \x1b[1;32mclear/cls\x1b[0m - Limpa a tela
  \x1b[1;32mhelp\x1b[0m      - Exibe esta ajuda
  \x1b[1;32mexit\x1b[0m      - Sair do terminal

\x1b[1;33m🔍 MÓDULOS:\x1b[0m
  \x1b[1;32mcyber\x1b[0m     - Ferramentas de Cibersegurança
  \x1b[1;32mosint\x1b[0m     - Open Source Intelligence
  \x1b[1;32maudit\x1b[0m     - Auditoria de Redes e Sistemas

\x1b[1;33m🤖 IA:\x1b[0m
  \x1b[1;32maurora\x1b[0m    - Ativa modo conversação com Maximus AI

\x1b[1;33m💡 DICA:\x1b[0m Digite comandos em linguagem natural!
  Exemplo: "analise o IP 8.8.8.8"
`;

const MAIN_MENU_TEXT = `
\x1b[1;36m╔════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║                    VÉRTICE - MENU PRINCIPAL                ║\x1b[0m
\x1b[1;36m╚════════════════════════════════════════════════════════════╝\x1b[0m

\x1b[1;33m🛡️  CYBER SECURITY\x1b[0m
  \x1b[1;32m1.\x1b[0m IP Intelligence    - Análise profunda de IPs
  \x1b[1;32m2.\x1b[0m Threat Intel       - Inteligência de Ameaças
  \x1b[1;32m3.\x1b[0m Onion Tracer       - Rastreamento Tor/Onion
  \x1b[1;32m4.\x1b[0m Port Scanner       - Varredura de portas

\x1b[1;33m🕵️  OSINT\x1b[0m
  \x1b[1;32m5.\x1b[0m Pessoas            - Investigação de pessoas
  \x1b[1;32m6.\x1b[0m Empresas           - Análise de empresas
  \x1b[1;32m7.\x1b[0m Veículos           - Consulta veicular
  \x1b[1;32m8.\x1b[0m Geolocalização     - Tracking e mapas

\x1b[1;33m⚙️  SISTEMA\x1b[0m
  \x1b[1;32m9.\x1b[0m Status             - Status dos serviços
  \x1b[1;32m10.\x1b[0m Logs               - Visualizar logs

\x1b[1;37mDigite o número ou comando, ou use linguagem natural.\x1b[0m
\x1b[1;37mExemplo: "analisar IP 1.1.1.1" ou "consultar placa ABC1234"\x1b[0m
`;

/**
 * Manages command processing, menu navigation, and result formatting.
 */
export const useCommandProcessor = (terminal) => {
  const { user: _user, getAuthToken } = useContext(AuthContext);
  const [menuContext, setMenuContext] = useState("main");
  const [isAIChatMode, setIsAIChatMode] = useState(false);
  const [aiChatHistory, setAiChatHistory] = useState([]);

  const { executeCommand: _executeCommand } = useTerminalCommands();
  const { processNaturalLanguage } = useNaturalLanguage();

  const write = useCallback(
    (text) => terminal.current?.write(text),
    [terminal],
  );
  const writeln = useCallback(
    (text) => terminal.current?.writeln(text),
    [terminal],
  );
  const clear = useCallback(() => {
    terminal.current?.clear();
    write(ASCII_BANNER);
  }, [terminal, write]);

  const showHelp = useCallback(() => writeln(HELP_TEXT), [writeln]);
  const showMainMenu = useCallback(() => {
    setMenuContext("main");
    writeln(MAIN_MENU_TEXT);
  }, [writeln]);

  const processAIChat = useCallback(
    async (_input) => {
      // AI chat processing logic from the original file...
      // ...
      writeln(`\r\n\x1b[1;32mAurora>\x1b[0m `);
    },
    [writeln],
  );

  const processCommand = useCallback(
    async (command, writePrompt) => {
      writeln(""); // New line after command

      // Handle empty command
      if (!command.trim()) {
        writePrompt();
        return;
      }

      if (isAIChatMode) {
        await processAIChat(command);
        writePrompt();
        return;
      }

      const [cmd, ..._args] = command.trim().split(/\s+/);

      switch (cmd.toLowerCase()) {
        case "clear":
        case "cls":
          clear();
          writePrompt();
          break;
        case "exit":
          writeln("\x1b[1;31mDesconectando...\x1b[0m");
          writePrompt();
          break;
        case "help":
          showHelp();
          writePrompt();
          break;
        case "menu":
          showMainMenu();
          writePrompt();
          break;
        case "cyber":
          writeln("\x1b[1;33m🛡️  CYBER SECURITY MODULE\x1b[0m");
          writeln("  ip-intel    - Análise de IPs");
          writeln("  threat      - Inteligência de Ameaças");
          writeln("  onion       - Rastreamento Tor/Onion");
          writeln("  scanner     - Varredura de portas");
          writePrompt();
          break;
        case "osint":
          writeln("\x1b[1;33m🕵️  OSINT MODULE\x1b[0m");
          writeln("  pessoas     - Investigação de pessoas");
          writeln("  empresas    - Análise de empresas");
          writeln("  veiculos    - Consulta veicular");
          writeln("  geo         - Geolocalização");
          writePrompt();
          break;
        case "aurora":
          writeln("\x1b[1;33m🤖 AURORA AI ACTIVATED\x1b[0m");
          writeln("Digite sua pergunta ou comando:");
          setIsAIChatMode(true);
          writePrompt();
          break;
        default:
          try {
            // Fallback to natural language processing
            writeln("\x1b[0;33mProcessando comando...\x1b[0m");
            const nlpResult = await processNaturalLanguage(
              command,
              getAuthToken(),
            );
            if (nlpResult && nlpResult.response) {
              writeln(`\x1b[1;36m${nlpResult.response}\x1b[0m`);
            } else {
              writeln(`\x1b[1;31mComando não encontrado: ${cmd}\x1b[0m`);
              writeln(
                `Digite \x1b[1;32m'help'\x1b[0m para ver comandos disponíveis`,
              );
            }
          } catch (e) {
            writeln(`\x1b[1;31mComando não encontrado: ${cmd}\x1b[0m`);
            writeln(
              `Digite \x1b[1;32m'help'\x1b[0m para ver comandos disponíveis`,
            );
          }
          writePrompt();
          break;
      }
    },
    [
      isAIChatMode,
      processAIChat,
      clear,
      showHelp,
      showMainMenu,
      processNaturalLanguage,
      getAuthToken,
      writeln,
      setIsAIChatMode,
    ],
  );

  return {
    menuContext,
    setMenuContext,
    isAIChatMode,
    setIsAIChatMode,
    aiChatHistory,
    setAiChatHistory,
    processCommand,
    clear,
    showHelp,
    showMainMenu,
  };
};

export default useCommandProcessor;

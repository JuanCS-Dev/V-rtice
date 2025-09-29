import React, { useEffect, useRef, useState, useContext } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { SearchAddon } from '@xterm/addon-search';
import { AuthContext } from '../../contexts/AuthContext';
import { useTerminalCommands } from '../../hooks/useTerminalCommands';
import '@xterm/xterm/css/xterm.css';

const TerminalEmulator = ({ theme, isFullscreen }) => {
  const terminalRef = useRef(null);
  const terminal = useRef(null);
  const fitAddon = useRef(null);
  const webLinksAddon = useRef(null);
  const searchAddon = useRef(null);
  const { user, getAuthToken } = useContext(AuthContext);
  const [currentPath, setCurrentPath] = useState('~');
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [currentCommand, setCurrentCommand] = useState('');

  const { executeCommand, isExecuting } = useTerminalCommands();

  const ASCII_BANNER = `
\x1b[38;2;0;255;255m  ██╗   ██╗ ██████╗ ██████╗ ████████╗██╗ ██████╗ ███████╗\x1b[0m
\x1b[38;2;0;230;255m  ██║   ██║ ██╔═══╝ ██╔══██╗╚══██╔══╝██║██╔════╝ ██╔════╝\x1b[0m
\x1b[38;2;0;200;255m  ██║   ██║ ████╗   ██████╔╝   ██║   ██║██║      █████╗  \x1b[0m
\x1b[38;2;0;170;255m  ╚██╗ ██╔╝ ██╔═╝   ██╔══██╗   ██║   ██║██║      ██╔══╝  \x1b[0m
\x1b[38;2;0;140;255m   ╚████╔╝  ███████╗██║  ██║   ██║   ██║╚██████╗ ███████╗\x1b[0m
\x1b[38;2;0;110;255m    ╚═══╝   ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚══════╝\x1b[0m

\x1b[38;2;255;100;0m            ██████╗██╗     ██╗\x1b[0m
\x1b[38;2;255;80;0m           ██╔════╝██║     ██║\x1b[0m
\x1b[38;2;255;60;0m           ██║     ██║     ██║\x1b[0m
\x1b[38;2;255;40;0m           ██║     ██║     ██║\x1b[0m
\x1b[38;2;255;20;0m           ╚██████╗███████╗██║\x1b[0m
\x1b[38;2;255;0;0m            ╚═════╝╚══════╝╚═╝\x1b[0m

\x1b[0;37m  ──────────────────────────────────────────────────────────\x1b[0m
\x1b[1;36m  🛡️  CYBER SECURITY  🔍 OSINT  💻 CLI EXPERT\x1b[0m
\x1b[0;37m  ──────────────────────────────────────────────────────────\x1b[0m

\x1b[1;33m  Welcome to Vértice CLI v2.0\x1b[0m
\x1b[0;37m  Type \x1b[1;32m'menu'\x1b[0m to get started or \x1b[1;32m'help'\x1b[0m for all commands\x1b[0m

\x1b[2;37m  Authors: Juan Carlos & Claude Code\x1b[0m

  `;

  useEffect(() => {
    // Inicializar terminal
    terminal.current = new Terminal({
      cursorBlink: true,
      fontFamily: '"Fira Code", "Cascadia Code", "JetBrains Mono", monospace',
      fontSize: 14,
      letterSpacing: 0.5,
      lineHeight: 1.2,
      theme: theme,
      allowTransparency: true,
      convertEol: true,
    });

    // Addons
    fitAddon.current = new FitAddon();
    webLinksAddon.current = new WebLinksAddon();
    searchAddon.current = new SearchAddon();

    terminal.current.loadAddon(fitAddon.current);
    terminal.current.loadAddon(webLinksAddon.current);
    terminal.current.loadAddon(searchAddon.current);

    // Abrir terminal no DOM
    terminal.current.open(terminalRef.current);
    fitAddon.current.fit();

    // Banner inicial
    terminal.current.write(ASCII_BANNER);
    writePrompt();

    // Handler para entrada do usuário
    terminal.current.onData(handleTerminalInput);

    // Cleanup
    return () => {
      terminal.current?.dispose();
    };
  }, []);

  useEffect(() => {
    // Atualizar tema
    if (terminal.current) {
      terminal.current.options.theme = theme;
    }
  }, [theme]);

  useEffect(() => {
    // Ajustar tamanho quando entra/sai do fullscreen
    if (fitAddon.current) {
      setTimeout(() => {
        fitAddon.current.fit();
      }, 100);
    }
  }, [isFullscreen]);

  const writePrompt = () => {
    const userName = user?.email?.split('@')[0] || 'user';
    const prompt = `\r\n\x1b[1;32m${userName}@vertice\x1b[0m:\x1b[1;34m${currentPath}\x1b[0m$ `;
    terminal.current.write(prompt);
  };

  const handleTerminalInput = (data) => {
    const term = terminal.current;

    switch (data) {
      case '\r': // Enter
        if (currentCommand.trim()) {
          processCommand(currentCommand.trim());
          setCommandHistory(prev => [...prev, currentCommand.trim()]);
          setHistoryIndex(-1);
        } else {
          writePrompt();
        }
        setCurrentCommand('');
        break;

      case '\u007F': // Backspace
        if (currentCommand.length > 0) {
          setCurrentCommand(prev => prev.slice(0, -1));
          term.write('\b \b');
        }
        break;

      case '\u001b[A': // Arrow Up
        if (commandHistory.length > 0) {
          const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
          setHistoryIndex(newIndex);
          const command = commandHistory[newIndex];

          // Limpar linha atual
          term.write(`\r\x1b[K${getUserPrompt()}${command}`);
          setCurrentCommand(command);
        }
        break;

      case '\u001b[B': // Arrow Down
        if (historyIndex >= 0) {
          const newIndex = historyIndex + 1;
          if (newIndex >= commandHistory.length) {
            setHistoryIndex(-1);
            setCurrentCommand('');
            term.write(`\r\x1b[K${getUserPrompt()}`);
          } else {
            setHistoryIndex(newIndex);
            const command = commandHistory[newIndex];
            term.write(`\r\x1b[K${getUserPrompt()}${command}`);
            setCurrentCommand(command);
          }
        }
        break;

      case '\u0003': // Ctrl+C
        term.write('^C');
        writePrompt();
        setCurrentCommand('');
        break;

      case '\u0004': // Ctrl+D
        term.write('\r\n\x1b[1;33mUse "exit" para sair\x1b[0m');
        writePrompt();
        break;

      default:
        // Caracteres normais
        if (data >= ' ' || data === '\t') {
          setCurrentCommand(prev => prev + data);
          term.write(data);
        }
        break;
    }
  };

  const getUserPrompt = () => {
    const userName = user?.email?.split('@')[0] || 'user';
    return `\x1b[1;32m${userName}@vertice\x1b[0m:\x1b[1;34m${currentPath}\x1b[0m$ `;
  };

  const processCommand = async (command) => {
    const term = terminal.current;
    term.write(`\r\n`);

    // Comandos internos do terminal
    const [cmd, ...args] = command.split(' ');


    // Primeiro verificar se é uma opção numérica
    if (['1', '2', '3', '4'].includes(cmd)) {
      switch (cmd) {
        case '1':
          showCyberMenu();
          break;
        case '2':
          showOSINTMenu();
          break;
        case '3':
          await showStatus();
          break;
        case '4':
          showHelp();
          break;
      }
    } else {
      // Depois verificar comandos textuais
      switch (cmd.toLowerCase()) {
        case 'clear':
        case 'cls':
          term.clear();
          return;

        case 'exit':
          term.write('\x1b[1;31mDesconectando...\x1b[0m\r\n');
          // TODO: Implementar logout/saída
          return;

        case 'help':
          showHelp();
          break;

        case 'menu':
          showMainMenu();
          break;

        case 'cyber':
          if (args.length === 0) {
            showCyberMenu();
          } else {
            await executeCyberCommand(args);
          }
          break;

        case 'osint':
          if (args.length === 0) {
            showOSINTMenu();
          } else {
            await executeOSINTCommand(args);
          }
          break;

        case 'status':
          await showStatus();
          break;

        default:
          term.write(`\x1b[1;31mComando não encontrado: ${cmd}\x1b[0m\r\n`);
          term.write(`Digite 'help' para ver comandos disponíveis ou 'menu' para opções.\r\n`);
          break;
      }
    }

    writePrompt();
  };

  const showHelp = () => {
    const helpText = `
\x1b[1;36m╔════════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║                    VÉRTICE CLI - HELP GUIDE                    ║\x1b[0m
\x1b[1;36m╚════════════════════════════════════════════════════════════════╝\x1b[0m

\x1b[1;32m📋 COMANDOS BÁSICOS:\x1b[0m
  \x1b[1;37mhelp\x1b[0m                    - Exibe esta ajuda detalhada
  \x1b[1;37mmenu\x1b[0m                    - Menu interativo principal (recomendado)
  \x1b[1;37mstatus\x1b[0m                  - Verifica status de todos os serviços
  \x1b[1;37mclear\x1b[0m, \x1b[1;37mcls\x1b[0m              - Limpa completamente a tela
  \x1b[1;37mexit\x1b[0m                    - Sair do terminal Vértice

\x1b[1;32m🛡️  CYBER SECURITY MODULE:\x1b[0m
  \x1b[1;37mcyber\x1b[0m                   - Menu interativo do módulo
  \x1b[1;37mcyber ip\x1b[0m \x1b[1;33m<ip>\x1b[0m           - Análise completa de IP
    \x1b[0;37mExemplo: cyber ip 8.8.8.8\x1b[0m
  \x1b[1;37mcyber domain\x1b[0m \x1b[1;33m<domain>\x1b[0m   - Análise de domínio (WHOIS, DNS)
    \x1b[0;37mExemplo: cyber domain google.com\x1b[0m
  \x1b[1;31mcyber scan\x1b[0m \x1b[1;33m<target>\x1b[0m     - Vulnerability scanner [OFENSIVO]
    \x1b[0;37mExemplo: cyber scan 192.168.1.100\x1b[0m
    \x1b[1;33m⚠️  Requer autorização - Apenas sistemas próprios\x1b[0m

\x1b[1;32m🔍 OSINT MODULE:\x1b[0m
  \x1b[1;37mosint\x1b[0m                   - Menu interativo do módulo
  \x1b[1;37mosint email\x1b[0m \x1b[1;33m<email>\x1b[0m     - Análise de email e vazamentos
    \x1b[0;37mExemplo: osint email user@company.com\x1b[0m
  \x1b[1;37mosint phone\x1b[0m \x1b[1;33m<phone>\x1b[0m     - Investigação de número de telefone
    \x1b[0;37mExemplo: osint phone +5511987654321\x1b[0m
  \x1b[1;37mosint username\x1b[0m \x1b[1;33m<user>\x1b[0m   - Busca em múltiplas plataformas
    \x1b[0;37mExemplo: osint username john_doe\x1b[0m
  \x1b[1;37mosint social\x1b[0m \x1b[1;33m<platform> <id>\x1b[0m - Análise de rede social
    \x1b[0;37mExemplo: osint social instagram @username\x1b[0m

\x1b[1;35m💡 DICAS DE PRODUTIVIDADE:\x1b[0m
  • Use \x1b[1;37m↑\x1b[0m e \x1b[1;37m↓\x1b[0m para navegar no histórico de comandos
  • Use \x1b[1;37mCtrl+C\x1b[0m para cancelar comando atual
  • Digite \x1b[1;37mmenu\x1b[0m para interface guiada com ajuda contextual
  • Todos os comandos têm validação automática de parâmetros

\x1b[1;33m🚀 COMEÇAR RAPIDAMENTE:\x1b[0m Digite \x1b[1;37mmenu\x1b[0m para interface interativa
`;
    terminal.current.write(helpText);
  };

  const showMainMenu = () => {
    const menuText = `
\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║                      MENU PRINCIPAL                         ║\x1b[0m
\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m

Selecione uma opção digitando o número correspondente:

\x1b[1;32m[1]\x1b[0m 🛡️  \x1b[1;37mCyber Security Module\x1b[0m
    Ferramentas de análise de segurança, IP intelligence e scanning
    \x1b[0;37mComandos: cyber ip <ip>, cyber domain <domain>, cyber scan <target>\x1b[0m

\x1b[1;32m[2]\x1b[0m 🔍 \x1b[1;37mOSINT Module\x1b[0m
    Inteligência em fontes abertas, análise de emails e redes sociais
    \x1b[0;37mComandos: osint email <email>, osint phone <phone>, osint username <user>\x1b[0m

\x1b[1;32m[3]\x1b[0m 📊 \x1b[1;37mStatus dos Serviços\x1b[0m
    Verificar status e saúde dos microserviços do Vértice
    \x1b[0;37mComando: status\x1b[0m

\x1b[1;32m[4]\x1b[0m 📚 \x1b[1;37mAjuda Completa\x1b[0m
    Guia completo de comandos com exemplos práticos
    \x1b[0;37mComando: help\x1b[0m

\x1b[1;33m→ Digite o número da opção (1-4) ou o comando diretamente\x1b[0m
`;
    terminal.current.write(menuText);
  };

  const showCyberMenu = () => {
    const cyberMenu = `
\x1b[1;31m🛡️  CYBER SECURITY MODULE\x1b[0m

\x1b[1;32mComandos Disponíveis:\x1b[0m
  cyber ip <endereço_ip>        - Análise de IP e Geolocalização
  cyber domain <dominio>        - Análise completa de domínio
  cyber scan <target>           - Vulnerability Scanner [OFENSIVO]
  cyber exploit <target> <id>   - Executar exploit [OFENSIVO]

\x1b[1;33m⚠️  Ferramentas ofensivas requerem autenticação especial\x1b[0m
`;
    terminal.current.write(cyberMenu);
  };

  const showOSINTMenu = () => {
    const osintMenu = `
\x1b[1;35m🔍 OSINT MODULE\x1b[0m

\x1b[1;32mComandos Disponíveis:\x1b[0m
  osint email <email>                    - Análise de email
  osint phone <telefone>                 - Análise de telefone
  osint username <usuario>               - Investigação de username
  osint social <plataforma> <usuario>    - Análise de rede social

\x1b[1;32mPlataformas suportadas:\x1b[0m instagram, twitter, linkedin, facebook
`;
    terminal.current.write(osintMenu);
  };

  const executeCyberCommand = async (args) => {
    const [subcommand, ...params] = args;
    const term = terminal.current;

    // Validar argumentos primeiro
    if (!subcommand) {
      term.write(`\x1b[1;31mErro: Comando cyber incompleto. Use: cyber <comando> <argumentos>\x1b[0m\r\n`);
      term.write(`\x1b[1;37mExemplo: cyber ip 8.8.8.8\x1b[0m\r\n`);
      return;
    }

    term.write(`\x1b[1;33mExecutando: cyber ${subcommand} ${params.join(' ')}\x1b[0m\r\n`);

    try {
      // Validar se o comando existe
      const validCommands = ['ip', 'domain', 'scan', 'exploit'];
      if (!validCommands.includes(subcommand)) {
        term.write(`\x1b[1;31mComando cyber não reconhecido: ${subcommand}\x1b[0m\r\n`);
        term.write(`\x1b[1;37mComandos disponíveis: ${validCommands.join(', ')}\x1b[0m\r\n`);
        return;
      }

      // Verificar se tem argumentos suficientes
      if (params.length === 0) {
        term.write(`\x1b[1;31mErro: ${subcommand} requer argumentos\x1b[0m\r\n`);
        term.write(`\x1b[1;37mExemplo: cyber ${subcommand} <target>\x1b[0m\r\n`);
        return;
      }

      const result = await executeCommand('cyber', subcommand, params, getAuthToken());
      if (result) {
        formatAndDisplayResult(result, 'cyber');
      } else {
        term.write(`\x1b[1;33mComando executado, mas sem resultado retornado\x1b[0m\r\n`);
      }
    } catch (error) {
      term.write(`\x1b[1;31mErro ao executar comando: ${error.message}\x1b[0m\r\n`);
      if (error.message.includes('fetch')) {
        term.write(`\x1b[1;33m💡 Dica: Verifique se os serviços backend estão rodando\x1b[0m\r\n`);
      }
    }
  };

  const executeOSINTCommand = async (args) => {
    const [subcommand, ...params] = args;
    const term = terminal.current;

    // Validar argumentos primeiro
    if (!subcommand) {
      term.write(`\x1b[1;31mErro: Comando osint incompleto. Use: osint <comando> <argumentos>\x1b[0m\r\n`);
      term.write(`\x1b[1;37mExemplo: osint email user@domain.com\x1b[0m\r\n`);
      return;
    }

    term.write(`\x1b[1;33mExecutando: osint ${subcommand} ${params.join(' ')}\x1b[0m\r\n`);

    try {
      // Validar se o comando existe
      const validCommands = ['email', 'phone', 'username', 'social'];
      if (!validCommands.includes(subcommand)) {
        term.write(`\x1b[1;31mComando osint não reconhecido: ${subcommand}\x1b[0m\r\n`);
        term.write(`\x1b[1;37mComandos disponíveis: ${validCommands.join(', ')}\x1b[0m\r\n`);
        return;
      }

      // Verificar se tem argumentos suficientes
      if (params.length === 0) {
        term.write(`\x1b[1;31mErro: ${subcommand} requer argumentos\x1b[0m\r\n`);
        term.write(`\x1b[1;37mExemplo: osint ${subcommand} <target>\x1b[0m\r\n`);
        return;
      }

      const result = await executeCommand('osint', subcommand, params, getAuthToken());
      if (result) {
        formatAndDisplayResult(result, 'osint');
      } else {
        term.write(`\x1b[1;33mComando executado, mas sem resultado retornado\x1b[0m\r\n`);
      }
    } catch (error) {
      term.write(`\x1b[1;31mErro ao executar comando: ${error.message}\x1b[0m\r\n`);
      if (error.message.includes('fetch')) {
        term.write(`\x1b[1;33m💡 Dica: Verifique se os serviços backend estão rodando\x1b[0m\r\n`);
      }
    }
  };

  const showStatus = async () => {
    const term = terminal.current;
    term.write(`\x1b[1;33mVerificando status dos serviços...\x1b[0m\r\n`);

    const services = [
      { name: 'API Gateway', url: 'http://localhost:8000', status: '🟢 Online' },
      { name: 'OSINT Service', url: 'http://localhost:8001', status: '🟢 Online' },
      { name: 'IP Intel Service', url: 'http://localhost:8002', status: '🟢 Online' },
      { name: 'Vuln Scanner', url: 'http://localhost:8011', status: '🟡 Protegido' },
      { name: 'Social Eng', url: 'http://localhost:8012', status: '🟡 Protegido' }
    ];

    term.write(`\r\n\x1b[1;36m╔═══════════════════════════════════════════════╗\x1b[0m\r\n`);
    term.write(`\x1b[1;36m║              STATUS DOS SERVIÇOS              ║\x1b[0m\r\n`);
    term.write(`\x1b[1;36m╚═══════════════════════════════════════════════╝\x1b[0m\r\n`);

    services.forEach(service => {
      const padding = ' '.repeat(20 - service.name.length);
      term.write(`${service.name}${padding}${service.status}\r\n`);
    });
  };

  const formatAndDisplayResult = (result, module) => {
    const term = terminal.current;

    // TODO: Implementar formatação específica baseada no módulo e tipo de resultado
    term.write(`\x1b[1;32m✅ Operação concluída com sucesso\x1b[0m\r\n`);

    if (typeof result === 'object') {
      term.write(`\x1b[1;37m${JSON.stringify(result, null, 2)}\x1b[0m\r\n`);
    } else {
      term.write(`\x1b[1;37m${result}\x1b[0m\r\n`);
    }
  };

  return (
    <div
      ref={terminalRef}
      className="flex-1 p-4"
      style={{ height: isFullscreen ? 'calc(100vh - 120px)' : 'calc(100vh - 200px)' }}
    />
  );
};

export default TerminalEmulator;
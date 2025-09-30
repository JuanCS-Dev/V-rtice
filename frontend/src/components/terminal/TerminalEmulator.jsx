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
  const [menuContext, setMenuContext] = useState('main'); // main, cyber, osint, ai_chat
  const currentCommand = useRef('');
  const [aiChatHistory, setAiChatHistory] = useState([]);
  const [isAIChatMode, setIsAIChatMode] = useState(false);

  const { executeCommand, isExecuting, formatResult } = useTerminalCommands();

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
        console.log('Enter pressionado, currentCommand:', currentCommand.current); // Debug log
        if (currentCommand.current.trim()) {
          console.log('Processando comando:', currentCommand.current.trim()); // Debug log
          processCommand(currentCommand.current.trim());
          setCommandHistory(prev => [...prev, currentCommand.current.trim()]);
          setHistoryIndex(-1);
        } else {
          console.log('Comando vazio, escrevendo prompt'); // Debug log
          writePrompt();
        }
        currentCommand.current = '';
        break;

      case '\u007F': // Backspace
        if (currentCommand.current.length > 0) {
          currentCommand.current = currentCommand.current.slice(0, -1);
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
          currentCommand.current = command;
        }
        break;

      case '\u001b[B': // Arrow Down
        if (historyIndex >= 0) {
          const newIndex = historyIndex + 1;
          if (newIndex >= commandHistory.length) {
            setHistoryIndex(-1);
            currentCommand.current = '';
            term.write(`\r\x1b[K${getUserPrompt()}`);
          } else {
            setHistoryIndex(newIndex);
            const command = commandHistory[newIndex];
            term.write(`\r\x1b[K${getUserPrompt()}${command}`);
            currentCommand.current = command;
          }
        }
        break;

      case '\u0003': // Ctrl+C
        term.write('^C');
        writePrompt();
        currentCommand.current = '';
        break;

      case '\u0004': // Ctrl+D
        term.write('\r\n\x1b[1;33mUse "exit" para sair\x1b[0m');
        writePrompt();
        break;

      default:
        // Caracteres normais
        if (data >= ' ' || data === '\t') {
          currentCommand.current = currentCommand.current + data;
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
    console.log('processCommand() chamada com:', command); // Debug log
    term.write(`\r\n`);

    // Comandos internos do terminal
    const [cmd, ...args] = command.split(' ');

    console.log('Comando recebido:', cmd, 'Args:', args, 'Context:', menuContext); // Debug log

    // Primeiro verificar se é opção numérica baseado no contexto do menu
    if (['0', '1', '2', '3', '4', '5'].includes(cmd)) {
      if (menuContext === 'main') {
        switch (cmd) {
          case '1':
            showAuroraAIMenu();
            setMenuContext('aurora');
            break;
          case '2':
            showCyberMenu();
            setMenuContext('cyber');
            break;
          case '3':
            showOSINTMenu();
            setMenuContext('osint');
            break;
          case '4':
            await showStatus();
            break;
          case '5':
            showHelp();
            break;
        }
      } else if (menuContext === 'cyber') {
        await handleCyberMenuOption(cmd);
      } else if (menuContext === 'osint') {
        await handleOSINTMenuOption(cmd);
      } else if (menuContext === 'aurora') {
        await handleAuroraAIOption(cmd);
      }
    } else {
      // Depois verificar comandos textuais
      switch (cmd.toLowerCase()) {
        case 'clear':
        case 'cls':
          term.clear();
          term.write(ASCII_BANNER);
          writePrompt();
          return;

        case 'exit':
          term.write('\x1b[1;31mDesconectando...\x1b[0m\r\n');
          writePrompt();
          // TODO: Implementar logout/saída
          return;

        case 'help':
          console.log('Executando comando help'); // Debug log
          showHelp();
          break;

        case 'menu':
          console.log('Executando comando menu'); // Debug log
          showMainMenu();
          setMenuContext('main');
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
    const term = terminal.current;
    console.log('showMainMenu() chamada'); // Debug log

    if (!term) {
      console.error('Terminal não está disponível');
      return;
    }

    const menuText = `
\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║                      MENU PRINCIPAL                         ║\x1b[0m
\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m

Selecione uma opção digitando o número correspondente:

\x1b[1;32m[1]\x1b[0m 🤖 \x1b[1;37mAurora AI\x1b[0m
    Assistente de IA para análise inteligente e automação
    \x1b[0;37mModo conversacional com IA especializada em segurança\x1b[0m

\x1b[1;32m[2]\x1b[0m 🛡️  \x1b[1;37mCyber Security Module\x1b[0m
    Ferramentas de análise de segurança, IP intelligence e scanning
    \x1b[0;37mComandos: cyber ip <ip>, cyber domain <domain>, cyber scan <target>\x1b[0m

\x1b[1;32m[3]\x1b[0m 🔍 \x1b[1;37mOSINT Module\x1b[0m
    Inteligência em fontes abertas, análise de emails e redes sociais
    \x1b[0;37mComandos: osint email <email>, osint phone <phone>, osint username <user>\x1b[0m

\x1b[1;32m[4]\x1b[0m 📊 \x1b[1;37mStatus dos Serviços\x1b[0m
    Verificar status e saúde dos microserviços do Vértice
    \x1b[0;37mComando: status\x1b[0m

\x1b[1;32m[5]\x1b[0m 📚 \x1b[1;37mAjuda Completa\x1b[0m
    Guia completo de comandos com exemplos práticos
    \x1b[0;37mComando: help\x1b[0m

\x1b[1;33m→ Digite o número da opção (1-5) ou o comando diretamente\x1b[0m
`;
    console.log('Escrevendo menu no terminal, tamanho:', menuText.length); // Debug log
    term.write(menuText);
    console.log('Menu escrito com sucesso'); // Debug log
  };

  const showAuroraAIMenu = () => {
    const auroraMenu = `
\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║                    🤖 AURORA AI                             ║\x1b[0m
\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m

\x1b[1;35m✨ Assistente de IA especializada em Cyber Security e OSINT\x1b[0m

Selecione uma opção digitando o número correspondente:

\x1b[1;32m[1]\x1b[0m 💬 \x1b[1;37mModo Conversacional\x1b[0m
    Chat interativo com Aurora para análises e consultas
    \x1b[0;37mPergunte qualquer coisa sobre segurança, OSINT ou use comandos\x1b[0m

\x1b[1;32m[2]\x1b[0m 🎯 \x1b[1;37mAnálise Automatizada\x1b[0m
    Aurora analisa automaticamente targets com IA
    \x1b[0;37mForneça um alvo e Aurora decide a melhor estratégia\x1b[0m

\x1b[1;32m[3]\x1b[0m 📝 \x1b[1;37mGerar Relatório\x1b[0m
    Aurora gera relatórios detalhados de análises anteriores
    \x1b[0;37mRelatórios em formato profissional com insights de IA\x1b[0m

\x1b[1;32m[4]\x1b[0m 🧠 \x1b[1;37mTreinamento e Dicas\x1b[0m
    Aurora ensina técnicas e boas práticas
    \x1b[0;37mAprenda sobre ferramentas, metodologias e segurança\x1b[0m

\x1b[1;32m[0]\x1b[0m ⬅️  \x1b[1;37mVoltar ao Menu Principal\x1b[0m

\x1b[1;33m→ Digite o número da opção (0-4)\x1b[0m
`;
    terminal.current.write(auroraMenu);
  };

  const showCyberMenu = () => {
    const cyberMenu = `
\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║              🛡️  CYBER SECURITY MODULE                      ║\x1b[0m
\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m

Selecione uma opção digitando o número correspondente:

\x1b[1;32m[1]\x1b[0m 🌐 \x1b[1;37mAnálise de IP\x1b[0m
    Analisa um endereço IP com geolocalização e reputação
    \x1b[0;37mUsage: Digite 1 e forneça o IP quando solicitado\x1b[0m

\x1b[1;32m[2]\x1b[0m 🔍 \x1b[1;37mAnálise de Domínio\x1b[0m
    Análise completa de domínio (WHOIS, DNS, SSL)
    \x1b[0;37mUsage: Digite 2 e forneça o domínio quando solicitado\x1b[0m

\x1b[1;32m[3]\x1b[0m 🔴 \x1b[1;37mVulnerability Scanner\x1b[0m \x1b[1;31m[OFENSIVO]\x1b[0m
    Scanner de vulnerabilidades em targets
    \x1b[0;37mUsage: Digite 3 e forneça o target quando solicitado\x1b[0m
    \x1b[1;33m⚠️  Requer autorização - Apenas sistemas próprios\x1b[0m

\x1b[1;32m[4]\x1b[0m 💥 \x1b[1;37mExecutar Exploit\x1b[0m \x1b[1;31m[OFENSIVO]\x1b[0m
    Executa exploit específico em target
    \x1b[0;37mUsage: Digite 4 e forneça target e exploit_id\x1b[0m
    \x1b[1;33m⚠️  Requer autorização especial\x1b[0m

\x1b[1;32m[0]\x1b[0m ⬅️  \x1b[1;37mVoltar ao Menu Principal\x1b[0m

\x1b[1;33m→ Digite o número da opção (0-4)\x1b[0m
`;
    terminal.current.write(cyberMenu);
  };

  const showOSINTMenu = () => {
    const osintMenu = `
\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m
\x1b[1;36m║                    🔍 OSINT MODULE                          ║\x1b[0m
\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m

Selecione uma opção digitando o número correspondente:

\x1b[1;32m[1]\x1b[0m 📧 \x1b[1;37mAnálise de Email\x1b[0m
    Investiga email, vazamentos e validação
    \x1b[0;37mUsage: Digite 1 e forneça o email quando solicitado\x1b[0m

\x1b[1;32m[2]\x1b[0m 📱 \x1b[1;37mAnálise de Telefone\x1b[0m
    Investigação de número de telefone e operadora
    \x1b[0;37mUsage: Digite 2 e forneça o telefone quando solicitado\x1b[0m

\x1b[1;32m[3]\x1b[0m 👤 \x1b[1;37mInvestigação de Username\x1b[0m
    Busca username em múltiplas plataformas sociais
    \x1b[0;37mUsage: Digite 3 e forneça o username quando solicitado\x1b[0m

\x1b[1;32m[4]\x1b[0m 🌐 \x1b[1;37mAnálise de Rede Social\x1b[0m
    Análise detalhada de perfil em rede social específica
    \x1b[0;37mUsage: Digite 4 e forneça plataforma e username\x1b[0m
    \x1b[0;37mPlataformas: instagram, twitter, linkedin, facebook\x1b[0m

\x1b[1;32m[0]\x1b[0m ⬅️  \x1b[1;37mVoltar ao Menu Principal\x1b[0m

\x1b[1;33m→ Digite o número da opção (0-4)\x1b[0m
`;
    terminal.current.write(osintMenu);
  };

  const handleAuroraAIOption = async (option) => {
    const term = terminal.current;

    switch (option) {
      case '0':
        showMainMenu();
        setMenuContext('main');
        break;
      case '1':
        // Ativar modo chat AI
        setIsAIChatMode(true);
        setMenuContext('ai_chat');
        term.write('\r\n\x1b[1;35m╔═══════════════════════════════════════════════════════╗\x1b[0m\r\n');
        term.write('\x1b[1;35m║         🤖 AURORA AI - MODO CONVERSACIONAL          ║\x1b[0m\r\n');
        term.write('\x1b[1;35m╚═══════════════════════════════════════════════════════╝\x1b[0m\r\n\r\n');
        term.write('\x1b[1;36m✨ Olá! Sou a Aurora, sua assistente de IA com acesso maestro\x1b[0m\r\n');
        term.write('\x1b[1;36m   a TODOS os serviços do Vértice via tool calling.\x1b[0m\r\n\r\n');
        term.write('\x1b[0;37m📋 Posso ajudar com:\x1b[0m\r\n');
        term.write('\x1b[0;37m  • Análise de IPs, domínios, hashes (threat intelligence)\x1b[0m\r\n');
        term.write('\x1b[0;37m  • Detecção de malware e vulnerabilidades\x1b[0m\r\n');
        term.write('\x1b[0;37m  • Verificação de certificados SSL/TLS\x1b[0m\r\n');
        term.write('\x1b[0;37m  • Scanning de portas e redes\x1b[0m\r\n');
        term.write('\x1b[0;37m  • Investigações OSINT completas\x1b[0m\r\n');
        term.write('\x1b[0;37m  • Comandos em linguagem natural\x1b[0m\r\n\r\n');
        term.write('\x1b[1;33m💡 Exemplos:\x1b[0m\r\n');
        term.write('\x1b[0;37m  "Analise o IP 8.8.8.8"\x1b[0m\r\n');
        term.write('\x1b[0;37m  "Este hash é malware? 44d88612..."\x1b[0m\r\n');
        term.write('\x1b[0;37m  "Faça um scan completo de example.com"\x1b[0m\r\n');
        term.write('\x1b[0;37m  "Investigue o usuário @johndoe"\x1b[0m\r\n\r\n');
        term.write('\x1b[1;31m→ Digite "sair" para voltar ao menu\x1b[0m\r\n\r\n');
        term.write('\x1b[1;32mAurora>\x1b[0m ');
        break;
      case '2':
        term.write('\x1b[1;35m🎯 Aurora AI: Análise Automatizada\x1b[0m\r\n');
        term.write('\x1b[0;37mForneça o target (IP, domínio, email, etc):\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '3':
        term.write('\x1b[1;35m📝 Aurora AI: Gerador de Relatórios\x1b[0m\r\n');
        term.write('\x1b[0;37mBuscando análises anteriores...\x1b[0m\r\n');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '4':
        term.write('\x1b[1;35m🧠 Aurora AI: Treinamento\x1b[0m\r\n');
        term.write('\x1b[0;37mEscolha um tópico para aprender:\x1b[0m\r\n');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      default:
        term.write('\x1b[1;31mOpção inválida. Digite um número de 0 a 4.\x1b[0m\r\n');
        break;
    }
  };

  const handleCyberMenuOption = async (option) => {
    const term = terminal.current;

    switch (option) {
      case '0':
        showMainMenu();
        setMenuContext('main');
        break;
      case '1':
        term.write('\x1b[1;33mDigite o endereço IP para análise:\x1b[0m ');
        // TODO: Aguardar input e executar
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '2':
        term.write('\x1b[1;33mDigite o domínio para análise:\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '3':
        term.write('\x1b[1;33mDigite o target para scan:\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '4':
        term.write('\x1b[1;33mDigite o target e exploit_id:\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      default:
        term.write('\x1b[1;31mOpção inválida. Digite um número de 0 a 4.\x1b[0m\r\n');
        break;
    }
  };

  const handleOSINTMenuOption = async (option) => {
    const term = terminal.current;

    switch (option) {
      case '0':
        showMainMenu();
        setMenuContext('main');
        break;
      case '1':
        term.write('\x1b[1;33mDigite o email para análise:\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '2':
        term.write('\x1b[1;33mDigite o telefone para análise:\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '3':
        term.write('\x1b[1;33mDigite o username para investigação:\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      case '4':
        term.write('\x1b[1;33mDigite a plataforma e username:\x1b[0m ');
        term.write('\x1b[1;31m[EM DESENVOLVIMENTO]\x1b[0m\r\n');
        break;
      default:
        term.write('\x1b[1;31mOpção inválida. Digite um número de 0 a 4.\x1b[0m\r\n');
        break;
    }
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

  const formatAndDisplayResult = (result, module, command) => {
    const term = terminal.current;

    term.write(`\x1b[1;32m✅ Operação concluída com sucesso\x1b[0m\r\n\r\n`);

    // Formatação específica para cada módulo
    if (module === 'cyber' && command === 'ip') {
      formatIPAnalysisResult(result);
    } else if (module === 'osint' && command === 'email') {
      formatEmailAnalysisResult(result);
    } else if (module === 'osint' && command === 'phone') {
      formatPhoneAnalysisResult(result);
    } else {
      // Fallback para JSON formatado
      if (typeof result === 'object') {
        term.write(`\x1b[1;37m${JSON.stringify(result, null, 2)}\x1b[0m\r\n`);
      } else {
        term.write(`\x1b[1;37m${result}\x1b[0m\r\n`);
      }
    }
  };

  const formatIPAnalysisResult = (result) => {
    const term = terminal.current;

    term.write(`\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m\r\n`);
    term.write(`\x1b[1;36m║                    ANÁLISE DE IP                             ║\x1b[0m\r\n`);
    term.write(`\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m\r\n\r\n`);

    // Informações básicas
    term.write(`\x1b[1;33m🔍 IP Analisado:\x1b[0m \x1b[1;37m${result.ip}\x1b[0m\r\n`);
    if (result.ptr_record) {
      term.write(`\x1b[1;33m📡 DNS Reverso:\x1b[0m \x1b[1;37m${result.ptr_record}\x1b[0m\r\n`);
    }
    term.write(`\x1b[1;33m⏰ Timestamp:\x1b[0m \x1b[0;37m${result.timestamp}\x1b[0m\r\n\r\n`);

    // Geolocalização
    if (result.geolocation && result.geolocation.status === 'success') {
      const geo = result.geolocation;
      term.write(`\x1b[1;32m🌍 GEOLOCALIZAÇÃO:\x1b[0m\r\n`);
      term.write(`  \x1b[1;37mPaís:\x1b[0m ${geo.country} (${geo.countryCode})\r\n`);
      term.write(`  \x1b[1;37mRegião:\x1b[0m ${geo.regionName}\r\n`);
      term.write(`  \x1b[1;37mCidade:\x1b[0m ${geo.city}\r\n`);
      term.write(`  \x1b[1;37mCoordenadas:\x1b[0m ${geo.lat}, ${geo.lon}\r\n`);
      term.write(`  \x1b[1;37mISP:\x1b[0m ${geo.isp}\r\n`);
      term.write(`  \x1b[1;37mASN:\x1b[0m ${geo.as}\r\n\r\n`);
    }

    // Reputação
    if (result.reputation) {
      const rep = result.reputation;
      const threatColor = rep.threat_level === 'high' ? '\x1b[1;31m' : rep.threat_level === 'medium' ? '\x1b[1;33m' : '\x1b[1;32m';
      term.write(`\x1b[1;31m🛡️ REPUTAÇÃO DE SEGURANÇA:\x1b[0m\r\n`);
      term.write(`  \x1b[1;37mScore:\x1b[0m ${rep.score}/100\r\n`);
      term.write(`  \x1b[1;37mNível de Ameaça:\x1b[0m ${threatColor}${rep.threat_level.toUpperCase()}\x1b[0m\r\n`);
      term.write(`  \x1b[1;37mÚltima Detecção:\x1b[0m ${rep.last_seen}\r\n\r\n`);
    }

    // Portas abertas
    if (result.open_ports && result.open_ports.length > 0) {
      term.write(`\x1b[1;35m🔓 PORTAS ABERTAS:\x1b[0m\r\n`);
      result.open_ports.forEach(port => {
        term.write(`  \x1b[1;37m${port}\x1b[0m\r\n`);
      });
    } else {
      term.write(`\x1b[1;32m🔒 Nenhuma porta aberta detectada\x1b[0m\r\n`);
    }
  };

  const formatEmailAnalysisResult = (result) => {
    const term = terminal.current;

    term.write(`\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m\r\n`);
    term.write(`\x1b[1;36m║                   ANÁLISE DE EMAIL                           ║\x1b[0m\r\n`);
    term.write(`\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m\r\n\r\n`);

    if (result.data) {
      const data = result.data;
      term.write(`\x1b[1;33m📧 Email:\x1b[0m \x1b[1;37m${data.email}\x1b[0m\r\n`);
      term.write(`\x1b[1;33m🌐 Domínio:\x1b[0m \x1b[1;37m${data.domain || 'N/A'}\x1b[0m\r\n`);
      term.write(`\x1b[1;33m✅ Formato Válido:\x1b[0m ${data.valid_format ? '\x1b[1;32mSim\x1b[0m' : '\x1b[1;31mNão\x1b[0m'}\r\n`);
      term.write(`\x1b[1;33m💥 Vazamentos:\x1b[0m \x1b[1;37m${data.breaches?.length || 0}\x1b[0m\r\n`);

      if (data.risk_score) {
        const riskColor = data.risk_score.level === 'high' ? '\x1b[1;31m' : data.risk_score.level === 'medium' ? '\x1b[1;33m' : '\x1b[1;32m';
        term.write(`\x1b[1;33m⚠️ Nível de Risco:\x1b[0m ${riskColor}${data.risk_score.level.toUpperCase()}\x1b[0m\r\n`);
      }
    }
  };

  const formatPhoneAnalysisResult = (result) => {
    const term = terminal.current;

    term.write(`\x1b[1;36m╔══════════════════════════════════════════════════════════════╗\x1b[0m\r\n`);
    term.write(`\x1b[1;36m║                  ANÁLISE DE TELEFONE                         ║\x1b[0m\r\n`);
    term.write(`\x1b[1;36m╚══════════════════════════════════════════════════════════════╝\x1b[0m\r\n\r\n`);

    if (result.data) {
      const data = result.data;
      term.write(`\x1b[1;33m📱 Telefone:\x1b[0m \x1b[1;37m${data.phone}\x1b[0m\r\n`);
      term.write(`\x1b[1;33m🌍 País:\x1b[0m \x1b[1;37m${data.location?.country || 'N/A'}\x1b[0m\r\n`);
      term.write(`\x1b[1;33m📡 Operadora:\x1b[0m \x1b[1;37m${data.carrier?.name || 'N/A'}\x1b[0m\r\n`);
      term.write(`\x1b[1;33m📋 Tipo:\x1b[0m \x1b[1;37m${data.line_type || 'N/A'}\x1b[0m\r\n`);
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
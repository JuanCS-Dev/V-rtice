import { API_BASE_URL } from "@/config/api";
import { useState, useCallback } from "react";
import logger from "@/utils/logger";

export const useNaturalLanguage = () => {
  const [isProcessing, setIsProcessing] = useState(false);

  /**
   * Processa comandos em linguagem natural e os converte para comandos estruturados
   * @param {string} input - Input do usuário em linguagem natural
   * @returns {Promise<Object>} - Comando estruturado ou resposta da IA
   */
  const processNaturalLanguage = useCallback(async (input, authToken) => {
    setIsProcessing(true);

    try {
      // Primeiro, tentar padrões simples locais
      const localCommand = parseLocalPatterns(input);
      if (localCommand) {
        setIsProcessing(false);
        return localCommand;
      }

      // Se não encontrar padrão local, usar o AI Agent Service
      const response = await fetch(
        `${API_BASE_URL}/api/ai-agent/process-command`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(authToken && { Authorization: `Bearer ${authToken}` }),
          },
          body: JSON.stringify({ query: input }),
        },
      );

      if (!response.ok) {
        throw new Error(
          `Erro ao processar linguagem natural: ${response.status}`,
        );
      }

      const result = await response.json();
      return result;
    } catch (error) {
      logger.error("Erro no processamento NLP:", error);

      // Fallback: tentar parsing básico
      const fallback = parseFallback(input);
      if (fallback) {
        return fallback;
      }

      return {
        type: "error",
        message:
          'Não consegui entender o comando. Tente ser mais específico ou use "help" para ver comandos disponíveis.',
      };
    } finally {
      setIsProcessing(false);
    }
  }, []);

  /**
   * Parser local para padrões comuns e simples
   */
  const parseLocalPatterns = (input) => {
    const lowerInput = input.toLowerCase().trim();

    // Padrões de análise de IP
    const ipRegex = /\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b/;
    const ipMatch = lowerInput.match(ipRegex);

    if (
      ipMatch &&
      (lowerInput.includes("analise") ||
        lowerInput.includes("analisa") ||
        lowerInput.includes("verifica") ||
        lowerInput.includes("investiga") ||
        lowerInput.includes("check") ||
        lowerInput.includes("analyze"))
    ) {
      return {
        type: "command",
        module: "cyber",
        command: "ip",
        args: [ipMatch[1]],
        natural_query: input,
      };
    }

    // Padrões de domínio
    const domainRegex = /\b([a-z0-9-]+\.[a-z]{2,})\b/i;
    const domainMatch = lowerInput.match(domainRegex);

    if (
      domainMatch &&
      (lowerInput.includes("dominio") ||
        lowerInput.includes("domain") ||
        lowerInput.includes("site") ||
        lowerInput.includes("website"))
    ) {
      return {
        type: "command",
        module: "cyber",
        command: "domain",
        args: [domainMatch[1]],
        natural_query: input,
      };
    }

    // Padrões de email
    const emailRegex = /\b([a-z0-9._-]+@[a-z0-9.-]+\.[a-z]{2,})\b/i;
    const emailMatch = lowerInput.match(emailRegex);

    if (emailMatch) {
      return {
        type: "command",
        module: "osint",
        command: "email",
        args: [emailMatch[1]],
        natural_query: input,
      };
    }

    // Padrões de telefone
    const phoneRegex = /\b(\+?\d{10,15})\b/;
    const phoneMatch = lowerInput.match(phoneRegex);

    if (
      phoneMatch &&
      (lowerInput.includes("telefone") ||
        lowerInput.includes("phone") ||
        lowerInput.includes("numero") ||
        lowerInput.includes("celular"))
    ) {
      return {
        type: "command",
        module: "osint",
        command: "phone",
        args: [phoneMatch[1]],
        natural_query: input,
      };
    }

    // Padrões de username/usuário
    if (
      (lowerInput.includes("usuario") ||
        lowerInput.includes("username") ||
        lowerInput.includes("user")) &&
      (lowerInput.includes("@") ||
        lowerInput.includes("perfil") ||
        lowerInput.includes("profile"))
    ) {
      const usernameMatch = lowerInput.match(/@([a-z0-9_.-]+)/i);
      if (usernameMatch) {
        return {
          type: "command",
          module: "osint",
          command: "username",
          args: [usernameMatch[1]],
          natural_query: input,
        };
      }
    }

    // Padrões de scan/vulnerability
    if (
      lowerInput.includes("scan") ||
      lowerInput.includes("vulnerabilidade") ||
      lowerInput.includes("vuln")
    ) {
      const targetMatch = lowerInput.match(
        /(?:scan|scanear|escanear)\s+([a-z0-9.-]+|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/i,
      );
      if (targetMatch) {
        return {
          type: "command",
          module: "cyber",
          command: "scan",
          args: [targetMatch[1]],
          natural_query: input,
          warning:
            "ATENÇÃO: Comando ofensivo. Use apenas em sistemas autorizados.",
        };
      }
    }

    // Padrões de malware/hash
    if (
      lowerInput.includes("malware") ||
      lowerInput.includes("hash") ||
      lowerInput.includes("virus")
    ) {
      const hashMatch = lowerInput.match(/\b([a-f0-9]{32,64})\b/i);
      if (hashMatch) {
        return {
          type: "query",
          service: "malware_analysis",
          action: "check_hash",
          parameters: { hash: hashMatch[1] },
          natural_query: input,
        };
      }
    }

    return null;
  };

  /**
   * Parser fallback simples quando a IA não está disponível
   */
  const parseFallback = (input) => {
    const lowerInput = input.toLowerCase();

    // Comandos informativos
    if (lowerInput.includes("ajuda") || lowerInput.includes("help")) {
      return {
        type: "help",
        message:
          'Digite "menu" para ver opções ou use comandos como:\n- "analise o IP 8.8.8.8"\n- "investigue o email user@domain.com"\n- "scan em exemplo.com"',
      };
    }

    if (lowerInput.includes("status") || lowerInput.includes("serviço")) {
      return {
        type: "command",
        module: "status",
        command: "check",
      };
    }

    return null;
  };

  /**
   * Converte resposta da IA em formato executável
   */
  const convertAIResponseToCommand = useCallback((aiResponse) => {
    if (!aiResponse || !aiResponse.intent) {
      return null;
    }

    // Mapear intenções da IA para comandos estruturados
    const intentMap = {
      analyze_ip: { module: "cyber", command: "ip" },
      analyze_domain: { module: "cyber", command: "domain" },
      scan_vulnerability: { module: "cyber", command: "scan" },
      analyze_email: { module: "osint", command: "email" },
      analyze_phone: { module: "osint", command: "phone" },
      investigate_username: { module: "osint", command: "username" },
      check_malware: { module: "malware", command: "check_hash" },
    };

    const commandMapping = intentMap[aiResponse.intent];
    if (!commandMapping) {
      return null;
    }

    return {
      type: "command",
      module: commandMapping.module,
      command: commandMapping.command,
      args: aiResponse.parameters || [],
      confidence: aiResponse.confidence,
      natural_query: aiResponse.original_query,
    };
  }, []);

  /**
   * Gera sugestões de comandos baseado em input parcial
   */
  const getSuggestions = useCallback((partialInput) => {
    const lowerInput = partialInput.toLowerCase();
    const suggestions = [];

    if (lowerInput.includes("ip") || /\d{1,3}\.\d{1,3}/.test(lowerInput)) {
      suggestions.push("Analise o IP 8.8.8.8");
    }

    if (lowerInput.includes("email") || lowerInput.includes("@")) {
      suggestions.push("Investigue o email usuario@dominio.com");
    }

    if (lowerInput.includes("domain") || lowerInput.includes("site")) {
      suggestions.push("Analise o domínio google.com");
    }

    if (lowerInput.includes("scan") || lowerInput.includes("vuln")) {
      suggestions.push("Faça um scan em exemplo.com");
    }

    if (lowerInput.includes("user") || lowerInput.includes("perfil")) {
      suggestions.push("Investigue o usuário @johndoe");
    }

    return suggestions;
  }, []);

  return {
    processNaturalLanguage,
    convertAIResponseToCommand,
    getSuggestions,
    isProcessing,
  };
};

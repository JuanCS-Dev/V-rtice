import { API_BASE_URL } from "@/config/api";
import { useState, useCallback } from "react";
import logger from "@/utils/logger";

export const useTerminalCommands = () => {
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const executeCommand = useCallback(
    async (module, command, args = [], token = null) => {
      setIsExecuting(true);

      try {
        let endpoint = "";
        let payload = {};

        // Mapear comandos para endpoints da API
        switch (module) {
          case "cyber":
            switch (command) {
              case "ip":
                endpoint = "/api/ip/analyze";
                payload = { ip: args[0] };
                break;
              case "domain":
                endpoint = "/api/domain/analyze";
                payload = { domain: args[0] };
                break;
              case "scan":
                endpoint = "/api/vuln-scanner/scan";
                payload = {
                  target: args[0],
                  scan_type: args[1] || "full",
                };
                break;
              case "exploit":
                endpoint = "/api/vuln-scanner/exploit";
                payload = {
                  target: args[0],
                  exploit_id: args[1],
                  payload_options: {},
                };
                break;
              default:
                throw new Error(`Comando cyber não reconhecido: ${command}`);
            }
            break;

          case "osint":
            switch (command) {
              case "email":
                endpoint = "/api/email/analyze";
                payload = { email: args[0] };
                break;
              case "phone":
                endpoint = "/api/phone/analyze";
                payload = { phone: args[0] };
                break;
              case "username":
                endpoint = "/api/username/investigate";
                payload = { username: args[0] };
                break;
              case "social":
                endpoint = "/api/social/profile";
                payload = {
                  platform: args[0],
                  identifier: args[1],
                };
                break;
              default:
                throw new Error(`Comando OSINT não reconhecido: ${command}`);
            }
            break;

          default:
            throw new Error(`Módulo não reconhecido: ${module}`);
        }

        // Fazer requisição
        const headers = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Erro HTTP: ${response.status}`);
        }

        const result = await response.json();
        setLastResult(result);
        return result;
      } catch (error) {
        logger.error("Erro ao executar comando:", error);
        throw error;
      } finally {
        setIsExecuting(false);
      }
    },
    [],
  );

  const getCommandHelp = useCallback((module, command) => {
    const helpMap = {
      cyber: {
        ip: "Analisa um endereço IP - Uso: cyber ip <endereço_ip>",
        domain: "Analisa um domínio - Uso: cyber domain <dominio>",
        scan: "Executa scan de vulnerabilidades - Uso: cyber scan <target> [tipo]",
        exploit: "Executa exploit - Uso: cyber exploit <target> <exploit_id>",
      },
      osint: {
        email: "Analisa um email - Uso: osint email <email>",
        phone: "Analisa um telefone - Uso: osint phone <telefone>",
        username: "Investiga username - Uso: osint username <usuario>",
        social:
          "Analisa perfil social - Uso: osint social <plataforma> <usuario>",
      },
    };

    return helpMap[module]?.[command] || "Comando não encontrado";
  }, []);

  const validateCommand = useCallback((module, command, args) => {
    const validations = {
      cyber: {
        ip: (args) => (args.length >= 1 ? null : "IP é obrigatório"),
        domain: (args) => (args.length >= 1 ? null : "Domínio é obrigatório"),
        scan: (args) => (args.length >= 1 ? null : "Target é obrigatório"),
        exploit: (args) =>
          args.length >= 2 ? null : "Target e exploit_id são obrigatórios",
      },
      osint: {
        email: (args) => (args.length >= 1 ? null : "Email é obrigatório"),
        phone: (args) => (args.length >= 1 ? null : "Telefone é obrigatório"),
        username: (args) =>
          args.length >= 1 ? null : "Username é obrigatório",
        social: (args) =>
          args.length >= 2 ? null : "Plataforma e usuário são obrigatórios",
      },
    };

    const validator = validations[module]?.[command];
    return validator ? validator(args) : null;
  }, []);

  const formatResult = useCallback((result, module, command) => {
    // Formatação específica baseada no tipo de resultado
    if (!result) return "Nenhum resultado";

    switch (module) {
      case "cyber":
        return formatCyberResult(result, command);
      case "osint":
        return formatOsintResult(result, command);
      default:
        return JSON.stringify(result, null, 2);
    }
  }, []);

  const formatCyberResult = (result, command) => {
    switch (command) {
      case "ip":
        if (result.success && result.data) {
          const data = result.data;
          return `
IP: ${result.ip}
País: ${data.location?.country || "N/A"}
Região: ${data.location?.region || "N/A"}
Cidade: ${data.location?.city || "N/A"}
ISP: ${data.isp || "N/A"}
ASN: ${data.asn?.number || "N/A"} - ${data.asn?.name || "N/A"}
Nível de Ameaça: ${data.threat_level || "N/A"}
          `.trim();
        }
        break;
      case "scan":
        if (result.success) {
          return `Scan iniciado - ID: ${result.scan_id}\nStatus: ${result.status}`;
        }
        break;
      default:
        return JSON.stringify(result, null, 2);
    }
    return "Erro ao processar resultado";
  };

  const formatOsintResult = (result, command) => {
    switch (command) {
      case "email":
        if (result.status === "success" && result.data) {
          const data = result.data;
          return `
Email: ${data.email}
Domínio: ${data.domain || "N/A"}
Formato Válido: ${data.valid_format ? "Sim" : "Não"}
Vazamentos: ${data.breaches?.length || 0}
Risco: ${data.risk_score?.level || "N/A"}
          `.trim();
        }
        break;
      case "phone":
        if (result.status === "success" && result.data) {
          const data = result.data;
          return `
Telefone: ${data.phone}
País: ${data.location?.country || "N/A"}
Operadora: ${data.carrier?.name || "N/A"}
Tipo: ${data.line_type || "N/A"}
          `.trim();
        }
        break;
      default:
        return JSON.stringify(result, null, 2);
    }
    return "Erro ao processar resultado";
  };

  return {
    executeCommand,
    isExecuting,
    lastResult,
    getCommandHelp,
    validateCommand,
    formatResult,
  };
};

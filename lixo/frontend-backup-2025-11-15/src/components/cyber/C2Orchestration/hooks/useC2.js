import { useState, useEffect, useCallback } from "react";
import logger from "@/utils/logger";
import {
  createC2Session,
  listC2Sessions,
  executeC2Command,
  passSession as apiPassSession,
  executeAttackChain,
} from "../../../../api/offensiveServices";

/**
 * useC2 - Hook para C2 Orchestration
 *
 * Gerencia sessões C2, comandos e attack chains
 */
export const useC2 = () => {
  const [sessions, setSessions] = useState([]);
  const [activeSessions, setActiveSessions] = useState([]);
  const [attackChains, setAttackChains] = useState([]);
  const [commandHistory, setCommandHistory] = useState([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Carrega lista de sessões
   */
  const loadSessions = useCallback(async () => {
    try {
      const result = await listC2Sessions();

      if (result.success) {
        const sessionList = result.sessions || result.data || [];
        setSessions(sessionList);

        // Separa sessões ativas
        const active = sessionList.filter(
          (session) =>
            session.status === "active" || session.status === "connected",
        );
        setActiveSessions(active);
      }
    } catch (err) {
      logger.error("Error loading sessions:", err);
      setError(err.message);
    }
  }, []);

  // Carrega sessões ao montar
  useEffect(() => {
    loadSessions();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Polling para sessões ativas
  useEffect(() => {
    const interval = setInterval(() => {
      if (activeSessions.length > 0) {
        loadSessions();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [activeSessions.length]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Cria nova sessão C2
   */
  const createSession = useCallback(
    async (framework, targetHost, payload, config = {}) => {
      setIsExecuting(true);
      setError(null);

      try {
        const result = await createC2Session(
          framework,
          targetHost,
          payload,
          config,
        );

        if (result.success) {
          // Adiciona nova sessão
          const newSession = {
            session_id: result.session_id || Date.now(),
            framework,
            target_host: targetHost,
            payload,
            status: "active",
            created_at: new Date().toISOString(),
            ...result,
          };

          setSessions((prev) => [...prev, newSession]);
          setActiveSessions((prev) => [...prev, newSession]);

          // Recarrega lista
          await loadSessions();

          return { success: true, sessionId: result.session_id };
        } else {
          setError(result.error);
          return { success: false, error: result.error };
        }
      } catch (err) {
        logger.error("Error creating session:", err);
        setError(err.message);
        return { success: false, error: err.message };
      } finally {
        setIsExecuting(false);
      }
    },
    [loadSessions],
  );

  /**
   * Executa comando em sessão
   */
  const executeCommand = useCallback(async (sessionId, command, args = []) => {
    setIsExecuting(true);
    setError(null);

    try {
      const result = await executeC2Command(sessionId, command, args);

      if (result.success) {
        // Adiciona ao histórico
        setCommandHistory((prev) => [
          ...prev,
          {
            session_id: sessionId,
            command,
            args,
            output: result.output || result.data,
            timestamp: new Date().toISOString(),
          },
        ]);

        return result;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error("Error executing command:", err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsExecuting(false);
    }
  }, []);

  /**
   * Passa sessão entre frameworks
   */
  const passSession = useCallback(
    async (sessionId, targetFramework) => {
      setIsExecuting(true);
      setError(null);

      try {
        const result = await apiPassSession(sessionId, targetFramework);

        if (result.success) {
          // Atualiza sessão
          setSessions((prev) =>
            prev.map((session) =>
              session.session_id === sessionId
                ? { ...session, framework: targetFramework }
                : session,
            ),
          );

          await loadSessions();

          return result;
        } else {
          setError(result.error);
          return { success: false, error: result.error };
        }
      } catch (err) {
        logger.error("Error passing session:", err);
        setError(err.message);
        return { success: false, error: err.message };
      } finally {
        setIsExecuting(false);
      }
    },
    [loadSessions],
  );

  /**
   * Executa attack chain
   */
  const executeChain = useCallback(async (chainConfig) => {
    setIsExecuting(true);
    setError(null);

    try {
      const result = await executeAttackChain(chainConfig);

      if (result.success) {
        // Adiciona aos chains executados
        setAttackChains((prev) => [
          ...prev,
          {
            ...chainConfig,
            execution_id: result.execution_id || Date.now(),
            status: "running",
            started_at: new Date().toISOString(),
          },
        ]);

        return result;
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (err) {
      logger.error("Error executing attack chain:", err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsExecuting(false);
    }
  }, []);

  /**
   * Refresh manual
   */
  const refreshSessions = useCallback(() => {
    loadSessions();
  }, [loadSessions]);

  return {
    sessions,
    activeSessions,
    attackChains,
    commandHistory,
    isExecuting,
    error,
    createSession,
    executeCommand,
    passSession,
    executeChain,
    refreshSessions,
  };
};

export default useC2;

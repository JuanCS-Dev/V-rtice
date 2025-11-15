/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MABA DASHBOARD - Maximus Autonomous Browser Agent
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dashboard para monitoramento e controle do agente de navegação autônomo.
 *
 * Funcionalidades:
 * - Visualização de Cognitive Map (Neo4j → D3.js)
 * - Gerenciamento de sessões de browser
 * - Timeline de navegações
 * - Galeria de screenshots
 * - Métricas de aprendizado
 *
 * Integração:
 * - useMABAStats: Estatísticas gerais
 * - useCognitiveMap: Grafo de conhecimento
 * - useBrowserSessions: Sessões ativas
 * - WebSocket: Eventos em tempo real
 */

import React, { useState } from "react";
import logger from "@/utils/logger";
import { useMABAStats } from "../../hooks/maba/useMABAStats";
import { useCognitiveMap } from "../../hooks/maba/useCognitiveMap";
import { useBrowserSessions } from "../../hooks/maba/useBrowserSessions";
import { useWebSocket } from "../../hooks/useWebSocket";
import { WS_ENDPOINTS } from "../../config/api";

// Components
import { CognitiveMapViewer } from "./components/CognitiveMapViewer";
import { BrowserSessionManager } from "./components/BrowserSessionManager";
import { NavigationTimeline } from "./components/NavigationTimeline";
import { StatsOverview } from "./components/StatsOverview";

// Styles
import styles from "./MABADashboard.module.css";

export const MABADashboard = ({ setCurrentView }) => {
  const [activeView, setActiveView] = useState("cognitive-map"); // cognitive-map, sessions, timeline

  // Data hooks
  const { stats, isLoading: statsLoading, error: statsError } = useMABAStats();
  const {
    graph,
    isLoading: graphLoading,
    error: graphError,
    refetch: refetchGraph,
  } = useCognitiveMap();
  const {
    sessions,
    isLoading: sessionsLoading,
    createSession,
    closeSession,
  } = useBrowserSessions();

  // WebSocket for real-time events
  const { data: liveEvent, isConnected } = useWebSocket(WS_ENDPOINTS.maba);

  // Error handling
  const hasError = statsError || graphError;
  const isLoading = statsLoading && graphLoading && sessionsLoading;

  // Handlers
  const handleBackToMain = () => {
    setCurrentView("main");
  };

  const handleRefresh = () => {
    refetchGraph();
  };

  const handleCreateSession = async (url) => {
    try {
      await createSession(url);
    } catch (error) {
      logger.error("Failed to create session:", error);
    }
  };

  const handleCloseSession = async (sessionId) => {
    try {
      await closeSession(sessionId);
    } catch (error) {
      logger.error("Failed to close session:", error);
    }
  };

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerTop}>
          <button
            className={styles.backButton}
            onClick={handleBackToMain}
            aria-label="Voltar para landing page"
          >
            ← Voltar
          </button>

          <div className={styles.headerTitle}>
            <h1 className={styles.title}>
              <span className={styles.icon}>🤖</span>
              MABA Dashboard
            </h1>
            <p className={styles.subtitle}>Maximus Autonomous Browser Agent</p>
          </div>

          <div className={styles.headerActions}>
            <button
              className={styles.refreshButton}
              onClick={handleRefresh}
              disabled={graphLoading}
              aria-label="Atualizar dados"
            >
              {graphLoading ? "⏳" : "🔄"}
            </button>
            <div className={styles.connectionIndicator}>
              <span
                className={isConnected ? styles.connected : styles.disconnected}
              >
                {isConnected ? "🟢" : "🔴"}
              </span>
              <span className={styles.connectionLabel}>
                {isConnected ? "LIVE" : "OFFLINE"}
              </span>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        {stats && <StatsOverview stats={stats} />}
      </header>

      {/* View Tabs */}
      <nav className={styles.tabs} role="tablist">
        <button
          className={`${styles.tab} ${activeView === "cognitive-map" ? styles.active : ""}`}
          onClick={() => setActiveView("cognitive-map")}
          role="tab"
          aria-selected={activeView === "cognitive-map"}
        >
          🧠 Cognitive Map
        </button>
        <button
          className={`${styles.tab} ${activeView === "sessions" ? styles.active : ""}`}
          onClick={() => setActiveView("sessions")}
          role="tab"
          aria-selected={activeView === "sessions"}
        >
          🌐 Browser Sessions
        </button>
        <button
          className={`${styles.tab} ${activeView === "timeline" ? styles.active : ""}`}
          onClick={() => setActiveView("timeline")}
          role="tab"
          aria-selected={activeView === "timeline"}
        >
          📜 Navigation Timeline
        </button>
      </nav>

      {/* Error State */}
      {hasError && (
        <div className={styles.error}>
          <div className={styles.errorIcon}>⚠️</div>
          <div className={styles.errorContent}>
            <h3>Erro ao carregar dados</h3>
            <p>{statsError?.message || graphError?.message}</p>
            <button className={styles.errorRetry} onClick={handleRefresh}>
              Tentar novamente
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && !hasError && (
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Carregando MABA Dashboard...</p>
        </div>
      )}

      {/* Content Views */}
      {!isLoading && !hasError && (
        <main className={styles.content}>
          {activeView === "cognitive-map" && (
            <CognitiveMapViewer graph={graph} isLoading={graphLoading} />
          )}

          {activeView === "sessions" && (
            <BrowserSessionManager
              sessions={sessions}
              isLoading={sessionsLoading}
              onCreateSession={handleCreateSession}
              onCloseSession={handleCloseSession}
            />
          )}

          {activeView === "timeline" && (
            <NavigationTimeline
              sessions={sessions}
              isLoading={sessionsLoading}
            />
          )}
        </main>
      )}

      {/* Live Event Toast */}
      {liveEvent && (
        <div className={styles.liveToast}>
          <span className={styles.liveIcon}>⚡</span>
          <span className={styles.liveText}>{liveEvent.message}</span>
        </div>
      )}
    </div>
  );
};

export default MABADashboard;

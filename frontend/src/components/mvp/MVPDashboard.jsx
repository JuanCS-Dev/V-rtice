/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MVP DASHBOARD - Maximus Vision Protocol
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dashboard para sistema de narrativas e observabilidade do Vértice.
 *
 * Funcionalidades:
 * - Feed de narrativas estilo Medium/blog
 * - Heatmap de anomalias (calendar view)
 * - System Pulse (métricas em tempo real)
 * - NQS (Narrative Quality Score) trends
 * - Filtros por tone e severity
 *
 * Integração:
 * - useMVPNarratives: Gestão de narrativas
 * - useAnomalies: Detecção de anomalias
 * - useSystemMetrics: Métricas do sistema
 * - WebSocket: Eventos em tempo real
 */

import React, { useState } from "react";
import { useMVPNarratives } from "../../hooks/mvp/useMVPNarratives";
import { useAnomalies } from "../../hooks/mvp/useAnomalies";
import { useSystemMetrics } from "../../hooks/mvp/useSystemMetrics";
import { useWebSocket } from "../../hooks/useWebSocket";
import { WS_ENDPOINTS } from "../../config/api";

// Components
import { NarrativeFeed } from "./components/NarrativeFeed";
import { AnomalyHeatmap } from "./components/AnomalyHeatmap";
import { SystemPulseVisualization } from "./components/SystemPulseVisualization";
import { StatsOverview } from "./components/StatsOverview";

// Styles
import styles from "./MVPDashboard.module.css";

export const MVPDashboard = ({ setCurrentView }) => {
  const [activeView, setActiveView] = useState("narratives"); // narratives, anomalies, pulse

  // Data hooks
  const {
    narratives,
    isLoading: narrativesLoading,
    error: narrativesError,
    generateNarrative,
    stats: narrativeStats,
  } = useMVPNarratives();

  const {
    anomalies,
    timeline,
    isLoading: anomaliesLoading,
    error: anomaliesError,
  } = useAnomalies();

  const {
    metrics,
    pulse,
    isLoading: metricsLoading,
    error: metricsError,
  } = useSystemMetrics({ includePulse: true });

  // WebSocket for real-time events
  const { data: liveEvent, isConnected } = useWebSocket(WS_ENDPOINTS.mvp);

  // Error handling
  const hasError = narrativesError || anomaliesError || metricsError;
  const isLoading = narrativesLoading && anomaliesLoading && metricsLoading;

  // Handlers
  const handleBackToMain = () => {
    setCurrentView("main");
  };

  const handleGenerateNarrative = async () => {
    try {
      await generateNarrative({
        tone: "analytical",
        max_length: 500,
      });
    } catch (error) {
      console.error("Failed to generate narrative:", error);
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
              <span className={styles.icon}>📖</span>
              MVP Dashboard
            </h1>
            <p className={styles.subtitle}>
              Maximus Vision Protocol - Sistema de Narrativas
            </p>
          </div>

          <div className={styles.headerActions}>
            <button
              className={styles.generateButton}
              onClick={handleGenerateNarrative}
              disabled={narrativesLoading}
              aria-label="Gerar nova narrativa"
            >
              {narrativesLoading ? "⏳" : "✍️"} Nova Narrativa
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
        {narrativeStats && <StatsOverview stats={narrativeStats} />}
      </header>

      {/* View Tabs */}
      <nav className={styles.tabs} role="tablist">
        <button
          className={`${styles.tab} ${activeView === "narratives" ? styles.active : ""}`}
          onClick={() => setActiveView("narratives")}
          role="tab"
          aria-selected={activeView === "narratives"}
        >
          📝 Narrativas
        </button>
        <button
          className={`${styles.tab} ${activeView === "anomalies" ? styles.active : ""}`}
          onClick={() => setActiveView("anomalies")}
          role="tab"
          aria-selected={activeView === "anomalies"}
        >
          🔥 Anomalias
        </button>
        <button
          className={`${styles.tab} ${activeView === "pulse" ? styles.active : ""}`}
          onClick={() => setActiveView("pulse")}
          role="tab"
          aria-selected={activeView === "pulse"}
        >
          💓 System Pulse
        </button>
      </nav>

      {/* Error State */}
      {hasError && (
        <div className={styles.error}>
          <div className={styles.errorIcon}>⚠️</div>
          <div className={styles.errorContent}>
            <h3>Erro ao carregar dados</h3>
            <p>
              {narrativesError?.message ||
                anomaliesError?.message ||
                metricsError?.message}
            </p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && !hasError && (
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Carregando MVP Dashboard...</p>
        </div>
      )}

      {/* Content Views */}
      {!isLoading && !hasError && (
        <main className={styles.content}>
          {activeView === "narratives" && (
            <NarrativeFeed
              narratives={narratives}
              isLoading={narrativesLoading}
            />
          )}

          {activeView === "anomalies" && (
            <AnomalyHeatmap
              anomalies={anomalies}
              timeline={timeline}
              isLoading={anomaliesLoading}
            />
          )}

          {activeView === "pulse" && (
            <SystemPulseVisualization
              pulse={pulse}
              metrics={metrics}
              isLoading={metricsLoading}
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

export default MVPDashboard;

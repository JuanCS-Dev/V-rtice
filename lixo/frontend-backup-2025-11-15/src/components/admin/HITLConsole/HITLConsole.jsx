/**
 * HITLConsole - Human-in-the-Loop Console for APV Review
 *
 * Main container for HITL dashboard with 3-column layout:
 * - Left: Review Queue (list of pending APVs)
 * - Center: Review Details (full APV context)
 * - Right: Decision Panel (approve/reject/modify/escalate)
 * - Bottom: HITL Statistics & History
 */

import React, { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import logger from "@/utils/logger";
import ReviewQueue from "./components/ReviewQueue";
import ReviewDetails from "./components/ReviewDetails";
import DecisionPanel from "./components/DecisionPanel";
import HITLStats from "./components/HITLStats";
import { useReviewQueue } from "./hooks/useReviewQueue";
import { useReviewDetails } from "./hooks/useReviewDetails";
import { useHITLStats } from "./hooks/useHITLStats";
import {
  useWebSocket,
  MessageType,
  WebSocketStatus,
} from "./hooks/useWebSocket";
import styles from "./HITLConsole.module.css";

const HITLConsole = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selectedAPV, setSelectedAPV] = useState(null);
  const [filters, setFilters] = useState({
    severity: null,
    patch_strategy: null,
    wargame_verdict: null,
  });

  // Fetch review queue
  // Boris Cherny Standard - GAP #38 FIX: Expose isRefetching for stale indicator
  const {
    reviews,
    loading: queueLoading,
    error: queueError,
    refetch: refetchQueue,
    isRefetching: queueRefetching,
  } = useReviewQueue(filters);

  // Fetch selected APV details
  const { review: selectedReview, loading: detailsLoading } =
    useReviewDetails(selectedAPV);

  // Fetch HITL stats
  const { stats, loading: statsLoading } = useHITLStats();

  // Boris Cherny Standard - GAP #83: Replace console.log with logger
  // WebSocket message handler
  const handleWebSocketMessage = useCallback(
    (message) => {
      logger.debug("[HITLConsole] WebSocket message received:", message);

      switch (message.type) {
        case MessageType.NEW_APV:
          // New APV added to queue - invalidate review queue cache
          logger.debug("[HITLConsole] New APV:", message.apv_code);
          queryClient.invalidateQueries({ queryKey: ["hitl-reviews"] });
          queryClient.invalidateQueries({ queryKey: ["hitl-stats"] });
          break;

        case MessageType.DECISION_MADE:
          // Decision made - invalidate caches
          logger.debug(
            "[HITLConsole] Decision made:",
            message.decision,
            "on",
            message.apv_code,
          );
          queryClient.invalidateQueries({ queryKey: ["hitl-reviews"] });
          queryClient.invalidateQueries({ queryKey: ["hitl-stats"] });
          break;

        case MessageType.STATS_UPDATE:
          // Stats updated - invalidate stats cache
          logger.debug("[HITLConsole] Stats updated:", message);
          queryClient.invalidateQueries({ queryKey: ["hitl-stats"] });
          break;

        case MessageType.CONNECTION_ACK:
          logger.debug(
            "[HITLConsole] Connected with client ID:",
            message.client_id,
          );
          break;

        default:
          // Other message types
          break;
      }
    },
    [queryClient],
  );

  // WebSocket connection
  const wsUrl = `${import.meta.env.VITE_HITL_API_URL.replace("http", "ws")}/hitl/ws`;
  const {
    status: wsStatus,
    isConnected: _wsConnected,
    clientId: _wsClientId,
  } = useWebSocket({
    url: wsUrl,
    channels: ["apvs", "decisions", "stats"],
    onMessage: handleWebSocketMessage,
    autoConnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  });

  // Handle APV selection
  const handleSelectAPV = (apv) => {
    setSelectedAPV(apv.apv_id);
  };

  // Handle decision submission success
  const handleDecisionSuccess = () => {
    // Refetch queue and clear selection
    refetchQueue();
    setSelectedAPV(null);
  };

  return (
    <div className={styles.container}>
      {/* Scan Line Animation */}
      <div className={styles.scanLine} aria-hidden="true" />

      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <span className={styles.headerIcon}>🛡️</span>
            <div>
              <h1 className={styles.headerTitle}>
                {t("hitl.title", "HITL CONSOLE")}
              </h1>
              <p className={styles.headerSubtitle}>
                {t("hitl.subtitle", "HUMAN DECISION PANEL")}
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          {stats && (
            <div className={styles.headerStats}>
              {/* WebSocket Status Indicator */}
              <div
                className={styles.statBadge}
                title={`WebSocket: ${wsStatus}`}
              >
                <span className={styles.statLabel}>
                  {wsStatus === WebSocketStatus.CONNECTED && "🟢"}
                  {wsStatus === WebSocketStatus.CONNECTING && "🟡"}
                  {wsStatus === WebSocketStatus.RECONNECTING && "🟠"}
                  {(wsStatus === WebSocketStatus.DISCONNECTED ||
                    wsStatus === WebSocketStatus.ERROR) &&
                    "🔴"}{" "}
                  {t("hitl.realtime", "Real-time")}
                </span>
              </div>

              <div className={styles.statBadge}>
                <span className={styles.statLabel}>
                  {t("hitl.pending", "Pending")}:
                </span>
                <span className={styles.statValue}>
                  {stats.pending_reviews}
                </span>
              </div>
              <div className={styles.statBadge}>
                <span className={styles.statLabel}>
                  {t("hitl.today", "Today")}:
                </span>
                <span className={styles.statValue}>
                  {stats.decisions_today}
                </span>
              </div>
              <div className={styles.statBadge}>
                <span className={styles.statLabel}>
                  {t("hitl.agreement", "Agreement")}:
                </span>
                <span className={styles.statValue}>
                  {(stats.human_ai_agreement_rate * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content - 3 Column Layout */}
      <main className={styles.mainContent}>
        {/* Left Column: Review Queue */}
        <div className={styles.queueColumn}>
          <ReviewQueue
            reviews={reviews}
            loading={queueLoading}
            error={queueError}
            selectedAPV={selectedAPV}
            onSelectAPV={handleSelectAPV}
            filters={filters}
            onFiltersChange={setFilters}
            isRefetching={queueRefetching}
          />
        </div>

        {/* Center Column: Review Details */}
        <div className={styles.detailsColumn}>
          <ReviewDetails
            review={selectedReview}
            loading={detailsLoading}
            apvSelected={!!selectedAPV}
          />
        </div>

        {/* Right Column: Decision Panel */}
        <div className={styles.decisionColumn}>
          <DecisionPanel
            review={selectedReview}
            apvSelected={!!selectedAPV}
            onSuccess={handleDecisionSuccess}
          />
        </div>
      </main>

      {/* Bottom: Statistics */}
      <footer className={styles.statsSection}>
        <HITLStats stats={stats} loading={statsLoading} />
      </footer>
    </div>
  );
};

export default HITLConsole;

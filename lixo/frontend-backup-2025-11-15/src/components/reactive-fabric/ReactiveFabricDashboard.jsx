/**
 * 🕸️ Reactive Fabric Dashboard - Phase 1 Intelligence Collection
 *
 * Central intelligence fusion center for passive honeypot monitoring.
 * Implements "Decoy Bayou" visualization with real-time threat tracking.
 *
 * @module ReactiveFabricDashboard
 * @implements {DOUTRINA_VERTICE} - Production-ready, zero placeholders
 * @phase Phase 1 - Passive Intelligence Collection Only
 */

"use client";

import React, { useState, useEffect, useCallback } from "react";
import logger from "@/utils/logger";
import {
  formatDateTime,
  formatDate,
  formatTime,
  getTimestamp,
} from "@/utils/dateHelpers";
import styles from "./ReactiveFabricDashboard.module.css";
import { DashboardFooter } from "../shared/DashboardFooter";
import DecoyBayouMap from "./DecoyBayouMap";
import IntelligenceFusionPanel from "./IntelligenceFusionPanel";
import ThreatTimelineWidget from "./ThreatTimelineWidget";
import HoneypotStatusGrid from "./HoneypotStatusGrid";

/**
 * Main dashboard component orchestrating all reactive fabric visualizations
 */
const ReactiveFabricDashboard = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [honeypotData, setHoneypotData] = useState([]);
  const [threatEvents, setThreatEvents] = useState([]);
  const [fusionIntel, setFusionIntel] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  /**
   * Fetch honeypot status from API Gateway
   */
  const fetchHoneypotStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/reactive-fabric/honeypots/status");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setHoneypotData(data.honeypots || []);
      setLastUpdate(new Date().toISOString());
    } catch (err) {
      logger.error("Failed to fetch honeypot status:", err);
      setError(err.message);
    }
  }, []);

  /**
   * Fetch latest threat events
   */
  const fetchThreatEvents = useCallback(async () => {
    try {
      const response = await fetch(
        "/api/reactive-fabric/events/recent?limit=50",
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setThreatEvents(data.events || []);
    } catch (err) {
      logger.error("Failed to fetch threat events:", err);
      setError(err.message);
    }
  }, []);

  /**
   * Fetch intelligence fusion data
   */
  const fetchIntelligenceFusion = useCallback(async () => {
    try {
      const response = await fetch("/api/reactive-fabric/intelligence/fusion");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setFusionIntel(data);
    } catch (err) {
      logger.error("Failed to fetch intelligence fusion:", err);
      setError(err.message);
    }
  }, []);

  /**
   * Initial data load
   */
  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      await Promise.all([
        fetchHoneypotStatus(),
        fetchThreatEvents(),
        fetchIntelligenceFusion(),
      ]);
      setIsLoading(false);
    };

    loadInitialData();
  }, [fetchHoneypotStatus, fetchThreatEvents, fetchIntelligenceFusion]);

  /**
   * Real-time polling (every 5 seconds)
   */
  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchHoneypotStatus();
      fetchThreatEvents();
      fetchIntelligenceFusion();
    }, 5000);

    return () => clearInterval(intervalId);
  }, [fetchHoneypotStatus, fetchThreatEvents, fetchIntelligenceFusion]);

  /**
   * Calculate metrics
   */
  const metrics = {
    activeHoneypots: honeypotData.filter((h) => h.status === "active").length,
    totalInteractions: threatEvents.length,
    uniqueAttackers: new Set(threatEvents.map((e) => e.source_ip)).size,
    criticalThreats: threatEvents.filter((e) => e.severity === "critical")
      .length,
  };

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <p className={styles.loadingText}>Initializing Reactive Fabric...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <div className={styles.errorIcon}>⚠️</div>
        <h2 className={styles.errorTitle}>Connection Failed</h2>
        <p className={styles.errorMessage}>{error}</p>
        <button
          className={styles.retryButton}
          onClick={() => window.location.reload()}
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>
            <span className={styles.titleIcon}>🕸️</span>
            Reactive Fabric
          </h1>
          <span className={styles.phase}>
            Phase 1 - Intelligence Collection
          </span>
        </div>

        <div className={styles.headerRight}>
          <div className={styles.statusBadge}>
            <span className={styles.statusDot} />
            Live Monitoring
          </div>
          {lastUpdate && (
            <span className={styles.lastUpdate}>
              Updated: {formatTime(lastUpdate)}
            </span>
          )}
        </div>
      </header>

      {/* Metrics Overview */}
      <div className={styles.metricsBar}>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Active Honeypots</span>
          <span className={styles.metricValue}>{metrics.activeHoneypots}</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Total Interactions</span>
          <span className={styles.metricValue}>
            {metrics.totalInteractions}
          </span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Unique Attackers</span>
          <span className={styles.metricValue}>{metrics.uniqueAttackers}</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Critical Threats</span>
          <span className={`${styles.metricValue} ${styles.critical}`}>
            {metrics.criticalThreats}
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className={styles.tabNav}>
        <button
          className={`${styles.tab} ${activeTab === "overview" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={`${styles.tab} ${activeTab === "decoy-bayou" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("decoy-bayou")}
        >
          Decoy Bayou
        </button>
        <button
          className={`${styles.tab} ${activeTab === "intelligence" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("intelligence")}
        >
          Intelligence Fusion
        </button>
        <button
          className={`${styles.tab} ${activeTab === "timeline" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("timeline")}
        >
          Threat Timeline
        </button>
      </nav>

      {/* Main Content */}
      <main className={styles.content}>
        {activeTab === "overview" && (
          <div className={styles.overviewGrid}>
            <div className={styles.gridItem}>
              <HoneypotStatusGrid honeypots={honeypotData} />
            </div>
            <div className={styles.gridItem}>
              <ThreatTimelineWidget events={threatEvents} compact />
            </div>
          </div>
        )}

        {activeTab === "decoy-bayou" && (
          <DecoyBayouMap honeypots={honeypotData} threats={threatEvents} />
        )}

        {activeTab === "intelligence" && (
          <IntelligenceFusionPanel
            fusionData={fusionIntel}
            events={threatEvents}
          />
        )}

        {activeTab === "timeline" && (
          <div data-testid="fabric-event-stream">
            <ThreatTimelineWidget events={threatEvents} />
          </div>
        )}
      </main>

      {/* Footer */}
      <DashboardFooter
        moduleName="REACTIVE FABRIC"
        classification="TOP SECRET"
        statusItems={[
          {
            label: "HONEYPOTS",
            value: `${metrics.activeHoneypots} ACTIVE`,
            online: metrics.activeHoneypots > 0,
          },
          { label: "PHASE", value: "INTELLIGENCE COLLECTION", online: true },
        ]}
        metricsItems={[
          { label: "INTERACTIONS", value: metrics.totalInteractions },
          { label: "ATTACKERS", value: metrics.uniqueAttackers },
          { label: "CRITICAL", value: metrics.criticalThreats },
        ]}
        showTimestamp={true}
      />
    </div>
  );
};

export default ReactiveFabricDashboard;

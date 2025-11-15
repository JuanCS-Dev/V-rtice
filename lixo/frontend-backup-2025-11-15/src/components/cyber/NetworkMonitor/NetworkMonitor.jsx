/**
 * NETWORK MONITOR - Real-time Network Traffic Monitoring Center
 *
 * Monitoramento de tráfego de rede em tempo real
 * Delegação de lógica para useNetworkMonitoring hook
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - Card wrapper with data-maximus-tool="network-monitor"
 * - <section> for AI assistance
 * - <section> for monitoring header/controls
 * - <section> for statistics dashboard
 * - <section> for event stream
 * - <section> for advanced controls
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="network-monitor"
 * - Monitor network status via data-maximus-status
 * - Access statistics via data-maximus-section="statistics"
 * - Interpret event stream via semantic structure
 *
 * @version 2.0.0 (Maximus Vision)
 * @author Gemini + Maximus Vision Protocol
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from "react";
import { Card } from "../../shared/Card";
import AskMaximusButton from "../../shared/AskMaximusButton";
import NetworkMonitorHeader from "./components/NetworkMonitorHeader";
import NetworkStatistics from "./components/NetworkStatistics";
import NetworkEventStream from "./components/NetworkEventStream";
import NetworkAdvancedControls from "./components/NetworkAdvancedControls";
import { useNetworkMonitoring } from "./hooks/useNetworkMonitoring";
import styles from "./NetworkMonitor.module.css";

export const NetworkMonitor = () => {
  const {
    isMonitoring,
    networkEvents,
    statistics,
    toggleMonitoring,
    getSeverityClass,
  } = useNetworkMonitoring();

  return (
    <Card
      title="NETWORK MONITORING CENTER"
      badge="CYBER"
      variant="cyber"
      data-maximus-tool="network-monitor"
      data-maximus-category="shared"
      data-maximus-status={isMonitoring ? "monitoring" : "idle"}
    >
      <div className={styles.widgetBody}>
        <section
          style={{ marginBottom: "1rem" }}
          role="region"
          aria-label="AI assistance"
          data-maximus-section="ai-assistance"
        >
          <AskMaximusButton
            context={{
              type: "network_monitor",
              data: { networkEvents, statistics },
              isMonitoring,
              eventsCount: networkEvents.length,
            }}
            prompt="Analyze this network traffic and identify anomalies, suspicious patterns, or security concerns"
            size="medium"
            variant="secondary"
          />
        </section>

        <section
          role="region"
          aria-label="Monitoring controls"
          data-maximus-section="controls"
        >
          <NetworkMonitorHeader
            isMonitoring={isMonitoring}
            onToggleMonitoring={toggleMonitoring}
          />
        </section>

        <section
          role="region"
          aria-label="Network statistics"
          data-maximus-section="statistics"
        >
          <NetworkStatistics statistics={statistics} />
        </section>

        <section
          role="region"
          aria-label="Network events stream"
          data-maximus-section="events"
        >
          <NetworkEventStream
            isMonitoring={isMonitoring}
            networkEvents={networkEvents}
            getSeverityClass={getSeverityClass}
          />
        </section>

        <section
          role="region"
          aria-label="Advanced controls"
          data-maximus-section="advanced-controls"
        >
          <NetworkAdvancedControls isMonitoring={isMonitoring} />
        </section>
      </div>
    </Card>
  );
};

export default NetworkMonitor;

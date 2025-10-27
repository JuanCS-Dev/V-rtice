/**
 * COCKPIT SOBERANO - HubAI Command & Intelligence Center
 * Centro de Comando da Célula Híbrida
 *
 * Dashboard de comando unificado com:
 * - Real-time verdict monitoring (WebSocket stream)
 * - Alliance relationship visualization
 * - C2L command execution console
 * - System health metrics
 * - NO MOCKS - 100% Real Data
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - Fully navigable by Maximus AI via data-maximus-* attributes
 * - WCAG 2.1 AAA compliant
 * - Semantic HTML5 structure (article, section, aside)
 * - ARIA 1.2 patterns for landmarks and live regions
 *
 * Maximus can:
 * - Identify dashboard via data-maximus-module="cockpit-soberano"
 * - Monitor verdicts via data-maximus-monitor="verdicts"
 * - Navigate alliance graph via data-maximus-section="alliance-graph"
 * - Execute commands via data-maximus-interactive="true"
 * - Access real-time streams via data-maximus-live="true"
 *
 * i18n: Fully internationalized with pt-BR and en-US support
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { SovereignHeader } from './components/SovereignHeader';
import { VerdictPanel } from './components/VerdictPanel';
import { RelationshipGraph } from './components/RelationshipGraph';
import { CommandConsole } from './components/CommandConsole';
import { DashboardFooter } from '../../shared/DashboardFooter';
import { useVerdictStream } from './hooks/useVerdictStream';
import { useCockpitMetrics } from './hooks/useCockpitMetrics';
import { useAllianceGraph } from './hooks/useAllianceGraph';
import SkipLink from '../../shared/SkipLink';
import QueryErrorBoundary from '../../shared/QueryErrorBoundary';
import styles from './CockpitSoberano.module.css';

export const CockpitSoberano = ({ setCurrentView }) => {
  const { t } = useTranslation();

  // Real data hooks - NO MOCKS
  const { verdicts, isConnected, stats, dismissVerdict } = useVerdictStream();
  const { metrics, loading: metricsLoading } = useCockpitMetrics();
  const { graphData, loading: graphLoading } = useAllianceGraph();

  const handleBack = () => {
    if (setCurrentView) {
      setCurrentView('main');
    }
  };

  // Extract unique agents from graph for command console
  const availableAgents = graphData.nodes.map(node => ({
    id: node.id,
    name: node.label,
    status: node.status
  }));

  return (
    <article
      className={styles.cockpitContainer}
      role="article"
      aria-labelledby="cockpit-soberano-title"
      data-maximus-module="cockpit-soberano"
      data-maximus-navigable="true"
      data-maximus-version="2.0"
      data-maximus-category="command-center">

      <SkipLink href="#cockpit-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Scanline Effect - Decorative */}
      <div className={styles.scanlineOverlay} aria-hidden="true"></div>

      {/* Header */}
      <QueryErrorBoundary>
        <SovereignHeader
          metrics={metrics}
          loading={metricsLoading}
          onBack={handleBack}
          systemHealth={metrics.systemHealth}
          verdictStats={stats}
        />
      </QueryErrorBoundary>

      {/* Main Content */}
      <section
        id="cockpit-content"
        className={styles.mainContent}
        role="region"
        aria-label={t('cockpit.workspace', 'Command center workspace')}
        data-maximus-section="workspace">

        {/* Left Panel: Verdicts */}
        <section
          className={styles.leftPanel}
          role="region"
          aria-label={t('cockpit.verdicts.title', 'Verdicts')}
          aria-live="polite"
          aria-atomic="false"
          data-maximus-section="verdicts"
          data-maximus-monitor="verdicts"
          data-maximus-live="true">

          <QueryErrorBoundary>
            <VerdictPanel
              verdicts={verdicts}
              onDismiss={dismissVerdict}
              isConnected={isConnected}
            />
          </QueryErrorBoundary>
        </section>

        {/* Right Panel: Alliance Graph + Command Console */}
        <aside
          className={styles.rightPanel}
          role="complementary"
          aria-label={t('cockpit.sidePanel', 'Alliance graph and command console')}
          data-maximus-section="side-panel">

          <section
            className={styles.graphSection}
            role="region"
            aria-label={t('cockpit.allianceGraph', 'Alliance relationship graph')}
            data-maximus-section="alliance-graph"
            data-maximus-interactive="true">

            <QueryErrorBoundary>
              <RelationshipGraph
                graphData={graphData}
                loading={graphLoading}
              />
            </QueryErrorBoundary>
          </section>

          <section
            className={styles.commandSection}
            role="region"
            aria-label={t('cockpit.commandConsole', 'C2L command console')}
            data-maximus-section="command-console"
            data-maximus-interactive="true">

            <QueryErrorBoundary>
              <CommandConsole
                availableAgents={availableAgents}
              />
            </QueryErrorBoundary>
          </section>
        </aside>
      </section>

      {/* Footer */}
      <DashboardFooter
        moduleName="COCKPIT SOBERANO"
        classification="TOP SECRET"
        statusItems={[
          { label: 'WEBSOCKET', value: isConnected ? 'CONNECTED' : 'DISCONNECTED', online: isConnected },
          { label: 'SYSTEM', value: metrics.systemHealth || 'UNKNOWN', online: metrics.systemHealth === 'HEALTHY' },
          { label: 'AGENTS', value: `${availableAgents.length} ONLINE`, online: availableAgents.length > 0 }
        ]}
        metricsItems={[
          { label: 'VERDICTS', value: verdicts.length },
          { label: 'ALLIANCES', value: graphData.nodes.length }
        ]}
        showTimestamp={true}
      />
    </article>
  );
};

CockpitSoberano.propTypes = {
  setCurrentView: PropTypes.func
};

export default CockpitSoberano;

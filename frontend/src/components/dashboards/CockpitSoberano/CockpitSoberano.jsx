/**
 * CockpitSoberano - HubAI Command & Intelligence Dashboard
 * 
 * Centro de Comando da Célula Híbrida
 * Real-time verdict monitoring, alliance visualization, and C2L command execution
 * 
 * NO MOCKS - 100% Real Data from backend services
 * Follows Vértice Design System v2.0
 * 
 * @version 1.0.0
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
    <div className={styles.cockpitContainer}>
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Scanline Effect */}
      <div className={styles.scanlineOverlay}></div>

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
      <main id="main-content" className={styles.mainContent} role="main">
        {/* Left Panel: Verdicts */}
        <section className={styles.leftPanel} aria-label={t('cockpit.verdicts.title', 'Verdicts')}>
          <QueryErrorBoundary>
            <VerdictPanel
              verdicts={verdicts}
              onDismiss={dismissVerdict}
              isConnected={isConnected}
            />
          </QueryErrorBoundary>
        </section>

        {/* Right Panel: Alliance Graph + Command Console */}
        <aside className={styles.rightPanel}>
          <div className={styles.graphSection}>
            <QueryErrorBoundary>
              <RelationshipGraph
                graphData={graphData}
                loading={graphLoading}
              />
            </QueryErrorBoundary>
          </div>

          <div className={styles.commandSection}>
            <QueryErrorBoundary>
              <CommandConsole
                availableAgents={availableAgents}
              />
            </QueryErrorBoundary>
          </div>
        </aside>
      </main>

      {/* Footer */}
      <DashboardFooter />
    </div>
  );
};

CockpitSoberano.propTypes = {
  setCurrentView: PropTypes.func
};

export default CockpitSoberano;

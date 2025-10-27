/**
 * PurpleTeamDashboard - Purple Team Operations Center
 *
 * Unified dashboard for purple team operations combining:
 * - RED TEAM: Offensive operations and attack simulations
 * - BLUE TEAM: Detection, monitoring, and defensive response
 * - CORRELATION: Attack-to-detection mapping
 * - GAP ANALYSIS: Identification of detection blind spots
 * - UNIFIED TIMELINE: Synchronized view of attacks and detections
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - Fully navigable by Maximus AI via data-maximus-* attributes
 * - WCAG 2.1 AAA compliant
 * - Semantic HTML5 structure (article, section)
 * - ARIA 1.2 patterns for dynamic view switching
 *
 * Maximus can:
 * - Identify dashboard via data-maximus-module="purple-team-dashboard"
 * - Monitor correlations via data-maximus-monitor="correlations"
 * - Switch views via data-maximus-view attributes
 * - Track coverage metrics in real-time
 *
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PurpleHeader } from './components/PurpleHeader';
import { SplitView } from './components/SplitView';
import { UnifiedTimeline } from './components/UnifiedTimeline';
import { GapAnalysis } from './components/GapAnalysis';
import { DashboardFooter } from '../../shared/DashboardFooter';
import { usePurpleTeamData } from './hooks/usePurpleTeamData';
import SkipLink from '../../shared/SkipLink';
import styles from './PurpleTeamDashboard.module.css';

export const PurpleTeamDashboard = ({ setCurrentView }) => {
  const { t } = useTranslation();
  const [activeView, setActiveView] = useState('split'); // 'split' | 'timeline' | 'analysis'
  const { attackData, defenseData, correlations, gaps, loading } = usePurpleTeamData();

  const handleBack = () => {
    if (setCurrentView) {
      setCurrentView('main');
    }
  };

  return (
    <article
      className={styles.purpleDashboard}
      role="article"
      aria-labelledby="purple-team-dashboard-title"
      data-maximus-module="purple-team-dashboard"
      data-maximus-navigable="true"
      data-maximus-version="2.0"
      data-maximus-category="purple-team">

      <SkipLink href="#purple-team-content">{t('accessibility.skipToMain')}</SkipLink>

      <PurpleHeader
        onBack={handleBack}
        activeView={activeView}
        onViewChange={setActiveView}
        stats={{
          activeAttacks: attackData.active.length,
          detections: defenseData.detections.length,
          coverage: gaps.coveragePercentage,
          correlations: correlations.length
        }}
      />

      <section
        id="purple-team-content"
        className={styles.content}
        role="region"
        aria-label={t('dashboard.purple.content', 'Purple team operations content')}
        aria-live="polite"
        aria-atomic="false"
        data-maximus-section="content"
        data-maximus-view={activeView}
        data-maximus-monitor="correlations"
        data-maximus-interactive="true">

        {activeView === 'split' && (
          <SplitView
            attackData={attackData}
            defenseData={defenseData}
            correlations={correlations}
            loading={loading}
          />
        )}

        {activeView === 'timeline' && (
          <UnifiedTimeline
            events={[...attackData.events, ...defenseData.events]}
            correlations={correlations}
            loading={loading}
          />
        )}

        {activeView === 'analysis' && (
          <GapAnalysis
            gaps={gaps}
            attackData={attackData}
            defenseData={defenseData}
            loading={loading}
          />
        )}
      </section>

      <DashboardFooter
        moduleName="PURPLE TEAM OPERATIONS"
        classification="CONFIDENCIAL"
        statusItems={[
          { label: 'RED TEAM', value: `${attackData.active.length} ACTIVE`, online: attackData.active.length > 0 },
          { label: 'BLUE TEAM', value: `${defenseData.detections.length} DETECTIONS`, online: true },
          { label: 'COVERAGE', value: `${gaps.coveragePercentage}%`, online: gaps.coveragePercentage > 80 }
        ]}
        metricsItems={[
          { label: 'ATTACKS', value: attackData.active.length },
          { label: 'CORRELATIONS', value: correlations.length }
        ]}
      />
    </article>
  );
};

export default PurpleTeamDashboard;

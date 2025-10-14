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
 * @version 1.0.0
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
    <div className={styles.purpleDashboard}>
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

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

      <div id="main-content" className={styles.content} role="main">
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
      </div>

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
    </div>
  );
};

export default PurpleTeamDashboard;
